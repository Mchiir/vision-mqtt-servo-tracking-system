# mqtt_client.py
from umqtt.simple import MQTTClient
import time

BROKER = "YOUR_VPS_IP"
CLIENT_ID = "esp8266_mchiir01"
TOPIC = b"vision/mchiir01/movement"
PORT = 1883

class MQTTHandler:
    def __init__(self, message_callback):
        self.client = MQTTClient(CLIENT_ID, BROKER, port=PORT)
        self.client.set_callback(message_callback)

    def connect(self):
        self.client.connect()
        self.client.subscribe(TOPIC)
        print("Subscribed to:", TOPIC)

    def check(self):
        self.client.check_msg()

    def reconnect(self):
        while True:
            try:
                self.connect()
                break
            except:
                print("Reconnecting MQTT...")
                time.sleep(5)