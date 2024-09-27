import os
import socket
import struct

PACKET_SIZE = 1024
PACKET_NUMBER_SIZE = 10  # Con 10 bytes se podrían mandar hasta 9999999999 paquetes


class Downloader:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def download(self, download_directory, filename):
        self.sock.sendto(f"download {filename}".encode(), (self.host, self.port))

        file_path = os.path.join(download_directory, filename)

        with open(file_path, 'wb') as file_to_download:
            last_packet_received = 0  # El 0 representa que se recibió ningún paquete
            while True:
                packet, address = self.sock.recvfrom(PACKET_SIZE + PACKET_NUMBER_SIZE)
                if packet == b"END":
                    break

                packet_number = struct.unpack('>I', packet[:4])[0]
                file_chunk = packet[4:]
                print(f"Paquete recibido: {packet_number}")
                if int(packet_number) != last_packet_received:  # TODO: Pensar si no deberíamos chequear que sea el siguiente paquete (paquetes ordenados)
                    file_to_download.write(file_chunk)
                    last_packet_received = int(packet_number)
                else:
                    print(f"Paquete {packet_number} ya recibido.")

                print(f"Enviando ACK {packet_number} al servidor.")
                self.sock.sendto(f'ACK_{packet_number}'.encode(), (self.host, self.port))

        print(f"Archivo {filename} descargado en {download_directory}")
