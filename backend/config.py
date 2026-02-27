"""
Central configuration for backend component.
This enforces protocol separation and clean deployment configuration.
"""

import os

# ==============================
# MQTT Configuration
# ==============================

MQTT_BROKER = os.getenv("MQTT_BROKER", "157.173.101.159")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "vision/mchiir01/#")

MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "backend_bridge_node")

# ==============================
# WebSocket Configuration
# ==============================

WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", 8000))