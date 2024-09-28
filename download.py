import argparse

from src.Downloader import Downloader
from utils.utils import show_help

DEFAULT_DOWNLOAD_DIR = '.'
DEFAULT_FILE_NAME = 'server_storage/ejemplo.txt'

HELP_LINES = [
    "Usage : download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]\n",
    "<command description>",
    "\nArguments (optional):",
    "  -h, --help            Show this help message and exit.",
    "  -v, --verbose         Increase output verbosity.",
    "  -q, --quiet           Decrease output verbosity.",
    "  -H, --host            Server IP address.",
    "  -p, --port            Server port.",
    "  -d, --dst             Destination file path.",
    "  -n, --name            File name."
]


def get_params():
    parser = argparse.ArgumentParser(description="Aplicación para descargar archivos.", add_help=False)

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-H', '--host', default='10.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=12345)
    parser.add_argument('-d', '--dst', default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument('-n', '--name', default='')  # TODO: Suponemos que el cliente sabe el nombre del archivo?

    return parser.parse_args()


def main():
    params = get_params()
    if hasattr(params, 'help') and params.help:
        show_help(HELP_LINES)

    downloader = Downloader(params.host, params.port)  # Server IP, Server port
    downloader.download(params.dst, params.name)


if __name__ == "__main__":
    main()
