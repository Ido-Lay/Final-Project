import os
import socket
from Common.packet_base.eve_packet import MessageType, Packet, PacketType
from dotenv import load_dotenv
from Common.encryptor import Encryptor

load_dotenv()
key = os.getenv("KEY")


class EveMapBaseSocket:
    tcp_socket: socket.socket
    encryptor: Encryptor

    def __init__(self) -> None:
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.encryptor = Encryptor(key.encode())

    def close(self) -> None:
        self.tcp_socket.close()

    def send_command(self, data: bytes, message_type: MessageType, packet_type: PacketType):
        packet = Packet.build_packet(data, message_type, packet_type)
        encrypted_packet = self.encryptor.encrypt(packet)

        length_bytes = len(encrypted_packet).to_bytes(4, byteorder='big')
        self.tcp_socket.send(length_bytes + encrypted_packet)

    def recv_command(self) -> tuple[bytes, MessageType, PacketType]:
        length_bytes = self.tcp_socket.recv(4)
        if not length_bytes:
            raise ConnectionError("Socket closed or no data received.")

        encrypted_length = int.from_bytes(length_bytes, byteorder="big")

        encrypted_data = b''
        while len(encrypted_data) < encrypted_length:
            chunk = self.tcp_socket.recv(encrypted_length - len(encrypted_data))
            if not chunk:
                raise ConnectionError("Incomplete encrypted data received.")
            encrypted_data += chunk

        decrypted_data = self.encryptor.decrypt(encrypted_data)
        packet = Packet.from_bytes(decrypted_data)
        return packet.message, packet.message_type, packet.packet_type


