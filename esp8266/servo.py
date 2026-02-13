# servo.py
from machine import Pin, PWM

class ServoController:
    def __init__(self, pin_number=5):
        self.pwm = PWM(Pin(pin_number), freq=50)
        self.current_angle = 90
        self.set_angle(90)

    def set_angle(self, angle):
        # Clamp angle
        angle = max(0, min(180, angle))
        self.current_angle = angle

        # Convert angle to duty cycle (MicroPython ESP8266 range 0-1023)
        duty = int((angle / 180) * 75 + 40)
        self.pwm.duty(duty)

    def move_left(self):
        self.set_angle(self.current_angle - 10)

    def move_right(self):
        self.set_angle(self.current_angle + 10)

    def center(self):
        self.set_angle(90)