import datetime
import json
import os
import re

from fastapi import FastAPI

import requests
from fastapi.params import Query
from fastapi.responses import JSONResponse
from pypush_gsa_icloud import icloud_login_mobileme, generate_anisette_headers

app = FastAPI()

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


@app.get("/SingleDeviceEncryptedReports/")
async def handle_form(
        advertisement_key: str = Query(
            description="Paste your Hashed Advertisement Base64 Key here. Please be aware this is NOT the Private Key, "
                        "nor Public Key! The Hashed Advertisement Key is a Base64 encoded string, that used SHA256 to "
                        "hash the Advertisement/Public Key.This API process one device at a time.",
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


@app.get("/MutipleDeviceEncryptedReports/")
async def handle_form(
        advertisement_keys: str = Query(
            description="Paste your Hashed Advertisement Base64 Key here. Please be aware this is NOT the Private Key, "
                        "nor Public Key! The Hashed Advertisement Key is a Base64 encoded string, that used SHA256 to "
                        "hash the Advertisement/Public Key. Sperate each key by a comma.",
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
