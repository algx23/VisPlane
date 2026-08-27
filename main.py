import requests
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import math
import json
import ctypes
import curses
from Flight import Flight

def main():
    # opensky url
    # https://opensky-network.org/api

    print("This will be a Plane Visualizer :D !")
    load_dotenv()

    location = input("Enter the location you want to use visplane for: ")
    long, lat = get_coordinates_of_place(location)
    min_lat, min_long, max_lat, max_long = calculate_bounding_box(long, lat)

    response = make_opensky_query(min_lat, min_long, max_lat, max_long)

    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    display_flights(response.json, screen_width, screen_height, (long, lat))

    return


def get_coordinates_of_place(location: str):
    """
    Retrieve the latitude and longitude of a place

    Arguments:
       - location str: the name of the city to use as the central point
         from which to start the visualization
    
    Returns
        - (longitude, latitude) (float, float): - a tuple of the longitude,
          and latitude of the place
    """

    long, lat = 0, 0
    locator = Nominatim(user_agent="VisPlane")
    geocoded_location = locator.geocode(location)
    lat, long = geocoded_location.latitude, geocoded_location.longitude

    return (long, lat)

def calculate_bounding_box(long: float, lat: float):
    """
    Calculates a bounding box based on the location latitude and
    longitude, with a radius of 50km

    REFERENCE: http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates 

    Arguments:
    - lat (float): latitude of the location centroid in degrees
    - long (float): longitude of the location centroid in degrees

    Returns:
    Bounding box Coordinates (tuple) consisting of -
    - min_lat (float): western-most latitude of bbox in radians
    - min_long (float): southern-most longitude of bbox in radians
    - max_lat (float): eastern-most latitude of bbox in radians
    - max_long (float): northern-most longitude of bbox in radians
    """

    rad_lat, rad_long = math.radians(lat), math.radians(long)

    # find r -> r = d/R
    # R = 6371x10^3
    # d => let's say it is 50km radius
    # r = 50x10^3/6371x10^3
    # r = 0.00784806152880238581070475592529 rad
    # lat = lat +- r
    r: float = 0.00784806152880238581070475592529


    lat_min, lat_max = math.degrees(rad_lat - r), math.degrees(rad_lat + r)
    lat_T = math.asin(math.sin(rad_lat) / math.cos(r))

    delta_long = math.asin((math.sin(r) / math.cos(rad_lat)))
    long_min, long_max = math.degrees(rad_long - delta_long), math.degrees(rad_long + delta_long)

    return (lat_min, long_min, lat_max, long_max)


def save_flight_data(response):
    nearby_flight_data = response.json()
    with open('nearby flights.json', 'w', encoding='utf-8') as f:
        json.dump(nearby_flight_data, f, ensure_ascii=False, indent=4)
    return

def make_opensky_query(min_lat, min_long, max_lat, max_long):
    request_url = f"https://opensky-network.org/api/states/all?lamin={min_lat}&lomin={min_long}&lamax={max_lat}&lomax={max_long}"

    VP_CLIENT_ID = os.getenv("VISPLANE_CLIENT_ID")
    VP_CLIENT_SECRET = os.getenv("VISPLANE_CLIENT_SECRET")
    response = requests.get(request_url, auth=(VP_CLIENT_ID, VP_CLIENT_SECRET))

    print(request_url)
    if response.status_code != 200:
        print("Something Went Wrong with the request")

    save_flight_data(response)

    return response

def convert_lat_long_to_screen_coordinates(long, lat, screen_y, screen_x):
    # long => -180 to 180
    # lat => -90 to 90
    normalized_long = ((long - -180) / (180 - -180)) * (screen_x) + 0
    print(long, normalized_long)
    normalized_lat = ((lat - -90) / (90 - -90)) * (screen_y) + 0
    print(lat, normalized_lat)
    return (normalized_long, normalized_lat)


def display_flights(flight_info_json, width, height, center):
    print(width, height)
    print(center)
    # 1920x1080 resolution
    # 50km bounding box
    stdscr = curses.initscr()
    screen_y, screen_x = stdscr.getmaxyx()
    print(f"Max Possible: {screen_x, screen_y}")

    center_long, center_lat = convert_lat_long_to_screen_coordinates(center[0], center[1], screen_y, screen_x)

    print(f"Normalized: {center_long, center_lat}")
    flight_list = load_flight_object("nearby flights.json")
    
    co_ords = dict()
    for flight in flight_list:

        co_ords[flight.icao] = convert_lat_long_to_screen_coordinates(flight.longitude, flight.latitude, screen_y, screen_x)
        print(co_ords)

    while True:
    
        stdscr.clear()

        stdscr.addch(int(center_lat), int(center_long), "o")

        for key in co_ords.keys():
            stdscr.addch(int(co_ords[key][1]), int(co_ords[key][0]), "x") 
        if stdscr.getch() == ord("q"): # press q to exit
            break

    
    curses.endwin()
    
    return

def load_flight_object(flight_json):
    flight_dict_keys = [
        "icao",
        "callsign",
        "origin",
        "time_pos",
        "last_contact",
        "longitude",
        "latitude",
        "geo_alt",
        "on_ground",
        "velocity",
        "heading",
        "v_rate",
        "sensors",
        "baro_alt",
        "squawk",
        "spi",
        "pos_src",
        "category"
        ]
    
    with open("nearby flights.json") as flight_file:
        data = json.load(flight_file)
        flights = data["states"]



    all_flights = dict()
    flight_list = []

    for flight in flights:
        flight_dict = dict(zip(flight_dict_keys, flight))
        all_flights.update({flight_dict["icao"]: flight_dict})
        flight_obj = Flight(flight_dict)

        if not flight_obj.on_ground:
            flight_list.append(flight_obj)

    return flight_list


if __name__ == "__main__":
    main()
    curses.endwin()

