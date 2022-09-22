#!/usr/bin/env python3
import argparse
import datetime
import time
import requests
import json
from FindMy_client import FindMyClient


class TraccarClient(FindMyClient):

    def __init__(self, prefix='', ip='127.0.0.1', port=6176, startDate_ms=None, endDate_ms=None, autorun=True, display=False, url=None, update_interval=None):
        super().__init__(prefix, ip, port, startDate_ms, endDate_ms, autorun, display)

        # self.last_update = {key: datetime.datetime.timestamp(datetime.datetime.now()) * 1000 for key in self.names.values()}
        self.last_update = {}

        self.url = url # "http://demo.traccar.org:5055/"
        if url is None:
            raise Exception('Need to have a url to post to in the format "http://demo.traccar.org:5055/"')

        if autorun:
            self.send_latest_to_traccar()
        
        self.update_interval = int(update_interval)

        if update_interval is not None:
            self.do_update_loop()
    
    def send_to_traccar(self, res):

        url = self.url
        url += "?id=" + str(res['key'])
        url += "&lat=" + str(res['lat'])
        url += "&lon=" + str(res['lon'])
        url += "&timestamp=" + str(res['timestamp'])

        
        print(f'Sent: "{url}"')
        req = requests.post(url)


    def send_latest_to_traccar(self):
        checked = []
        for i in range(len(self.ordered)):
            if self.ordered[-i]['key'] in checked:
                continue
            checked.append(self.ordered[-i]['key'])

            if self.ordered[-i]['key'] not in self.last_update.keys() or \
            self.last_update[self.ordered[-i]['key']] < self.ordered[-i]['timestamp']:
                self.last_update[self.ordered[-i]['key']] = self.ordered[-i]['timestamp']
                self.send_to_traccar(self.ordered[-i])
            else:
                print(f"Duplicate detected for key: {self.ordered[-i]['key']}, not updating")
            if set(checked) == set(self.found):
                break
    
    def do_update_loop(self):
        while True:
            self.read_keyfiles()
            self.do_request()
            self.decode_results()
            self.send_latest_to_traccar()
            time.sleep(self.update_interval)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='only use keyfiles starting with this prefix', default='')
    parser.add_argument('-u', '--url', help='traccar url, formatted like "http://demo.traccar.org:5055/"', default=None)
    parser.add_argument('-i', '--interval', help='update interval (seconds)', default=None)

    args = parser.parse_args()
    TraccarClient(prefix=args.prefix, url=args.url, update_interval=args.interval, autorun=(args.interval is None))
