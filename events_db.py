import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Final

import schedule
import json
from Event import Event
from location_from_coordinates import get_location_from_coordinates

DATABASE_FILENAME: Final[str] = 'final_project.db'  # TODO change


class EventsDAL:
    @staticmethod
    def adapt_datetime(dt: datetime) -> str:
        return dt.isoformat()

    @staticmethod
    def convert_datetime(dt_str: bytes) -> datetime:
        return datetime.fromisoformat(dt_str.decode("utf-8"))

    @staticmethod
    def create_events_table(cursor):
        event_table = """CREATE TABLE IF NOT EXISTS EVENTS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    def create_users_table(cursor):
        user_table = """ CREATE TABLE IF NOT EXISTS USERS (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        mail_address TEXT UNIQUE,
                        password_hash TEXT NOT NULL,
                        home_long REAL,
                        home_lat REAL
                    ); """
        cursor.execute(user_table)

    @staticmethod
    def create_database():
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        EventsDAL.create_events_table(cursor)
        EventsDAL.create_users_table(cursor)

        connection.commit()
        connection.close()

    @staticmethod
    def insert_event(event: Event):
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        region, city = get_location_from_coordinates(event)

        if (event.region, event.city) == ("Unknown", "Unknown"):
            print(f"Warning: Could not fetch location info for event {event.event_name}")
            return

        # Debugging: Print the data before insertion
        print(f"Inserting event: "
              f"{event.identity}, {event.event_name}, {event.longitude}, {event.latitude}, {event.risk}, {region}, {city}")

        cursor.execute("""
            INSERT INTO EVENTS (event_name, longitude, latitude, risk, region, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event.event_name, event.longitude, event.latitude, event.risk.value, region, city, datetime.now()))

        connection.commit()
        connection.close()

    @staticmethod
    def cleanup_database():
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        # Calculate the cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=10)

        # Delete rows older than the cutoff time
        cursor.execute("DELETE FROM EVENTS WHERE created_at < ?", (cutoff_time,))

        connection.commit()
        connection.close()

    @staticmethod
    def run_scheduler():
        schedule.every(1).minutes.do(EventsDAL.cleanup_database)
        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def start_cleanup_thread():
        cleanup_thread = threading.Thread(target=EventsDAL.run_scheduler, daemon=True)
        cleanup_thread.start()

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
