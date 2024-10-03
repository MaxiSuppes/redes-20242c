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
        self.ack_thread = None
        self.ack_stop_event = threading.Event()
        self.lock = threading.Lock()
        self.warnings = 0

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
                sack_packet = self.receive_packet(timeout=settings.timeout())
                logger.debug(f"Recibido ack {sack_packet.sequence_number()} con payload {sack_packet.payload()}")
                ack_number = sack_packet.sequence_number()

                received_packets = set()
                for i in range(0, ack_number):
                    received_packets.add(i)

                string_ranges = sack_packet.sack_string_ranges()
                for range_ in string_ranges:
                    start, end = range_.split("-")
                    for i in range(int(start), int(end)):
                        received_packets.add(i)

                if len(string_ranges) == 0:
                    self.warnings = 0
                else:
                    self.warnings += 1

                with self.lock:
                    for packet_number in received_packets:
                        if packet_number in self.not_acknowledged_packets.keys():
                            logger.debug(f"Se recibió el ack {ack_number}. Eliminando paquete {packet_number}")
                            del self.not_acknowledged_packets[packet_number]

                logger.debug(f"Quedan sin ack {self.not_acknowledged_packets.keys()}")
            except self.timeout_error_class():
                self.warnings = settings.max_warnings()

    def send_file(self, file_path):
        logger.info(f"Enviando archivo {file_path} a {self.external_host_address}")

        self.start_ack_thread()
        
        with open(file_path, 'rb') as file_to_send:
            packet_number = 0

            end_of_file = False
            while True:
                # Envia paquetes hasta llenar la ventana de transmisión
                while len(self.not_acknowledged_packets.keys()) < self.window_size:
                    file_chunk = file_to_send.read(settings.packet_size())
                    if not file_chunk:
                        end_of_file = True
                        logger.debug(f"Fin de archivo")
                        break

                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)
                    with self.lock:
                        self.not_acknowledged_packets[packet_number] = packet

                    packet_number += 1

                logger.debug(f"Acks faltantes despues de la ventana: {self.not_acknowledged_packets.keys()}")
                with self.lock:
                    if self.warnings >= settings.max_warnings() or end_of_file:
                        self.warnings = 0
                        logger.debug(f"Se superó el límite de advertencias. Reenviando todos los paquetes.")
                        for not_ack_packet_number, not_ack_packet in list(self.not_acknowledged_packets.items()):
                            logger.debug(f"Reenviando paquete {not_ack_packet_number}")
                            self.send_message(not_ack_packet)

                # Romper si ya no hay más paquetes que enviar o confirmar
                if len(self.not_acknowledged_packets) == 0 and end_of_file:
                    break

        # Enviar señal de fin de archivo
        logger.debug(f"Enviando señal de fin de archivo")
        packet = Packet(packet_number, settings.end_file_command().encode()).as_bytes()
        self.send_message(packet)
        self.stop_ack_thread()

    def receive_file(self, file_path):
        logger.info(f"Recibiendo archivo en {file_path} desde {self.external_host_address}")

        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = -1
            received_packets = {}

            while True:
                packet = self.receive_packet()

                packet_number = packet.sequence_number()
                logger.debug(f"Paquete número {packet_number} recibido")
                payload = packet.payload()

                if payload == settings.end_file_command().encode():
                    logger.debug(f"Señal de fin de archivo recibida, terminando recepción.")
                    break

                # Ignoro los packets duplicados
                if packet_number > last_packet_received:
                    received_packets[packet_number] = payload

                    # Verificar si el paquete es el siguiente en la secuencia
                    if packet_number == last_packet_received + 1:
                        logger.debug(f"Paquete número {packet_number}. Escribiendo a archivo.")
                        file_to_storage.write(payload)
                        last_packet_received = packet_number

                        # Escribir todos los paquetes subsecuentes que están en orden
                        while last_packet_received + 1 in received_packets.keys():
                            last_packet_received += 1
                            logger.debug(f"Paquete subsecuente número {last_packet_received} Escribiendo a archivo.")
                            file_to_storage.write(received_packets.pop(last_packet_received))

                        logger.debug(f"Enviando ack {last_packet_received + 1}")
                        sack_packet = Packet(last_packet_received + 1, settings.sack_command().encode()).as_bytes()
                        self.send_message(sack_packet)
                    else:
                        receive_packets_numbers = list(received_packets.keys())
                        receive_packets_numbers.sort()
                        index_of_current_packet = receive_packets_numbers.index(packet_number)
                        ranges = []
                        i = index_of_current_packet
                        range_left = receive_packets_numbers[i]
                        while i < len(receive_packets_numbers):
                            range_right = receive_packets_numbers[i] + 1

                            if range_right not in received_packets:
                                ranges.append(f"{range_left}-{range_right}")
                                if i == len(receive_packets_numbers) - 1:
                                    break
                                range_left = receive_packets_numbers[i + 1]

                            i += 1

                        logger.debug(f"Enviando ack {last_packet_received + 1} con {settings.sack_command(ranges).encode()}.")
                        sack_packet = Packet(last_packet_received + 1, settings.sack_command(ranges).encode()).as_bytes()
                        self.send_message(sack_packet)

            logger.info(f"Archivo recibido correctamente en {file_path}")

    def start_ack_thread(self):
        self.ack_thread = threading.Thread(target=self.receive_acks)
        self.ack_thread.start()

    def stop_ack_thread(self):
        self.ack_stop_event.set()
        if self.ack_thread:
            self.ack_thread.join()
