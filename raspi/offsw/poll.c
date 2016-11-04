#include <err.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>

int main(int argc, char *argv[]) {

	if (argc != 2)
		errx(1, "invalid argument");

	int fd = open(argv[1], O_RDONLY);

	if (fd < 0) err(1, "open");
	
	int ret = lseek(fd, 0, SEEK_END);
	if (ret < 0) err(1, "lseek");

	{
		char buf[1];
		int ret = read(fd, buf, 1);
		if (ret < 0) err(1, "read");
	}

	struct pollfd pollfd = {
		.fd = fd,
		.events = POLLPRI|POLLERR,
	};

	ret = poll(&pollfd, 1, -1);

	if (ret < 0) err(1, "poll");

	return 0;
}

