nsm-git
=======

nsm-git makes git a little easier to use with [non session manager](http://non.tuxfamily.org/nsm/) sessions. creates a git repository in the current session and commits all untracked and unstaged files to it whenever save is pressed. nsm-git also reads the session.nsm file and deletes any saved applications that are not in the session.

This program is meant to be executed within NSM.

Requirements
------------
* git and [GitPython](https://github.com/gitpython-developers/GitPython)
* liblo and pyliblo
* NSM or something that uses NSM API v1.2

TODO
----
* ensure this program actually works
* make a cool gui that shows more descriptive changes
