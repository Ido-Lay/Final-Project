from dataclasses import dataclass
from enum import Enum


class Risk(Enum):
    DANGER = 0
    GOOD = 1
    NEUTRAL = 2


@dataclass
class Event:
    event_name: str
    longitude: float
    latitude: float
    risk: Risk
    region: str
    city: str
    identity: int = -1

    def to_dict(self):
        return {
            "identity": self.identity,
            "event_name": self.event_name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "risk": self.risk,
            "region": self.region,
            "city": self.city,
        }

    def print_event(self):
        print(
            "id: ",
            self.identity,
            ", ",
            "name: ",
            self.event_name,
            ", ",
            "longitude: ",
            self.longitude,
            ", ",
            "latitude: ",
            self.latitude,
            ", ",
            "region: ",
            self.region,
            ", ",
            "city: ",
            self.city,
            ", ",
            "risk: ",
            self.risk,
        )

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            identity=data["identity"],
            event_name=data["event_name"],
            risk=Risk(data["risk"]),
            longitude=data["longitude"],
            latitude=data["latitude"],
            region=data["region"],
            city=data["city"],
        )
