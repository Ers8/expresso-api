from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json

active_connections: List[WebSocket] = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"[WS] Client terhubung. Total: {len(active_connections)}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("[WS] Client disconnect")

async def broadcast_alert(alert_data: dict):
    if not active_connections:
        return
    message = json.dumps(alert_data)
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)