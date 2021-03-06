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
from console.Console import Console
from peripherals.GPIOsPanel import GPIOsPanel
from peripherals.UARTPanel import UARTPanel
from peripherals.PwmPanel import PwmPanel
from peripherals.ADCPanel import ADCPanel
from peripherals.DACPanel import DACPanel
import json

from threading import Lock

VERSION = "1.2"

class SocketMultiThread:
	def __init__(self,socket):
		self.socket = socket
		self.mutex = Lock()
		
	def sendall(self,data):
		self.mutex.acquire()
		self.socket.sendall(data)
		self.mutex.release()

class PanelEmulator:
	def __init__(self,basePath):
		self.c = Console(basePath)
		self.__socket = None
		self.__emulatorLauncher = None
		self.__basePath = basePath
		self.gpiosWindow = None
		self.uartWindow = None
		self.rs485Window = None
		self.pwmWindow = None
		self.adcWindow = None
		self.dacWindow = None
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/EmulatorPanel.glade")
		except Exception,e:
			print(e)
			return
			
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title("EDU-CIAA Emulator Panel "+VERSION)

		self.buttonOk = builder.get_object("btnSw1")
		self.buttonOk.connect("pressed", self.__btnSw1, (False))
		self.buttonOk.connect("released", self.__btnSw1, (True))

		self.buttonOk = builder.get_object("btnSw2")
		self.buttonOk.connect("pressed", self.__btnSw2, (False))
		self.buttonOk.connect("released", self.__btnSw2, (True))

		self.buttonOk = builder.get_object("btnSw3")
		self.buttonOk.connect("pressed", self.__btnSw3, (False))
		self.buttonOk.connect("released", self.__btnSw3, (True))


		self.buttonOk = builder.get_object("btnSw4")
		self.buttonOk.connect("pressed", self.__btnSw4, (False))
		self.buttonOk.connect("released", self.__btnSw4, (True))

		#leds
		self.chkLed1 = builder.get_object("chkLed1")
		self.chkLed2 = builder.get_object("chkLed2")
		self.chkLed3 = builder.get_object("chkLed3")
		self.lblRgb = builder.get_object("lblRgb")
		self.lblRgb.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))
		
		self.imgBkg = builder.get_object("image1")
		self.imgBkg.set_from_file(basePath+"/educiaa.png")
		

		#menu -------------------------------------------------------------------------
		self.mnuItemGpio = builder.get_object("imagemenuitem1")
		self.mnuItemGpio.set_label("GPIOs")
		self.mnuItemGpio.connect("activate", self.__mnuGpios, None)
		
		self.mnuItemUart = builder.get_object("imagemenuitem2")
		self.mnuItemUart.set_label("UART")
		self.mnuItemUart.connect("activate", self.__mnuUart, None)
		
		self.mnuItem485 = builder.get_object("imagemenuitem3")
		self.mnuItem485.set_label("RS-485")
		self.mnuItem485.connect("activate", self.__mnu485, None)
		
		self.mnuItemTimers = builder.get_object("imagemenuitem4")
		self.mnuItemTimers.set_label("PWM")
		self.mnuItemTimers.connect("activate", self.__mnuPwm, None)

		self.mnuItemTimers = builder.get_object("imagemenuitem5")
		self.mnuItemTimers.set_label("ADC")
		self.mnuItemTimers.connect("activate", self.__mnuAdc, None)

		self.mnuItemTimers = builder.get_object("imagemenuitem6")
		self.mnuItemTimers.set_label("DAC")
		self.mnuItemTimers.connect("activate", self.__mnuDac, None)
		
		self.mnuItemQuit = builder.get_object("imagemenuitem7")
		self.mnuItemQuit.set_label("Quit")
		self.mnuItemQuit.connect("activate", self.__mnuQuit, None)

		self.mnuItemAbout = builder.get_object("imagemenuitem10")
		self.mnuItemAbout.set_label("About")
		self.mnuItemAbout.connect("activate", self.__mnuAbout, None)
		#-----------------------------------------------------------------------------
		
		self.window.show_all()

		
		
	def showConsole(self,port,serialMock):
		self.c.showConsole(port,serialMock)

	def __btnSw1(self,a1,stat):
		if self.__socket!=None:
			self.__socket.sendall(json.dumps({"per":"Switch","swn":0,"swv":stat}))
		
	def __btnSw2(self,a1,stat):
		if self.__socket!=None:
			self.__socket.sendall(json.dumps({"per":"Switch","swn":1,"swv":stat}))

	def __btnSw3(self,a1,stat):
		if self.__socket!=None:
			self.__socket.sendall(json.dumps({"per":"Switch","swn":2,"swv":stat}))

	def __btnSw4(self,a1,stat):
		if self.__socket!=None:
			self.__socket.sendall(json.dumps({"per":"Switch","swn":3,"swv":stat}))

	def update(self,data):
		if data["per"]=="LED":
			gtk.gdk.threads_enter()			
			ledsStatus = data["data"]
			self.chkLed1.set_active(ledsStatus[0])
			self.chkLed2.set_active(ledsStatus[1])
			self.chkLed3.set_active(ledsStatus[2])
			r = (ledsStatus[3]/15.0)*255
			if r>255 :
				r=255
			g = (ledsStatus[4]/15.0)*255
			if g>255 :
				g=255
			b = (ledsStatus[5]/15.0)*255
			if b>255 :
				b=255
			colorStr = "%0.2X" % r
			colorStr+= "%0.2X" % g
			colorStr+= "%0.2X" % b
			self.lblRgb.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#'+colorStr))
			gtk.gdk.threads_leave()
		elif data["per"]=="GPIO":
			if self.gpiosWindow!=None:
				self.gpiosWindow.update(data)
		elif data["per"]=="PWM":
			if self.pwmWindow!=None:
				self.pwmWindow.update(data)
		elif data["per"]=="DAC":
			if self.dacWindow!=None:
				self.dacWindow.update(data)
		elif data["per"]=="UART":
			if data["uartn"]==3:
				if self.uartWindow!=None:
					self.uartWindow.update(data)
			if data["uartn"]==0:
				if self.rs485Window!=None:
					self.rs485Window.update(data)
	
		
	def setSocket(self,socket):
		self.__socket = SocketMultiThread(socket)
	
	def __closePanel(self,arg):
		self.c.closeConsole()
		self.window.destroy()
		if self.__emulatorLauncher!=None:
			self.__emulatorLauncher.closeAll()
	
	def setEmulatorLauncher(self,el):
		self.__emulatorLauncher = el
		
	# Menu items events
	def __mnuGpios(self,widget,arg):
		if self.gpiosWindow==None:
			self.gpiosWindow = GPIOsPanel(self.__basePath,self.__closeGpioWindowEvent,self.__socket)
	def __closeGpioWindowEvent(self):
		self.gpiosWindow = None
		
	def __mnuUart(self,widget,arg):
		if self.uartWindow==None:
			self.uartWindow = UARTPanel(self.__basePath,self.__closeUartWindowEvent,self.__socket,3) 
	def __closeUartWindowEvent(self):
		self.uartWindow = None
		
	
	def __mnu485(self,widget,arg):
		if self.rs485Window==None:
			self.rs485Window = UARTPanel(self.__basePath,self.__closeRs485WindowEvent,self.__socket,0)
	def __closeRs485WindowEvent(self):
		self.rs485Window = None
	
	def __mnuPwm(self,widget,arg):
		if self.pwmWindow==None:
			self.pwmWindow = PwmPanel(self.__basePath,self.__closePwmWindowEvent,self.__socket)
	def __closePwmWindowEvent(self):
		self.pwmWindow = None
	
	def __mnuAdc(self,widget,arg):
		if self.adcWindow==None:
			self.adcWindow =  ADCPanel(self.__basePath,self.__closeAdcWindowEvent,self.__socket)
	def __closeAdcWindowEvent(self):
		self.adcWindow = None

	def __mnuDac(self,widget,arg):
		if self.dacWindow==None:
			self.dacWindow =  DACPanel(self.__basePath,self.__closeDacWindowEvent,self.__socket)
	def __closeDacWindowEvent(self):
		self.dacWindow = None
		
		
		
		
	def __mnuQuit(self,widget,arg):
		self.__closePanel(None)
	
	def __mnuAbout(self,widget,arg):
		# show standard gtk about window
		def show_about():
			about_dialog = gtk.AboutDialog()
			about_dialog.set_transient_for(self.window)
			about_dialog.set_destroy_with_parent(True)
			about_dialog.set_name("EDU-CIAA Python Emulator")
			about_dialog.set_version(VERSION)
			about_dialog.set_copyright("")
			about_dialog.set_website("https://github.com/ernesto-g/educiaa_python_emulator")
			about_dialog.set_comments("Ernesto Gigliotti <2016-2017>\nGNU License.")
			#about_dialog.set_authors("Ernesto Gigliotti")
			#about_dialog.set_logo_icon_name(gtk.STOCK_EDIT)	
			#img = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(BASE_PATH,"splash.png"), 80, 45)
			#about_dialog.set_logo(img)

			# callbacks for destroying the about dialog
			def close(dialog, response, editor):
				editor.about_dialog = None
				dialog.destroy()

			def delete_event(dialog, event, editor):
				editor.about_dialog = None
				return True

			about_dialog.connect("response", close, self)
			about_dialog.connect("delete-event", delete_event, self)

			self.about_dialog = about_dialog
			about_dialog.show()

		# run functions
		show_about()
	#______________________	