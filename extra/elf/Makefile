SRC = main.c

CPPFLAGS = -g -Wall

TARGETS  = main_amd64
TARGETS += main_x86
TARGETS += main.so
TARGETS += main_arm32
TARGETS += main_arm64

all: $(TARGETS)

%.so: %.c
	$(CC) $(CPPFLAGS) $^ -shared -o $@

main_%: main.c
	$(CC) $(CPPFLAGS) $^ -o $@

main_x86: CC=i686-linux-gnu-gcc
main_amd64: CC=gcc
main_arm32: CC=arm-linux-gnueabi-gcc
main_arm64: CC=aarch64-linux-gnu-gcc-10

clean:
	rm -vf $(TARGETS)
