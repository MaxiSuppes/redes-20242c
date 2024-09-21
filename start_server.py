import argparse
import os
import socket


DEFAULT_STORAGE_DIRECTORY = './storage'


def show_help():
    print("Usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]\n<command description>")
    print("\nArguments (optional):")
    print("  -h, --help            Show this help message and exit.")
    print("  -v, --verbose         Increase output verbosity.")
    print("  -q, --quiet           Decrease output verbosity.")
    print("  -H, --host            Server IP address.")
    print("  -p, --port            Server port.")
    print("  -s, --storage         Storage dir path.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor de almacenamiento de archivos.", add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-H', '--host', default='10.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-s', '--storage', default=DEFAULT_STORAGE_DIRECTORY)

    return parser.parse_args()


def start_server(host, port, storage_directory):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"Servidor escuchando en {host}:{port}")

    while True:
        data, client_address = server_socket.recvfrom(1024)
        command = data.decode()
        print(f"Comando recibido: {command} desde {client_address}")

        if command.startswith('upload'):
            filename = command.split()[1]
            print(f"Se va a recibir el archivo {filename}")
            receive_file(server_socket, client_address, filename, storage_directory)
        elif command.startswith('download'):
            filename = command.split()[1]
            print(f"Se solicitó el archivo {filename}")
            send_file(server_socket, client_address, filename, storage_directory)


def receive_file(sock, client_address, filename, storage_directory):
    file_path = os.path.join(storage_directory, filename)

    with open(file_path, 'wb') as f:
        while True:
            data, address = sock.recvfrom(1024)
            if data == b'END':
                break
            f.write(data)
            sock.sendto(b'ACK', client_address)

    print(f"Archivo {filename} guardado en {storage_directory}")


def send_file(sock, client_address, filename, storage_directory):
    file_path = os.path.join(storage_directory, filename)

    if not os.path.exists(file_path):
        print(f"Archivo {filename} no encontrado")
        # TODO: Enviar mensaje de error al cliente?
        return

    print(f"Enviando archivo {filename} a {client_address}")

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sock.sendto(data, client_address)
            ack, address = sock.recvfrom(1024)
            if ack != b'ACK':
                print("No se recibió un ACK. Reenviando paquete.")
                f.seek(-1024, os.SEEK_CUR)  # Retrocede el puntero del archivo para volver a enviar el paquete

    sock.sendto(b'END', client_address)
    print(f"Se envió el archivo {filename} correctamente")


def main():
    args = parse_arguments()
    print(args)
    if hasattr(args, 'help') and args.help:
        show_help()
        return

    start_server(args.host, args.port, args.storage)


if __name__ == "__main__":
    main()
