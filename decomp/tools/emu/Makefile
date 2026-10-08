# Needs libmgba-dev (Debian/Ubuntu: apt install libmgba-dev)
CFLAGS ?= -O2 -Wall
harness: harness.c
	$(CC) $(CFLAGS) -DM_CORE_GBA -DENABLE_VFS -o $@ $< -lmgba
