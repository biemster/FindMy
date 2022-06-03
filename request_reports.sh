#!/usr/bin/env bash

ids='["123","456"]'

AppleID_UUID=$(security find-generic-password -s 'iCloud' | awk -F\" '/acct/{print $(NF-1)}')
searchPartyToken=$(security find-generic-password -w -s 'com.apple.account.AppleAccount.search-party-token')

anisette=$(./AOSKit 2>&1)
machineID=$(echo "$anisette" | awk -F\" '/X-Apple-MD-M\"/{print $(NF-1)}')
oneTimePassword=$(echo "$anisette" | awk -F\" '/X-Apple-MD\"/{print $(NF-1)}')

swver=$(sw_vers | sed -E 's/.*:[[:blank:]](.*)/\1/' | paste -d\; -s -)
model=$(ioreg -d2 -c IOPlatformExpertDevice | awk -F\" '/model/{print $(NF-1)}')
userAgent="searchpartyd/1 <$model>/<$swver>"

clientTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)
timeZone=$(date +%Z)
unixEpoch=$(date +%s)
endDate=$(($unixEpoch * 1000))
startDate=$(($endDate - (86400000*7)))

auth_b64=$(echo "$AppleID_UUID:$searchPartyToken" | base64)

data="{\"search\": [{\"endDate\": $endDate, \"startDate\": $startDate, \"ids\": $ids}]}"

echo $clientTime $timeZone $unixEpoch
echo "AppleID_UUID:" $AppleID_UUID
echo "search-party-token:" $searchPartyToken
echo "machineID:" $machineID
echo "oneTimePassword:" $oneTimePassword
echo "User-Agent:" $userAgent
echo "data:" $data


curl -v \
 --header "Authorization: Basic $auth_b64" \
 --header "X-Apple-I-MD: $oneTimePassword" \
 --header "X-Apple-I-MD-RINFO: 17106176" \
 --header "X-Apple-I-MD-M: $machineID" \
 --header "X-Apple-I-TimeZone: $timeZone" \
 --header "X-Apple-I-Client-Time: $clientTime" \
 --header "Content-Type: application/json" \
 --header "Accept: application/json" \
 --header "X-BA-CLIENT-TIMESTAMP: $unixEpoch" \
 --user-agent "$userAgent" \
 -d "$data" \
 -X POST https://gateway.icloud.com/acsnservice/fetch

