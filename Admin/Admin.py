import socket
import json
from Event import Event
from admin_db import AdminDAL
from typing import Final

HOST: Final[str] = '127.0.0.1'
PORT: Final[int] = 6000

server_socket = socket.socket()
server_socket.bind((HOST, PORT))

server_socket.listen(2)
print('accepting')
conn, address = server_socket.accept()
print("Connection from: " + str(address))
while True:
    data = conn.recv(1024).decode()
    if data:
        print("from connected user: " + str(data))
        event_data = json.loads(data)
        event = Event.from_dict(event_data)
        AdminDAL.insert_event(event)
        conn.send(data.encode())
        conn.close()
    conn, address = server_socket.accept()
