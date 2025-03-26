import socket
import json
from Event import Event
from db_admin import DbAdminActions

db_mouse = DbAdminActions()

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
