
PACKAGE_NAME=canossa
DEPENDENCIES=tff termprop
PYTHON=python
PYTHON25=python2.5
PYTHON26=python2.6
PYTHON27=python2.7
SETUP_SCRIPT=setup.py
RM=rm -rf
PIP=pip
CYTHON=cython

.PHONY: smoketest nosetest build setuptools install uninstall clean update

build: update_license_block smoketest
	ln -f $(PWD)/canossa/tff/tff.py /tmp/ctff.pyx
	$(CYTHON) /tmp/ctff.pyx -o ctff.c
	$(PYTHON) $(SETUP_SCRIPT) sdist
	$(PYTHON25) $(SETUP_SCRIPT) bdist_egg
	$(PYTHON26) $(SETUP_SCRIPT) bdist_egg
	$(PYTHON27) $(SETUP_SCRIPT) bdist_egg

setup_environment:
	if test -d tools; do \
		ln -f tools/gitignore .gitignore \
		ln -f tools/vimprojects .vimprojects \
    fi

update_license_block:
	chmod +x update_license
	find . -type f | grep '\(.py\|.c\)$$' | xargs ./update_license

setuptools:
	$(PYTHON) -c "import setuptools" || \
		curl http://peak.telecommunity.com/dist/ez_$(SETUP_SCRIPT) | $(PYTHON)

install: smoketest setuptools
	$(PYTHON) $(SETUP_SCRIPT) install

uninstall:
	for package in $(PACKAGE_NAME) $(DEPENDENCIES); \
	do \
		$(PIP) uninstall -y $$package; \
	done

clean:
	for name in dist cover build *.egg-info htmlcov; \
		do find . -type d -name $$name || true; \
	done | xargs $(RM)
	for name in *.pyc *.o; \
		do find . -type f -name $$name || true; \
	done | xargs $(RM)

test: smoketest nosetest

smoketest:
	$(PYTHON25) $(SETUP_SCRIPT) test
	$(PYTHON26) $(SETUP_SCRIPT) test
	$(PYTHON27) $(SETUP_SCRIPT) test

nosetest:
	if $$(which nosetests); \
	then \
	    nosetests --with-doctest \
	              --with-coverage \
	              --cover-html \
	              --cover-package=sskk; \
	fi

update: clean test
	$(PYTHON) $(SETUP_SCRIPT) register
	$(PYTHON) $(SETUP_SCRIPT) sdist upload
	$(PYTHON25) $(SETUP_SCRIPT) bdist_egg upload
	$(PYTHON26) $(SETUP_SCRIPT) bdist_egg upload
	$(PYTHON27) $(SETUP_SCRIPT) bdist_egg upload

cleanupdate: update
	ssh zuse.jp "rm -rf $(PACKAGE_NAME)"
	ssh zuse.jp "git clone git@github.com:saitoha/$(PACKAGE_NAME) --recursive"
	ssh zuse.jp "cd $(PACKAGE_NAME) && $(PYTHON26) $(SETUP_SCRIPT) bdist_egg upload"
	ssh zuse.jp "cd $(PACKAGE_NAME) && $(PYTHON27) $(SETUP_SCRIPT) bdist_egg upload"

