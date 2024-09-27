import os
import socket
import struct

PACKET_SIZE = 1024
TIMEOUT = 5


class Uploader:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def upload_file(self, source_directory, filename):
        file_path = os.path.join(source_directory, filename)
        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            return

        self.sock.sendto(f"upload {filename}".encode(), (self.host, self.port))
        print(f"Enviando archivo {filename} a {self.host}:{self.port}")

        with (open(file_path, 'rb') as file_to_send):
            packet_number = 1
            while True:
                file_chunk = file_to_send.read(PACKET_SIZE)
                if not file_chunk:
                    print(f"Fin de archivo")
                    break

                missing_ack = True
                while missing_ack:
                    print(f"Enviando paquete {packet_number}", f"{self.host}:{self.port}")
                    # Se arma el struct para que del ot ro lado no haya que hacer un .decode() para un pdf
                    # no funca (por ejemplo)
                    header = struct.pack('>I', packet_number)  # >I empaqueta un unsigned int de 4 bytes en big-endian
                    packet = header + file_chunk
                    self.sock.sendto(packet, (self.host, self.port))
                    try:
                        self.sock.settimeout(TIMEOUT)
                        ack, address = self.sock.recvfrom(PACKET_SIZE)
                        print(f"Elemento recibido mientras se espera el ack: {ack.decode()}")
                        if ack.decode() == f'ACK_{packet_number}':
                            print(f"ACK correcto: {ack.decode()}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            print(f"ACK incorrecto: {ack.decode()}")
                    except socket.timeout:
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Fin de archivo. reseteando timeout")
        self.sock.settimeout(None)
        print(f"Enviando end")
        self.sock.sendto(b'END', (self.host, self.port))
        print(f"Se envió el archivo {filename} correctamente")
