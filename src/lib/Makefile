CFLAGS=-Wall -Wextra

SRCDIR=src
BINDIR=bin

SRCS=$(wildcard $(SRCDIR)/*.c)
EXES=$(patsubst $(SRCDIR)/%.c,$(BINDIR)/%,$(SRCS))

all: $(EXES)

$(BINDIR)/%: $(SRCDIR)/%.c | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ $<

$(BINDIR):
	mkdir -p $(BINDIR)

clean:
	rm -rf $(BINDIR)/*

.PHONY: all clean

