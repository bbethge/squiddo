import math
import os
from OpenGL.GL import *
from OpenGL.GLUT import *

default_width = 640   # Default window dimensions
default_height = 480  #
background_color = 1., 1., 1.

class Box:
	__aspect = 2.0  # Width/height ratio for all boxes
	__color = 0.7, 0.7, 0.7
	__corner_size = 0.25  # Size of the rounded corners relative to the height
	__corner_detail = 8  # Number of line segments used on rounded corners
	__display_list = None
		# Display list for drawing the background shape of the box (value None
		# indicates it hasn't been created yet)

	def __init__(self, path):
		'''\
			Create a box representing the given filesystem path
		'''
		self.__path = path
		self.__name = os.path.basename(path)  # Name to be displayed
		self.__name_display_list = None
			# None indicates it hasn't been created yet
		self.__contents = None  # List of items (boxes) this box contains
			# (value None indicates we haven't checked for contents yet)
		self.__n_hidden = 0  # Number of hidden items this box contains
		self.__ensure_display_list_created()
	def __ensure_display_list_created(self):
		'''\
			Create Box.__display_list if it hasn't been created yet
			Post: Box.__display_list is a valid display list number
		'''
		if Box.__display_list != None:
			return
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
		#self.__name_display_list = glGenLists(1)
		#glNewList(self.__name_display_list, GL_COMPILE)
		#glColor3d(0., 0., 0.)
		#glutStrokeString(GLUT_STROKE_ROMAN, self.__name)
		#glEndList()
	def __ensure_contents_loaded(self):
		'''\
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
		# TODO: Make cross-platform
		self.__n_hidden = len(filter((lambda n: n[0] == '.'), names))
		self.__contents = [
			Box(os.path.join(self.__path, name) ) for name in names]
	def draw(self, y, height, win_width, win_height):
		glEnable(GL_TEXTURE_2D)
		glDisable(GL_POLYGON_SMOOTH)
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
		if height < 16:
			alpha = (height - 10.)/6.
		self.__ensure_name_rendered()
		glColor4d(0., 0., 0., alpha)
		glRasterPos2d(win_width - width, y + 0.5*height)
		glutBitmapString(GLUT_BITMAP_9_BY_15, self.__name)
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
	__crosshair_color = 0., 0., 0.
	__arrow_color = 0., 0., 0.
	__arrow_size = 12.0  # Size of arrow head in pixels
	__arrow_angle = math.radians(25)  # Half the angle of the point of the arrow
	__mode_button = GLUT_LEFT_BUTTON  # Which mouse button to use to change mode
	__speed_x = 0.04
	__speed_y = 20
	__crosshair_size = 7  # Radius of crosshair in pixels
	__crosshair_display_list = None
	__arrowhead_display_list = None
	def __init__(self):
		self.moving = False
		self.y = 0.0
		self.log_scale = math.log(default_height)
		self.width = default_width
		self.height = default_height
		self.mouse_x = 0
		self.mouse_y = 0
		self.window = glutCreateWindow("Squiddo System Browser")
		self.__ensure_display_lists_created()
		self.box = Box('/')  # TODO: Make cross-platform
		glutReshapeFunc(self.reshape)
		glutDisplayFunc(self.draw)
		glutMotionFunc(self.mouse_motion)
		glutPassiveMotionFunc(self.mouse_motion)
		glutMouseFunc(self.mouse_button)
		glClearColor(
			background_color[0], background_color[1], background_color[2], 1.)
		glEnable(GL_BLEND)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	def __ensure_display_lists_created(self):
		if App.__crosshair_display_list != None:
			return
		# Create crosshair display list
		App.__crosshair_display_list = glGenLists(1)
		glNewList(App.__crosshair_display_list, GL_COMPILE)
		glDisable(GL_LINE_SMOOTH)
		glLineWidth(1.)
		glColor3dv(App.__crosshair_color)
		glBegin(GL_LINES)
		glVertex2d(0., -App.__crosshair_size)
		glVertex2d(0., App.__crosshair_size)
		glVertex2d(-App.__crosshair_size, 0.)
		glVertex2d(App.__crosshair_size, 0.)
		glEnd()
		glEndList()
		# Create arrowhead display list
		App.__arrowhead_display_list = glGenLists(1)
		glNewList(App.__arrowhead_display_list, GL_COMPILE)
		glBegin(GL_TRIANGLES)
		glVertex2d(0., 0.)
		glVertex2d(
			-App.__arrow_size*math.cos(App.__arrow_angle),
			App.__arrow_size*math.sin(App.__arrow_angle) )
		glVertex2d(
			-App.__arrow_size*math.cos(App.__arrow_angle),
			-App.__arrow_size*math.sin(App.__arrow_angle) )
		glEnd()
		glEndList()
	def reshape(self, width, height):
		'''\
			Handler for window reshape events
		'''
		self.y += (height - self.height)/2.
		self.width = width
		self.height = height
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0., width, 0., height, -1., 1.)
		glMatrixMode(GL_MODELVIEW)
	def mouse_motion(self, x, y):
		'''\
			Handler for pointer motion events
		'''
		self.mouse_x = x
		self.mouse_y = y
	def draw(self):
		glClear(GL_COLOR_BUFFER_BIT)
		self.box.draw(self.y, math.exp(self.log_scale), self.width, self.height)
		glColor3d(0., 0., 0.)
		glDisable(GL_TEXTURE_2D)
		glPushMatrix()
		glTranslated(self.width/2., self.height/2., 0.)
		glCallList(App.__crosshair_display_list)
		glPopMatrix()
		if self.moving:
			glColor3dv(App.__arrow_color)
			glEnable(GL_LINE_SMOOTH)    # These happen not to work correctly on
			glEnable(GL_POLYGON_SMOOTH) # my hardware (all coverage values are 1)
			glLineWidth(2.)
			self.draw_arrow(
				self.width/2., self.height/2.,
				self.mouse_x, self.height - self.mouse_y)
		glutSwapBuffers()
	def mouse_button(self, button, state, x, y):
		if button == App.__mode_button and state == GLUT_DOWN:
			self.moving = not self.moving
			if self.moving:
				glutSetCursor(GLUT_CURSOR_NONE)
				glutTimerFunc(30, self.update, None)
			else:
				glutSetCursor(GLUT_CURSOR_INHERIT)
				glutPostRedisplay()
	def update(self, unused):
		if not self.moving:
			return
		x = 2.*self.mouse_x/self.width - 1.
		y = -(2.*self.mouse_y/self.height - 1.)
		d_log_scale = x*App.__speed_x
		self.log_scale += d_log_scale
		self.y = (
			self.height/2. + math.exp(d_log_scale)*(self.y - self.height/2.)
			- y*App.__speed_y)
		glutSetWindow(self.window)
		glutPostRedisplay()
		glutTimerFunc(30, self.update, None)
	def draw_arrow(self, xt, yt, xh, yh):
		'''\
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
		glCallList(App.__arrowhead_display_list)
		glPopMatrix()

glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
glutInitWindowSize(default_width, default_height)
glutInit(sys.argv)
app = App()
glutMainLoop()
