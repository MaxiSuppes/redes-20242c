import queue
import struct
import socket

PACKET_SIZE = 1024
PACKET_NUMBER_SIZE = 4
TIMEOUT = 2


class UDPStopAndWait:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address  # (ip, port)
        self.connection = connection
        self.message_queue = message_queue

    def receive_packet(self):
        if self.message_queue:
            print(f"Obteniendo mensaje de la Queue")
            return self.message_queue.get()
        else:
            print(f"Obteniendo mensaje del socket")
            packet, address = self.connection.recvfrom(PACKET_SIZE + PACKET_NUMBER_SIZE)
            return packet

    def set_timeout_and_receive_packet(self):
        if self.message_queue:
            print(f"Seteando timeout en la queue")
            return self.message_queue.get(TIMEOUT)
        else:
            print(f"Seteando timeout en el socket")
            self.connection.settimeout(TIMEOUT)
            return self.receive_packet()

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
                    header = struct.pack('>I', packet_number)  # >I empaqueta un unsigned int de 4 bytes en big-endian
                    packet = header + file_chunk
                    self.connection.sendto(packet, self.external_host_address)
                    try:
                        packet = self.set_timeout_and_receive_packet()
                        print(f"Elemento recibido mientras se espera el ack: {packet.decode()}")
                        if packet.decode() == f'ACK_{packet_number}':
                            print(f"ACK correcto: {packet.decode()}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            print(f"ACK incorrecto: {packet.decode()}")
                    except self.timeout_error_class():
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Enviando end")
        self.send_message(b'END')

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # El 0 representa que se recibió ningún paquete
            while True:
                packet = self.receive_packet()
                if packet == b"END":
                    break

                packet_number = struct.unpack('>I', packet[:4])[0]
                file_chunk = packet[4:]
                print(f"Paquete recibido: {packet_number}")
                if int(packet_number) != last_packet_received:
                    file_to_storage.write(file_chunk)
                    last_packet_received = int(packet_number)
                else:
                    print(f"Paquete {packet_number} ya recibido.")

                print(f"Enviando ACK {packet_number} a {self.external_host_address}.")
                self.connection.sendto(f'ACK_{packet_number}'.encode(), self.external_host_address)

