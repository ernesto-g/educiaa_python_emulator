########################################################################
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

#
#	EDU-CIAA Python editor (2016)
#	
#	<ernestogigliotti@gmail.com>
#
########################################################################

import json
import time
import threading
import sys
import Queue
from threading import Lock

class CPUMock:
	def __init__(self):
		self.sws = [True,True,True,True]		
		self.leds = [False,False,False,False,0,0,0]
		self.gpiosValue = [0,0,0,0,0,0,0,0,0]
		self.gpiosMode = [0,0,0,0,0,0,0,0,0]
		self.gpiosPull = [0,0,0,0,0,0,0,0,0]
		self.uartBuffer = bytearray()
		self.rs485Buffer = bytearray()
		self.uartMutex = Lock()
		self.rs485Mutex = Lock()
		

class PeripheralMockManager:
	socket = None
	cpu = CPUMock()
	stdinQueue = Queue.Queue()
	stdinBuffer = ""
	stdinCondition = threading.Condition()

	@staticmethod
	def pmm_setSocket(s):
		PeripheralMockManager.socket = s
	@staticmethod
	def sendData(data):
		if PeripheralMockManager.socket!=None:
			try:
				PeripheralMockManager.socket.send(data)
				#try:
				#	PeripheralMockManager.socket.close()
				#except:
				#	pass
			except:
				pass
	@staticmethod
	def pmm_startReception():
		if PeripheralMockManager.socket!=None:
			t = threading.Thread(target=PeripheralMockManager.runReception)
			t.daemon = True
			t.start()
	@staticmethod
	def runReception():
		while True:
			try:
				data = PeripheralMockManager.socket.recv(4096)
			except:
				print(">>pyb>>RCV ERROR. closing socket")
				PeripheralMockManager.socket.close()
				return
			
			try:
				data = json.loads(data)
			except:
				if len(data)==0:
					print(">>pyb>>RCV ERROR JSON. closing socket")				
					PeripheralMockManager.socket.close()
					return
				else:
					continue
				
			if data["per"]=="Switch":
				PeripheralMockManager.cpu.sws[data["swn"]] = data["swv"]
			if data["per"]=="GPIO":
				PeripheralMockManager.cpu.gpiosValue[data["gpion"]] = data["gpiov"]
			if data["per"]=="GPIOREQUEST":
				PeripheralMockManager.updateGpios() 	

			if data["per"]=="UART":
				bytes = bytearray()
				bytes.extend(data["data"])
				if data["uartn"]==3:
					PeripheralMockManager.cpu.uartMutex.acquire()
					for b in bytes:
						PeripheralMockManager.cpu.uartBuffer.append(b)
					PeripheralMockManager.cpu.uartMutex.release()
				if data["uartn"]==0:
					PeripheralMockManager.cpu.rs485Mutex.acquire()
					for b in bytes:
						PeripheralMockManager.cpu.rs485Buffer.append(b)
					PeripheralMockManager.cpu.rs485Mutex.release()
					
			if data["per"]=="STDIN":
				if data["data"]=="\n" or data["data"]=="\r\n":
					PeripheralMockManager.stdinCondition.acquire()
					PeripheralMockManager.stdinQueue.put(PeripheralMockManager.stdinBuffer)
					PeripheralMockManager.stdinCondition.notify()
					PeripheralMockManager.stdinCondition.release()
					PeripheralMockManager.stdinBuffer = ""
					PeripheralMockManager.sendData(json.dumps({"per":"STDOUT","data":data["data"]})) # echo
				else:
					if data["data"]=="\b":
						if len(PeripheralMockManager.stdinBuffer)>=1:
							PeripheralMockManager.sendData(json.dumps({"per":"STDOUT","data":"\x1b[K"})) # echo
							PeripheralMockManager.stdinBuffer = PeripheralMockManager.stdinBuffer[0:-1]
					else:
						PeripheralMockManager.sendData(json.dumps({"per":"STDOUT","data":data["data"]})) # echo
						PeripheralMockManager.stdinBuffer+=data["data"]

				
	@staticmethod
	def updateLeds():
		PeripheralMockManager.sendData(json.dumps({"per":"LED","data":PeripheralMockManager.cpu.leds}))

	@staticmethod
	def updateGpios():
		PeripheralMockManager.sendData(json.dumps({"per":"GPIO","data":PeripheralMockManager.cpu.gpiosValue,"data2":PeripheralMockManager.cpu.gpiosMode}))
		
	@staticmethod
	def readStdin():
		while True:
			PeripheralMockManager.stdinCondition.acquire()
			if not PeripheralMockManager.stdinQueue.empty():
				r = PeripheralMockManager.stdinQueue.get()
				PeripheralMockManager.stdinCondition.release()
				return r
			else:
				PeripheralMockManager.stdinCondition.wait()
				PeripheralMockManager.stdinCondition.release()
		
