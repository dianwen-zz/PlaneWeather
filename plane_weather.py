import collections
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

EARTH_RADIUS = 6373.0  # In km
MILES_PER_KM = 0.621371
SECONDS_IN_HOUR = 3600

app = Flask(__name__)
app.config['DEBUG'] = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)


@app.route('/resolve/<location>')
def get_location(location):
    coords = resolve_location(location)
    return jsonify(location=[coords[0], coords[1]])


@app.route('/forecast/<src>/<dest>/<departure_datetime>/<speed_mph>/<time_step>')
def get_forecast(src, dest, departure_datetime, speed_mph, time_step):
    src_coord = resolve_location(src)
    dest_coord = resolve_location(dest)
    departure_date = datetime.strptime(departure_datetime, '%Y-%m-%dT%H:%M:%S')
    miles_per_step = float(speed_mph) * float(time_step)

    forecasts = []
    total_miles = calculate_distance(src_coord, dest_coord)
    distance_traveled = 0  # Miles
    time_traveled = 0  # Hours
    while distance_traveled < total_miles:
        current_loc_tuple = get_new_coord(src_coord, dest_coord, distance_traveled)
        current_loc_arr = [current_loc_tuple[0], current_loc_tuple[1]]
        current_timestamp = int((departure_date +
                         timedelta(seconds=time_traveled * SECONDS_IN_HOUR)).strftime('%s'))
        weather_info = get_weather(current_loc_tuple, current_timestamp)
        forecast = {
            'humidity': weather_info.humidity,
            'incomplete': weather_info.incomplete,
            'location': current_loc_arr,
            'location_rnd': [round(i, 2) for i in current_loc_arr],
            'temperature': weather_info.temperature,
            'time': current_timestamp,
            'time_offset': weather_info.time_offset,
            'time_rnd': int(current_timestamp),
            'wind_speed': weather_info.wind_speed
        }
        forecast = {k: v for k, v in forecast.items() if v}  # Remove None values
        forecasts.append(forecast)
        distance_traveled += miles_per_step
        time_traveled += float(time_step)
    return jsonify(forecast=forecasts)


def calculate_distance(src_coord, dest_coord):
    '''Calculates the distance between two coordinates
    :param (int, int) src_coord: source coordinate in latitude, longitude
    :param (int, int) dest_coord: destination coordinate in latitude, longitude
    :return int: distance in miles
    '''
    src_coord = tuple(radians(i) for i in src_coord)
    dest_coord = tuple(radians(i) for i in dest_coord)
    dlat = dest_coord[0] - src_coord[0]
    dlong = dest_coord[1] - src_coord[1]

    a = sin(dlat / 2)**2 + cos(src_coord[0]) * cos(dest_coord[0]) * sin(dlong / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS * c * MILES_PER_KM


def get_airport_coordinates(iata_code):
    ''' Gets the the coordinates of an airport given its iata code
    :param str iata_code: airport iata code
    :return (int, int): airport coordinate in latitude, longitude
    '''
    iata_code = iata_code.upper()
    request = urllib2.Request('{}airport/{}?user_key={}'.format(
        AERO_CODES_ENDPOINT, iata_code, AERO_KEY), headers={'Accept': 'application/json'})
    airport_info = json.loads(urllib2.urlopen(request).read())['airports'][0]
    return airport_info['lat'], airport_info['lng']


def get_new_coord(src_coord, dest_coord, miles_traveled):
    ''' Calculates the waypoint coordinate based on the number of miles traveled
    :param (int, int) src_coord: source coordinate in latitude, longitude
    :param (int, int) dest_coord: destination coordinate in latitude, longitude
    :param int miles_traveled:
    :return (int, int): waypoint coordinate in latitude, longitude
    '''
    total_distance = calculate_distance(src_coord, dest_coord)
    proportion_traveled = miles_traveled / total_distance

    slope = (dest_coord[0] - src_coord[0]) / (dest_coord[1] - src_coord[1])
    y_intercept = src_coord[0] - slope * src_coord[1]

    new_long = (dest_coord[1] - src_coord[1]) * proportion_traveled + src_coord[1]
    new_lat = slope * new_long + y_intercept
    return new_lat, new_long


def get_weather(coord, timestamp):
    ''' Gets weather information from forecast.io
    :param (int, int) coord: coordinate in latitude, longitude
    :param int timestamp: unix timestamp
    :return WeatherInfo: weather information for a given time and location
    '''
    request = urllib2.Request('{}{}/{},{},{}'.format(
        FORECAST_ENDPOINT, FORECAST_KEY, coord[0], coord[1], timestamp))
    forecast_info = json.loads(urllib2.urlopen(request).read())

    humidity = forecast_info['currently'].get('humidity')
    temperature = forecast_info['currently'].get('temperature')
    wind_speed = forecast_info['currently'].get('windSpeed')
    time_offset = forecast_info.get('offset')
    incomplete = any(i is None for i in [humidity, temperature, wind_speed, time_offset])

    WeatherInfo = collections.namedtuple('WeatherInfo', 'humidity, incomplete, temperature, wind_speed, time_offset')
    return WeatherInfo(humidity, incomplete, temperature, wind_speed, time_offset)


def resolve_location(location):
    ''' Gets the coordinates of a location provided as the IATA code or coordinate
    :param location: IATA code (str) or coordinate ((int, int) in latitude, longitude)
    :return: location's coordinate in latitude, longitude
    '''
    if ',' in location:
        lat_long = location.split(',')
        lat = int(lat_long[0])
        long = int(lat_long[1])
    else:
        lat, long = get_airport_coordinates(location)
    return lat, long


if __name__ == '__main__':
    app.run()
