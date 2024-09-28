import queue
import socket

from src.Logger import logger
from src.Packet import Packet
from src.settings import settings


class UDPStopAndWait:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address  # (ip, port)
        self.connection = connection
        self.message_queue = message_queue

    def receive_packet(self, timeout=None):
        if self.message_queue:
            logger.debug(f"Obteniendo mensaje de la Queue con timeout {timeout}")
            raw_packet = self.message_queue.get(timeout=timeout)
        else:
            logger.debug(f"Obteniendo mensaje del socket con timeout {timeout}")
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

    def send_file(self, file_path):
        logger.info(f"Enviando archivo {file_path} a {self.external_host_address}")

        with (open(file_path, 'rb') as file_to_send):
            packet_number = 1
            while True:
                file_chunk = file_to_send.read(settings.packet_size())
                if not file_chunk:
                    logger.debug(f"Fin de archivo")
                    break

                missing_ack = True
                while missing_ack:
                    logger.debug(f"Enviando paquete {packet_number}", f"{self.external_host_address}")
                    # Se arma el struct para que del otro lado no haya que hacer un .decode() para un pdf
                    # no funca (por ejemplo)
                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)
                    try:
                        packet = self.receive_packet(timeout=settings.timeout())
                        decoded_payload = packet.decoded_payload()
                        if packet.is_valid_ack(packet_number):
                            logger.debug(f"ACK correcto: {decoded_payload}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            logger.debug(f"ACK incorrecto: {decoded_payload}")
                    except self.timeout_error_class():
                        logger.error(f"TIMEOUT: Reenviando paquete {packet_number}")

        logger.debug(f"Enviando end")
        packet = Packet(packet_number + 1, settings.end_file_command().encode()).as_bytes()
        self.send_message(packet)

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # El 0 representa que se recibió ningún paquete
            while True:
                packet = self.receive_packet()
                if packet.payload() == settings.end_file_command().encode():
                    break

                packet_number = packet.sequence_number()
                logger.debug(f"Paquete recibido: {packet_number}")
                if packet_number != last_packet_received:
                    file_to_storage.write(packet.payload())
                    last_packet_received = int(packet_number)
                else:
                    logger.debug(f"Paquete {packet_number} ya recibido.")

                logger.debug(f"Enviando ACK {packet_number} a {self.external_host_address}.")
                packet = Packet(packet_number, settings.ack_command().encode()).as_bytes()
                self.send_message(packet)

