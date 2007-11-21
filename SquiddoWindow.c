#include <glib-object.h>
#include <gtk/gtk.h>
#include "SquiddoWindow.h"

static void squiddo_window_init(GTypeInstance *inst, gpointer klass);

GType squiddo_window_get_type(void) {
	static GType type = 0;
	if(type == 0) {
		static const GTypeInfo info = {
			sizeof(SquiddoWindowClass),
			NULL, /* base_init */
			NULL, /* base_finalize */
			(GClassInitFunc) NULL,
			NULL, /* class_finalize */
			NULL, /* class_data */
			sizeof(SquiddoWindow),
			0, /* n_preallocs */
			(GInstanceInitFunc) squiddo_window_init
		};
		type = g_type_register_static(
			GTK_TYPE_WINDOW, "SquiddoWindowType", &info, 0
		);
	}
	return type;
}

static void squiddo_window_init(GTypeInstance *inst, gpointer klass) {
	GtkWidget *self = (GtkWidget*)inst;
	GtkWidget *vbox;
	GtkWidget *toolbar;
	GtkToolItem *quit_button;
	GtkWidget *statusbar;

	gtk_window_set_default_size(GTK_WINDOW(self), 400, 300);
	gtk_window_set_title(GTK_WINDOW(self), "Squiddo System Browser");

	vbox = gtk_vbox_new(FALSE, 0);
	gtk_container_add(GTK_CONTAINER(self), vbox);
	gtk_widget_show(vbox);

	toolbar = gtk_toolbar_new();
	gtk_box_pack_start(GTK_BOX(vbox), toolbar, FALSE, FALSE, 0);
	gtk_widget_show(toolbar);

	quit_button = gtk_tool_button_new_from_stock(GTK_STOCK_QUIT);
	g_signal_connect_swapped(
		G_OBJECT(quit_button), "clicked",
		G_CALLBACK(gtk_widget_destroy), self
	);
	gtk_toolbar_insert(GTK_TOOLBAR(toolbar), quit_button, -1);
	gtk_widget_show(GTK_WIDGET(quit_button));

	statusbar = gtk_statusbar_new();
	gtk_box_pack_start(GTK_BOX(vbox), statusbar, FALSE, FALSE, 0);
	gtk_widget_show(statusbar);
}

GtkWidget *squiddo_window_new() {
	return g_object_new(SQUIDDO_WINDOW_TYPE, NULL);
}
