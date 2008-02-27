import math
import os
import gobject
import gtk
from gtk import gdk
import cairo

class Window(gtk.Window):
	'''
		The main window for our application
	'''
	def __init__(self):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.set_default_size(400, 300)
		self.set_title('Squiddo System Browser')
		vbox = gtk.VBox()
		self.add(vbox)
		toolbar = gtk.Toolbar()
		vbox.pack_start(toolbar, False, False, 0)
		quit_button = gtk.ToolButton(stock_id = gtk.STOCK_QUIT)
		quit_button.connect_object('clicked', Window.hide, self)
		toolbar.insert(quit_button, -1)
		frame = gtk.Frame()
		frame.set_shadow_type(gtk.SHADOW_IN)
		control = Control()
		frame.add(control)
		control.show()
		vbox.pack_start(frame, True, True, 0)
		vbox.show_all()
gobject.type_register(Window)

__arrow_size = 12.0
__arrow_angle = math.radians(30)
def draw_arrow(cc, xt, yt, xh, yh):
	'''
		Draw an arrow on the Cairo context cc, with tail
		at (xt, yt) and head at (xh, yh).
	'''
	cc.new_path()
	cc.move_to(xt, yt)
	cc.line_to(xh, yh)
	cc.save()
	cc.translate(xh, yh)
	cc.rotate(math.atan2(yh - yt, xh - xt))
	cc.move_to(
		-__arrow_size*math.cos(__arrow_angle),
		-__arrow_size*math.sin(__arrow_angle))
	cc.line_to(0, 0)
	cc.line_to(
		-__arrow_size*math.cos(__arrow_angle),
		__arrow_size*math.sin(__arrow_angle))
	cc.restore()
	cc.stroke()
class Control(gtk.Widget):
	'''
		The widget that contains the zooming area
	'''
	__mode_button = 1  # Which mouse button to use to change mode
	__speed_x = 0.04
	__speed_y = 20
	__crosshair_size = 7
	__invisible_cursor = None
	def __init__(self):
		gtk.Widget.__init__(self)
		self.__moving = False
		# Create an invisible cursor for the class if this is the first
		# instance to be created.
		if Control.__invisible_cursor == None:
			blank_pixmap = gdk.Pixmap(None, 1, 1, 1)
			color = gdk.Color()
			Control.__invisible_cursor = gdk.Cursor(
				blank_pixmap, blank_pixmap, color, color, 0, 0)
		self.__box = Box('/')  # TODO: Make cross-platform
		self.__y = 0.0
		self.__log_scale = 0.0
		# Give me a window, dammit
		self.unset_flags(gtk.NO_WINDOW)
	def do_realize(self):
		self.set_flags(gtk.REALIZED)
		self.window = gdk.Window(
			parent = self.get_parent_window(),
			width = self.allocation.width,
			height = self.allocation.height,
			window_type = gdk.WINDOW_CHILD,
			event_mask = self.get_events() |
				gdk.EXPOSURE_MASK |
				gdk.POINTER_MOTION_MASK |
				gdk.BUTTON_PRESS_MASK,
			wclass = gdk.INPUT_OUTPUT,
			x = self.allocation.x,
			y = self.allocation.y)
		self.window.set_user_data(self)
		self.set_style(self.style.attach(self.window))
	def do_expose_event(self, event):
		w = self.allocation.width
		h = self.allocation.height
		cc = self.window.cairo_create()
		# Fill the background
		cc.new_path()
		cc.rectangle(0, 0, w, h)
		cc.set_source_rgb(1.0, 1.0, 1.0)
		cc.fill()
		cc.set_source_rgb(0.0, 0.0, 0.0)
		self.__box.draw(
			cc, self.__y, h*math.exp(self.__log_scale), w, h)
		# Draw a crosshair
		cc.new_path()
		cc.move_to(w/2 + 0.5 - Control.__crosshair_size, h/2 + 0.5)
		cc.line_to(w/2 + 0.5 + Control.__crosshair_size, h/2 + 0.5)
		cc.move_to(w/2 + 0.5, h/2 + 0.5 - Control.__crosshair_size)
		cc.line_to(w/2 + 0.5, h/2 + 0.5 + Control.__crosshair_size)
		cc.save()
		cc.set_line_width(1)
		cc.stroke()
		cc.restore()
		if self.__moving:
			# Draw an arrow
			x, y = self.get_pointer()
			draw_arrow(cc, w/2.0, h/2.0, x, y)
		return True
	def do_motion_notify_event(self, event):
		self.queue_draw()
		return True
	def do_button_press_event(self, event):
		if event.type != gdk.BUTTON_PRESS or \
			event.button != Control.__mode_button:
			return False
		self.__moving = not self.__moving
		if self.__moving:
			gdk.pointer_grab(
				window = self.window,
				owner_events = True,
				event_mask = 0,
				confine_to = self.window,
				cursor = Control.__invisible_cursor,
				time = event.time)
			gobject.timeout_add(30, self.__update)
		else:
			gdk.pointer_ungrab(event.time)
		self.queue_draw()
		return True
	def __update(self):
		if not self.__moving:
			return False
		w = self.allocation.width
		h = self.allocation.height
		x, y = self.get_pointer()
		x = 2.0*x/w - 1
		y = 2.0*y/h - 1
		d_log_scale = x*Control.__speed_x
		self.__log_scale += d_log_scale
		self.__y = h/2.0 + math.exp(d_log_scale)*(self.__y - h/2.0) \
			- y*Control.__speed_y
		self.queue_draw()
		return True
