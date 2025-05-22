from cryptography.fernet import Fernet


class Encryptor:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        if data:
            return self.fernet.encrypt(data)
        return b''

    def decrypt(self, encrypted_data: bytes) -> bytes:
        if encrypted_data:
            return self.fernet.decrypt(encrypted_data)
        return b''

