import queue
import socket
from src.Packet import Packet

PACKET_SIZE = 1024
TIMEOUT = 5
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
            finished_sending = False

            while True:
                # Enviar paquetes hasta llenar la ventana, solo si no hemos terminado de leer el archivo
                while len(window) < self.window_size and not finished_sending:
                    file_chunk = file_to_send.read(PACKET_SIZE)

                    if not file_chunk:
                        print("Todos los paquetes han sido enviados. Esperando confirmaciones.")
                        finished_sending = True
                        break

                    packet = Packet(packet_number, file_chunk).as_bytes()
                    self.send_message(packet)
                    print(f"Enviado paquete {packet_number} a {self.external_host_address}")

                    # Añadir el paquete a la ventana para posible retransmisión
                    window[packet_number] = packet
                    packet_number += 1

                if finished_sending and not window:
                    print("Todos los paquetes han sido confirmados. Enviando END.")
                    packet = Packet(packet_number, b"END").as_bytes()
                    self.send_message(packet)
                    break

                # Esperar SACK
                try:
                    sack = self.receive_sack(timeout=TIMEOUT)
                    print(f"Recibido SACK: {sack}")

                    for acked_packet in sack["acks"]:
                        if acked_packet in window:
                            print(f"Paquete {acked_packet} confirmado, eliminando de la ventana")
                            del window[acked_packet]

                except self.timeout_error_class():
                    print("Timeout esperando SACK, retransmitiendo paquetes no confirmados.")
                    for packet_num, packet_data in window.items():
                        print(f"Retransmitiendo paquete {packet_num}")
                        self.send_message(packet_data)

    def receive_file(self, file_path):
        with open(file_path, 'wb') as file_to_storage:
            expected_packet = 1 

            while True:
                try:
                    packet = self.receive_packet(timeout=TIMEOUT)
                except self.timeout_error_class():
                    print("Timeout esperando paquetes. Terminando recepción.")
                    break

                # Si recibimos el paquete "END", terminamos
                if packet.payload() == b"END":
                    print("Paquete END recibido. Finalizando recepción.")
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
                sack_message = f"SACK {' '.join(map(str, sorted(acked_packets)))}"
                self.send_message(sack_message.encode())
                print(f"Enviado SACK con acks: {acked_packets}")

        
    def receive_sack(self, timeout=None):
        try:
            raw_sack, address = self.connection.recvfrom(1024)
            print(f"Recibido raw SACK desde {address}: {raw_sack}")
            sack_data = raw_sack.decode().replace("SACK", "").strip()
            print(f"Datos SACK decodificados: {sack_data}")
            acked_packets = set(map(int, sack_data.split()))
            return {"acks": acked_packets}
        except Exception as e:
            print(f"Error recibiendo SACK: {e}")
            return {"acks": set()}
