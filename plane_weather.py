from flask import Flask, jsonify
import json
import logging
import sys
import urllib2

AERO_API_KEY = '83af8148873102bc1995d8aa5938df18'
AERO_CODES_ENDPOINT = 'https://airport.api.aero/'

app = Flask(__name__)
app.config['DEBUG'] = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)


@app.route('/')
def test():
    return 'Hello World!'


@app.route('/resolve/<location>')
def resolve_location(location):
    if ',' in location:
        lat_long = location.split(',')
        lat = int(lat_long[0])
        long = int(lat_long[1])
    else:
        lat, long = get_airport_coordinates(location)

    return jsonify(location=[lat, long])


def get_airport_coordinates(iata_code):
    iata_code = iata_code.upper()
    request = urllib2.Request('{}airport/{}?user_key={}'.format(
        AERO_CODES_ENDPOINT, iata_code, AERO_API_KEY), headers={'Accept': 'application/json'})
    airport_info = json.loads(urllib2.urlopen(request).read())['airports'][0]
    return airport_info['lat'], airport_info['lng']


print(get_airport_coordinates('rdu'))