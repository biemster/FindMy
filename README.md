# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and others.

## Install
Installation requires XCode (for as long as I need to figure out how to use python ctypes on AOSKit), a Mac (real or virtual) and an Apple ID

0. Generate an Apple ID, and instal the Catalina Pre-installed docker image from https://github.com/sickcodes/Docker-OSX#run-catalina-pre-installed-, and login to iCloud using your AppleID
1. Clone and build https://github.com/biemster/AppleIDAuth (you will have to change the build phase copy of `AOSKit` to the directory you are running this script in)
2. Add your public keys to `request_reports.sh` at the top, and run (only internal tools are used, no dependencies)

