#ifndef _FS_SERVER_H
#define _FS_SERVER_H

#include <glib.h>
#include "box.h"

typedef struct {
	const gchar *path;
	GAsyncQueue *queue;
} FilesystemRequest;

typedef struct {
	Box **items;
	guint n_items;
	guint n_hidden;
} FilesystemResponse;

extern GAsyncQueue *fs_server_queue;

gpointer filesystem_server(gpointer unused);

#endif
