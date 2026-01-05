"""
WebSocket Alerts - Real-time alert notifications for teachers.

Cortez82: Created for Mejora 4.6 - Notificaciones push de alertas criticas

Provides:
- WebSocket endpoint for real-time teacher alerts
- Connection management for multiple teachers
- Broadcast mechanism for critical alerts
"""
import asyncio
import logging
import json
from typing import Dict, Set, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from ..deps import get_user_repository
from ...database.repositories import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Alerts"])


class AlertConnectionManager:
    """
    Manages WebSocket connections for teacher alerts.

    Thread-safe connection management with broadcast capabilities.
    """

    def __init__(self):
        # teacher_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # All teacher connections for broadcasts
        self.all_teachers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, teacher_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        async with self._lock:
            if teacher_id not in self.active_connections:
                self.active_connections[teacher_id] = set()
            self.active_connections[teacher_id].add(websocket)
            self.all_teachers.add(websocket)

        logger.info(
            "WebSocket connected",
            extra={
                "teacher_id": teacher_id,
                "total_connections": len(self.all_teachers)
            }
        )

    async def disconnect(self, websocket: WebSocket, teacher_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if teacher_id in self.active_connections:
                self.active_connections[teacher_id].discard(websocket)
                if not self.active_connections[teacher_id]:
                    del self.active_connections[teacher_id]
            self.all_teachers.discard(websocket)

        logger.info(
            "WebSocket disconnected",
            extra={
                "teacher_id": teacher_id,
                "total_connections": len(self.all_teachers)
            }
        )

    async def send_to_teacher(self, teacher_id: str, message: dict):
        """Send a message to a specific teacher."""
        async with self._lock:
            connections = self.active_connections.get(teacher_id, set()).copy()

        disconnected = []
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to teacher {teacher_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self.active_connections.get(teacher_id, set()).discard(ws)
                    self.all_teachers.discard(ws)

    async def broadcast_to_all_teachers(self, message: dict):
        """Broadcast a message to all connected teachers."""
        async with self._lock:
            connections = self.all_teachers.copy()

        disconnected = []
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast: {e}")
                disconnected.append(websocket)

        # Clean up disconnected
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self.all_teachers.discard(ws)

    def get_connected_count(self) -> int:
        """Get number of connected teachers."""
        return len(self.all_teachers)

    def is_teacher_connected(self, teacher_id: str) -> bool:
        """Check if a specific teacher is connected."""
        return teacher_id in self.active_connections and len(self.active_connections[teacher_id]) > 0


# Global connection manager
alert_manager = AlertConnectionManager()


def get_alert_manager() -> AlertConnectionManager:
    """Dependency to get the alert manager."""
    return alert_manager


@router.websocket("/ws/teacher/alerts")
async def websocket_teacher_alerts(
    websocket: WebSocket,
    token: str = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time teacher alerts.

    **Authentication:**
    Pass JWT token as query parameter: ws://host/ws/teacher/alerts?token=xxx

    **Message Types Received:**
    - `ping`: Keepalive, responds with `pong`
    - `subscribe`: Subscribe to specific alert types

    **Message Types Sent:**
    - `alert`: New alert notification
    - `alert_update`: Alert status change
    - `pong`: Response to ping
    - `connected`: Connection confirmation

    **Example Alert Message:**
    ```json
    {
        "type": "alert",
        "data": {
            "alert_id": "alert_xxx",
            "severity": "critical",
            "student_id": "student_001",
            "message": "Alta dependencia de IA detectada",
            "timestamp": "2026-01-04T12:00:00Z"
        }
    }
    ```
    """
    from ..security import get_user_id_from_token

    # Validate token
    teacher_id = None
    if token:
        teacher_id = get_user_id_from_token(token)

    if not teacher_id:
        # Allow connection but mark as anonymous in dev mode
        import os
        if os.getenv("ENVIRONMENT") == "development":
            teacher_id = "anonymous_teacher"
        else:
            await websocket.close(code=4001, reason="Authentication required")
            return

    try:
        await alert_manager.connect(websocket, teacher_id)

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {
                "teacher_id": teacher_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Conectado al sistema de alertas en tiempo real"
            }
        })

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages with timeout for keepalive
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0  # 60 second timeout
                )

                # Handle incoming messages
                msg_type = data.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                elif msg_type == "subscribe":
                    # Handle subscription to specific alert types (future feature)
                    await websocket.send_json({
                        "type": "subscribed",
                        "data": data.get("filters", {})
                    })

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {teacher_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        await alert_manager.disconnect(websocket, teacher_id)


# =====================================================================
# HELPER FUNCTIONS FOR SENDING ALERTS
# =====================================================================


async def send_alert_notification(
    alert_id: str,
    severity: str,
    student_id: str,
    message: str,
    teacher_id: Optional[str] = None,
    extra_data: Optional[dict] = None,
):
    """
    Send an alert notification to teachers.

    If teacher_id is specified, sends only to that teacher.
    Otherwise broadcasts to all connected teachers.

    Args:
        alert_id: Unique alert identifier
        severity: Alert severity (critical, high, medium, low)
        student_id: ID of the student
        message: Human-readable alert message
        teacher_id: Optional specific teacher to notify
        extra_data: Additional data to include
    """
    notification = {
        "type": "alert",
        "data": {
            "alert_id": alert_id,
            "severity": severity,
            "student_id": student_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(extra_data or {})
        }
    }

    if teacher_id:
        await alert_manager.send_to_teacher(teacher_id, notification)
    else:
        await alert_manager.broadcast_to_all_teachers(notification)

    logger.info(
        "Alert notification sent",
        extra={
            "alert_id": alert_id,
            "severity": severity,
            "student_id": student_id,
            "target": teacher_id or "broadcast"
        }
    )


async def send_alert_update(
    alert_id: str,
    new_status: str,
    updated_by: str,
):
    """
    Broadcast an alert status update to all teachers.

    Args:
        alert_id: Alert that was updated
        new_status: New status (acknowledged, in_progress, resolved)
        updated_by: Teacher who updated the alert
    """
    notification = {
        "type": "alert_update",
        "data": {
            "alert_id": alert_id,
            "new_status": new_status,
            "updated_by": updated_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    await alert_manager.broadcast_to_all_teachers(notification)


# =====================================================================
# REST ENDPOINT FOR MANUAL NOTIFICATION TRIGGERS
# =====================================================================


@router.post(
    "/alerts/notify",
    summary="Enviar notificación de alerta",
    description="Endpoint para enviar notificaciones manuales de alerta. Requiere rol admin."
)
async def trigger_alert_notification(
    alert_id: str = Query(..., description="ID de la alerta"),
    severity: str = Query(..., description="Severidad: critical, high, medium, low"),
    student_id: str = Query(..., description="ID del estudiante"),
    message: str = Query(..., description="Mensaje de la alerta"),
    teacher_id: Optional[str] = Query(None, description="ID del docente (opcional, broadcast si no se especifica)"),
):
    """
    Trigger a manual alert notification.

    This endpoint allows other parts of the system to send
    real-time notifications to teachers.
    """
    await send_alert_notification(
        alert_id=alert_id,
        severity=severity,
        student_id=student_id,
        message=message,
        teacher_id=teacher_id
    )

    return {
        "success": True,
        "message": f"Notificación enviada: {alert_id}",
        "connected_teachers": alert_manager.get_connected_count()
    }


@router.get(
    "/alerts/connections",
    summary="Estado de conexiones WebSocket",
    description="Obtiene el estado de las conexiones WebSocket de alertas."
)
async def get_websocket_status():
    """Get WebSocket connection status."""
    return {
        "success": True,
        "data": {
            "connected_teachers": alert_manager.get_connected_count(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
