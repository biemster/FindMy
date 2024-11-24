#!/usr/bin/env python
import sys,os
import subprocess
from base64 import b64decode

if len(sys.argv) != 2 or os.getuid() != 0:
	print(f'Usage: sudo {sys.argv[0]} <base64 of advkey>')
	exit()

public_key = list(b64decode(sys.argv[1]))
ble_mac = [public_key[0] | 0xc0] + public_key[1:6]
adv = [
    0x1e, # Length (30)
    0xff, # Manufacturer Specific Data (type 0xff)
    0x4c, 0x00, # Company ID (Apple)
    0x12, 0x19, # Offline Finding type and length
    0x00, # State
] + public_key[-22:] + [
    0x00, # First two bits
    0x00, # Hint (0x00)
]

subprocess.run(['btmgmt', '-i', 'hci0', 'power', 'off'])
subprocess.run(['btmgmt', '-i', 'hci0', 'le', 'on'])
subprocess.run(['btmgmt', '-i', 'hci0', 'connectable', 'on']) # this is needed to set addr, but we don't want it
subprocess.run(['btmgmt', '-i', 'hci0', 'public-addr', ":".join(hex(c)[2:].zfill(2) for c in ble_mac)])
subprocess.run(['btmgmt', '-i', 'hci0', 'power', 'on'])
subprocess.run(['btmgmt', '-i', 'hci0', 'rm-adv', '1'])
subprocess.run(['btmgmt', '-i', 'hci0', 'add-adv', '-d', bytes(adv).hex(), '1'])
