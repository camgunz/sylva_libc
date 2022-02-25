.PHONY: help venv depinstall install linuxtest macos_test

help:
	@echo "Commands: linux_test | macos_test | depinstall | install"

venv:
ifeq ($(VIRTUAL_ENV), )
	$(error "Not running in a virtualenv")
endif

depinstall: venv
	@pip install -r dev-requirements.txt

install: depinstall
	python setup.py install

linux_test: install
	sylva_libc --preprocessor=/usr/bin/clang $$(cat musl-libc.txt)

macos_test: install
	sylva_libc --preprocessor=/usr/bin/clang --libclang=/Library/Developer/CommandLineTools/usr/lib/libclang.dylib $$(cat macos-libc.txt)
