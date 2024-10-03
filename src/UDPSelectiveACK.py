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
        self.ack_thread_lock = threading.Lock()

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
                expected_packet = ack_number + 1
                if ack_packet.is_an_ack():
                    with self.ack_thread_lock:
                        try:
                            del self.not_acknowledged_packets[ack_number]  # El anterior al que me pide lo recibio si o si
                            logger.debug(f"Llegó ACK-{ack_number} quedó esto: {self.not_acknowledged_packets.keys()}")
                        except KeyError as e:
                            print(f"Error: {e}")
                            print(self.not_acknowledged_packets.keys())
                elif ack_packet.is_an_sack():
                    left, right = ack_packet.sack_range()
                    for sack_number in range(left, right):
                        if sack_number in self.not_acknowledged_packets.keys():
                            with self.ack_thread_lock:
                                del self.not_acknowledged_packets[sack_number]
                                logger.debug(f"Llegó SACK-{left, right} y quedó esto: {self.not_acknowledged_packets.keys()}")

                    for sack_number in range(expected_packet, left):
                        packet = self.not_acknowledged_packets[sack_number]
                        packet_number = sack_number
                        logger.debug(f"Reenviadno paquete {packet_number}")
                        self.send_message(Packet(packet_number, packet).as_bytes())
            except self.timeout_error_class():
                continue  # Ignoro el timeout

    def send_file(self, file_path):
        logger.info(f"Enviando archivo {file_path} a {self.external_host_address}")

        self.start_ack_thread()

        with open(file_path, 'rb') as file_to_send:
            packet_number = 1
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

                    with self.ack_thread_lock:
                        self.send_message(packet)
                        self.not_acknowledged_packets[packet_number] = packet

                    packet_number += 1

                logger.debug(f"Acks faltantes despues de la ventana: {self.not_acknowledged_packets.keys()}")

                # Romper si ya no hay más paquetes que enviar o confirmar
                if len(self.not_acknowledged_packets) == 0 and end_of_file:
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

                # Ignoro los packets duplicados
                if packet_number > last_packet_received:
                    received_packets[packet_number] = payload

                    # Verificar si el paquete es el siguiente en la secuencia
                    expected_packet = last_packet_received + 1
                    if packet_number == expected_packet:
                        last_packet_received = packet_number
                        while last_packet_received in received_packets.keys():
                            file_to_storage.write(received_packets.pop(last_packet_received))
                            last_packet_received += 1

                        last_packet_received -= 1
                        ack_packet = Packet(last_packet_received, settings.ack_command().encode()).as_bytes()
                        logger.debug(f"Ultimo recibido: {last_packet_received}")
                        self.send_message(ack_packet)
                    else:
                        received_packets_numbers = list(received_packets.keys())  # [1, 2, 5, 6, 7], expected = 3
                        range_start = expected_packet
                        while range_start not in received_packets_numbers:
                            range_start += 1

                        range_end = range_start
                        for i in range(range_start + 1, len(received_packets)):
                            if i in received_packets_numbers:
                                range_end += 1
                            else:
                                break

                        logger.debug(f"Recibi algo malo. Espero {expected_packet} pero tengo {range_start}-{range_end}")
                        sack_packet = Packet(expected_packet, f"SACK:{range_start},{range_end}".encode()).as_bytes()
                        self.send_message(sack_packet)
                logger.info(f"Es duplicado {packet_number}")
            logger.info(f"Archivo recibido correctamente en {file_path}")

    def start_ack_thread(self):
        self.ack_thread = threading.Thread(target=self.receive_acks)
        self.ack_thread.start()

    def stop_ack_thread(self):
        self.ack_stop_event.set()
        if self.ack_thread:
            self.ack_thread.join()
