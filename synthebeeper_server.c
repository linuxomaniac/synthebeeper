/*
 * Compilation : gcc synthebeeper_server.c -Wall -std=c11 -o synthebeeper_server
 * Écrit par Linuxomaniac, licence GPLv3
 */

#define PORT 4243

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/kd.h>
#include <arpa/inet.h>

#ifndef CLOCK_TICK_RATE
#define CLOCK_TICK_RATE 1193180
#endif

int console_fd = -1;

void beep(unsigned int freq) {
	if(ioctl(console_fd, KIOCSOUND, (int)(freq != 0 ? CLOCK_TICK_RATE/freq : freq)) < 0) {
		perror("ioctl");
	}
}

void handle_signal(int signum) {
	if(signum == SIGINT) {
		if(console_fd >= 0) {
			beep(0);
			close(console_fd);
		}
		exit(signum);
	}
}

int main(void) {
	int serversock, newsock, n;
	struct sockaddr_in my_addr;
	unsigned int yes = 1, buf;

	if((serversock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		exit(1);
	}

	my_addr.sin_family = AF_INET;
	my_addr.sin_port = htons(PORT);
	my_addr.sin_addr.s_addr = INADDR_ANY;
	memset(my_addr.sin_zero, 0, sizeof(my_addr.sin_zero));

	if(setsockopt(serversock, SOL_SOCKET, SO_REUSEADDR, (char *)&yes, sizeof(int)) < 0) {
		close(serversock);
		exit(2);
	}

	if(bind(serversock, (struct sockaddr *)&my_addr, sizeof(struct sockaddr)) < 0) {
		close(serversock);
		exit(3);
	}

	if(listen(serversock, 1) < 0) {
		close(serversock);
		exit(4);
	}

	printf("En écoute sur le port tai tai %d...\n", PORT);

	signal(SIGINT, handle_signal);

	while(1) {
		if((newsock = accept(serversock, NULL, NULL)) < 0) {
			close(serversock);
			exit(5);
		}

		if((console_fd = open("/dev/tty0", O_WRONLY)) < 0) {
			printf("Could not open /dev/tty0 for writing.\n");
			perror("Open");
			close(newsock);
			close(serversock);
			exit(6);
		}

		printf("Une connexion ! En écoute de la sauce...\n");

		while((n = recv(newsock, &buf, sizeof(unsigned int), 0)) > 0) {
			beep(buf);
		}

		beep(0);
		close(console_fd);
		console_fd = -1;

		close(newsock);
		printf("Connexion fermée.\n");
	}

	return 0;
}
