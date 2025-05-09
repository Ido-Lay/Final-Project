import socket
import json
from typing import Final
from flask import Flask, request, render_template_string
import folium
from Event import Event, Risk
from dal import EveMapDAL
from flask_login import LoginManager
from flask import request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required
from User import User
import secrets
from geopy.geocoders import Nominatim

HOST_IP: Final[str] = '0.0.0.0'
HOST_SOCKET_PORT: Final[int] = 6000
HOST_FLASK_PORT: Final[int] = 5000

EveMapDAL.start_cleanup_thread()

app = Flask(__name__)


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


def add_all_markers_to_ui(events: list[Event], m):
    for event in events:
        print(
            f"Adding marker: {event.event_name}, Lat: {event.latitude}, Long: {event.longitude}, Risk: {event.risk}"
        )  # Debugging
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
        client_socket.connect((HOST_IP, HOST_SOCKET_PORT))  # connect to the server
        if event.risk == Risk.DANGER:
            client_socket.send(json.dumps(event_json).encode('utf-8'))  # send message
        else:
            EveMapDAL.insert_event(event)

    except Exception as ex:
        print(f"Error sending data: {ex}")

    return "Sent successfully"


app.secret_key = secrets.token_hex(32)


@login_manager.user_loader
def load_user(user_id):
    return EveMapDAL.get_user_by_email(user_id)  # Should return a User object or None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = EveMapDAL.get_user_by_email(email)
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
def report_event(): ...


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        street = request.form["street"]
        city = request.form["city"]
        state = request.form["state"]

        # Check if user already exists
        existing_user = EveMapDAL.get_user_by_email(email)
        if existing_user:
            return render_template("signup_error.html", email=email)

        # If new user, proceed to create
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="signup_app")
        location = geolocator.geocode(f"{street}, {city}, {state}, Israel")
        if location is None:
            flash("Could not find the location. Please enter a valid address.")
            return redirect(url_for("signup"))

        user = User(
            name=name,
            mail_address=email,
            password=password,
            home_address={"longitude": location.longitude, "latitude": location.latitude},
        )

        EveMapDAL.insert_user(user)
        flash("Account created successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/api/all_markers")
def get_all_markers() -> list[dict]:
    city = request.args.get("city")
    region = request.args.get("region")
    risk = request.args.get("risk", type=int)

    all_markers = EveMapDAL.fetch_all_coordinates_from_events(city=city, region=region, risk=risk)
    return [m.to_dict() for m in all_markers]


@app.route("/api/get_marker", methods=['POST'])
def get_marker():
    event_json = request.json
    return send_marker(event_json)


@app.route("/")
@login_required
def map_with_markers():
    m = folium.Map(location=[32.0, 35.0], zoom_start=8)
    events = EveMapDAL.fetch_all_coordinates_from_events()
    add_all_markers_to_ui(events, m)
    map_html = m._repr_html_()

    cities = EveMapDAL.get_unique_cities()
    regions = EveMapDAL.get_unique_regions()

    return render_template("map_view.html", map_html=map_html, cities=cities, regions=regions)


@app.route("/submit")
def submit_event():
    return render_template("submit_event.html")


@app.route("/api/filters")
def get_filter_options():
    cities = EveMapDAL.get_unique_cities()
    regions = EveMapDAL.get_unique_regions()
    return {"cities": cities, "regions": regions}


if __name__ == "__main__":
    app.run(host=HOST_IP, port=HOST_FLASK_PORT, debug=True)
