#!/usr/bin/env python3
import os,glob,datetime,argparse
import base64,json
import hashlib,codecs,struct
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import sqlite3
from pypush_gsa_icloud import icloud_login_mobileme, generate_anisette_headers

def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()

def decrypt(enc_data, algorithm_dkey, mode):
    decryptor = Cipher(algorithm_dkey, mode, default_backend()).decryptor()
    return decryptor.update(enc_data) + decryptor.finalize()

def decode_tag(data):
    latitude = struct.unpack(">i", data[0:4])[0] / 10000000.0
    longitude = struct.unpack(">i", data[4:8])[0] / 10000000.0
    confidence = int.from_bytes(data[8:9], 'big')
    status = int.from_bytes(data[9:10], 'big')
    return {'lat': latitude, 'lon': longitude, 'conf': confidence, 'status':status}

def getAuth(regenerate=False, second_factor='sms'):
    CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/auth.json"
    if os.path.exists(CONFIG_PATH) and not regenerate:
        with open(CONFIG_PATH, "r") as f: j = json.load(f)
    else:
        mobileme = icloud_login_mobileme(second_factor=second_factor)
        j = {'dsid': mobileme['dsid'], 'searchPartyToken': mobileme['delegates']['com.apple.mobileme']['service-data']['tokens']['searchPartyToken']}
        with open(CONFIG_PATH, "w") as f: json.dump(j, f)
    return (j['dsid'], j['searchPartyToken'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--hours', help='only show reports not older than these hours', type=int, default=24)
    parser.add_argument('-p', '--prefix', help='only use keyfiles starting with this prefix', default='')
    parser.add_argument('-r', '--regen', help='regenerate search-party-token', action='store_true')
    parser.add_argument('-t', '--trusteddevice', help='use trusted device for 2FA instead of SMS', action='store_true')
    args = parser.parse_args()

    sq3db = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + '/reports.db')
    sq3 = sq3db.cursor()

    privkeys = {}
    names = {}
    for keyfile in glob.glob(os.path.dirname(os.path.realpath(__file__)) + '/' + args.prefix + '*.keys'):
        # read key files generated with generate_keys.py
        with open(keyfile) as f:
            hashed_adv = priv = ''
            name = os.path.basename(keyfile)[len(args.prefix):-5]
            for line in f:
                key = line.rstrip('\n').split(': ')
                if key[0] == 'Private key': priv = key[1]
                elif key[0] == 'Hashed adv key': hashed_adv = key[1]

            if priv and hashed_adv:
                privkeys[hashed_adv] = priv
                names[hashed_adv] = name
            else: print(f"Couldn't find key pair in {keyfile}")

    unixEpoch = int(datetime.datetime.now().strftime('%s'))
    startdate = unixEpoch - (60 * 60 * args.hours)
    data = { "search": [{"startDate": startdate *1000, "endDate": unixEpoch *1000, "ids": list(names.keys())}] }

    r = requests.post("https://gateway.icloud.com/acsnservice/fetch",
            auth=getAuth(regenerate=args.regen, second_factor='trusted_device' if args.trusteddevice else 'sms'),
            headers=generate_anisette_headers(),
            json=data)
    res = json.loads(r.content.decode())['results']
    print(f'{r.status_code}: {len(res)} reports received.')

    ordered = []
    found = set()
    for report in res:
        priv = int.from_bytes(base64.b64decode(privkeys[report['id']]), 'big')
        data = base64.b64decode(report['payload'])

        # the following is all copied from https://github.com/hatomist/openhaystack-python, thanks @hatomist!
        timestamp = int.from_bytes(data[0:4], 'big') +978307200
        sq3.execute(f"INSERT OR REPLACE INTO reports VALUES ('{names[report['id']]}', {timestamp}, {report['datePublished']}, '{report['payload']}', '{report['id']}', {report['statusCode']})")
        if timestamp >= startdate:
            eph_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP224R1(), data[5:62])
            shared_key = ec.derive_private_key(priv, ec.SECP224R1(), default_backend()).exchange(ec.ECDH(), eph_key)
            symmetric_key = sha256(shared_key + b'\x00\x00\x00\x01' + data[5:62])
            decryption_key = symmetric_key[:16]
            iv = symmetric_key[16:]
            enc_data = data[62:72]
            tag = data[72:]

            decrypted = decrypt(enc_data, algorithms.AES(decryption_key), modes.GCM(iv, tag))
            tag = decode_tag(decrypted)
            tag['timestamp'] = timestamp
            tag['isodatetime'] = datetime.datetime.fromtimestamp(timestamp).isoformat()
            tag['key'] = names[report['id']]
            tag['goog'] = 'https://maps.google.com/maps?q=' + str(tag['lat']) + ',' + str(tag['lon'])
            found.add(tag['key'])
            ordered.append(tag)
    print(f'{len(ordered)} reports used.')
    ordered.sort(key=lambda item: item.get('timestamp'))
    for rep in ordered: print(rep)
    print(f'found:   {list(found)}')
    print(f'missing: {[key for key in names.values() if key not in found]}')
    sq3.close()
    sq3db.commit()
    sq3db.close()