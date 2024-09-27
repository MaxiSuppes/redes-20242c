import os
import socket

from src.UDPStopAndWait import UDPStopAndWait


class Uploader:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def upload(self, source_directory, filename):
        file_path = os.path.join(source_directory, filename)
        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            return

        protocol = UDPStopAndWait(connection=self.sock, external_host_address=(self.server_ip, self.server_port))
        protocol.send_message(f"upload {filename}".encode())
        protocol.send_file(file_path)
        print(f"Se envió el archivo {filename} correctamente")
