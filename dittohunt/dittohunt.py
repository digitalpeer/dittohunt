#!/usr/bin/python
#
# Ditto Hunt
#
# Copyright (c) 2017 Joshua Henderson <digitalpeer@digitalpeer.com>
#
# SPDX-License-Identifier: GPL-3.0

"""Ditto Hunt"""
import sys
import os
import subprocess
import codecs
from .qt import *
from .version import __version__
from .finddups import find_duplicates
from .dittohunt_rc import *

def checked_files(tree):
    """ Returns a list of checked file names. """

    checked = list()
    iterator = QT_QTreeWidgetItemIterator(tree)
    while iterator.value():
        item = iterator.value()
        if item.checkState(1) == QtCore.Qt.Checked:
            checked.append(item.text(0))
        iterator += 1
    return checked

def delete_move_file(files, movedir=None):
    """ Delete or move the specified files. """

    for f in files:
        QT_QApplication.processEvents()
        if movedir is None:
            os.remove(f)
        else:
            target = os.path.join(movedir, f)
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            os.rename(f, target)

def add_duplicates(tree, duplist, check_children=False):
    """ Add the list of duplicate files to the tree. """

    dup = sorted(duplist, reverse=True)

    # pick the first one to be the parent
    parent = QT_QTreeWidgetItem(tree)
    parent.setText(0, duplist[0])
    parent.setCheckState(1, QtCore.Qt.Unchecked)
    parent.setExpanded(True)

    # all the rest are children
    for dup in duplist[1:]:
        child = QT_QTreeWidgetItem(parent)
        child.setText(0, dup)
        if check_children:
            child.setCheckState(1, QtCore.Qt.Checked)
        else:
            child.setCheckState(1, QtCore.Qt.Unchecked)

class FindThread(QtCore.QThread):
    """ Thread to handle file searching so we don't block the main thread. """

    done = QtCore.pyqtSignal(list, name='done')

    def __init__(self, path):
        super(FindThread, self).__init__()
        self.path = path

    def run(self):
        dups = find_duplicates(self.path)
        self.done.emit(dups)

    def __del__(self):
        self.wait()

