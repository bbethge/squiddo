#include <glib.h>
#include <stdlib.h>
#include "fs_server.h"

GAsyncQueue *fs_server_queue = NULL;

gpointer filesystem_server(gpointer unused) {
	fs_server_queue = g_async_queue_new();
	for (;;) {
		FilesystemRequest *req =
			(FilesystemRequest*) g_async_queue_pop(fs_server_queue);
		FilesystemResponse *resp = g_new(FilesystemResponse, 1);
		GDir *dir = g_dir_open(req->path, 0, NULL);
		if (dir == NULL) {
			resp->items = NULL;
			resp->n_items = 0;
			resp->n_hidden = 0;
		} else {
			// Count directory entries
			resp->n_items = 0;
			for (;;) {
				if (g_dir_read_name(dir) == NULL) {
					break;
				}
				resp->n_items++;
			}
			g_dir_rewind(dir);
			// Actually read directory entries, and record the
			// number that are hidden
			resp->items = g_new(Box*, resp->n_items);
			resp->n_hidden = 0;
			for (guint i = 0; i < resp->n_items; i++) {
				const gchar *name = g_dir_read_name(dir);
				// name can't be NULL, right?
				gchar *path = g_build_filename(
					req->path, name, NULL
				);
				resp->items[i] = box_new(path);
				g_free(path);
				if (name[0] == '.') {  // TODO: make portable
					resp->n_hidden++;
				}
			}
			// Sort items
			qsort(
				resp->items, (size_t)resp->n_items,
				sizeof (resp->items[0]), box_compare
			);
		}
		// Send response
		g_async_queue_push(req->queue, resp);
		g_free(req);
	}
	g_async_queue_unref(fs_server_queue);
	return NULL;
}
