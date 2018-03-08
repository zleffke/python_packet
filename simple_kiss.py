#!/usr/bin/env python
#Cript for experimenting with serial interface to TNC in KISS Mode

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

#from optparse import OptionParser
import argparse

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD

def main():
    """ Main entry point to start the service. """

    startup_ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    #--------START Command Line argument parser------------------------------------------------------
    parser = argparse.ArgumentParser(description="Simple Serial TNC Connect and Print Program")

    cfg = parser.add_argument_group('Serial Port Parameters')
    cfg.add_argument('--device',
                       dest='dev',
                       type=str,
                       default="/dev/ttyUSB0",
                       help="Path to device",
                       action="store")
    cfg.add_argument('--baud',
                       dest='baud',
                       type=int,
                       default=9600,
                       help="Baud rate of serial port connection",
                       action="store")

    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------
    ser = serial.Serial(args.dev, args.baud)
    ser_data = bytearray()
    kiss_frame = {}
    print ser.isOpen()
    while (1):
        try:
            if ser.inWaiting() >= 1:
                ser_data.append(ser.read())
                time.sleep(0.01)
            elif len(ser_data)>0:
                print type(ser_data)
                ser_data = bytearray(ser_data)
                print type(ser_data)
                print binascii.hexlify(ser_data)
                if ser_data[0]==FEND and ser_data[-1]==FEND: #KISS Frame received
                    print 'KISS Frame detected'
                    print binascii.hexlify(ser_data)
                    new_kiss = []
                    for byte in ser_data:
                        print hex(byte)
                        if byte == FESC:
                            print 'Detected FESC'
                            next_byte = ser.read()
                            if next_byte == TFEND:


                ser_data = []
        except Exception as e:
            print "Exception", e# -*- coding: utf-8 -*-
            sys.exit()

    sys.exit()


if __name__ == '__main__':
    main()
