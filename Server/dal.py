import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Final, Optional
import schedule
import json
from Event import Event
from location_from_coordinates import get_location_from_coordinates
from User import User

DATABASE_FILENAME: Final[str] = 'evemap.db'


class EveMapDAL:
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
    def create_admin_events_table(cursor):
        event_table = """ CREATE TABLE IF NOT EXISTS ADMIN_EVENTS (
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
    def create_database():
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()

        EveMapDAL.create_events_table(cursor)
        EveMapDAL.create_users_table(cursor)
        EveMapDAL.create_admin_events_table(cursor)

        connection.commit()
        connection.close()

    @staticmethod
    def insert_event_to_table(table_name: str, event: Event):
        if not table_name.isalpha():
            return

        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        region, city = get_location_from_coordinates(event)

        if (event.region, event.city) == ("Unknown", "Unknown"):
            print(f"Warning: Could not fetch location info for event {event.event_name}")

        # Debugging: Print the data before insertion
        print(f"Inserting event: "
              f"{event.identity}, {event.event_name}, {event.longitude}, {event.latitude}, {event.risk}, {region}, {city}")

        cursor.execute(f"""
            INSERT INTO {table_name} (event_name, longitude, latitude, risk, region, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event.event_name, event.longitude, event.latitude, event.risk.value, region, city, datetime.now()))

        connection.commit()
        connection.close()

    @staticmethod
    def insert_event(event: Event):
        EveMapDAL.insert_event_to_table('EVENTS', event)

    @staticmethod
    def insert_admin_event(event: Event):
        EveMapDAL.insert_event_to_table('ADMIN_EVENTS', event)

    @staticmethod
    def insert_user(user: User):
        conn = sqlite3.connect(DATABASE_FILENAME)
        c = conn.cursor()

        # Safely get coordinates
        longitude, latitude = user.get_longitude_and_latitude()

        c.execute('''
            INSERT INTO USERS (name, mail_address, password_hash, home_long, home_lat)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.name, user.mail_address, user.password_hash, longitude, latitude))

        conn.commit()
        conn.close()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        conn = sqlite3.connect(DATABASE_FILENAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, mail_address, password_hash, home_long, home_lat FROM USERS WHERE mail_address = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            name, email, password_hash, long, lat = row
            return User(name=name, mail_address=email, password=password_hash,
                        password_is_hashed=True,
                        home_address={"longitude": long, "latitude": lat})
        return None

    @staticmethod
    def get_all_users() -> Optional[list[User]]:
        conn = sqlite3.connect(DATABASE_FILENAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name, mail_address, password_hash, home_long, home_lat FROM USERS")
        rows = cursor.fetchall()
        conn.close()

        users: list[User] = []
        for row in rows:
            name, email, password_hash, long, lat = row
            row_data = {
                'name': name,
                'home_address': {"home_long": long,
                                 "home_lat": lat},
                'mail_address': email,
                'password': password_hash,
            }
            e = User.from_dict(row_data)
            users.append(e)

        return users

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
        schedule.every(1).minutes.do(EveMapDAL.cleanup_database)
        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def start_cleanup_thread():
        cleanup_thread = threading.Thread(target=EveMapDAL.run_scheduler, daemon=True)
        cleanup_thread.start()

    @staticmethod
    def fetch_all_coordinates_from_table(table_name: str, city=None, region=None, risk=None) -> list[Event]:
        conn = sqlite3.connect(DATABASE_FILENAME)
        cursor = conn.cursor()

        # Modify the query to include the identity field
        query = f"SELECT id, event_name, latitude, longitude, risk, city, region FROM {table_name} WHERE 1=1"
        params = []

        if city is not None:
            query += " AND city = ?"
            params.append(city)

        if region is not None:
            query += " AND region = ?"
            params.append(region)

        if risk is not None:
            query += " AND risk = ?"
            params.append(risk)

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching admin events: {e}")
            rows = []  # Return empty list on error
        finally:
            conn.close()

        events = []
        for row in rows:
            try:
                event = Event(
                    identity=row[0],
                    event_name=row[1],
                    latitude=row[2],
                    longitude=row[3],
                    risk=row[4],
                    city=row[5] if row[5] else "Unknown",
                    region=row[6] if row[6] else "Unknown"
                )
                events.append(event)
            except Exception as e:
                print(f"Error processing row {row}: {e}")  # Catch errors during Event object creation

        return events

    @staticmethod
    def fetch_all_coordinates_from_events():
        return EveMapDAL.fetch_all_coordinates_from_table('EVENTS')

    @staticmethod
    def fetch_all_coordinates_from_admin_events():
        return EveMapDAL.fetch_all_coordinates_from_table('ADMIN_EVENTS')

    @staticmethod
    def get_unique_cities():
        conn = sqlite3.connect(DATABASE_FILENAME)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT city FROM EVENTS WHERE city IS NOT NULL")
        cities = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cities

    @staticmethod
    def get_unique_regions():
        conn = sqlite3.connect(DATABASE_FILENAME)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT region FROM EVENTS WHERE region IS NOT NULL")
        regions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return regions

    @staticmethod
    def delete_event(db_id: int) -> bool:
        connection = sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        try:
            with sqlite3.connect(DATABASE_FILENAME, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ADMIN_EVENTS WHERE id = ?", (db_id,))
            if cursor.rowcount == 0:
                print(f"Warning: No event found with id {db_id}. No rows deleted.")
                return False
            else:
                print(f"Successfully deleted event with id {db_id}.")
                return True

        except sqlite3.Error as e:
            print(f"Database error occurred: {e}")
            return False
