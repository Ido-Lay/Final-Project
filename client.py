import socket
import json
from class_events import Event
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 888  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        try:
            lat = float(input("Enter latitude: "))
            long = float(input("Enter longitude: "))
            if not (-90 <= lat <= 90 and -180 <= long <= 180):
                print("Invalid coordinates! Please enter valid latitude (-90 to 90) and longitude (-180 to 180).")
                continue
            risk = int(input("Enter risk level (0-2): "))
            if risk not in [0, 1, 2]:
                print("Invalid risk level! Please enter 0, 1, or 2.")
                continue
        except ValueError:
            print("Invalid input! Please enter numbers only.")
            continue

        event = Event(input("Event name: "), long, lat, risk)
        event_data = json.dumps(event.to_dict()).encode()
        s.sendall(event_data)
