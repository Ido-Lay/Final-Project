from geopy.geocoders import Nominatim
from class_events import Event


def get_location_info(event):
    geolocator = Nominatim(user_agent="my_geopy_app")

    # Pass coordinates as a tuple
    location = geolocator.reverse((event.lat, event.long))

    if location and 'address' in location.raw:
        address = location.raw['address']
        new_event = Event(event.event_name, event.long, event.lat,
                      address.get('state', ''),
                      address.get('city', ''), event.risk)
        return new_event
    return None


