# Vision MQTT Servo Tracking System

## Overview

This project implements a real-time distributed face tracking system
using MQTT and WebSocket communication.

The system is composed of four completely independent components:

1.  PC Vision Node\
2.  ESP8266 Edge Controller\
3.  Backend Relay Server (VPS)\
4.  Web Dashboard

The architecture strictly enforces protocol separation and real-time
event-driven communication.

---

## System Architecture

### Golden Rule

Vision computes.\
Devices speak MQTT.\
Browsers speak WebSocket.\
Backend relays in real time.

Violation of this separation breaks architectural integrity.

---

## Component Responsibilities

### 1️⃣ PC Vision Node

- Captures live camera feed
- Detects face position
- Determines movement state:
  - MOVE_LEFT
  - MOVE_RIGHT
  - CENTERED
  - NO_FACE
- Publishes movement messages via MQTT (using id **mchiir01** and base topic **vision/mchiir01/**)

Restrictions: - Must NOT communicate directly with ESP8266 - Must NOT
communicate directly with browser - Must NOT use HTTP for control

---

### 2️⃣ ESP8266 Edge Controller

- Subscribes to MQTT movement topic
- Controls servo motor
- Rotates physically based on movement instruction

Restrictions: - Must NOT use HTTP - Must NOT use WebSocket - Must NOT
communicate directly with browser

---

### 3️⃣ Backend (VPS)

- Hosts MQTT Broker (Port 1883)
- Subscribes to movement messages
- Broadcasts updates to browser via WebSocket
- Acts as protocol translator:

MQTT → WebSocket

---

### 4️⃣ Web Dashboard

- Connects to backend via WebSocket
- Displays:
  - Current movement
  - Timestamp
  - Tracking status

Restrictions: - Must NOT connect directly to MQTT - Must NOT use polling

---

## Communication Flow

PC Vision → MQTT Broker\
MQTT Broker → ESP8266\
MQTT Broker → Backend Subscriber\
Backend → WebSocket → Dashboard

---

## Project Structure

    vision-mqtt-servo-tracking-system/

    /pc_vision
        main.py

    /esp8266
        main.py

    /backend
        server.py

    /dashboard
        index.html

    README.md

---

## Technologies Used

- Python (OpenCV, Paho MQTT)
- MicroPython (ESP8266)
- MQTT (Mosquitto Broker)
- WebSocket
- HTML / CSS / JavaScript

---

## Deployment Notes

- MQTT broker runs on VPS (Port 1883)
- Backend WebSocket server runs on VPS
- PC Vision publishes movement messages
- ESP8266 subscribes and drives servo motor
- Dashboard receives real-time updates via WebSocket

---
