#!/usr/bin/env python2

import liblo, sys, os, time, datetime, subprocess, signal, shutil
import git
from PyQt4 import QtGui, QtCore

GUI_HIDDEN = liblo.Message('/nsm/client/gui_is_hidden')
GUI_SHOWN = liblo.Message('/nsm/client/gui_is_shown')

class NSMGitServerThread(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    def __init__(self):
        super(NSMGitServerThread, self).__init__()
        self.server = None

    def run(self):
        self.server = NSMGitServer()
        self.timer = QtCore.QTimer()
        self.timer.start(100)
        self.timer.timeout.connect(self.server.recv)

class UISignal(QtCore.QObject):
    visible = QtCore.pyqtSignal(bool)

class NSMGitServer(liblo.Server):
    def __init__(self):
        super(NSMGitServer, self).__init__()
        self.add_method("/reply", 'ssss', self.handshake_callback)
        self.add_method("/nsm/client/open", 'sss', self.open_callback)
        self.add_method("/nsm/client/save", None, self.save_callback)
        self.add_method("/nsm-git/save", None, self.popup_save_callback)

        self.ui_signal = UISignal()
        self.ui_visible = self.ui_signal.visible
        self.add_method("/nsm/client/show_optional_gui", None, self.show_gui_callback)
        self.add_method("/nsm/client/hide_optional_gui", None, self.hide_gui_callback)
        self.add_method("/reply", 'ss', self.server_save_callback)
        self.add_method("/error", 'sis', self.error_callback)
        self.add_method(None, None, self.fallback)

        self.session_dir = None
        self.capabilities = None
        self.server_saved = False
        self.exit = False
        self.gui = None
        self.log_file = None

        self.NSM_URL = os.getenv('NSM_URL')
        os.environ['GIT_AUTHOR_NAME'] = 'nsm-git'
        os.environ['GIT_AUTHOR_EMAIL'] = 'noreply@nsm-git'

        if not self.NSM_URL:
            print("NSM_URL isn't set")

        self.handshake()

        #self.timer = QtCore.QTimer()
        #self.timer.start(100)
        #self.timer.timeout.connect(self.recv)

    # ---------------------------------------------------------------------
    # callbacks
    
    def handshake_callback(self, path, args):
        assert(args[0] == "/nsm/server/announce")
        self.capabilities = args[3]
        message = "{} says: {}".format(args[2], args[1])
        self.log_write('received handshake')
        self.log_write(message)
        liblo.send(self.NSM_URL, GUI_HIDDEN)

    def open_callback(self, path, args):
        self.session_dir, self.display_name, self.client_id = args
        self.session_dir = os.path.split(self.session_dir)[0]
        self.begin_logging()
        self.log_write("session dir is {}".format(self.session_dir))
        self.log_write('attempting to commit... ', False)
        self.save()
        message = liblo.Message('/reply', "/nsm/client/open", 'done')
        liblo.send(self.NSM_URL, message)

    def save_callback(self, path, args):
        s_c = datetime.datetime.now().second
        self.server_saved = False
        message = liblo.Message('/reply', "/nsm/client/save", 'nsm-git is waiting to save')
        liblo.send(self.NSM_URL, message)
        self.log_write('save called. waiting...', False)
        while not self.server_saved:
            s_d = datetime.datetime.now().second
            if s_d - s_c > 3:
                message = liblo.Message("/nsm/client/message", 1, "nsm-git has waited long enough")
                liblo.send(self.NSM_URL, message)
                self.log_write('nsm-git has waited long enough. saving...')
                break
            self.recv(50)

        saved = self.save()
        msg = "nsm-git has committed" if saved else "nothing for nsm-git to commit"
        message = liblo.Message("/nsm/client/message", 1, msg)
        liblo.send(self.NSM_URL, message)

    def popup_save_callback(self, path, args):
        # will open a popup dialog to write a save message
        pass

    def server_save_callback(self, path, args):
        if args[0] == "/nsm/server/save" and args[1] == "Saved.":
            self.log_write('server callback received.')
            self.server_saved = True

    def error_callback(self, path, args):
        if args[1] == -6:
            self.log_write('no session open')
            self.exit = True

    def show_gui_callback(self, path, args):
        self.ui_visible.emit(True)
        liblo.send(GUI_SHOWN)

    def hide_gui_callback(self, path, args):
        self.ui_visible.emit(False)
        liblo.send(GUI_HIDDEN)

    def fallback(self, path, args, types, src):
        self.log_write("got unknown message '{}' from '{}'".format(path, src.url))
        for a, t in zip(args, types):
            self.log_write("argument of type '{}': {}".format(t, a))

    # ---------------------------------------------------------------------
    # internal methods

    def handshake(self):
        application_name = "nsm-git"
        capabilities = ":message:optional-gui:"
        executable_name = os.path.realpath(__file__)
        self.executable_dir = os.path.dirname(executable_name)
        executable_name = "nsm-git" # this leads to mostly correct behaviour, I don't know how to find the actual 'correct' value though
        pid = os.getpid()
        api_version_major = 1
        api_version_minor = 2

        message = liblo.Message("/nsm/server/announce", application_name, capabilities, executable_name, api_version_major, api_version_minor, pid)
        liblo.send(self.NSM_URL, message)

        while not self.session_dir:
            self.recv()
            if self.exit:
                sys.exit()


    # ---------------------------------------------------------------------
    # save methods

    def begin_logging(self):
        self.log_file = os.path.join(self.session_dir, 'nsm-git.log')
        self.log_write('==================================')
        self.log_write('begin log')
        self.log_write('server capabilities: {}'.format(self.capabilities))

    def log_write(self, text, newline=True):
        '''
        outputs to nsm-git.log
        '''
        if self.log_file:
            text = str(text) + '\n' if newline else str(text)
            with open(self.log_file, 'a') as log:
                log.write(text)
        
    def init_repo(self):
        '''
        opens the existing git repository or creates a new one
        '''
        try:
            self.repo = git.Repo(self.session_dir)
            self.log_write('opened git repo... ', False)
        except git.exc.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.session_dir)
            self.log_write('created git repo... ', False)

    def remove_removed(self):
        '''
        removes a file if it is removed from session.nsm. currently only works with Hydrogen and Carla files
        '''
        with open(os.path.join(self.session_dir, 'session.nsm'), 'rb') as session_file:
            active_session = session_file.read()
        session_contents = os.listdir(self.session_dir)
        entries_to_remove = []
        for entry in session_contents:
            if any(app in entry for app in ['Hydrogen','Carla', 'Non-Mixer']):
                entry_id = entry.split('.')[1]
                if not entry_id in active_session:
                    self.log_write('alert {} removed from session'.format(entry))
                    entries_to_remove.append(entry)
                    if os.path.isdir(os.path.join(self.session_dir, entry)):
                        shutil.rmtree(os.path.join(self.session_dir, entry))
        if entries_to_remove:
            try:
                self.repo.index.remove(entries_to_remove, working_tree=True, force=True, r=True)
                return entries_to_remove
            except git.exc.GitCommandError, err:
                self.log_write(str(err))
                return False
        else:
            return False

    def save_port_list(self):
        #ports = subprocess.check_output("jack_lsp", shell = True)
        #with open(os.path.join(self.session_dir,'jack_lsp'), 'w') as jack_lsp:
        #    jack_lsp.write(ports)

    def save(self):
        removed = untracked = updated = False
        self.save_port_list()
        self.init_repo()

        if not os.path.isfile(os.path.join(self.session_dir,'.gitignore')):
            with open(os.path.join(self.session_dir,'.gitignore'), 'wb') as gitignore:
                gitignore.write('*.swp\n*.lock\n*autosave*\n.*\nnsm-git.log')

        removed = self.remove_removed()

        if self.repo.is_dirty(untracked_files=True):
            self.log_write('adding untracked files')
            untracked = self.repo.untracked_files
            self.repo.index.add(self.repo.untracked_files)

        if self.repo.git.diff(None):
            self.log_write('adding updated files')
            updated = [diff.a_blob.path for diff in self.repo.index.diff(None)]
            self.repo.index.add(updated)

        if any((removed, untracked, updated)):
            message = 'nsm-git'
            if removed:
                message += "\n\tremoved {}".format('\n\t        '.join(removed))
            if untracked:
                message += "\n\tadded {}".format('\n\t      '.join(untracked))
            if updated:
                message += "\n\tupdated {}".format('\n\t        '.join(updated))

            try:
                self.repo.index.commit(message)
                self.log_write('committed.')
                return True
            except git.exc.GitCommandError, err:
                self.log_write(str(err))
                return False
        else:
            self.log_write('nothing to be done.')
            return False

