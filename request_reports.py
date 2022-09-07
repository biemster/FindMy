#!/usr/bin/env python2
import os,glob
import base64,json
import hashlib,hmac
import codecs,struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import objc
from Foundation import NSBundle, NSClassFromString, NSData, NSPropertyListSerialization
from p224 import scalar_mult,curve


def bytes_to_int(b):
    return int(codecs.encode(b, 'hex'), 16)

def int_to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()

def decrypt_AES(enc_data, dkey, mode):
    cipher = Cipher(algorithms.AES(dkey), mode, default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(enc_data) + decryptor.finalize()

def decode_tag(data):
    latitude = struct.unpack(">i", data[0:4])[0] / 10000000.0
    longitude = struct.unpack(">i", data[4:8])[0] / 10000000.0
    confidence = bytes_to_int(data[8:9])
    return {'lat': latitude, 'lon': longitude, 'conf': confidence}

def getAppleDSIDandSearchPartyToken(iCloudKey):
    # copied from https://github.com/Hsn723/MMeTokenDecrypt
    decryption_key = hmac.new("t9s\"lx^awe.580Gj%'ld+0LG<#9xa?>vb)-fkwb92[}", base64.b64decode(iCloudKey), digestmod=hashlib.md5).digest()
    mmeTokenFile = glob.glob("%s/Library/Application Support/iCloud/Accounts/[0-9]*" % os.path.expanduser("~"))[0]
    decryptedBinary = decrypt_AES(open(mmeTokenFile, 'rb').read(), decryption_key, modes.CBC(b'\00' *16));
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    decryptedBinary = unpadder.update(decryptedBinary) + unpadder.finalize()
    binToPlist = NSData.dataWithBytes_length_(decryptedBinary, len(decryptedBinary))
    tokenPlist = NSPropertyListSerialization.propertyListWithData_options_format_error_(binToPlist, 0, None, None)[0]
    return tokenPlist["appleAccountInfo"]["dsPrsID"], tokenPlist["tokens"]['searchPartyToken']

def getOTPHeaders():
    AOSKitBundle = NSBundle.bundleWithPath_('/System/Library/PrivateFrameworks/AOSKit.framework')
    objc.loadBundleFunctions(AOSKitBundle, globals(), [("retrieveOTPHeadersForDSID", '')])
    util = NSClassFromString('AOSUtilities')

    anisette = str(util.retrieveOTPHeadersForDSID_("-2")).replace('"', ' ').replace(';', ' ').split()
    return anisette[6], anisette[3]

def getCurrentTimes():
    import datetime, time
    clientTime = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    clientTimestamp = int(datetime.datetime.now().strftime('%s'))
    return clientTime, time.tzname[1], clientTimestamp


if __name__ == "__main__":
    from getpass import getpass
    iCloud_decryptionkey = getpass("Enter your iCloud decryption key ($ security find-generic-password -ws 'iCloud'):")
    AppleDSID,searchPartyToken = getAppleDSIDandSearchPartyToken(iCloud_decryptionkey)
    machineID, oneTimePassword = getOTPHeaders()
    UTCTime, Timezone, unixEpoch = getCurrentTimes()

    request_headers = {
        'Authorization': "Basic %s" % (base64.b64encode((AppleDSID + ':' + searchPartyToken).encode('ascii')).decode('ascii')),
        'X-Apple-I-MD': "%s" % (oneTimePassword),
        'X-Apple-I-MD-RINFO': '17106176',
        'X-Apple-I-MD-M': "%s" % (machineID) ,
        'X-Apple-I-TimeZone': "%s" % (Timezone),
        'X-Apple-I-Client-Time': "%s" % (UTCTime),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-BA-CLIENT-TIMESTAMP': "%s" % (unixEpoch)
    }

    ids = {}
    for keyfile in glob.glob('./*keys'):
        # read key files generated with generate_keys.py
        with open(keyfile) as f:
            hashed_adv = ''
            priv = ''
            for line in f:
                key = line.rstrip('\n').split(': ')
                if key[0] == 'Private key':
                    priv = key[1]
                elif key[0] == 'Hashed adv key':
                    hashed_adv = key[1]

            if priv and hashed_adv:
                ids[hashed_adv] = priv
            else:
                print "Couldn't find key pair in " + keyfile

    data = '{"search": [{"endDate": %d, "startDate": %d, "ids": %s}]}' % (unixEpoch *1000, (unixEpoch *1000) -(86400000 *7), ids.keys())

    # send out the whole thing
    import httplib, urllib
    conn = httplib.HTTPSConnection('gateway.icloud.com')
    conn.request("POST", "/acsnservice/fetch", data, request_headers)
    response = conn.getresponse()
    print response.status, response.reason
    res = json.loads(response.read())['results']
    print '%d reports received.' % len(res)

    for report in res:
        priv = bytes_to_int(base64.b64decode(ids[report['id']]))
        data = base64.b64decode(report['payload'])

        # the following is all copied from https://github.com/hatomist/openhaystack-python, thanks @hatomist!
        timestamp = bytes_to_int(data[0:4])
        eph_key = (bytes_to_int(data[6:34]), bytes_to_int(data[34:62]))
        shared_key = scalar_mult(priv, eph_key)
        symmetric_key = sha256(int_to_bytes(shared_key[0], 28) + int_to_bytes(1, 4) + data[5:62])
        decryption_key = symmetric_key[:16]
        iv = symmetric_key[16:]
        enc_data = data[62:72]
        tag = data[72:]

        decrypted = decrypt_AES(enc_data, decryption_key, modes.GCM(iv, tag))
        res = decode_tag(decrypted)
        res['timestamp'] = timestamp + 978307200
        print report['id'] + ': ' + str(res)
