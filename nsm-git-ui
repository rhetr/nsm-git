#!/usr/bin/env python
# filename: nsm-git-ui

import os
import time, datetime
from PyQt4 import QtGui, QtCore
import git
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import cStringIO as SIO

html_escape_table = {
        '"': "&quot;",
        "'": "&apos;",
        " ": "&nbsp;"
        }

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
        self.curr_commit = None
        self.curr_diff = None

        self.list = CommitList(git.Repo(repo))
        #self.commit_notes = QtGui.QPlainTextEdit()
        self.file_list = QtGui.QListWidget()

        self.list.setMaximumWidth(260)
        #self.commit_notes.setMaximumWidth(260)
        self.file_list.setMaximumWidth(260)

        self.viewer = QtGui.QTextEdit()
        self.viewer.setReadOnly(True)

        self.list.currentRowChanged.connect(self.showCommit)
        self.file_list.currentRowChanged.connect(self.showFile)

        self.leftvBox = QtGui.QVBoxLayout()
        self.leftvBox.addWidget(QtGui.QLabel('commits'))
        self.leftvBox.addWidget(self.list)
        #self.leftvBox.addWidget(QtGui.QLabel('commit notes'))
        #self.leftvBox.addWidget(self.commit_notes)
        self.leftvBox.addWidget(QtGui.QLabel('changed files'))
        self.leftvBox.addWidget(self.file_list)

        self.rightvBox = QtGui.QVBoxLayout()
        self.rightvBox.addWidget(self.viewer)

        self.hBox = QtGui.QHBoxLayout()
        self.hBox.addLayout(self.leftvBox)
        self.hBox.addLayout(self.rightvBox)
        self.setLayout(self.hBox)
        self.list.setCurrentRow(0)


    def showCommit(self, commit_index):
        commit_item = self.list.item(commit_index)
        if self.curr_commit == commit_item:
            return

        self.curr_commit = commit_item
        self.file_list.clear()
        self.viewer.clear()
        self.diffs = []
        commit = commit_item.commit

        try:
            self.diffs = commit.parents[0].diff(commit, create_patch=True)
            for diff in self.diffs:
                status_color = (QtCore.Qt.green, QtCore.Qt.red, QtCore.Qt.cyan)
                if diff.new_file:
                    status = 0
                    blob = diff.b_blob
                elif diff.deleted_file:
                    status = 1
                    blob = diff.a_blob
                else:
                    status = 2
                    blob = diff.a_blob
                
                list_item = QtGui.QListWidgetItem(blob.path)
                list_item.setForeground(status_color[status])
                self.file_list.addItem(list_item)
            self.file_list.setCurrentRow(0)

        except IndexError:
            pass
            #for item in commit.tree:
            #    if item.name != '.gitignore':
            #        file_contents = SIO.StringIO()
            #        item.stream_data(file_contents)
            #        viewer = QtGui.QTextEdit()
            #        viewer.setReadOnly(True)
            #        viewer.setHtml(file_contents.getvalue())
            #        file_contents.close()
            #        self.tabs.addTab(viewer, item.path)



    def showFile(self, file_index):
        diff = self.diffs[file_index]
        format_lines = [escape(x, html_escape_table) for x in diff.diff.split('\n')[2:]]
        for l in range(len(format_lines)):
            if len(format_lines[l]) > 0:
                if format_lines[l][0] == '-':
                    format_lines[l] = '<div style="color:red;">' + format_lines[l][1:] + '</div>'
                elif format_lines[l][0] == '+':
                    format_lines[l] = '<div style="color:green;">' + format_lines[l][1:] + '</div>'
                else:
                    format_lines[l] = '<div>' + format_lines[l] + '</div>'
        text = ''.join(format_lines)
        self.viewer.setHtml(text)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    if len(sys.argv) > 1:
        print sys.argv[1]
        main = MainWindow(sys.argv[1])
        main.show()
        sys.exit(app.exec_())
