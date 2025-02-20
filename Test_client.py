import socket
import json
import time

from EventClass import Event
import random
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 888  # The port used by the server

def manual_tester():
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

def automated_tester():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            time.sleep(1)
            risk = random.randint(0, 3)
            lat = random.uniform(-90.0, 90.0)
            long = random.uniform(-180.0, 180.0)
            event = Event("Test", long, lat, risk)
            event_data = json.dumps(event.to_dict()).encode()
            s.sendall(event_data)

automated_tester()

