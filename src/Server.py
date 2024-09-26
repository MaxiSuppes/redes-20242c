import os
import socket
from host import Host

DEFAULT_STORAGE_DIRECTORY = './storage'


class Server(Host):
    def __init__(self, host, port, storage_directory):
        super().__init__(host, port)
        self.storage_directory = storage_directory
        self.client_address = None
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            packet, self.client_address = self.receive_packet()
            command = packet.payload
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
                packet, address = self.receive_packet()
                payload = packet.payload
                if payload == b'END':
                    break
                f.write(payload)
                self.send_ack(packet.get_seq_number(), client_address=self.client_address)

        print(f"Archivo {filename} guardado en {self.storage_directory}")

    def send_file(self, filename):
        file_path = os.path.join(self.storage_directory, filename)

        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            # TODO: Enviar mensaje de error al cliente?
            return

        print(f"Enviando archivo {filename} a {self.client_address}")

        with open(file_path, 'rb') as f:
            seq_number = 0
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.send_payload(data, seq_number, client_address=self.client_address)
                packet = self.receive_packet()[0]
                if  not packet.is_ACK and packet.seq_number != seq_number:
                    print("No se recibió un ACK. Reenviando paquete.")
                    f.seek(-1024, os.SEEK_CUR)  # Retrocede el puntero del archivo para volver a enviar el paquete
                else:
                    seq_number += 1

        self.send_payload(b'END', seq_number)
        print(f"Se envió el archivo {filename} correctamente")

