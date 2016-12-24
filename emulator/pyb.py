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
import os
import struct

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
		self.pwmsValue = [0,0,0,0,0,0,0,0,0,0,0]
		self.pwmFreq = 0
		self.adcValues = [0,0,0]
		self.dacMode = 0
		self.dacFreq = 0
		self.dacData = None

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
			if data["per"]=="PWMREQUEST":
				PeripheralMockManager.updatePwms() 	
			if data["per"]=="DACREQUEST":
				PeripheralMockManager.updateDac() 	
			if data["per"]=="ADC":
				index = data["data"]
				value = data["data2"]
				PeripheralMockManager.cpu.adcValues[index] = value	

			if data["per"]=="UART":
				bytes = bytearray()
				try:
					hexData = str(data["data"]).decode("hex")
					bytes.extend(hexData)
				except:
					pass
					
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
	def updatePwms():
		PeripheralMockManager.sendData(json.dumps({"per":"PWM","data":PeripheralMockManager.cpu.pwmsValue,"data2":PeripheralMockManager.cpu.pwmFreq}))
	
	@staticmethod
	def updateDac():
		PeripheralMockManager.sendData(json.dumps({"per":"DAC","data":PeripheralMockManager.cpu.dacMode,"data2":PeripheralMockManager.cpu.dacFreq,"data3":PeripheralMockManager.cpu.dacData}))

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
		self.__packet_mode=False
		self.__packet_end_char=None
		
	def init(self,baudrate,bits=8,parity=None,stop=1,timeout=0,timeout_char=0,read_buf_len=2048,packet_mode=False,packet_end_char=None):
		self.__baudrate = baudrate
		self.__timeout=timeout
		self.__timeout_char=timeout_char
		self.__packet_mode=packet_mode
		self.__packet_end_char=packet_end_char
		
	def write(self,data):
		if isinstance(data, basestring):
			#data is a string. Convert to hexascii 
			data = "".join("{:02x}".format(ord(c)) for c in data)
		elif isinstance(data, bytearray):
			#data is a bytearray. Convert to hexascii
			data = "".join("{:02x}".format(c) for c in data)
		else:
			return
	
		if self.__timeout_char==0:
			PeripheralMockManager.sendData(json.dumps({"per":"UART","data":data,"uartn":self.__uartNumber}))
		else:
			i=0
			while i<len(data):
				PeripheralMockManager.sendData(json.dumps({"per":"UART","data":data[i]+data[i+1],"uartn":self.__uartNumber}))
				time.sleep(self.__timeout_char/1000.0)
				i=i+2
		
	def writechar(self,data):
		PeripheralMockManager.sendData(json.dumps({"per":"UART","data":data,"uartn":self.__uartNumber}))

	def get_baudrate(self):
		return self.__baudrate 

	def any(self):
		r = False
		if self.__packet_mode==False:
			# byte mode
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
		else:
			#packet mode			
			if self.__uartNumber==0:
				PeripheralMockManager.cpu.rs485Mutex.acquire()
				if self.__timeout==0:
					#use end char
					for b in PeripheralMockManager.cpu.rs485Buffer:
						if b==self.__packet_end_char:
							r=True
							break
				else:
					#use timeout
					if len(PeripheralMockManager.cpu.rs485Buffer)>0:
						r = True
				PeripheralMockManager.cpu.rs485Mutex.release()
			if self.__uartNumber==3:
				PeripheralMockManager.cpu.uartMutex.acquire()
				if self.__timeout==0:
					#use end char
					for b in PeripheralMockManager.cpu.uartBuffer:
						#print("comparo:"+str(b)+" con:"+str(self.__packet_end_char))
						if b==self.__packet_end_char:
							r=True
							break
				else:
					#use timeout
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
			
		
	
class PWM:

	def __init__(self,pwmNumber):
		if pwmNumber>10 or pwmNumber<0:
			raise Exception("Invalid PWM number")
		self.pwmNumber = pwmNumber
		self.duty = 0
		
	@staticmethod
	def set_frequency(freq):
		PeripheralMockManager.cpu.pwmFreq = freq
		PeripheralMockManager.updatePwms()
		
	def duty_cycle(self,val=None):
		if val==None:
			return PeripheralMockManager.cpu.pwmsValue[self.pwmNumber]
		PeripheralMockManager.cpu.pwmsValue[self.pwmNumber] = val
		PeripheralMockManager.updatePwms()
		
	
class ADC:
	
	def __init__(self,adcNumber):
		if adcNumber>3 or adcNumber<=0:
			raise Exception("Invalid ADC number")
		self.adcNumber = adcNumber - 1
		
	def read(self):
		return PeripheralMockManager.cpu.adcValues[self.adcNumber]
		
