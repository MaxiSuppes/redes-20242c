import argparse
from src.Server import Server
from utils.utils import show_help


DEFAULT_STORAGE_DIRECTORY = './storage'

HELP_LINES = [
    "Usage: start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]\n<command description>",
    "\nArguments (optional):",
    "  -h, --help            Show this help message and exit.",
    "  -v, --verbose         Increase output verbosity.",
    "  -q, --quiet           Decrease output verbosity.",
    "  -H, --host            Server IP address.",
    "  -p, --port            Server port.",
    "  -s, --storage         Storage dir path."
]


def get_params():
    parser = argparse.ArgumentParser(description="Servidor de almacenamiento de archivos.", add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-H', '--host', default='10.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-s', '--storage', default=DEFAULT_STORAGE_DIRECTORY)

    return parser.parse_args()


def main():
    params = get_params()
    if hasattr(params, 'help') and params.help:
        show_help(HELP_LINES)

    server = Server(params.host, params.port, params.storage)
    server.start()


if __name__ == "__main__":
    main()
