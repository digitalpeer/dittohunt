RCC = pyrcc4 -py3

generated = dittohunt/dittohunt_rc.py

all: $(generated)

dittohunt/%_rc.py: dittohunt/res/%.qrc
	$(RCC) $< -o $@
# Get rid of the generated PyQt4 import and use our own wrapper
	sed -i 's/from PyQt4 import QtCore/from .qt import */' $@

LINT_FILES=dittohunt/dittohunt.py

pylint:
	pylint --reports=n $(LINT_FILES)

pylint3:
	pylint3 --reports=n $(LINT_FILES)

clean:
	rm -f *.pyc dittohunt/*.pyc *.pyo dittohunt/*.pyo $(generated)
	rm -rf dist build dittohunt.egg-info

package: $(generated)
	python setup.py sdist
	python setup.py bdist_wheel

installer: $(generated)
	pyinstaller -y dittohunt.spec
	( cd dist && zip dittohunt.zip -r dittohunt )
