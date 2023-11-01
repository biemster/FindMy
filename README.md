# FindMy
Query Apple's Find My network, based on all the hard work of https://github.com/seemoo-lab/openhaystack/ and @vtky and @hatomist and others.

This is version 2, which does not require a Mac anymore to do the requests thanks to https://github.com/JJTech0130/pypush. Version 1 that can be run on Macs can still be found in the catalina (python2) and monterey (python3) branches.

## Installation and initial setup
An Apple ID is required, and until `pypush` implements SMS 2FA a trusted Apple device (real or virtual) where this ID is logged in is necessary for initial setup.

1. Clone this repository, the `openhaystack` branch of `pypush` and `anisette-v3-server`:
```bash
git clone https://github.com/biemster/FindMy
git clone -b openhaystack https://github.com/beeper/pypush.git
git clone https://github.com/Dadoum/anisette-v3-server
```
2. Follow the installation instructions for `anisette-v3-server` and make sure it works
3. Change `pypush/icloud/gsa.py` to use your local Anisette server:
```bash
sed -i 's|ANISETTE = False|ANISETTE = http://localhost:6969|' pypush/icloud/gsa.py`
```
4. (Optional, if you don't have a MAC and/or Apple ID): Generate an Apple ID, and install the Catalina Pre-installed docker image from https://github.com/sickcodes/Docker-OSX#run-catalina-pre-installed-, and login to iCloud using your AppleID.
5. Retrieve your `search-party-token` using pypush:
```bash
anisette-v3-server/anisette-v3-server & cd pypush ; python3 examples/openhaystack.py ; cd ..; killall anisette-v3-server
```

In the last step you might have to create a `config` directory in your local `pypush` copy. Also that step is the point where you need to get a verification code from a trusted device.
If all went well, you should now have a `openhaystack.json` file with the required tokens, and you don't have to rerun step 5 until that expires (delete the current `openhaystack.json` if that occurs).

## Run
1. `cd` into the `FindMy` directory and generate keys using `./generate_keys.py`.
2. Deploy your advertisement keys on devices supported by OpenHaystack. The ESP32 firmware is a mirror of the OpenHaystack binary, the Lenze 17H66 is found in most 1$ tags obtained from the east. An nRF51 firmware can be found here: https://github.com/dakhnod/FakeTag
3. run
```bash
../anisette-v3-server/anisette-v3-server & ./request_reports.py ; killall anisette-v3-server
```
in the same directory as your `.keys` files.

This current non-Mac workflow is a bit convoluted, mainly because `pypush` is still under heavy development.
If you have a running Mac easily available it is probably a good idea to use that, with the code in either the `catalina` or `moneterey` branch.
Under development in `pypush` is SMS 2FA and Anisette data generation, so when that lands it will be integrated here too which will simplify things a lot.
Check back here every now and then to see the progress on that.
