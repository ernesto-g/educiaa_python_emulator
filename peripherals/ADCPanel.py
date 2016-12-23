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
	
	
	
class ADCPanel:

	def __init__(self,basePath,closeCallback,socket):
		self.__socket = socket
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/ADCPanel.glade")
		except Exception,e:
			print(e)
			return
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title("Analog Inputs")
		
		self.vsAdc0 = builder.get_object("vsAdc0")
		self.vsAdc1 = builder.get_object("vsAdc1")
		self.vsAdc2 = builder.get_object("vsAdc2")

		self.vsAdc0.set_update_policy(gtk.UPDATE_CONTINUOUS)
		self.vsAdc1.set_update_policy(gtk.UPDATE_CONTINUOUS)
		self.vsAdc2.set_update_policy(gtk.UPDATE_CONTINUOUS)
		
		adj0 = builder.get_object("adjustment0")
		adj0.connect("value_changed", self.__changeAdcEvent,0)

		adj1 = builder.get_object("adjustment1")
		adj1.connect("value_changed", self.__changeAdcEvent,1)

		adj2 = builder.get_object("adjustment2")
		adj2.connect("value_changed", self.__changeAdcEvent,2)
		
		self.window.show_all()

		
	
	def __changeAdcEvent(self,adj,index):
		#print("cambio!"+str(index)+" val:"+str(adj.value))
		self.__socket.sendall(json.dumps({"per":"ADC","data":index,"data2":int(adj.value)})) # request initial data


	def update(self,data):
		gtk.gdk.threads_enter()				
		gtk.gdk.threads_leave()
		
		
		
	def __closePanel(self,arg):
		self.__threadRequestRunning=False
		self.__closeCallback()
		self.window.destroy()	