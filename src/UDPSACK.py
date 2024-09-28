import queue
import socket
from src.Packet import Packet

PACKET_SIZE = 1024
TIMEOUT = 2
WINDOW_SIZE = 5  
class UDPSACK:
    def __init__(self, connection, external_host_address, message_queue=None):
        self.external_host_address = external_host_address  # (ip, port)
        self.connection = connection
        self.message_queue = message_queue
        self.window_size = WINDOW_SIZE
        self.acknowledged_packets = set() 
        self.received_packets = {} 

    def receive_packet(self, timeout=None):
        if self.message_queue:
            raw_packet = self.message_queue.get(timeout=timeout)
        else:
            if timeout:
                self.connection.settimeout(timeout)
            raw_packet, address = self.connection.recvfrom(PACKET_SIZE + 4)

        return Packet.from_bytes(raw_packet)

    def timeout_error_class(self):
        return queue.Empty if self.message_queue else socket.timeout

    def send_message(self, message):
        self.connection.sendto(message, self.external_host_address)

    def send_file(self, file_path):
        print(f"Enviando archivo {file_path} a {self.external_host_address}")

        with open(file_path, 'rb') as file_to_send:
            packet_number = 1
            window = {}  # Paquetes que han sido enviados y no confirmados

            while True:
                while len(window) < self.window_size:
                    file_chunk = file_to_send.read(PACKET_SIZE)
                    if not file_chunk:
                        break

                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)
                    print(f"Enviado paquete {packet_number} a {self.external_host_address}")

                    window[packet_number] = packet
                    packet_number += 1

                try:
                    sack = self.receive_sack(timeout=TIMEOUT)
                    print(f"Recibido SACK: {sack}")

                    for acked_packet in sack["acks"]:
                        if acked_packet in window:
                            print(f"Paquete {acked_packet} confirmado")
                            del window[acked_packet]

                except self.timeout_error_class():
                    print("Timeout esperando SACK, retransmitiendo paquetes no confirmados")
                    for packet_num, packet_data in window.items():
                        print(f"Retransmitiendo paquete {packet_num}")
                        self.send_message(packet_data)

                if not window and not file_chunk:
                    break

        # Enviar paquete de finalización "END"
        print(f"Enviando paquete END")
        packet = Packet(packet_number, b"END").as_bytes()
        self.send_message(packet)

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            expected_packet = 1  # El próximo paquete que esperamos recibir

            while True:
                packet = self.receive_packet()

                # Si recibimos el paquete "END", terminamos
                if packet.payload() == b"END":
                    break

                packet_number = packet.sequence_number()

                # Si el paquete es el esperado, escribir en el archivo
                if packet_number == expected_packet:
                    print(f"Paquete {packet_number} recibido correctamente y en orden")
                    file_to_storage.write(packet.payload())
                    expected_packet += 1

                    # Verificar si hay paquetes fuera de orden en el buffer que ahora pueden escribirse
                    while expected_packet in self.received_packets:
                        print(f"Escribiendo paquete fuera de orden {expected_packet}")
                        file_to_storage.write(self.received_packets.pop(expected_packet))
                        expected_packet += 1

                # Si el paquete está fuera de orden, almacenarlo en buffer
                elif packet_number > expected_packet:
                    print(f"Paquete {packet_number} recibido fuera de orden, almacenado")
                    self.received_packets[packet_number] = packet.payload()

                # Enviar SACK con los paquetes recibidos hasta ahora
                acked_packets = list(range(1, expected_packet)) + list(self.received_packets.keys())
                sack_message = f"SACK {sorted(acked_packets)}"
                self.send_message(sack_message.encode())

    def receive_sack(self, timeout=None):
        raw_sack, address = self.connection.recvfrom(1024)
        sack_data = raw_sack.decode().replace("SACK", "").strip()
        acked_packets = set(map(int, sack_data.split()))
        return {"acks": acked_packets}
