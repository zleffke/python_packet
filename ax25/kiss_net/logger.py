#!/usr/bin/env python3

# Logger utilities

import math, sys, os, time, struct, traceback, binascii, logging
import datetime
import numpy as np

class MyFormatter(logging.Formatter):
    #Overriding formatter for datetime
    converter=datetime.datetime.utcfromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        #else:
        #    t = ct.strftime("%Y%m%dT%H:%M:%SZ")
        #    s = "%s,%03d" % (t, record.msecs)
        return s

def setup_logger(cfg):
    if cfg['startup_ts'] == None: ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    else: ts = cfg['startup_ts']
    name = cfg['name']
    verbose = cfg['verbose']
    path = cfg['path']
    level = cfg['level']
    file = "{:s}.{:s}.log".format(ts, name)
    file_path = '/'.join([path, file])

    #formatter = MyFormatter(fmt='%(asctime)s | %(threadName)8s | %(levelname)8s | %(message)s',datefmt='%Y-%m-%dT%H:%M:%S.%fZ')
    #formatter = MyFormatter(fmt='[%(asctime)s][%(threadName)8s][%(levelname)8s] %(message)s',datefmt='%Y-%m-%dT%H:%M:%S.%fZ')
    formatter = MyFormatter(fmt='[%(asctime)s | %(threadName)s | %(levelname)8s] %(message)s',datefmt='%Y-%m-%dT%H:%M:%S.%fZ')

    log = logging.getLogger(name)
    if   level == 'DEBUG'   : log.setLevel(logging.DEBUG)
    elif level == 'INFO'    : log.setLevel(logging.INFO)
    elif level == 'WARNING' : log.setLevel(logging.WARNING)
    elif level == 'ERROR'   : log.setLevel(logging.ERROR)
    elif level == 'CRITICAL': log.setLevel(logging.CRITICAL)

    #Always setup file log
    fileHandler = logging.FileHandler(file_path)
    fileHandler.setFormatter(formatter)
    log.addHandler(fileHandler)
    #if desired, setup stdout logging
    if verbose:
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        log.addHandler(streamHandler)
        print ("STDOUT Logger Initialized, Switching to Stream Handler....")
    log.info('Logger Initialized')
    return log
