# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and @vtky and @hatomist and others.

## Install and Run
To install just clone this repo, to run a Mac (real or virtual) and an Apple ID are required.

1. (Optional, if you don't have a MAC and/or Apple ID): Generate an Apple ID, and install the Catalina Pre-installed docker image from https://github.com/sickcodes/Docker-OSX#run-catalina-pre-installed-, and login to iCloud using your AppleID.
2. Generate keys using `generate_keys.py`.
3. Deploy your advertisement keys on devices supported by OpenHaystack. The ESP32 firmware is a mirror of the OpenHaystack binary, the Lenze 17H66 is found in most 1$ tags obtained from the east. An nRF51 firmware can be found here: https://github.com/dakhnod/FakeTag
4. run `request_reports.py` in the same directory as your `.keys` files (should work out of the box, no dependencies). Your keychain password is by default your login password.
5. Alternatively, use the `FindMy_{proxy,client}.py` combination. Run the `FindMy_proxy.py` on a (virtual) Mac, and use the `FindMy_client.py` on any other device where you need the reports. Ideally use local port forwarding `ssh <your.mac> -L6176::6176` to login to the Mac, and start the proxy from that shell. Or ssh out of your mac with remote port forwarding `ssh <some.public.machine> -R6176::6176` while the proxy is running, so you can access it in your mobile app from anywhere in the world. Although then anyone can, so that might not be what you want.

This is using the ancient urllib on python 2.7 that comes with Catalina preinstalled. If you are on Monterey 12.3+ `python2` is removed and you should use `python3`, see the `monterey` branch in this repo for that.
