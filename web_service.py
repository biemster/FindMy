import datetime
import hashlib
import json
import os
import re
import struct

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import FastAPI, UploadFile

import requests
from fastapi.params import Query, File
from fastapi.responses import JSONResponse
from pypush_gsa_icloud import icloud_login_mobileme, generate_anisette_headers
from cryptography.hazmat.primitives.asymmetric import ec

import base64
import logging

logging.basicConfig(level=logging.ERROR)

app = FastAPI(
    title="FindMy Gateway API",
    summary="Query Apple's Find My network, allowing none Apple devices to retrieve the location reports.",
    description="### Important Concepts:  "
                "\n**Private Key:** Generated on your device as a secret, used for decrypting the report.  "
                "\n**Public Key / Advertisement Key:** Derive from the private key, used for broadcasting.  "
                "\n**Hashed Advertisement Key:** SHA256 hashed public key, used for querying reports.  "
)

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/auth.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        j = json.load(f)
else:
    mobileme = icloud_login_mobileme(second_factor='sms')
    j = {'dsid': mobileme['dsid'],
         'searchPartyToken': mobileme['delegates']['com.apple.mobileme']['service-data']['tokens'][
             'searchPartyToken']}
    with open(CONFIG_PATH, "w") as f:
        json.dump(j, f)

dsid = j['dsid']
searchPartyToken = j['searchPartyToken']


def private_to_hashed_key(private_key_b64: str) -> str:
    logging.debug(f"Private Key B64: {private_key_b64}")
    private_key = ec.derive_private_key(int.from_bytes(base64.b64decode(private_key_b64), byteorder="big"),
                                        ec.SECP224R1(), default_backend())

    public_key = private_key.public_key()
    public_key_bytes = public_key.public_numbers().x.to_bytes(28, byteorder='big')

    logging.debug(f"Public Key Bytes: {public_key_bytes.hex()}")
    digest = hashlib.new("sha256")
    digest.update(public_key_bytes)
    sha_value = digest.digest()
    s256_b64 = base64.b64encode(sha_value).decode("ascii")
    logging.debug(f"Hash ADV Key: {s256_b64}")
    return s256_b64


def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()


def decrypt(enc_data, algorithm_dkey, mode):
    decryptor = Cipher(algorithm_dkey, mode, default_backend()).decryptor()
    return decryptor.update(enc_data) + decryptor.finalize()


def decrypt_payload(report: str, private_key: str) -> {}:
    data = base64.b64decode(report)
    priv = int.from_bytes(base64.b64decode(private_key), byteorder="big")

    timestamp = int.from_bytes(data[0:4]) + 978307200
    eph_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP224R1(), data[5:62])
    shared_key = ec.derive_private_key(priv, ec.SECP224R1(), default_backend()).exchange(ec.ECDH(), eph_key)
    symmetric_key = sha256(shared_key + b'\x00\x00\x00\x01' + data[5:62])
    iv = symmetric_key[16:]
    decryption_key = symmetric_key[:16]
    ciper_txt = data[62:72]
    auth_tag = data[72:]

    clear_text = decrypt(ciper_txt, algorithms.AES(decryption_key), modes.GCM(iv, auth_tag))

    result = {}
    latitude = struct.unpack(">i", clear_text[0:4])[0] / 10000000.0
    longitude = struct.unpack(">i", clear_text[4:8])[0] / 10000000.0
    confidence = int.from_bytes(clear_text[8:9])
    status = int.from_bytes(clear_text[9:10])

    result['timestamp'] = timestamp
    result['isodatetime'] = datetime.datetime.fromtimestamp(timestamp).isoformat()
    result['lat'] = latitude
    result['lon'] = longitude
    result['confidence'] = confidence
    result['status'] = status

    return result


@app.post("/SingleDeviceEncryptedReports/", summary="Retrieve reports for one device at a time.")
async def single_device_encrypted_reports(
        advertisement_key: str = Query(
            description="Hashed Advertisement Base64 Key.",
            min_length=44, max_length=44, regex=r"^[-A-Za-z0-9+/]*={0,3}$"),
        hours: int = Query(1, description="Hours to search back in time", ge=1, le=24)):
    unix_epoch = int(datetime.datetime.now().strftime('%s'))
    start_date = unix_epoch - (60 * 60 * hours)
    data = {"search": [{"startDate": start_date * 1000, "endDate": unix_epoch * 1000,
                        "ids": [advertisement_key.strip().replace(" ", "")]}]}

    r = requests.post("https://gateway.icloud.com/acsnservice/fetch",
                      auth=(dsid, searchPartyToken),
                      headers=generate_anisette_headers(),
                      json=data)

    return json.loads(r.content.decode(encoding='utf-8'))


