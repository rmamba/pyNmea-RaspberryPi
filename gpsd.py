#!/usr/bin/python
# FIlename: gpsd.py

'''
Created on 17 Dec 2013

@author: rmamba@gmail.com
'''

from daemon import Daemon
from decimal import Decimal

import sys
import time
import math
import json

#sudo apt-get install python-serial
import serial

class MyDaemon(Daemon):
    def _writeLog(self, msg, isDate=True):
        sys.stdout.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        sys.stdout.flush()
    
    def _writeErr(self, msg, isDate=True):
        sys.stderr.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        sys.stderr.flush()
    def _toDoubleLatLong(self, latlon, side):
        val = 0
        tmp = Decimal(latlon)
        tmp /= 100
        val = math.floor(tmp)
        tmp = (tmp - val) * 100
        val += tmp/60
        tmp -= math.floor(tmp)
        tmp *= 60
        if ((side.ToUpper() == "S") or (side.ToUpper()=="W")):
            val *= -1
        return val
    
    def run(self):
        while True:
            line = self.__ser.readline()
            if (self.__hislog != None):
                self.__hislog.write(line)
            if (line.startwith('$GPGGA')):
                GGA = line.split(',')
                self.GPS['DateTime']['time'] = GGA[1]
                self.GPS['Lat'] = self._toDoubleLatLong(GGA[2], GGA[3]) 
                self.GPS['Lon'] = self._toDoubleLatLong(GGA[4], GGA[5])
                self.GPS['Satellites'] = GGA[7]
                self.GPS['Dilution'] = GGA[8]
                self.GPS['Alt'] = GGA[9]
            if (line.startwith('$GPRMC')):
                RMC = line.split(',')
                self.GPS['DateTime']['utc'] = RMC[1]
                self.GPS['Warning'] = RMC[2]
                
                self.GPS['Speed']['knots'] = RMC[7]
                self.GPS['Speed']['kmh'] = RMC[7] * 1.85200000
                self.GPS['Speed']['kmh'] = RMC[7] * 1.15077945
                self.GPS['Speed']['mps'] = RMC[7] * 0.51444444
                self.GPS['Direction'] = RMC[8]
                self.GPS['DateTime']['date'] = RMC[9]
            
    def begin(self):
        self._writeLog("Starting(%s)..." % self.pidfile)
        self.GPS = {'Lat':None, 'Lon':None, 'Alt':None, 'Direction':None, 'Satellites':None, 'Quality':None, 'Dilution':None, 'DateTime': {'utc', 'time', 'date'}, 'Speed': {'knots', 'kmh', 'mph', 'mps'}, 'Warning': None }
        #self.nmea = NMEA(self.__device, self.__baud, self.__timeout)
        
        try:
            self.__hislog = None
            if (self.__history != None):
                self.__hislog = open(self.__history, 'w')
        except:
            self._writeErr("Exception crating history file %s" % self.__history)
            self.stop()
        
        try:
            self._writeLog("Opening port %s" % self.__device)
            self.__ser = serial.Serial(port=self.__device, baudrate=self.__baud, timeout=self.__timeout)
            if (self.__ser != None):
                self._writeLog("Opened...")
                
        except:
            self._writeErr("Exception opening port %s" % self.__device)
            self.stop()

    def end(self):
        if (self.__ser != None):
            self.__ser.close()
        if (self.__hislog != None):
            self.__hislog.close()
        del self.__ser
        del self.__hislog
        self._writeLog("Exiting...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: %s start|stop|restart|location|json|pjson" % sys.argv[0])
        sys.exit(2)
    
    f = open('gpsd.config', 'r')
    s = f.read()
    __config = json.loads(s)
    f.close()
    if (__config['device']==''):
        print("Device not found in configuration file")
        sys.exit(1)

    __device = __config['device']
    __baud = __config['baud']
    __log = __config['log']
    __history = __config['history']
        
    daemon = MyDaemon('/var/run/gpsd.pid', '/dev/null', __log, '/var/log/gpsd.error.log', __device, __baud, __history)

    if 'start' == sys.argv[1]:
        daemon.start()
    elif 'stop' == sys.argv[1]:
        daemon.stop()
    elif 'restart' == sys.argv[1]:
        daemon.restart()
    elif 'location' == sys.argv[1]:
        print json.dumps(daemon.GPS) #, indent=4, separators=(',', ': '))
    else:
        print("Unknown command")
        sys.exit(2)
    sys.exit(0)