# functions
def delay(val):
	time.sleep(val/1000.0)

# classes		
class LED:
	def __init__(self,ledNumber):
		self.__ln=ledNumber-1		
	def on(self):
		PeripheralMockManager.cpu.leds[self.__ln] = True
		PeripheralMockManager.updateLeds()
	def off(self):
		PeripheralMockManager.cpu.leds[self.__ln] = False
		PeripheralMockManager.updateLeds()
	def intensity(self,val):
		PeripheralMockManager.cpu.leds[self.__ln] = val
		PeripheralMockManager.updateLeds()

class Switch:
	def __init__(self,swNumber):
		self.__sn=swNumber-1
		self.__threadCallback = None
		self.__state0 = False
	def switch(self):
		return PeripheralMockManager.cpu.sws[self.__sn]
	def callback(self,fn):
		self.__fnCallback = fn
		if self.__threadCallback == None:
			t = threading.Thread(target=self.__callbackPool)
			t.daemon = True
			t.start()
	def __callbackPool(self):
		while True:
			time.sleep(0.1)
			#print("pool estado sw")
			try:
				if PeripheralMockManager.cpu.sws[self.__sn] == False:
					if self.__state0==False:
						self.__fnCallback(self)
						self.__state0 = True
				else:
					self.__state0 = False
			except:
				break

class Pin:
	IN = 0
	OUT_PP = 1
	OUT_OD = 2

	PULL_NONE = 0
	PULL_UP = 1
	PULL_DOWN = 2
	
	def __init__(self,gpioNumber):
		if gpioNumber>=9:
			raise Exception("Invalid GPIO "+str(gpioNumber))
			
		self.__gpioNumber = gpioNumber
	
	def init(self,mode,pull):
		PeripheralMockManager.cpu.gpiosMode[self.__gpioNumber] = mode
		PeripheralMockManager.cpu.gpiosPull[self.__gpioNumber] = pull
		PeripheralMockManager.updateGpios()
		
	def low(self):
		if PeripheralMockManager.cpu.gpiosMode[self.__gpioNumber]!=Pin.IN:
			PeripheralMockManager.cpu.gpiosValue[self.__gpioNumber] = 0
			PeripheralMockManager.updateGpios()

	def high(self):
		if PeripheralMockManager.cpu.gpiosMode[self.__gpioNumber]!=Pin.IN:
			PeripheralMockManager.cpu.gpiosValue[self.__gpioNumber] = 1
			PeripheralMockManager.updateGpios()
		
	def value(self):
		return PeripheralMockManager.cpu.gpiosValue[self.__gpioNumber]
		
	def internal_getGpioNumber(self):
		return self.__gpioNumber

