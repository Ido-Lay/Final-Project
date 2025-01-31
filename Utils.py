from geopy.geocoders import Nominatim
from class_events import Event


def get_location_info(longitude, latitude, event_name, risk):
    geolocator = Nominatim(user_agent="my_geopy_app")

    # Pass coordinates as a tuple
    location = geolocator.reverse((latitude, longitude))

    if location and 'address' in location.raw:
        address = location.raw['address']
        event = Event(event_name, longitude, latitude,
                      address.get('state', ''),
                      address.get('city', ''), risk)
        return event
    return None


# Example call
event = get_location_info(34.912380, 32.439809, 'fire', 0)
event.print_event()
