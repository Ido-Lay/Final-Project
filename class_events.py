class Event:
    def __init__(self, event_name, long, lat, region, city, risk):
        self.event_name = event_name
        self.long = long
        self.lat = lat
        self.region = region
        self.city = city
        self.risk = risk

    def to_dict(self):
        return {
            "event_name": self.event_name,
            "long": self.long,
            "lat": self.lat,
            "region": self.region,
            "city": self.city,
            "risk": self.risk,
        }

    @staticmethod
    def from_dict(data):
        return Event(
            event_name=data["event_name"],
            long=data["long"],
            lat=data["lat"],
            region=data["region"],
            city=data["city"],
            risk=data["risk"],
        )