from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
from app.core.cache_manager import cache_manager

router = APIRouter()


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.stats_cache = {
            "total_logs": 0,
            "success_logs": 0,
            "error_logs": 0,
            "last_updated": None
        }
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_log(self, log_data: Dict[str, Any]):
        """
        Broadcast new log to all connected clients
        Sends individual log and updated stats
        """
        try:
            # Update stats
            self._update_stats(log_data)
            
            # Prepare message
            message = {
                "type": "new_log",
                "data": log_data,
                "stats": self.stats_cache,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all connected clients
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)
                
        except Exception as e:
            print(f"Error broadcasting log: {e}")
    
    async def broadcast_stats(self):
        """
        Broadcast current stats to all clients
        Called periodically (every 2 seconds)
        """
        try:
            # Recalculate stats from cache
            cache_logs = cache_manager.get_logs_by_pattern("log:*")
            
            total = len(cache_logs)
            errors = sum(1 for log in cache_logs if log.get('logLevel') == 'ERROR')
            success = total - errors
            
            self.stats_cache = {
                "total_logs": total,
                "success_logs": success,
                "error_logs": errors,
                "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                "last_updated": datetime.now().isoformat()
            }
            
            message = {
                "type": "stats_update",
                "stats": self.stats_cache
            }
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending stats to client: {e}")
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(conn)
                
        except Exception as e:
            print(f"Error broadcasting stats: {e}")
    
    def _update_stats(self, log_data: Dict[str, Any]):
        """Update internal stats cache"""
        self.stats_cache["total_logs"] += 1
        
        if log_data.get('logLevel') == 'ERROR':
            self.stats_cache["error_logs"] += 1
        else:
            self.stats_cache["success_logs"] += 1
        
        total = self.stats_cache["total_logs"]
        success = self.stats_cache["success_logs"]
        self.stats_cache["success_rate"] = round((success / total * 100) if total > 0 else 0, 2)
        self.stats_cache["last_updated"] = datetime.now().isoformat()
    
    async def send_initial_stats(self, websocket: WebSocket):
        """Send current stats to newly connected client"""
        try:
            message = {
                "type": "initial_stats",
                "stats": self.stats_cache
            }
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending initial stats: {e}")


# Singleton instance
websocket_manager = WebSocketManager()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log updates
    Sends new logs and stats every 2 seconds
    """
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial stats
        await websocket_manager.send_initial_stats(websocket)
        
        # Keep connection alive and send periodic stats
        while True:
            try:
                # Wait for client message (ping/pong or commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=2.0
                )
                
                # Handle client messages
                if data:
                    try:
                        message = json.loads(data)
                        
                        if message.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
                        
                        elif message.get("type") == "request_stats":
                            await websocket_manager.broadcast_stats()
                    
                    except json.JSONDecodeError:
                        pass
            
            except asyncio.TimeoutError:
                # No message received, send periodic stats update
                await websocket_manager.broadcast_stats()
                continue
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print("Client disconnected normally")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@router.websocket("/ws/live-stats")
async def websocket_live_stats(websocket: WebSocket):
    """
    WebSocket endpoint specifically for live statistics
    Updates every 2 seconds
    """
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial stats
        await websocket_manager.send_initial_stats(websocket)
        
        # Send stats every 2 seconds
        while True:
            await asyncio.sleep(2)
            await websocket_manager.broadcast_stats()
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)