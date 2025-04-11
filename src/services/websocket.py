from typing import Dict, Any

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self, ):
        self.active_connections: Dict[Any, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {self.active_connections[user_id]} connected")  # Лог подключения

    async def session_connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"User {self.active_connections[session_id]} connected")  # Лог подключения

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_json(self, user_id: int, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                print(f"Sending message to user {user_id}: {message}")  # Лог перед отправкой
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                await self.disconnect(user_id)
        else:
            print(f"No active WebSocket connection for user {user_id}")

    async def notify_progress(self, session_id: str, payload: Dict[str, Any]):
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_json(payload)


manager = ConnectionManager()
