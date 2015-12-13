from flask import Flask, jsonify
import logging
import sys

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

@app.route('/')
def test():
    return 'Hello World!'