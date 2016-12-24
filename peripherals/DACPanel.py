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
	
def createKFunction(value):
	def functionTemplate(x):
		return value/1023.0
	return functionTemplate	
	
def createTriangleFunction():
	def functionTemplate(x):
		table = [0,8,16,24,32,40,48,56,64,72,80,88,96,104,112,120,128,136,144,152,160,168,176,184,192,200,208,216,224,232,240,248,256,264,272,280,288,296,304,312,320,328,336,344,352,360,368,376,384,392,400,408,416,424,432,440,448,456,464,472,480,488,496,504,512,520,528,536,544,552,560,568,576,584,592,600,608,616,624,632,640,648,656,664,672,680,688,696,704,712,720,728,736,744,752,760,768,776,784,792,800,808,816,824,832,840,848,856,864,872,880,888,896,904,912,920,928,936,944,952,960,968,976,984,992,1000,1008,1016,1023,1016,1008,1000,992,984,976,968,960,952,944,936,928,920,912,904,896,888,880,872,864,856,848,840,832,824,816,808,800,792,784,776,768,760,752,744,736,728,720,712,704,696,688,680,672,664,656,648,640,632,624,616,608,600,592,584,576,568,560,552,544,536,528,520,512,504,496,488,480,472,464,456,448,440,432,424,416,408,400,392,384,376,368,360,352,344,336,328,320,312,304,296,288,280,272,264,256,248,240,232,224,216,208,200,192,184,176,168,160,152,144,136,128,120,112,104,96,88,80,72,64,56,48,40,32,24,16,8]
		#period : 2pi
		x = x % (2*math.pi)
		x = int(x*255/(2*math.pi))
		return (table[x]/1023.0)
	return functionTemplate	

def createNoiseFunction():
	def functionTemplate(x):
		table = [ 892,351,115,611,678,365,86,777,403,722,735,1005,501,134,751,694,955,647,472,375,100,1008,61,821,418,587,927,110,632,639,727,212,318,552,613,386,302,818,405,881,986,432,1016,205,198,737,955,260,984,801,729,151,768,379,422,786,41,419,748,844,659,560,321,647,797,835,752,23,760,166,400,625,344,693,993,129,611,159,765,653,991,660,299,576,1019,427,835,705,921,779,965,776,646,865,983,125,228,770,689,366,343,935,527,711,671,278,339,690,992,323,484,435,580,333,421,388,759,630,568,400,268,144,728,470,65,828,311,25,630,488,355,769,7,597,244,397,703,985,523,875,758,279,555,25,206,971,401,421,345,982,819,402,780,532,465,279,989,85,249,829,776,346,878,582,850,685,910,130,767,445,647,485,378,381,919,690,708,230,730,998,829,448,965,471,417,569,535,457,588,431,652,510,467,229,376,948,41,358,865,150,987,508,494,593,975,961,694,48,643,813,508,626,993,316,272,230,857,747,94,38,315,484,890,94,172,279,342,627,465,449,355,32,483,847,365,216,425,912,814,500,665,393,136,94,55,574,845,10,329,516,282,122,231,610,155,263 ]		#period : 2pi
		x = x % (2*math.pi)
		x = int(x*255/(2*math.pi))
		return (table[x]/1023.0)
	return functionTemplate	

def createTimedFunction(data):
	def functionTemplate(x):
		table = data 		#period : 2pi
		x = x % (2*math.pi)
		x = int(x*(len(table))/(2*math.pi))
		try:
			v = table[x]
		except:
			v = -1
		if v >1023:
			v=1023
		return (v/1023.0)
	return functionTemplate	

	
class DACPanel:

	def __init__(self,basePath,closeCallback,socket):
		self.__socket = socket
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/DACPanel.glade")
		except Exception,e:
			print(e)
			return
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title("DAC out")
		
		self.lblFreq = builder.get_object("lblFreq")
		
		self.area= builder.get_object("drawingarea1")
		self.plotter = PlotArea(self.area);
		self.plotter.set_range(0, 5*math.pi, -1.5, 1.5)
				
		self.__threadRequestRunning=True
		self.t = threading.Thread(target=self.__sendStatusRequest)
		self.t.start()
		
		self.window.show_all()

		self.mode = 0
		self.freq = 0
		self.data = None
		self.lblFreq.set_label("0Hz")
		
		
		
	def __sendStatusRequest(self):
		while self.__threadRequestRunning:
			if self.__socket!=None:
				self.__socket.sendall(json.dumps({"per":"DACREQUEST"})) # request initial data
			time.sleep(1)
			

		
	def __updateDrawings(self):
		v=""
		if self.freq<1000:
			v = str(self.freq)+" Hz"
		elif self.freq<1000000:
			v = str(self.freq/1000)+" kHz"
			
		self.lblFreq.set_label(v)

		if self.mode == 0: #value
			if self.data!=None:
				self.lblFreq.set_label("val:"+str(self.data[0]))
				self.plotter.addFunction(0,createKFunction(self.data[0]))
		elif self.mode == 1: # noise
			self.plotter.addFunction(0,createNoiseFunction())
		elif self.mode == 2:# triangle
			self.plotter.addFunction(0,createTriangleFunction())
		elif self.mode == 3: # timed
			if self.data!=None:
				self.plotter.addFunction(0,createTimedFunction(self.data))

		self.plotter.updateGraph()
		

	def update(self,data):
		gtk.gdk.threads_enter()				
		if data["per"]=="DAC":
			# data["data"] # dac mode
			# data["data2"] # dac freq
			# data["data3"] # dac data
			self.mode = data["data"]
			self.freq = data["data2"]
			self.data = data["data3"]
			self.__threadRequestRunning=False
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