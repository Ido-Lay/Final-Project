import socket
import json
from EventClass import Event
from db_admin import DbAdminActions

HOST = "127.0.0.1"
PORT = 6000

db_mouse = DbAdminActions()
db_mouse.make_database()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing address
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}...")

    while True:
        conn, addr = s.accept()  # Accept new client connection
        print(f"Connected by {addr}")

        with conn:
            while True:
                try:
                    data = conn.recv(4096)
                    if not data:
                        print("Client disconnected.")
                        break  # Go back to accepting a new connection

                    print("Received:", data.decode())
                    event_data = json.loads(data.decode())
                    event = Event.from_dict(event_data)
                    db_mouse.insert_event(event)

                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break  # Exit inner loop on error, but keep server running