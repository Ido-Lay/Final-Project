import socket

from .eve_packet import MessageType, Packet, PacketType


class EveMapBaseSocket:
    tcp_socket: socket.socket

    def __init__(self) -> None:
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def close(self) -> None:
        self.tcp_socket.close()

    def send_command(self, data: bytes, message_type: MessageType, packet_type: PacketType):
        packet = Packet.build_packet(data, message_type, packet_type)
        self.tcp_socket.send(packet.to_bytes())

    def recv_command(self) -> tuple[bytes, MessageType, PacketType]:
        data_length = int.from_bytes(self.tcp_socket.recv(Packet.get_data_length_field_size()))
        packet_type = PacketType(int.from_bytes(self.tcp_socket.recv(Packet.get_packet_type_field_size())))
        message_type = MessageType(int.from_bytes(self.tcp_socket.recv(Packet.get_message_type_field_size())))
        message = self.tcp_socket.recv(data_length)
        return message, message_type, packet_type
