#ifndef _SQUIDDO_WINDOW_H
#define _SQUIDDO_WINDOW_H

#include <glib-object.h>
#include <gtk/gtkwidget.h>
#include <gtk/gtkwindow.h>

typedef struct _SquiddoWindow SquiddoWindow;
typedef struct _SquiddoWindowClass SquiddoWindowClass;

#define SQUIDDO_WINDOW_TYPE (squiddo_window_get_type())
#define SQUIDDO_WINDOW(obj) ( \
	G_TYPE_CHECK_INSTANCE_CAST((obj), SQUIDDO_WINDOW_TYPE, SquiddoWindow) \
)
#define SQUIDDO_WINDOW_CLASS(klass) ( \
	G_TYPE_CHECK_CLASS_CAST( \
		(klass), SQUIDDO_WINDOW_TYPE, SquiddoWindowClass \
	) \
)
#define SQUIDDO_IS_WINDOW(obj) ( \
	G_TYPE_CHECK_INSTANCE_TYPE((obj), SQUIDDO_WINDOW_TYPE) \
)
#define SQUIDDO_IS_WINDOW_CLASS(klass) ( \
	G_TYPE_CHECK_CLASS_TYPE((klass), SQUIDDO_WINDOW_TYPE) \
)
#define SQUIDDO_WINDOW_GET_CLASS(obj) ( \
	G_TYPE_INSTANCE_GET_CLASS( \
		(obj), SQUIDDO_WINDOW_TYPE, SquiddoWindowClass \
	) \
)

struct _SquiddoWindow {
	GtkWindow parent;
};

struct _SquiddoWindowClass {
	GtkWindowClass parent;
};

GType squiddo_window_get_type();
GtkWidget *squiddo_window_new();

#endif
