import socket
import os

import argparse
from datetime import datetime


DEFAULT_FILE_NAME = f'file_{datetime.now().strftime("%Y%m%d%H%M%S")}'


def show_help():
    print("Usage : upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]\n"
          "<command description>")
    print("\nArguments (optional):")
    print("  -h, --help            Show this help message and exit.")
    print("  -v, --verbose         Increase output verbosity.")
    print("  -q, --quiet           Decrease output verbosity.")
    print("  -H, --host            Server IP address.")
    print("  -p, --port            Server port.")
    print("  -s, --src             Source file path.")
    print("  -n, --name            File name.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Aplicación para subir archivos.", add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-H', '--host', default='10.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-s', '--src', default=os.getcwd())
    parser.add_argument('-n', '--name', default=DEFAULT_FILE_NAME)

    return parser.parse_args()


def start_client():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def upload_file(client_socket, server_host, server_port, filename):
    client_socket.sendto(f"upload {filename}".encode(), (server_host, server_port))  # Envia al server el comando upload

    if not os.path.exists(filename):
        print(f"Archivo {filename} no encontrado")
        return

    print(f"Subiendo archivo {filename} al servidor")

    with open(filename, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendto(data, (server_host, server_port))
            ack, address = client_socket.recvfrom(1024)
            if ack != b'ACK':
                print("No se recibió ACK, reenviando bloque")
                f.seek(-1024, os.SEEK_CUR)  # Retrocede el puntero del archivo para volver a enviar el paquete

    client_socket.sendto(b'END', (server_host, server_port))
    print(f"Archivo {filename} subido correctamente")


def main():
    args = parse_arguments()
    print(args)
    if hasattr(args, 'help') and args.help:
        show_help()
        return

    client_socket = start_client()
    upload_file(client_socket, args.host, args.port, args.src)


if __name__ == "__main__":
    main()

