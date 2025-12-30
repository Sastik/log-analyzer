from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Set
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

class WebSocketManager:
    """Manages WebSocket connections for live log streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}  # Connection -> set of filters
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_log(self, log_data: Dict[str, Any]):
        """Broadcast new log to all connected clients"""
        if not self.active_connections:
            return
        
        message = {
            "type": "log_update",
            "data": log_data
        }
        
        disconnected = []
        
        for connection in self.active_connections:
            try:
                # Check if client has filters
                filters = self.subscriptions.get(connection, set())
                
                # Apply filters if any
                if filters:
                    if not self._matches_filters(log_data, filters):
                        continue
                
                await connection.send_json(message)
                
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    def _matches_filters(self, log_data: Dict[str, Any], filters: Set[str]) -> bool:
        """Check if log matches client filters"""
        # Filter format: "api_name:JobApi", "log_level:ERROR", etc.
        for filter_str in filters:
            if ':' not in filter_str:
                continue
            
            filter_type, filter_value = filter_str.split(':', 1)
            
            if filter_type == 'api_name' and log_data.get('apiName') != filter_value:
                return False
            elif filter_type == 'service_name' and log_data.get('serviceName') != filter_value:
                return False
            elif filter_type == 'log_level' and log_data.get('logLevel') != filter_value:
                return False
        
        return True
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

# Singleton instance
websocket_manager = WebSocketManager()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live log streaming
    
    Clients can send filter commands:
    {
        "action": "subscribe",
        "filters": {
            "api_name": "JobApi",
            "log_level": "ERROR"
        }
    }
    """
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client (for filters)
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get('action')
                
                if action == 'subscribe':
                    # Update client filters
                    filters = message.get('filters', {})
                    filter_set = set()
                    
                    for key, value in filters.items():
                        filter_set.add(f"{key}:{value}")
                    
                    websocket_manager.subscriptions[websocket] = filter_set
                    
                    await websocket_manager.send_personal_message(
                        {"type": "subscription_updated", "filters": list(filter_set)},
                        websocket
                    )
                
                elif action == 'unsubscribe':
                    # Clear filters
                    websocket_manager.subscriptions[websocket] = set()
                    
                    await websocket_manager.send_personal_message(
                        {"type": "subscription_cleared"},
                        websocket
                    )
                
                elif action == 'ping':
                    # Heartbeat
                    await websocket_manager.send_personal_message(
                        {"type": "pong"},
                        websocket
                    )
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client")
            except Exception as e:
                logger.error(f"Error processing client message: {e}")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": len(websocket_manager.active_connections),
        "status": "healthy"
    }