from evemap_base_socket import EveMapBaseSocket
from packet import Packet, MessageType, PacketType
import json


class EveMapClientSocket(EveMapBaseSocket):
    def get_users_command(self) -> list[User]:
        self.__send_command(b'', MessageType.FETCH_USERS, PacketType.REQUEST)
        message, message_type, packet_type = self.__recv_command()

        if not (message_type == MessageType.FETCH_USERS and packet_type == PacketType.REPLY):
            print('Bad packet')
            return

        user_list_json = json.loads(message.decode())
        return [User.from_dict(user_json) for user_json in user_list_json]
