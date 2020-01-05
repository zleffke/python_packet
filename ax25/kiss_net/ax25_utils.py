#!/usr/bin/env python3
#################################################
#   Title: KISS NETWORK TX
# Project: Multiple (KISS/AX.25)
# Version: 0.0.1
#    Date: Jan, 20202
#  Author: Zach Leffke, KJ4QLP
# Comment:
# - Helper utilities for manipulating AX.25 and KISS Frames
#################################################
import json
import numpy
import logging
import binascii

# FEND = 0xC0
# FESC = 0xDB
# TFEND = 0xDC
# TFESC = 0xDD

FEND = numpy.uint8(0xc0)
FESC = numpy.uint8(0xdb)
TFEND = numpy.uint8(0xdc)
TFESC = numpy.uint8(0xdd)

def ImportPackets(fp_pkt):
    pass

def DictToAx25(pkt_dict):
    ax25 = bytearray()
    #--Handle Destination Call----
    for char in pkt_dict['dest_call']: ax25.append(((ord(char) << 1) & 0xFE))
    #--Handle Destination SSID----
    ax25.append(((pkt_dict['dest_ssid'] << 1) | 0x60))
    #--Handle Source Call----
    for char in pkt_dict['src_call']: ax25.append(((ord(char) << 1) & 0xFE))
    #--Handle Source SSID----
    ax25.append(((pkt_dict['src_ssid'] << 1) | 0x61))
    #--Handle Control Byte----
    ax25.append(0x03) #Contol
    #--Handle PID Byte----
    ax25.append(0xF0) #PID
    #--Handle Message----
    if pkt_dict['payload']['syntax'] == "ascii":
        ax25.extend(pkt_dict['payload']['message'].encode())
    elif pkt_dict['payload']['syntax'] == "hex":
        ax25.extend(binascii.unhexlify(pkt_dict['payload']['message']))
    else:
        pass
    # print ("AX.25 Frame: {:s}".format(ax25.hex()))
    return ax25

def Ax25ToKiss(ax25, log_name = None):
    if log_name:
        log = logging.getLogger(log_name)
        log.info('Converting AX.25 to KISS...')
    kiss = bytearray()
    kiss.append(FEND)
    kiss.append(numpy.uint8(0))
    for i,x in enumerate(ax25):
        if x == FESC:
            if log_name: log.info("    Detected FESC at index: {:d}, inserting FESC, FESC".format(i))
            kiss.append(FESC)
            kiss.append(TFESC)
        elif x == FEND:
            if log_name: log.info("    Detected FEND at index: {:d}, inserting FESC, TFEND".format(i))
            kiss.append(FESC)
            kiss.append(TFEND)
        else:
            kiss.append(numpy.uint8(x))
    kiss.append(FEND)
    return kiss

def KissToAx25(kiss, log_name = None):
    if log_name:
        log = logging.getLogger(log_name)
        log.info('Decoding KISS to AX.25...')
    buff = bytearray()
    escape_flag = False
    for i,byte in enumerate(kiss):
        if byte == FEND:
            if log_name: log.info("    Detected FEND at index: {:d}".format(i))
        elif i == 1:
            kiss_port = (byte >> 4) & 0x0F #Hi Nibble
            kiss_cmd = (byte) & 0x0F #Low Nibble
            if log_name:
                log.info("       KISS Port: 0x{:02X}".format(kiss_port))
                log.info("    KISS Command: 0x{:02X}".format(kiss_cmd))
        elif escape_flag:
            if byte == TFEND:
                if log_name: log.info("    detected TFEND at index: {:d}, inserting FEND".format(i))
                buff.append(FEND)
            elif byte == TFESC:
                if log_name: log.info("    detected TFESC at index: {:d}, inserting FESC".format(i))
                buff.append(FESC)
            escape_flag = False
        elif byte == FESC:
            escape_flag = True
            if log_name: log.info('    Detected FESC at index: {:d}'.format(i))
        else:
            buff.append(byte)
    return buff, kiss_port, kiss_cmd
