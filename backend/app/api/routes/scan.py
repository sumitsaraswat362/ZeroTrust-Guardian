"""
Scan API routes — Start scans, get scan status, list scans.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config import settings
from app.models.scan import ScanRequest, ScanResult, ScanStatus
from app.agents.orchestrator import Orchestrator
from app.utils.helpers import scan_store, generate_id

logger = logging.getLogger("zerotrust.api.scan")
router = APIRouter()


def _is_safe_url(url: str) -> bool:
    """Validate URL and prevent SSRF by blocking private/internal IPs."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False

        # Allow localhost for local testing/demo, but in pure production
        # you would block it. We allow it here because the vulnerable app
        # runs on localhost:4000
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return True

        # Resolve IP to check for private ranges
        try:
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            # If it's a private network but not loopback, block it (SSRF protection)
            if ip_obj.is_private and not ip_obj.is_loopback:
                return False
        except socket.gaierror:
            # If we can't resolve it, it might be a local docker hostname or invalid
            pass
            
        return True
    except Exception:
        return False


@router.post("/scan", response_model=dict)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start a new security scan.

    Creates a scan job and runs it in the background. Returns the scan ID
    immediately so the client can connect via WebSocket for live updates.
    """
    # Rate Limiting
    active_scans = sum(1 for s in scan_store.values() if s.status == ScanStatus.RUNNING)
    if active_scans >= settings.max_concurrent_scans:
        raise HTTPException(
            status_code=429, 
            detail=f"Too many active scans. Maximum {settings.max_concurrent_scans} allowed."
        )

    scan_id = generate_id("scan")

    # Normalize URL
    target_url = request.target_url.strip()
    if not target_url.startswith("http"):
        target_url = f"http://{target_url}"

    # Validate URL (SSRF protection)
    if not _is_safe_url(target_url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid or unsafe target URL. Internal IP ranges are blocked."
        )

    # Create scan result entry
    scan_result = ScanResult(
        id=scan_id,
        target_url=target_url,
        status=ScanStatus.QUEUED,
    )
    scan_store[scan_id] = scan_result

    logger.info("Scan %s created for %s", scan_id, target_url)

    # Run the scan in background
    background_tasks.add_task(_run_scan, scan_id, target_url, request.scan_config)

    # Return relative WS path, client should construct full URL
    return {
        "scan_id": scan_id,
        "status": "queued",
        "target_url": target_url,
        "message": f"Scan queued. Connect to WebSocket at /ws/scan/{scan_id} for live updates.",
    }


async def _run_scan(scan_id: str, target_url: str, config):
    """Background task that runs the full scan pipeline."""
    try:
        orchestrator = Orchestrator(
            scan_id=scan_id,
            target_url=target_url,
            config=config,
        )
        await orchestrator.run()
    except Exception as exc:
        logger.exception("Scan %s failed: %s", scan_id, exc)
        scan_result = scan_store.get(scan_id)
        if scan_result:
            scan_result.status = ScanStatus.FAILED


@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str):
    """Get the current status and results of a scan."""
    scan_result = scan_store.get(scan_id)
    if not scan_result:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return scan_result.model_dump(mode="json")


@router.get("/scans")
async def list_scans():
    """List all scans, most recent first."""
    scans = sorted(
        scan_store.values(),
        key=lambda s: s.started_at,
        reverse=True,
    )
    return {
        "scans": [
            {
                "id": s.id,
                "target_url": s.target_url,
                "status": s.status.value,
                "started_at": s.started_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "vulnerability_count": len(s.vulnerabilities),
                "risk_score": s.risk_score,
                "pages_crawled": s.pages_crawled,
                "scan_duration_seconds": s.scan_duration_seconds,
            }
            for s in scans
        ],
        "total": len(scans),
    }
