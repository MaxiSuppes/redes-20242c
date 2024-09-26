import socket
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