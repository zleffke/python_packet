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
import json
import binascii
import socket
import errno

#from optparse import OptionParser
import argparse
from main_thread import *
from logger import *

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
                       default="adsb_parse_config.json",
                       help="Configuration File",
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
    #cfg['log']['name'] = cfg['name']

    log_name = '.'.join([cfg['name'],'main'])
    cfg['main_log'].update({
        "path":cfg['log_path'],
        "name":log_name,
        "startup_ts":startup_ts
    })

    for key in cfg['thread_enable'].keys():
        print(key)
        print(cfg[key]['log'])
        log_name =  '.'.join([cfg['name'],cfg[key]['name']])
        cfg[key]['main_log']=cfg['main_log']['name']
        cfg[key]['log'].update({
            'path':cfg['log_path'],
            'name':log_name,
            'startup_ts':startup_ts,
            'verbose':cfg[key]['log']['verbose'],
            'level':cfg['main_log']['level']
        })

    if 'current' in cfg['out_path']:
        cfg['out_path'] = "/".join([cwd,'output'])
    cfg['out_file'] = "_".join([cfg['out_file'],startup_ts])
    cfg['out_file'] = ".".join([cfg['out_file'],'json'])

    print (json.dumps(cfg, indent=4))
    #sys.exit()

    main_thread = Main_Thread(cfg, name="Main_Thread")
    main_thread.daemon = True
    main_thread.run()
    sys.exit()








    # #Import Packet(s)
    # fp_pkt = '/'.join([args.pkt_path,args.pkt_file])
    # if not os.path.isfile(fp_pkt) == True:
    #     print ('ERROR: Invalid Packet File: {:s}'.format(fp_pkt))
    #     sys.exit()
    # with open(fp_pkt, 'r') as json_data:
    #     pkt_dict = json.load(json_data)
    #     json_data.close()
    #
    # setup_logger(cfg['log'])
    # log = logging.getLogger(cfg['log']['name']) #main logger
    # log.info("config file: {:s}".format(fp_cfg))
    # log.info("configs: {:s}".format(json.dumps(cfg)))
    # log.info("packet file: {:s}".format(fp_pkt))
    # log.info("packet json: {:s}".format(json.dumps(pkt_dict)))
    #
    # ax25 = DictToAx25(pkt_dict)
    # # print ("AX.25 Frame: {:s}".format(ax25.hex()))
    # log.info("Generated AX.25 Frame:     {:s}".format(ax25.hex()))
    #
    # kiss = Ax25ToKiss(ax25, cfg['log']['name'])
    # log.info(" Generated KISS Frame: {:s}".format(kiss.hex()))
    #
    # # ax25_decode, kiss_port, kiss_cmd = KissToAx25(kiss, cfg['log']['name'])
    # ax25_decode, kiss_port, kiss_cmd = KissToAx25(kiss, cfg['log']['name'])
    # log.info("KISS -> AX.25 Decoded: {:s}".format(ax25_decode.hex()))
    # log.info("Decoded Matches Original AX.25: {:s}".format(str(ax25 == ax25_decode)))
    #
    # #Setup TX Timer
    #
    #
    # sys.exit()

    # connected = False
    # log.info('Creating TCP Client Socket')
    # repeat = 0
    # q = Queue()
    # while 1:
    #     try:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #         sock.setblocking(0)
    #         sock.settimeout(cfg['net']['sock_timeout'])
    #         sock.connect((cfg['net']['ip'], cfg['net']['port']))
    #         connected = True
    #         log.info("Connected to: [{:s}:{:d}]".format(cfg['net']['ip'], cfg['net']['port']))
    #         if cfg['net']['auto']:
    #             tx_timer = Watchdog(cfg['net']['auto_delay'], 'TX Timer', _tx_timer_expired(sock,kiss,log,q))
    #             tx_timer.start()
    #     except:
    #         log.info("Failed to Connect to: [{:s}:{:d}]".format(cfg['net']['ip'], cfg['net']['port']))
    #         log.info("Is the server side running?....")
    #         log.info("Attempting to reconnect in {:f} seconds...".format(cfg['net']['retry_timeout']))
    #         time.sleep(cfg['net']['retry_timeout'])
    #         tx_timer.stop()
    #     while (connected):
    #         try:
    #             data = sock.recv(1024)
    #             log.info("RX: {:s}".format(data.hex()))
    #         except socket.error as err:
    #             #print(err, err.errno)
    #             if err == 'timed out':
    #                 pass
    #             elif err.errno==errno.EPIPE:  #Client disconnected
    #                 connected = False
    #                 log.info('Client Disconnected')
    #                 repeat = 0
    #                 break
    #
    #             # else:
    #                 # log.info(err, err.errno)
    #         except Exception as e:
    #             log
    #
    # sys.exit()
    #
    # # connected = False
    # # print 'Creating TCP Client Socket'
    # # repeat = 0
    # # while 1:
    # #     try:
    # #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # #         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # #         sock.setblocking(1)
    # #         sock.connect((args.ip, args.port))
    # #         connected = True
    # #         print "Connected to: [{:s}:{:d}]".format(args.ip, args.port)
    # #     except:
    # #         print "Failed to Connect to: [{:s}:{:d}]".format(args.ip, args.port)
    # #         print "Is the server side running?...."
    # #         print "Attempting to reconnect in {:f} seconds...".format(args.retry)
    # #         time.sleep(args.retry)
    # #
    # #     while (connected):
    # #             try:
    # #                 data = sock.recv(1024)
    # #                 ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # #                 print "\n{:s} | RX: {:s}".format(ts, binascii.hexlify(data))
    # #                 print "delaying {:3.3f} seconds...".format(args.delay)
    # #                 time.sleep(args.delay)
    # #                 ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # #                 print "{:s} | TX: {:s}".format(ts, binascii.hexlify(data))
    # #                 sock.sendall(data)
    # #             except socket.error, v:
    # #                 connected = False
    # #                 errorcode=v[0]
    # #                 if errorcode==errno.EPIPE:  #Client disconnected
    # #                     print 'Client Disconnected'
    # #                     repeat = 0
    # #                     break
    # #     print 'Finished Playback'
    # #     repeat = 0
    # # sys.exit()


if __name__ == '__main__':
    main()
