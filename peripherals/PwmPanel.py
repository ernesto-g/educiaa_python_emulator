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
		
		for i in range(0,11):
			chkPwm = builder.get_object("chkPwm"+str(i))
			chkPwm.connect("clicked", self.__checkEvent,(i))
		
		
		self.area= builder.get_object("drawingarea1")
		self.plotter = PlotArea(self.area);
		self.plotter.set_range(0, 4*math.pi, -1.5, 1.5)
		
		
		self.window.show_all()
	
	def __checkEvent(self,widget,index):
		if widget.get_active():
			self.plotter.addFunction(index,createPwmFunction(5*index))
		else:
			self.plotter.addFunction(index,None)		
		self.plotter.updateGraph()
		
	def __closePanel(self,arg):
		self.__closeCallback()
		self.window.destroy()	