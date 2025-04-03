import sqlite3
import json
from Event import Event
from typing import Final
from datetime import datetime, timedelta
from location_from_coordinates import get_location_from_coordinates

DATABASE_FILENAME: Final[str] = 'admin_side.db'  # TODO change

class AdminDAL():
    @staticmethod
    def creat_database():
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        AdminDAL.create_events_table(cursor)

        connection.commit()
        connection.close()

    @staticmethod
    def create_events_table(cursor):
        event_table = """ CREATE TABLE EVENTS (
                            id INTEGER,
                            event_name TEXT,
                            longitude REAL,
                            latitude REAL,
                            risk INT,
                            region TEXT,
                            city TEXT,
                            created_at DATETIME
                        ); """
        cursor.execute(event_table)

    @staticmethod
    def insert_event(event):
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        region, city = get_location_from_coordinates(event)

        if (event.region, event.city) == ("Unknown", "Unknown"):
            print(f"Warning: Could not fetch location info for event {event.event_name}")
            return

        # Debugging: Print the data before insertion
        print(
            f"Inserting event: {event.identity}, {event.event_name}, {event.longitude}, {event.latitude}, {event.risk}, {region}, {city}")

        cursor.execute("""
            INSERT INTO EVENTS (id, event_name, longitude, latitude, risk, region, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (event.identity, event.event_name, event.longitude, event.latitude, event.risk.value, region, region, datetime.now()))

        connection.commit()
        connection.close()

    @staticmethod
    def fetch_all_coordinates():
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("SELECT id, event_name, longitude, latitude, risk, region, city FROM EVENTS")
        rows = cursor.fetchall()
        connection.close()

        events: list[Event] = []
        for row in rows:
            e = Event(*row)
            events.append(e)

        return events


