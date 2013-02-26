#!/usr/bin/python

from datetime import datetime, timedelta
from flask import Flask, render_template, request
from pymongo import MongoClient
import csv
import yaml
import json
import os
import pytz
import re
import sys

DATE_FORMAT='%H:%M %Y-%m-%d'

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('main.html', sensors=collect(), days=request.args.get('days',2))

@app.route('/history')
def history():
    start = datetime.now() - timedelta(days=int(request.args.get('days', 2)))
    data = []
    documents = []
    headers = {'date': 'Data'}
    for temperature in getCollection().find({'date': {'$gte': start}}).sort('date', 1):
        if 'sensors' not in temperature:
            continue

        documents.append(temperature)
        for address in temperature['sensors']:
            if address not in headers and 'name' in temperature['sensors'][address]:
                headers[address] = temperature['sensors'][address]['name']

    row = []
    for key in headers:
        row.append(headers[key])

    data.append(row)

    for document in documents:
        row = [document['date'].strftime('%m-%d %H:%M')]
        for key in headers:
            if key != 'date':
                row.append(document['sensors'][key]['temperature'] if key in document['sensors'] else None)

        data.append(row)

    return json.dumps(data)

def collect():
    sensors = getConfig()['sensors']
    command = 'cat /sys/bus/w1/devices/%s/w1_slave | tail -n1 | cut -f2 -d= | awk \'{print $1/1000}\''
    for address in sensors:
        if os.path.exists('/sys/bus/w1/devices/' + address):
            temperature = None
            while temperature is None:
                sensor = open('/sys/bus/w1/devices/' + address + '/w1_slave', 'r').read().replace("\n", " ")
                if re.search(r"crc=.* YES", sensor):
                    match = re.search(r"t=([0-9\-]+)", sensor)
                    temperature = round(float(match.group(1)) / 1000, 1)
            sensors[address]['temperature'] = temperature

    return sensors

def output():
    print yaml.dump(collect(), default_flow_style=False)

def store():
    getCollection().insert({
        'date': datetime.now(),
        'sensors': collect()
    })

def getCollection():
    config = getConfig()['database']

    conn = MongoClient(config['host'], config['port'])
    db = conn[config['collection']]
    db.authenticate(config['user'], config['pass'])

    return db.temperatures

def migrate():
    return
    addresses = {'outdoor': '28-00000476ee01', 'living-room': '28-0000047632af'}
    db = getCollection()
    temps = {}
    for document in db.find({'date': {'$lte': datetime(2013, 2, 17, 18, 00)}, 'sensor': {'$exists': True}, 'sensors': {'$exists': False}}):
        if document['date'] not in temps:
            temps[document['date']] = {'date': document['date'], 'sensors': {}}

        print document
        temps[document['date']]['sensors'][addresses[document['sensor']]] = {
            'id': document['sensor'],
            'temperature': document['temperature']
        }
        db.remove(document)

    for date in temps:
        db.insert(temps[date])

def getConfig():
  return yaml.load(file(os.path.dirname(os.path.realpath(__file__)) + '/config.yml'))

if __name__ != 'pithermo': # wsgi
    if __name__ == "__main__" and len(sys.argv) == 1:
        #app.run(host='0.0.0.0', debug=True)
        app.run(host='91.227.39.112', port=8000, debug=True)
    elif sys.argv[1] == '--migrate':
        migrate()
    elif sys.argv[1] == '--output':
        output()
    else:
        store()
