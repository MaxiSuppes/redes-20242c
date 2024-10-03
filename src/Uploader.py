import os
import socket

from src.Logger import logger
from src.settings import settings


class Uploader:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def upload(self, source_directory, filename):
        file_path = os.path.join(source_directory, filename)
        if not os.path.exists(file_path):
            logger.info(f"Archivo {filename} no encontrado")
            return

        protocol = settings.protocol()(connection=self.sock, external_host_address=(self.server_ip, self.server_port))
        logger.info(f"Usando el protocolo {settings.protocol_name()} para {settings.upload_command()} de {filename}")
        protocol.send_message(f"{settings.upload_command()} {filename}".encode())
        protocol.send_file(file_path)
