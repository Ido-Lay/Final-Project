class Event:
    def __init__(self, ident, event_name, long, lat, risk, region="", city=""):
        self.ident = ident
        self.event_name = event_name
        self.long = long
        self.lat = lat
        self.risk = risk
        self.region = region
        self.city = city


    def to_dict(self):
        return {
            "ident": self.ident,
            "event_name": self.event_name,
            "long": self.long,
            "lat": self.lat,
            "risk": self.risk,
            "region": self.region,
            "city": self.city,
        }

    def print_event(self):
        print(self.ident, ", ", self.event_name, ", ", self.long, ", ", self.lat, ", ", self.region, ", ", self.city, ", ", self.risk)
    @staticmethod
    def from_dict(data):
        return Event(
            ident=data["ident"],
            event_name=data["event_name"],
            long=data["long"],
            lat=data["lat"],
            risk=data["risk"],
            region=data["region"],
            city=data["city"],
        )