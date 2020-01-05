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

from logger import *
from network_thread import *
from cli_thread import *
from watchdog_timer import *
from ax25_utils import *

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
        self.packets = {}

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
            self._import_packets()
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
    #---- END STATE HANDLERS -----------------------------------
    ###############################################################
    #---- PACKET HANDLERS -----------------------------------
    def _import_packets(self):
        pkt_path = self.cfg['packet']['path']
        pkt_file = self.cfg['packet']['file']
        fp_pkt = '/'.join([pkt_path,pkt_file])
        self.logger.info('Importing Packets from: {:s}'.format(fp_pkt))
        with open(fp_pkt, 'r') as json_data:
            pkt_dict = json.load(json_data)
            json_data.close()
        print(pkt_dict)
        self.packets = []
        for i, pld in enumerate(pkt_dict['payloads']):
            pkt = pkt_dict['header']
            pkt['payload'] = pkt_dict['payloads'][i]
            ax25 = DictToAx25(pkt)
            kiss = Ax25ToKiss(ax25)
            pkt = {
                "index":i,
                "name":pld['name'],
                "hex":kiss.hex()
            }
            self.packets.append(pkt)
        self.logger.info('Imported Packets: {:s}'.format(json.dumps(self.packets)))
        self.user_thread.set_packets(self.packets)
    #---- END PACKET HANDLERS -----------------------------------
    ###############################################################
    #---- CHILD THREAD COMMS HANDLERS & CALLBACKS ----------------------------
    def _process_network_message(self, msg):
        print (msg)

    def _process_user_message(self, msg):
        if ((msg['type']=="CMD") and (msg['cmd']=="SEND")):
            if self.connected:
                #print (msg['msg'])
                self.logger.info("Sending Command: {:s}:{:s}".format(msg['msg']['name'],
                                                                     msg['msg']['hex']))
                self.network_thread.tx_q.put(msg)
            else:
                self.logger.info("Command Not Sent, not connected to endpoint.")

        elif msg['type']=="CTL":
            if msg['cmd']   == 'EXIT': self._stop_threads()
            elif msg['cmd'] == 'STATUS':
                if self.cfg['thread_enable']['network']:
                    self.network_thread.get_tlm()
                    if not self.network_thread.tlm_q.empty():
                        msg = self.network_thread.tlm_q.get()
                        msg['state'] = self.state
                        self.user_thread.rx_q.put(msg)
            elif msg['cmd']=='RESET':
                self.network_thread.tx_q.put(msg)


    def set_connected_status(self, status): #called by service thread
        self.connected = status
        self.logger.info("Network Connection Status: {0}".format(self.connected))

    def _check_thread_queues(self):
        #check for service message
        if (self.cfg['thread_enable']['network'] and (not self.network_thread.rx_q.empty())): #Received a message from user
            msg = self.network_thread.rx_q.get()
            self._process_network_message(msg)
        if (self.cfg['thread_enable']['user'] and (not self.user_thread.cmd_q.empty())): #Received a message from user
            msg = self.user_thread.cmd_q.get()
            self._process_user_message(msg)

    def _ptt_watchdog_expired(self):
        self.logger.info('PTT Watchdog Expired')
        self._set_state('RX')

    def _send_device_msg(self,msg):
        self.logger.info('Sent Signal to {:s}: {:s}'.format(self.cfg['device']['name'], msg))
        self.device_thread.tx_q.put(msg)
    #---- END CHILD THREAD COMMS HANDLERS & CALLBACKS ----------------------------
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
                    elif key == 'user': #Initialize Device Thread
                        self.logger.info('Setting up User Thread')
                        self.user_thread = Simple_CLI(self.cfg['user'], self)
                        self.user_thread.daemon = True
            #Launch threads
            for key in self.cfg['thread_enable'].keys():
                if self.cfg['thread_enable'][key]:
                    if key == 'network': #Start Service Thread
                        self.logger.info('Launching Network Thread...')
                        self.network_thread.start() #non-blocking
                    elif key == 'user': #Initialize Device Thread
                        self.logger.info('Launching User CLI')
                        self.user_thread.start()
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
