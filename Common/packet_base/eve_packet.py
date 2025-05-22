from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    SEND_MAIL = 0
    CHECK_MAIL = 1
    DELETE_EVENT = 2
    DELETE_ADMIN_EVENT = 3
    INSERT_EVENT = 4
    INSERT_ADMIN_EVENT = 5
    FETCH_EVENTS = 6
    FETCH_USERS = 7


class PacketType(Enum):
    REQUEST = 0
    REPLY = 1


@dataclass
class Packet:
    data_length: int
    packet_type: PacketType
    message_type: MessageType
    message: bytes

    @classmethod
    def build_packet(cls, data: bytes, message_type: MessageType, packet_type: PacketType) -> 'Packet':
        return cls(len(data), packet_type, message_type, data)

    def to_bytes(self) -> bytes:
        return (
            self.data_length.to_bytes(4)
            + self.packet_type.value.to_bytes(1)
            + self.message_type.value.to_bytes(2)
            + self.message
        )

    @staticmethod
    def get_data_length_field_size():
        return 4

    @staticmethod
    def get_packet_type_field_size():
        return 1

    @staticmethod
    def get_message_type_field_size():
        return 2

    @classmethod
    def from_bytes(cls, raw_packet: bytes) -> 'Packet':
        curr_pos = 0

        data_length = int.from_bytes(raw_packet[: Packet.get_data_length_field_size()])
        curr_pos += Packet.get_data_length_field_size()

        packet_type = PacketType(int.from_bytes(raw_packet[curr_pos : curr_pos + Packet.get_packet_type_field_size()]))
        curr_pos += Packet.get_packet_type_field_size()

        message_type = MessageType(
            int.from_bytes(raw_packet[curr_pos : curr_pos + Packet.get_message_type_field_size()])
        )
        curr_pos += Packet.get_message_type_field_size()

        data = raw_packet[curr_pos:]
        return cls(data_length, packet_type, message_type, data)
