#!/usr/bin/env bash

ids='["123","456"]'

searchPartyToken=$(security find-generic-password -w -s 'com.apple.account.AppleAccount.search-party-token')
AppleID_UUID=$(security find-generic-password -w -s 'iCloud')

anisette=$(curl -s localhost:8080/anisette | python -c "import sys,json; print(json.load(sys.stdin)['base64_encoded_data'])" | base64 -D)
machineID=$(python -c "import sys,json; print(json.loads('$anisette')['machineID'])")
oneTimePassword=$(python -c "import sys,json; print(json.loads('$anisette')['oneTimePassword'])")
routingInfo=$(python -c "import sys,json; print(json.loads('$anisette')['routingInfo'])")

swver=$(sw_vers | sed -E 's/.*:[[:blank:]](.*)/\1/' | paste -d\; -s -)
model=$(ioreg -d2 -c IOPlatformExpertDevice | awk -F\" '/model/{print $(NF-1)}')
userAgent="searchpartyd/1 <$model>/<$swver>"

clientTime=$(date +%Y-%m-%dT%H:%M:%S%z)
timeZone=$(date +%Z)
unixEpoch=$(date +%s)
startDate=$(bc <<<"1654016611 - (86400*7)")

auth_b64=$(echo "$searchPartyToken:$AppleID_UUID" | base64)

data="{search: [{"endDate": $unixEpoch,"startDate": $startDate,"ids": $ids}]}"

echo $clientTime $timeZone $unixEpoch
echo "search-party-token:" $searchPartyToken
echo "AppleID_UUID:" $AppleID_UUID
echo "machineID:" $machineID
echo "oneTimePassword:" $oneTimePassword
echo "User-Agent:" $userAgent
echo "data:" $data


curl -v \
 --header "Authorization: $auth_b64" \
 --header "X-Apple_I_MD: $oneTimePassword" \
 --header "X-Apple_I_MD-RINFO: $routingInfo" \
 --header "X-Apple_I_MD-M: $machineID" \
 --header "X-Apple_I_TimeZone: $timeZone" \
 --header "X-Apple_I_ClientTime: $clientTime" \
 --header "Content-Type: application/json" \
 --header "Accept: application/json" \
 --header "X-BA-CLIENT-TIMESTAMP: $unixEpoch" \
 --user-agent "$userAgent" \
 -d "$data" \
 -X POST https://gateway.icloud.com/acsnservice/fetch

