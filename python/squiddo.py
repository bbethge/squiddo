import math
import os
import pygame
from OpenGL.GL import *

# Initialize pygame first so GL calls work
pygame.display.init()
pygame.display.set_mode( (640, 480), pygame.OPENGL | pygame.DOUBLEBUF)
pygame.font.init()

class Vector(tuple):
	def __repr__(self):
		return 'Vector(' + repr(self) + ')'
	def __add__(self, other):
		result = ()
		for x, y in zip(self, other):
			result += x + y,
		return Vector(result)
	def __sub__(self, other):
		result = ()
		for x, y in zip(self, other):
			result += x - y,
		return Vector(result)
	def __mul__(self, scale):
		result = ()
		for x in self:
			result += scale*x,
		return Vector(result)

background_color = 1., 1., 1.

class Box:
	__aspect = 2.0  # Width/height ratio for all boxes
	__color = 0.7, 0.7, 0.7
	__corner_size = 0.25  # Size of the rounded corners relative to the height
	__corner_detail = 8
	__display_list = None
	__font = pygame.font.Font(pygame.font.get_default_font(), 14)

	def __init__(self, path):
		'''\
			Create a box representing the given filesystem path
		'''
		self.__path = path
		self.__name = os.path.basename(path)  # Name to be displayed
		self.__name_display_list = None
		self.__contents = None  # List of items (boxes) this box contains
			# (value None indicates we haven't checked for contents yet)
		self.__n_hidden = 0  # Number of hidden items this box contains
		if Box.__display_list == None:
			Box.__display_list = glGenLists(1)
			glNewList(Box.__display_list, GL_COMPILE)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 2, 2, 0, GL_RGB,
				GL_UNSIGNED_BYTE,
				([int(x*255.) for x in Box.__color + background_color]
					+ [0, 0])*2)
			glBegin(GL_QUAD_STRIP)
			def vertex(x, y):
				glTexCoord2d(0.25 + 0.25*x/Box.__aspect + 0.25*(1. - y), 0.5)
				glVertex2d(x, y)
			vertex(Box.__aspect, 0.)
			vertex(Box.__aspect, 1.)
			for n in range(Box.__corner_detail + 1):
				agl = (math.pi/2.)*n/Box.__corner_detail
				vertex(
					Box.__corner_size*(1. - math.sin(agl) ),
					Box.__corner_size*(1. - math.cos(agl) ) )
				vertex(
					Box.__corner_size*(1. - math.sin(agl) ),
					1. - Box.__corner_size*(1. - math.cos(agl) ) )
			glEnd()
			glEndList()
	def __ensure_name_rendered(self):
		if self.__name_display_list != None:
			return
		surf = Box.__font.render(self.__name, True, (0., 0., 0., 1.) )
		print dir(surf)
		surf = surf.convert(32, (0xFF00, 0xFF0000, 0xFF000000, 0xFF) )
		self.__name_display_list = glGenLists(1)
		glNewList(self.__name_display_list, GL_COMPILE)
		glRasterPos2d(0., 0.)
		glDrawPixels(
			surf.get_width(), surf.get_height(), GL_ARGB,
			GL_UNSIGNED_INT_8_8_8_8)
		glEndList();
	def __ensure_contents_loaded(self):
		'''
			Load contents if they haven't been loaded yet.  On exit,
			self.__contents is guaranteed to be a (possibly empty) list of
			boxes, and self.__n_hidden will be the number of hidden items.
		'''
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
			Box(os.path.join(self.__path, name) ) for name in names]
	def draw(self, y, height, win_width, win_height):
		glEnable(GL_TEXTURE_2D)
		self.__draw(y, height, win_width, win_height)
	def __draw(self, y, height, win_width, win_height):
		if height < 2:
			return  # No point drawing anything
		width = height*Box.__aspect
		# Draw background
		alpha = 1.0
		if height < 8:
			# Gradually increase the opacity to get a fade-in effect
			alpha = (height - 2.)/6.
		glPushMatrix()
		glTranslated(win_width - width, y, 0.)
		glScaled(height, height, 1.)
		glColor4d(1., 1., 1., alpha)
		glCallList(Box.__display_list)
		glPopMatrix()
		if height <= 10:
			return  # No point drawing label
		# Draw label
		self.__ensure_name_rendered()
		glPushMatrix()
		glTranslated(win_width - width, y + 0.5*height, 0.)
		glCallList(self.__name_display_list)
		glPopMatrix()
		if height <= 20:
			return  # Don't draw contents
		# Draw contents
		self.__ensure_contents_loaded()
		if len(self.__contents) == 0:
			return
		elif len(self.__contents) == 1:
			self.__contents[0].draw(
				y + height/4.0, height/2.0, win_width, win_height)
			return
		unit_height = height/(2.*len(self.__contents) - self.__n_hidden)
		item_y = y + height
		for item in self.__contents:
			if item.is_hidden():
				item_height = unit_height
			else:
				item_height = 2.0*unit_height
			item_y -= item_height
			if item_y + item_height > 0 and item_y < win_height:
				item.__draw(item_y, item_height, win_width, win_height)
	def is_hidden(self):
		return self.__name[0] == '.'

