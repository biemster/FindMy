#!/usr/bin/env python3
import os
import argparse
from base64 import b64decode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyfile', help='Path to .keys file', type=str, required=True)
    parser.add_argument('--adv-interval', help='Advertisement interval (seconds)', type=int, choices=[2,3,5,10,20,30], default=3)
    args = parser.parse_args()
    patch_fw(args.keyfile, args.adv_interval)

def read_key(keyfile):
    hashed_adv = ''
    with open(keyfile) as keyfile:
        for line in keyfile:
            key = line.rstrip('\n').split(': ')
            if key[0] == 'Advertisement key': hashed_adv = key[1]
    return hashed_adv

def patch_fw(keyfile, adv_interval=3):
    interval_patches = {2:[0x05,0xc8], 3:[0x05,0x2c], 5:[0x09,0xf4], 10:[0x11,0xe8], 20:[0x21,0xd0], 30:[0x31,0xb8]}
    adv = b64decode(read_key(keyfile))
    fw = bytearray(open('main.bin', 'rb').read())
    key_start = fw.find(bytes([0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xaa,0xbb,0xcc,0xdd,0xef,0xfe,0xdd,0xcc,0xbb,0xaa,0x99,0x88,0x77,0x66,0x55,0x44,0x33,0x22,0x11]))
    fw[key_start:key_start +28] = adv
    interval_start = fw.find(bytes([0x05,0x64,0x93,0x05,0x04,0x2c]))
    fw[interval_start] = interval_patches[adv_interval][0]
    fw[interval_start +5] = fw[interval_start +15] = interval_patches[adv_interval][1]
    with open('FindMy_' + os.path.basename(keyfile)[:-5] + '.bin', 'wb') as fw_out:
        fw_out.write(fw)

if __name__ == '__main__':
    main()