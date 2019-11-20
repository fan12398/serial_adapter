# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import time
import sys
# PyQt5
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication
# user lib
import log

MQTT_BROKER = 'mqtt.tx1.meetwhale.com'
MQTT_PORT = 1883

HEARTBEAT_TIME = 180

class CComm(QThread):
    def __init__(self, log_cate='rfid_log', loglevel=logging.WARN):
        super().__init__()
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
        buf = {}
        buf['hub_sn'] = ''
        buf['sn'] = ''
        buf['proto_ver'] = '1.0.0'
        buf['id'] = 1
        buf['timestamp'] = time.time()
        self.mqtt.publish('raw-device-register', json.dumps(buf), 2)
        self.log.info('raw-device-register: ' + str(buf))

    def heartbeat(self):
        buf = {}
        buf['sn'] = ''
        buf['id'] = 1
        buf['proto_ver'] = '1.0.0'
        buf['ver'] = '1.0.1'
        self.mqtt.publish('raw-device-heartbeat', json.dumps(buf), 0)
        self.log.info('raw-device-heartbeat: ' + str(buf))
        
    def send(self, tag):
        buf = {}
        buf['sn'] = ''
        buf['data']=''
        buf['cmd'] = 2
        buf['prot_ver'] = '1.0.0'
        buf['hub_sn'] = ''
        buf['timestamp'] = int(time.time())
        self.mqtt.publish('device-data', json.dumps(buf), 1)
        self.log.info('device-data: ' + str(buf))
    
    def run(self):
        self.mqtt.loop_forever()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comm = CComm()
    comm.send('hello world')
    sys.exit(app.exec_())

    