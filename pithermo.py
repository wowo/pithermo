#!/usr/bin/python

import csv
import gviz_api
import os
import pytz
import sys
import appconfig
from datetime import datetime
from flask import Flask
from flask import render_template
from pymongo import MongoClient

DATE_FORMAT='%H:%M %Y-%m-%d'

app = Flask(__name__)


@app.route("/")
def hello():
    data = [temperature for temperature in getCollection().find()]
    data_table = gviz_api.DataTable({'date': ('datetime', 'Czas'), 'temperature': ('number', 'Temperatura')})
    data_table.LoadData(data)
    
    current = collect()
    current['data_table'] = data_table.ToJSon()

    return render_template('main.html', **current)

def collect():
    temp = os.popen('cat /sys/bus/w1/devices/28-*/w1_slave | tail -n1 | cut -f2 -d= | awk \'{print $1/1000}\'').read()
    date = datetime.now()

    return {
      'temperature': round(float(temp), 1),
      'date': date,
      'date_literal': date.strftime(DATE_FORMAT),
      'sensor': 'living-room'
    }

def store():
    getCollection().insert(collect())

def getCollection():
    conn = MongoClient(appconfig.MONGO_HOST, appconfig.MONGO_PORT)
    db = conn[appconfig.MONGO_COLLECTION]
    db.authenticate(appconfig.MONGO_USER, appconfig.MONGO_PASS)

    return db.temperatures


if __name__ == "__main__" and len(sys.argv) == 1:
    app.run(host='0.0.0.0', debug=True)
else:
    store()
