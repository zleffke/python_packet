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
import binascii
import socket
import errno

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
    parser = argparse.ArgumentParser(description="Play KISS frames over TCP connection")

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
    ctl = parser.add_argument_group('Control Parameters')
    ctl.add_argument('--rate',
                       dest='rate',
                       type=float,
                       default=1.0,
                       help="Playback Rate, seconds",
                       action="store")
    ctl.add_argument('--repeat',
                       dest='repeat',
                       type=int,
                       default=1,
                       help="Repeat file, 0=no",
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
                       required = True)

    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------

    fp = '/'.join([args.kiss_path,args.kiss_file])
    if not os.path.isfile(fp) == True:
        print 'ERROR: Invalid Configuration File: {:s}'.format(fp)
        sys.exit()

    ser_buff = bytearray()
    kiss_frames = []
    #--Read in KISS Frames from File
    #--Create List of Kiss Frames
    print 'reading KISS frames from:', fp
    with open(fp, 'rb') as f:
        while 1:
            b = f.read(1)
            if not b: #eof
                print 'eof'
                break
            if ord(b) == FEND: #beginning of KISS frame
                #print 'Detected FEND'
                ser_buff.append(b)
                kiss_flag = True
                while (kiss_flag):
                    char = f.read(1)
                    ser_buff.append(char)
                    if ord(char) == FEND: #end of kiss frame
                        kiss_frames.append(ser_buff)
                        ser_buff = bytearray()
                        kiss_flag = False
    f.close()
    print 'Detected {:d} KISS Frames'.format(len(kiss_frames))

    #--Wait for connection from Client
    #--Playback frames at the specified rate
    repeat = 1
    while 1:
        print 'Creating TCP Server'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((args.ip, args.port))
        sock.listen(1)
        print "Playback begins on client connection"
        print "Playback rate [s]: {:f}".format(args.rate)
        print "Playback repeat: {:d}".format(args.repeat)
        print "Server listening on: [{:s}:{:d}]".format(args.ip, args.port)
        conn, client = sock.accept()
        print "Connection from client: [{:s}:{:d}]".format(client[0], client[1])
        print "Beginning playback..."
        while repeat:
            repeat = args.repeat
            for i,f in enumerate(kiss_frames):
                print i, binascii.hexlify(f)
                try:
                    conn.sendall(bytearray(f))
                except socket.error, v:
                    errorcode=v[0]
                    if errorcode==errno.EPIPE:  #Client disconnected
                        print 'Client Disconnected'
                        repeat = 0
                        break
                time.sleep(args.rate)
        conn.close()
        print 'Finished Playback'
        repeat = 1
    sys.exit()


if __name__ == '__main__':
    main()
