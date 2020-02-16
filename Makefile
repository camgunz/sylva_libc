.PHONY: test install help

help:
	@echo "Commands: test | install"

venv:
ifeq ($(VIRTUAL_ENV), )
	$(error "Not running in a virtualenv")
endif

depinstall: venv
	@pip install -r dev-requirements.txt

install: depinstall
	python setup.py install

test: install
	sylva_libc $$(cat musl-libc.txt)
