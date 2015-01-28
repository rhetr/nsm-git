#!/usr/bin/env python
# filename: nsm-git-ui

import os
import time, datetime
from PyQt4 import QtGui, QtCore
import git
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import cStringIO as SIO


class Commit(QtGui.QListWidgetItem):
    def __init__(self, commit):
        QtGui.QListWidgetItem.__init__(self)

        self.commit = commit
        date = datetime.datetime.strptime(time.ctime(self.commit.committed_date), '%a %b %d %H:%M:%S %Y')
        date = date.strftime('%a %b %d %I:%M %p %Y')
        self.setText('{}...\t{}'.format(str(self.commit)[:7], date))


class CommitList(QtGui.QListWidget):
    def __init__(self, repo):
        QtGui.QListWidget.__init__(self)
        self.repo = repo
        commits = list(self.repo.iter_commits())
        for c in commits:
            self.addItem(Commit(c))


class MainWindow(QtGui.QWidget):
    def __init__(self, repo):
        QtGui.QWidget.__init__(self)
        self.list = CommitList(repo)
        self.tabs = QtGui.QTabWidget()
        self.curview = None

        self.list.itemActivated.connect(self.callback)

        self.hBox = QtGui.QHBoxLayout()
        self.hBox.addWidget(self.list)
        self.hBox.addWidget(self.tabs)
        self.setLayout(self.hBox)


    def callback(self, commit_item):
        if not self.curview == commit_item:
            self.curview = commit_item
            self.tabs.clear()
            commit = commit_item.commit
            html_escape_table = {
                    '"': "&quot;",
                    "'": "&apos;"
                    }
            try:
                diffs = commit.parents[0].diff(commit, create_patch=True)
                for diff in diffs:
                    lines = [escape(x, html_escape_table) for x in diff.diff.split('\n')[2:]]
                    for l in range(len(lines)):
                        if len(lines[l]) > 0:
                            if lines[l][0] == '-':
                                lines[l] = '<div style="color:red;">' + lines[l][1:] + '</div>'
                            elif lines[l][0] == '+':
                                lines[l] = '<div style="color:green;">' + lines[l][1:] + '</div>'
                            else:
                                lines[l] = '<div>' + lines[l] + '</div>'
                    text = ''.join(lines)
                    viewer = QtGui.QTextEdit()
                    viewer.setReadOnly(True)
                    viewer.setHtml(text)
                    self.tabs.addTab(viewer, diff.a_blob.name)
            except IndexError:
                for item in commit.tree:
                    if item.name != '.gitignore':
                        file_contents = SIO.StringIO()
                        item.stream_data(file_contents)
                        viewer = QtGui.QTextEdit()
                        viewer.setReadOnly(True)
                        viewer.setHtml(file_contents.getvalue())
                        file_contents.close()
                        self.tabs.addTab(viewer, item.name)


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    main = MainWindow(git.Repo(os.getenv('HOME')+'/tmp/testgit'))
    main.show()
    sys.exit(app.exec_())
