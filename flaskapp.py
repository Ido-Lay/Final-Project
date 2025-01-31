import http

from flask import Flask, render_template_string, request
import folium
import sqlite3
from class_events import Event

app = Flask(__name__)


def fetch_all_coordinates():
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()
    cursor.execute("SELECT event_name, long, lat, region, city, risk FROM EVENTS")
    rows = cursor.fetchall()
    connection.close()

    events: list[Event] = []
    for row in rows:
        e = Event(*row)
        events.append(e)

    return events


def add_all_markers_to_ui(events, m):
    for event in events:
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


@app.route("/api/all_markers")
def get_all_markers():
    all_markers = fetch_all_coordinates()
    serialized_markers = [marker.to_dict() for marker in all_markers]
    return serialized_markers


@app.route("/api/add_marker", methods=['POST'])
def add_marker():
    json_data = request.json
    event = Event.from_dict(json_data)

    return 'Added successfully'


@app.route("/")
def map_with_markers():
    m = folium.Map(location=[32.0, 35.0], zoom_start=8)  # Adjust center and zoom level as needed
    events = fetch_all_coordinates()
    add_all_markers_to_ui(events, m)
    return m.get_root().render()


if __name__ == "__main__":
    app.run(debug=True)
