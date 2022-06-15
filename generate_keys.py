#!/usr/bin/env python2
import sys,base64,hashlib,random
from p224 import scalar_mult,curve

def int_to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()


nkeys = 1
if len(sys.argv) == 2 and sys.argv[1].isdigit():
    nkeys = int(sys.argv[1])

for i in range(nkeys):
    priv = random.getrandbits(224)
    adv,_ = scalar_mult(priv, curve.g)

    priv_bytes = int_to_bytes(priv, 28)
    adv_bytes = int_to_bytes(adv, 28)

    priv_b64 = base64.b64encode(priv_bytes).decode("ascii")
    adv_b64 = base64.b64encode(adv_bytes).decode("ascii")
    s256_b64 = base64.b64encode(sha256(adv_bytes)).decode("ascii")

    print('%d)' % (i+1))
    print('Private key: %s' % priv_b64)
    print('Advertisement key: %s' % adv_b64)
    print('Hashed adv key: %s' % s256_b64)
    if '/' in s256_b64[:7]:
        print('no key file written, there was a / in the b64 of the hashed pubkey :(')
    else:
        with open('%s.keys' % s256_b64[:7], 'w') as f:
            f.write('Private key: %s\n' % priv_b64)
            f.write('Advertisement key: %s\n' % adv_b64)
            f.write('Hashed adv key: %s\n' % s256_b64)

