"""
WebSocket connection manager.
Maintains active connections and broadcasts messages to all clients.
"""

from fastapi import WebSocket
from typing import List
import asyncio


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove disconnected WebSocket client.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """
        Broadcast message to all connected clients.
        """
        if not self.active_connections:
            return

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove broken connections safely
                self.disconnect(connection)