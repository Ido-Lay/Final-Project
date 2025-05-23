import os
import socket
from typing import Optional

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
        packet.update_message(self.encryptor.encrypt(packet.message))
        self.tcp_socket.send(packet.to_bytes())

    def recv_command(self) -> Optional[tuple[bytes, MessageType, PacketType]]:
        raw_data_length = self.tcp_socket.recv(Packet.get_data_length_field_size())
        if raw_data_length == b'':
            return None

        data_length = int.from_bytes(raw_data_length)
        packet_type = PacketType(int.from_bytes(self.tcp_socket.recv(Packet.get_packet_type_field_size())))
        message_type = MessageType(int.from_bytes(self.tcp_socket.recv(Packet.get_message_type_field_size())))
        encrypted_message = self.tcp_socket.recv(data_length)
        message = self.encryptor.decrypt(encrypted_message)
        return message, message_type, packet_type


