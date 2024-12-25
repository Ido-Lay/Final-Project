from flask import Flask, render_template_string
import folium
import sqlite3

app = Flask(__name__)

# Database helper function
def fetch_all_coordinates():
    """Fetch longitude, latitude, and event names from the database."""
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()
    cursor.execute("SELECT long, lat, event_name FROM EVENTS")
    rows = cursor.fetchall()
    connection.close()
    print("Fetching:", len(rows))
    return rows


@app.route("/")
def map_with_markers():
    """Create a map with markers from the database."""
    # Create the base map
    m = folium.Map(location=[32.0, 35.0], zoom_start=8)  # Adjust center and zoom level as needed

    # Fetch coordinates from the database and add markers
    coordinates = fetch_all_coordinates()
    for long, lat, event_name in coordinates:
        folium.Marker(
            location=[lat, long],
            popup=event_name,
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

    # Render the map
    return m.get_root().render()


if __name__ == "__main__":
    app.run(debug=True)
