import socket
import os
from packet import Packet

class Host:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def receive_packet(self):
        data, address = self.sock.recvfrom(1024)
        return Packet.from_bytes(data), address
    
    def send_ack(self, seq_number, client_address: None):
        ack_packet = Packet(seq_number, True, "ACK")
        if client_address:
            self.sock.sendto(ack_packet.as_bytes(), client_address)
        else:
            self.sock.sendto(ack_packet.as_bytes(), (self.host, self.port))

    def send_payload(self, payload, seq_number, client_address=None):
        packet = Packet(seq_number, False, payload)
        if client_address:
            self.sock.sendto(packet.as_bytes(), client_address)
        else:
            self.sock.sendto(packet.as_bytes(), (self.host, self.port))

    def send_file(self, filename, file_path, client_address=None):

        with open(file_path, 'rb') as f:
            seq_number = 0
            while True:
                data = f.read(1024)
                if not data:
                    break
                if client_address:
                    self.send_payload(data, seq_number, client_address=client_address)
                else:
                    self.send_payload(data, seq_number)
                packet = self.receive_packet()[0]
                if  not packet.is_ACK and packet.seq_number != seq_number:
                    print("No se recibió un ACK. Reenviando paquete.")
                    f.seek(-1024, os.SEEK_CUR)  # Retrocede el puntero del archivo para volver a enviar el paquete
                else:
                    seq_number += 1

        self.send_payload(b'END', seq_number)
        print(f"Se envió el archivo {filename} correctamente")