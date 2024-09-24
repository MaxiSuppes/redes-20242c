import os
import socket

PACKET_SIZE = 1024


class Downloader:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def download(self, download_directory, filename):
        self.sock.sendto(f"download {filename}".encode(), (self.host, self.port))

        file_path = os.path.join(download_directory, filename)
        expected_packet = 0
        with open(file_path, 'wb') as f:
            while True:
                data, address = self.sock.recvfrom(PACKET_SIZE)
                if data == b'END':
                    break

                f.write(data)
                self.sock.sendto(f'ACK_{expected_packet}'.encode(), (self.host, self.port))
                print(f"Enviado ACK {expected_packet} al servidor.")
                expected_packet += 1

        print(f"Archivo {filename} descargado en {download_directory}")
