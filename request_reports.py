#!/usr/bin/env python2
import os,glob
import datetime, time
import argparse,getpass
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

def decrypt(enc_data, algorithm_dkey, mode):
    decryptor = Cipher(algorithm_dkey, mode, default_backend()).decryptor()
    return decryptor.update(enc_data) + decryptor.finalize()

def unpad(paddedBinary, blocksize):
    unpadder = PKCS7(blocksize).unpadder()
    return unpadder.update(paddedBinary) + unpadder.finalize()

def decode_tag(data):
    latitude = struct.unpack(">i", data[0:4])[0] / 10000000.0
    longitude = struct.unpack(">i", data[4:8])[0] / 10000000.0
    confidence = bytes_to_int(data[8:9])
    status = bytes_to_int(data[9:10])
    return {'lat': latitude, 'lon': longitude, 'conf': confidence, 'status':status}

def getAppleDSIDandSearchPartyToken(iCloudKey):
    # copied from https://github.com/Hsn723/MMeTokenDecrypt
    decryption_key = hmac.new("t9s\"lx^awe.580Gj%'ld+0LG<#9xa?>vb)-fkwb92[}", base64.b64decode(iCloudKey), digestmod=hashlib.md5).digest()
    mmeTokenFile = glob.glob("%s/Library/Application Support/iCloud/Accounts/[0-9]*" % os.path.expanduser("~"))[0]
    decryptedBinary = unpad(decrypt(open(mmeTokenFile, 'rb').read(), algorithms.AES(decryption_key), modes.CBC(b'\00' *16)), algorithms.AES.block_size);
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
    clientTime = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    clientTimestamp = int(datetime.datetime.now().strftime('%s'))
    return clientTime, time.tzname[1], clientTimestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--hours', help='only show reports not older than these hours', type=int, default=24)
    parser.add_argument('-p', '--prefix', help='only use keyfiles starting with this prefix', default='')
    parser.add_argument('-k', '--key', help="iCloud decryption key ($ security find-generic-password -ws 'iCloud')")
    args = parser.parse_args()
    iCloud_decryptionkey = args.key if args.key else getpass.getpass("Enter your iCloud decryption key ($ security find-generic-password -ws 'iCloud'):")

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
    names = {}
    for keyfile in glob.glob(args.prefix+'*.keys'):
        # read key files generated with generate_keys.py
        with open(keyfile) as f:
            hashed_adv = ''
            priv = ''
            name = keyfile[len(args.prefix):-5]
            for line in f:
                key = line.rstrip('\n').split(': ')
                if key[0] == 'Private key':
                    priv = key[1]
                elif key[0] == 'Hashed adv key':
                    hashed_adv = key[1]

            if priv and hashed_adv:
                ids[hashed_adv] = priv
                names[hashed_adv] = name
            else:
                print "Couldn't find key pair in " + keyfile

    startdate = unixEpoch - 60 * 60 * args.hours
    data = '{"search": [{"endDate": %d, "startDate": %d, "ids": %s}]}' % ((unixEpoch -978307200) *1000000, (startdate -978307200)*1000000, ids.keys())

    # send out the whole thing
    import httplib, urllib
    conn = httplib.HTTPSConnection('gateway.icloud.com')
    conn.request("POST", "/acsnservice/fetch", data, request_headers)
    response = conn.getresponse()
    print response.status, response.reason
    res = json.loads(response.read())['results']
    print '%d reports received.' % len(res)

    ordered = []
    found = set()
    for report in res:
        priv = bytes_to_int(base64.b64decode(ids[report['id']]))
        data = base64.b64decode(report['payload'])

        # the following is all copied from https://github.com/hatomist/openhaystack-python, thanks @hatomist!
        timestamp = bytes_to_int(data[0:4])
        if timestamp + 978307200 >= startdate:
            eph_key = (bytes_to_int(data[6:34]), bytes_to_int(data[34:62]))
            shared_key = scalar_mult(priv, eph_key)
            symmetric_key = sha256(int_to_bytes(shared_key[0], 28) + int_to_bytes(1, 4) + data[5:62])
            decryption_key = symmetric_key[:16]
            iv = symmetric_key[16:]
            enc_data = data[62:72]
            tag = data[72:]

            decrypted = decrypt(enc_data, algorithms.AES(decryption_key), modes.GCM(iv, tag))
            res = decode_tag(decrypted)
            res['timestamp'] = timestamp + 978307200
            res['isodatetime'] = datetime.datetime.fromtimestamp(res['timestamp']).isoformat()
            res['key'] = names[report['id']]
            res['goog'] = 'https://maps.google.com/maps?q=' + str(res['lat']) + ',' + str(res['lon'])
            found.add(res['key'])
            ordered.append(res)
    print '%d reports used.' % len(ordered)
    ordered.sort(key=lambda item: item.get('timestamp'))
    for rep in ordered: print rep
    print 'found:   ', list(found)
    print 'missing: ', [key for key in names.values() if key not in found]