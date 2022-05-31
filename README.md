# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and others.

## Install
Installation is just 2 easy steps (4 if you don't have a Mac and Apple ID)
0. Generate an Apple ID, and instal the Catalina Pre-installed docker image from https://github.com/sickcodes/Docker-OSX#run-catalina-pre-installed-
1. Download the latest release of `cook` from https://github.com/n3d1117/cook, and follow the install instructions from there. Run like this:
```
./cook anisette_server --secret anisette
```
2. Add your public keys to `request_reports.sh` at the top, and run (only internal tools are used, no dependencies)

