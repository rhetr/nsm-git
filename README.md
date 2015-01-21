nsm-git
=======

makes git a little easier to use with [non session manager](http://non.tuxfamily.org/nsm/) sessions. creates a git repository in the current session and commits all untracked and unstaged files to a git repository whenever save is pressed.

This program is meant to be executed within NSM.

Requirements
------------
* git
* NSM or something that uses NSM API v1.2
* [GitPython](https://github.com/gitpython-developers/GitPython)
* liblo
* pyliblo

TODO
----
* ensure this program actually works
* make a cool gui that shows more descriptive changes
* use submodule instead of gitpython?
