import argparse

from src.Downloader import Downloader
from src.Logger import setup_logging
from src.settings import settings
from src.utils import show_help

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
    parser.add_argument('-d', '--dst', default=settings.download_directory())
    # TODO: Suponemos que el cliente sabe el nombre del archivo?
    parser.add_argument('-n', '--name', default=settings.server_example_file())

    return parser.parse_args()


def main():
    params = get_params()
    if hasattr(params, 'help') and params.help:
        show_help(HELP_LINES)

    setup_logging(params.verbose, params.quiet)

    downloader = Downloader(params.host, params.port)  # Server IP, Server port
    downloader.download(params.dst, params.name)


if __name__ == "__main__":
    main()
