import os
import queue
import socket
import threading

from src.Logger import logger
from src.UDPSelectiveACK import UDPSelectiveAck
from src.UDPStopAndWait import UDPStopAndWait
from src.settings import settings


class Server:
    def __init__(self, host, port, storage_directory):
        self.host = host
        self.port = port
        self.storage_directory = storage_directory
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.clients = {}

        self.create_storage_if_not_exists()

    def create_storage_if_not_exists(self):
        if not os.path.exists(self.storage_directory):
            os.makedirs(self.storage_directory)

    def start(self):
        logger.info(f"Servidor iniciado en {self.host}:{self.port}")

        while True:
            expected_packet_size = settings.packet_size() + settings.packet_number_size()
            data, client_address = self.sock.recvfrom(expected_packet_size)
            if client_address not in self.clients.keys():
                logger.debug(f"Nuevo cliente: {client_address}")
                self.clients[client_address] = queue.Queue()
                threading.Thread(target=self.handle_client, args=(client_address,)).start()

            self.clients[client_address].put(data)

    def handle_client(self, client_address):
        data = self.clients[client_address].get()

        try:
            command = data.decode()
            if command.startswith(settings.upload_command()):
                filename = command.split()[1]
                logger.info(f"Se va a recibir el archivo {filename}")
                protocol = UDPSelectiveAck(connection=self.sock, external_host_address=client_address,
                                           message_queue=self.clients[client_address])
                file_path = os.path.join(self.storage_directory, filename)
                protocol.receive_file(file_path)
                logger.info(f"Archivo guardado en {file_path}")
            elif command.startswith(settings.download_command()):
                filename = command.split()[1]
                file_path = os.path.join(self.storage_directory, filename)
                if not os.path.exists(file_path):
                    logger.info(f"Archivo {filename} no encontrado")
                    return

                logger.info(f"Se solicitó el archivo {filename}")
                protocol = UDPSelectiveAck(connection=self.sock, external_host_address=client_address,
                                           message_queue=self.clients[client_address])
                protocol.send_file(file_path)
                logger.info(f"Se envió el archivo {filename} correctamente")
        except UnicodeDecodeError:
            logger.error(f"Hubo un error al gestionar la solicitud. Intentar nuevamente")
            return
