#!/usr/bin/env python
#Script for playing KISS Frames from file over TCP connection

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

    kiss = parser.add_argument_group('KISS File Parameters')
    kiss.add_argument('--kiss_path',
                       dest='kiss_path',
                       type=str,
                       default=os.getcwd(),
                       help="KISS File Path",
                       action="store")

    kiss.add_argument('--kiss_file',
                       dest='kiss_file',
                       type=str,
                       default="",
                       help="KISS File",
                       action="store",
                       required = False)

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
    except:
        print "Failed to Connect to: [{:s}:{:d}]".format(args.ip, args.port)
        print "Is the server side running?...."
        sys.exit()

    packet_count = 0
    ax25_frames = []
    while connected:
        #try:
        data = sock.recv(1024)
        ts_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f UTC")
        if data:
            packet_count += 1
            print "\nPacket Received: {:d}".format(packet_count)
            print "Time Stamp [UTC]:", ts_str
            kiss_frame = bytearray(data)
            if kiss_frame[0] == FEND and kiss_frame[-1]==FEND: #KISS Frame Detected
                print '  KISS Frame: {:s}'.format(str(binascii.hexlify(kiss_frame)))
                ax25 = {}
                ax25['kiss_hex'] = binascii.hexlify(kiss_frame)
                del kiss_frame[0]
                del kiss_frame[-1]
                new_kiss = bytearray()
                for i,byte in enumerate(kiss_frame):
                    #print hex(byte)
                    if byte == FESC:
                        print 'Detected FESC'
                        next_byte = kiss_frame[i+1]
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
                kiss_command = new_kiss.pop(0)
                kiss_port = (kiss_command >> 4) & 0x0F #Hi Nibble
                kiss_cmd = (kiss_command) & 0x0F #Low Nibble
                ax25['kiss_port'] = '0x{:02X}'.format(kiss_port)
                ax25['kiss_cmd'] = '0x{:02X}'.format(kiss_cmd)
                ax25_frame = new_kiss #since we've popped the last KISS character, rename the variable
                print 'KISS Port: 0x{:02X}'.format(kiss_port)
                print 'KISS Command: 0x{:02X}'.format(kiss_cmd)
                print ' AX.25 Frame: {:s}'.format(str(binascii.hexlify(ax25_frame)))
                print ax25_frame


                ax25['uuid'] = uuid.uuid4().hex
                ax25['ts_utc'] = ts_str
                ax25['ax25_hex'] = str(binascii.hexlify(ax25_frame))
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
                ax25['payload'] = binascii.hexlify(ax25_frame)
                #ax25['info_str'] = str(ax25_frame)

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
                via_cnt = 0
                for key in ax25.keys():
                    if 'via' in key: via_cnt += 1
                via_cnt = via_cnt / 2
                print "VIA COUNT:", via_cnt
                for i in range(via_cnt):
                    #SOMETHINGS NOT RIGHT, NOT PRINTING ALL VIA FIELDS
                    aprs_str += ","
                    via_call_key = 'via{:d}_call'.format(i+1)
                    via_ssid_key = 'via{:d}_ssid'.format(i+1)
                    aprs_str += ax25[via_call_key]
                    if 'WIDE' in ax25[via_call_key]:
                        if ax25[via_ssid_key] > 0:
                            aprs_str += "-" + str(ax25[via_ssid_key])
                        else:  aprs_str += "*"
                    elif ax25[via_ssid_key] > 0:
                        aprs_str += "-" + str(ax25[via_ssid_key])
                aprs_str += ":"
                aprs_str += str(binascii.unhexlify(ax25['payload']))



                print "APRS:", aprs_str
                #ax25['aprs'] = aprs_str

                try:
                    ax25_json = json.dumps(ax25, indent=4)
                    #print ax25_json
                    ax25_frames.append(ax25)
                    ax25_frames_json = json.dumps(ax25_frames, indent=4)
                    print ax25_frames_json
                except:
                    pass



    sys.exit()


if __name__ == '__main__':
    main()
