import json
import socket

from evemap_base_socket import EveMapBaseSocket


class EveMapConnSocket(EveMapBaseSocket):
    def __init__(self, conn_socket: socket.socket):
        super().__init__()
        self.tcp_socket = conn_socket

    def handle_user_command(self, user_list: list[User]):
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.FETCH_USERS and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        user_list_json = json.dumps([user.to_dict() for user in user_list]).encode()
        self.__send_command(user_list_json, MessageType.FETCH_USERS, PacketType.REPLY)
