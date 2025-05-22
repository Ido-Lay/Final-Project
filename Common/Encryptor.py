from cryptography.fernet import Fernet
from Common.packet_base.eve_packet import Packet


class Encryptor:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt(self, packet: Packet) -> bytes:
        raw_data = packet.to_bytes()
        return self.fernet.encrypt(raw_data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)

