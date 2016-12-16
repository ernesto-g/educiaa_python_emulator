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

class UARTPanel:
	def __init__(self,basePath,closeCallback,socket,title):
		self.__socket = None
		self.__flagFirstTime=True
		self.__closeCallback=closeCallback
		self.__flagUpdate=False
		
		try:
			builder = gtk.Builder()
			builder.add_from_file(basePath+"/UARTPanel.glade")
		except Exception,e:
			print(e)
			return
		self.window = builder.get_object("window1")
		self.window.connect("destroy", self.__closePanel)
		self.window.set_icon_from_file(basePath+"/icons/icon.ico")
		self.window.set_title(title)
		
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


			
		self.window.show_all()
		
	def _autoscroll(self, *args):
		adj = self.sw.get_vadjustment()
		adj.set_value(adj.get_upper() - adj.get_page_size())
	
	
	def update(self,data):
		self.__flagUpdate=True
		gtk.gdk.threads_enter()				
		if data["per"]=="UART":
			ts = datetime.datetime.now().strftime("[%H:%M:%S]>")
			text = ts+data["data"]+"\n"
			end_iter = self.textbuffer.get_end_iter()
			self.textbuffer.insert(end_iter, text)	
		gtk.gdk.threads_leave()
		self.__flagUpdate=False
	
	def __closePanel(self,arg):
		self.__threadRequestRunning=False
		self.__closeCallback()
		self.window.destroy()
	