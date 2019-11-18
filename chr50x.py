# -*- coding: utf-8 -*-

"""
Auther: Fan Tenglong
Time: 2019-11-28
"""


import serial
import time
import os
import logging
# pyqt5
from PyQt5.QtCore import QThread, pyqtSignal
# user lib
import log

UART_READ_LEN = 1024

class CHR50X(QThread):
    sigSerialError = pyqtSignal()
    sigTag = pyqtSignal(str, int, bytes, int)
    Forever = 0xffff

    def __init__(self, port=None, log_cate='rfid_log', loglevel=logging.WARN):
        super().__init__()
        self.uart = serial.Serial()
        self.uart.port = port
        self.uart.baudrate = 115200
        self.uart.timeout = 0.1
        self.log = log.Log(__name__, log_cate, loglevel, loglevel).getlog()
        self.runflag = True
        self.remain = b''

    def setPort(self, port):
        self.uart.port = port

    def isOpen(self):
        return(self.uart.isOpen())

    def open(self, port=None):
        if(port != None):
            self.uart.port = port
        open_flag = False
        try:
            self.uart.open()
        except serial.serialutil.SerialException:
            self.sigSerialError.emit()
            self.log.error("failed opening serial port: %s!" %(self.uart.port))
        else:
            open_flag = True
            self.runflag = True
            self.start()
        return(open_flag)
    
    def close(self):
        # 结束线程
        self.runflag = False
        self.wait()
        if(self.uart.isOpen()):
            self.uart.close()
    
    def send(self, buf):
        result = False
        if(self.uart.isOpen()):
            self.uart.write(buf)
            self.log.debug("serial send: " + str(buf))
            result = True
        else:
            self.sigSerialError.emit()
            self.log.error("serial failed send: " + str(buf) + ", port is closed.")
        return(result)
    
    def checkBcc(self, dat):
        check = 0
        for i in range(len(dat)):
            check ^= dat[i]
        return(check)
    
    def inventory(self, cycles=1):
        pkt = b'\x1b\x39\x00\x00\x02\x00'
        dat = cycles.to_bytes(2, byteorder="little", signed=False)
        bcc = self.checkBcc(dat).to_bytes(1, byteorder="little", signed=False)
        pkt += dat
        pkt += bcc
        self.log.info("send inventory packet, cycles: %d" %cycles)
        self.send(pkt)

    def stop_inventory(self):
        pkt = b'\x1b\x3b\x00\x00\x01\x00\x00\x00'
        self.log.info("send stop inventory packet")
        self.send(pkt)
    
    def run(self):
        while(self.runflag):
            try:
                buf = self.uart.read(UART_READ_LEN)
            except serial.serialutil.SerialException:
                self.sigSerialError.emit()
                self.log.error("serial read error: serial.serialutil.SerialException")
            else:
                if(buf):
                    self.log.debug("recv raw: " + str(buf))
                    dicts = self.unpackStream(buf)
                    for d in dicts:
                        self.log.info("unpacked packet: " + str(d))
                        if(d['type'] == 'tag'):
                            self.sigTag.emit(d['type'], d['rssi'], d['tid'], d['ant'])

    def pickPacket(self, buf):
        start = 0
        stop = 0
        while(True):
            if(len(buf) < start+8):
                break
            if(buf[start]==0x1b and buf[start+1]==0x39 and buf[start+2]==0x01):
                plen = int.from_bytes(buf[start+4:start+6], byteorder='little', signed=False)
                if(len(buf) < (start+plen+7)):
                    break
                else:
                    if(buf[start+plen+6] == self.checkBcc(buf[start+6:start+plen+6])):
                        stop = start + plen + 7
                        break
                    else:
                        start += 1
            else:
                start += 1
        return(start, stop)

    def unpackStream(self, buf):
        buf = self.remain + buf
        components = []
        while(True):
            (start, stop) = self.pickPacket(buf)
            pkt_len = stop - start
            if(pkt_len < 8):
                break
            else:
                comp = {}
                if(pkt_len == 8):
                    comp['type'] = 'retcode'
                    comp['retcode'] = buf[start+6]
                elif(pkt_len == 10):
                    tag_num = int.from_bytes(buf[start+6:start+8], byteorder='little', signed=False)
                    if(tag_num == 0xffff):
                        comp['type'] = 'cycle_end'
                        comp['ant'] = buf[start+8]
                    else:
                        comp['type'] = 'ant_end'
                        comp['tag_num'] = tag_num
                        comp['ant'] = buf[start+8]
                elif( 15 < pkt_len < 30):
                    comp['type'] = 'tag'
                    vlen = buf[start+6]
                    comp['rssi'] = buf[start+7]
                    comp['pc'] = buf[start+8:start+10]
                    comp['tid'] = buf[start+10:start+6+vlen]
                    comp['ant'] = buf[start+6+vlen]
                components.append(comp)
                buf = buf[stop:]
        self.remain = buf
        return(components)

if __name__ == "__main__":
    rfid = CHR50X("COM5", loglevel=logging.DEBUG)
    rfid.open()
    rfid.inventory(2)
    time.sleep(2)
    rfid.close()

