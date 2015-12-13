import dateutil.parser as date_parser
from flask import Flask, jsonify
import json
import logging
from math import sin, cos, sqrt, atan2, radians
import sys
import urllib2

AERO_API_KEY = '83af8148873102bc1995d8aa5938df18'
AERO_CODES_ENDPOINT = 'https://airport.api.aero/'
EARTH_RADIUS = 6373.0  # In km
MILES_PER_KM = 0.621371

app = Flask(__name__)
app.config['DEBUG'] = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)


@app.route('/')
def test():
    return str(get_forecast((52.2296756, 21.0122287), (52.406374, 16.9251681)))


@app.route('/resolve/<location>')
def get_location(location):
    coords = resolve_location(location)
    return jsonify(location=[coords[0], coords[1]])


@app.route('/forecast/<src>/<dest>/<departure_datetime>/<speed_mph>/<time_step>')
def get_forecast(src, dest, departure_datetime, speed_mph, time_step):
    src_coord = resolve_location(src)
    dest_coord = resolve_location(dest)
    departure_date = date_parser.parse(departure_datetime)
    miles_per_step = float(speed_mph) * float(time_step)

    forecasts = []
    total_miles = calculate_distance(src_coord, dest_coord)
    miles_traveled = 0
    while miles_traveled < total_miles:
        current_loc_tuple = get_new_coord(src_coord, dest_coord, miles_traveled)
        current_loc_arr = [current_loc_tuple[0], current_loc_tuple[1]]
        forecast = {
            'location': current_loc_arr,
            'location_rnd': [round(i, 2) for i in current_loc_arr],
        }
        forecasts.append(forecast)
        miles_traveled += miles_per_step
    return jsonify(forecast=forecasts)


def get_airport_coordinates(iata_code):
    iata_code = iata_code.upper()
    request = urllib2.Request('{}airport/{}?user_key={}'.format(
        AERO_CODES_ENDPOINT, iata_code, AERO_API_KEY), headers={'Accept': 'application/json'})
    airport_info = json.loads(urllib2.urlopen(request).read())['airports'][0]
    return airport_info['lat'], airport_info['lng']


def get_new_coord(src_coord, dest_coord, miles_traveled):
    total_distance = calculate_distance(src_coord, dest_coord)
    proportion_traveled = miles_traveled / total_distance

    slope = (dest_coord[0] - src_coord[0]) / (dest_coord[1] - src_coord[1])
    y_intercept = src_coord[0] - slope * src_coord[1]

    new_long = (dest_coord[1] - src_coord[1]) * proportion_traveled + src_coord[1]
    new_lat = slope * new_long + y_intercept
    return new_lat, new_long


def resolve_location(location):
    if ',' in location:
        lat_long = location.split(',')
        lat = int(lat_long[0])
        long = int(lat_long[1])
    else:
        lat, long = get_airport_coordinates(location)
    return lat, long


def calculate_distance(src_coord, dest_coord):
    src_coord = tuple(radians(i) for i in src_coord)
    dest_coord = tuple(radians(i) for i in dest_coord)
    dlat = dest_coord[0] - src_coord[0]
    dlong = dest_coord[1] - src_coord[1]

    a = sin(dlat / 2)**2 + cos(src_coord[0]) * cos(dest_coord[0]) * sin(dlong / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS * c * MILES_PER_KM


if __name__ == '__main__':
    app.run()
