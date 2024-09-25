import os
import socket
import threading

DEFAULT_STORAGE_DIRECTORY = './storage'
PACKET_SIZE = 1024
TIMEOUT = 5


class Server:
    def __init__(self, host, port, storage_directory):
        self.host = host
        self.port = port
        self.storage_directory = storage_directory
        self.sock = None

        if not os.path.exists(self.storage_directory):
            os.makedirs(self.storage_directory)

    def handle_client(self, data, client_address):
        while True:
            command = data.decode()
            if command.startswith('upload'):
                filename = command.split()[1]
                print(f"Se va a recibir el archivo {filename}")
                self.receive_file(filename, client_address)
            elif command.startswith('download'):
                filename = command.split()[1]
                print(f"Se solicitó el archivo {filename}")
                # TODO: Acá no habría enviar un ACK al cliente antes de empezar a enviar el archivo?
                self.send_file(filename, client_address)

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"Servidor escuchando en {self.host}:{self.port}")

        while True:
            try:
                data, client_address = self.sock.recvfrom(PACKET_SIZE)
                if data.decode().startswith('download'):
                    print(f"Se recibió un comando download de {client_address}. Se abre nuevo thread")
                threading.Thread(target=self.handle_client, args=(data, client_address), daemon=True).start()
            except Exception as e:
                print(f"Error recibiendo info: {e}")

    def receive_file(self, filename, client_address):
        # TODO: Hacerlo multiclient y con gestión de errores
        file_path = os.path.join(self.storage_directory, filename)

        with open(file_path, 'wb') as f:
            while True:
                data, address = self.sock.recvfrom(PACKET_SIZE)
                if data == b'END':
                    break
                f.write(data)
                self.sock.sendto(b'ACK', client_address)

        print(f"Archivo {filename} guardado en {self.storage_directory}")

    def send_file(self, filename, client_address):
        file_path = os.path.join(self.storage_directory, filename)

        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            # TODO: Enviar mensaje de error al cliente?
            return

        print(f"Enviando archivo {filename} a {client_address}")
        with open(file_path, 'rb') as file_to_send:
            while True:
                file_chunk = file_to_send.read(PACKET_SIZE)
                if not file_chunk:
                    print(f"Fin de archivo")
                    break

                packet_number = 1
                missing_ack = True
                while missing_ack:
                    print(f"Enviando paquete {packet_number}", file_chunk)
                    packet = f"{packet_number}:".encode() + file_chunk
                    self.sock.sendto(packet, client_address)
                    try:
                        self.sock.settimeout(TIMEOUT)
                        ack, address = self.sock.recvfrom(PACKET_SIZE)
                        print(f"Elemento recibido mientras se espera el ack: {ack.decode()}")
                        if ack.decode() == f'ACK_{packet_number}':
                            print(f"ACK correcto: {ack.decode()}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            print(f"ACK incorrecto: {ack.decode()}")
                    except socket.timeout:
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Fin de archivo. reseteando timeout")
        self.sock.settimeout(None)
        print(f"Enviando end")
        self.sock.sendto(b'END', client_address)
        print(f"Se envió el archivo {filename} correctamente")

