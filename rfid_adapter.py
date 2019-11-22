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
    def __init__(self, port, reverse=False, timeout=10):
        super().__init__()
        self.tags = {}
        self.reverse = reverse
        self.timeout = timeout
        
        # init trans communicator
        self.comm = CComm()
        # init rfid device
        self.rfid = CHR50X(port)
        self.rfid.sigTag.connect(self.procTagsNew)
        self.rfid.sigSerialError.connect(self.procError)
        self.rfid.open()
        # start inventory forever
        self.rfid.inventory(self.rfid.Forever)
        # start run tag timeout
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.procTagsTimeout)
        self.timer.start(100)
    
    def procError(self):
        print("receive serial error signal, close application!!!")
        sys.exit(0)
    
    def procTagsNew(self, type, rssi, tid, ant):
        if(tid not in self.tags):
            if(self.reverse):
                print("pick up:", tid)
                self.pickupEvent(tid)
            else:
                print("put down:", tid)
                self.putdownEvent(tid)
        self.tags[tid] = 0
    
    def procTagsTimeout(self):
        for id in list(self.tags.keys()):
            self.tags[id] += 1
            if(self.tags[id] >= self.timeout):
                del self.tags[id]
                if(self.reverse):
                    print("put down:", id)
                    self.putdownEvent(id)
                else:
                    print("pick up:", id)
                    self.pickupEvent(id)

    # please rewrite these two functions to implement the events    
    def pickupEvent(self, tag):
        data = {'sensor_flag':1, 'sensor_uid':tag}
        self.comm.send(json.dumps(data))

    def putdownEvent(self, tag):
        data = {'sensor_flag':0, 'sensor_uid':tag}
        self.comm.send(json.dumps(data))


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port', type=str, required=True, help="RFID reader serial port eg: COM5, /dev/ttyUSB0")
    parser.add_argument('-t','--timeout', type=int, default=10, help="tag search missing timeout, N*0.1 seconds")
    parser.add_argument('-r','--reverse', action='store_true', default=False, help="indicate whether inverse tag search mode")
    return parser.parse_args(argv)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    args = parse_arguments(sys.argv[1:])

    rfid_adapter = CAdapter(port=args.port, reverse=args.reverse, timeout=args.timeout)

    sys.exit(app.exec_())

