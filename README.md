# DEP-Notify-Decom
Spotlight tagging code base to help decommission BYOD systems

## Introduction

After having a few beers with a friend and discussing the ins and outs of BYOD programs, I had an idea to use Spotlight to tag and remove specific applications when a BYOD system leaves your program.

This is a static code base that will tag applications upon install (or later on) with custom Spotlight object attributes that you can later use to remove Orginizational or Licensed Software, when a BYOD system is decommissioned from your management program.  This is a proof of concept repo, and was a side project of mine.  No pull requests, as I don't have any need to decommission BYOD systems as my Org does not allow BYOD laptops.  Please feel free to borrow the code or fork all you want.

## Usage

use the `app_tagger.py` script to tag apps, ideally as an `after script` in a policy to tag the app you just installed.  Example usage:

```
# note I passed none 3 times because jamf reserves the first 3 parameters when ran locally

python app_tagger.py none none none /Applications/Microsoft\ Word.app/  kMDOrgInstalled kMDRemoval delete
```

In the above code I have tagged Microsoft Word with `kMDOrgInstalled` which will set this value to `true` by default in my code, and I have chosen to create a custom tag of `kMDRemoval` as the tag I will use to search for apps via Spotlight to remove them when a device runs the decommission workflow.  The last value, `delete` tells the code that I can just delete it from the file system. If your app requires an uninstall policy, use the custom trigger for that policy instead of "delete", i.e. `uninstall_myapp`

To test this you can just use `mdfind` to see what apps you have tagged:

```
mdfind -onlyin /Applications/ -name "kMDOrgInstalled = true"
/Applications/Microsoft PowerPoint.app
/Applications/Microsoft Excel.app
/Applications/Microsoft Word.app
```

In the above output you can see I have a few Office 365 Apps tagged, so the `decom.py` code can find them and remove them when the decommission workflow is executed.  

To configure the `decom.py` script you will need to fill in the positional parameters with your DEP Notify information, your custom branding, and modify any log paths if you wish the code to not log to `/tmp` for example.

This was a side project I put together as a fun idea for me to learn more about Spotlight in Python and the Objective C bridge.  Since we do not allow BYOD systems, I won't be putting too much investment in this, but I hope some of you find this useful.

Thanks!
