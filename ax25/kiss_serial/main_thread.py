#!/usr/bin/env python
#############################################
#   Title: C2 Main Thread                   #
# Project: TRIPPWIRE                        #
# Version: 1.0                              #
#    Date: Oct 2017                         #
#  Author: Zach Leffke, KJ4QLP              #
# Comment:                                  #
#   Main Command and Control Thread         #
#   Handles State machine of C2             #
#############################################

import threading
import os
import math
import sys
import string
import time
import socket
import json

from optparse import OptionParser
from datetime import datetime as date
import datetime as dt

from logger import *
from serial_thread import *

class Main_Thread(threading.Thread):
    def __init__ (self, cfg):
        threading.Thread.__init__(self, name = 'Main_Thread')
        self._stop      = threading.Event()
        self.cfg = cfg

        self.main_log_fh = setup_logger('main', ts=cfg['log_ts'], log_path=cfg['log_path'])
        self.logger = logging.getLogger('main') #main logger

        self.state  = 'BOOT' #BOOT, ACTIVE

    def run(self):
        print "Main Thread Started..."
        self.logger.info('Launched main thread')
        try:
            while (not self._stop.isSet()):
                if self.state == 'BOOT':
                    #C2 activating for the first time
                    #Activate all threads
                    #State Change:  BOOT --> STANDBY
                    #All Threads Started
                    if self._init_threads():#if all threads activate succesfully
                        self.logger.info('Successfully Launched Threads, Switching to ACTIVE State')
                        #self.set_state_standby()
                        self.set_state('ACTIVE')
                    else:
                        self.set_state('FAULT')
                    pass
                elif self.state == 'ACTIVE':
                    print 'ACTIVE'
                    #Describe ACTIVE here
                    #read uplink Queue from C2 Radio thread
                    # if (not self.c2_radio_thread.rx_q.empty()): #Uplink Received!
                    #     up_msg = self.c2_radio_thread.rx_q.get()
                    #     self._process_rx_command(up_msg)
                    # if (not self.fc_handler.rx_q.empty()): #Received a message from flight computer
                    #     fc_msg = self.fc_handler.rx_q.get()
                    #     self._process_fc_message(fc_msg)
                    # #if (not self.dbg_handler.rx_q.empty()): #Received a message from debug interface computer
                    # #    dbg_msg = self.dbg_handler.rx_q.get()
                    # #    self._process_dbg_message(dbg_msg)
                    # if (not self.ins_msg_thread.ins_q.empty()): #INS Message ready to beacon
                    #     ins_msg = self.ins_msg_thread.ins_q.get()
                    #     if (ins_msg):
                    #         self._beacon_ins_message(ins_msg)
                    #     else:
                    #         self.logger.info('INS Message empty, no Beacon')
                    #         ts = dt.datetime.utcnow().strftime("%Y%m%d %H%M%S.%f")
                    #         self._beacon_ins_message_invalid(ts)

                time.sleep(1)

        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            print "\nCaught CTRL-C, Killing Threads..."
            self.logger.warning('Caught CTRL-C, Terminating Threads...')
            #self.gps_thread.stop(self.name)
            #self.gps_thread.join() # wait for the thread to finish what it's doing
            self.serial_thread.stop(self.name)
            self.serial_thread.join() # wait for the thread to finish what it's doing
            
            self.logger.warning('Terminating Main Thread...')

            sys.exit()
        sys.exit()




    def _init_threads(self):
        try:
            #Initialize Serial Thread
            self.logger.info('Setting up Serial Thread')
            self.serial_thread = SerialThread(self.cfg, self.logger, self) #Serial Thread
            self.serial_thread.daemon = True

            #Launch threads
            self.logger.info('Launching Serial Thread')
            self.serial_thread.start() #non-blocking

            return True
        except Exception as e:
            self.logger.warning('Error Launching Threads:')
            self.logger.warning(str(e))
            self.logger.warning('Setting STATE --> FAULT')
            self.state = 'FAULT'
            return False

    #---C2 STATE FUNCTIONS----

    def set_state(self, state):
        self.state = state
        self.logger.info('Changed STATE to: {:s}'.format(self.state))
        if self.state == 'ACTIVE':
            time.sleep(5)
        if self.state == 'FAULT':
            pass
        #time.sleep(0.1)

    def get_state(self):
        return self.state
    #---END C2 STATE FUNCTIONS----

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | "

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
