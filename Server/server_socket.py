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
        conn_socket.handle_user_command()