class DAC:

	__MODE_VAL = 0
	__MODE_NOISE = 1
	__MODE_TRIAN = 2
	__MODE_TIMED = 3

	CIRCULAR = 0
	NORMAL = 1
	
	
	def __init__(self,dacNumber):
		if dacNumber>3 or dacNumber<=0:
			raise Exception("Invalid DAC number")
			
		PeripheralMockManager.cpu.dacMode = DAC.__MODE_VAL
		self.timedMode = DAC.CIRCULAR
		
	def write(self,v):
		PeripheralMockManager.cpu.dacMode = DAC.__MODE_VAL
		if PeripheralMockManager.cpu.dacData == None:
			PeripheralMockManager.cpu.dacData = list()
			PeripheralMockManager.cpu.dacData.append(int(v))
		else:
			PeripheralMockManager.cpu.dacData[0] = int(v)
		PeripheralMockManager.updateDac()
		
	def noise(self,f):
		PeripheralMockManager.cpu.dacMode = DAC.__MODE_NOISE
		PeripheralMockManager.cpu.dacFreq = f
		PeripheralMockManager.updateDac()
		
	def triangle(self,f):
		PeripheralMockManager.cpu.dacMode = DAC.__MODE_TRIAN
		PeripheralMockManager.cpu.dacFreq = f
		PeripheralMockManager.updateDac()
	
	def write_timed(self,data,freq,mode):
		PeripheralMockManager.cpu.dacMode = DAC.__MODE_TIMED
		buf = list()
		index=0
		while index<len(data):
			l = data[index]
			index+=1
			h = data[index]
			index+=1			
			buf.append(int(h<<8|l))
		PeripheralMockManager.cpu.dacData = buf
		self.timedMode = mode
		PeripheralMockManager.cpu.dacFreq = freq / len(buf)
		PeripheralMockManager.updateDac()
	
class EEPROM:

	__CONFIG_FILENAME = ".educiaapythonemulatoreeprom.dat"
	
	def __init__(self):
		try:
			from win32com.shell import shellcon, shell            
			self.homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
		except ImportError:
			self.homedir = os.path.expanduser("~")		
		self.homedir = os.path.join(self.homedir,".educiaa-python-emulator")
		if not os.path.exists(self.homedir):
			os.makedirs(self.homedir)
		#print("Home dir:"+self.homedir)
		self.absolutePath = os.path.join(self.homedir,EEPROM.__CONFIG_FILENAME)
		if not os.path.exists(self.absolutePath):
			self.__createCleanFile()
		
	def write_byte(self,addr,val):
		if addr>=(16*1024):
			raise Exception("Invalid address")
		with open(self.absolutePath, 'r+b') as f:
			f.seek(addr)
			b = bytearray()
			b.append(val&0xFF)
			f.write(b)

	def write_int(self,addr,val):
		bytes = struct.pack("<I", val)
		for b in bytes:
			self.write_byte(addr,ord(b))
			addr+=1
		
		
	def write_float(self,addr,val):
		bytes = struct.pack("<f", val)
		for b in bytes:
			self.write_byte(addr,ord(b))
			addr+=1
		
	def write(self,val):
		addr=0
		for b in val:
			self.write_byte(addr,ord(b))
			addr+=1


			
	def read_byte(self,addr):
		r = -1
		if addr>=(16*1024):
			raise Exception("Invalid address")
		with open(self.absolutePath, 'r+b') as f:
			f.seek(addr)
			r = f.read(1)
			b = bytearray()
			b.append(r)
			return b[0]
		return r	

	def read_int(self,addr):
		b0 = self.read_byte(addr)
		b1 = self.read_byte(addr+1)
		b2 = self.read_byte(addr+2)
		b3 = self.read_byte(addr+3)
		return b3<<24 | b2<<16 | b1<<8 | b0

	def read_float(self,addr):
		b0 = self.read_byte(addr)
		b1 = self.read_byte(addr+1)
		b2 = self.read_byte(addr+2)
		b3 = self.read_byte(addr+3)
		b = bytearray()
		b.append(b0)
		b.append(b1)
		b.append(b2)
		b.append(b3)
		f = struct.unpack("<f", str(b))
		return f[0]
		
	def readall(self):
		out = bytearray()
		addr=0
		while True:
			b = self.read_byte(addr)
			if b==0x00:
				break
			out.append(b)
			addr+=1
				
		return str(out)
		
	def __createCleanFile(self):
		with open(self.absolutePath, 'wb') as f:
			myArr = bytearray(16*1024)
			f.write(myArr)
	