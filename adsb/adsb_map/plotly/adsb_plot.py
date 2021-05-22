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

    print (data)
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

    fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", hover_name="callsign",
                                 color='altitude', color_continuous_scale=px.colors.sequential.Plasma,
                                 hover_data=["altitude",'range','azimuth','elevation'],
                                 zoom=7, height=500, width=700)
    fig.add_trace(px.scatter_mapbox(df_rx, lat="rx_lat", lon="rx_lon",hover_name="callsign",
                                 color='rx_alt',).data[0])
    # fig.update_layout(mapbox_style="open-street-map")

    #fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    fig.update_layout(
        autosize=True,
        # hovermode='closest',
        mapbox_style="open-street-map",
        mapbox=go.layout.Mapbox(
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=32.696966,
                lon=-117.248741
            ),
            pitch=0,
            zoom=7,
            #style="stamen-terrain",
            style="open-street-map",
            # height=500,
            # width=700
        ),
    )



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
