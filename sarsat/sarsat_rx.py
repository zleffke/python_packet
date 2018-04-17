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

#from optparse import OptionParser
import argparse

def main():
    """ Main entry point to start the service. """

    startup_ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    #--------START Command Line argument parser------------------------------------------------------
    parser = argparse.ArgumentParser(description="Simple Serial TNC Connect and Print Program")

    net = parser.add_argument_group('Network Parameters')
    net.add_argument('--ip',
                       dest='ip',
                       type=str,
                       default='0.0.0.0',
                       help="IP Address",
                       action="store")
    net.add_argument('--port',
                       dest='port',
                       type=int,
                       default=8000,
                       help="IP Address",
                       action="store")

    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------
    connected = False


    print 'Creating TCP Client Socket'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(1)
    try:
        sock.connect((args.ip, args.port))
        connected = True
        print 'Connected to Server'
    except:
        print "Failed to Connect to: [{:s}:{:d}]".format(args.ip, args.port)
        print "Is the server side running?...."
        sys.exit()

    packet_count = 0
    ax25_frames = []
    while connected:
        #try:
        data = sock.recv(24) #SARP Message should be 24 bytes long
        ts_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        if data:
            packet_count += 1
            print "\n Packet Received: {:d}".format(packet_count)
            print "Time Stamp [UTC]:", ts_str
            sarp_msg = bytearray(data)
            print "SARP Message Hex: {:s}".format(binascii.hexlify(sarp_msg))

            sync_word = [0] * 2
            sarp = {}
            sarp['ts_str'] = ts_str
            sarp['hex_str'] = binascii.hexlify(sarp_msg)
            sync_word[0] = sarp_msg[0]
            sync_word[1] = sarp_msg[1] & 0xF0
            sarp['sync_word'] = "0x"+"".join("{:x}".format(c) for c in sync_word)

            pseudo = (sarp_msg[1] >> 3) & 0x01
            if pseudo:
                sarp['pseudo'] = 'pseudo-message'
            else:
                sarp['pseudo'] = 'beacon-message'

            dru = (sarp_msg[1] >> 1) & 0x03
            dru = int(dru)
            sarp['dru'] = dru

            msg_format = sarp_msg[1] & 0x01
            if msg_format:
                sarp['format'] = 'long-message'
            else:
                sarp['format'] = 'short-message'

            latest = (sarp_msg[2] >> 7) & 0x01
            if latest:
                sarp['latest'] = 'most recent msg, playback'
            else:
                sarp['latest'] = 'others'

            rt_pb = (sarp_msg[2] >> 6) & 0x01
            if latest:
                sarp['rt_pb'] = 'real time'
            else:
                sarp['rt_pb'] = 'playback'

            level = sarp_msg[2] & 0x3F
            sarp['level_dbm'] = 0.564 * level - 140

            s = 99360.0/5203205.0
            md =[0] + list(sarp_msg[3:6])
            #print md
            #print len(md), md
            md = ((numpy.uint32(struct.unpack('<I',bytearray(md)))[0] >> 1) & 0x7FFFFF)
            #print md
            #timecode is temporary until conversion equation can be understood
            tc_1s = bin(md).count("1")
            print bin(md), tc_1s
            sarp['timecode'] = md

            tc_parity = sarp_msg[5] & 0x01
            sarp['timecode_valid'] = (tc_1s%2==tc_parity)

            if sarp['format'] == 'short-message':
                beacon_data = sarp_msg[6:18]
                sarp['beacon_data'] = binascii.hexlify(beacon_data)
                dw = [0] + list(sarp_msg[18:21])
                dw_parity = sarp_msg[20] & 0x01
                sarp['zero_word'] = binascii.hexlify(sarp_msg[21:])
            elif sarp['format'] == 'long-message':
                beacon_data = sarp_msg[6:21]
                sarp['beacon_data'] = binascii.hexlify(beacon_data)
                dw = [0] + list(sarp_msg[21:])
                dw_parity = sarp_msg[23] & 0x01

            dw = ((numpy.uint32(struct.unpack('<I',bytearray(dw)))[0] >> 1) & 0x7FFFFF)
            dw_1s = bin(dw).count("1")
            sarp['doppler_valid'] = (dw_1s%2==dw_parity)

            a = 1.0/(pow(2,19)*624)
            f_r = 5203205.0
            #b = 78 + (1/pow(2,26)) + (16.0/624.0) + (15.5/(pow(2,24)*624))
            b = 78.02564104137
            print b
            f_in = f_r *((a*dw) + b)

            sarp['doppler'] = f_in

            print sarp

            # new_kiss = bytearray()
            # kiss_command = new_kiss.pop(0)
            # kiss_port = (kiss_command >> 4) & 0x0F #Hi Nibble
            # kiss_cmd = (kiss_command) & 0x0F #Low Nibble
            # ax25['kiss_port'] = '0x{:02X}'.format(kiss_port)
            # ax25['kiss_cmd'] = '0x{:02X}'.format(kiss_cmd)
            # ax25_frame = new_kiss #since we've popped the last KISS character, rename the variable
            # print 'KISS Port: 0x{:02X}'.format(kiss_port)
            # print 'KISS Command: 0x{:02X}'.format(kiss_cmd)
            # print ' AX.25 Frame: {:s}'.format(str(binascii.hexlify(ax25_frame)))
            # print ax25_frame

    sys.exit()


if __name__ == '__main__':
    main()
