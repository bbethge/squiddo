#include <GL/freeglut.h>
#include <GL/gl.h>
#include <glib.h>
#include <stdlib.h>
#include <math.h>
#include "browser.h"
#include "box.h"

#define DEFAULT_WIDTH 640u   // Default window dimensions
#define DEFAULT_HEIGHT 480u  //
#define MODE_SWITCH_BUTTON GLUT_LEFT_BUTTON
#define CROSSHAIR_SIZE 7  // Radius of crosshair in pixels
#define SENS_Y_PIX_PER_SEC 667.0
#define FRAME_PERIOD_MSEC 30
#define ARROW_SIZE 12.0
#define ARROW_ANGLE (25.0*M_PI/180.0)

#define FRAME_RATE (1000.0/FRAME_PERIOD_MSEC)
#define SENS_Y_PIX_PER_FRAME (SENS_Y_PIX_PER_SEC/FRAME_RATE)

const GLubyte background_color[3] = { 255, 255, 255 };
const GLubyte arrow_color[3] = { 0, 0, 0 };
const GLubyte crosshair_color[3] = { 0, 0, 0 };

// Nifty GCC-only macro to compute squares
#define SQ(x) ({ typeof (x) __x = (x); __x*__x; })

// Forward declare all static functions
double get_root_box_height(Browser *self);
void on_reshape(int width, int height);
void on_mouse_motion(int x, int y);
void on_mouse_button(int button, int state, int x, int y);
void draw_arrow(int xt, int yt, int xh, int yh);

// For now this is a singleton.  Since GLUT doesn't support user data in
// callbacks, it's hard to support multiple browser windows.
Browser *browser;

Browser *browser_new(const char *path) {
	Browser *self = g_new(Browser, 1);
	self->moving = FALSE;
	self->y = 0.0;
	self->log_scale = 0.0;
	self->width = DEFAULT_WIDTH;
	self->height = DEFAULT_HEIGHT;
	self->frame_count = 0u;
	// Create a window
	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE);
	glutInitWindowSize(DEFAULT_WIDTH, DEFAULT_HEIGHT);
	self->window = glutCreateWindow("Squiddo System Browser");
	box_class_init();
	self->root_box = box_new(path);
	// Register window callbacks with GLUT
	glutReshapeFunc(on_reshape);
	glutMotionFunc(on_mouse_motion);
	glutPassiveMotionFunc(on_mouse_motion);
	glutMouseFunc(on_mouse_button);
	glutDisplayFunc(browser_draw);
	// Initialize GL state
	glClearColor(
		background_color[0]/255.0, background_color[1]/255.0,
		background_color[2]/255.0, 1.0
	);
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);
	glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAX_LEVEL, 0);
	return self;
}

void browser_destroy(Browser *self) {
	box_destroy(self->root_box);
	g_free(self);
}

double get_root_box_height(Browser *self) {
	return self->height*exp(self->log_scale);
}

void browser_update(int unused) {
	if (!browser->moving) return;
	double sens_x_logs_per_frame = SENS_Y_PIX_PER_FRAME/(browser->width/2);
	double mouse_scale = (double) MIN(browser->width/2, browser->height/2);
	double x = (browser->mouse_x-browser->width/2) / mouse_scale;
	double y = -(browser->mouse_y-browser->height/2) / mouse_scale;
	double d_log_scale = x*sens_x_logs_per_frame;
	double min_log_scale =
		MIN(0.0, log(browser->width/(browser->height*BOX_ASPECT) ) );
	if (browser->log_scale + d_log_scale < min_log_scale) {
		d_log_scale = min_log_scale - browser->log_scale;
	}
	browser->log_scale += d_log_scale;
	browser->y = 
		browser->height/2.0
		+ exp(d_log_scale) * (browser->y - browser->height/2.0)
		- y*SENS_Y_PIX_PER_FRAME;
	double root_box_height = get_root_box_height(browser);
	if (browser->log_scale < 0.0) {
		if (browser->y < 0.0) {
			browser->y = 0.0;
		} else if (browser->y + root_box_height > browser->height) {
			browser->y = browser->height - root_box_height;
		}
	} else {
		if (browser->y > 0.0) {
			browser->y = 0.0;
		} else if (browser->y + root_box_height < browser->height) {
			browser->y = browser->height - root_box_height;
		}
	}
	glutSetWindow(browser->window);
	glutPostRedisplay();
	glutTimerFunc(FRAME_PERIOD_MSEC, browser_update, 0);
}

