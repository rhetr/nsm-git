nsm-git
=======

nsm-git makes git a little easier to use with [non session manager](http://non.tuxfamily.org/nsm/) sessions. creates a git repository in the current session and commits all untracked and unstaged files to it whenever save is pressed. nsm-git also reads the session.nsm file and deletes any saved applications that are not listed in the session.

This program is meant to be executed within NSM.

Requirements
------------
* git and [GitPython](https://github.com/gitpython-developers/GitPython)
* liblo and pyliblo
* NSM or something that uses NSM API v1.2


USAGE
-----
run nsm-git within NSM. you can open the UI by pressing the GUI button in the non-session-manager user interface.

TODO/WISHLIST 
-------------
* create install script and configuration settings (don't know what the settings would at this point)
* differentiate between important versions and incremental updates (git tags?)
* include git manipulation features like checkout, revert, merge
	* reverting things live? unlikely
* delete stuff that isn't referenced in session.nsm
	* move media files to junk folder pending manual deletion
* add optional comments (possibly using git notes)
* convert diff information to musical information
	* use an xmldiff program instead of git-diff where appropriate
	* patching and session changes can be visualized on an patchbay canvas
* figure out what to do with audio files and other non-text-based data (git-annex?)

CURRENT ISSUES
--------------
* verify the commits/changed files view is actually correct
* folders act weird sometimes
* nsm-git doesn't load when a session is restored and I don't know why
