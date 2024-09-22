import os
import socket


class Uploader:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def upload_file(self, source_directory, filename):
        file_path = os.path.join(source_directory, filename)
        if not os.path.exists(file_path):
            print(f"Archivo {filename} no encontrado")
            return

        self.sock.sendto(f"upload {filename}".encode(), (self.host, self.port))
        # TODO: Acá no habría que esperar el ack del servidor antes de empezar a recibir el archivo?
        print(f"Subiendo archivo {filename} al servidor")

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.sock.sendto(data, (self.host, self.port))
                ack, address = self.sock.recvfrom(1024)
                if ack != b'ACK':
                    print("No se recibió ACK, reenviando bloque")
                    f.seek(-1024, os.SEEK_CUR)

        self.sock.sendto(b'END', (self.host, self.port))
        print(f"Archivo {filename} subido correctamente")
