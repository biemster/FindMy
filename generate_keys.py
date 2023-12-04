#!/usr/bin/env python3
import base64, hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import argparse


def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--nkeys', help='number of keys to generate', type=int, default=1)
parser.add_argument('-p', '--prefix', help='prefix of the keyfiles')
parser.add_argument('-y', '--yaml', help='yaml file where to write the list of generated keys')
parser.add_argument('-v', '--verbose', help='print keys as they are generated', action="store_true")
args = parser.parse_args()

if args.yaml:
    yaml = open(args.yaml + '.yaml', 'w')
    yaml.write('  keys:\n')

for i in range(args.nkeys):
    private_key = ec.generate_private_key(ec.SECP224R1(), default_backend())
    public_key = private_key.public_key()

    private_key_bytes = private_key.private_numbers().private_value.to_bytes(28, byteorder='big')
    public_key_bytes = public_key.public_numbers().x.to_bytes(28, byteorder='big')

    private_key_b64 = base64.b64encode(private_key_bytes).decode("ascii")
    public_key_b64 = base64.b64encode(public_key_bytes).decode("ascii")
    s256_b64 = base64.b64encode(sha256(public_key_bytes)).decode("ascii")

    if args.verbose:
        print('%d)' % (i + 1))
        print('Private key: %s' % private_key_b64)
        print('Advertisement key: %s' % public_key_b64)
        print('Hashed adv key: %s' % s256_b64)

    if '/' in s256_b64[:7]:
        print('no key file written, there was a / in the b64 of the hashed pubkey :(')
    else:
        if args.prefix:
            fname = '%s_%s.keys' % (args.prefix, s256_b64[:7])
        else:
            fname = '%s.keys' % s256_b64[:7]

        with open(fname, 'w') as f:
            f.write('Private key: %s\n' % private_key_b64)
            f.write('Advertisement key: %s\n' % public_key_b64)
            f.write('Hashed adv key: %s\n' % s256_b64)

        if args.yaml:
            yaml.write('    - "%s"\n' % public_key_b64)
