import json
import socket
from typing import Optional

from evemap_base_socket import EveMapBaseSocket
from ...Server.User import User
from packet import Packet, MessageType, PacketType
from ...Server.Event import Event
from ...Server.dal import EveMapDAL
from ...Server.Mail import send_email


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
        if EveMapDAL.insert_event(event):
            self.__send_command(b'1', MessageType.INSERT_EVENT, PacketType.REPLY)
        else:
            self.__send_command(b'0', MessageType.INSERT_EVENT, PacketType.REPLY)

    def handle_insert_admin_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.INSERT_ADMIN_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        event = Event.from_dict(json.loads(message.decode()))
        if EveMapDAL.insert_event(event):
            self.__send_command(b'1', MessageType.INSERT_ADMIN_EVENT, PacketType.REPLY)
        else:
            self.__send_command(b'0', MessageType.INSERT_ADMIN_EVENT, PacketType.REPLY)

    def handle_delete_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.DELETE_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        if EveMapDAL.delete_event(int(message.decode())):
            self.__send_command(b'1', MessageType.DELETE_EVENT, PacketType.REPLY)
        else:
            self.__send_command(b'0', MessageType.DELETE_EVENT, PacketType.REPLY)

    def handle_delete_admin_event_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.DELETE_ADMIN_EVENT and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        if EveMapDAL.delete_admin_event(int(message.decode())):
            self.__send_command(b'1', MessageType.DELETE_ADMIN_EVENT, PacketType.REPLY)
        else:
            self.__send_command(b'0', MessageType.DELETE_ADMIN_EVENT, PacketType.REPLY)

    def handle_send_email_command(self) -> Optional[bytes]:
        message, message_type, packet_type = self.__recv_command()
        if not (message_type == MessageType.SEND_MAIL and packet_type == PacketType.REQUEST):
            print('Bad packet')
            return

        message = json.loads(message.decode())
        user = message[0]
        event = message[1]

        if send_email(user, event):
            self.__send_command(b'1', MessageType.SEND_MAIL, PacketType.REPLY)
        else:
            self.__send_command(b'0', MessageType.SEND_MAIL, PacketType.REPLY)
