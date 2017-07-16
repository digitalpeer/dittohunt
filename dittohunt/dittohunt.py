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
from collections import defaultdict
import shutil
from .qt import *
from .version import __version__
from .finddups import find_duplicates
from .dittohunt_rc import *

def checked_files(tree):
    """ Returns a list of checked file names. """

    checked = list()
    iterator = QTreeWidgetItemIterator(tree)
    while iterator.value():
        item = iterator.value()
        if item.checkState(1) == Qt.Checked:
            checked.append(item.text(0))
        iterator += 1
    return checked

def delete_move_file(files, movedir=None):
    """ Delete or move the specified files. """

    for f in files:
        QApplication.processEvents()
        if movedir is None:
            os.remove(f)
        else:
            # special handling of drive, and also the fact that os.path.join
            # won't join an absolute path
            drive, path = os.path.splitdrive(os.path.abspath(f))
            target = os.path.join(movedir, path.lstrip(os.sep))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            shutil.move(f, target)

class FindThread(QThread):
    """ Thread to handle file searching so we don't block the main thread. """

    done = QtCore.pyqtSignal(list, str, name='done')

    def __init__(self, parent, path):
        super(FindThread, self).__init__(parent)
        self.path = path

    def run(self):
        errorstr = None
        dups = []
        try:
            dups = find_duplicates(self.path)
        except Exception as e:
            errorstr = str(e)
        self.done.emit(dups, errorstr)

    def __del__(self):
        self.wait()

