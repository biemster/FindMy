#!/usr/bin/env python3
import glob
import datetime
import argparse
import base64,json
import hashlib
import codecs,struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import socket

def bytes_to_int(b):
    return int(codecs.encode(b, 'hex'), 16)

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
    confidence = bytes_to_int(data[8:9])
    status = bytes_to_int(data[9:10])
    return {'lat': latitude, 'lon': longitude, 'conf': confidence, 'status':status}

class FindMyClient:
    def __init__(self, prefix='', ip='127.0.0.1', port=6176, startDate_ms=None, endDate_ms=None, autorun=True, display=False):
        self.ip = ip
        self.port = port
        
        self.ids = {}
        self.names = {}
    
        self.read_keyfiles(prefix)

        self.response = {}
        self.res = {}

        self.ordered = []
        self.found = set()

        if autorun:
            self.read_keyfiles(prefix)
            self.do_request(startDate_ms, endDate_ms)
            self.decode_results()

        if display:
            for rep in self.ordered: print(rep)
        print('found:   ', list(self.found))
        print('missing: ', [key for key in self.names.values() if key not in self.found])

    def read_keyfiles(self, prefix=''):
        for keyfile in glob.glob(prefix+'*.keys'):
            # read key files generated with generate_keys.py
            with open(keyfile) as f:
                hashed_adv = ''
                priv = ''
                name = keyfile[len(prefix):-5]
                for line in f:
                    key = line.rstrip('\n').split(': ')
                    if key[0] == 'Private key':
                        priv = key[1]
                    elif key[0] == 'Hashed adv key':
                        hashed_adv = key[1]

                if priv and hashed_adv:
                    self.ids[hashed_adv] = priv
                    self.names[hashed_adv] = name
                else:
                    print("Couldn't find key pair in", keyfile)

    def do_request(self, startDate_ms=None, endDate_ms=None):
        startDateStr = f'"startDate": {startDate_ms}, ' if startDate_ms is not None else ''
        endDateStr = f'"endDate": {endDate_ms}, ' if endDate_ms is not None else ''

        data = '{"search": [{%s"ids": %s}]}' % (startDateStr + endDateStr, list(self.ids.keys()))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.ip, self.port))
            sock.sendall(bytes(data + '\n', encoding='ascii'))
            response = b''
            while True:
                rdata = sock.recv(1024)
                if not rdata: break
                response += rdata
        finally:
            sock.close()
        self.response = response
        self.res = json.loads(self.response)['results']
        print('%d reports received.' % len(self.res))
    
    def decode_results(self):
        for report in self.res:
            priv = bytes_to_int(base64.b64decode(self.ids[report['id']]))
            data = base64.b64decode(report['payload'])

            # the following is all copied from https://github.com/hatomist/openhaystack-python, thanks @hatomist!
            timestamp = bytes_to_int(data[0:4])
            eph_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP224R1(), data[5:62])
            shared_key = ec.derive_private_key(priv, ec.SECP224R1(), default_backend()).exchange(ec.ECDH(), eph_key)
            symmetric_key = sha256(shared_key + b'\x00\x00\x00\x01' + data[5:62])
            decryption_key = symmetric_key[:16]
            iv = symmetric_key[16:]
            enc_data = data[62:72]
            tag = data[72:]

            decrypted = decrypt(enc_data, algorithms.AES(decryption_key), modes.GCM(iv, tag))
            self.res = decode_tag(decrypted)
            self.res['timestamp'] = timestamp + 978307200
            self.res['isodatetime'] = datetime.datetime.fromtimestamp(self.res['timestamp']).isoformat()
            self.res['key'] = self.names[report['id']]
            self.res['goog'] = 'https://maps.google.com/maps?q=' + str(self.res['lat']) + ',' + str(self.res['lon'])
            self.found.add(self.res['key'])
            self.ordered.append(self.res)
        self.ordered.sort(key=lambda item: item.get('timestamp'))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='only use keyfiles starting with this prefix', default='')
    parser.add_argument('--ip', help='ip of the proxy server', default='127.0.0.1')
    parser.add_argument('--port', help='port of the proxy server', default=6176)
    parser.add_argument('--hours', help='query the past n hours', default=None)
    parser.add_argument('-d', '--days', help='query the past n days', default=None)
    parser.add_argument('-m', '--minutes', help='query the past n minutes', default=None)
    parser.add_argument('--start-time', help='query records after a given time', default=None)
    parser.add_argument('--end-time', help='query records until a given time', default=None)
    args = parser.parse_args()

    endDate_ms = int(args.end_time) if args.end_time is not None else None
    startDate_ms = int(args.start_time) if args.start_time is not None else None

    if any([args.minutes, args.hours, args.days]):
        minutes = float(args.minutes) if args.minutes is not None else 0
        hours = float(args.hours) if args.hours is not None else 0
        days = float(args.days) if args.days is not None else 0
        query_duration_ms = int(1000 * 60 * (minutes + 60 * (hours + 24 * days)))
    else:
        query_duration_ms = None


    if startDate_ms is None and query_duration_ms is not None:
        if endDate_ms is None: # If given a query duration but no end date, use now as the end
            endDate_ms = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        startDate_ms = endDate_ms - query_duration_ms

    fmc = FindMyClient(prefix=args.prefix, ip=args.ip, port=args.port, endDate_ms=endDate_ms, startDate_ms=startDate_ms, autorun=True, display=True)
    pass
