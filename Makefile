
all:
	
run:
	python canossa/__init__.py

install:
	#curl http://peak.telecommunity.com/dist/ez_setup.py | python
	python setup.py install

uninstall:
	yes | pip uninstall tff canossa 
	
clean:
	rm -rf dist/ build/ canossa.egg-info
	rm -f **/*.pyc

test:
	python setup.py test

update:
	python setup.py register
	python setup.py sdist upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload

