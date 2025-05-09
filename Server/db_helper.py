import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Final, Optional
import schedule
import json
from Event import Event, Risk  # Make sure Risk is imported
from location_from_coordinates import get_location_from_coordinates  # Assuming this exists and works
from User import User
from events_db import EventsDAL  # Import the DAL classes
from admin_db import AdminDAL  # Import the DAL classes
import os


# Mock function for get_location_from_coordinates if it's not available
# or to avoid external API calls during testing/dummy data creation.
# Replace this with the actual import if the file exists and works.
def get_location_from_coordinates(event: Event) -> tuple[str, str]:
    """
    Mock function to return plausible region/city based on coordinates.
    Replace with actual implementation if available.
    """
    # Simple logic: Assign based on longitude range (example for Israel)
    if 34.0 < event.longitude < 35.0:
        region = "Center District"
        if 31.8 < event.latitude < 32.2:
            city = "Tel Aviv"
        elif 32.7 < event.latitude < 33.0:
            city = "Haifa"
        else:
            city = "Central City"
    elif 35.0 <= event.longitude < 36.0:
        region = "Jerusalem District"
        if 31.5 < event.latitude < 32.0:
            city = "Jerusalem"
        else:
            city = "Eastern City"
    else:
        region = "Unknown Region"
        city = "Unknown City"
    # Simulate potential lookup failure
    if event.event_name == "Unknown Location Event":
        return "Unknown", "Unknown"
    return region, city


# --- Define Database Filenames ---
# Use the names defined in the original DAL files
EVENTS_DB_FILENAME = 'final_project.db'
ADMIN_DB_FILENAME = 'admin_side.db'


