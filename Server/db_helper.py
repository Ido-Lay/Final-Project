import sqlite3
from datetime import datetime, timedelta  # Not directly used in this version of helper, but good to keep if expanding
import os
from typing import Final  # Not directly used in this version of helper

# Assuming Event.py, User.py are in the same directory or accessible
from Event import Event, Risk
from User import User

# Import from the refactored dal.py
from dal import EveMapDAL, DATABASE_FILENAME  # Import the single DAL and the database filename


# Mock function for get_location_from_coordinates.
# This is useful if the actual `location_from_coordinates.py` makes external API calls
# and you want to avoid them during dummy data creation.
# For EveMapDAL to use this specific mock when helper.py is run,
# the 'location_from_coordinates.py' file itself should ideally contain this mock logic,
# or advanced patching should be used. dal.py imports it directly.
def get_location_from_coordinates(event: Event) -> tuple[str, str]:
    """
    Mock function to return plausible region/city based on coordinates.
    This function will be called by EveMapDAL.insert_event_to_table.
    """
    # Simple logic: Assign based on longitude range (example for Israel)
    if 34.0 < event.longitude < 35.0:  # Roughly Central Israel
        region = "Center District"
        if 31.8 < event.latitude < 32.2:  # Roughly Tel Aviv latitude
            city = "Tel Aviv"
        elif 32.7 < event.latitude < 33.0:  # Roughly Haifa latitude
            city = "Haifa"
        else:
            city = "Central City"
    elif 35.0 <= event.longitude < 36.0:  # Roughly Eastern Israel / Jerusalem
        region = "Jerusalem District"
        if 31.5 < event.latitude < 32.0:  # Roughly Jerusalem latitude
            city = "Jerusalem"
        else:
            city = "Eastern City"
    elif 34.5 < event.longitude < 35.5 and 30.0 < event.latitude < 31.5:  # Roughly Southern Israel
        region = "Southern District"
        city = "Be'er Sheva"
    else:
        region = "Unknown Region"
        city = "Unknown City"

    # Simulate potential lookup failure for a specific event name
    if event.event_name == "Unknown Location Event":
        return "Unknown", "Unknown"
    return region, city