@app.post("/MultipleDeviceEncryptedReports/", summary="Retrieve reports for multiple devices at a time.")
async def multiple_device_encrypted_reports(
        advertisement_keys: str = Query(
            description="Hashed Advertisement Base64 Key. "
                        "Separate each key by a comma.", min_length=44, max_length=8192,
        ),
        hours: int = Query(1, description="Hours to search back in time", ge=1, le=24)):
    re_exp = r"^[-A-Za-z0-9+/]*={0,3}$"
    advertisement_keys_list = set()
    advertisement_keys_invalid_list = set()
    for key in advertisement_keys.strip().replace(" ", "").split(','):
        if len(key) != 44 or not re.match(re_exp, key):
            advertisement_keys_invalid_list.add(key)
        else:
            if len(key) > 0:
                advertisement_keys_list.add(key)

    # Error handling
    if len(advertisement_keys_invalid_list) > 0:
        return JSONResponse(
            content={"error": f"Invalid Hashed Advertisement Base64 Key(s): {advertisement_keys_invalid_list}"},
            status_code=400)
    if len(advertisement_keys_list) == 0:
        return JSONResponse(
            content={"error": f"No valid Hashed Advertisement Base64 Key(s) found"},
            status_code=400)
    if len(advertisement_keys_list) > 96:
        return JSONResponse(
            content={"error": f"Too many Hashed Advertisement Base64 Key(s) found, Apple limits to 96"},
            status_code=400)

    unix_epoch = int(datetime.datetime.now().strftime('%s'))
    start_date = unix_epoch - (60 * 60 * hours)
    data = {"search": [{"startDate": start_date * 1000, "endDate": unix_epoch * 1000, "ids": advertisement_keys_list}]}

    r = requests.post("https://gateway.icloud.com/acsnservice/fetch",
                      auth=(dsid, searchPartyToken),
                      headers=generate_anisette_headers(),
                      json=data)

    return json.loads(r.content.decode(encoding='utf-8'))


@app.post("/Decryption/", summary="Decrypt reports for one or many devices.")
async def report_decryption(
        private_keys: str = Query(
            description="**PRIVACY WARNING: Private key is a secret and shall not be sent to any untrusted website, "
                        "use at your own risk!**  "
                        "\nBase64 format, separate each key by a comma.  ", min_length=40, max_length=8192,
        ),
        reports: UploadFile = File(..., max_size=5 * 1024 * 1024,
                                   description="The JSON response from MultipleDeviceEncryptedReports or "
                                               "SingleDeviceEncryptedReports"),
        skip_invalid: bool = Query(description="Ignore report and private mismatch", default=False)):
    valid_private_keys = set()
    invalid_private_keys = set()

    key_dict = {}
    re_exp = r"^[-A-Za-z0-9+/]*={0,3}$"
    for key in private_keys.strip().split(','):
        if len(key) != 40 or not re.match(re_exp, key):
            invalid_private_keys.add(key)
        else:
            if len(key) > 0:
                valid_private_keys.add(key)

    for key in valid_private_keys:
        try:
            key_dict[private_to_hashed_key(key)] = key
        except Exception as e:
            logging.error(f"Private Key Decode Failed: {e}", exc_info=True)
            invalid_private_keys.add(key)

    valid_reports = {}
    invalid_reports = set()

    try:
        loaded_reports = json.loads(reports.file.read())
        logging.debug("JSON Loaded")
        if loaded_reports['statusCode'] == '200':
            logging.debug("Status Code 200")
        else:
            return JSONResponse(
                content={"error": f"Upstream informed an error. {loaded_reports['statusCode']}"},
                status_code=400)

        reports = loaded_reports['results']
        for report in reports:
            logging.debug(f"Processing {report}")
            if report['id'] in valid_reports:
                valid_reports[report['id']].add(report)
            else:
                logging.debug(f"ID is not in dict, creating list and adding ...")
                valid_reports[report['id']] = set()
                valid_reports[report['id']].add(report)

    except Exception as e:
        logging.error(f"JSON Decode Failed: {e}", exc_info=True)
        return JSONResponse(
            content={"error": f"Invalid JSON Format, Report Decode Failed"},
            status_code=400)

    if len(valid_reports) == 0:
        return JSONResponse(
            content={"error": f"No valid reports found"},
            status_code=400)

    for hash_key in valid_reports:
        if hash_key in key_dict:
            for report in valid_reports.get(hash_key):
                clear_text = decrypt_payload(report['payload'], key_dict[hash_key])
                report['decrypted_payload'] = clear_text
        else:
            invalid_reports.add(hash_key)

    if len(invalid_reports) > 0 and not skip_invalid:
        return JSONResponse(
            content={"error": f"Invalid Hashed Advertisement Base64 Key(s): {invalid_reports}"},
            status_code=400)

    return valid_reports
