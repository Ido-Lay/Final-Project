import sqlite3
import json
from EventClass import Event
import Utils
from datetime import datetime, timedelta
class DbAdminActions():
    def make_database(self):
        connection = sqlite3.connect('Pending.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS EVENTS")
        event_table = """ CREATE TABLE EVENTS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT,
                    long REAL,
                    lat REAL,
                    risk INT,
                    region TEXT,
                    city TEXT,
                    created_at DATETIME
                ); """
        cursor.execute(event_table)
        connection.commit()
        connection.close()

    def insert_event(self, event):
        connection = sqlite3.connect('Pending.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        new_event = Utils.get_location_info(event)

        if new_event is None:
            print(f"Warning: Could not fetch location info for event {event.event_name}")
            return

        # Debugging: Print the data before insertion
        print(
            f"Inserting event: {new_event.event_name}, {new_event.long}, {new_event.lat}, {new_event.risk}, {new_event.region}, {new_event.city}")

        cursor.execute("""
            INSERT INTO EVENTS (event_name, long, lat, risk, region, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (new_event.event_name, new_event.long, new_event.lat, new_event.risk, new_event.region, new_event.city,
              datetime.now()))
        connection.commit()
        connection.close()


    def fetch_all_events(self):
        connection = sqlite3.connect('Pending.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM EVENTS")
        output = cursor.fetchall()
        connection.close()
        return json.dumps(output, default=str)

    def fetch_all_coordinates(self):
        connection = sqlite3.connect('Pending.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("SELECT event_name, long, lat, risk, region, city FROM EVENTS")
        rows = cursor.fetchall()
        connection.close()

        events: list[Event] = []
        for row in rows:
            e = Event(*row)
            events.append(e)

        return events


