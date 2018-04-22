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

from sarsat_protocol_decoders import *

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
            sarp = {}
            packet_count += 1
            print "Packet Received: {:d}".format(packet_count)
            print "Time Stamp [UTC]:", ts_str
            sarp_msg = bytearray(data)
            print "SARP Message Hex: {:s}".format(binascii.hexlify(sarp_msg))
            sync_word = [0] * 2
            sarp['ts_str'] = ts_str
            sarp['pkt_cnt'] = packet_count
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
            #print bin(md), tc_1s
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
            f_in = f_r *((a*dw) + b)

            sarp['doppler'] = f_in
            sarp['doppler_offset'] = f_in - 406.0e6

            if sarp['doppler_valid'] and sarp['timecode_valid']:
                print "\n----VALID--------------------------------------------"
                sarp_bits = bitarray.bitarray(endian='little')
                #sarp_bits.frombytes(bytearray(sarp_msg))
                for b in bytearray(binascii.unhexlify(sarp['beacon_data'])):
                    a = bitarray.bitarray('{0:08b}'.format(b))
                    sarp_bits.extend(a)

                #print len(sarp_bits), sarp_bits.to01()

                if sarp['format'] == 'short-message':
                    sarp_bits = sarp_bits[:87]
                elif sarp['format'] == 'long-message':
                    sarp_bits = sarp_bits[:119]
                #print len(sarp_bits), sarp_bits.to01()

                bcn_bits = {}
                bcn_bits['protocol_flag']    = sarp_bits[0:1].to01()
                bcn_bits['country_code']     = sarp_bits[1:11].to01()
                id_plus_pos = sarp_bits[11:60]
                bcn_bits['id_plus_pos']      = sarp_bits[11:60].to01()
                bcn_bits['bch_1']            = sarp_bits[60:81].to01()
                if sarp['format'] == 'short-message':
                    bcn_bits['em_ntnl_supp']     = sarp_bits[81:].to01()
                elif sarp['format'] == 'long-message':
                    bcn_bits['pdf_2']     = sarp_bits[81:107].to01()
                    bcn_bits['bch_2']     = sarp_bits[107:].to01()

                country_code = sarp_bits[1:11]

                # print country_code.to01(), \
                #       binascii.hexlify(country_code.tobytes()), \
                #       struct.unpack(">H", country_code)[0]

                cc = [0] * 2
                cc_rev = country_code.copy()
                cc_rev.reverse()
                cc[0] = ord(cc_rev.tobytes()[0])
                cc[1] = ord(cc_rev.tobytes()[1])
                cc = bytearray(cc)
                bcn_bits["cc_int"] = struct.unpack("<H", cc)[0]

                protocol_flag = sarp_bits[0:1].tobytes()
                #print binascii.hexlify(protocol_flag)

                id_plus_pos = sarp_bits[11:60]


                if ord(protocol_flag) & 0x01:
                    print "user or user-location protocols"
                    prot_code = id_plus_pos[0:3]

                else:
                    print "standard/national protocols"
                    prot_code = id_plus_pos[0:4]
                #print prot_code.to01()

                #User and USer Location Protocols
                if prot_code.to01() == "000":
                    print "Orbitography Protocol"
                elif prot_code.to01() == "001":
                    print "ELT - Aviation User Protocol"
                    decode_aviation_user(id_plus_pos)
                elif prot_code.to01() == "010":
                    print "EPIRB - Maritime User Protocol"
                    decode_maritime_user(id_plus_pos)
                elif prot_code.to01() == "011":
                    print "Serial User Protocol"
                elif prot_code.to01() == "100":
                    print "National User Protocol"
                elif prot_code.to01() == "101":
                    print "Spare"
                if prot_code.to01() == "110":
                    print "EPIRB - Radio Call Sign User Protocol"
                    decode_radio_callsign_user(id_plus_pos)
                if prot_code.to01() == "111":
                    print "Test User Protocol"

                #Standard Location and National Protocols
                if prot_code.to01() == "0010":
                    print "EPIRB - MMSI/Location Protocol"
                elif prot_code.to01() == "0011":
                    print "ELT - 24-bit Address/Location Protocol"
                elif prot_code.to01() == "0100":
                    print "Serial Location Protocol: ELT - serial"
                elif prot_code.to01() == "0101":
                    print "Serial Location Protocol: ELT - aircraft operator designator"
                elif prot_code.to01() == "0110":
                    print "Serial Location Protocol: EPIRB - serial"
                elif prot_code.to01() == "0111":
                    print "Serial Location Protocol: PLB - serial"
                elif prot_code.to01() == "1100":
                    print "Ship Security"
                elif prot_code.to01() == "1000":
                    print "National Location Protocol: ELT"
                elif prot_code.to01() == "1010":
                    print "National Location Protocol: EPIRB"
                elif prot_code.to01() == "1011":
                    print "National Location Protocol: PLB"
                elif prot_code.to01() == "1110":
                    print "Standard Test Location Protocol"
                elif prot_code.to01() == "1111":
                    print "National Test Location Protocol"
                elif prot_code.to01() == "1101":
                    print "RLS Location Protocol"
                elif (prot_code.to01() == "0000") or (prot_code.to01() == "0001"):
                    print "Orbitography"
                elif prot_code.to01() == "1001":
                    print "Spare"

                #print json.dumps(sarp, indent=4)
                #print json.dumps(bcn_bits, indent=4)
                print "----VALID--------------------------------------------\n"

    sys.exit()


if __name__ == '__main__':
    main()
