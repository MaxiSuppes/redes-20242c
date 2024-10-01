import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self._packet_size = int(os.getenv('PACKET_SIZE'))
        self._packet_number_size = int(os.getenv('PACKET_NUMBER_SIZE'))
        self._timeout = int(os.getenv('TIMEOUT'))
        self._server_storage = os.getenv('SERVER_STORAGE')
        self._server_example_file = os.getenv('SERVER_EXAMPLE_FILE')
        self._download_directory = os.getenv('DOWNLOAD_DIRECTORY')
        self._client_example_file = os.getenv('CLIENT_EXAMPLE_FILE')
        self._ack_command = "ACK"
        self._upload_command = "upload"
        self._download_command = "download"
        self._end_file_command = "END"

    def packet_size(self) -> int:
        return self._packet_size

    def packet_number_size(self) -> int:
        return self._packet_number_size

    def timeout(self) -> int:
        return self._timeout

    def server_storage(self) -> str:
        return self._server_storage

    def server_example_file(self) -> str:
        return self._server_example_file

    def download_directory(self) -> str:
        return self._download_directory

    def client_example_file(self) -> str:
        return self._client_example_file

    def ack_command(self) -> str:
        return self._ack_command

    def upload_command(self) -> str:
        return self._upload_command

    def download_command(self) -> str:
        return self._download_command

    def end_file_command(self) -> str:
        return self._end_file_command


settings = Settings()
