#!/usr/bin/env python2
import sys,base64,hashlib,random
from p224 import scalar_mult,curve
import argparse

def int_to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()



parser = argparse.ArgumentParser()
parser.add_argument('-k','--keys', help='number of keys to generate', type=int, default=1)
parser.add_argument('-n','--name', help='name (prefix) of the keyfiles')
parser.add_argument('-y','--yaml', help='yaml file where to write the list of generated keys')
parser.add_argument('-v','--verbose', help='print keys as they are generated', action="store_true")
args=parser.parse_args()

if args.yaml is not None:
  yaml=open(args.yaml+'.yaml','w')
  yaml.write('  keys:\n')

i=1
while i<=args.keys:
    priv = random.getrandbits(224)
    adv,_ = scalar_mult(priv, curve.g)

    priv_bytes = int_to_bytes(priv, 28)
    adv_bytes = int_to_bytes(adv, 28)

    priv_b64 = base64.b64encode(priv_bytes).decode("ascii")
    adv_b64 = base64.b64encode(adv_bytes).decode("ascii")
    s256_b64 = base64.b64encode(sha256(adv_bytes)).decode("ascii")

    if args.verbose:
      print('%d)' % (i))
      print('Private key: %s' % priv_b64)
      print('Advertisement key: %s' % adv_b64)
      print('Hashed adv key: %s' % s256_b64)
    if '/' in s256_b64[:7]:
        print('no key file written, there was a / in the b64 of the hashed pubkey :(')
    else:
        if args.name:
          fname = '%s_%d.keys' % (args.name, i)
        else:
          fname = '%s.keys' % s256_b64[:7]
        with open(fname, 'w') as f:
            f.write('Private key: %s\n' % priv_b64)
            f.write('Advertisement key: %s\n' % adv_b64)
            f.write('Hashed adv key: %s\n' % s256_b64)
        i = i +1
        if args.yaml is not None:
          yaml.write('    - "%s"\n' % adv_b64)
