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
    packet = False
    packet_count = 0
    ax25_frames = []
    ts_flag = False
    ts_str = ""
    print ser.isOpen()
    while (1):
        try:

            if ser.inWaiting() >= 1:
                if ts_str == "":
                    ts_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f UTC")
                ser_data.append(ser.read())
                time.sleep(0.01)
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
                    del ser_data[0] #remove the first FEND
                    del ser_data[-1] #remove the last FEND
                    new_kiss = bytearray()
                    for i,byte in enumerate(ser_data):
                        #print hex(byte)
                        if byte == FESC:
                            print 'Detected FESC'
                            next_byte = ser_data[i+1]
                            if next_byte == TFEND:
                                print "detected TFEND, inserting FEND"
                                new_kiss.append(FEND)
                            elif next_byte == TFESC:
                                print 'detected TFESC, inserting FESC'
                                new_kiss.append(FESC)
                        else:
                            new_kiss.append(byte)
                    new_kiss = bytearray(new_kiss)
                    print '  Un-Escaped: {:s}'.format(str(binascii.hexlify(new_kiss)))
                    kiss_cmd = new_kiss.pop(0)
                    ax25_frame = new_kiss #since we've popped the last KISS character, rename the variable
                    print 'Control Character: 0x{:02X}'.format(kiss_cmd)
                    print ' AX.25 Frame: {:s}'.format(str(binascii.hexlify(ax25_frame)))
                    print ax25_frame

                    ax25 = {}
                    ax25['ts_utc'] = ts_str
                    ax25['hex_frame'] = str(binascii.hexlify(ax25_frame))
                    ax25['dest_call'] = ""
                    ax25['dest_ssid'] = 0
                    ax25['src_call'] = ""
                    ax25['src_ssid'] = 0

                    EOA_idx = 0 #End Of Address Index
                    for i,byte in enumerate(ax25_frame):
                        #print "{:d} 0x{:02X} {:08b}".format(i,byte,byte)
                        if (byte & 0x01): #should be end of address field
                            EOA_idx = i
                            break
                    addr_cnt = (EOA_idx+1)/7 #count of address field
                    #print EOA_idx, addr_cnt, (EOA_idx+1)%7

                    #extract DESTINATION field
                    dest_call = ax25_frame[0:6]
                    del ax25_frame[0:6] #remove from frame
                    for byte in dest_call:
                        ax25['dest_call'] += chr((byte >> 1) & 0x7F)
                    ax25['dest_call'] = ax25['dest_call'].strip()
                    dest_ssid = ax25_frame.pop(0)
                    ax25['dest_ssid'] = int((dest_ssid >> 1) & 0x0F)
                    addr_cnt -= 1 #decrement address count

                    #extract SOURCE field
                    src_call = ax25_frame[0:6]
                    del ax25_frame[0:6] #remove from frame
                    for byte in src_call:
                        ax25['src_call'] += chr((byte >> 1) & 0x7F)
                    ax25['src_call'] = ax25['src_call'].strip()
                    src_ssid = ax25_frame.pop(0)
                    ax25['src_ssid'] = int((src_ssid >> 1) & 0x0F)
                    addr_cnt -= 1 #decrement address count

                    #Extract Additional VIA address fields
                    while (addr_cnt):
                        #print addr_cnt
                        via_str = ""
                        via_ssid = 0
                        via = ax25_frame[0:6]
                        del ax25_frame[0:6] #remove from frame
                        for byte in via:
                            via_str += chr((byte >> 1) & 0x7F)
                        via_ssid = int((ax25_frame.pop(0) >> 1) & 0x0F)
                        via_cnt = 0
                        for key in ax25.keys():
                            if 'via' in key: via_cnt += 1
                        via_cnt = via_cnt / 2
                        via_call_key = 'via{:d}_call'.format(via_cnt+1)
                        via_ssid_key = 'via{:d}_ssid'.format(via_cnt+1)
                        ax25[via_call_key] = via_str.strip()
                        ax25[via_ssid_key] = via_ssid
                        addr_cnt -= 1

                    ax25['control'] = '0x{:02X}'.format(ax25_frame.pop(0))
                    ax25['pid'] = '0x{:02X}'.format(ax25_frame.pop(0))
                    ax25['info_str'] = str(ax25_frame)

                    print ax25

                    #Lets play with APRS
                    src_str = ax25['src_call']
                    if ax25['src_ssid'] > 0:
                        src_str += "-{:d}".format(ax25['src_ssid'])
                    dest_str = ax25['dest_call']
                    if ax25['dest_ssid'] > 0:
                        dest_str += "-{:d}".format(ax25['dest_ssid'])

                    aprs_str = ""
                    aprs_str += ax25['ts_utc'] + ":"
                    aprs_str += src_str + ">"
                    aprs_str += dest_str
                    for i in range(via_cnt):
                        #SOMETHINGS NOT RIGHT, NOT PRINTING ALL VIA FIELDS
                        aprs_str += ","
                        via_call_key = 'via{:d}_call'.format(i+1)
                        via_ssid_key = 'via{:d}_ssid'.format(i+1)
                        aprs_str += ax25[via_call_key]
                        if ax25[via_ssid_key] > 0:
                            aprs_str += "-" + str(ax25[via_ssid_key])
                    aprs_str += ":"
                    aprs_str += ax25['info_str']



                    print aprs_str

                    ax25_frames.append(ax25)

                ts_str = "" #reset timestamp
                ser_data = bytearray() #reset serial buffer
                packet = False #reset packet flag
        except Exception as e:
            print "Exception", e# -*- coding: utf-8 -*-

        except(KeyboardInterrupt):
            for i,frame in enumerate(ax25_frames):
                print i, frame
            sys.exit()

    sys.exit()


if __name__ == '__main__':
    main()
