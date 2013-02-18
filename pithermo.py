#!/usr/bin/python

from datetime import datetime, timedelta
from flask import Flask
from flask import render_template
from pymongo import MongoClient
import csv
import yaml
import json
import os
import pytz
import sys

DATE_FORMAT='%H:%M %Y-%m-%d'

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('main.html', sensors=collect())

@app.route('/history')
def history():
    start = datetime.now() - timedelta(days=2)
    data = []
    documents = []
    headers = {'date': 'Data'}
    for temperature in getCollection().find({'date': {'$gte': start}}):
        if 'sensors' not in temperature:
            continue

        documents.append(temperature)
        for sensor in temperature['sensors']:
            if temperature['sensors'][sensor]['id'] not in headers:
                headers[sensor] = temperature['sensors'][sensor]['name']

    row = []
    for key in headers:
        row.append(headers[key])

    data.append(row)

    for document in documents:
        row = [document['date'].strftime('%Y-%m-%d %H:%M')]
        for key in headers:
            if key != 'date':
                row.append(document['sensors'][key]['temperature'])

        data.append(row)

    return json.dumps(data)

def collect():
    sensors = yaml.load(file(os.path.dirname(__file__) + '/config.yml'))['sensors']
    command = 'cat /sys/bus/w1/devices/%s/w1_slave | tail -n1 | cut -f2 -d= | awk \'{print $1/1000}\''
    for address in sensors:
        if os.path.exists('/sys/bus/w1/devices/' + address):
            sensors[address]['temperature'] = round(float(os.popen(command % address).read()), 1)

    return sensors

def store():
    getCollection().insert({
        'date': datetime.now(),
        'sensors': collect()
    })

def getCollection():
    config = yaml.load(file(os.path.dirname(__file__) + '/config.yml'))['database']

    conn = MongoClient(config['host'], config['port'])
    db = conn[config['collection']]
    db.authenticate(config['user'], config['pass'])

    return db.temperatures

def migrate():
    return
    addresses = {'outdoor': '28-00000476ee01', 'living-room': '28-0000047632af'}
    db = getCollection()
    temps = {}
    for document in db.find({'date': {'$gt': datetime(2013, 2, 17, 18, 00)}, 'id': {'$exists': True}}):
        if document['date'] not in temps:
            temps[document['date']] = {'date': document['date'], 'sensors': {}}

        print document
        temps[document['date']]['sensors'][addresses[document['id']]] = {
            'id': document['id'],
            'name': document['name'],
            'temperature': document['temperature']
        }
        db.remove(document)

    for date in temps:
        db.insert(temps[date])

if __name__ == "__main__" and len(sys.argv) == 1:
    app.run(host='0.0.0.0', debug=True)
else:
    store()
