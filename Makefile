.PHONY: test install help

test: install
	sylva_libc -o libc.sy $$(cat musl-libc.txt)

install:
	python setup.py install

help:
	@echo "Commands: test | install"
