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
import binascii

class UARTPanel:
	def __init__(self,basePath,closeCallback,socket,uartNumber):
		self.__socket = socket
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		self.__uartNumber=uartNumber
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/UARTPanel.glade")
		except Exception,e:
			print(e)
			return
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		if self.__uartNumber==0:
			self.window.set_title("RS485")
		elif self.__uartNumber==3:
			self.window.set_title("UART")
		
		
		#console config
		self.sw = builder.get_object("scrolledwindow1")
		textview = builder.get_object("txtConsole")
		textview.set_editable(False)
		textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
		textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
		textview.connect("size-allocate", self._autoscroll)
		font = pango.FontDescription('Monospace 10')
		textview.set_cursor_visible(False)
		textview.modify_font(font)
		self.textbuffer = textview.get_buffer()
		textview.get_buffer().set_text("")
		#_____________

		#send panel
		self.btnSend = builder.get_object("btnSend")
		self.txtSend = builder.get_object("txtTosend")
		self.btnSend.connect("pressed", self.__btnSendEvent, (False))
		#_____________
		
		#radio buttons panel
		self.rbuttonAscii = builder.get_object("rbtnAscii")
		self.rbuttonHex = builder.get_object("rbtnHex")
		self.rbuttonHex.set_group(self.rbuttonAscii)
		
		self.rbuttonAscii.connect("toggled", self.__callbackMode, "")
		self.rbuttonHex.connect("toggled", self.__callbackMode, "")	

		self.__mode=0
		#_____________
			
		self.window.show_all()
		
	def _autoscroll(self, *args):
		adj = self.sw.get_vadjustment()
		adj.set_value(adj.get_upper() - adj.get_page_size())
	
	def __callbackMode(self,widget,data=None):
		if widget==self.rbuttonAscii and widget.get_active():
			self.__mode=0
			
		if widget==self.rbuttonHex and widget.get_active():
			self.__mode=1
	
	
	def update(self,data):
		self.__flagUpdate=True
		gtk.gdk.threads_enter()				
		if data["per"]=="UART":
			ts = datetime.datetime.now().strftime("[%H:%M:%S]>")
			if self.__mode==0:
				text = data["data"] #ascii
				bytes = bytearray()
				try:
					hexData = str(text).decode("hex")
					bytes.extend(hexData)
					text=""
					for b in bytes:
						if b>127:
							text+=str("\\x"+ "{:02x}".format(b) )
						else:	
							text+=chr(b)
					text = ts+text+"\n" #ascii
				except:
					text = ts+">>ERROR: Invalid ASCII packet.Hex:"+data["data"]+"\n" #ascii
			else:
				text = ts+data["data"]+"\n" #hex
			end_iter = self.textbuffer.get_end_iter()
			self.textbuffer.insert(end_iter, text)	
		gtk.gdk.threads_leave()
		self.__flagUpdate=False
	
	def __closePanel(self,arg):
		self.__threadRequestRunning=False
		self.__closeCallback()
		self.window.destroy()
	
	def __btnSendEvent(self,a1,a2):
		if self.__socket!=None:
			text = self.txtSend.get_text()
			if self.__mode==0:
				#ascii
				try:
					text = self.txtSend.get_text()
					text = "".join("{:02x}".format(ord(c)) for c in text)
					dataToSend = json.dumps({"per":"UART","uartn":self.__uartNumber,"data":text})
					self.__socket.sendall(dataToSend)				
				except:
					dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Invalid ASCII value")
					dialog.run()
					dialog.destroy()
			else:
				#hex
				try:
					text = self.txtSend.get_text()
					binascii.unhexlify(text) #for checking correct hex string
					dataToSend = json.dumps({"per":"UART","uartn":self.__uartNumber,"data":text})
					self.__socket.sendall(dataToSend)					
				except:
					dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Invalid HEX value")
					dialog.run()
					dialog.destroy()
			
				