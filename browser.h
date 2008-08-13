#ifndef _BROWSER_H
#define _BROWSER_H

#include <glib.h>
#include <GL/gl.h>
#include "box.h"

typedef struct {
	gboolean moving;
	double y;
	double log_scale;
	int width, height;
	int mouse_x, mouse_y;
	guint frame_count;
	int window;
	Box *root_box;
} Browser;

extern const GLubyte background_color[3];

extern Browser *browser;

Browser *browser_new(const char *path);
void browser_update(int unused);
void browser_draw(void);
void browser_destroy(Browser *self);

#endif
