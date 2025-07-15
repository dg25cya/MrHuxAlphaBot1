"""WebSocket routes for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional

from ..websocket import ws_manager
from ..auth import get_admin_token

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/tokens")
async def token_updates(
    websocket: WebSocket,
    token: Optional[str] = Depends(get_admin_token)
):
    """WebSocket endpoint for real-time token updates."""
    try:
        await ws_manager.connect(websocket, "token_updates")
        while True:
            try:
                # Keep connection alive and handle messages
                data = await websocket.receive_json()
                # Handle any incoming messages if needed
            except WebSocketDisconnect:
                await ws_manager.disconnect(websocket, "token_updates")
                break
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

@router.websocket("/ws/alerts")
async def alert_updates(
    websocket: WebSocket,
    token: Optional[str] = Depends(get_admin_token)
):
    """WebSocket endpoint for real-time alert updates."""
    try:
        await ws_manager.connect(websocket, "alerts")
        while True:
            try:
                # Keep connection alive and handle messages
                data = await websocket.receive_json()
                # Handle any incoming messages if needed
            except WebSocketDisconnect:
                await ws_manager.disconnect(websocket, "alerts")
                break
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

@router.websocket("/ws/analytics")
async def analytics_updates(
    websocket: WebSocket,
    token: Optional[str] = Depends(get_admin_token)
):
    """WebSocket endpoint for real-time analytics updates."""
    try:
        await ws_manager.connect(websocket, "analytics")
        while True:
            try:
                # Keep connection alive and handle messages
                data = await websocket.receive_json()
                # Handle any incoming messages if needed
            except WebSocketDisconnect:
                await ws_manager.disconnect(websocket, "analytics")
                break
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
