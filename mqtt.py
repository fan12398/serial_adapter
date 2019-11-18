# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import time
import sys
# PyQt5
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication

MQTT_BROKER = 'mqtt.meetwhale.com'
MQTT_PORT = 1883
MQTT_USER = 'whale_smart'
MQTT_PASSWD = 'whale123'

HEARTBEAT_TIME = 180

class CComm(QThread):
    def __init__(self):
        super().__init__()
        self.mqtt = mqtt.Client()
        self.mqtt.username_pw_set(MQTT_USER, MQTT_PASSWD)
        self.mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        # init heartbeat timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.heartbeat)
        self.timer.start(HEARTBEAT_TIME*1000)
        # register
        self.register()
    
    def register(self):
        print('device-register')

    def heartbeat(self):
        buf = {}
        buf['hub_sn'] = ''
        buf['sn'] = ''
        buf['proto_ver'] = '1.0.1'
        buf['id'] = 1
        buf['timestamp'] = time.time()
        print('heart beat')
        #self.mqtt.publish('device-heartbeat', json.dumps(buf), 1)
        

    def send(self, tag):
        buf = {}
        buf['sn'] = ''
        buf['data']=''
        buf['cmd'] = 2
        buf['prot_ver'] = '1.0.1'
        buf['hub_sn'] = ''
        buf['timestamp'] = int(time.time())
        self.mqtt.publish('device-data', json.dumps(buf), 1)
    
    def run(self):
        self.mqtt.loop_forever()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    comm = CComm()
    #comm.send('hello world')
    sys.exit(app.exec_())

    