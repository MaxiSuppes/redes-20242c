import pickle

class Packet:
    def __init__(self) -> None:
        self.seq_numer: int
        self.is_ACK: bool
        self.payload: bytes
        self.length: int

    def __init__(self, seq_number: int, is_ACK: bool, payload: bytes) -> None:
        self.seq_number = seq_number
        self.is_ACK = is_ACK
        self.payload = payload
        self.length = len(payload)

    def get_seq_number(self) -> int:
        return self.seq_number
    
    def is_ack(self) -> bool:
        return self.is_ACK
    
    def is_empty(self) ->bool:
        return self.length == 0
    
    def get_payload(self) -> str:
        return str(self.payload)
    
    def get_length(self) -> int:
        return len(self.payload)
    
    def as_bytes(self) -> bytes:
        return pickle.dumps(self)
    
    @staticmethod
    def from_bytes(data: bytes) -> 'Packet':
        return pickle.loads(data)