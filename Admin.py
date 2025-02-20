import socket
import json
from EventClass import Event

HOST = "127.0.0.1"
PORT = 6000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(4096)
            if data:
                event_data = json.loads(data.decode())
                event = Event.from_dict(event_data)
                event.print_event()