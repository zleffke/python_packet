#!/usr/bin/env python
################################################################################
#   Title: KISS NETWORK
# Project: VTGS
# Version: 1.0.0
#    Date: Jan, 2020
#  Author: Zach Leffke, KJ4QLP
# Comments:
#   - Kiss/AX.25 TCP Interface
#   - TX and RX
################################################################################

import threading
import time
import datetime
import json
import numpy
import uuid
import pandas as pd

from logger import *
from network_thread import *
from watchdog_timer import *
from astro_func import *

class Main_Thread(threading.Thread):
    """ docstring """
    def __init__ (self, cfg, name):
        #super(Main_Thread, self).__init__(name=name)
        threading.Thread.__init__(self)
        threading.current_thread().name = "Main_Thread"
        self.setName("Main_Thread")
        self._stop      = threading.Event()
        self.cfg        = cfg

        setup_logger(self.cfg['main_log'])
        self.logger = logging.getLogger(self.cfg['main_log']['name']) #main logger
        self.logger.info("configs: {:s}".format(json.dumps(self.cfg)))

        self.state  = 'BOOT' #BOOT, IDLE, STANDBY, ACTIVE, FAULT, CALIBRATE
        self.state_map = {
            'BOOT':0x00,        #bootup
            'IDLE':0x01,        #threads launched, no connections
            'RUN':0x02,         #client connected
        }

        self.connected = False #Connection Status, Network Thread
        #self.ptt_timer = self.timer = threading.Timer(self.timeout, self.handler)
        self.rx_lat = self.cfg['geo']['rx_lat']
        self.rx_lon = self.cfg['geo']['rx_lon']
        self.rx_alt = self.cfg['geo']['rx_alt']

        self.valid = [] #list of valid packets
        self.out_fp = "/".join([self.cfg['out_path'],self.cfg['out_file']])

    def run(self):
        self.logger.info('Launched {:s}'.format(self.name))
        try:
            while (not self._stop.isSet()):
                if self.state == 'BOOT':
                    self._handle_state_boot()
                elif self.state == 'FAULT':
                    self._handle_state_fault()
                else:# NOT in BOOT or FAULT state
                    if self.state == 'IDLE':  self._handle_state_idle()
                    elif self.state == 'RUN':  self._handle_state_run()
                time.sleep(0.000001)

        except (KeyboardInterrupt): #when you press ctrl+c
            self.logger.warning('Caught CTRL-C, Terminating Threads...')
            self._stop_threads()
            self.logger.warning('Terminating Main Thread...')
            sys.exit()
        except SystemExit:
            self.logger.warning('Terminating Main Thread...')
        sys.exit()

    #---- STATE HANDLERS -----------------------------------
    def _handle_state_run(self):
        if (not self.connected):
            self._set_state('IDLE')
        self._check_thread_queues() #Check for messages from threads

    def _handle_state_idle(self):
        if (self.connected): #Client and Device connected
            self._set_state('RUN')
        self._check_thread_queues() #Check for messages from threads

    def _handle_state_boot(self):
        if self._init_threads():#if all threads activate succesfully
            self.logger.info('Successfully Launched Threads, Switching to IDLE State')
            self._set_state('IDLE')
            time.sleep(1)
        else:
            self.logger.info('Failed to Launched Threads...')
            self._set_state('FAULT')

    def _handle_state_fault(self):
        self.logger.warning("in FAULT state, exiting.......")
        self.logger.warning("Do Something Smarter.......")
        sys.exit()

    def _set_state(self, state):
        self.state = state
        self.logger.info('Changed STATE to: {:s}'.format(self.state))
        #self.watchdog = Watchdog(10, 'PTT Watchdog', self._watchdog_expired)
        #self.watchdog.start()
    #---- END STATE HANDLERS -----------------------------------
    ###############################################################
    #---- CHILD THREAD COMMS HANDLERS & CALLBACKS ----------------------------
    def _process_network_message(self, msg):
        #print (type(msg))
        #print (str(msg))
        #self.watchdog.reset()
        try:
            msg_dict = json.loads(msg)
            if 'altitude' in msg_dict.keys():
                if not (math.isnan(msg_dict['altitude']) or
                        math.isnan(msg_dict['latitude']) or
                        math.isnan(msg_dict['altitude'])):
                    if msg_dict['altitude'] > 0:
                        #RAZEL(deployed_lat,deployed_lon,deployed_alt, balloon_lat,balloon_lon,balloon_alt)
                        razel = RAZEL(self.rx_lat,self.rx_lon,self.rx_alt,
                                      msg_dict['latitude'], msg_dict['longitude'],
                                      msg_dict['altitude']*0.0003048) #convert to km
                        #msg_dict['razel'] = razel
                        msg_dict['range'] = razel['rho_mag']
                        msg_dict['azimuth'] = razel['az']
                        msg_dict['elevation'] = razel['el']
                        #msg_pd = pd.DataFrame(msg_dict)
                        self.valid.append(msg_dict)
                        print (json.dumps(msg_dict, indent=4))
                        print("Updating to JSON File: {:s}".format(self.out_fp))
                        with open(self.out_fp, 'w') as ofp:
                            json.dump(self.valid, ofp, indent = 4)
        except Exception as e:
            print (e)
            print (msg)

    def _watchdog_expired(self):
        print ("---------- WATCHDOG!!!!!---------------------")
        print (len(self.valid))
        out_fp = "/".join([self.cfg['out_path'],self.cfg['out_file']])
        print("Writing to JSON File: {:s}".format(out_fp))
        with open(out_fp, 'w') as ofp:
            json.dump(self.valid, ofp, indent = 4)


    def set_connected_status(self, status): #called by service thread
        self.connected = status
        self.logger.info("Network Connection Status: {0}".format(self.connected))

    def _check_thread_queues(self):
        #check for service message
        if (self.cfg['thread_enable']['network'] and (not self.network_thread.rx_q.empty())): #Received a message from user
            msg = self.network_thread.rx_q.get()
            self._process_network_message(msg)
    ###############################################################
    #---- MAIN THREAD CONTROLS -----------------------------------
    def _init_threads(self):
        try:
            #Initialize Threads
            #print 'thread_enable', self.thread_enable
            self.logger.info("Thread enable: {:s}".format(json.dumps(self.cfg['thread_enable'])))
            for key in self.cfg['thread_enable'].keys():
                if self.cfg['thread_enable'][key]:
                    if key == 'network': #Initialize Service Thread
                        self.logger.info('Setting up Network Thread')
                        if self.cfg['network']['type'] == "TCP":
                            self.network_thread = Thread_TCP_Client(self.cfg['network'], self) #Service Thread
                        self.network_thread.daemon = True
            #Launch threads
            for key in self.cfg['thread_enable'].keys():
                if self.cfg['thread_enable'][key]:
                    if key == 'network': #Start Service Thread
                        self.logger.info('Launching Network Thread...')
                        self.network_thread.start() #non-blocking
            return True
        except Exception as e:
            self.logger.error('Error Launching Threads:', exc_info=True)
            self.logger.warning('Setting STATE --> FAULT')
            self._set_state('FAULT')
            return False

    def _stop_threads(self):
        #stop all threads
        for key in self.cfg['thread_enable'].keys():
            if self.cfg['thread_enable'][key]:
                if key == 'network':
                    self.network_thread.stop()
                    self.logger.warning("Terminated Network Thread.")
                    #self.service_thread.join() # wait for the thread to finish what it's doing
                elif key == 'user': #Initialize Radio Thread
                    #self.user_thread.stop()
                    self.logger.warning("Terminated User Thread...")
                    #self.md01_thread.join() # wait for the thread to finish what it's doing
        self.stop()

    def stop(self):
        self.logger.warning('{:s} Terminating...'.format(self.name))
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
    #---- END MAIN THREAD CONTROLS -----------------------------------
    ###############################################################
