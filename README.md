PiThermo
========

Raspberry Pi Temperature fetching application using Python Flask microframework

Features:
* Fetches current temperature from Dallas digital thermometer connected via Onewire (through GPIO)
* Collects temperature in TSV format, which can be easily stored in a file
* Shows temperature graph

Technology:
* Dallas DS1820 thermometer connected via Onewire to GPIO (uses w1-gpio and w1-therm modules)
* Flask Python web microframework
* Twitter Bootstrap 2.2
* Google Charts API
