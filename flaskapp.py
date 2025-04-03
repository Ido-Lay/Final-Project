import socket
import json
from typing import Final

from flask import Flask, request
import folium
from Event import Event, Risk
from events_db import EventsDAL

SERVER_IP: Final[str] = '127.0.0.1'
SERVER_PORT: Final[int] = 6000

EventsDAL.start_cleanup_thread()

app = Flask(__name__)


def add_all_markers_to_ui(events: list[Event], m):
    for event in events:
        print(
            f"Adding marker: {event.event_name}, Lat: {event.latitude}, Long: {event.longitude}, Risk: {event.risk}")  # Debugging
        if event.risk == 0:
            icon_color = 'red'
        elif event.risk == 1:
            icon_color = 'green'
        elif event.risk == 2:
            icon_color = 'blue'
        else:
            icon_color = 'black'
            # TODO handle it

        folium.Marker(
            location=[event.latitude, event.longitude],
            popup=event.event_name,
            icon=folium.Icon(color=icon_color, icon="info-sign"),
        ).add_to(m)


def send_marker(event_json: dict):
    event = Event.from_dict(event_json)
    event.print_event()

    try:
        client_socket = socket.socket()  # instantiate
        client_socket.connect((SERVER_IP, SERVER_PORT))  # connect to the server
        if event.risk == Risk.DANGER:
            client_socket.send(json.dumps(event_json).encode('utf-8'))  # send message
        else:
            EventsDAL.insert_event(event)

    except Exception as ex:
        print(f"Error sending data: {ex}")

    return "Sent successfully"


@app.route("/api/all_markers")
def get_all_markers() -> list[dict]:
    all_markers = EventsDAL.fetch_all_coordinates()
    serialized_markers = [marker.to_dict() for marker in all_markers]
    return serialized_markers


@app.route("/api/get_marker", methods=['POST'])
def get_marker():
    event_json = request.json
    return send_marker(event_json)


@app.route("/")
def map_with_markers() -> str:
    m = folium.Map(location=[32.0, 35.0], zoom_start=8, world_copy_jump=True)  # Adjust center and zoom level as needed
    events = EventsDAL.fetch_all_coordinates()
    add_all_markers_to_ui(events, m)
    return m._repr_html_()


if __name__ == "__main__":
    app.run(debug=True)
