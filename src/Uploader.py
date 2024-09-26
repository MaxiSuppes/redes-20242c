import os
from packet import Packet
from host import Host


class Uploader(Host):
    def __init__(self, host, port):
        super().__init__(host, port)

    def request_upload(self, filename):
        payload = f"upload {filename}"
        packet = Packet(0, False, payload)
        self.sock.sendto(packet.as_bytes(), (self.host, self.port))

    def upload_file(self, source_directory, filename):
        file_path = os.path.join(source_directory, filename)
        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            return
        
        self.request_upload(filename)
        # TODO: Acá no habría que esperar el ack del servidor antes de empezar a recibir el archivo?
        print(f"Subiendo archivo {filename} al servidor")

        self.send_file(filename, file_path)