gobject.type_register(Control)

class Box:
	__aspect = 2.0
	__colors = ( (0.7, 0.7, 0.7), (0.8, 0.8, 0.9) )
	def __init__(self, path):
		self.__path = path
		self.__name = os.path.basename(path)
		self.__contents = None
		self.__n_hidden = 0
	def __ensure_contents_loaded(self):
		if self.__contents != None:
			return
		if not os.path.isdir(self.__path):
			# Treat non-directories like empty directories
			self.__contents = []
			return
		try:
			names = os.listdir(self.__path)
		except OSError:
			# Treat I/O errors like empty directories
			self.__contents = []
			return
		names.sort()
		self.__n_hidden = len(filter((lambda n: n[0] == '.'), names))
		self.__contents = [
			Box(os.path.join(self.__path, name))
			for name in names]
	def draw(self, cc, y, height, win_width, win_height):
		cc.save()
		self.__draw(cc, y, height, Box.__colors[0], win_width, win_height)
		cc.restore()
	def __draw(self, cc, y, height, color, win_width, win_height):
		if height < 2:
			return  # No point drawing anything
		rad = height/4.0  # Radius of the rounded corners
		width = height*Box.__aspect
		# Draw background
		gradient = cairo.LinearGradient(0., 0., 1., 0.)
		alpha = 1.0
		if height < 8:
			# Gradually increase the opacity to get a fade-in effect
			alpha = (height - 2.)/6.
		gradient.add_color_stop_rgba(0., color[0], color[1], color[2], alpha)
		gradient.add_color_stop_rgba(1., 1., 1., 1., alpha)
		pat_mat = cairo.Matrix()
		pat_mat.scale(1./width, 1)
		pat_mat.translate(-(win_width - width), 0)
		gradient.set_matrix(pat_mat)
		cc.set_source(gradient)
		cc.new_path()
		if width - rad > win_width:
			cc.move_to(win_width, max(y, 0) )
			cc.line_to(0, max(y, 0) )
			cc.line_to(0, min(y + height, win_height) )
			cc.line_to(win_width, min(y + height, win_height) )
		else:
			cc.move_to(win_width, y)
			cc.arc_negative(
				win_width - width + rad, y + rad, rad, 1.5*math.pi, math.pi)
			cc.arc_negative(
				win_width - width + rad, y + height - rad,
				rad, math.pi, 0.5*math.pi)
			cc.line_to(win_width, y + height)
		cc.close_path()
		cc.fill()
		if height <= 10:
			return  # No point drawing label
		# Draw label
		cc.save()
		cc.set_source_rgb(0., 0., 0.)
		cc.new_path()
		cc.rectangle(
			max(win_width - width, 0), max(y, 0),
			min(width, win_width), min(height, win_height))
		cc.clip()
		cc.move_to(win_width - width, y + 0.75*height)
		cc.show_text(self.__name)
		cc.restore()
		if height <= 20:
			return  # Don't draw contents
		# Draw contents
		self.__ensure_contents_loaded()
		if len(self.__contents) == 0:
			return
		elif len(self.__contents) == 1:
			self.__contents[0].draw(
				cc, y + height/4.0, height/2.0, win_width, win_height)
			return
		unit_height = \
			height/(2.0*len(self.__contents) - self.__n_hidden)
		item_y = y
		c_index = 0
		for item in self.__contents:
			if item.is_hidden():
				item_height = unit_height
			else:
				item_height = 2.0*unit_height
			if item_y + item_height > 0 and item_y < win_height:
				item.__draw(
					cc, item_y, item_height, Box.__colors[c_index],
					win_width, win_height)
			item_y += item_height
			c_index = (c_index + 1)%2
	def is_hidden(self):
		return self.__name[0] == '.'

if __name__ == '__main__':
	gtk.init_check() # Is this even necessary?
	win = Window()
	win.connect('hide', gtk.main_quit)
	win.show()
	gtk.main()
