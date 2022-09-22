#!/usr/bin/env python3
import argparse
import tempfile
from FindMy_client import FindMyClient

class MappingClient(FindMyClient):

    def __init__(self, prefix='', ip='127.0.0.1', port=6176, startDate_ms=None, endDate_ms=None, autorun=True, display=False):
        super().__init__(prefix, ip, port, startDate_ms, endDate_ms, autorun, display)

        if autorun:
            self.handle_map()

    def handle_map(self):
        import folium,webbrowser
        iconcolors = ['red','blue','green','purple','pink','orange','beige','darkred','darkblue','darkgreen','darkpurple','lightred','lightblue','lightgreen','cadetblue','gray','lightgray','black']
        osmap = folium.Map((self.ordered[-1]['lat'],self.ordered[-1]['lon']), zoom_start=15)
        for rep in self.ordered:
            dt = rep["isodatetime"].split('T')
            popup = folium.Popup(folium.IFrame(html=f'<h1>{rep["key"]}</h1> <h3>{dt[0]}</h3> <h3>{dt[1]}</h3>', width=150, height=150))
            osmap.add_child(folium.Marker(location=(rep['lat'],rep['lon']), popup=popup, icon=folium.Icon(color=iconcolors[list(self.found).index(rep['key'])])))
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as fp:
            fp.close()
            osmap.save(fp.name)
            webbrowser.open(f'file://{fp.name}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='only use keyfiles starting with this prefix', default='')
    args = parser.parse_args()
    MappingClient(prefix=args.prefix, autorun=True)