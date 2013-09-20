.PHONY: lint, test, dist, release

develop:
	virtualenv .venv --distribute
	. .venv/bin/activate && python setup.py develop && pip install nose-cov pylint

lint:
	pylint --rcfile .pylintrc gossamer

test:
	nosetests --verbose --with-cover --cover-erase --cover-package=gossamer

doc:
	pandoc -f markdown -t rst README.md > README

dist:
	python setup.py sdist --format=gztar

release:
	make doc
	make dist
	git tag -a $(version) -m "Release $(version)"
