import socket
import json
from typing import Final
from flask import Flask, request, render_template_string
import folium
from Event import Event, Risk
from events_db import EventsDAL
from flask_login import LoginManager
from flask import request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required
from User import User
import secrets
from geopy.geocoders import Nominatim


SERVER_IP: Final[str] = '127.0.0.1'
SERVER_PORT: Final[int] = 6000

EventsDAL.start_cleanup_thread()

app = Flask(__name__)


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)



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

app.secret_key = secrets.token_hex(32)
@login_manager.user_loader
def load_user(user_id):
    return EventsDAL.get_user_by_email(user_id)  # Should return a User object or None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = EventsDAL.get_user_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("map_with_markers"))
        else:
            flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/report", methods=["GET", "POST"])
@login_required
def report_event():
    ...

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']

        # Get the address as a dictionary
        address = {"street": street, "city": city, "state": state}

        # Create the user object
        user = User(name, home_address=address, mail_address=email, password=password)

        # Add the user to the simulated database (replace with actual database insert)
        EventsDAL.insert_user(user)

        return redirect(url_for('login'))

    return render_template('signup.html')


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

@app.route("/submit")
def submit_event():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Submit an Event</title>
        <style>
            #map {
                width: 100%;
                height: 90vh;
            }
            .leaflet-popup-content {
                width: 200px !important;
            }
        </style>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    </head>
    <body>
        <h2>Submit an Event</h2>
        <p>Click anywhere on the map to report an event</p>
        <div id="map"></div>

        <script>
            // Create map
            let map = L.map('map').setView([32.0, 35.0], 6);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);

            // Auto center on user location
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(pos => {
                    let lat = pos.coords.latitude;
                    let lon = pos.coords.longitude;
                    map.setView([lat, lon], 13);
                }, err => {
                    console.warn("Geolocation failed:", err);
                });
            }

            // Handle map click
            map.on('click', function(e) {
                let lat = e.latlng.lat;
                let lng = e.latlng.lng;

                let popupContent = `
                    <form id="eventForm">
                        <label>Event Name:</label><br>
                        <input type="text" id="eventName" required><br>
                        <label>Risk Level:</label><br>
                        <select id="riskLevel">
                            <option value="0">DANGER</option>
                            <option value="1">GOOD</option>
                            <option value="2">NATURAL</option>
                        </select><br><br>
                        <button type="submit">Submit</button>
                    </form>
                `;

                let popup = L.popup()
                    .setLatLng([lat, lng])
                    .setContent(popupContent)
                    .openOn(map);

                // Wait for form submission
                setTimeout(() => {
                    document.getElementById("eventForm").addEventListener("submit", function(event) {
                        event.preventDefault();
                        let name = document.getElementById("eventName").value;
                        let risk = parseInt(document.getElementById("riskLevel").value);

                        fetch('/api/get_marker', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                identity: 0,
                                event_name: name,
                                latitude: lat,
                                longitude: lng,
                                risk: risk,
                                region: "Unknown",
                                city: "Unknown"
                            })
                        }).then(res => res.text())
                          .then(data => {
                              alert("Event submitted!");
                              map.closePopup();
                          })
                          .catch(err => alert("Error submitting event: " + err));
                    });
                }, 100);
            });
        </script>
    </body>
    </html>
    """)



if __name__ == "__main__":
    app.run(debug=True)
