#!/usr/bin/env python
##################################################
# Title: Serial KISS Interface, Threaded
# Author: Zachary James Leffke
# Description: Threaded interface for KISS
# Generated: Oct 2017
##################################################


import os
import sys
import string
import serial
import math
import time
import numpy

import argparse
#from threading import Thread
from main_thread import *
import datetime

def main(cfg):
    main_thread = Main_Thread(cfg)
    main_thread.daemon = True
    main_thread.run()
    sys.exit()

if __name__ == '__main__':
    """ Main entry point to start the service. """
    startup_ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    #--------START Command Line argument parser------------------------------------------------------
    parser = argparse.ArgumentParser(description="Simple Serial TNC Connect and Print Program")
    ser = parser.add_argument_group('Serial Port Parameters')
    ser.add_argument('--device',
                       dest='dev',
                       type=str,
                       default="/dev/ttyUSB0",
                       help="Path to device",
                       action="store")
    ser.add_argument('--baud',
                       dest='baud',
                       type=int,
                       default=9600,
                       help="Baud rate of serial port connection",
                       action="store")

    log = parser.add_argument_group('Logging Parameters')
    log.add_argument('--log_path',
                       dest='log_path',
                       type=str,
                       default="/log/kiss_serial",
                       help="Logging Path",
                       action="store")
    log.add_argument('--log_ts',
                       dest='log_ts',
                       type=str,
                       default=startup_ts,
                       help="Logging timestamp",
                       action="store")
    log.add_argument('--log_flag',
                       dest='log_flag',
                       type=int,
                       default=0,
                       help="Logging Flag, 0 = Disabled, 1= Enabled",
                       action="store")

    args = parser.parse_args()
    #--------END Command Line argument parser------------------------------------------------------

    cfg = vars(args)


    main(cfg)
    sys.exit()
