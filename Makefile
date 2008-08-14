CC := gcc
CFLAGS := -std=gnu99 $(shell pkg-config --cflags glib-2.0) \
	$(shell pkg-config --cflags gthread-2.0) \
	$(shell pkg-config --cflags pangoft2)
LDLIBS := -lm -lGL -lGLU -lglut $(shell pkg-config --libs glib-2.0) \
	$(shell pkg-config --libs gthread-2.0) \
	$(shell pkg-config --libs pangoft2)
DEBUG := 1
ifeq ($(strip $(DEBUG)),1)
	CFLAGS += -g
	LDFLAGS += -g
endif

squiddo: main.o browser.o box.o fs_server.o
	$(CC) -o $@ $^ $(LDFLAGS) $(LDLIBS)

.PHONY: clean
clean:
	$(RM) squiddo *.o
