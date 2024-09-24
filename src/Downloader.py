import os
import socket


class Downloader:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def download(self, download_directory, filename):
        self.sock.sendto(f"download {filename}".encode(), (self.host, self.port))

        file_path = os.path.join(download_directory, filename)

        with open(file_path, 'wb') as f:
            while True:
                data, address = self.sock.recvfrom(1024)
                if data == b'END':
                    break
                f.write(data)
                self.sock.sendto(b'ACK', (self.host, self.port))

        print(f"Archivo {filename} descargado en {download_directory}")
