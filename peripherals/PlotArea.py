import gtk
import copy

NPOINTS = 500

class PlotArea:

	COLOR_BLUE = gtk.gdk.Color(0*255, 0*255, 255*255)
	COLOR_RED = gtk.gdk.Color(255*255,0*255, 0*255)
	COLOR_GREEN = gtk.gdk.Color(0*255, 255*255, 0*255)
	COLOR_VIOLET = gtk.gdk.Color(163*255, 73*255, 164*255)
	COLOR_ORANGE = gtk.gdk.Color(255*255, 128*255, 0*255)
	COLOR_YELLOW = gtk.gdk.Color(234*255, 234*255, 0*255)
	COLOR_CYAN = gtk.gdk.Color(128*255, 255*255, 255*255)
	COLOR_PINK = gtk.gdk.Color(255*255, 128*255, 255*255)
	COLOR_BLACK = gtk.gdk.Color(0*255, 0*255, 0*255)
	COLOR_BROWN = gtk.gdk.Color(128*255,128*255, 64*255)
	COLOR_GRAY = gtk.gdk.Color(192*255,192*255,192*255)
	
	def __init__(self, area):
		assert isinstance(area, gtk.DrawingArea)
		self.plot_x1 = 0
		self.plot_x2 = 0
		self.plot_y1 = 0
		self.plot_y2 = 0
		self.area = area
		self.area_width = 0
		self.area_height = 0
		area.connect("expose-event", self.expose_cb)
		area.connect("size-allocate", self.size_allocate_cb)
		area.connect("realize", self.realize_cb)
		self.pixmap = None
		self.functions = [None,None,None,None,None,None,None,None,None,None,None]
		self.colors = [PlotArea.COLOR_BLUE,PlotArea.COLOR_RED,PlotArea.COLOR_GREEN,PlotArea.COLOR_VIOLET,PlotArea.COLOR_ORANGE,PlotArea.COLOR_YELLOW,PlotArea.COLOR_CYAN,PlotArea.COLOR_PINK,PlotArea.COLOR_BLACK,PlotArea.COLOR_BROWN,PlotArea.COLOR_GRAY]


	def addFunction(self,channel,function):
		if channel<len(self.functions):
			self.functions[channel] = function
		
	def __update_conv(self):
		self._sx = self.area_width  / (self.plot_x2 - self.plot_x1)
		self._sy = self.area_height / (self.plot_y2 - self.plot_y1)

	def set_range(self, x1, x2, y1, y2):
		self.plot_x1 = float(x1)
		self.plot_x2 = float(x2)
		self.plot_y1 = float(y1)
		self.plot_y2 = float(y2)
		self.__update_conv()

	def _convert_x(self, x):
		return (x - self.plot_x1)*self._sx

	def _convert_y(self, y):
		return self.area_height - (y - self.plot_y1)*self._sy

			
	def do_plot(self):
		if self.pixmap is None: return
		#fg = self.area.style.fg_gc[gtk.STATE_NORMAL]
		#bg = self.area.style.bg_gc[gtk.STATE_NORMAL]
		
		bg = gtk.gdk.GC(self.pixmap)
		bg.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
		self.pixmap.draw_rectangle(gc=bg,filled=1,x=0, y=0,width=self.area_width,height=self.area_height)
		
		#draw grid lines
		fg =  gtk.gdk.GC(self.pixmap)
		fg.set_rgb_fg_color(gtk.gdk.Color(60000, 60000, 60000))
		for i in range(0,11):
			self.pixmap.draw_line(fg, int((self.area_width/10)*i), 0, int((self.area_width)/10*i), self.area_height)
		for i in range(0,11):
			self.pixmap.draw_line(fg, 0, int((self.area_height/10)*i), self.area_width, int((self.area_height/10)*i) )	
		#_______________		
		
		i=0
		for function in self.functions:
			if function==None:
				i=i+1
				continue
			x = self.plot_x1
			#print self.plot_x2, self.plot_x1
			delta = float(self.plot_x2 - self.plot_x1)/NPOINTS
			if delta <= 0: continue
			wxold = None
			wyold = None
			while x <= self.plot_x2:
				y = function(x)
				wx = self._convert_x(x)
				wy = self._convert_y(y)
				x += delta
				# drawing
				if wxold is not None:
					fg =  gtk.gdk.GC(self.pixmap)
					fg.set_rgb_fg_color(self.colors[i])
					self.pixmap.draw_line(fg, int(wxold), int(wyold), int(wx), int(wy))
				wxold = wx
				wyold = wy
			i=i+1


	def realize_cb(self, widget):
		if self.pixmap is None:
			self.pixmap = gtk.gdk.Pixmap(widget.window, self.area_width,
						 self.area_height, -1)
			self.do_plot()

	def size_allocate_cb(self, widget, allocation):
		self.area_width = allocation.width
		self.area_height = allocation.height
		self.__update_conv()
		if widget.window is None: return
		self.pixmap = gtk.gdk.Pixmap(widget.window, self.area_width,
						 self.area_height, -1)
		self.do_plot()

	def expose_cb(self, widget, event):
		if self.pixmap is None: return
		area = event.area
		widget.window.draw_drawable(gc=widget.style.fg_gc[gtk.STATE_NORMAL],
						src=self.pixmap,
						xsrc=area.x, ysrc=area.y,
						xdest=area.x, ydest=area.y,
						width=area.width, height=area.height)
		return 1
		
	def updateGraph(self):
		self.do_plot()
		self.area.queue_draw()