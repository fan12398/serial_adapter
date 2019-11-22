# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import time
import sys
import logging
import requests
# PyQt5
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication
# user lib
import log
import whalesn

HEARTBEAT_TIME = 180

MQTT_BROKER = 'mqtt.tx1.meetwhale.com'
MQTT_PORT = 1883

CENTRAL_SERVER = 'http://192.168.2.192:9898'
REGISTER_URL = CENTRAL_SERVER + '/register'
HEARTBEAT_URL = CENTRAL_SERVER + '/heart'
LISTEN_PORT = 64666

class CComm(QThread):
    def __init__(self, log_cate='rfid_log', loglevel=logging.WARN):
        super().__init__()
        # init params
        self.request_id = 0
        self.ip = whalesn.get_ip_adrress()
        self.sn = whalesn.generateSN()
        # logger
        self.log = log.Log(__name__, log_cate, loglevel, loglevel).getlog()
        # mqtt
        self.mqtt = mqtt.Client()
        self.mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        # init heartbeat timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.heartbeat)
        self.timer.start(HEARTBEAT_TIME*1000)
        # start thread
        self.start()
        # register
        self.register()
    
    def register(self):
        payload = {}
        payload['request_id'] = self.request_id
        self.request_id += 1
        if(len(self.ip) < 7):
            self.ip = whalesn.get_ip_adrress()
        payload['ip'] = self.ip
        payload['port'] = LISTEN_PORT
        payload['device_num'] = 1
        payload['timestamp'] = int(time.time())
        if(len(self.sn) != 19):
            self.sn = whalesn.generateSN()
        payload['device'] = [{'sn':self.sn, 'ver':'1.0.1'}]
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(payload)
        response = requests.request("POST", REGISTER_URL, data=body, headers=headers)
        self.log.info('register: ' + body)

    def heartbeat(self):
        payload = {}
        payload['request_id'] = self.request_id
        self.request_id += 1
        if(len(self.ip) < 7):
            self.ip = whalesn.get_ip_adrress()
        payload['ip'] = self.ip
        payload['port'] = LISTEN_PORT
        payload['device_num'] = 1
        payload['timestamp'] = int(time.time())
        if(len(self.sn) != 19):
            self.sn = whalesn.generateSN()
        payload['device'] = [{'sn':self.sn}]
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(payload)
        response = requests.request("POST", HEARTBEAT_URL, data=body, headers=headers)
        self.log.info('heartbeat: ' + body)
        
    def send(self, data):
        payload = {}
        payload['cmd'] = 2
        payload['data'] = data
        payload['id'] = 1
        payload['prot_ver'] = '1.0.0'
        payload['sn'] = self.sn
        payload['timestamp'] = int(time.time())
        body = json.dumps(payload)
        self.mqtt.publish('rfid-data', body, 1)
        self.log.info('rfid-data: ' + body)
    
    def run(self):
        self.mqtt.loop_forever()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comm = CComm(loglevel=logging.INFO)
    comm.send('hello world')
    sys.exit(app.exec_())

    