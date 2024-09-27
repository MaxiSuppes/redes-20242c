import os
from src import Host
import threading
import queue

DEFAULT_STORAGE_DIRECTORY = './storage'

class Server(Host):
    def __init__(self, host, port, storage_directory):
        super().__init__(host, port)
        self.storage_directory = storage_directory
        self.client_address = None
        self.clients = {}

    def start(self):
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            packet, client_address = self.receive_packet()
            if client_address not in self.clients.keys():
                print("Nuevo cliente: ", client_address)
                self.clients[client_address] = queue.Queue()
                threading.Thread(target=self.handle_client, args=(client_address,)).start()

            payload = packet.get_payload()

            print(f"Guardando {payload} desde {client_address}")
            self.clients[client_address].put(payload)

    def handle_client(self, client_address):
        command = self.clients[client_address].get()

        try:
            if command.startswith('upload'):
                filename = command.split()[1]
                print(f"Se va a recibir el archivo {filename}")
                self.receive_file_from_client(filename, client_address)
            elif command.startswith('download'):
                filename = command.split()[1]
                print(f"Se solicitó el archivo {filename}")
                self.send_file_to_client(filename, client_address)
        except UnicodeDecodeError:
            print(f"Comando no reconocido: {command}")

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

