from flask import Flask, jsonify
import logging
import sys

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
        lat = lat_long[0]
        long = lat_long[1]
    else:
        lat = 0
        long = 0
    jsonify(location=[lat, long])