class Flight:
    def __init__(self, icao, origin, time_pos, last_cnct, longitude, latitude, geo_alt, on_ground, velocity, heading, v_rate, alt, squawk):
        self.icao = icao
        self.origin = origin
        self.time_pos = time_pos
        self.last_cnct = last_cnct
        self.longitude = longitude
        self.latitude = latitude
        self.geo_alt = geo_alt
        self.on_ground = on_ground
        self.velocity = velocity
        self.heading = heading
        self.v_rate = v_rate
        self.alt = alt
        self.squawk = squawk
