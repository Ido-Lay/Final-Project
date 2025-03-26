import sqlite3
import json
from EventClass import Event
import Utils
from datetime import datetime, timedelta

class DbAdminActions():
    def make_database(self):
        connection = sqlite3.connect('Pending.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        event_table = """ CREATE TABLE EVENTS (
                    id INTEGER,
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
        region_and_city = Utils.get_location_info(event)

        if event.region and event.city is None:
            print(f"Warning: Could not fetch location info for event {event.event_name}")
            return

        # Debugging: Print the data before insertion
        print(
            f"Inserting event: {event.ident}, {event.event_name}, {event.long}, {event.lat}, {event.risk}, {region_and_city[0]}, {region_and_city[1]}")

        cursor.execute("""
            INSERT INTO EVENTS (id, event_name, long, lat, risk, region, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (event.ident, event.event_name, event.long, event.lat, event.risk, region_and_city[0], region_and_city[1],
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
        cursor.execute("SELECT id, event_name, long, lat, risk, region, city FROM EVENTS")
        rows = cursor.fetchall()
        connection.close()

        events: list[Event] = []
        for row in rows:
            e = Event(*row)
            events.append(e)

        return events


