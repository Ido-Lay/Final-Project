import sqlite3
from datetime import datetime, timedelta
import threading
import time
import schedule
import json
from class_events import Event

def adapt_datetime(dt):
    return dt.isoformat()


def convert_datetime(dt_str):
    return datetime.fromisoformat(dt_str.decode("utf-8"))


def make_database():
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS EVENTS")
    table = """ CREATE TABLE EVENTS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                long INT,
                lat INT,
                region TEXT,
                city TEXT,
                risk INT,
                created_at DATETIME
            ); """
    cursor.execute(table)
    connection.commit()
    connection.close()


def insert_event(event):
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()

    # Insert the event with the current timestamp
    cursor.execute("""
        INSERT INTO EVENTS (event_name, long, lat, region, city, risk, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (event.event_name, event.long, event.lat, event.region, event.city, event.risk, datetime.now()))

    connection.commit()
    connection.close()


def cleanup_database():
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()

    # Calculate the cutoff time
    cutoff_time = datetime.now() - timedelta(minutes=10)

    # Delete rows older than the cutoff time
    cursor.execute("DELETE FROM EVENTS WHERE created_at < ?", (cutoff_time,))

    connection.commit()
    connection.close()


def run_scheduler():
    schedule.every(10).minutes.do(cleanup_database)
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_cleanup_thread():
    cleanup_thread = threading.Thread(target=run_scheduler, daemon=True)
    cleanup_thread.start()


def fetch_all_events():
    connection = sqlite3.connect('Events.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM EVENTS")
    output = cursor.fetchall()
    connection.close()
    return json.dumps(output, default=str)
