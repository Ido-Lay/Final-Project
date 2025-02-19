import sqlite3
from datetime import datetime, timedelta
import threading
import time
import schedule
import json
from class_events import Event
import Utils

class DataBaseActions():
    def adapt_datetime(self, dt):
        return dt.isoformat()

    def convert_datetime(self, dt_str):
        return datetime.fromisoformat(dt_str.decode("utf-8"))

    def make_database(self):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS EVENTS")
        table = """ CREATE TABLE EVENTS (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT,
                    long REAL,
                    lat REAL,
                    risk INT,
                    region TEXT,
                    city TEXT,
                    created_at DATETIME
                ); """
        cursor.execute(table)
        connection.commit()
        connection.close()

    '''def insert_event(event):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        # Insert the event with the current timestamp
        cursor.execute("""
            INSERT INTO EVENTS (event_name, long, lat, region, city, risk, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event.event_name, event.long, event.lat, event.region, event.city, event.risk, datetime.now()))

        connection.commit()
        connection.close()'''

    def insert_event(self, event):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
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

    def cleanup_database(self):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        # Calculate the cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=10)

        # Delete rows older than the cutoff time
        cursor.execute("DELETE FROM EVENTS WHERE created_at < ?", (cutoff_time,))

        connection.commit()
        connection.close()

    def run_scheduler(self):
        schedule.every(10).minutes.do(self.cleanup_database)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def start_cleanup_thread(self):
        cleanup_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        cleanup_thread.start()

    def fetch_all_events(self):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM EVENTS")
        output = cursor.fetchall()
        connection.close()
        return json.dumps(output, default=str)

    def fetch_all_coordinates(self):
        connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("SELECT event_name, long, lat, risk, region, city FROM EVENTS")
        rows = cursor.fetchall()
        connection.close()

        events: list[Event] = []
        for row in rows:
            e = Event(*row)
            events.append(e)

        return events


