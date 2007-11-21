#include <gtk/gtk.h>
#include "SquiddoWindow.h"

int main(int argc, char *argv[]) {
	GtkWidget *win;

	gtk_init(&argc, &argv);
	win = squiddo_window_new();
	g_signal_connect(
		G_OBJECT(win), "hide", G_CALLBACK(gtk_main_quit), NULL
	);
	gtk_widget_show(win);

	gtk_main();
	return 0;
}
