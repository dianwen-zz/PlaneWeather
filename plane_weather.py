from datetime import datetime, timedelta
from flask import Flask, jsonify
import json
import logging
from math import sin, cos, sqrt, atan2, radians
from pytz import timezone
import sys
import urllib2

AERO_KEY = '83af8148873102bc1995d8aa5938df18'
AERO_CODES_ENDPOINT = 'https://airport.api.aero/'
FORECAST_KEY = '21c8103568c26a8ba85b25c9fc678983'
FORECAST_ENDPOINT = 'https://api.forecast.io/forecast/'
GOOGLE_MAP_TIME_ZONE_KEY = 'AIzaSyDKGwy9xNxoPwLDvsmClo8NkLQw6XoF1cA'
GOOGLE_MAP_ENDPOINT = 'https://maps.googleapis.com/maps/api/'

EARTH_RADIUS = 6373.0  # In km
MILES_PER_KM = 0.621371
SECONDS_IN_HOUR = 3600

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
    utc_offset = get_offset_from_utc(src_coord)
    departure_date = datetime.strptime(departure_datetime, '%Y-%m-%dT%H:%M:%S')
    departure_date_utc = (departure_date + timedelta(seconds=utc_offset)).replace(
        tzinfo=timezone('UTC'))
    miles_per_step = float(speed_mph) * float(time_step)

    forecasts = []
    total_miles = calculate_distance(src_coord, dest_coord)
    distance_traveled = 0  # Miles
    time_traveled = 0  # Hours
    while distance_traveled < total_miles:
        current_loc_tuple = get_new_coord(src_coord, dest_coord, distance_traveled)
        current_loc_arr = [current_loc_tuple[0], current_loc_tuple[1]]
        utc_offset = get_offset_from_utc(current_loc_tuple)
        forecast = {
            'location': current_loc_arr,
            'location_rnd': [round(i, 2) for i in current_loc_arr],
            'time': int((departure_date_utc +
                         timedelta(seconds=time_traveled * SECONDS_IN_HOUR)).strftime('%s')),
            'time_offset': utc_offset / SECONDS_IN_HOUR if utc_offset is not None else None
        }
        forecasts.append(forecast)
        distance_traveled += miles_per_step
        time_traveled += float(time_step)
    return jsonify(forecast=forecasts)


def get_airport_coordinates(iata_code):
    iata_code = iata_code.upper()
    request = urllib2.Request('{}airport/{}?user_key={}'.format(
        AERO_CODES_ENDPOINT, iata_code, AERO_KEY), headers={'Accept': 'application/json'})
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


def get_offset_from_utc(coord):
    request = urllib2.Request('{}timezone/json?location={},{}&timestamp=0&key={}'.format(
        GOOGLE_MAP_ENDPOINT, coord[0], coord[1], GOOGLE_MAP_TIME_ZONE_KEY))
    time_zone_info = json.loads(urllib2.urlopen(request).read())
    print('request: {}, coord: {}, response: {}'.format('{}timezone/json?location={},{}&timestamp=0&key={}'.format(
        GOOGLE_MAP_ENDPOINT, coord[0], coord[1], GOOGLE_MAP_TIME_ZONE_KEY), coord, time_zone_info))
    return time_zone_info.get('rawOffset', None)  # Seconds


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
