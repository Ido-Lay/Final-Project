from geopy.geocoders import Nominatim
from EventClass import Event


def get_location_info(event):
    geolocator = Nominatim(user_agent="my_geopy_app")

    # Pass coordinates as a tuple
    location = geolocator.reverse((event.lat, event.long))

    if location and 'address' in location.raw:
        address = location.raw['address']
        region = address.get('state', '')  # The state (region)
        city = address.get('city', '')  # The city

        loc_data = (region, city)
        return loc_data

    print(f"Warning: Could not fetch location info for event {event.event_name}")
    loc_data = ["unknown", "unknown"]
    return loc_data



