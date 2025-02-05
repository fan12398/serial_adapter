# -*- coding: utf-8 -*-
"""
Auther: Fan Tenglong
Time: 2019-11-28
"""

import time
import json
import argparse
import sys
import logging
# pyqt5
import sip
import PyQt5.QtGui
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication
# user lib
from chr50x import CHR50X
from mqtt import CComm

class CAdapter(QThread):
    def __init__(self, port, reverse=False, timeout=10, dest=None, loglevel=logging.WARN):
        super().__init__()
        # 4 antennas
        self.tags = [{} for i in range(4)]
        self.reverse = reverse
        self.timeout = timeout
        
        # init rfid device
        self.rfid = CHR50X(port,loglevel=loglevel)
        self.rfid.sigTag.connect(self.procTagsNew)
        self.rfid.sigSerialError.connect(self.procError)
        self.rfid.open()
        # init trans communicator
        self.comm = CComm(dest=dest,loglevel=loglevel)

        # start inventory forever
        self.rfid.inventory(self.rfid.Forever)
        # start run tag timeout
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.procTagsTimeout)
        self.timer.start(100)
    
    def procError(self):
        print("receive serial error signal, close application!!!")
        sys.exit(0)
    
    def inWhichAnt(self, tid):
        for ant in range(len(self.tags)):
            if(tid in self.tags[ant]):
                return(ant)
        return(-1)
    
    def procTagsNew(self, type, rssi, tid, ant):
        occu_ant = self.inWhichAnt(tid)
        if(occu_ant == -1):
            if(self.reverse):
                print("pick up:", tid)
                self.pickupEvent(tid, ant)
            else:
                print("put down:", tid)
                self.putdownEvent(tid, ant)
            self.tags[ant][tid] = 0
        elif(occu_ant == ant):
            self.tags[ant][tid] = 0

    '''
    # tags process function without sort ant_id
    def procTagsNew(self, type, rssi, tid, ant):
        if(tid not in self.tags[ant]):
            if(self.reverse):
                print("pick up:", tid)
                self.pickupEvent(tid, ant)
            else:
                print("put down:", tid)
                self.putdownEvent(tid, ant)
        self.tags[ant][tid] = 0
    '''

    def procTagsTimeout(self):
        for ant in range(len(self.tags)):
            for tid in list(self.tags[ant].keys()):
                self.tags[ant][tid] += 1
                if(self.tags[ant][tid] >= self.timeout):
                    if(self.reverse):
                        print("put down:", tid)
                        self.putdownEvent(tid, ant)
                    else:
                        print("pick up:", tid)
                        self.pickupEvent(tid, ant)
                    del self.tags[ant][tid]

    # please rewrite these two functions to implement the events    
    def pickupEvent(self, tag, ant_id):
        sn = self.tag2sn(tag)
        data = {'sensor_flag':1, 'sensor_uid':sn}
        self.comm.send_dest(data, ant_id)

    def putdownEvent(self, tag, ant_id):
        sn = self.tag2sn(tag)
        data = {'sensor_flag':0, 'sensor_uid':sn}
        self.comm.send_dest(data, ant_id)
    
    def tag2sn(self, bs):
        tag = ''.join(['%02X' %b for b in bs])
        if(len(tag) < 15):
            sn = 'WLT2' + tag
            absent = 19-len(sn)
            sn += tag[-absent:]
        else:
            sn = 'WLT2' + tag[-15:]
        return(sn)


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port', type=str, required=True, help="RFID reader serial port eg: COM5, /dev/ttyUSB0")
    parser.add_argument('-t','--timeout', type=int, default=10, help="tag search missing timeout, N*0.1 seconds")
    parser.add_argument('-r','--reverse', action='store_true', default=False, help="indicate whether inverse tag search mode")
    parser.add_argument('-d','--destination', type=str, nargs='+', help='remote destination ip of ubuntu mqtt broker')
    parser.add_argument('-l','--loglevel', type=str, default='warn', help='log level, eg: debug, info, warn, error, critical, fatal')
    return parser.parse_args(argv)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    args = parse_arguments(sys.argv[1:])

    if(args.loglevel.lower() == 'debug'):
        loglevel = logging.DEBUG
    elif(args.loglevel.lower() == 'info'):
        loglevel = logging.INFO
    elif(args.loglevel.lower() == 'warn'):
        loglevel = logging.WARN
    elif(args.loglevel.lower() == 'error'):
        loglevel = logging.ERROR
    elif(args.loglevel.lower() == 'critical'):
        loglevel = logging.CRITICAL
    elif(args.loglevel.lower() == 'fatal'):
        loglevel = logging.FATAL
    else:
        loglevel = logging.WARN

    rfid_adapter = CAdapter(port=args.port, reverse=args.reverse, timeout=args.timeout, dest=args.destination, loglevel=loglevel)

    sys.exit(app.exec_())
