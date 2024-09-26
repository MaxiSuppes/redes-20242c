import os
from src import Packet
from src import Host

class Downloader(Host):
    def __init__(self, host, port):
        super().__init__(host, port)

    def request_download(self, filename):
        payload = f"download {filename}"
        packet = Packet(0, False, payload)
        self.sock.sendto(packet.as_bytes(), (self.host, self.port))

    def download(self, download_directory, filename):
        self.request_download(filename)
        self.receive_file(download_directory, filename)
        print(f"Archivo {filename} descargado en {download_directory}")
