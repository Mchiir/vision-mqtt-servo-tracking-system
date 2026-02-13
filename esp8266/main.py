# main.py
import time
from servo import ServoController
from mqtt_client import MQTTHandler

servo = ServoController(pin_number=5)

def on_message(topic, msg):
    movement = msg.decode()
    print("Received:", movement)

    if movement == "MOVE_LEFT":
        servo.move_left()

    elif movement == "MOVE_RIGHT":
        servo.move_right()

    elif movement == "CENTERED":
        servo.center()

    elif movement == "NO_FACE":
        pass  # Optional: stop or center

mqtt = MQTTHandler(on_message)
mqtt.connect()

while True:
    try:
        mqtt.check()
        time.sleep(0.1)
    except Exception as e:
        print("Error:", e)
        mqtt.reconnect()