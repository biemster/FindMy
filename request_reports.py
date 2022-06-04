#!/usr/bin/env python2

import subprocess

ids = []
ids.append("123") # append your keys like so
ids.append("456")


def getAppleIDUUID():
    iCloud_keys = subprocess.check_output(['/usr/bin/security', 'find-generic-password', '-s', 'iCloud'])
    acct_start = iCloud_keys[iCloud_keys.find('"acct"<blob>="') +len('"acct"<blob>="'):]
    return acct_start[:acct_start.find('"')]

def getSearchPartyToken():
    return subprocess.check_output(['/usr/bin/security', 'find-generic-password', '-w', '-s', 'com.apple.account.AppleAccount.search-party-token']).rstrip('\n')

def getOTPHeaders():
    import objc; from Foundation import NSBundle, NSClassFromString
    AOSKitBundle = NSBundle.bundleWithPath_('/System/Library/PrivateFrameworks/AOSKit.framework')
    objc.loadBundleFunctions(AOSKitBundle, globals(), [("retrieveOTPHeadersForDSID", '')])
    util = NSClassFromString('AOSUtilities')

    anisette = str(util.retrieveOTPHeadersForDSID_("-2")).split('"')
    return anisette[7], anisette[3]

def getCurrentTimes():
    import datetime, time
    clientTime = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    clientTimestamp = int(datetime.datetime.utcnow().strftime('%s'))
    return clientTime, time.tzname[1], clientTimestamp


if __name__ == "__main__":
    AppleID_UUID = getAppleIDUUID()
    searchPartyToken = getSearchPartyToken()
    machineID, oneTimePassword = getOTPHeaders()
    UTCTime, Timezone, unixEpoch = getCurrentTimes()

    import base64
    request_headers = {
        'Authorization': "Basic %s" % (base64.b64encode((AppleID_UUID + ':' + searchPartyToken).encode('ascii')).decode('ascii')),
        'X-Apple-I-MD': "%s" % (oneTimePassword),
        'X-Apple-I-MD-RINFO': '17106176',
        'X-Apple-I-MD-M': "%s" % (machineID) ,
        'X-Apple-I-TimeZone': "%s" % (Timezone),
        'X-Apple-I-Client-Time': "%s" % (UTCTime),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-BA-CLIENT-TIMESTAMP': "%s" % (unixEpoch)
    }

    data = '{"search": [{"endDate": %d, "startDate": %d, "ids": %s}]}' % (unixEpoch *1000, (unixEpoch *1000) -(86400000 *7), ids)

    # send out the whole thing
    import httplib, urllib
    conn = httplib.HTTPSConnection('gateway.icloud.com')
    conn.request("POST", "/acsnservice/fetch", data, request_headers)
    response = conn.getresponse()
    print response.status, response.reason
    print response.read()

