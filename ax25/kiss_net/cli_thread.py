#!/usr/bin/env python3
################################################################################
#   Title: KISS Network
# Project: VTGS
# Version: 1.0.0
#    Date: Jan, 2020
#  Author: Zach Leffke, KJ4QLP
# Comments:
#   -This is the user interface thread
################################################################################

import threading
import time
import socket
import errno
import json
import cmd

from queue import Queue
from logger import *
from ax25_utils import *

class Simple_CLI(cmd.Cmd, threading.Thread):
    def __init__(self, cfg, parent):
        super().__init__(completekey="tab", stdin=None, stdout=None)
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.cfg    = cfg
        self.parent = parent
        self.setName(self.cfg['thread_name'])
        self.logger = logging.getLogger(self.cfg['main_log'])

        self.cmd_q = Queue()
        self.rx_q = Queue()
        self.logger.info("Initializing {}".format(self.name))

        self.packets = self._initialize_packets()
        self.prompt='KISS_NET> '

    def run(self):
        time.sleep(2)
        os.system('reset')
        self.cmdloop('Send KISS Packets over a Network Connection')
        self.logger.warning('{:s} Terminated'.format(self.name))

    def do_list(self, line):
        ''' List avaialable packets '''

        if self.packets is not None:
            #for pkt_key in self.packets
            length = 0
            for i,cmd in enumerate(self.packets):
                l = len(cmd['hex']) + len(cmd['name']) + 10 +3+3
                if l > length: length = l

            print("Available KISS Commands:")
            #print(self.packets)
            banner = "=" * length
            print (banner)
            print("|{:^3s}|{:^20s}| {:s}".format("IDX","NAME", "HEX"))
            print (banner)
            for i, cmd in enumerate(self.packets):
                #print(cmd)
                print ("|{:^3d}|{:20s}| {:s}".format(i, cmd['name'], cmd['hex']))
                #print(i, cmd, '\t',self.packets[i])
            print (banner)
        else:
            print("No packets")

    def do_send(self, cmd):
        '''
        send packet over network connection
        syntax: send <name> OR send <index>
        get packet name and index using \'list\' command
        '''
        if cmd:
            #try to typecast to int
            try: cmd = int(cmd)
            except: pass
            try:
                if isinstance(cmd, int):
                    if cmd < len(self.packets):
                        pkt = self.packets[int(cmd)]
                        self._send_packet(pkt)
                    else:
                        print("Invalid \'send\' Index: {:d}".format(cmd))
                elif isinstance(cmd, str):
                    names = []
                    for i,pkt in enumerate(self.packets): names.append(pkt['name'])
                    if cmd in names:
                        for i, pkt in enumerate(self.packets):
                            if pkt['name'] == cmd:
                                self._send_packet(pkt)
                    else:
                        print("Invalid \'send\' Name: {:s}".format(cmd))
            except:
                print("Invalid \'send\' Selection: \'{:s}\'".format(cmd))
        else:
            print("Invalid \'send\' Selection: \'{:s}\'".format(cmd))
        time.sleep(0.001)

    def _send_packet(self, pkt):
        self.logger.info("Sending Packet: {:s}".format(pkt['name']))
        print("Sending Packet: {:d} | {:s} | {:s}".format(pkt['index'],pkt['name'], pkt['hex']))
        cmd_dict={
            "type":"CMD",
            "cmd":"SEND",
            "msg":pkt
        }
        self.cmd_q.put(cmd_dict)
        time.sleep(0.1)

    def do_connect(self,line):
        print("Connecting...")

    def do_auto(self,line):
        '''
        Automatic TX Control
        Syntax:
            auto <index>
            auto stop
            auto STOP
        '''
        pass



    def do_status(self, line):
        ''' Network Status '''
        print("Querying Network Status...")
        self.cmd_q.put({"type":"CTL","cmd":"STATUS"})
        time.sleep(.1)
        if not self.rx_q.empty(): #Received a message from user
            msg = self.rx_q.get()
            #print("Status: {:s}".format(json.dumps(msg, indent=4)))
            con = "Connected" if msg['connected'] else "Disconnected"
            print("   Program State: {:s}".format(msg['state']))
            print("Connected Status: {:s}".format(con))
            print("       End Point: [{:s}:{:d}]".format(msg['ip'], msg['port']))
            print(" TX Packet Count: {:d}".format(msg['tx_count']))
            print(" RX Packet Count: {:d}".format(msg['rx_count']))
        else:
            print("No Status Feedback Received...")


    def do_reset(self,line):
        ''' reset the program '''
        self.logger.info("Resetting Program.")
        print("Resetting Program....")
        self.cmd_q.put({"type":"CTL","cmd":"RESET"})
        time.sleep(.1)

    def do_clear(self,line):
        ''' clear screen '''
        os.system('reset')

    def do_exit(self, line):
        ''' Terminate the program '''
        self.cmd_q.put({"type":"CTL","cmd":"EXIT"})
        return True

    def do_quit(self, line):
        ''' Terminate the program '''
        self.do_exit('')

    def do_EOF(self):
        return True

    def set_packets(self, packets):
        self.packets = packets

    def _initialize_packets(self):
        return None

    def stop(self):
        #self.conn.close()
        self.logger.info('{:s} Terminating...'.format(self.name))
        #self.do_EOF()

    def stopped(self):
        return self._stop.isSet()
