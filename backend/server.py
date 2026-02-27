"""
Backend WebSocket Server.

Responsibilities:
- Accept WebSocket clients (dashboard)
- Start MQTT bridge
- Relay MQTT messages to WebSocket clients
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from websocket_manager import WebSocketManager
from mqtt_bridge import MQTTBridge
import config


app = FastAPI()
manager = WebSocketManager()

# ==============================
# Startup Event
# ==============================

@app.on_event("startup")
async def startup_event():
    """
    Start MQTT bridge when backend starts.
    """
    mqtt_bridge = MQTTBridge(manager)
    mqtt_bridge.start()
    print("MQTT Bridge started")


# ==============================
# WebSocket Endpoint
# ==============================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive (no polling, just wait)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==============================
# Run Server
# ==============================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=config.WS_HOST,
        port=config.WS_PORT,
        reload=False
    )