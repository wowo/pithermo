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
import urllib

DATE_FORMAT='%m-%d %H:%M'
LOG_FILE='failed-inserts.json'

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
        row = [document['date'].strftime(DATE_FORMAT)]
        for key in headers:
            if key != 'date':
                row.append(document['sensors'][key]['temperature'] if key in document['sensors'] else None)

        data.append(row)

    return json.dumps(mergeWithForecast(data))

@app.route('/sensor/<sensor>')
def sensor(sensor):
    sensors = getConfig()['sensors']
    for address in sensors:
        if sensor == sensors[address]['id']:
            return str(collectTemperatureFromSensor(address))

    # not found sensor with given id
    return 'n/a', 404

def mergeWithForecast(data):
    config = getConfig()['forecast']
    forecast = json.loads(urllib.urlopen('http://newmeteo.sznapka.pl/%d/%d' % (config['rows'], config['cols'])).read())
    data[0].append(forecast[0][1])
    length = len(data)
    for row in forecast[1:]:
        inserted = False
        for orig in data[1:length]:
            date = datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S")
            origDate = datetime.strptime(str(datetime.now().year) + '-' + orig[0], '%Y-' + DATE_FORMAT)
            delta = origDate - date
            if len(orig) < len(data[0]) and delta.seconds < (60 * 10 - 1) and delta.days == 0:
                orig.append(row[1])
                inserted = True
                break
        if not inserted:
            newRow = [date.strftime(DATE_FORMAT)]
            for i in range(1, len(data[0]) - 1):
                newRow.append(None)
            newRow.append(row[1])
            data.append(newRow)

    for orig in data[1:]:
        if len(orig) < len(data[0]):
            orig.append(None)

    merged = {}
    for orig in data[1:]:
        if orig[0] not in merged:
            merged[orig[0]] = orig

    headers = data[0]
    data = merged.values()
    data = sorted(data, key=lambda data: data[0])
    data.insert(0, headers)

    return data 

def collect():
    sensors = getConfig()['sensors']
    for address in sensors:
        sensors[address]['temperature'] = collectTemperatureFromSensor(address)

    return sensors

def collectTemperatureFromSensor(address):
    if not os.path.exists('/sys/bus/w1/devices/' + address):
        raise RuntimeException('sensor with %s address does not exists' % address)

    temperature = None
    while temperature is None:
        sensor = open('/sys/bus/w1/devices/' + address + '/w1_slave', 'r').read().replace("\n", " ")
        if re.search(r"crc=.* YES", sensor):
            match = re.search(r"t=([0-9\-]+)", sensor)
            temperature = round(float(match.group(1)) / 1000, 1)

    return temperature

def output():
    print yaml.dump(collect(), default_flow_style=False)

def store():
    try:
        document = {
            'date': datetime.now(),
            'sensors': collect()
        }
        getCollection().insert(document)
        insertFailed()
    except:
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime) else None
        log = open(LOG_FILE, 'a+')
        log.write(json.dumps(document, default=dthandler) + "\n")
        log.close()

def insertFailed():
    try:
        log = open(LOG_FILE, 'r')
    except IOError:
        print "Nothing to insert from failed inserts log"
        return

    collection = getCollection()
    lines = log.readlines()
    print "Processing %d lines" % len(lines)
    index = 0
    for line in lines:
        try:
            line = re.sub(r"(datetime.datetime\()(\d+), (\d+), (\d+), (\d+), (\d+), \d+, \d+\)(.*)", r'"\2-\3-\4T\5:\6:00.000000"\7', line)
            document = json.loads(line)
            document['date'] = datetime.strptime(document['date'], '%Y-%m-%dT%H:%M:%S.%f')
            document['date'] = document['date'].replace(second=0, microsecond=0)
            existing = collection.find_one({'date': {'$gte': document['date'], '$lte': document['date'] + timedelta(0, 60)}})
            if existing:
                print "Document with date %s exists, ommiting" % document['date']
            else: 
                print "Document with date %s does not exist" % document['date']
                collection.insert(document)

            index += 1
            if index % 50 == 0:
                print "Processed %d lines already (%.2f)" % (index, index / float(len(lines)))
        except:
            print line
            raise
    log.close()
    os.remove(LOG_FILE)

def getCollection():
    config = getConfig()['database']

    conn = MongoClient(config['host'], config['port'])
    db = conn[config['collection']]
    db.authenticate(config['user'], config['pass'])

    return db.temperatures

def getConfig():
  return yaml.load(file(os.path.dirname(os.path.realpath(__file__)) + '/config.yml'))

if __name__ != 'pithermo': # wsgi
    if __name__ == "__main__" and len(sys.argv) == 1:
        app.run(host='0.0.0.0', port=8000, debug=True)
        #app.run(host='91.227.39.112', port=8000, debug=True)
    elif sys.argv[1] == '--insert-failed':
        insertFailed()
    elif sys.argv[1] == '--output':
        output()
    else:
        store()
