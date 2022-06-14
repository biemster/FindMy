#!/usr/bin/env python3
import sys,base64,hashlib,random
from p224 import scalar_mult,curve

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

    adv_b64 = base64.b64encode(adv.to_bytes(28, "big")).decode("ascii")
    s256_b64 = base64.b64encode(sha256(adv.to_bytes(28, "big"))).decode("ascii")

    print(f'{i+1})')
    print(f'Private key: {base64.b64encode(priv.to_bytes(28, "big")).decode("ascii")}')
    print(f'Advertisement key: {adv_b64}')
    print(f'Hashed adv key: {s256_b64}')
    if '/' in s256_b64[:7]:
        print('no key file written, there was a / in the b64 of the hashed pubkey :(')
    else:
        with open(f'{s256_b64[:7]}.keys', 'w') as f:
            f.write(f'Private key: {base64.b64encode(priv.to_bytes(28, "big")).decode("ascii")}\n')
            f.write(f'Advertisement key: {adv_b64}\n')
            f.write(f'Hashed adv key: {s256_b64}\n')