def create_dummy_data_for_database():
    """
    Creates dummy data for the main database (evemap.db), populating
    USERS, EVENTS, and ADMIN_EVENTS tables.
    Ensures at least 5 rows are added to each relevant table where applicable.
    """
    print("Starting dummy data creation...")

    # --- Ensure Database and Tables Exist ---
    # Delete existing database if it exists to start fresh
    if os.path.exists(DATABASE_FILENAME):
        os.remove(DATABASE_FILENAME)
        print(f"Removed existing database: {DATABASE_FILENAME}")

    print("Creating database schema (USERS, EVENTS, ADMIN_EVENTS tables)...")
    EveMapDAL.create_database()  # This single call creates all necessary tables
    print("Database schema created.")

    # --- Dummy Data for evemap.db ---

    # 1. Dummy Users
    print("\nInserting dummy users into USERS table...")
    dummy_users = [
        User(
            name="Alice Smith",
            mail_address="ido.eliav10@gmail.com",
            password="password123",
            home_address={"longitude": 34.8, "latitude": 32.1},
        ),  # Tel Aviv area
        User(
            name="Bob Johnson",
            mail_address="ido.eliavgames@gmail.com",
            password="bobspassword",
            home_address={"longitude": 35.2, "latitude": 31.8},
        ),  # Jerusalem area
        User(
            name="Charlie Brown",
            mail_address="sussyzyla@gmail.com",
            password="securepass",
            home_address={"longitude": 34.9, "latitude": 32.8},
        ),  # Haifa area
        User(
            name="Diana Prince",
            mail_address="annastiseuss@gmail.com",
            password="wonder",
            home_address={"longitude": 34.7, "latitude": 31.3},
        ),  # South area
        User(
            name="Ethan Hunt",
            mail_address="annastiseussim@gmail.com",
            password="mission",
            home_address={"longitude": 35.5, "latitude": 32.9},
        ),  # North area
        User(
            name="Fiona Glenanne",
            mail_address="annastiodseussim@gmail.com",
            password="boom",
            home_address={"longitude": 35.55, "latitude": 32.95},
        ),  # Example, can add more
    ]
    for user in dummy_users:
        try:
            EveMapDAL.insert_user(user)
            print(f"Inserted user: {user.name}")
        except sqlite3.IntegrityError as e:  # Catch if mail_address is not unique
            print(f"Could not insert user {user.name} ({user.mail_address}): {e}")
        except Exception as e:
            print(f"An error occurred inserting user {user.name}: {e}")

    # 2. Dummy Events for EVENTS and ADMIN_EVENTS tables
    # The 'identity' passed to Event constructor here is a placeholder;
    # the actual ID in the database will be AUTOINCREMENT.
    # Region/City are "Fetching..." as they will be determined by get_location_from_coordinates
    # during the insertion process in EveMapDAL.
    print("\nInserting dummy events into EVENTS and ADMIN_EVENTS tables...")
    dummy_events_data = [
        # Events for ADMIN_EVENTS table (e.g., higher risk, admin-verified)
        Event(
            event_name="Major Traffic Jam",
            longitude=34.7818,
            latitude=32.0853,
            risk=Risk.DANGER,
            region="Fetching...",
            city="Fetching...",
        ),  # Tel Aviv Center
        Event(
            event_name="Accident Reported",
            longitude=34.75,
            latitude=32.05,
            risk=Risk.DANGER,
            region="Fetching...",
            city="Fetching...",
        ),  # Near Tel Aviv
        Event(
            event_name="Accident - Route 4",
            longitude=34.81,
            latitude=32.1,
            risk=Risk.DANGER,
            region="Fetching...",
            city="Fetching...",
        ),
        Event(
            event_name="VIP Security Zone",
            longitude=34.79,
            latitude=32.09,
            risk=Risk.DANGER,
            region="Fetching...",
            city="Fetching...",
        ),
        Event(
            event_name="Emergency Roadwork",
            longitude=35.00,
            latitude=32.5,
            risk=Risk.DANGER,
            region="Fetching...",
            city="Fetching...",
        ),  # Another danger event
        # Events for EVENTS table (e.g., user-reported, neutral, good)
        Event(
            event_name="Road Closure - Main St",
            longitude=35.2137,
            latitude=31.7683,
            risk=Risk.NEUTRAL,
            region="Fetching...",
            city="Fetching...",
        ),  # Jerusalem Center
        Event(
            event_name="Public Gathering - Park",
            longitude=34.9896,
            latitude=32.7940,
            risk=Risk.GOOD,
            region="Fetching...",
            city="Fetching...",
        ),  # Haifa Area
        Event(
            event_name="Construction Zone",
            longitude=35.22,
            latitude=31.78,
            risk=Risk.NEUTRAL,
            region="Fetching...",
            city="Fetching...",
        ),  # Near Jerusalem
        Event(
            event_name="Festival Prep",
            longitude=34.85,
            latitude=32.15,
            risk=Risk.GOOD,
            region="Fetching...",
            city="Fetching...",
        ),  # Near Tel Aviv North
        Event(
            event_name="Festival - City Park",
            longitude=35.21,
            latitude=31.77,
            risk=Risk.GOOD,
            region="Fetching...",
            city="Fetching...",
        ),
        Event(
            event_name="Planned Maintenance - Bridge",
            longitude=34.99,
            latitude=32.8,
            risk=Risk.NEUTRAL,
            region="Fetching...",
            city="Fetching...",
        ),
        Event(
            event_name="Community Cleanup Event",
            longitude=34.76,
            latitude=31.25,
            risk=Risk.GOOD,
            region="Fetching...",
            city="Fetching...",
        ),  # Be'er Sheva area
        Event(
            event_name="Reported Road Hazard",
            longitude=35.1,
            latitude=32.5,
            risk=Risk.NEUTRAL,
            region="Fetching...",
            city="Fetching...",
        ),  # Somewhere between Haifa and Jerusalem
        Event(
            event_name="Unknown Location Event",
            longitude=1.0,
            latitude=1.0,
            risk=Risk.NEUTRAL,
            region="Fetching...",
            city="Fetching...",
        ),  # Intentionally bad coordinates for testing location fallback
        Event(
            event_name="Local Market Day",
            longitude=34.77,
            latitude=32.07,
            risk=Risk.GOOD,
            region="Fetching...",
            city="Fetching...",
        ),  # Another good event
    ]

    admin_events_count = 0
    user_events_count = 0

    for event in dummy_events_data:
        try:
            # Example logic: DANGER events go to ADMIN_EVENTS, others to EVENTS
            if event.risk == Risk.DANGER:
                EveMapDAL.insert_admin_event(event)
                admin_events_count += 1
                print(
                    f"Inserted into ADMIN_EVENTS: {event.event_name} ({event.risk.name}) at ({event.latitude}, {event.longitude})"
                )
            else:
                EveMapDAL.insert_event(event)
                user_events_count += 1
                print(
                    f"Inserted into EVENTS: {event.event_name} ({event.risk.name}) at ({event.latitude}, {event.longitude})"
                )
        except Exception as e:
            print(f"An error occurred inserting event {event.event_name}: {e}")

    print(f"\nFinished inserting events: {admin_events_count} into ADMIN_EVENTS, {user_events_count} into EVENTS.")


