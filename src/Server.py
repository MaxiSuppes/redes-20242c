import os
import queue
import socket
import struct
import threading

DEFAULT_STORAGE_DIRECTORY = './storage'
PACKET_SIZE = 1024
TIMEOUT = 5
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
                self.receive_file(filename, client_address)
            elif command.startswith('download'):
                filename = command.split()[1]
                print(f"Se solicitó el archivo {filename}")
                self.send_file(filename, client_address)
        except UnicodeDecodeError:
            print(f"Comando no reconocido: {data}")

    def receive_file(self, filename, client_address):
        file_path = os.path.join(self.storage_directory, filename)

        with open(file_path, 'wb') as file_to_storage:
            last_packet_received = 0  # El 0 representa que se recibió ningún paquete
            while True:
                packet = self.clients[client_address].get()
                print("packeeeet", packet)
                if packet == b"END":
                    break

                packet_number = struct.unpack('>I', packet[:4])[0]
                file_chunk = packet[4:]
                print(f"Paquete recibido: {packet_number}")
                if int(packet_number) != last_packet_received:
                    file_to_storage.write(file_chunk)
                    last_packet_received = int(packet_number)
                else:
                    print(f"Paquete {packet_number} ya recibido.")

                print(f"Enviando ACK {packet_number} al cliente.")
                self.sock.sendto(f'ACK_{packet_number}'.encode(), client_address)

        print(f"Archivo {filename} guardado en {self.storage_directory}")

    def send_file(self, filename, client_address):
        file_path = os.path.join(self.storage_directory, filename)

        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            # TODO: Enviar mensaje de error al cliente?
            return

        print(f"Enviando archivo {filename} a {client_address}")
        with (open(file_path, 'rb') as file_to_send):
            packet_number = 1
            while True:
                file_chunk = file_to_send.read(PACKET_SIZE)
                if not file_chunk:
                    print(f"Fin de archivo")
                    break

                missing_ack = True
                while missing_ack:
                    print(f"Enviando paquete {packet_number}", client_address)
                    # Se arma el struct para que del otro lado no haya que hacer un .decode() para un pdf
                    # no funca (por ejemplo
                    header = struct.pack('>I', packet_number)  # >I empaqueta un unsigned int de 4 bytes en big-endian
                    packet = header + file_chunk
                    self.sock.sendto(packet, client_address)
                    try:
                        ack = self.clients[client_address].get(timeout=TIMEOUT)
                        print(f"Elemento recibido mientras se espera el ack: {ack.decode()}")
                        if ack.decode() == f'ACK_{packet_number}':
                            print(f"ACK correcto: {ack.decode()}")
                            missing_ack = False
                            packet_number += 1
                        else:
                            print(f"ACK incorrecto: {ack.decode()}")
                    except queue.Empty:
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Enviando end")
        self.sock.sendto(b'END', client_address)
        print(f"Se envió el archivo {filename} correctamente")
