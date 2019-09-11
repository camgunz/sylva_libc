.PHONY: test install help

test: install
	sylva_libc $(cat musl-libc.txt) -o libc.sy

install:
	python setup.py install

help:
	@echo "Commands: test | install"
