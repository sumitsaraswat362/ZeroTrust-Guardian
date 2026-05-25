"""
ZeroTrust Guardian — AI-Powered Digital Safety Platform
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import scan, reports, dashboard, analyze
from app.utils.helpers import scan_store, ws_manager

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("zerotrust")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup / shutdown hooks."""
    logger.info("ZeroTrust Guardian starting up …")
    logger.info("CORS origins: %s", settings.cors_origins)
    logger.info("Gemini API key: %s", "configured ✓" if settings.gemini_api_key else "not set ✗")
    yield
    logger.info("ZeroTrust Guardian shutting down …")


app = FastAPI(
    title="ZeroTrust Guardian",
    description="AI-powered digital safety platform — protecting everyday users from scams, phishing, and deceptive websites",
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST Routes ──────────────────────────────────────────────────────────────
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(scan.router, prefix="/api", tags=["Scans"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])


# ── WebSocket endpoint for real-time scan progress ──────────────────────────
@app.websocket("/ws/scan/{scan_id}")
async def websocket_scan_progress(websocket: WebSocket, scan_id: str):
    """Stream real-time scan progress to the frontend via WebSocket."""
    try:
        await ws_manager.connect(scan_id, websocket)
    except Exception:
        return

    try:
        while True:
            # Keep connection alive; we push messages from the scan pipeline.
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(scan_id, websocket)
    except Exception:
        ws_manager.disconnect(scan_id, websocket)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    from app.models.scan import ScanStatus

    return {
        "status": "healthy",
        "service": "ZeroTrust Guardian",
        "version": "3.0.0",
        "active_scans": sum(
            1 for s in scan_store.values() if s.status == ScanStatus.RUNNING
        ),
        "total_scans": len(scan_store),
        "gemini_configured": bool(settings.gemini_api_key),
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
