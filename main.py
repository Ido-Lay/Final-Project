import sqlite3
from datetime import datetime, timedelta
import threading
import time
import schedule
import database
import socket
import json
from class_events import Event

HOST = "127.0.0.1"
PORT = 888

if __name__ == '__main__':
    sqlite3.register_adapter(datetime, database.adapt_datetime)
    sqlite3.register_converter("DATETIME", database.convert_datetime)
    database.make_database()
    database.start_cleanup_thread()
    count = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                if data:
                    event_data = json.loads(data.decode())
                    event = Event.from_dict(event_data)
                    database.insert_event(event)
                elif data == b"close":
                    conn.close()