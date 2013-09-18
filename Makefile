.PHONY: lint, test

lint:
	pylint --rcfile .pylintrc huxley

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=huxley