void browser_draw(void) {
	browser->frame_count++;
	glClear(GL_COLOR_BUFFER_BIT);
	// Draw box hierarchy
	box_draw(
		browser->root_box, browser->y, get_root_box_height(browser),
		browser->width, browser->height
	);
	// Draw crosshair
	glColor3ubv(crosshair_color);
	glDisable(GL_LINE_SMOOTH);
	glBegin(GL_LINES);
		glVertex2i(browser->width/2, browser->height/2-CROSSHAIR_SIZE);
		glVertex2i(browser->width/2, browser->height/2+CROSSHAIR_SIZE);
		glVertex2i(browser->width/2-CROSSHAIR_SIZE, browser->height/2);
		glVertex2i(browser->width/2+CROSSHAIR_SIZE, browser->height/2);
	glEnd();
	if (browser->moving) {
		// Draw arrow
		glColor3ubv(arrow_color);
		glEnable(GL_LINE_SMOOTH);    // These happen not to work correctly on
		glEnable(GL_POLYGON_SMOOTH); // my hardware (all coverage values are 1)
		glLineWidth(2.0);
		draw_arrow(
			browser->width/2, browser->height/2,
			browser->mouse_x, browser->height - browser->mouse_y
		);
		glLineWidth(1.0);
	}
	glutSwapBuffers();
}

void draw_arrow(int xt, int yt, int xh, int yh) {
	glPushMatrix();
		glTranslated(xt, yt, 0.0);
		glRotated(atan2(yh - yt, xh - xt)*180.0/M_PI, 0.0, 0.0, 1.0);
		glBegin(GL_LINES);
			glVertex2d(0.0, 0.0);
			double length = sqrt(SQ(xh - xt) + SQ(yh - yt) );
			glVertex2d(length - ARROW_SIZE*cos(ARROW_ANGLE), 0.0);
		glEnd();
		glTranslated(length, 0.0, 0.0);
		glBegin(GL_TRIANGLES);
			glVertex2d(0.0, 0.0);
			glVertex2d(
				-ARROW_SIZE*cos(ARROW_ANGLE),
				ARROW_SIZE*sin(ARROW_ANGLE)
			);
			glVertex2d(
				-ARROW_SIZE*cos(ARROW_ANGLE),
				-ARROW_SIZE*sin(ARROW_ANGLE)
			);
		glEnd();
	glPopMatrix();
}

void on_reshape(int width, int height) {
	browser->y += (height - browser->height)/2.0;
	browser->width = width;
	browser->height = height;
	glViewport(0, 0, width, height);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0.0, width, 0.0, height, -1.0, 1.0);
	glMatrixMode(GL_MODELVIEW);
}

void on_mouse_motion(int x, int y) {
	browser->mouse_x = x;
	browser->mouse_y = y;
}

void on_mouse_button(int button, int state, int x, int y) {
	if (button == MODE_SWITCH_BUTTON && state == GLUT_DOWN) {
		browser->moving = !browser->moving;
		if (browser->moving) {
			glutSetCursor(GLUT_CURSOR_NONE);
			glutTimerFunc(FRAME_PERIOD_MSEC, browser_update, 0);
		} else {
			glutSetCursor(GLUT_CURSOR_INHERIT);
			glutPostRedisplay();
		}
	}
}
