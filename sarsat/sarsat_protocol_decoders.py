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
