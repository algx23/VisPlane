class Flight:
    def __init__(self, flight):
        for k,v in flight.items():
            setattr(self, k, v)

