#!/usr/bin/python

"""
This script will tag your applications you install with meta data tags that can be later used via
Spotlight searches, to find apps or files that have been installed by your Organization.

This can later be used in a decommission or app removal workflow for things like BYOD systems, or if you want to only
remove licensed software from your Organization
"""

# import modules

import xattr
import sys
import os

# positional parameters

# this will be the path of what you are wanting to tag, example: /Applications/Firefox.app
TAGPATH = sys.argv[4]
# meta data tag, i.e. the name of the tag you want to use for searching for the apps you have installed
# examples:  InstalledByJamf, InstalledByCompany, AcmeApp, etc.
TAGNAME = sys.argv[5]
# name of the removal tag, i.e. RemovalMethod, Uninstall, etc
REMOVETAG = sys.argv[6]
# uninstall method, i.e. jamf policy manual event trigger, or just delete it, use delete if you want it to be deleted
REMOVAL = sys.argv[7]

# start functions

def tag_app(path, name, removetag, removal):
    """function that uses xattr to tag an app with custom attributes"""
    # check if the file exists, if not exit script
    if not os.path.exists(path):
        print('File %s does not exist' % path)
        sys.exit(1)
    # create instance of object to tag
    attr = xattr.xattr(path)
    # now set the tags
    # tag the fact that we installed it first, set value to 'true'
    spname = 'com.apple.metadata:' + name
    attr.set(spname, 'true')
    # set the name for the removal tag and the value
    spremovetag = 'com.apple.metadata:' + removetag
    attr.set(spremovetag, removal)


def main():
    """run the main"""
    tag_app(TAGPATH, TAGNAME, REMOVETAG, REMOVAL)


if __name__=='__main__':
    main()
