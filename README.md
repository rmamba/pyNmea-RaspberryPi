README for pyNmea-RaspberryPi
==================

Python daemon for NMEA based serial/usb GPS receivers on RaspberryPi.  
I needed a GPS daemon that would continuously update position in memory on raspberry Pi (
This is done by pyRestDb project).  
Position can be returned by calling the daemon with correct parameter via command line. Or any other program that can access pyRestDb.  
```
sudo ./gpsd.py json
sudo ./gpsd.py pjson
sudo ./gpsd.py location
sudo ./gpsd.py gmaps
```

Links:
======

pyNmea-RaspberryPi. . . . . https://github.com/rmamba/pyNmea-RaspberryPi/  
pyRestDb  . . . . . . . . . https://github.com/rmamba/pyRestDb/  

Install:
========

Grab a release from github.com and unpack it on your rPi. 
https://github.com/rmamba/pyNmea-RaspberryPi/releases  
All you need to do now is run the command (assuming you're in the same folder as gpsd.py): 
```
sudo ./gpsd.py start
```

ToDO...


Source Code Content:
===================
daemon.py          - Daemon logic  
gpsd.config        - Configuration file  
gpsd.py            - Main program  
README             - This file  
LICENCE            - MIT Licence  

