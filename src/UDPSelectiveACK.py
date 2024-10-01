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
        self.window_size = settings.window_size()  # Tamaño de la ventana
        self.not_acknowledged_packets = {}  # Paquetes enviados pero no confirmados
        self.received_acks = set()  # Lista de acks recibidos
        self.file_transfer_complete = False

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

        with open(file_path, 'rb') as file_to_send:
            packet_number = 1
            window_size = settings.window_size()
            last_packet_number = 0

            while True:
                # Enviar paquetes hasta llenar la ventana de transmisión
                while len(self.not_acknowledged_packets.keys()) < window_size:
                    file_chunk = file_to_send.read(settings.packet_size())
                    if not file_chunk:
                        logger.debug(f"Fin de archivo")
                        break

                    # Crear y enviar el paquete
                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)

                    # Añadirlo a la lista de no confirmados
                    self.not_acknowledged_packets[packet_number] = packet
                    logger.debug(f"Paquete {packet_number} enviado a {self.external_host_address}")

                    packet_number += 1

                # Esperar por ACKs y manejar retransmisión en caso de timeout
                try:
                    ack_packet = self.receive_packet(timeout=settings.timeout())
                    ack_number = ack_packet.sequence_number()

                    # Validar y procesar el ACK recibido
                    if ack_number in self.not_acknowledged_packets:
                        logger.debug(f"ACK recibido para paquete {ack_number}")
                        del self.not_acknowledged_packets[ack_number]  # Marcar como confirmado
                        self.received_acks.add(ack_number)

                except self.timeout_error_class():
                    logger.debug(f"TIMEOUT: Retransmitiendo paquetes no confirmados")
                    # Retransmitir solo paquetes que no fueron confirmados
                    for not_acknowledged_packet_number, not_acknowledged_packet in list(
                            self.not_acknowledged_packets.items()):
                        logger.debug(f"Retransmitiendo paquete {not_acknowledged_packet_number}")
                        self.send_message(not_acknowledged_packet)

                # Romper si ya no hay más paquetes que enviar o confirmar
                if len(self.not_acknowledged_packets) == 0 and not file_chunk:
                    break

        # Enviar señal de fin de archivo
        logger.debug(f"Enviando señal de fin de archivo")
        packet = Packet(packet_number + 1, settings.end_file_command().encode()).as_bytes()
        self.send_message(packet)


    def wait_for_acks(self):
        while True:
            try:
                ack_packet = self.receive_packet(timeout=settings.timeout())
                ack_number = ack_packet.sequence_number()

                if ack_number in self.not_acknowledged_packets:
                    logger.debug(f"ACK received for packet {ack_number}")
                    del self.not_acknowledged_packets[ack_number] 
                    self.received_acks.add(ack_number)

            except self.timeout_error_class():
                logger.debug(f"TIMEOUT: Retransmitting unacknowledged packets")
                for packet_number, packet in list(self.not_acknowledged_packets.items()):
                    logger.debug(f"Retransmitting packet {packet_number}")
                    self.send_message(packet)

            if self.file_transfer_complete and len(self.not_acknowledged_packets) == 0:
                break

    def send_file2(self, file_path):
        logger.info(f"Sending file {file_path} to {self.external_host_address}")

        with open(file_path, 'rb') as file_to_send:
            packet_number = 1
            window_size = settings.window_size()

            ack_thread = threading.Thread(target=self.wait_for_acks)
            ack_thread.start()

            while True:
                while len(self.not_acknowledged_packets.keys()) < window_size:
                    file_chunk = file_to_send.read(settings.packet_size())
                    if not file_chunk:
                        logger.debug(f"End of file")
                        self.file_transfer_complete = True
                        break

                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)

                    self.not_acknowledged_packets[packet_number] = packet
                    logger.debug(f"Packet {packet_number} sent to {self.external_host_address}")

                    packet_number += 1

                if self.file_transfer_complete:
                    break  

        logger.debug(f"Sending end-of-file signal")
        end_packet = Packet(packet_number + 1, settings.end_file_command().encode()).as_bytes()
        self.send_message(end_packet)

        ack_thread.join()

    def handle_received_packet(self, packet_number, payload, received_packets, file_to_storage, last_packet_received):
        if packet_number <= last_packet_received:  # Check if the packet has already been received (duplicate)
            logger.debug(f"Duplicate packet {packet_number}, sending ACK anyway.")

        elif packet_number == last_packet_received + 1:  # Check if the packet is the next one in sequence
            logger.debug(f"Packet {packet_number} in sequence. Writing to file.")
            file_to_storage.write(payload)
            last_packet_received += 1

            # Write all subsequent in-sequence packets
            while last_packet_received + 1 in received_packets:
                last_packet_received += 1
                file_to_storage.write(received_packets.pop(last_packet_received))
                logger.debug(f"Packet {last_packet_received} in sequence. Writing to file.")

        else:  # Store the packet if it's out of order
            logger.debug(f"Packet {packet_number} out of order. Not written yet.")
            received_packets[packet_number] = payload
            logger.debug(f"Packet {packet_number} stored, waiting for ACK.")

        return last_packet_received  # Return the updated last packet received

    def receive_file(self, file_path):
        logger.info(f"Receiving file at {file_path} from {self.external_host_address}")

        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # Number of the last packet received in order
            received_packets = {}  # Store out-of-order packets

            while True:
                packet = self.receive_packet()

                packet_number = packet.sequence_number()
                payload = packet.payload()

                if payload == settings.end_file_command().encode():
                    logger.debug(f"End of file signal received, terminating reception.")
                    break

                logger.debug(f"Packet received: {packet_number}")

                # Update the last_packet_received after handling the packet
                last_packet_received = self.handle_received_packet(packet_number, payload, received_packets, file_to_storage, last_packet_received)

                # Send an ACK for the current packet (even if it's out of order or a duplicate)
                ack_packet = Packet(packet_number, settings.ack_command().encode()).as_bytes()
                self.send_message(ack_packet)
                logger.debug(f"ACK sent for packet {packet_number} to {self.external_host_address}")

        logger.info(f"File received successfully at {file_path}")