def create_dummy_data_for_databases():
    """
    Creates dummy data for both the main events/users database
    and the admin events database.
    Ensures at least 5 rows are added to each relevant table.
    """
    print("Starting dummy data creation...")

    # --- Ensure Databases and Tables Exist ---
    # Delete existing databases if they exist to start fresh
    if os.path.exists(EVENTS_DB_FILENAME):
        os.remove(EVENTS_DB_FILENAME)
        print(f"Removed existing database: {EVENTS_DB_FILENAME}")
    if os.path.exists(ADMIN_DB_FILENAME):
        os.remove(ADMIN_DB_FILENAME)
        print(f"Removed existing database: {ADMIN_DB_FILENAME}")

    print("Creating database schemas...")
    EventsDAL.create_database()
    AdminDAL.creat_database()  # Note: Original function name was 'creat_database'
    print("Database schemas created.")

    # --- Dummy Data for final_project.db (EventsDAL) ---

    # 1. Dummy Users
    print("Inserting dummy users into final_project.db...")
    dummy_users = [
        User(name="Alice Smith", mail_address="ido.eliav10@gmail.com", password="password123",
             home_address={"longitude": 34.8, "latitude": 32.1}),  # Tel Aviv area
        User(name="Bob Johnson", mail_address="ido.eliavgames@gmail.com", password="bobspassword",
             home_address={"longitude": 35.2, "latitude": 31.8}),  # Jerusalem area
        User(name="Charlie Brown", mail_address="sussyzyla@gmail.com", password="securepass",
             home_address={"longitude": 34.9, "latitude": 32.8}),  # Haifa area
        User(name="Diana Prince", mail_address="annastiseuss@gmail.com", password="wonder",
             home_address={"longitude": 34.7, "latitude": 31.3}),  # South area
        User(name="Ethan Hunt", mail_address="annastiseussim@gmail.com", password="mission",
             home_address={"longitude": 35.5, "latitude": 32.9}),  # North area
        User(name="Fiona Glenanne", mail_address="annastiodseussim@gmail.com", password="boom", home_address={"longitude": 35.55, "latitude": 32.95})  # No home address
    ]
    for user in dummy_users:
        try:
            EventsDAL.insert_user(user)
            print(f"Inserted user: {user.name}")
        except sqlite3.IntegrityError as e:
            print(f"Could not insert user {user.name} ({user.mail_address}): {e}")
        except Exception as e:
            print(f"An error occurred inserting user {user.name}: {e}")

    # 2. Dummy Events for final_project.db
    # Note: Event identity is AUTOINCREMENT in this DB, so the 'identity' passed
    #       to the Event constructor here doesn't determine the stored ID.
    #       We pass dummy IDs like 0 or -1.
    print("\nInserting dummy events into final_project.db...")
    dummy_events_main = [
        Event(identity=0, event_name="Major Traffic Jam", longitude=34.7818, latitude=32.0853, risk=Risk.DANGER,
              region="Fetching...", city="Fetching..."),  # Tel Aviv Center
        Event(identity=0, event_name="Road Closure - Main St", longitude=35.2137, latitude=31.7683, risk=Risk.NEUTRAL,
              region="Fetching...", city="Fetching..."),  # Jerusalem Center
        Event(identity=0, event_name="Public Gathering - Park", longitude=34.9896, latitude=32.7940, risk=Risk.GOOD,
              region="Fetching...", city="Fetching..."),  # Haifa Area
        Event(identity=0, event_name="Accident Reported", longitude=34.75, latitude=32.05, risk=Risk.DANGER,
              region="Fetching...", city="Fetching..."),  # Near Tel Aviv
        Event(identity=0, event_name="Construction Zone", longitude=35.22, latitude=31.78, risk=Risk.NEUTRAL,
              region="Fetching...", city="Fetching..."),  # Near Jerusalem
        Event(identity=0, event_name="Festival Prep", longitude=34.85, latitude=32.15, risk=Risk.GOOD,
              region="Fetching...", city="Fetching..."),  # Near Tel Aviv North
        Event(identity=0, event_name="Unknown Location Event", longitude=1.0, latitude=1.0, risk=Risk.NEUTRAL,
              region="Fetching...", city="Fetching..."),  # Intentionally bad coordinates for testing location fallback

        Event(identity=101, event_name="Accident - Route 4", longitude=34.81, latitude=32.1, risk=Risk.DANGER,
              region="Admin Fetch...", city="Admin Fetch..."),
        Event(identity=102, event_name="Festival - City Park", longitude=35.21, latitude=31.77, risk=Risk.GOOD,
              region="Admin Fetch...", city="Admin Fetch..."),
        Event(identity=103, event_name="Planned Maintenance - Bridge", longitude=34.99, latitude=32.8,
              risk=Risk.NEUTRAL, region="Admin Fetch...", city="Admin Fetch..."),
        Event(identity=104, event_name="VIP Security Zone", longitude=34.79, latitude=32.09, risk=Risk.DANGER,
              region="Admin Fetch...", city="Admin Fetch..."),
        Event(identity=105, event_name="Community Cleanup Event", longitude=34.76, latitude=31.25, risk=Risk.GOOD,
              region="Admin Fetch...", city="Admin Fetch..."),  # Be'er Sheva area
        Event(identity=106, event_name="Reported Road Hazard", longitude=35.1, latitude=32.5, risk=Risk.NEUTRAL,
              region="Admin Fetch...", city="Admin Fetch...")  # Somewhere between Haifa and Jerusalem
    ]
    for event in dummy_events_main:
        try:
            if event.risk != Risk.DANGER:
                EventsDAL.insert_event(event)
            else:
                AdminDAL.insert_event(event)
            print(f"Inserted event (main DB): {event.event_name} at ({event.latitude}, {event.longitude})")
        except Exception as e:
            print(f"An error occurred inserting event {event.event_name} into main DB: {e}")


# --- Main execution block ---
if __name__ == "__main__":
    # This block allows you to run this script directly to populate the databases.
    # Ensure Event.py, User.py, events_db.py, admin_db.py, and
    # location_from_coordinates.py (or the mock function) are in the same directory
    # or accessible via Python's path.

    # Replace the mock with the real import if available
    # from location_from_coordinates import get_location_from_coordinates

    create_dummy_data_for_databases()

    # Optional: Verify data insertion by fetching back some data
    print("\nVerifying data insertion...")
    try:
        print("\nUsers in final_project.db:")
        all_users = EventsDAL.get_all_users()
        if all_users:
            for user in all_users:
                user.print_user()  # Prints name, address, email
        else:
            print("No users found.")

        print("\nEvents in final_project.db:")
        all_events_main = EventsDAL.fetch_all_coordinates()
        if all_events_main:
            for event in all_events_main:
                event.print_event()
        else:
            print("No events found.")

        print("\nEvents in admin_side.db:")
        all_events_admin = AdminDAL.fetch_all_coordinates()
        if all_events_admin:
            for event in all_events_admin:
                event.print_event()
        else:
            print("No events found.")

    except Exception as e:
        print(f"\nAn error occurred during verification: {e}")
