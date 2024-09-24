import os
import socket

DEFAULT_STORAGE_DIRECTORY = './storage'


class Server:
    def __init__(self, host, port, storage_directory):
        self.host = host
        self.port = port
        self.storage_directory = storage_directory
        self.client_address = None
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            data, self.client_address = self.sock.recvfrom(1024)
            command = data.decode()
            print(f"Comando recibido: {command} desde {self.client_address}")

            if command.startswith('upload'):
                filename = command.split()[1]
                print(f"Se va a recibir el archivo {filename}")
                self.receive_file(filename)
            elif command.startswith('download'):
                filename = command.split()[1]
                print(f"Se solicitó el archivo {filename}")
                # TODO: Acá no habría enviar un ACK al cliente antes de empezar a enviar el archivo?
                self.send_file(filename)

    def receive_file(self, filename):
        file_path = os.path.join(self.storage_directory, filename)

        with open(file_path, 'wb') as f:
            while True:
                data, address = self.sock.recvfrom(1024)
                if data == b'END':
                    break
                f.write(data)
                self.sock.sendto(b'ACK', self.client_address)

        print(f"Archivo {filename} guardado en {self.storage_directory}")

    def send_file(self, filename):
        file_path = os.path.join(self.storage_directory, filename)

        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            # TODO: Enviar mensaje de error al cliente?
            return

        print(f"Enviando archivo {filename} a {self.client_address}")

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.sock.sendto(data, self.client_address)
                ack, address = self.sock.recvfrom(1024)
                if ack != b'ACK':
                    print("No se recibió un ACK. Reenviando paquete.")
                    f.seek(-1024, os.SEEK_CUR)  # Retrocede el puntero del archivo para volver a enviar el paquete

        self.sock.sendto(b'END', self.client_address)
        print(f"Se envió el archivo {filename} correctamente")

