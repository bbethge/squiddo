#ifndef _BOX_H
#define _BOX_H

#include <glib.h>
#include <GL/gl.h>

#define BOX_ASPECT 2.0

typedef struct _Box {
	char *path;  // Filesystem path of the directory this box represents
	char *name;  // Pretty name of this box
	guint n_items;
	struct _Box **items;
	guint n_hidden;
	gboolean contents_requested;
	gboolean contents_loaded;
	GAsyncQueue *queue;
	char *collation_key;
	GLuint name_display_list;  // 0 means hasn't been created yet
} Box;

void box_class_init(void);
	// Make sure you call this between creating a GLUT window and the first
	// call to box_new.  Multiple calls are okay.

Box *box_new(const gchar *path);
void box_destroy(Box *self);

void box_draw(
	Box *self, double y, double height, int win_width, int win_height
);	// Draw a (root) box.
	// y = y-coord of bottom of box in GL coords
	// height = height of box in pixels (GL coords)
	// win_width, win_height = dimensions of window

gint box_compare(const void *a, const void *b);
	// To be used with qsort.  The arguments must be double pointers to Box,
	// ie, type Box**.  Compares based on the pretty names of the boxes.

#endif
