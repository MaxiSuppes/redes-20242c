import os
import socket
from src import Host

DEFAULT_STORAGE_DIRECTORY = './storage'

class Server(Host):
    def __init__(self, host, port, storage_directory):
        super().__init__(host, port)
        self.storage_directory = storage_directory
        self.client_address = None

    def start(self):
        self.sock.bind((self.host, self.port))
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            packet, self.client_address = self.receive_packet()
            command = packet.payload

            print(f"Comando recibido: {command} desde {self.client_address}")

            if command.startswith('upload'):
                filename = command.split()[1]
                print(f"Se va a recibir el archivo {filename}")
                self.receive_file_from_client(filename)
            elif command.startswith('download'):
                filename = command.split()[1]
                print(f"Se solicitó el archivo {filename}")
                # TODO: Acá no habría enviar un ACK al cliente antes de empezar a enviar el archivo?
                self.send_file_to_client(filename)

    def receive_file_from_client(self, filename):
        self.receive_file(self.storage_directory, filename, client_address=self.client_address)
        print(f"Archivo {filename} guardado en {self.storage_directory}")

    def send_file_to_client(self, filename):
        file_path = os.path.join(self.storage_directory, filename)

        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            # TODO: Enviar mensaje de error al cliente?
            return

        print(f"Enviando archivo {filename} a {self.client_address}")

        self.send_file(filename, file_path, client_address=self.client_address)

