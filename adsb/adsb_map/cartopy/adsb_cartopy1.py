#!/usr/bin/env python3

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
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib import colorbar, colors
from cartopy.io.img_tiles import OSM

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
    #print (data)
    df = pd.DataFrame.from_dict(data)
    print (df)
    print (df.columns.values)
    calls = df['callsign'].unique()
    print(calls)
    geo={"rx_lat":32.696966, "rx_lon":-117.248741, "rx_alt":0.1, "callsign":"RECEIVER", }
    df_rx = pd.DataFrame(geo, index=[0])


    fig = plt.figure()
    #ax = fig.add_subplot(1, 1, 1, projection=imagery.crs)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())


    ax.set_extent([-119.0, -116, 32, 34], crs=ccrs.PlateCarree())
    ax.gridlines()
    coast_10m = cfeature.NaturalEarthFeature('physical', 'coastline', '10m',
                                            edgecolor='black',
                                            facecolor='white')
    ax.add_feature(coast_10m, zorder = 0)
    #ax.add_feature(coast_10m)
    ax.plot(geo['rx_lon'], geo['rx_lat'], marker='D', color='red', markersize=12,
             alpha=1, zorder = 1)

    ax.scatter(df['longitude'], df['latitude'], c=df['altitude'],cmap=plt.get_cmap('coolwarm'), zorder=2)


    #geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    #plt.colorbar(cmap=plt.get_cmap('coolwarm'))
    plt.show()

    sys.exit()

if __name__ == '__main__':
    main()
