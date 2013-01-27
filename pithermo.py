#!/usr/bin/python

import os
import sys
import pytz
from datetime import datetime
from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('main.html', **collect())

def collect():
    return {
      'temperature': os.popen('cat /sys/bus/w1/devices/28-*/w1_slave | tail -n1 | cut -f2 -d= | awk \'{print $1/1000}\'').read(),
      'date': datetime.now(pytz.timezone('Europe/Warsaw')).strftime('%H:%M %Y-%m-%d')
    }

if __name__ == "__main__" and len(sys.argv) == 1:
    app.run(host='0.0.0.0', debug=True)
else:
    sensor = collect()
    print "%s\t%s" % (sensor['date'], sensor['temperature'].rstrip('\r\n'))
