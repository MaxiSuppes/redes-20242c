import os
import socket
from src.UDPStopAndWait import UDPStopAndWait


class Downloader:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # TODO: Podríamos tener como variable de configuración el protocolo (StopAndWait, SelectiveRepeat)

    def download(self, download_directory, filename):
        protocol = UDPStopAndWait(connection=self.sock, external_host_address=(self.server_ip, self.server_port))

        protocol.send_message(f"download {filename}".encode())
        file_path = os.path.join(download_directory, filename)
        protocol.receive_file(file_path)
        print(f"Archivo guardado en {file_path}")
