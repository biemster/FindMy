# FindMy ESP32 firmware
Straight copy from OpenHaystack with small changes to `flash_esp32.sh`, kept here for archival purposes.
Please refer to https://github.com/seemoo-lab/openhaystack for more info, all credit goes there.

## How to use:
`esptool.py` from Espressiff needs to be installed, then just simply type
```
$ ./flash_esp32.sh <your base64 adv key>
```

## MicroPython scripts
Additionally there are two micropython scripts in development, one for Apple's FindMy network and
one for Google's. The Apple script doesn't work yet because micropython does not support changing
the BT MAC out of the box (there is a workaround in
https://github.com/orgs/micropython/discussions/10080#discussioncomment-4247358 though)
The Google script is still very much a work in progress, it just implemented table 8 from
https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn#advertised-frames
and shows up as an Eddystone with the ephemeral id as data field in nRF Connect.
