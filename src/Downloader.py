import os
from packet import Packet
from host import Host

class Downloader(Host):
    def __init__(self, host, port):
        super().__init__(host, port)

    def request_download(self, filename):
        payload = f"download {filename}"
        packet = Packet(0, False, payload)
        self.sock.sendto(packet.as_bytes(), (self.host, self.port))

    def download(self, download_directory, filename):
        self.request_download(filename)

        file_path = os.path.join(download_directory, filename)

        with open(file_path, 'wb') as f:
            while True:
                packet = self.receive_packet()[0]
                if packet.payload == b'END':
                    break
                f.write(packet.payload)
                self.send_ack(packet.seq_number)

        print(f"Archivo {filename} descargado en {download_directory}")
