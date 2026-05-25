"""
Dashboard API routes — Aggregate statistics for the dashboard.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.models.scan import ScanStatus
from app.utils.helpers import scan_store

logger = logging.getLogger("zerotrust.api.dashboard")
router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get aggregate statistics for the dashboard."""
    all_scans = list(scan_store.values())
    completed_scans = [s for s in all_scans if s.status == ScanStatus.COMPLETED]
    running_scans = [s for s in all_scans if s.status == ScanStatus.RUNNING]

    total_vulns = sum(len(s.vulnerabilities) for s in completed_scans)
    total_pages = sum(s.pages_crawled for s in completed_scans)
    total_endpoints = sum(s.endpoints_tested for s in completed_scans)

    # Severity aggregation
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    type_counts: dict[str, int] = {}

    for s in completed_scans:
        for v in s.vulnerabilities:
            severity_counts[v.severity.value] += 1
            type_counts[v.type.value] = type_counts.get(v.type.value, 0) + 1

    # Average risk score
    avg_risk = 0.0
    if completed_scans:
        avg_risk = round(sum(s.risk_score for s in completed_scans) / len(completed_scans), 1)

    # Recent scans (last 10)
    recent = sorted(all_scans, key=lambda s: s.started_at, reverse=True)[:10]

    return {
        "total_scans": len(all_scans),
        "completed_scans": len(completed_scans),
        "running_scans": len(running_scans),
        "total_vulnerabilities": total_vulns,
        "total_pages_crawled": total_pages,
        "total_endpoints_tested": total_endpoints,
        "average_risk_score": avg_risk,
        "severity_breakdown": severity_counts,
        "type_breakdown": type_counts,
        "recent_scans": [
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
            for s in recent
        ],
    }
