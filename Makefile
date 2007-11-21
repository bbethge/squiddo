CC := gcc
override CFLAGS += -Wall $(shell pkg-config gtk+-2.0 --cflags) \
	-DGTK_DISABLE_DEPRECATED=1 -DGDK_DISABLE_DEPRECATED=1 \
	-DG_DISABLE_DEPRECATED=1
override LDFLAGS += $(shell pkg-config gtk+-2.0 --libs) -lm
GOB := gob2
GOB_FLAGS += --no-touch --no-private-header
GOB_SOURCES := squiddo-window.gob squiddo-control.gob squiddo-box.gob
GENERATED_C_SOURCES := $(GOB_SOURCES:.gob=.c)
GENERATED_HEADERS := $(GOB_SOURCES:.gob=.h)
C_SOURCES := main.c $(GENERATED_C_SOURCES)
OBJECTS := $(C_SOURCES:.c=.o)

squiddo: $(OBJECTS)
	$(CC) -o $@ $(LDFLAGS) $^ $(LDLIBS)

%.d: %.c
	@set -e; rm -f $@; \
	$(CC) -MM $(CPPFLAGS) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

include $(C_SOURCES:.c=.d)

%.c %.h: %.gob
	$(GOB) $(GOB_FLAGS) $^

.SECONDARY: $(GENERATED_C_SOURCES)

clean:
	$(RM) $(C_SOURCES:.c=.d)
	$(RM) $(GENERATED_C_SOURCES)
	$(RM) $(GENERATED_HEADERS)
	$(RM) $(OBJECTS)
	$(RM) squiddo
