import requests
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import math
import json
import ctypes
import curses


def main():
    # opensky url
    # https://opensky-network.org/api

    print("This will be a Plane Visualizer :D !")
    load_dotenv()

    location = input("Enter the location you want to use visplane for: ")
    lat, long = get_coordinates_of_place(location)
    min_lat, min_long, max_lat, max_long = calculate_bounding_box(lat, long)

    response = make_opensky_query(min_lat, min_long, max_lat, max_long)

    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    display_flights(response.json, screen_width, screen_height, (long, lat))
    return


def get_coordinates_of_place(location: str):

    long, lat = 0, 0
    locator = Nominatim(user_agent="VisPlane")
    geocoded_location = locator.geocode(location)
    lat, long = geocoded_location.latitude, geocoded_location.longitude

    return (long, lat)

def calculate_bounding_box(lat: float, long: float):
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
        exit(1)

    save_flight_data(response)

    return response

def convert_lat_long_to_screen_coordinates(long, lat, screen_y, screen_x):
    # long => -180 to 180
    # lat => -90 to 90
    normalized_long = ((long - -180) / (180 - -180)) * (screen_x) + 0
    normalized_lat = ((lat - -90) / (90 - -90)) * (screen_y) + 0

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
    while True:
    
        stdscr.refresh()
        print(f"On Screen {int(center_long), int(center_lat)}")
        stdscr.addch(int(center_lat), int(center_long), "o")
        if stdscr.getch() == ord("q"): # press q to exit
            break

    
    curses.endwin()
    return


if __name__ == "__main__":
    main()

