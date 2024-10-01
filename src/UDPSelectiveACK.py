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
        self.file_transfer_complete

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
            self.file_transfer_complete = False

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

    def handle_received_packet(self, packet_number, payload, received_packets, file_to_storage):
        if packet_number <= last_packet_received: # Verificar si el paquete ya fue recibido (duplicado)
            logger.debug(f"Paquete duplicado {packet_number}, enviando ACK de todas formas.")

        elif packet_number == last_packet_received + 1: # Verificar si el paquete es el siguiente en la secuencia
            logger.debug(f"Paquete {packet_number} en secuencia. Escribiendo a archivo.")
            file_to_storage.write(payload)
            last_packet_received += 1

            while last_packet_received + 1 in received_packets: # Escribir todos los paquetes subsecuentes que están en orden
                last_packet_received += 1
                file_to_storage.write(received_packets.pop(last_packet_received))
                logger.debug(f"Paquete {last_packet_received} en secuencia. Escribiendo a archivo.")

        else: # Almacenar el paquete si está fuera de orden
            logger.debug(f"Paquete {packet_number} fuera de orden. No escrito aún.")
            received_packets[packet_number] = payload
            logger.debug(f"Paquete {packet_number} almacenado, esperando ACK.")

    def receive_file(self, file_path):
        logger.info(f"Recibiendo archivo en {file_path} desde {self.external_host_address}")

        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # Número del último paquete recibido en orden
            received_packets = {}  # Almacena paquetes recibidos fuera de orden

            while True:
                packet = self.receive_packet()

                packet_number = packet.sequence_number()
                payload = packet.payload()

                if payload == settings.end_file_command().encode():
                    logger.debug(f"Señal de fin de archivo recibida, terminando recepción.")
                    break

                logger.debug(f"Paquete recibido: {packet_number}")

                self.handle_received_packet(packet_number, payload, received_packets, file_to_storage)

                # Enviar un ACK para el paquete actual (aunque esté fuera de orden o duplicado)
                ack_packet = Packet(packet_number, settings.ack_command().encode()).as_bytes()
                self.send_message(ack_packet)
                logger.debug(f"ACK enviado para paquete {packet_number} a {self.external_host_address}")

            logger.info(f"Archivo recibido correctamente en {file_path}")

