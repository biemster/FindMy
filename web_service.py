import datetime
import json
import os
import re

from fastapi import FastAPI

import requests
from fastapi.params import Query
from fastapi.responses import JSONResponse
from pypush_gsa_icloud import icloud_login_mobileme, generate_anisette_headers

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


@app.get("/SingleDeviceEncryptedReports/",summary="Retrieve reports for one device at a time.")
async def single_device_encrypted_reports(
        advertisement_key: str = Query(
            description="Hashed Advertisement Base64 Key.",
            min_length=44, max_length=44, regex=r"^[-A-Za-z0-9+/]*={0,3}$"),
        hours: int = Query(1, description="Hours to search back in time", ge=1, le=24)):
    unix_epoch = int(datetime.datetime.now().strftime('%s'))
    start_date = unix_epoch - (60 * 60 * hours)
    data = {"search": [{"startDate": start_date * 1000, "endDate": unix_epoch * 1000, "ids": [advertisement_key]}]}

    r = requests.post("https://gateway.icloud.com/acsnservice/fetch",
                      auth=(dsid, searchPartyToken),
                      headers=generate_anisette_headers(),
                      json=data)

    return json.loads(r.content.decode(encoding='utf-8'))


@app.get("/MutipleDeviceEncryptedReports/",summary="Retrieve reports for multiple devices at a time.")
async def mutiple_device_encrypted_reports(
        advertisement_keys: str = Query(
            description="Hashed Advertisement Base64 Key. "
                        "Separate each key by a comma.",
        ),
        hours: int = Query(1, description="Hours to search back in time", ge=1, le=24)):
    re_exp = r"^[-A-Za-z0-9+/]*={0,3}$"
    advertisement_keys_list = []
    advertisement_keys_invalid_list = []
    for key in advertisement_keys.strip().split(','):
        if len(key) != 44 or not re.match(re_exp, key):
            advertisement_keys_invalid_list.append(key)
        else:
            if len(key)>0:
                advertisement_keys_list.append(key)

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
