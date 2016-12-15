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

import gtk 
import pango
import serial
import threading
import struct
import time
import datetime
import json

class GPIOsPanel:
	def __init__(self,basePath,closeCallback,socket):
		self.__socket = None
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/GPIOsPanel.glade")
		except Exception,e:
			print(e)
			return
			
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title("GPIOs")
		
		self.gpiosInOutLbls = []
		for i in range(0,9):
			self.gpiosInOutLbls.append(builder.get_object("lblInOut"+str(i)))
		
		self.gpiosStateChk = []
		for i in range(0,9):
			self.gpiosStateChk.append(builder.get_object("chkOnOff"+str(i)))
			self.gpiosStateChk[i].connect("clicked", self.__checkEvent, (i))

		self.__socket = socket
		self.__threadRequestRunning=True
		self.t = threading.Thread(target=self.__sendStatusRequest)
		self.t.start()

			
		self.window.show_all()
		
	def __sendStatusRequest(self):
		while self.__threadRequestRunning:
			if self.__socket!=None:
				self.__socket.sendall(json.dumps({"per":"GPIOREQUEST"})) # request initial data
			time.sleep(1)
		
	def __checkEvent(self,widget,index):
		if self.gpiosStateChk[index]!=None:
			if self.gpiosInOutLbls[index].get_text()=="IN":
				val = self.gpiosStateChk[index].get_active()
				if val:
					val=1
				else:
					val=0
				if self.__socket!=None:
					self.__socket.sendall(json.dumps({"per":"GPIO","gpion":index,"gpiov":val}))
	
	
	def update(self,data):
		self.__flagUpdate=True
		gtk.gdk.threads_enter()				
		if data["per"]=="GPIO":

			for i in range(0,9):
				valInOut = data["data2"][i]
				val = data["data"][i]
				if valInOut==0: # IN
					self.gpiosInOutLbls[i].set_text("IN")
					self.gpiosStateChk[i].set_sensitive(True)
					if self.__flagFirstTime:
						if val==1:
							self.gpiosStateChk[i].set_active(True)
						else:
							self.gpiosStateChk[i].set_active(False)										
				else: # OUT
					self.gpiosInOutLbls[i].set_text("OUT")
					self.gpiosStateChk[i].set_sensitive(False)
					if val==1:
						self.gpiosStateChk[i].set_active(True)
					else:
						self.gpiosStateChk[i].set_active(False)					

			self.__flagFirstTime=False
			self.__threadRequestRunning=False # stop thread requesting for initial data
		gtk.gdk.threads_leave()
		self.__flagUpdate=False
	
	def __closePanel(self,arg):
		self.__threadRequestRunning=False
		self.__closeCallback()
		self.window.destroy()
	