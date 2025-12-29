from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
from app.core.file_watcher import file_watcher
from app.models.log_entry import LogEntry
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

manager = ConnectionManager()

async def handle_new_logs(entries: List[LogEntry]):
    """Callback function for file watcher - broadcasts new logs"""
    if not manager.active_connections:
        return
    
    # Convert entries to dict
    logs_data = [entry.dict() for entry in entries]
    
    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "new_logs",
        "logs": logs_data,
        "count": len(logs_data),
        "timestamp": entries[-1].timestamp if entries else None
    })

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection success message
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to log stream"
        }, websocket)
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive messages from client (ping/pong, filters, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong"
                    }, websocket)
                
                elif message.get("type") == "subscribe":
                    # Client wants to subscribe to specific filters
                    # TODO: Implement filtered streaming
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "filters": message.get("filters", {})
                    }, websocket)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON"
                }, websocket)
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break
    
    finally:
        manager.disconnect(websocket)

@router.on_event("startup")
async def startup_event():
    """Subscribe to file watcher on startup"""
    file_watcher.subscribe(handle_new_logs)
    logger.info("WebSocket subscribed to file watcher")

@router.on_event("shutdown")
async def shutdown_event():
    """Unsubscribe from file watcher on shutdown"""
    file_watcher.unsubscribe(handle_new_logs)
    logger.info("WebSocket unsubscribed from file watcher")