import os
import socket

from src.Logger import logger
from src.settings import settings


class Downloader:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # TODO: Podríamos tener como variable de configuración el protocolo (StopAndWait, SelectiveRepeat)

    def download(self, download_directory, filename):
        protocol = settings.protocol()(connection=self.sock, external_host_address=(self.server_ip, self.server_port))

        logger.info(f"Enviando código de descarga {settings.download_command()}")
        protocol.send_message(f"{settings.download_command()} {filename}".encode())
        logger.info(f"Usando el protocolo {settings.protocol_name()} para {settings.download_command()} de {filename}")
        file_path = os.path.join(download_directory, filename)
        protocol.receive_file(file_path)
