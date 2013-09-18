.PHONY: lint, test

lint:
	pylint --rcfile .pylintrc gossamer

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=gossamer
