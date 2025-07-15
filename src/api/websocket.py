"""WebSocket handlers for real-time updates."""
from typing import Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from asyncio import Queue, create_task, Task
import json

from loguru import logger

# Using absolute imports to avoid circular references
from src.core.services.alert_formatter import AlertFormatter
from src.config.settings import get_settings
from src.utils.cache import cache

settings = get_settings()

class WebSocketManager:
    """Manager for WebSocket connections and real-time updates."""
    
    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {
            "token_updates": [],
            "alerts": [],
            "analytics": []
        }
        self.formatter = AlertFormatter()
        self._broadcast_tasks: List[Task] = []
    
    async def connect(self, websocket: WebSocket, channel: str):
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            channel: The update channel to subscribe to
        """
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].append(websocket)
            logger.info(f"New WebSocket connection to {channel} channel")
            
            # Send initial data
            await self._send_initial_data(websocket, channel)
    
    async def disconnect(self, websocket: WebSocket, channel: str):
        """Disconnect a WebSocket client."""
        if channel in self.active_connections:
            try:
                self.active_connections[channel].remove(websocket)
                logger.info(f"WebSocket disconnected from {channel} channel")
            except ValueError:
                pass
    
    async def broadcast_token_update(self, token_data: Dict[str, Any]):
        """Broadcast token update to all connected clients."""
        if not self.active_connections["token_updates"]:
            return
            
        message = {
            "type": "token_update",
            "data": token_data
        }
        
        await self._broadcast_to_channel("token_updates", message)
    
    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcast new alert to all connected clients."""
        if not self.active_connections["alerts"]:
            return
            
        # Format the alert
        formatted_alert = self.formatter.format_token_alert(
            alert_data,
            alert_data.get("alert_type", "new_token")
        )
        
        message = {
            "type": "alert",
            "data": {
                "formatted": formatted_alert,
                "raw": alert_data
            }
        }
        
        await self._broadcast_to_channel("alerts", message)
    
    async def broadcast_analytics(self, analytics_data: Dict[str, Any]):
        """Broadcast analytics update to all connected clients."""
        if not self.active_connections["analytics"]:
            return
            
        message = {
            "type": "analytics_update",
            "data": analytics_data
        }
        
        await self._broadcast_to_channel("analytics", message)
    
    async def _broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any]
    ):
        """Broadcast message to all connections in a channel."""
        dead_connections = []
        
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket, channel)
    
    @cache(ttl=60)  # Cache for 1 minute
    async def _get_cached_analytics(self) -> Dict[str, Any]:
        """Get cached analytics data."""
        # This would be implemented to get current analytics
        # from the TokenAnalysisService
        return {}
    
    async def _send_initial_data(
        self,
        websocket: WebSocket,
        channel: str
    ):
        """Send initial data to new connections."""
        try:
            if channel == "analytics":
                # Send current analytics
                analytics = await self._get_cached_analytics()
                await websocket.send_json({
                    "type": "analytics_snapshot",
                    "data": analytics
                })
            
            elif channel == "token_updates":
                # Send current token states
                # This would be implemented to get current token states
                pass
                
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
