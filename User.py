import hashlib
from geopy.geocoders import Nominatim

class User:
    def __init__(self, name: str, home_address: dict[str, float] = None, mail_address: str = None,
                 password: str = None):
        self.name = name
        self.home_address = home_address if home_address is not None else {"longitude": None, "latitude": None}
        self.mail_address = mail_address
        self.password_hash = self._hash_password(password)
        if home_address:
            self.latitude, self.longitude = self.get_coordinates_from_address(home_address)


    def _hash_password(self, password: str) -> str:
        """Hashes the password using SHA-256 for security."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verifies if the given password matches the stored hash."""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Convert the object to a dictionary (including password hash)."""
        return {
            "name": self.name,
            "home_address": self.home_address,
            "mail_address": self.mail_address,
            "password_hash": self.password_hash,  # Store hashed password, not plain text
        }

    @classmethod
    def from_dict(cls, data):
        """Create a User instance from a dictionary (restoring hashed password)."""
        return cls(
            name=data["name"],
            home_address=data.get("home_address"),
            mail_address=data.get("mail_address"),
            password=data["password"],  # Load hashed password directly
        )

    def print_user(self):
        """Print user details (excluding password for security)."""
        print(self.name, ", ", self.home_address, ", ", self.mail_address)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.mail_address  # Assuming mail_address is unique

    def get_coordinates_from_address(self, address: dict):
        """Get latitude and longitude from the address."""
        geolocator = Nominatim(user_agent="my_geopy_app")
        location = geolocator.geocode(f"{address['street']}, {address['city']}, {address['state']}")
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
