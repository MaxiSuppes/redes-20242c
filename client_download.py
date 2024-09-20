import argparse
import os
import socket

DEFAULT_DESTINATION_FILE_PATH = 'client_storage'


def show_help():
    print("Usage : download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]\n"
          "<command description>")
    print("\nArguments (optional):")
    print("  -h, --help            Show this help message and exit.")
    print("  -v, --verbose         Increase output verbosity.")
    print("  -q, --quiet           Decrease output verbosity.")
    print("  -H, --host            Server IP address.")
    print("  -p, --port            Server port.")
    print("  -d, --dst             Destination file path.")
    print("  -n, --name            File name.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Aplicación para descargar archivos.", add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-H', '--host', default='10.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-d', '--dst', default=DEFAULT_DESTINATION_FILE_PATH)
    parser.add_argument('-n', '--name', default='')

    return parser.parse_args()


def start_client():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def download_file(client_socket, server_host, server_port, destination_file_path, filename):
    print(f"{server_host}, {server_port}, {filename}")
    client_socket.sendto(f"download {filename}".encode(),
                         (server_host, server_port))  # Envía al server el comando download

    print(f"Descargando archivo {filename} desde el servidor")

    with open(os.path.join(destination_file_path, filename), 'wb') as f:
        while True:
            data, address = client_socket.recvfrom(1024)
            if data == b'END':
                break
            f.write(data)
            client_socket.sendto(b'ACK', (server_host, server_port))

    print(f"Archivo {filename} descargado correctamente a {destination_file_path}")


def main():
    args = parse_arguments()
    print(args)
    if hasattr(args, 'help') and args.help:
        show_help()
        return

    client_socket = start_client()
    download_file(client_socket, args.host, args.port, args.dst, args.name)


if __name__ == "__main__":
    main()
