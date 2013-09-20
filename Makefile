.PHONY: lint, test

develop:
	virtualenv .venv --distribute
	. .venv/bin/activate && python setup.py develop && pip install nose-cov pylint

lint:
	pylint --rcfile .pylintrc gossamer

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=gossamer
