import socket
import json

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 888  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    signal = "fetch all markers"
    s.connect((HOST, PORT))
    s.sendall(signal.encode())
    data = s.recv(4096)
    data = data.decode()
    events = json.loads(data)
    for row in events:
        print(row)
