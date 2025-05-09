from evemap_base_socket import EveMapBaseSocket
from packet import Packet, MessageType, PacketType
import json
from ...Server.User import User
from ...Server.Event import Event


class EveMapClientSocket(EveMapBaseSocket):
    def get_users_command(self) -> list[User]:
        self.__send_command(b'', MessageType.FETCH_USERS, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.FETCH_USERS and packet_type == PacketType.REPLY):
            print('Bad packet')
            return

        user_list_json = json.loads(message.decode())
        return [User.from_dict(user_json) for user_json in user_list_json]

    def get_events_command(self) -> list[Event]:
        self.__send_command(b'', MessageType.FETCH_EVENTS, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.FETCH_EVENTS and packet_type == PacketType.REPLY):
            print('Bad packet')
            return

        event_list_json = json.loads(message.decode())
        return [Event.from_dict(event_json) for event_json in event_list_json]

    def insert_event_command(self, event: Event) -> bool:
        self.__send_command(json.dumps(event).encode(), MessageType.INSERT_EVENT, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.INSERT_EVENT and packet_type == PacketType.REPLY):
            print('Bad packet')
            return False

        if message.decode() == "1": return True
        if message.decode() == "0": return False

    def insert_admin_event_command(self, event: Event) -> bool:
        self.__send_command(json.dumps(event).encode(), MessageType.INSERT_ADMIN_EVENT, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.INSERT_ADMIN_EVENT and packet_type == PacketType.REPLY):
            print('Bad packet')
            return False

        if message.decode() == "1": return True
        if message.decode() == "0": return False

    def delete__event_command(self, db_id: int) -> bool:
        self.__send_command((str(db_id)).encode(), MessageType.DELETE_EVENT, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.DELETE_EVENT and packet_type == PacketType.REPLY):
            print('Bad packet')
            return False

        if message.decode() == "1": return True
        if message.decode() == "0": return False

    def delete_admin_event_command(self, db_id: int) -> bool:
        self.__send_command((str(db_id)).encode(), MessageType.DELETE_ADMIN_EVENT, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.DELETE_ADMIN_EVENT and packet_type == PacketType.REPLY):
            print('Bad packet')
            return False

        if message.decode() == "1": return True
        if message.decode() == "0": return False
