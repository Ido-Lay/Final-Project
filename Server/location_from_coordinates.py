from Server.Event import Event
from geopy.geocoders import Nominatim


def get_location_from_coordinates(event: Event) -> tuple[str, str]:
    geolocator = Nominatim(user_agent="my_geopy_app")

    # Pass coordinates as a tuple
    location = geolocator.reverse((event.latitude, event.longitude))

    if location and 'address' in location.raw:
        address = location.raw['address']
        region = address.get('state', '')  # The state (region)
        city = address.get('city', '')  # The city

        if region:
            if city:
                return region, city
            else:
                return region, "Unknown"
        if city:
            if region:
                return region, city
            else:
                return "Unknown", city

    print(f"Warning: Could not fetch location info for event {event.event_name}")
    return "Unknown", "Unknown"
