import queue
import socket

from src.Packet import Packet

PACKET_SIZE = 1024
PACKET_NUMBER_SIZE = 4
TIMEOUT = 2


class UDPStopAndWait:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address  # (ip, port)
        self.connection = connection
        self.message_queue = message_queue

    def receive_packet(self, timeout=None):
        if self.message_queue:
            print(f"Obteniendo mensaje de la Queue con timeout {timeout}")
            raw_packet = self.message_queue.get(timeout=timeout)
        else:
            print(f"Obteniendo mensaje del socket con timeout {timeout}")
            if timeout:
                self.connection.settimeout(timeout)
            raw_packet, address = self.connection.recvfrom(PACKET_SIZE + PACKET_NUMBER_SIZE)

        return Packet.from_bytes(raw_packet)

    def timeout_error_class(self):
        if self.message_queue:
            return queue.Empty
        else:
            return socket.timeout

    def send_message(self, message):
        self.connection.sendto(message, self.external_host_address)

    def send_file(self, file_path):
        print(f"Enviando archivo {file_path} a {self.external_host_address}")

        with (open(file_path, 'rb') as file_to_send):
            packet_number = 1
            while True:
                file_chunk = file_to_send.read(PACKET_SIZE)
                if not file_chunk:
                    print(f"Fin de archivo")
                    break

                missing_ack = True
                while missing_ack:
                    print(f"Enviando paquete {packet_number}", f"{self.external_host_address}")
                    # Se arma el struct para que del otro lado no haya que hacer un .decode() para un pdf
                    # no funca (por ejemplo)
                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)
                    try:
                        packet = self.receive_packet(timeout=TIMEOUT)
                        decoded_payload = packet.decoded_payload()
                        print(f"Elemento recibido mientras se espera el ack: {decoded_payload}")
                        if packet.is_valid_ack(packet_number):
                            print(f"ACK correcto: {decoded_payload}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            print(f"ACK incorrecto: {decoded_payload}")
                    except self.timeout_error_class():
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Enviando end")
        packet = Packet(packet_number + 1, b"END").as_bytes()
        self.send_message(packet)

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # El 0 representa que se recibió ningún paquete
            while True:
                packet = self.receive_packet()
                if packet.payload() == b"END":
                    break

                packet_number = packet.sequence_number()
                print(f"Paquete recibido: {packet_number}")
                if packet_number != last_packet_received:
                    file_to_storage.write(packet.payload())
                    last_packet_received = int(packet_number)
                else:
                    print(f"Paquete {packet_number} ya recibido.")

                print(f"Enviando ACK {packet_number} a {self.external_host_address}.")
                packet = Packet(packet_number, "ACK".encode()).as_bytes()
                self.send_message(packet)

