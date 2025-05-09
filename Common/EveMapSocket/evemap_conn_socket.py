import json
import socket
from typing import Optional

from evemap_base_socket import EveMapBaseSocket
from ...Server.User import User
from packet import Packet, MessageType, PacketType
from ...Server.Event import Event
from ...Server.dal import EveMapDAL


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

    def handle_event_command(self, event_list: list[Event]):
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.FETCH_EVENTS and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        event_list_json = json.dumps([event.to_dict() for event in event_list]).encode()
        self.__send_command(event_list_json, MessageType.FETCH_USERS, PacketType.REPLY)

    def handle_insert_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.INSERT_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        event = Event.from_dict(json.loads(message.decode()))
        if EveMapDAL.insert_event(event): return b"1"
        return b"0"

    def handle_insert_admin_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.INSERT_ADMIN_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        event = Event.from_dict(json.loads(message.decode()))
        if EveMapDAL.insert_admin_event(event): return b"1"
        return b"0"

    def handle_delete_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.DELETE_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        if EveMapDAL.delete_event(int(message.decode())): return b"1"
        return b"0"

    def handle_delete_admin_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.DELETE_ADMIN_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        if EveMapDAL.delete_admin_event(int(message.decode())): return b"1"
        return b"0"
