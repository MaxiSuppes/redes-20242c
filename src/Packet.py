import struct


class Packet:
    def __init__(self, sequence_number: int, payload: bytes) -> None:
        self._sequence_number = sequence_number
        self._payload = payload

    def sequence_number(self) -> int:
        return self._sequence_number

    def payload(self) -> bytes:
        return self._payload

    def decoded_payload(self) -> str:
        return self._payload.decode()

    def is_an_ack(self):
        return self.decoded_payload() == "ACK"

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