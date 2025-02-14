from geopy.geocoders import Nominatim
from class_events import Event


def get_location_info(event):
    geolocator = Nominatim(user_agent="my_geopy_app")

    # Pass coordinates as a tuple
    location = geolocator.reverse((event.lat, event.long))

    if location and 'address' in location.raw:
        address = location.raw['address']
        region = address.get('state', '')  # The state (region)
        city = address.get('city', '')  # The city

        # Ensure correct order of parameters in the Event constructor
        new_event = Event(event.event_name, event.long, event.lat, event.risk, region, city)
        return new_event

    print(f"Warning: Could not fetch location info for event {event.event_name}")
    return event



