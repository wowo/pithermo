PiThermo
========

Raspberry Pi Temperature fetching application using Python Flask microframework

Features
--------

* Fetches current temperatures from Dallas digital thermometers connected via 1wire (through GPIO)
* Collects temperatures and stores them in MongoDB database
* Shows temperatures graph (multiple series)

Technology
----------

* Dallas DS1820 thermometers connected via Onewire to GPIO (uses w1-gpio and w1-therm modules)
* Flask Python web microframework
* INK Framework (frontend)
* Google Charts API

Example
-------

![example](http://pbs.twimg.com/media/BBpdYxpCAAAV9g_.png:large)