# --- Main execution block ---
if __name__ == "__main__":
    # This block allows you to run this script directly to populate the database.
    # Ensure Event.py, User.py, dal.py, and a (potentially mock)
    # location_from_coordinates.py are in the same directory or accessible.

    # If location_from_coordinates.py contains the real API call, and you want to use the mock
    # for this script, you'd typically replace the content of location_from_coordinates.py
    # with the mock function temporarily, or use a more advanced patching technique.
    # For simplicity, this script assumes dal.py's import will resolve to either the
    # real function or a mock version made available at the `location_from_coordinates` import path.

    create_dummy_data_for_database()

    # Optional: Verify data insertion by fetching back some data
    print("\nVerifying data insertion...")
    try:
        print(f"\nUsers in {DATABASE_FILENAME}:")
        all_users = EveMapDAL.get_all_users()
        if all_users:
            for user in all_users:
                # Assuming User class has a __str__ or a print_user method
                print(f"  User: {user.name}, Email: {user.mail_address}, Home: ({user.get_longitude_and_latitude()})")
        else:
            print("  No users found.")

        print(f"\nEvents in EVENTS table ({DATABASE_FILENAME}):")
        all_events_main = EveMapDAL.fetch_all_coordinates_from_events()
        if all_events_main:
            for event in all_events_main:
                # Assuming Event class has a __str__ or a print_event method
                print(
                    f"  Event ID: {event.identity}, Name: {event.event_name}, Risk: {event.risk}, Location: ({event.latitude}, {event.longitude}), City: {event.city}, Region: {event.region}"
                )
        else:
            print("  No events found in EVENTS table.")

        print(f"\nEvents in ADMIN_EVENTS table ({DATABASE_FILENAME}):")
        all_events_admin = EveMapDAL.fetch_all_coordinates_from_admin_events()
        if all_events_admin:
            for event in all_events_admin:
                print(
                    f"  Admin Event ID: {event.identity}, Name: {event.event_name}, Risk: {event.risk}, Location: ({event.latitude}, {event.longitude}), City: {event.city}, Region: {event.region}"
                )
        else:
            print("  No events found in ADMIN_EVENTS table.")

    except Exception as e:
        print(f"\nAn error occurred during verification: {e}")

    print("\nHelper script finished.")
