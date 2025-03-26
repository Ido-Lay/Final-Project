import http
import socket
import json
from flask import Flask, render_template_string, request
import folium
import sqlite3
from EventClass import Event
from db_web import DataBaseActions

database_mouse = DataBaseActions()
database_mouse.start_cleanup_thread()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing address
try:
    sock.connect(('127.0.0.1', 6002))
except Exception as e:
    print(f"Error connecting to server: {e}")

app = Flask(__name__)


def add_all_markers_to_ui(events, m):
    for event in events:
        print(
            f"Adding marker: {event.event_name}, Lat: {event.lat}, Long: {event.long}, Risk: {event.risk}")  # Debugging
        if event.risk == 0:
            folium.Marker(
                location=[event.lat, event.long],
                popup=event.event_name,
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
        if event.risk == 1:
            folium.Marker(
                location=[event.lat, event.long],
                popup=event.event_name,
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(m)
        if event.risk == 2:
            folium.Marker(
                location=[event.lat, event.long],
                popup=event.event_name,
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(m)


def send_marker(json_data):
    event = Event.from_dict(json_data)
    event.print_event()

    """try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("127.0.0.1", 6002))
            sock.sendall(json.dumps(json_data).encode('utf-8'))  # Send data
            print("Packet sent successfully!")

    except Exception as e:
        print(f"Error sending data: {e}")

    return "Sent successfully"""""
    try:
        host = socket.gethostname()  # as both code is running on same pc
        port = 6002  # socket server port number

        client_socket = socket.socket()  # instantiate
        client_socket.connect((host, port))  # connect to the server
        if event.risk == 0:
            client_socket.send(json.dumps(json_data).encode('utf-8'))  # send message
        else:
            database_mouse.insert_event(event)

    except Exception as e:
        print(f"Error sending data: {e}")

    return "Sent successfully"


@app.route("/api/all_markers")
def get_all_markers():
    all_markers = database_mouse.fetch_all_coordinates()
    serialized_markers = [marker.to_dict() for marker in all_markers]
    return serialized_markers


@app.route("/api/get_marker", methods=['POST'])
def get_marker():
    json_data = request.json
    return send_marker(json_data)


@app.route("/")
def map_with_markers():
    m = folium.Map(location=[32.0, 35.0], zoom_start=8, world_copy_jump=True)  # Adjust center and zoom level as needed
    events = database_mouse.fetch_all_coordinates()
    add_all_markers_to_ui(events, m)
    return m._repr_html_()


@app.route("/test")
def test_map():
    m = folium.Map(location=[32.0, 35.0], zoom_start=8)
    folium.Marker(location=[40.7128, -74.0060], popup="Test Marker").add_to(m)
    return m.get_root().render()


if __name__ == "__main__":
    app.run(debug=True)
