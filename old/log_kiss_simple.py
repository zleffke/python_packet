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

    log = parser.add_argument_group('Log File Parameters')
    log.add_argument('--log_path',
                       dest='log_path',
                       type=str,
                       default=os.getcwd(),
                       help="Daemon Configuration File Path",
                       action="store")
    raw_log_file = '.'.join([startup_ts, 'kiss'])
    log.add_argument('--raw_file',
                       dest='raw_file',
                       type=str,
                       default=raw_log_file,
                       help="Raw Log File",
                       action="store")

    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------

    fp_raw = '/'.join([args.log_path,args.raw_file])
    print ' dumping KISS to:', fp_raw
    ser = serial.Serial(args.dev, args.baud)
    ser_data = bytearray()
    kiss_frame = {}
    packet = False
    packet_count = 0
    ax25_count = 0
    ax25_frames = []
    ts_flag = False
    ts_str = ""
    print 'Serial Port Open:',ser.isOpen()
    while (1):
        try:
            if ser.inWaiting() >= 1:
                #NEED TO START Checking for KISS DATA HERE
                #Could have back to back KISS frames that jacks everything up.
                if ts_str == "":
                    ts_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f UTC")
                ser_data.append(ser.read())
                #time.sleep(0.01)
            elif ((len(ser_data) > 0) and (ser.inWaiting() < 1)):
                packet = True
                packet_count += 1

            if packet: #packet received, lets parse it!
                print "\nPacket Received: {:d}".format(packet_count)
                print "Time Stamp [UTC]:", ts_str
                ser_data = bytearray(ser_data)
                print binascii.hexlify(ser_data)
                if ser_data[0]==FEND and ser_data[-1]==FEND: #KISS Frame received
                    print '  KISS Frame: {:s}'.format(str(binascii.hexlify(ser_data)))
                    with open(fp_raw, 'a') as f:
                        f.write(ser_data)
                    f.close()
                    print "Raw KISS data saved to file"


                ts_str = "" #reset timestamp
                ser_data = bytearray() #reset serial buffer
                packet = False #reset packet flag
        except Exception as e:
            print "Exception", e# -*- coding: utf-8 -*-
            ts_str = "" #reset timestamp
            ser_data = bytearray() #reset serial buffer
            packet = False #reset packet flag

        except(KeyboardInterrupt):
            for i,frame in enumerate(ax25_frames):
                print i, frame
            sys.exit()
        time.sleep(0.001) #needed to throttle for CPU

    sys.exit()


if __name__ == '__main__':
    main()