class MainWindow(QMainWindow):
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
            self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        else:
            self.tree.header().setResizeMode(0, QHeaderView.Stretch)
        self.tree.headerItem().setText(1, "Selected")
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.onOpenMenu)
        self.tree.itemSelectionChanged.connect(self.onItemSelected)

        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored,
                                      QSizePolicy.Ignored)
        self.imageLabel.installEventFilter(self)
        self.imageLabel.setText("PREVIEW")
        self.imageLabel.setStyleSheet('color: lightgrey')

        self.actionOpen.triggered.connect(self.onOpen)
        self.actionQuit.triggered.connect(QApplication.quit)
        self.actionSelectAll.triggered.connect(self.onSelectAll)
        self.actionSelectNone.triggered.connect(self.onSelectNone)
        self.actionExpandAll.triggered.connect(self.onExpandAll)
        self.actionCollapseAll.triggered.connect(self.onCollapseAll)
        self.actionAbout.triggered.connect(self.onAbout)
        self.actionAboutQt.triggered.connect(QApplication.aboutQt)
        self.deleteButton.clicked.connect(self.onBtnDelete)
        self.deleteButton.setEnabled(False)
        self.moveButton.clicked.connect(self.onBtnMove)
        self.moveButton.setEnabled(False)

        self.actionAutoSelectOld.setEnabled(False)
        self.actionAutoSelectNew.setEnabled(False)

        group = QActionGroup(self)
        group.addAction(self.actionAutoSelectNone)
        group.addAction(self.actionAutoSelect)
        group.addAction(self.actionAutoSelectOld)
        group.addAction(self.actionAutoSelectNew)

    def onOpenMenu(self, position):
        indexes = self.tree.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level == 0 or level == 1:
            menu = QMenu()
            menu.addAction(QAction("Open File", self,
                                      triggered=self.onOpenFile))
            menu.exec_(self.tree.viewport().mapToGlobal(position))

    def eventFilter(self, widget, event):
        if event.type() == QEvent.Resize and widget is self.imageLabel:
            self.onItemSelected()
            return True
        return QMainWindow.eventFilter(self, widget, event)

    def hunt(self):
        self.imageLabel.clear()
        self.imageLabel.setText("PREVIEW")
        self.tree.clear()
        self.statusBar().showMessage("")

        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Working")
        self.progress_dialog.setLabelText("Finding duplicate files...")
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.setValue(-1)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.thread = FindThread(self, self.path)
        self.thread.done.connect(self.onDone)
        self.thread.start()

    def onOpen(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Open Directory")
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_() == QDialog.Accepted:
            self.path = dialog.selectedFiles()[0]
            self.hunt()

    def onSelectAll(self):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(1, Qt.Checked)
            iterator += 1

    def onSelectNone(self):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setCheckState(1, Qt.Unchecked)
            iterator += 1

    def onExpandAll(self):
        iterator = QTreeWidgetItemIterator(self.tree,
                                           QTreeWidgetItemIterator.HasChildren)
        while iterator.value():
            item = iterator.value()
            item.setExpanded(True)
            iterator += 1

    def onCollapseAll(self):
        iterator = QTreeWidgetItemIterator(self.tree,
                                           QTreeWidgetItemIterator.HasChildren)
        while iterator.value():
            item = iterator.value()
            item.setExpanded(False)
            iterator += 1

    def onDone(self, dups, errorstr):
        if errorstr:
            msg = "An unhandled exception occurred trying to search files."
            errorbox = QMessageBox(self)
            errorbox.setText(msg + "\n\n" + errorstr)
            errorbox.setWindowTitle("Error")
            errorbox.exec_()
            self.path = None
        else:
            for dup in dups:
                self.addDuplicates(dup)

            self.statusBar().showMessage("Found {} files with at least one"
                                         " duplicate.".format(len(dups)))
            self.deleteButton.setEnabled(True)
            self.moveButton.setEnabled(True)

        self.progress_dialog.hide()

    def onBtnDelete(self):
        notice = "Are you sure you want to permanently delete all selected files?"
        reply = QMessageBox.question(self, 'Delete Files',
                                     notice,
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_move_file(checked_files(self.tree))
            self.hunt()

    def onBtnMove(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Target Directory")
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
            delete_move_file(checked_files(self.tree), path)
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
            image = QImage(selected[0].text(0))
            if image.isNull():
                self.imageLabel.clear()
                self.imageLabel.setText("PREVIEW")
                return
            pixmap = QPixmap.fromImage(image)
            width = min(pixmap.width(), self.imageLabel.width())
            height = min(pixmap.height(), self.imageLabel.height())
            self.imageLabel.setPixmap(pixmap.scaled(width, height,
                                                    Qt.KeepAspectRatio))

    def onAbout(self):
        """About menu clicked."""
        msg = QMessageBox(self)
        image = QImage(":/icons/32x32/dittohunt.png")
        pixmap = QPixmap(image).scaledToHeight(32,
                                               Qt.SmoothTransformation)
        msg.setIconPixmap(pixmap)
        msg.setInformativeText("Copyright (c) 2017 Joshua Henderson")
        msg.setWindowTitle("Ditto Hunt " + __version__)
        with codecs.open(os.path.join(os.path.dirname(__file__),'LICENSE.txt'),
                         encoding='utf-8') as f:
            msg.setDetailedText(f.read())
        msg.setText(
            "<p><b>Ditto Hunt</b> is a duplicate file finder that quickly finds"
            " duplicate files recursively under a folder and allows you to"
            " preview and then select which versions should be deleted or moved"
            " to another folder.  It does not use filenames for comparison,"
            " and instead does a binary comparison of all files.</p>"
            "<p>This utility is handy, for example, if you have a bunch of"
            " images and want to find and get rid of duplicate images.</p>")

        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def addDuplicates(self, duplist):
        """ Add the list of duplicate files to the tree. """

        duplist = sorted(duplist,
                         reverse=self.actionSortDupsReverse.isChecked())

        # pick the first one to be the parent
        parent = QTreeWidgetItem(self.tree)
        parent.setText(0, duplist[0])
        parent.setCheckState(1, Qt.Unchecked)
        parent.setExpanded(True)

        # all the rest are children
        for dup in duplist[1:]:
            child = QTreeWidgetItem(parent)
            child.setText(0, dup)
            if self.actionAutoSelect.isChecked():
                child.setCheckState(1, Qt.Checked)
            else:
                child.setCheckState(1, Qt.Unchecked)

def main():
    """Create main app and window."""
    app = QApplication(sys.argv)
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
