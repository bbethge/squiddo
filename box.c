#include <glib.h>
#include <glib-object.h>
#include <pango/pango.h>
#include <pango/pangoft2.h>
#include <ft2build.h>
#include FT_FREETYPE_H
#include <GL/freeglut.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "browser.h"
#include "fs_server.h"
#include "box.h"

#define CORNER_SIZE 0.25
#define CORNER_DETAIL 8
#define BACKGROUND_FADE_START_HEIGHT 3.0
#define BACKGROUND_FADE_END_HEIGHT 10.0
#define LABEL_FADE_START_HEIGHT 12.0
#define LABEL_FADE_END_HEIGHT 20.0
#define CONTENTS_MIN_HEIGHT 20.0
#define N_COLORS 2

const GLubyte box_colors[N_COLORS][3] =
	{ { 200, 200, 200 }, { 180, 200, 220 } };
const GLubyte label_color[3] = { 0, 0, 0 };

// Forward declare all static functions
void background_vertex(double x, double y);
void create_name_display_list(Box *self);
void draw(
	Box *self, double y, double height, guint color,
	int win_width, int win_height
);

GLuint bg_display_list_base;
PangoFontMap *font_map;
PangoContext *pango_context;

void background_vertex(double x, double y) {
	glTexCoord1d(0.25 + 0.25*x/BOX_ASPECT + 0.25*(1.0 - y) );
	glVertex2d(x, y);
}

void box_class_init(void) {
	if (bg_display_list_base != 0) return;
	bg_display_list_base = glGenLists(N_COLORS);
	for (guint color = 0; color < N_COLORS; color++) {
		glNewList(bg_display_list_base + color, GL_COMPILE);
			GLubyte texture[8];
			memcpy(
				&texture[0], box_colors[color],
				sizeof (box_colors[color])
			);
			memcpy(
				&texture[3], background_color,
				sizeof (background_color)
			);
			glEnable(GL_TEXTURE_1D);
			glTexImage1D(
				GL_TEXTURE_1D, 0, GL_RGB8, 2, 0, GL_RGB,
				GL_UNSIGNED_BYTE, texture
			);
			glBegin(GL_QUAD_STRIP);
				background_vertex(BOX_ASPECT, 0.0);
				background_vertex(BOX_ASPECT, 1.0);
				for (int n = 0; n < CORNER_DETAIL + 1; n++) {
					double agl = M_PI_2*n/CORNER_DETAIL;
					background_vertex(
						CORNER_SIZE*(1.0 - sin(agl) ),
						CORNER_SIZE*(1.0 - cos(agl) )
					);
					background_vertex(
						CORNER_SIZE*(1.0 - sin(agl) ),
						1.0 - CORNER_SIZE*(1.0 - cos(agl) )
					);
				}
			glEnd();
			glDisable(GL_TEXTURE_1D);
		glEndList();
	}
	glPixelZoom(1.0f, -1.0f);
	font_map = pango_ft2_font_map_new();
	pango_ft2_font_map_set_resolution(
		PANGO_FT2_FONT_MAP(font_map), 100, 100
	);
	pango_context =
		pango_ft2_font_map_create_context(PANGO_FT2_FONT_MAP(font_map));
	pango_context_set_language(pango_context, pango_language_get_default());
	pango_context_set_base_dir(pango_context, PANGO_DIRECTION_LTR);
}

// TODO: actually call this
void box_class_fini() {
	glDeleteLists(bg_display_list_base, 1);
	g_object_unref(G_OBJECT(pango_context) );
	g_object_unref(G_OBJECT(font_map) );
}

Box *box_new(const gchar *path) {
	Box *self = g_new(Box, 1);
	self->path = g_strdup(path);
	self->name = g_path_get_basename(path);
	self->contents_requested = FALSE;
	self->contents_loaded = FALSE;
	self->collation_key = g_utf8_collate_key_for_filename(
		self->name[0] == '.' ? self->name+1 : self->name, -1
	);
	self->queue = NULL;
	self->name_display_list = 0;
	return self;
}

void box_destroy(Box *self) {
	g_free(self->path);
	g_free(self->name);
	g_free(self->collation_key);
	if (self->queue != NULL) {
		g_async_queue_unref(self->queue);
	}
	if (self->contents_loaded && self->items != NULL) {
		for (guint i = 0; i < self->n_items; i++) {
			box_destroy(self->items[i]);
		}
		g_free(self->items);
	}
	if (self->name_display_list != 0) {
		glDeleteLists(self->name_display_list, 1);
	}
	g_free(self);
}