class MainWindow(QT_QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        load_ui_widget(os.path.join(os.path.dirname(__file__), 'dittohunt.ui'),
                       self)

        self.path = None
        self.progress_dialog = None
        self.thread = None

        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 90)

        self.tree.header().setStretchLastSection(False)
        self.tree.headerItem().setText(0, "Path")
        if USE_QT_PY == PYQT5:
            self.tree.header().setSectionResizeMode(0, QT_QHeaderView.Stretch)
        else:
            self.tree.header().setResizeMode(0, QT_QHeaderView.Stretch)
        self.tree.headerItem().setText(1, "Selected")
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.onOpenMenu)
        self.tree.itemSelectionChanged.connect(self.onItemSelected)

        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QT_QSizePolicy.Ignored,
                                      QT_QSizePolicy.Ignored)
        self.imageLabel.installEventFilter(self)

        self.actionOpen.triggered.connect(self.onOpen)
        self.actionQuit.triggered.connect(QT_QApplication.quit)
        self.actionSelectAll.triggered.connect(self.onSelectAll)
        self.actionSelectNone.triggered.connect(self.onSelectNone)
        self.actionAbout.triggered.connect(self.onAbout)
        self.actionAboutQt.triggered.connect(QT_QApplication.aboutQt)
        self.deleteButton.clicked.connect(self.onBtnDelete)
        self.deleteButton.setEnabled(False)

    def onOpenMenu(self, position):
        indexes = self.tree.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level == 0:
            menu = QT_QMenu()
            menu.addAction(QT_QAction("Open File", self,
                                      triggered=self.onOpenFile))
            menu.exec_(self.tree.viewport().mapToGlobal(position))

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.Resize and widget is self.imageLabel:
            self.onItemSelected()
            return True
        return QT_QMainWindow.eventFilter(self, widget, event)

    def hunt(self):
        self.imageLabel.clear()
        self.tree.clear()
        self.statusBar().showMessage("")

        self.progress_dialog = QT_QProgressDialog(self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Working")
        self.progress_dialog.setLabelText("Finding duplicate files...")
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.setValue(-1)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.thread = FindThread(self.path)
        self.thread.done.connect(self.done)
        self.thread.start()

    def onOpen(self):
        dialog = QT_QFileDialog(self)
        dialog.setWindowTitle('Open Directory')
        dialog.setFileMode(QT_QFileDialog.Directory)
        if dialog.exec_() == QT_QDialog.Accepted:
            self.path = dialog.selectedFiles()[0]
            self.hunt()

    def onSelectAll(self):
        iterator = QT_QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(1, QtCore.Qt.Checked)
            iterator += 1

    def onSelectNone(self):
        iterator = QT_QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(1, QtCore.Qt.Unchecked)
            iterator += 1

    def done(self, dups):
        for dup in dups:
            add_duplicates(self.tree, dup, self.actionAutoSelect.isChecked())
        self.statusBar().showMessage("Found {} files with at least one"
                                     " duplicate.".format(len(dups)))
        self.progress_dialog.hide()
        self.deleteButton.setEnabled(True)

    def onBtnDelete(self):
        msg = "Are you sure you want to permanently delete all selected files?"
        reply = QT_QMessageBox.question(self, 'Delete Files',
                                        msg,
                                        QT_QMessageBox.Yes,
                                        QT_QMessageBox.No)

        if reply == QT_QMessageBox.Yes:
            delete_move_file(checked_files(self.tree))
            self.hunt()

    def onOpenFile(self):
        selected = self.tree.selectedItems()
        if selected:
            path = selected[0].text(0)
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path) # pylint: disable=no-member
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))

    def onItemSelected(self):
        selected = self.tree.selectedItems()
        if selected:
            image = QtGui.QImage(selected[0].text(0))
            if image.isNull():
                self.imageLabel.clear()
                return
            pixmap = QtGui.QPixmap.fromImage(image)
            width = min(pixmap.width(), self.imageLabel.width())
            height = min(pixmap.height(), self.imageLabel.height())
            self.imageLabel.setPixmap(pixmap.scaled(width, height,
                                                    QtCore.Qt.KeepAspectRatio))

    def onAbout(self):
        """About menu clicked."""
        msg = QT_QMessageBox(self)
        image = QtGui.QImage(":/icons/32x32/dittohunt.png")
        pixmap = QtGui.QPixmap(image).scaledToHeight(32,
                                                     QtCore.Qt.SmoothTransformation)
        msg.setIconPixmap(pixmap)
        msg.setInformativeText("Copyright (c) 2017 Joshua Henderson")
        msg.setWindowTitle("Ditto Hunt " + __version__)
        with codecs.open(os.path.join(os.path.dirname(__file__),'LICENSE.txt'), encoding='utf-8') as f:
            msg.setDetailedText(f.read())
        msg.setText(
            "<p><b>Ditto Hunt</b> is a duplicate file finder that quickly finds"
            " duplicate files recursively under a folder and allows you to"
            " preview and then select which versions should be deleted or moved"
            " to another folder.  It does not use filenames for comparison,"
            " and instead does a binary comparison of all files.</p>"
            "<p>This utility is handy, for example, if you have a bunch of"
            " images and want to find and get rid of duplicate images.</p>")

        msg.setStandardButtons(QT_QMessageBox.Ok)
        msg.exec_()


def main():
    """Create main app and window."""
    app = QT_QApplication(sys.argv)
    app.setApplicationName("Ditto Hunt")
    win = MainWindow(None)
    win.setWindowTitle("Ditto Hunt " + __version__)
    win.showMaximized()

    if len(sys.argv) >= 2:
        win.path = sys.argv[1]
        win.hunt()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
