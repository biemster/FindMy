#!/usr/bin/env python3
import sys, os
from base64 import b64decode

in_keyfile = sys.argv[1]

hashed_adv = ''
with open(in_keyfile) as keyfile:
    for line in keyfile:
        key = line.rstrip('\n').split(': ')
        if key[0] == 'Advertisement key': hashed_adv = key[1]
adv = b64decode(hashed_adv)

fw = bytearray(open('./FindMy.bin', 'rb').read())
key_start = 21284
fw[key_start:key_start +28] = adv
with open('FindMy_' + os.path.basename(in_keyfile)[:-5] + '.bin', 'wb') as fw_out:
    fw_out.write(fw)