class ExtInt:
	IRQ_RISING = 0
	IRQ_FALLING = 1
	IRQ_RISING_FALLING = 2
	
	def __init__(self,pinObj,irqMode,pull,callback):
		self.__pinObj=pinObj
		self.__irqMode=irqMode
		self.__pull=pull
		self.__fnCallback=callback
		self.__line = pinObj.internal_getGpioNumber()
		self.__enable=True
		self.__state0 = PeripheralMockManager.cpu.gpiosValue[self.__line]
		self.__state1 = self.__state0

		t = threading.Thread(target=self.__callbackPool)
		t.daemon = True
		t.start()
		
	def line(self):
		return self.__line
		
	def enable(self):
		self.__enable=True
		
	def disable(self):
		self.__enable=False
		
	def swint(self):
		self.__fnCallback(self.__line)
		
	def __callbackPool(self):
		while True:
			time.sleep(0.1)
			#print("pool estado sw")
			try:
				self.__state1 = PeripheralMockManager.cpu.gpiosValue[self.__line]
				
				if self.__irqMode == ExtInt.IRQ_RISING:
					if  self.__state1 == True and self.__state0 == False:
						if self.__enable:
							self.__fnCallback(self.__line)
				elif self.__irqMode == ExtInt.IRQ_FALLING:
					if  self.__state1 == False and self.__state0 == True:
						if self.__enable:
							self.__fnCallback(self.__line)
				elif self.__irqMode == ExtInt.IRQ_RISING_FALLING:
					if  (self.__state1 == False and self.__state0 == True) or (self.__state1 == True and self.__state0 == False):
						if self.__enable:
							self.__fnCallback(self.__line)
						
				self.__state0 = self.__state1
			except:
				break
	
class UART:
	def __init__(self,uartNumber):
		self.__uartNumber=uartNumber
		if uartNumber!=0 and uartNumber!=3:
			raise Exception("Invalid UART number")
	
		self.__baudrate = None
		self.__timeout=0
		
	def init(self,baudrate,bits=8,parity=None,stop=1,timeout=0,timeout_char=0,read_buf_len=2048,packet_mode=False,packet_end_char=None):
		self.__baudrate = baudrate
		self.__timeout=timeout
		self.__timeout_char=timeout_char
		
	def write(self,data):
		if self.__timeout_char==0:
			PeripheralMockManager.sendData(json.dumps({"per":"UART","data":data,"uartn":self.__uartNumber}))
		else:
			for b in data:
				PeripheralMockManager.sendData(json.dumps({"per":"UART","data":b,"uartn":self.__uartNumber}))
				time.sleep(self.__timeout_char/1000.0)
		
	def writechar(self,data):
		PeripheralMockManager.sendData(json.dumps({"per":"UART","data":data,"uartn":self.__uartNumber}))

	def get_baudrate(self):
		return self.__baudrate 

	def any(self):
		r = False
		if self.__uartNumber==0:
			PeripheralMockManager.cpu.rs485Mutex.acquire()
			if len(PeripheralMockManager.cpu.rs485Buffer)>0:
				r = True
			PeripheralMockManager.cpu.rs485Mutex.release()
		if self.__uartNumber==3:
			PeripheralMockManager.cpu.uartMutex.acquire()
			if len(PeripheralMockManager.cpu.uartBuffer)>0:
				r = True
			PeripheralMockManager.cpu.uartMutex.release()
		return r

	def __internal_getByteFromBuffer(self):
		out = -1
		if self.__uartNumber==0:
			PeripheralMockManager.cpu.rs485Mutex.acquire()
			out = PeripheralMockManager.cpu.rs485Buffer[0]
			PeripheralMockManager.cpu.rs485Buffer = PeripheralMockManager.cpu.rs485Buffer[1:] #delete the read one
			PeripheralMockManager.cpu.rs485Mutex.release()
		if self.__uartNumber==3:
			PeripheralMockManager.cpu.uartMutex.acquire()
			out = PeripheralMockManager.cpu.uartBuffer[0]
			PeripheralMockManager.cpu.uartBuffer = PeripheralMockManager.cpu.uartBuffer[1:] #delete the read one			
			PeripheralMockManager.cpu.uartMutex.release()
		return out

	def __internal_waitData(self):
		t = self.__timeout
		while t>0 and self.any()==False:
			time.sleep(0.001) #1ms
			t=t-1
	
	def readchar(self):
		self.__internal_waitData()
		if self.any():
			return self.__internal_getByteFromBuffer()
		return -1
		
	def read(self,nBytes=2049):
		self.__internal_waitData()
		c=0
		out = bytearray()
		while c<nBytes and self.any(): 
			b = self.__internal_getByteFromBuffer()
			out.append(b)
			c=c+1
		return out
		
	def readall(self):
		return self.read()
		
	def readinto(self,buff,nBytes=2049):
		out = self.read(nBytes)
		for b in out:
			buff.append(b)
			
		
	