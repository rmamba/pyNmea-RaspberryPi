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
import requests

#sudo apt-get install python-serial
import serial

class MyDaemon(Daemon):
	
	def _writeLog(self, msg, isDate=True):
		sys.stdout.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
		sys.stdout.flush()
	
	def _writeErr(self, msg, isDate=True):
		sys.stderr.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
		sys.stderr.flush()
	
	def _isNoneOrEmptry(self, val):
		if (val==None) or (val==""):
			return True
		return False
	
	def _toDoubleLatLong(self, latlon, side):
		val = None
		if (self._isNoneOrEmptry(latlon) or self._isNoneOrEmptry(side)):
			return None
		try:
			tmp = float(latlon)
			tmp /= 100
			val = math.floor(tmp)
			tmp = (tmp - val) * 100
			val += tmp/60
			tmp -= math.floor(tmp)
			tmp *= 60
			if ((side.upper() == "S") or (side.upper()=="W")):
				val *= -1
		except ValueError:
			self._writeErr("Can't calculate from {0} side {1}".format(latlon, side))
			val = None
		return val
	
	def _toFloat(self, value):
		val = None
		if self._isNoneOrEmptry(value):
			return None
		try:
			val = float(value)
		except ValueError:
			self._writeErr("Can't convert to float: {0}".format(value))
			val = None
		return val
	
	def _toInt(self, value):
		val = None
		if self._isNoneOrEmptry(value):
			return None
		try:
			val = int(value)
		except ValueError:
			self._writeErr("Can't convert to int: {0}".format(value))
			val = None
		return val
	
	def run(self):
		while True:
			isChanged = False
			if self.__ser.inWaiting()>40:
				line = self.__ser.readline()
				if (self.__hislog != None):
					self.__hislog.write(line)
				if (line.startswith('$GPGGA')):
					GGA = line.split(',')
					self.GPS['DateTime']['time'] = self._toFloat(GGA[1])
					self.GPS['Lat'] = self._toDoubleLatLong(GGA[2], GGA[3]) 
					self.GPS['Lon'] = self._toDoubleLatLong(GGA[4], GGA[5])
					self.GPS['Url']['GoogleMaps'] = 'https://maps.google.com?q={Lat},{Lon}&z=17'.format(**self.GPS)
					self.GPS['Satellites'] = self._toInt(GGA[7])
					self.GPS['Dilution'] = self._toFloat(GGA[8])
					self.GPS['Alt'] = self._toFloat(GGA[9])
					isChanged = True
				if (line.startswith('$GPRMC')):
					RMC = line.split(',')
					self.GPS['DateTime']['utc'] = self._toFloat(RMC[1])
					self.GPS['Warning'] = RMC[2]
					
					_knots = self._toFloat(RMC[7])
					self.GPS['Speed']['knots'] = self.GPS['Speed']['kmh'] = self.GPS['Speed']['mph'] = self.GPS['Speed']['mps'] = None
					if _knots != None:
						self.GPS['Speed']['knots'] = _knots
						self.GPS['Speed']['kmh'] = _knots * 1.85200000
						self.GPS['Speed']['mph'] = _knots * 1.15077945
						self.GPS['Speed']['mps'] = _knots * 0.51444444
					self.GPS['Direction'] = self._toFloat(RMC[8])
					self.GPS['DateTime']['date'] = self._toInt(RMC[9])
					isChanged = True
				
				#if isChanged:
					r = requests.post(self.restDbUrl+'/post/GPS', data=json.dumps(self.GPS), headers={'Content-Type': 'application/json'})
					if r.status_code != 200:
						self._writeErr(r.text)
			time.sleep(.2)
			
	def begin(self):
		self._writeLog("Starting(%s)..." % self.pidfile)

		try:
			self.__hislog = None
			if (self.history != None):
				self.__hislog = open(self.history, 'w')
		except:
			self._writeErr("Exception creating history file %s" % self.history)
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
		print("usage: %s start|stop|restart|gmaps|json|pjson|location" % sys.argv[0])
		sys.exit(2)
	
	f = open('gpsd.config', 'r')
	s = f.read()
	__config = json.loads(s)
	f.close()
	
	__device = '/dev/ttyUSB0'
	if 'device' in __config:
		__device = __config['device']
	
	__baud = 4800
	if 'baud' in __config:
		__baud = __config['baud']
	
	__log = '/var/log/gpsd.log'
	if 'log' in __config:
		__log = __config['log']
		
	__errlog = '/var/log/gpsd.error.log'
	if 'errlog' in __config:
		__errlog = __config['errlog']
	
	__history = None
	if 'history' in __config:
		__history = __config['history']
		
	__dbUrl = '127.0.0.1:666'
	if 'RestDB' in __config:
		__dbUrl = 'http://' + __config['RestDB']
		
	__dbUrlPass = None
		
	daemon = MyDaemon('/var/run/gpsd.pid', '/dev/null', __log, __errlog, __device, __baud, __history, __dbUrl, __dbUrlPass)

	if 'start' == sys.argv[1]:
		daemon.start()
	elif 'stop' == sys.argv[1]:
		daemon.stop()
	elif 'restart' == sys.argv[1]:
		daemon.restart()
	elif 'gmaps' == sys.argv[1]:
		r = requests.get(__dbUrl+'/GPS')
		_json = json.loads(r.text)
		url = 'https://maps.google.com?q={Lat},{Lon}'.format(**_json)
		print url
	elif 'location' == sys.argv[1]:
		r = requests.get(__dbUrl+'/GPS')
		_json = json.loads(r.text)
		loc = "Lat: {Lat}\r\nLon: {Lon}\r\nAlt: {Alt}".format(**_json)
		print loc
	elif 'json' == sys.argv[1]:
		r = requests.get(__dbUrl+'/GPS')
		print r.text
	elif 'pjson' == sys.argv[1]:
		r = requests.get(__dbUrl+'/GPS?pjson')
		print r.text
	else:
		print("Unknown command")
		sys.exit(2)
	sys.exit(0)
