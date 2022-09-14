# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and @vtky and @hatomist and others.

## Install and Run
To install just clone this repo, to run a Mac with Monterey and an Apple ID are required. (It is possible to use a VM to run this, refer to the main branch of this repo.)

1. Prerequisites: XCode or Command Line Tools, latest pip (`pip3 install -U pip`, otherwise `cryptography` will not install), python packages `cryptography`, `pyobjc` and `requests`.
2. Generate keys using `generate_keys.py`.
3. Deploy your advertisement keys on devices supported by OpenHaystack. The ESP32 firmware is a mirror of the OpenHaystack binary, the Lenze 17H66 is found in most 1$ tags obtained from the east. An nRF51 firmware can be found here: https://github.com/dakhnod/FakeTag
4. run `request_reports.py` in the same directory as your `.keys` files (should work out of the box, no dependencies). Your keychain password is by default your login password.
