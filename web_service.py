import datetime
import json
import os
from fastapi import FastAPI

import requests
from fastapi.params import Query
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


@app.get("/get_encrypted_reports/")
async def handle_form(
        advertisement_key: str = Query(
            description="Paste your Hashed Advertisement Base64 Key here. Please be aware this is NOT the Private Key, "
                        "or Public Key! The Hashed Advertisement Key is a Base64 encoded string, that used SHA256 to "
                        "hash the Advertisement/Public Key.",
                                       min_length=44, max_length=44, regex=r"^[-A-Za-z0-9+/]*={0,3}$"),
        hours: int = Query(1, description="Hours to search back in time", ge=1, le=24), ) -> str:
    unix_epoch = int(datetime.datetime.now().strftime('%s'))
    start_date = unix_epoch - (60 * 60 * hours)
    data = {"search": [{"startDate": start_date * 1000, "endDate": unix_epoch * 1000, "ids": [advertisement_key]}]}

    r = requests.post("https://gateway.icloud.com/acsnservice/fetch",
                      auth=(dsid, searchPartyToken),
                      headers=generate_anisette_headers(),
                      json=data)
    res = r.content.decode()

    return res
