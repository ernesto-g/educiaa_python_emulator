import gtk 
import pango
import serial
import threading
import struct
import time
import datetime
import json
from PlotArea import PlotArea
import math


def createPwmFunction(delta):

	def pwmFunctionTemplate(x):
		x = x % (2*math.pi)
		x0 = delta*(2*math.pi)/100
		if x<x0:
			return 1
		return -1
	return pwmFunctionTemplate	
	
	
	
class PwmPanel:

	def __init__(self,basePath,closeCallback,socket):
		self.__socket = socket
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/PWMPanel.glade")
		except Exception,e:
			print(e)
			return
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title("PWM outs")
		
		self.lblFreq = builder.get_object("lblFreq")
		self.chkList = list()
		for i in range(0,11):
			chkPwm = builder.get_object("chkPwm"+str(i))
			chkPwm.connect("clicked", self.__checkEvent,(i))
			self.chkList.append(chkPwm)
		
		self.area= builder.get_object("drawingarea1")
		self.plotter = PlotArea(self.area);
		self.plotter.set_range(0, 4*math.pi, -1.5, 1.5)
		
		self.pwmValues = [0,0,0,0,0,0,0,0,0,0,0]
		self.pwmFreq = 0
		
		self.__threadRequestRunning=True
		self.t = threading.Thread(target=self.__sendStatusRequest)
		self.t.start()
		
		self.window.show_all()

		
		
	def __sendStatusRequest(self):
		while self.__threadRequestRunning:
			if self.__socket!=None:
				self.__socket.sendall(json.dumps({"per":"PWMREQUEST"})) # request initial data
			time.sleep(1)
			

	def __updateCheckValues(self):
		i=0
		for val in self.pwmValues:
			#print("pwm "+str(i)+" val:"+str(val))
			self.chkList[i].set_label("PWM_"+str(i)+" ("+str(val)+"%)")
			i=i+1
		
		v=""
		if self.pwmFreq<1000:
			v = str(self.pwmFreq)+" Hz"
		elif self.pwmFreq<1000000:
			v = str(self.pwmFreq/1000)+" kHz"
		else:
			v = str(self.pwmFreq/1000000)+" MHz"
			
		self.lblFreq.set_label(v)

	def __updateDrawings(self):
		index=0
		for widget in self.chkList:
			if widget.get_active():
				self.plotter.addFunction(index,createPwmFunction(self.pwmValues[index]))
			else:
				self.plotter.addFunction(index,None)		
			index+=1
		self.plotter.updateGraph()


	def update(self,data):
		gtk.gdk.threads_enter()				
		if data["per"]=="PWM":
			self.__threadRequestRunning=False
			self.pwmValues = data["data"]
			self.pwmFreq = data["data2"]
			self.__updateCheckValues()
			self.__updateDrawings()
		gtk.gdk.threads_leave()
		
		
	def __checkEvent(self,widget,index):
		if widget.get_active():
			self.plotter.addFunction(index,createPwmFunction(self.pwmValues[index]))
		else:
			self.plotter.addFunction(index,None)		
		self.plotter.updateGraph()
		pass
		
	def __closePanel(self,arg):
		self.__threadRequestRunning=False
		self.__closeCallback()
		self.window.destroy()	