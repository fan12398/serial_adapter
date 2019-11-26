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
        try:
            self.mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        except:
            self.log.error('mqtt broker connect error')
        # start thread
        self.start()
        # register
        time.sleep(1)
        self.register()
        # init heartbeat timer
        time.sleep(1)
        self.heartbeat()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.heartbeat)
        self.timer.start(HEARTBEAT_TIME*1000)
    
    def register(self):
        payload = {}
        payload['request_id'] = self.request_id
        self.request_id += 1
        if(len(self.ip) < 9):
            self.ip = whalesn.get_ip_adrress()
        payload['ip'] = self.ip
        payload['port'] = LISTEN_PORT
        payload['device_num'] = 1
        payload['timestamp'] = int(time.time()*1000)
        if(len(self.sn) != 19):
            self.sn = whalesn.generateSN()
        payload['device'] = [{'sn':self.sn, 'ver':'1.0.1', 'id':1}]
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(payload)
        response = requests.request("POST", REGISTER_URL, data=body, headers=headers)
        self.log.info('send: ' + body)
        self.log.info('response: ' + response.text)

    def heartbeat(self):
        payload = {}
        payload['request_id'] = self.request_id
        self.request_id += 1
        if(len(self.ip) < 9):
            self.ip = whalesn.get_ip_adrress()
        payload['ip'] = self.ip
        payload['port'] = LISTEN_PORT
        payload['device_num'] = 1
        payload['timestamp'] = int(time.time()*1000)
        if(len(self.sn) != 19):
            self.sn = whalesn.generateSN()
        payload['device'] = [{'sn':self.sn}]
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(payload)
        session = requests.session()
        response = session.post(HEARTBEAT_URL, data=body, headers=headers)
        session.close()
        self.log.info('send: ' + body)
        self.log.info('response: ' + response.text)
        
    def send(self, data):
        payload = {}
        payload['cmd'] = 2
        payload['data'] = data
        payload['id'] = 1
        payload['proto_ver'] = '1.0.0'
        payload['sn'] = self.sn
        payload['timestamp'] = int(time.time())
        body = json.dumps(payload)
        self.mqtt.publish('device-data', body, 1)
        self.log.info('device-data: ' + body)
    
    def run(self):
        self.mqtt.loop_forever()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comm = CComm(loglevel=logging.INFO)
    data = {'sensor_flag':1, 'sensor_uid':'This is a tag'}
    comm.send(data)
    sys.exit(app.exec_())

    