#!/usr/bin/env python3
#################################################
#   Title: KISS NETWORK TX
# Project: Multiple (KISS/AX.25)
# Version: 0.0.1
#    Date: Jan, 20202
#  Author: Zach Leffke, KJ4QLP
# Comment:
# - Script for playing KISS Frames from file over TCP connection
# - Packets to send defined with JSON packet definition files
#################################################

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
    parser = argparse.ArgumentParser(description="AX.25/KISS Client playback over TCP Socket",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    cwd = os.getcwd()
    cfg_fp_default = '/'.join([cwd, 'config'])
    cfg = parser.add_argument_group('Configuration File')
    cfg.add_argument('--cfg_path',
                       dest='cfg_path',
                       type=str,
                       default=cfg_fp_default,
                       help="Configuration File Path",
                       action="store")
    cfg.add_argument('--cfg_file',
                       dest='cfg_file',
                       type=str,
                       default="kiss_net_tx_config.json",
                       help="Configuration File",
                       action="store")
    cwd = os.getcwd()
    pkt_fp_default = '/'.join([cwd, 'packets'])
    log_fp_default = '/'.join([cwd, 'log'])
    pkt = parser.add_argument_group('Packet File Parameters')
    pkt.add_argument('--pkt_path',
                       dest='pkt_path',
                       type=str,
                       default=pkt_fp_default,
                       help="File Path to packet definitions",
                       action="store")
    pkt.add_argument('--pkt_file',
                       dest='pkt_file',
                       type=str,
                       default="odu_hello.json",
                       help="Packet File",
                       action="store")
    pkt.add_argument('--rx_pkt_file',
                       dest='rx_pkt_file',
                       type=str,
                       default="odu_hello.json",
                       help="Packet File",
                       action="store")


    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------
    os.system('reset')
    #Import Configs
    fp_cfg = '/'.join([args.cfg_path,args.cfg_file])
    if not os.path.isfile(fp_cfg) == True:
        print ('ERROR: Invalid Configuration File: {:s}'.format(fp_cfg))
        sys.exit()
    print ('Importing configuration File: {:s}'.format(fp_cfg))
    with open(fp_cfg, 'r') as json_data:
        cfg = json.load(json_data)
        json_data.close()
    cfg['startup_ts'] = startup_ts
    print ("CONFIGS", '\n\r', json.dumps(cfg, indent=4))
    #Import Packet(s)
    fp_pkt = '/'.join([args.pkt_path,args.pkt_file])
    if not os.path.isfile(fp_pkt) == True:
        print ('ERROR: Invalid Configuration File: {:s}'.format(fp_pkt))
        sys.exit()
    print ('Importing configuration File: {:s}'.format(fp_pkt))
    with open(fp_pkt, 'r') as json_data:
        pkt_json = json.load(json_data)
        json_data.close()
    print (json.dumps(pkt_json, indent=4))

    pkt = bytearray()

    sys.exit()

    # connected = False
    # print 'Creating TCP Client Socket'
    # repeat = 0
    # while 1:
    #     try:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #         sock.setblocking(1)
    #         sock.connect((args.ip, args.port))
    #         connected = True
    #         print "Connected to: [{:s}:{:d}]".format(args.ip, args.port)
    #     except:
    #         print "Failed to Connect to: [{:s}:{:d}]".format(args.ip, args.port)
    #         print "Is the server side running?...."
    #         print "Attempting to reconnect in {:f} seconds...".format(args.retry)
    #         time.sleep(args.retry)
    #
    #     while (connected):
    #             try:
    #                 data = sock.recv(1024)
    #                 ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    #                 print "\n{:s} | RX: {:s}".format(ts, binascii.hexlify(data))
    #                 print "delaying {:3.3f} seconds...".format(args.delay)
    #                 time.sleep(args.delay)
    #                 ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    #                 print "{:s} | TX: {:s}".format(ts, binascii.hexlify(data))
    #                 sock.sendall(data)
    #             except socket.error, v:
    #                 connected = False
    #                 errorcode=v[0]
    #                 if errorcode==errno.EPIPE:  #Client disconnected
    #                     print 'Client Disconnected'
    #                     repeat = 0
    #                     break
    #     print 'Finished Playback'
    #     repeat = 0
    # sys.exit()


if __name__ == '__main__':
    main()
