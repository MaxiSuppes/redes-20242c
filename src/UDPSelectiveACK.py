import queue
import socket
import threading

from src.Logger import logger
from src.Packet import Packet
from src.settings import settings


class UDPSelectiveAck:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address
        self.connection = connection
        self.message_queue = message_queue
        self.window_size = settings.window_size()
        self.not_acknowledged_packets = {}
        self.received_acks = set()
        self.ack_thread = None
        self.ack_stop_event = threading.Event()
        self.lock = threading.Lock()

    def receive_packet(self, timeout=None):
        if self.message_queue:
            raw_packet = self.message_queue.get(timeout=timeout)
        else:
            if timeout:
                self.connection.settimeout(timeout)
            expected_packet_size = settings.packet_size() + settings.packet_number_size()
            raw_packet, address = self.connection.recvfrom(expected_packet_size)

        return Packet.from_bytes(raw_packet)

    def timeout_error_class(self):
        if self.message_queue:
            return queue.Empty
        else:
            return socket.timeout

    def send_message(self, message):
        self.connection.sendto(message, self.external_host_address)

    def receive_acks(self):
        while not self.ack_stop_event.is_set():
            try:
                ack_packet = self.receive_packet(timeout=settings.timeout())
                ack_number = ack_packet.sequence_number()
                logger.debug(f"ACK recibido {ack_number}")
                with self.lock:
                    if ack_number in self.not_acknowledged_packets.keys():
                        del self.not_acknowledged_packets[ack_number]
                        self.received_acks.add(ack_number)
            except self.timeout_error_class():
                continue  # Ignoro el timeout

    def send_file(self, file_path):
        logger.info(f"Enviando archivo {file_path} a {self.external_host_address}")

        self.start_ack_thread()
        
        with open(file_path, 'rb') as file_to_send:
            packet_number = 1

            while True:
                # Enviar paquetes hasta llenar la ventana de transmisión
                while len(self.not_acknowledged_packets.keys()) < self.window_size:
                    file_chunk = file_to_send.read(settings.packet_size())
                    if not file_chunk:
                        logger.debug(f"Fin de archivo")
                        break

                    # Crear y enviar el paquete
                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)

                    # Añadirlo a la lista de no confirmados
                    with self.lock:
                        self.not_acknowledged_packets[packet_number] = packet

                    packet_number += 1

                logger.debug(f"self.not_acknowledged_packets {len(self.not_acknowledged_packets)}")
                with self.lock:
                    for not_acknowledged_packet_number, not_acknowledged_packet in list(
                            self.not_acknowledged_packets.items()):
                        self.send_message(not_acknowledged_packet)

                # Romper si ya no hay más paquetes que enviar o confirmar
                if len(self.not_acknowledged_packets) == 0 and not file_chunk:
                    break

        # Enviar señal de fin de archivo
        logger.debug(f"Enviando señal de fin de archivo")
        packet = Packet(packet_number + 1, settings.end_file_command().encode()).as_bytes()
        self.send_message(packet)
        self.stop_ack_thread()

    def receive_file(self, file_path):
        logger.info(f"Recibiendo archivo en {file_path} desde {self.external_host_address}")

        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0
            received_packets = {}

            while True:
                packet = self.receive_packet()

                packet_number = packet.sequence_number()
                payload = packet.payload()

                if payload == settings.end_file_command().encode():
                    logger.debug(f"Señal de fin de archivo recibida, terminando recepción.")
                    break

                logger.debug(f"Paquete recibido: {packet_number}")

                # Verificar si el paquete ya fue recibido (duplicado)
                if packet_number <= last_packet_received:
                    logger.debug(f"Paquete número {packet_number}. Ya fue recibido. Enviando ACK.")
                else:
                    received_packets[packet_number] = payload

                    # Verificar si el paquete es el siguiente en la secuencia
                    if packet_number == last_packet_received + 1:
                        logger.debug(f"Paquete número {packet_number}. Escribiendo a archivo.")
                        file_to_storage.write(payload)
                        last_packet_received += 1

                        # Escribir todos los paquetes subsecuentes que están en orden
                        while last_packet_received + 1 in received_packets:
                            logger.debug(f"Paquete subsecuente número {last_packet_received} Escribiendo a archivo.")
                            last_packet_received += 1
                            file_to_storage.write(received_packets.pop(last_packet_received))
                    else:
                        logger.debug(f"Paquete número {packet_number}. Fuera de orden. Guardando para después.")

                # Enviar un ACK para el paquete actual (aunque esté fuera de orden o duplicado)
                ack_packet = Packet(packet_number, settings.ack_command().encode()).as_bytes()
                self.send_message(ack_packet)

            logger.info(f"Archivo recibido correctamente en {file_path}")

    def start_ack_thread(self):
        self.ack_thread = threading.Thread(target=self.receive_acks)
        self.ack_thread.start()

    def stop_ack_thread(self):
        self.ack_stop_event.set()
        if self.ack_thread:
            self.ack_thread.join()
