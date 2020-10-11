.PHONY: all tests

all: linting tests elfs

linting:
	# flake8 abstruct
	pylint abstruct

tests:
	py.test

elfs:
	make -C extra/elf/

clean:
	make -C extra/elf/ clean
