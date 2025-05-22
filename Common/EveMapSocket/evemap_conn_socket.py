import json
import socket

from .evemap_base_socket import EveMapBaseSocket
from Server.user import User
from Common.packet_base.eve_packet import MessageType, PacketType
from Server.event import Event
from Server.eve_map_dal import EveMapDAL
from Server.mail import Mail


class EveMapConnSocket(EveMapBaseSocket):
    def __init__(self, conn_socket: socket.socket):
        super().__init__()
        self.tcp_socket = conn_socket

    def handle_user_command(self, user_list: list[User]):
        user_list_json = json.dumps([user.to_dict() for user in user_list]).encode()
        self.send_command(user_list_json, MessageType.FETCH_USERS, PacketType.REPLY)

    def handle_event_command(self, event_list: list[Event]):
        event_list_json = json.dumps([event.to_dict() for event in event_list]).encode()
        self.send_command(event_list_json, MessageType.FETCH_EVENTS, PacketType.REPLY)

    def handle_insert_event_command(self, message: bytes):
        event = Event.from_dict(json.loads(message.decode()))
        if EveMapDAL.insert_event(event):
            self.send_command(b'1', MessageType.INSERT_EVENT, PacketType.REPLY)
        else:
            self.send_command(b'0', MessageType.INSERT_EVENT, PacketType.REPLY)

    def handle_insert_admin_event_command(self, message: bytes):
        event = Event.from_dict(json.loads(message.decode()))
        if EveMapDAL.insert_event(event):
            self.send_command(b'1', MessageType.INSERT_ADMIN_EVENT, PacketType.REPLY)
        else:
            self.send_command(b'0', MessageType.INSERT_ADMIN_EVENT, PacketType.REPLY)

    def handle_delete_event_command(self, message: bytes):
        if EveMapDAL.delete_event(int(message.decode())):
            self.send_command(b'1', MessageType.DELETE_EVENT, PacketType.REPLY)
        else:
            self.send_command(b'0', MessageType.DELETE_EVENT, PacketType.REPLY)

    def handle_delete_admin_event_command(self, message: bytes):
        if EveMapDAL.delete_admin_event(int(message.decode())):
            self.send_command(b'1', MessageType.DELETE_ADMIN_EVENT, PacketType.REPLY)
        else:
            self.send_command(b'0', MessageType.DELETE_ADMIN_EVENT, PacketType.REPLY)

    def handle_send_email_command(self, message: bytes):
        message = json.loads(message.decode())
        event: Event = Event.from_dict(message)
        user: User = User.from_dict(message)

        if Mail.send_email(user, event):
            self.send_command(b'1', MessageType.SEND_MAIL, PacketType.REPLY)
        else:
            self.send_command(b'0', MessageType.SEND_MAIL, PacketType.REPLY)

    def handle_check_email_command(self):
        result_message = Mail.check_email(EveMapDAL.fetch_all_coordinates_from_admin_events())
        self.send_command(result_message.encode(), MessageType.CHECK_MAIL, PacketType.REPLY)
