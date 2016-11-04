CFLAGS+=-Wall

.phony: install clean

poll: poll.c

install: poll
	install poll offsw /usr/local/sbin

clean:
	rm -f poll
