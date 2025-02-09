import socket
import json
from class_events import Event
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 888  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        event = Event(input("event name: "), int(input("long: ")), int(input("lat: ")), int(input("risk: ")))
        event_data = json.dumps(event.to_dict()).encode()
        s.sendall(event_data)
