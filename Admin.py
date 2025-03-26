import socket
import json
from EventClass import Event
from db_admin import DbAdminActions

db_mouse = DbAdminActions()

"""HOST = "127.0.0.1"
PORT = 6000

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
                    break  # Exit inner loop on error, but keep server running"""


host = '0.0.0.0'
port = 6002  # initiate port no above 1024

server_socket = socket.socket()  # get instance
# look closely. The bind() function takes tuple as argument
server_socket.bind((host, port))  # bind host address and port together

# configure how many client the server can listen simultaneously
server_socket.listen(2)
print('accepting')
conn, address = server_socket.accept()  # accept new connection
print("Connection from: " + str(address))
while True:
    # receive data stream. it won't accept data packet greater than 1024 bytes
    data = conn.recv(1024).decode()
    if not data:
        # if data is not received break
        break
    print("from connected user: " + str(data))
    event_data = json.loads(data)
    event = Event.from_dict(event_data)
    db_mouse.insert_event(event)
    conn.send(data.encode())  # send data to the client
    conn.close()
    conn, address = server_socket.accept()  # accept new connection


