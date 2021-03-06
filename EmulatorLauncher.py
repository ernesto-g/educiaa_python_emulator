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
#	EDU-CIAA Python emulator (2016)
#	
#	<ernestogigliotti@gmail.com>
#
########################################################################

import socket
import sys
import json
import time
from console.PanelEmulator import PanelEmulator
import gtk
import os
import threading
from SerialMock import SerialMock
from emulator.Emulate import Emulate
import signal

# debug
#import logging
#logger = logging.getLogger('myapp')
#hdlr = logging.FileHandler('/var/tmp/myapp.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)
#logger.addHandler(hdlr) 
#logger.setLevel(logging.INFO)
#_______


BASE_PATH,filename = os.path.split(sys.argv[0])
if(BASE_PATH==""):
    BASE_PATH="."

def exitEvent(signum,frame):
	print("EXIT BY SYGNAL")
	sys.exit(0)


class EmulatorLauncher:
	def __init__(self,panelEm,serialMock,file):
		self.panelEmulator = panelEm
		self.serialMock = serialMock
		self.file=file
		
	def startServer(self):
		self.threadServer = threading.Thread(target=self.__runServer, args=())
		self.threadServer.setDaemon(1)
		self.threadServer.start()
		#logger.info('Inicio thread de server')
	def __runServer(self):
		self.port=10000
		self.flagConnOk=False
		while True:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				server_address = ('localhost', self.port)
				print >>sys.stderr, 'starting up on %s port %s' % server_address
				sock.bind(server_address)
				break
			except:
				time.sleep(0.1)
				self.port+=1
		self.flagConnOk=True	
		sock.listen(1)
		# Wait for a connection
		print >>sys.stderr, 'waiting for a connection'
		connection, client_address = sock.accept()
		try:
			print >>sys.stderr, 'connection from', client_address
			self.serialMock.setSocket(connection)
			self.panelEmulator.setSocket(connection)
			self.panelEmulator.setEmulatorLauncher(self)
			self.connection = connection
			while True:
				data = connection.recv(4096)
				#logger.info('Llego data:'+str(data))
				if data:
					try:
						parts = data.split("}{")
						for data in parts:
							if data[0]!="{":
								data = "{"+data
							if data[-1]!="}":
								data = data + "}"
							data = json.loads(data)
							if data["per"]=="STDOUT":
								self.serialMock.insertText(data["data"])
							else:
								self.panelEmulator.update(data)
					except:
						print("ERROR RCV")
						#logger.info('ERROR RVC')
				else:
					print >>sys.stderr, 'no more data from', client_address
					#logger.info('Data vino vacio')
					break
		except:
			connection.close()
			#logger.info('Server.Cierro la conexion en except')			
		finally:
			# Clean up the connection
			connection.close()		
			#logger.info('Server.Cierro la conexion en finally')

		#logger.info('FIN del thread del server')

	def startEmulator(self):
		self.threadEmulator = threading.Thread(target=self.__runEmulator, args=())
		self.threadEmulator.setDaemon(1)
		self.threadEmulator.start()
		#logger.info('Inicio thread de emulador')
			
	def __runEmulator(self):
		self.serialMock.insertText("\x15")
		e = Emulate()
		while self.flagConnOk==False:
			time.sleep(1)
		#logger.info('Inicio emulador')
		e.start(self.file,self.port)
		#logger.info('FIN emulador y thread')


	def closeAll(self):
		self.connection.close()
		if sys.platform != 'win32':
			os.kill(os.getpid(),signal.SIGTERM)
		else:
			#os.kill(os.getpid(),signal.CTRL_BREAK_EVENT)		
			os.kill(os.getpid(),signal.SIGINT)		
		#gtk.main_quit()


if len(sys.argv) == 2:
	file = sys.argv[1]

	signal.signal(signal.SIGTERM,exitEvent)
	signal.signal(signal.SIGINT,exitEvent)
		
	gtk.gdk.threads_init()
	c = PanelEmulator(BASE_PATH)
	serialMock = SerialMock()			

	el = EmulatorLauncher(c,serialMock,file)
	el.startServer()
	el.startEmulator()

	c.showConsole("",serialMock)
	gtk.main()
else:
		print("ERROR. A file must be provided")


