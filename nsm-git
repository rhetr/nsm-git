#!/usr/bin/env python

import liblo, sys, os, time, datetime, subprocess, signal, shutil
import git

class NSMGit(liblo.Server):
    def __init__(self):
        liblo.Server.__init__(self)
        self.add_method("/reply", 'ssss', self.handshake_callback)
        self.add_method("/nsm/client/open", 'sss', self.open_callback)
        self.add_method("/nsm/client/save", None, self.save_callback)
        self.add_method("/nsm/client/show_optional_gui", None, self.show_gui_callback)
        self.add_method("/nsm/client/hide_optional_gui", None, self.hide_gui_callback)
        self.add_method("/reply", 'ss', self.server_save_callback)
        self.add_method("/error", 'sis', self.error_callback)
        self.add_method(None, None, self.fallback)

        self.session_dir = None
        self.server_saved = False
        self.exit = False
        self.app = None

        self.NSM_URL = os.getenv('NSM_URL')
        os.environ['GIT_AUTHOR_NAME'] = 'nsm-git'
        os.environ['GIT_AUTHOR_EMAIL'] = 'noreply@nsm-git'

        if not self.NSM_URL:
           sys.exit()

        self.handshake()

    # ---------------------------------------------------------------------
    # callbacks

    def handshake_callback(self, path, args):
        print 'received handshake'

    def open_callback(self, path, args):
        self.session_dir, self.display_name, self.client_id = args
        self.session_dir = os.path.split(self.session_dir)[0]
        print "session dir is {}".format(self.session_dir)
        print 'attempting to commit'
        self.save()
        message = liblo.Message('/reply', "/nsm/client/open", 'done')
        liblo.send(self.NSM_URL, message)

    def save_callback(self, path, args):
        s_c = datetime.datetime.now().second
        self.server_saved = False
        message = liblo.Message('/reply', "/nsm/client/save", 'nsm-git is waiting to save')
        liblo.send(self.NSM_URL, message)
        print 'save called. waiting...'
        while not self.server_saved:
            s_d = datetime.datetime.now().second
            if s_d - s_c > 3:
                message = liblo.Message("/nsm/client/message", 1, "nsm-git has waited long enough")
                liblo.send(self.NSM_URL, message)
                print 'nsm-git has waited long enough. saving...'
                break
            self.recv(50)

        saved = self.save()
        msg = "nsm-git has committed" if saved else "nothing for nsm-git to commit"
        message = liblo.Message("/nsm/client/message", 1, msg)
        liblo.send(self.NSM_URL, message)

    def server_save_callback(self, path, args):
        if args[0] == "/nsm/server/save" and args[1] == "Saved.":
            print 'server callback received.'
            self.server_saved = True

    def error_callback(self, path, args):
        if args[1] == -6:
            print 'no session open'
            self.exit = True

    def show_gui_callback(self, path, args):
        if self.app:
            if self.app.poll() == 0:
                self.app = None
            else:
                print 'gui already shown'

        if not self.app:
            self.app = subprocess.Popen([os.path.join(self.executable_dir, 'nsm-git-ui'), self.session_dir],
                                        stdout=subprocess.PIPE,
                                        preexec_fn=os.setsid)
            print 'showing gui', self.app.pid

    def hide_gui_callback(self, path, args):
        print 'hiding gui'
        os.killpg(self.app.pid, signal.SIGTERM)
        self.app = None


    def fallback(self, path, args, types, src):
        print "got unknown message '%s' from '%s'" % (path, src.url)
        for a, t in zip(args, types):
            print "argument of type '%s': %s" % (t, a)

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
        
    def init_repo(self):
        '''
        opens the existing git repository or creates a new one
        '''
        try:
            self.repo = git.Repo(self.session_dir)
            print 'opened git repo'
        except git.exc.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.session_dir)
            print 'created git repo'

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
                    print 'alert {} removed from session'.format(entry)
                    entries_to_remove.append(entry)
                    if os.path.isdir(os.path.join(self.session_dir, entry)):
                        shutil.rmtree(os.path.join(self.session_dir, entry))
        if entries_to_remove:
            try:
                self.repo.index.remove(entries_to_remove, working_tree=True, force=True, r=True)
                return entries_to_remove
            except git.exc.GitCommandError, err:
                print str(err)
                return False
        else:
            return False

    def save(self):
        removed = untracked = updated = False
        self.init_repo()

        if not os.path.isfile(os.path.join(self.session_dir,'.gitignore')):
            with open(os.path.join(self.session_dir,'.gitignore'), 'wb') as gitignore:
                gitignore.write('*.swp\n*.lock\n*autosave*\n.*')

        removed = self.remove_removed()

        if self.repo.is_dirty(untracked_files=True):
            print 'adding untracked files'
            untracked = self.repo.untracked_files
            self.repo.index.add(self.repo.untracked_files)

        if self.repo.git.diff(None):
            print 'adding updated files'
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
                print 'committed'
                return True
            except git.exc.GitCommandError, err:
                print str(err)
                return False
        else:
            print 'nothing to be done'
            return False


try:
    nsm_git = NSMGit()
except liblo.ServerError, err:
    print str(err)
    sys.exit()

while True:
    nsm_git.recv(100)
