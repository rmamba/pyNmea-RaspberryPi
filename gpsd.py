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
    
    #GPS = None
    
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', device='/dev/tty0', baud='9600', history=None):
        #self.GPS = {'Lat':None, 'Lon':None, 'Alt':None, 'Direction':None, 'Satellites':None, 'Quality':None, 'Dilution':None, 'DateTime': {'utc': None, 'time': None, 'date': None}, 'Speed': {'knots': None, 'kmh': None, 'mph': None, 'mps': None}, 'Warning': None }
        Daemon.__init__(self, pidfile, stdin, stdout, stderr, device, baud, history)
    
    def _writeLog(self, msg, isDate=True):
        sys.stdout.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        sys.stdout.flush()
    
    def _writeErr(self, msg, isDate=True):
        sys.stderr.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        sys.stderr.flush()
    def _toDoubleLatLong(self, latlon, side):
        val = 0
        tmp = float(latlon)
        tmp /= 100
        val = math.floor(tmp)
        tmp = (tmp - val) * 100
        val += tmp/60
        tmp -= math.floor(tmp)
        tmp *= 60
        if ((side.upper() == "S") or (side.upper()=="W")):
            val *= -1
        return val
    
    def run(self):
        
        while True:
            isChanged = False
            line = self.__ser.readline()
            if (self.__hislog != None):
                self.__hislog.write(line)
            if (line.startswith('$GPGGA')):
                GGA = line.split(',')
                self.GPS['DateTime']['time'] = GGA[1]
                self.GPS['Lat'] = self._toDoubleLatLong(GGA[2], GGA[3]) 
                self.GPS['Lon'] = self._toDoubleLatLong(GGA[4], GGA[5])
                self.GPS['Satellites'] = GGA[7]
                self.GPS['Dilution'] = GGA[8]
                self.GPS['Alt'] = float(GGA[9])
                isChanged = True
            if (line.startswith('$GPRMC')):
                RMC = line.split(',')
                self.GPS['DateTime']['utc'] = RMC[1]
                self.GPS['Warning'] = RMC[2]
                
                self.GPS['Speed']['knots'] = float(RMC[7])
                self.GPS['Speed']['kmh'] = float(RMC[7]) * 1.85200000
                self.GPS['Speed']['kmh'] = float(RMC[7]) * 1.15077945
                self.GPS['Speed']['mps'] = float(RMC[7]) * 0.51444444
                self.GPS['Direction'] = float(RMC[8])
                self.GPS['DateTime']['date'] = RMC[9]
                isChanged = True
            
            if isChanged:
                with open('/var/log/gps.json', 'w') as f:
                    f.write(json.dumps(self.GPS, indent=4, separators=(',', ': ')))
                    f.flush()
            
    def begin(self):
        self._writeLog("Starting(%s)..." % self.pidfile)

        try:
            self.__hislog = None
            if (self.history != None):
                self.__hislog = open(self.history, 'w')
        except:
            self._writeErr("Exception crating history file %s" % self.history)
            self.stop()
        
        try:
            self._writeLog("Opening port %s" % self.device)
            self.__ser = serial.Serial(port=self.device, baudrate=self.baud, timeout=self.timeout)
            if (self.__ser != None):
                self._writeLog("Opened...")
                
        except:
            self._writeErr("Exception opening port %s" % self.device)
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
        print("usage: %s start|stop|restart|gps|json|pjson" % sys.argv[0])
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
    #elif 'gps' == sys.argv[1]:
    #    print daemon.GPS
    #elif 'json' == sys.argv[1]:
    #    print json.dumps(daemon.GPS)
    #elif 'pjson' == sys.argv[1]:
    #    print json.dumps(daemon.GPS, indent=4, separators=(',', ': '))
    else:
        print("Unknown command")
        sys.exit(2)
    sys.exit(0)
