import socket
import threading
from ..Common.EveMapSocket import EveMapServerSocket,EveMapConnSocket, MessageType, PacketType
from dal import EveMapDAL
HOST = '0.0.0.0'

def start_server_socket_loop(_:int):
    server_socket = EveMapServerSocket()
    server_socket.bind_and_listen(HOST)

    print(f"Server listening on {HOST}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected to {addr}")
        client_thread = threading.Thread(target=handle_client, args=(conn,))
        client_thread.daemon = True
        client_thread.start()


def handle_client(conn_socket:EveMapConnSocket):
    while True:
        message, message_type, packet_type = conn_socket.recv_command()

        if message_type == MessageType.FETCH_USERS and packet_type == PacketType.REQUEST:
            conn_socket.handle_user_command(EveMapDAL.get_all_users())

        elif message_type == MessageType.FETCH_EVENTS and packet_type == PacketType.REQUEST:
            conn_socket.handle_event_command(EveMapDAL.fetch_all_coordinates_from_admin_events())

        elif message_type == MessageType.INSERT_EVENT and packet_type == PacketType.REQUEST:
            conn_socket.handle_insert_event_command(message)

        elif message_type == MessageType.INSERT_ADMIN_EVENT and packet_type == PacketType.REQUEST:
            conn_socket.handle_insert_admin_event_command(message)

        elif message_type == MessageType.DELETE_EVENT and packet_type == PacketType.REQUEST:
            conn_socket.handle_delete_event_command(message)

        elif message_type == MessageType.DELETE_ADMIN_EVENT and packet_type == PacketType.REQUEST:
            conn_socket.handle_delete_admin_event_command(message)

        elif message_type == MessageType.SEND_MAIL and packet_type == PacketType.REQUEST:
            conn_socket.handle_send_email_command(message)

        elif message_type == MessageType.CHECK_MAIL and packet_type == PacketType.REQUEST:
            conn_socket.handle_check_email_command()

        else:
            print(f"Bad packet {message=} {message_type=} {packet_type=}")






