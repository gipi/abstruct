.PHONY: all

all: linting tests elfs

linting:
	# flake8 abstruct
	pylint abstruct

tests:
	python -m unittest

elfs:
	make -C extra/elf/

clean:
	make -C extra/elf/ clean
