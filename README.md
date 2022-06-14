# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and @vtky and others.

## Install and Run
To install just clone this repo, to run a Mac (real or virtual) and an Apple ID are required

1. (Optional, if you don't have a MAC and/or Apple ID): Generate an Apple ID, and install the Catalina Pre-installed docker image from https://github.com/sickcodes/Docker-OSX#run-catalina-pre-installed-, and login to iCloud using your AppleID.
2. Generate keys using `generate_keys.py`.
3. Deploy your advertisement keys on devices supported by OpenHaystack. (Soon ESP32 firmware will be added to this repo, and after that Lenze 17H26 and 17H66 based tags.)
4. run `request_reports.py` in the same directory as your `.keys` files (only internal tools are used, no dependencies).

This is using the ancient urllib on python 2.7 that comes with Catalina, so it might need some tweaking if you are on a more recent version.
But if you are using the docker from step 1 you should be good to go.

