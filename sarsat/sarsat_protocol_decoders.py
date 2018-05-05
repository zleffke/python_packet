#!/usr/bin/env python
#Script for parsing SARSAT SARP messages on PDS.

import math
import string
import time
import sys
import os
import datetime
import logging
import json
import serial
import binascii
import socket
import errno
import uuid
import numpy
import struct
import bitarray


def decode_maritime_user(bits):
    print "---Maritime User Protocol---"
    #print bits.to01()
    protocol_code   = bits[0:3]
    mmsi_rc         = bits[3:39]
    bcn_number      = bits[39:45]
    spare           = bits[45:47]
    aux_rl_dev_type = bits[47:]

    msg_bin = {}
    msg_bin['protocol_code']    = protocol_code.to01()
    msg_bin['mmsi_rc']          = mmsi_rc.to01()
    msg_bin['bcn_number']       = bcn_number.to01()
    msg_bin['spare']            = spare.to01()
    msg_bin['aux_rl_dev_type']  = aux_rl_dev_type.to01()

    print json.dumps(msg_bin, indent=4)
    return msg_bin

def decode_radio_callsign_user(bits):
    print "---Radio Callsign User Protocol---"
    protocol_code   = bits[0:3]
    radio_callsign  = bits[3:39]
    bcn_number      = bits[39:45]
    spare           = bits[45:47]
    aux_rl_dev_type = bits[47:]

    msg_bin = {}
    msg_bin['protocol_code']    = protocol_code.to01()
    msg_bin['radio_callsign']   = radio_callsign.to01()
    msg_bin['bcn_number']       = bcn_number.to01()
    msg_bin['spare']            = spare.to01()
    msg_bin['aux_rl_dev_type']  = aux_rl_dev_type.to01()

    print json.dumps(msg_bin, indent=4)
    return msg_bin

def decode_aviation_user(bits):
    print "---Aviation User Protocol---"
    protocol_code   = bits[0:3]
    air_reg_mark    = bits[3:45]
    spare           = bits[45:47]
    aux_rl_dev_type = bits[47:]

    msg_bin = {}
    msg_bin['protocol_code']    = protocol_code.to01()
    msg_bin['air_reg_mark']     = air_reg_mark.to01()
    msg_bin['spare']            = spare.to01()
    msg_bin['aux_rl_dev_type']  = aux_rl_dev_type.to01()

    print json.dumps(msg_bin, indent=4)
    return msg_bin

def decode_national_location_plb(bits):
    print "---National Location PLB Protocol---"
    protocol_code   = bits[0:4]
    identification  = bits[4:22]
    north_south     = bits[23]
    latitude_deg    = bits[24:31]
    latitude_min    = bits[31:36]
    east_west       = bits[36]
    longitude_deg   = bits[37:45]
    longitude_min   = bits[45:50]

    lat_deg = ord(latitude_deg.tobytes())
    lat_min = ord(latitude_min.tobytes())
    latitude = lat_deg + lat_min/60.0
    if north_south: latitude = latitude * -1

    lon_deg = ord(longitude_deg.tobytes())
    lon_min = ord(longitude_min.tobytes())
    longitude = lon_deg + lon_min/60.0
    if east_west: longitude = longitude * -1

    print latitude, longitude


    msg_bin = {}
    msg_bin['protocol_code']    = protocol_code.to01()


    print json.dumps(msg_bin, indent=4)
    return msg_bin
