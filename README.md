Ditto Hunt
==========

Ditto Hunt is a duplicate file finder that quickly finds duplicate files
recursively under a folder and allows you to preview and then select which
versions should be deleted or moved to another folder.  It does not use
filenames for comparison, and instead does a binary comparison of all files.

This utility is handy, for example, if you have a bunch of images and want to
find and get rid of duplicate images.  However, it can be used with any file
type.


Features
--------

* Quick duplicate file search.
* Multi platform.
* Easy and straightforward to use.

Runtime Requirements
--------------------

This is just an overview of runtime requirements. All major versions of both the
Python interpreter and QT API are supported.

* [Python2 or Python3](https://www.python.org/)
* [PyQt4 or PyQt5](https://riverbankcomputing.com/software/pyqt/intro) or
  [PySide](https://wiki.qt.io/PySide)
* [Qt](https://www.qt.io/)


Installation
------------
For simplicity, instructions for only PyQt4 and Python2 are listed here.
However, you can adjust to use any combination of Python2/Python3 and
PyQt4/PyQt5/PySide if you prefer when it comes to runtime dependencies.

On Ubuntu or Debian, first install dependencies using the system package
manager.

    sudo apt-get install python python-qt4 python-pip

Then, use pip to install dittohunt.

    pip install [--user] dittohunt

Or, if you're installing from source:

    pip install [--user] dittohunt-<version>.tar.bz2

The --user option causes dittohunt to be installed in your home directory under
~/.local. You may have to add this to your path in some environments.

Then, if you somehow get fed up with Ditto Hunt's awesomeness, uninstall it.

    pip uninstall dittohunt


Running
-------

Just execute `dittohunt`.


Screenshots
-----------
![Main Window](https://raw.githubusercontent.com/digitalpeer/dittohunt/master/screenshots/main_window.png)


PyQt4/PyQt5/PySide
------------------
Ditto Hunt can use PyQt4, PyQt5, or PySide for its Qt API.  As long as you have
one installed, it will be automatically detected and used at runtime. However,
if you wish to force a specific Qt API, you can set the QT_API environment
variable to one of the following values when running.

    QT_API=pyqt4 dittohunt
    QT_API=pyqt5 dittohunt
    QT_API=pyside dittohunt


License
-------
Ditto Hunt is licensed under GPL Version 3.  See the `LICENSE.txt` file.  `qt.py`
is licensed under 3-clause BSD.  `pyside_dyanmic.py` is MIT licensed.
