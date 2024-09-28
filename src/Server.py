import os
import queue
import socket
import threading
#from src.UDPStopAndWait import UDPStopAndWait
from src.UDPSACK import UDPSACK

DEFAULT_STORAGE_DIRECTORY = './storage'
PACKET_SIZE = 1024
PACKET_NUMBER_SIZE = 4


class Server:
    def __init__(self, host, port, storage_directory):
        self.host = host
        self.port = port
        self.storage_directory = storage_directory
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.clients = {}
        if not os.path.exists(self.storage_directory):
            os.makedirs(self.storage_directory)

    def start(self):
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            data, client_address = self.sock.recvfrom(PACKET_SIZE + PACKET_NUMBER_SIZE)
            if client_address not in self.clients.keys():
                print("Nuevo cliente: ", client_address)
                self.clients[client_address] = queue.Queue()
                threading.Thread(target=self.handle_client, args=(client_address,)).start()

            print(f"Guardando {data} desde {client_address}")
            self.clients[client_address].put(data)

    def handle_client(self, client_address):
        data = self.clients[client_address].get()

        try:
            command = data.decode()
            if command.startswith('upload'):
                filename = command.split()[1]
                print(f"Se va a recibir el archivo {filename}")
                """ protocol = UDPStopAndWait(connection=self.sock, external_host_address=client_address,
                                          message_queue=self.clients[client_address]) """
                protocol = UDPSACK(connection=self.sock, external_host_address=client_address,
                                          message_queue=self.clients[client_address])
                file_path = os.path.join(self.storage_directory, filename)
                protocol.receive_file(file_path)
                print(f"Archivo guardado en {file_path}")
            elif command.startswith('download'):
                filename = command.split()[1]
                file_path = os.path.join(self.storage_directory, filename)
                if not os.path.exists(file_path):
                    print(f"Archivo {filename} no encontrado")
                    return

                print(f"Se solicitó el archivo {filename}")
                """ protocol = UDPStopAndWait(connection=self.sock, external_host_address=client_address,
                                          message_queue=self.clients[client_address]) """
                protocol = UDPSACK(connection=self.sock, external_host_address=client_address,
                                          message_queue=self.clients[client_address])
                protocol.send_file(file_path)
                print(f"Se envió el archivo {filename} correctamente")
        except UnicodeDecodeError:
            print(f"Comando no reconocido: {data}")
