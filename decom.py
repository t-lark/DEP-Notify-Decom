#!/usr/bin/python

"""
This script will use DEP Notify to systematically remove all apps based on the tags you set in the
tagging script tied to this project

"""

# import modules
from Foundation import NSMetadataQuery, NSPredicate, NSRunLoop, NSDate
import sys
from SystemConfiguration import SCDynamicStoreCopyConsoleUser
import logging
import subprocess
import shutil
import os


# global variables and parameters
# the tag which you used to validate you installed it
SEARCHTAG = sys.argv[4]
# removal method tag
REMOVAL = sys.argv[5]
# path to your copy of DEP Notify
DNPATH = sys.argv[6]
# path to your custom branding for DEP Notify
DNBRAND = sys.argv[7]
# global logger info for this workflow, can set path to something else
LOGFILE = '/tmp/decommission.log'
# basic logging config for the logger
logging.basicConfig(filename='%s' % LOGFILE, format='%(asctime)s %(message)s',level=logging.DEBUG)
# log for DEP Notify
DEPLOG = '/tmp/depnotify.log'
# local user info to run process as user
USER, UID, GID = SCDynamicStoreCopyConsoleUser(None, None, None)


# start functions


def create_logs():
    """create log file for this specific script"""
    if not os.path.exists(LOGFILE):
        open(LOGFILE, 'w')
        LOGFILE.close()
        logging.info('Creating log file...')


def write_to_dnlog(text):
    """function to modify the DEP log and send it commands"""
    depnotify = "/private/var/tmp/depnotify.log"
    with open(depnotify, "a+") as log:
        log.write(text + "\n")


def get_apps(tag, removal):
    """use spotlight to find apps by custom tag"""
    # main dictionary 
    removals = {}
    # set NSMetaDatQuery predicate by your custom tag with value of true
    predicate = "%s = 'true'" % tag
    # build and execute the spotlight query
    query = NSMetadataQuery.alloc().init()
    query.setPredicate_(NSPredicate.predicateWithFormat_(predicate))
    query.setSearchScopes_(['/Applications'])
    query.startQuery()
    start_time = 0
    max_time = 20
    while query.isGathering() and start_time <= max_time:
        start_time += 0.3
        NSRunLoop.currentRunLoop(
        ).runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.3))
    query.stopQuery()
    # iterate through the results to grab spotlight attributes
    for item in query.results():
        app = item.valueForAttribute_('kMDItemFSName')
        path = item.valueForAttribute_('kMDItemPath')
        customtag = item.valueForAttribute_(removal)
        if customtag:
            # build nested dictionary of tagged apps and attribute values
            removals[app] = {}
            removals[app]['path'] = path
            removals[app]['method'] = customtag

    return removals


def start_dep_notify():
    """function to launch DEPNotify as end user"""
    # launchctl does not like integer data types, so you must convert the UID to a string
    # build unix command in list
    cmd = ['launchctl', 'asuser', str(UID), 'open', '-a', DNPATH]
    # run the command
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    # test output, force non zero exit status if fails
    if proc.returncode != 0:
        logging.error('DEPNotify failed to launch')
        sys.exit(1)
    else:
        return True


def remove_apps(appdict):
    """parse removal items and remove items based on custom tags from Spotlight"""
    # start dep notify log status
    write_to_dnlog('Status: Installing software...')
    # grab number of items to remove to dynamically build progress bar
    number_of_items = len(appdict.keys())
    # set number of steps to DEP Notify
    write_to_dnlog('Command: DeterminateManual: %s' % number_of_items)
    # iterate through the dictionary from the spotlight results
    for k, v in appdict.iteritems():
        # get the values from our dictionary
        name = k
        path = appdict[k]['path']
        removal = appdict[k]['method']
        # check if we are manually deleting the item
        if removal == 'delete':
            write_to_dnlog('Status: Removing %s' % name)
            write_to_dnlog('Command: DeterminateManualStep:')
            logging.info('removing %s...' % name)
            shutil.rmtree(path)
        # test if the removal is a custom workflow, use your jamf policy trigger
        if removal != 'delete':
            # if you have a policy that removes it, i.e. custom uninstaller
            cmd = ['jamf', 'policy', '-event', str(removal)]
            write_to_dnlog('Status: Removing %s' % name)
            write_to_dnlog('Command: DeterminateManualStep:')
            logging.info('removing %s...' % name)
            # call the process
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, errors = proc.communicate()
            if proc.returncode != 0:
                error_msg = '%s code %s' % (errors.strip(), proc.returncode)
                logging.error('jamf binary failed to install %s, %s', removal, error_msg)
                write_to_dnlog('Status: %s policy failed, please see logs...' % removal)
            elif proc.returncode == 0:
                logging.info('jamf policy %s returned successful..' % removal)
                write_to_dnlog('Status: %s was successfully installed...' % name)
    write_to_dnlog('Command: DeterminateOff:')
    write_to_dnlog('Command: DeterminateOffReset:')


def remove_fv2():
    """if we are decommissioning it, we need to disable FV2"""
    # this needs to be the last step and the device needs to be plugged in
    # please test this in your env and adjust
    # start DEPNotify log
    write_to_dnlog('Status: Disabling FileVault 2...')
    write_to_dnlog('Command: DeterminateManual: 1')
    # build FV2 disable command and execute
    cmd = ['fdesetup', 'disable']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        logging.error('FV2 failed to disable: %s' % err)
    write_to_dnlog('Command: DeterminateOff:')
    write_to_dnlog('Command: DeterminateOffReset:')


def remove_jamf():
    """last we remove jamf, note this does not remove the device record, only the client agent/binary"""
    write_to_dnlog('Status: Removing Device from Program...')
    write_to_dnlog('Command: DeterminateManual: 1')
    cmd = ['jamf', 'removeframework']
    subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.info('removing jamf agents...fin')
    write_to_dnlog('Command: DeterminateOff:')
    write_to_dnlog('Command: DeterminateOffReset:')


def main():
    """main to run it all"""
    # create the log file
    create_logs()
    # log start info
    logging.info('Starting new decommission flow...')
    write_to_dnlog('Command: Image: %s' % DNBRAND)
    write_to_dnlog('Command: MainTitle: Decommission Process')
    write_to_dnlog('Command: MainText: Please wait while we decommission your device.  '
                   'This should only take a few minutes and will remove items from your device.  '
                   'If you need assistance please contact IT at email@acme.com')
    write_to_dnlog('Status: Preparing your system...')
    # launch DEP Notify as current user
    start_dep_notify()
    # get the custom tagged apps for removal
    apps = get_apps(SEARCHTAG, REMOVAL)
    # remove apps
    remove_apps(apps)
    # remove jamf
    remove_jamf()
    # remove FV2
    remove_fv2()
    # write final DEP Notify commands
    write_to_dnlog('Status: Decom is complete, exiting...')
    write_to_dnlog('Command: Quit')

if __name__ == '__main__':
    """call the main policy"""
    main()