class App:
	__width, __height = 640, 480
	__crosshair_color = 0., 0., 0.
	__arrow_color = 0., 0., 0.
	__arrow_size = 12.0  # Size of arrow head in pixels
	__arrow_angle = math.radians(25)  # Half the angle of the point of the arrow
	__mode_button = 1  # Which mouse button to use to change mode
	__speed_x = 0.04
	__speed_y = 20
	__crosshair_size = 7  # Radius of crosshair in pixels

	__crosshair_display_list = glGenLists(1)
	glNewList(__crosshair_display_list, GL_COMPILE)
	glDisable(GL_LINE_SMOOTH)
	glLineWidth(1.)
	glColor3dv(__crosshair_color)
	glBegin(GL_LINES)
	glVertex2d(__width/2., __height/2. - __crosshair_size)
	glVertex2d(__width/2., __height/2. + __crosshair_size)
	glVertex2d(__width/2. - __crosshair_size, __height/2.)
	glVertex2d(__width/2. + __crosshair_size, __height/2.)
	glEnd()
	glEndList()
	def __init__(self):
		self.moving = False
		self.box = Box('/')  # TODO: Make cross-platform
		self.y = 0.0
		self.log_scale = 0.0
		self.clock = pygame.time.Clock()
		self.done = False
		glClearColor(
			background_color[0], background_color[1], background_color[2], 1.)
		glEnable(GL_BLEND)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_PROJECTION)
		glOrtho(0., App.__width, 0., App.__height, -1., 1.)
		glMatrixMode(GL_MODELVIEW)
	def draw(self):
		glClear(GL_COLOR_BUFFER_BIT)
		glDisable(GL_POLYGON_SMOOTH)
		self.box.draw(self.y, App.__height*math.exp(self.log_scale),
			App.__width, App.__height)
		glColor3d(0., 0., 0.)
		glDisable(GL_TEXTURE_2D)
		glCallList(App.__crosshair_display_list)
		if self.moving:
			mouse_x, mouse_y = pygame.mouse.get_pos()
			glColor3dv(App.__arrow_color)
			glEnable(GL_LINE_SMOOTH)
			glEnable(GL_POLYGON_SMOOTH)
			glLineWidth(2.)
			self.draw_arrow(
				App.__width/2., App.__height/2.,
				mouse_x, App.__height - mouse_y)
		pygame.display.flip()
	def handle_event(self, ev):
		if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN
			and ev.key == pygame.K_ESCAPE):
			return False
		if ev.type == pygame.MOUSEBUTTONDOWN:
			if ev.button == App.__mode_button:
				self.moving = not self.moving
				pygame.mouse.set_visible(not self.moving)
				pygame.event.set_grab(self.moving)
		elif ev.type == pygame.VIDEOEXPOSE:
			self.draw()
		return True
	def update(self):
		if not self.moving:
			return self.handle_event(pygame.event.wait() )
		# Handle all events in the queue
		while True:
			ev = pygame.event.poll()
			if ev.type == pygame.NOEVENT:
				break
			cont = self.handle_event(ev)
			if not cont:
				return False
		x, y = pygame.mouse.get_pos()
		x = 2.*x/App.__width - 1.
		y = -(2.*y/App.__height - 1.)
		d_log_scale = x*App.__speed_x
		self.log_scale += d_log_scale
		self.y = (
			App.__height/2. + math.exp(d_log_scale)*(self.y - App.__height/2.)
			- y*App.__speed_y)
		self.draw()
		self.clock.tick(30)
		return True
	def draw_arrow(self, xt, yt, xh, yh):
		'''
			Draw an arrow with tail at (xt, yt) and head at (xh, yh).
		'''
		glPushMatrix()
		glTranslated(xt, yt, 0.)
		glRotated(math.degrees(math.atan2(yh - yt, xh - xt) ), 0., 0., 1.)
		glBegin(GL_LINES)
		glVertex2d(0., 0.)
		length = math.sqrt( (xh - xt)**2 + (yh - yt)**2)
		glVertex2d(length - App.__arrow_size*math.cos(App.__arrow_angle), 0.)
		glEnd()
		glTranslated(length, 0., 0.)
		glBegin(GL_TRIANGLES)
		glVertex2d(0., 0.)
		glVertex2d(
			-App.__arrow_size*math.cos(App.__arrow_angle),
			App.__arrow_size*math.sin(App.__arrow_angle) )
		glVertex2d(
			-App.__arrow_size*math.cos(App.__arrow_angle),
			-App.__arrow_size*math.sin(App.__arrow_angle) )
		glEnd()
		glPopMatrix()

app = App()
while app.update():
	pass
