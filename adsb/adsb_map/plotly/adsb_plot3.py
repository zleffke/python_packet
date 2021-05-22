#!/usr/bin/env python3
#################################################
#   Title: ADSB Plot
# Project: ADSB
# Version: 0.0.1
#    Date: Jan, 2020
#  Author: Zach Leffke, KJ4QLP
# Comment:
# - learning plotly
#################################################

import math
import string
import time
import sys
import os
import datetime
import json
import binascii
import argparse
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def main():
    """ Main entry point to start the service. """

    startup_ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    #--------START Command Line argument parser------------------------------------------------------
    parser = argparse.ArgumentParser(description="ADSB Simple plot, plotly",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    cwd = os.getcwd()
    fp_default = '/'.join([cwd, 'data'])
    cfg = parser.add_argument_group('Configuration File')
    cfg.add_argument('--adsb_path',
                       dest='adsb_path',
                       type=str,
                       default=fp_default,
                       help="ADSB Data File Path",
                       action="store")
    cfg.add_argument('--adsb_file',
                       dest='adsb_file',
                       type=str,
                       default="adsb_valid.json",
                       help="ADSB File",
                       action="store")
    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------
    os.system('reset')
    fp = '/'.join([args.adsb_path,args.adsb_file])
    if not os.path.isfile(fp) == True:
        print ('ERROR: Invalid ADSB Data File: {:s}'.format(fp))
        sys.exit()
    print ('Importing ADSB Data File: {:s}'.format(fp))

    with open(fp,'r') as f:
        data = json.load(f)

    mapbox_access_token = open(".mapbox_token_default").read()

    #print (data)
    df = pd.DataFrame.from_dict(data)

    #df = pd.read_json(fp, precise_float=True, lines=True)
    print (df)
    print (df.columns.values)
    calls = df['callsign'].unique()
    print(calls)
    # for v in df['callsign'].unique():
    #     print df[df['col_name'] == v]
    geo={"rx_lat":32.696966, "rx_lon":-117.248741, "rx_alt":0.1, "callsign":"RECEIVER", }
    df_rx = pd.DataFrame(geo, index=[0])

    adsb_scatter = px.scatter_mapbox(df, lat="latitude", lon="longitude", hover_name="callsign",
                                 color='snr', color_continuous_scale=px.colors.sequential.Agsunset,
                                 hover_data=["altitude",'range','azimuth','elevation', 'snr'],
                                 zoom=7, height=700, width=800, )
    adsb_scatter.data[0]['marker']['size'] = 8
    print(adsb_scatter.data[0])

    rx_scatter = px.scatter_mapbox(df_rx, lat="rx_lat", lon="rx_lon", hover_name="callsign",)
                                 # zoom=7, height=500, width=700)
    #print(rx_scatter.data[0])

    rx_scatter.data[0]['marker']=dict(color='red', size=10, opacity=1.0)  #this works
    #rx_scatter.data[0]['marker']=dict(size=10, symbol='marker')  #this works
    rx_scatter.data[0]['hovertemplate']='<b>%{hovertext}</b>'


    fig_data = [adsb_scatter.data[0], rx_scatter.data[0]]
    #fig_data = [adsb_scatter.data[0], rx_data]
    layout = go.Layout(adsb_scatter.layout)
    #layout = [layout, mapbox_style="open-street-map"]
    #print (fig_data)
    #sys.exit()
    # adsb_data.layout(mapbox_style="open-street-map")
    fig = go.Figure(data=fig_data, layout=layout)
    fig.update_layout(
        mapbox=go.layout.Mapbox(
            accesstoken = mapbox_access_token,
            style="streets",
            center={'lon': -117.5, 'lat': 33.2},
            zoom=7.5,
            pitch=0
        )
    )
    #fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig.show()
    sys.exit()

if __name__ == '__main__':
    main()

# fig = go.Figure(go.Scattergeo())
# fig.update_geos(
#     visible=False, resolution=50,
#     showcountries=True, countrycolor="RebeccaPurple"
# )
# fig.update_layout(height=300, margin={"r":0,"t":0,"l":0,"b":0})
# fig.show()