gint box_compare(const void *a, const void *b) {
	Box *box_a = *(Box**)a;
	Box *box_b = *(Box**)b;
	return strcmp(box_a->collation_key, box_b->collation_key);
}

void create_name_display_list(Box *self) {
	PangoLayout *layout = pango_layout_new(pango_context);
	pango_layout_set_text(layout, self->name, -1);
	PangoRectangle extents;
	pango_layout_get_pixel_extents(layout, &extents, NULL);
	// Create an FT_Bitmap by hand
	FT_Bitmap bitmap;
	bitmap.width = extents.width;
	bitmap.rows = extents.height;
	bitmap.pitch = (bitmap.width+3) & ~3;
	bitmap.pixel_mode = FT_PIXEL_MODE_GRAY;
	bitmap.num_grays = 256;
	bitmap.buffer = g_new0(guchar, bitmap.pitch*bitmap.rows);
	pango_ft2_render_layout(&bitmap, layout, -extents.x, -extents.y);
	self->name_display_list = glGenLists(1);
	glNewList(self->name_display_list, GL_COMPILE);
		glDrawPixels(
			bitmap.width, bitmap.rows, GL_ALPHA, GL_UNSIGNED_BYTE,
			bitmap.buffer
		);
	glEndList();
	g_object_unref(G_OBJECT(layout) );
	g_free(bitmap.buffer);
}

void box_draw(
	Box *self, double y, double height, int win_width, int win_height
) {
	glDisable(GL_LINE_SMOOTH);
	draw(self, y, height, 0, win_width, win_height);
}

void draw(
	Box *self, double y, double height, guint color,
	int win_width, int win_height
) {
	double alpha;
	// Draw background
	if (height < BACKGROUND_FADE_END_HEIGHT) {
		alpha = (height-BACKGROUND_FADE_START_HEIGHT)
			/ (BACKGROUND_FADE_END_HEIGHT
				- BACKGROUND_FADE_START_HEIGHT);
	} else {
		alpha = 1.0;
	}
	glColor4d(1.0, 1.0, 1.0, alpha);
	glPushMatrix();
		glTranslated(win_width - height*BOX_ASPECT, y, 0.0);
		glScaled(height, height, 1.0);
		glCallList(bg_display_list_base + color);
	glPopMatrix();
	if (height < LABEL_FADE_START_HEIGHT) return;
	if (self->name_display_list == 0) {
		create_name_display_list(self);
	}
	if (height < LABEL_FADE_END_HEIGHT) {
		alpha = (height-LABEL_FADE_START_HEIGHT)
			/ (LABEL_FADE_END_HEIGHT-LABEL_FADE_START_HEIGHT);
	} else {
		alpha = 1.0;
	}
	glColor4ub(
		label_color[0], label_color[1], label_color[2],
		(GLubyte) (alpha*255.0)
	);
	glRasterPos2d(win_width - height*BOX_ASPECT, y + height/2.0);
	glCallList(self->name_display_list);
	if (height < CONTENTS_MIN_HEIGHT) return;  // No point drawing contents
	// Make sure contents are loaded
	if (!self->contents_loaded) {
		if (!self->contents_requested) {
			if (self->queue == NULL) {
				self->queue = g_async_queue_new();
			}
			FilesystemRequest *req = g_new(FilesystemRequest, 1);
			req->path = self->path;
			req->queue = self->queue;
			g_async_queue_push(fs_server_queue, req);
			self->contents_requested = TRUE;
		}
		FilesystemResponse *resp = g_async_queue_try_pop(self->queue);
		if (resp == NULL) return;  // Couldn't load contents this time
		self->items = resp->items;
		self->n_items = resp->n_items;
		self->n_hidden = resp->n_hidden;
		self->contents_loaded = TRUE;
	}
	if (self->n_items == 0) return;
	if (self->n_items == 1) {
		draw(
			self->items[0], y + height/4.0, height/2.0,
			(color+1) % N_COLORS, win_width, win_height
		);
		return;
	}
	double item_height = height/self->n_items;
	if (item_height < BACKGROUND_FADE_START_HEIGHT) return;
	guint first_box = 0;
	if (y + height > win_height) {
		first_box = (guint) ( (y+height-win_height) / item_height);
	}
	guint last_box = self->n_items;
	if (y < 0.0) {
		last_box = self->n_items - (guint) (-y/item_height);
	}
	for (guint i = first_box; i < last_box; i++) {
		draw(
			self->items[i],
			y + (self->n_items-i-1) * item_height, item_height,
			(color+i+1) % N_COLORS, win_width, win_height
		);
	}
}
