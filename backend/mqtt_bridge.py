"""
MQTT → WebSocket bridge.

Subscribes to MQTT broker and forwards messages
to all connected WebSocket clients.
"""

import json
import threading
import paho.mqtt.client as mqtt
from . import config


class MQTTBridge:
    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.client = mqtt.Client(client_id=config.MQTT_CLIENT_ID)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    # ==============================
    # MQTT Callbacks
    # ==============================

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            client.subscribe(config.MQTT_TOPIC)
            print(f"Subscribed to topic: {config.MQTT_TOPIC}")
        else:
            print(f"MQTT connection failed: {rc}")

    def on_message(self, client, userdata, msg):
        """
        Forward MQTT payload directly to WebSocket clients.
        """
        try:
            payload = msg.payload.decode()
            json.loads(payload)  # Validate JSON format

            # Broadcast asynchronously to WebSocket clients
            import asyncio
            asyncio.run(self.websocket_manager.broadcast(payload))

        except Exception as e:
            print("Invalid MQTT message:", e)

    # ==============================
    # Start Bridge
    # ==============================

    def start(self):
        """
        Start MQTT client in a background thread.
        """
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)

        thread = threading.Thread(target=self.client.loop_forever)
        thread.daemon = True
        thread.start()