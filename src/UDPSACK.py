import queue
import socket
from src.Packet import Packet

PACKET_SIZE = 1024
PACKET_NUMBER_SIZE = 4
TIMEOUT = 2
WINDOW_SIZE = 5  # Tamaño de la ventana deslizante para SACK

class UDPSACK:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address  # (ip, port)
        self.connection = connection
        self.message_queue = message_queue
        self.window_size = WINDOW_SIZE
        self.received_packets = {}  # Mantiene un registro de los paquetes recibidos
        self.acknowledged_packets = set()  # Paquetes reconocidos

    def receive_packet(self, timeout=None):
        if self.message_queue:
            print(f"Obteniendo mensaje de la Queue con timeout {timeout}")
            raw_packet = self.message_queue.get(timeout=timeout)
        else:
            print(f"Obteniendo mensaje del socket con timeout {timeout}")
            if timeout:
                self.connection.settimeout(timeout)
            raw_packet, address = self.connection.recvfrom(PACKET_SIZE + PACKET_NUMBER_SIZE)

        return Packet.from_bytes(raw_packet)

    def timeout_error_class(self):
        if self.message_queue:
            return queue.Empty
        else:
            return socket.timeout

    def send_message(self, message):
        self.connection.sendto(message, self.external_host_address)

    def send_file(self, file_path):
        print(f"Enviando archivo {file_path} a {self.external_host_address}")

        with (open(file_path, 'rb') as file_to_send):
            packet_number = 1
            while True:
                file_chunk = file_to_send.read(PACKET_SIZE)
                if not file_chunk:
                    print(f"Fin de archivo")
                    break

                missing_ack = True
                while missing_ack:
                    print(f"Enviando paquete {packet_number}", f"{self.external_host_address}")
                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)

                    try:
                        sack = self.receive_sack(timeout=TIMEOUT)
                        print(f"Recibido SACK: {sack}")
                        missing_ack = packet_number in sack["acks"]  # Verifica si este paquete fue reconocido
                        if missing_ack:
                            print(f"Paquete {packet_number} recibido correctamente")
                            packet_number += 1
                        else:
                            print(f"Paquete {packet_number} no confirmado. Retransmitiendo.")
                    except self.timeout_error_class():
                        print(f"Timeout. Reenviando paquete {packet_number}")

        print(f"Enviando END")
        packet = Packet(packet_number + 1, b"END").as_bytes()
        self.send_message(packet)

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            while True:
                packet = self.receive_packet()
                if packet.payload() == b"END":
                    break

                packet_number = packet.sequence_number()
                print(f"Paquete recibido: {packet_number}")
                if packet_number not in self.acknowledged_packets:
                    file_to_storage.write(packet.payload())
                    self.acknowledged_packets.add(packet_number)

                # Enviar SACK con los números de paquetes recibidos
                sack_message = f"SACK {sorted(self.acknowledged_packets)}"
                self.send_message(sack_message.encode())

    def receive_sack(self, timeout=None):
        raw_sack, address = self.connection.recvfrom(1024)
        sack_data = raw_sack.decode().replace("SACK", "").strip()
        acked_packets = set(map(int, sack_data.split()))
        return {"acks": acked_packets}
