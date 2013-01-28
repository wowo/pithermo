#!/usr/bin/python

import csv
import gviz_api
import os
import pytz
import sys
from datetime import datetime
from flask import Flask
from flask import render_template

DATE_FORMAT='%H:%M %Y-%m-%d'

app = Flask(__name__)

@app.route("/")
def hello():
    data = []
    with open('temperatures.tsv') as csvfile:
      reader = csv.reader(csvfile, dialect='excel-tab')
      for row in reader:
        data.append({'date': datetime.strptime(row[0], DATE_FORMAT), 'temperature': float(row[1])})

    data_table = gviz_api.DataTable({'date': ('datetime', 'Czas'), 'temperature': ('number', 'Temperatura')})
    data_table.LoadData(data)
    
    vars = collect()
    vars['data_table'] = data_table.ToJSon()
    return render_template('main.html', **vars)

def collect():
    temp = os.popen('cat /sys/bus/w1/devices/28-*/w1_slave | tail -n1 | cut -f2 -d= | awk \'{print $1/1000}\'').read()

    return {
      'temperature': round(float(temp), 1),
      'date': datetime.now(pytz.timezone('Europe/Warsaw')).strftime(DATE_FORMAT)
    }

if __name__ == "__main__" and len(sys.argv) == 1:
    app.run(host='0.0.0.0', debug=True)
else:
    sensor = collect()
    print "%s\t%s" % (sensor['date'], sensor['temperature'])
