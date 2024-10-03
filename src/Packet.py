import struct

from src.settings import settings


class Packet:
    def __init__(self, sequence_number: int, payload: bytes) -> None:
        self._sequence_number = sequence_number
        self._payload = payload

    def sequence_number(self) -> int:
        return self._sequence_number

    def sack_string_ranges(self):
        # SACK 2-3, 4-6, 8-10 -> [2-3, 4-6, 8-10]
        if self.decoded_payload() == settings.sack_command():
            return []
        string_ranges = self.decoded_payload().split("SACK ")[1]
        return string_ranges.split(", ")

    def payload(self) -> bytes:
        return self._payload

    def decoded_payload(self) -> str:
        return self._payload.decode()

    def is_an_ack(self):
        return self.decoded_payload() == settings.ack_command()

    def is_a_sack(self):
        return self.decoded_payload().startswith(settings.sack_command())

    def is_valid_ack(self, sequence_number: int) -> bool:
        return self.is_an_ack() and self.sequence_number() == sequence_number

    def as_bytes(self) -> bytes:
        header = struct.pack('>I', self._sequence_number)  # >I empaqueta un unsigned int de 4 bytes en big-endian
        return header + self._payload

    @staticmethod
    def from_bytes(raw_data: bytes) -> 'Packet':
        sequence_number = struct.unpack('>I', raw_data[:4])[0]
        file_chunk = raw_data[4:]
        return Packet(sequence_number, file_chunk)