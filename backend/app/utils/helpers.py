"""
Shared helpers: in-memory store, WebSocket connection manager, ID generation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.models.scan import ScanResult

logger = logging.getLogger("zerotrust.helpers")

# ─────────────────────────────────────────────────────────────────────────────
# In-memory scan store  (swap for a DB adapter later)
# ─────────────────────────────────────────────────────────────────────────────
scan_store: dict[str, ScanResult] = {}


def generate_id(prefix: str = "scan") -> str:
    """Generate a short unique ID like ``scan-a1b2c3d4``."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket connection manager
# ─────────────────────────────────────────────────────────────────────────────
class WebSocketManager:
    """Manages per-scan WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        # scan_id -> list of active websocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, scan_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(scan_id, []).append(ws)
        logger.debug("WS connected for scan %s (total: %d)", scan_id, len(self._connections[scan_id]))

    def disconnect(self, scan_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(scan_id, [])
        if ws in conns:
            conns.remove(ws)
        logger.debug("WS disconnected for scan %s", scan_id)

    async def broadcast(self, scan_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to every client listening on *scan_id*."""
        conns = self._connections.get(scan_id, [])
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(scan_id, ws)

    async def send_progress(
        self,
        scan_id: str,
        *,
        phase: str,
        message: str,
        progress: float,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Convenience wrapper to broadcast a structured progress event."""
        payload: dict[str, Any] = {
            "type": "progress",
            "scan_id": scan_id,
            "phase": phase,
            "message": message,
            "progress": round(progress, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if data:
            payload["data"] = data
        await self.broadcast(scan_id, payload)

    async def send_vulnerability(self, scan_id: str, vuln_dict: dict) -> None:
        """Push a newly-discovered vulnerability to clients."""
        await self.broadcast(scan_id, {
            "type": "vulnerability",
            "scan_id": scan_id,
            "vulnerability": vuln_dict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def send_complete(self, scan_id: str, summary: dict) -> None:
        """Notify clients the scan is finished."""
        await self.broadcast(scan_id, {
            "type": "complete",
            "scan_id": scan_id,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def send_error(self, scan_id: str, error: str) -> None:
        """Notify clients of a scan error."""
        await self.broadcast(scan_id, {
            "type": "error",
            "scan_id": scan_id,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# Singleton
ws_manager = WebSocketManager()
