#include <GL/freeglut.h>
#include <glib.h>
#include <glib-object.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "browser.h"
#include "fs_server.h"

int main(int argc, char *argv[]) {
	g_thread_init(NULL);
	g_type_init();
	glutInit(&argc, argv);
	glutSetOption(
		GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_CONTINUE_EXECUTION
	);
	g_thread_create(filesystem_server, NULL, FALSE, NULL);
	browser = browser_new("/");
	glutMainLoop();
	return 0;
}
