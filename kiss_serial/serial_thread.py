#!/usr/bin/env python
##################################################
# Title: Serial KISS Interface
# Author: Zachary James Leffke
# Description:
#   Threaded serial interface for KISS
# Generated: May 12, 2014
##################################################

import threading
import datetime as dt
import os
import serial
import numpy
import time
from Queue import Queue
from logger import *

FEND  = 0xC0
FESC  = 0xDB
TFEND = 0xDC
TFESC = 0xDD

class SerialThread(threading.Thread):
    def __init__ (self, cfg, logger, parent=None):
        threading.Thread.__init__(self, name='Serial_Thread')
        self._stop      = threading.Event()
        self.parent = parent
        self.dev    = cfg['dev']
        self.baud   = cfg['baud']

        self.logger = logger #Main Logger

        self.rx_q   = Queue() #Messages received from radio
        self.tx_q   = Queue() #Messages to send to radio

        self.rx_pkt_cnt = numpy.uint16(0)
        self.tx_pkt_cnt = numpy.uint16(0)

        self.tlm = {} #Current Telemetry Status, including


    def run(self):
        print "Serial Thread..."
        self.logger.info('Serial Thread...')
        self.ser    = serial.Serial(self.dev, self.baud, timeout=0, write_timeout=0)
        self.logger.info('Opened Serial Port: {:s}'.format(self.dev))
        self.ser.reset_input_buffer()
        if (self.ser.isOpen()):#returns 1 on success
            while (not self._stop.isSet()):
                [frame,rx_ts]=self._read_serial()
                if frame:
                    print rx_ts, binascii.hexlify(frame)
                time.sleep(0.1)
                # try:
                #     self._radio_ctl_response()
                #     if (not self.tx_q.empty()): #new message in Queue for transmission
                #         tx_q = self.tx_q.get()
                #         self._send_message(tx_q)
                # except Exception as e:
                #    # Something else happened, handle error, exit, etc.
                #     self.logger.warning('Failure: {:s}'.format(e))
                #     print e
        self.logger.warning('Serial Thread Terminating...')
        sys.exit()

    def _read_serial(self):
        frame = bytearray()
        if self.ser.in_waiting > 0:  #Serial data in buffer
            ts = dt.datetime.utcnow()
            time.sleep(0.01) # make sure buffer is full
            while self.ser.in_waiting > 0: #churn through buffer
                char = self.ser.read()
                if ord(char) == FEND: #KISS FRAME detected
                    print '--KISS START--'
                    kiss_flag = True
                    frame.append(char)
                    while (kiss_flag):  #inside kiss frame
                        char = self.ser.read()
                        #print type(char), binascii.hexlify(char)
                        frame.append(char)
                        if ord(char) == FEND: #END OF KISS FRAME
                            print "--KISS STOP--"
                            kiss_flag = False
                    break
            return [frame, ts]
        else:
            return None, None

    def _read_serial_OLD(self):
        frame = bytearray()
        if self.ser.in_waiting > 0:  #Serial data in buffer
            ts = dt.datetime.utcnow()
            time.sleep(0.01) # make sure buffer is full
            while self.ser.in_waiting > 0: #churn through buffer
                char = self.ser.read()
                if ord(char) == FEND: #KISS FRAME detected
                    kiss_flag = True
                    while (kiss_flag):
                        char = self.ser.read()
                        if ord(char) == FESC: #ESCAPE SEQUENCE DETECTED
                            esc_char = self.ser.read()
                            if ord(esc_char) == TFESC: #Data = FESC
                                frame.append(FESC)
                            elif ord(esc_char) == TFEND: #Data = FEND
                                frame.append(FEND)
                        elif ord(char) == FEND: #end of kiss frame
                            kiss_flag = False
                            self.ser.reset_input_buffer()
                        elif len(frame) > 100: #protect against out of sync?
                            kiss_flag = False
                            self.ser.reset_input_buffer()
                        else:
                            frame.append(char)
            return [frame, ts]
        else:
            return None, None

    def _send_message(self, msg):
        #create message
        self.tx_pkt_cnt += numpy.uint16(1)
        msg = struct.pack('>H', self.tx_pkt_cnt) + msg
        #print "sending to radio:", len(msg), binascii.hexlify(msg)
        self._write_serial_tx(msg)

    def _write_serial_tx(self, msg):
        #writes KISS Framed message
        if type(msg) != 'bytearray': msg = bytearray(msg) #ensure bytearray type for KISS Framing
        #print type(msg), binascii.hexlify(msg)

        tx_msg = bytearray()
        tx_msg =  struct.pack('<B', FEND)
        tx_msg += struct.pack('<B', 0x00)
        for item in msg:
            if item == FEND:
                #print 'FEND DETECT'
                tx_msg += struct.pack('<B', FESC)
                tx_msg += struct.pack('<B', TFEND)
            elif item == FESC:
                #print 'FESC DETECT'
                tx_msg += struct.pack('<B', FESC)
                tx_msg += struct.pack('<B', TFESC)
            else:
                #print binascii.hexlify(item)
                tx_msg += struct.pack('<B',item)
        tx_msg += struct.pack('<B', int(FEND))
        tx_msg = bytearray(tx_msg)
        print "Sending to Radio for TX:", len(tx_msg), binascii.hexlify(tx_msg)
        self.tx_data_logger.info(binascii.hexlify(tx_msg))
        self.ser.write(tx_msg)
        time.sleep(0.1)

    def stop(self, caller=None):
        print "Serial Thread Terminating..."
        self.logger.info("Serial Thread Terminating...")
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
