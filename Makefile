.PHONY: test

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=huxley
