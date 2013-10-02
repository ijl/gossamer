.PHONY: lint
.PHONY: test
.PHONY: doc
.PHONY: dist
.PHONY: release

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
	rm -rf dist
	python setup.py sdist --format=gztar
	rm -rf *.egg-info

release:
	make doc
	make dist
	git tag -a $(version) -m "Release $(version)"
	rm README
