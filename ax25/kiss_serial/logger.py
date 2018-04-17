#!/usr/bin/env python2

# Logger utilities

import math, sys, os, time, struct, traceback, binascii, logging
import datetime as dt

class MyFormatter(logging.Formatter):
    #Overriding formatter for datetime
    converter=dt.datetime.utcfromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y%m%d_%H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


def setup_logger(log_name, level=logging.DEBUG, ts = None, log_path = None, log_ext="log"):
    l = logging.getLogger(log_name)
    if ts == None: ts = str(get_uptime())
    log_file = "{:s}_{:s}.{:s}".format(log_name, ts, log_ext)
    if log_path == None: log_path = '.'
    log_path = log_path + '/' + log_file
    #log_path = os.getcwd() + '/log/' + log_file
    print log_path

    formatter = MyFormatter(fmt='%(asctime)s UTC | %(threadName)14s | %(levelname)8s | %(message)s',datefmt='%Y%m%d %H:%M:%S.%f')
    #fileHandler = logging.FileHandler(log_path, mode='w')
    fileHandler = logging.FileHandler(log_path)
    fileHandler.setFormatter(formatter)
    #streamHandler = logging.StreamHandler()
    #streamHandler.setFormatter(formatter)
    l.setLevel(level)
    l.addHandler(fileHandler)
    l.info('Logger Initialized')
    #l.addHandler(streamHandler)
    return fileHandler
