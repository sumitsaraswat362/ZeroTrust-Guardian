"""
Reports API routes — Get detailed reports for completed scans.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.scan import ScanStatus
from app.utils.helpers import scan_store

logger = logging.getLogger("zerotrust.api.reports")
router = APIRouter()


@router.get("/reports")
async def list_reports():
    """List all completed scan reports."""
    completed = [
        s for s in scan_store.values()
        if s.status == ScanStatus.COMPLETED
    ]
    completed.sort(key=lambda s: s.completed_at or s.started_at, reverse=True)

    return {
        "reports": [
            {
                "scan_id": s.id,
                "target_url": s.target_url,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "vulnerability_count": len(s.vulnerabilities),
                "risk_score": s.risk_score,
                "risk_level": _risk_level(s.risk_score),
                "summary": s.summary,
                "scan_duration_seconds": s.scan_duration_seconds,
                "pages_crawled": s.pages_crawled,
                "endpoints_tested": s.endpoints_tested,
            }
            for s in completed
        ],
        "total": len(completed),
    }


@router.get("/reports/{scan_id}")
async def get_report(scan_id: str):
    """Get a detailed report for a specific scan."""
    scan_result = scan_store.get(scan_id)
    if not scan_result:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    if scan_result.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scan {scan_id} is not completed yet (status: {scan_result.status.value})",
        )

    # Build detailed report
    severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    type_breakdown: dict[str, int] = {}

    for v in scan_result.vulnerabilities:
        severity_breakdown[v.severity.value] += 1
        type_breakdown[v.type.value] = type_breakdown.get(v.type.value, 0) + 1

    # Generate executive summary
    total = len(scan_result.vulnerabilities)
    risk_score = scan_result.risk_score
    level = _risk_level(risk_score)

    if total == 0:
        executive_summary = (
            f"Security scan of {scan_result.target_url} completed. "
            f"No vulnerabilities were discovered."
        )
    else:
        executive_summary = (
            f"Security scan of {scan_result.target_url} identified {total} "
            f"vulnerability(ies) with a risk score of {risk_score}/100 ({level}). "
        )
        if severity_breakdown["critical"] > 0:
            executive_summary += (
                f"{severity_breakdown['critical']} critical issue(s) require immediate remediation. "
            )
        if severity_breakdown["high"] > 0:
            executive_summary += (
                f"{severity_breakdown['high']} high-severity issue(s) need urgent attention. "
            )

    # Prioritized remediation
    remediation: list[dict] = []
    seen_types: set[str] = set()
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_vulns = sorted(
        scan_result.vulnerabilities,
        key=lambda v: severity_order.get(v.severity.value, 5),
    )
    for v in sorted_vulns:
        if v.type.value not in seen_types:
            seen_types.add(v.type.value)
            remediation.append({
                "priority": len(remediation) + 1,
                "severity": v.severity.value,
                "type": v.type.value,
                "title": v.title,
                "remediation": v.remediation,
            })

    return {
        "scan_id": scan_result.id,
        "target_url": scan_result.target_url,
        "status": scan_result.status.value,
        "risk_score": risk_score,
        "risk_level": level,
        "executive_summary": executive_summary,
        "started_at": scan_result.started_at.isoformat(),
        "completed_at": scan_result.completed_at.isoformat() if scan_result.completed_at else None,
        "scan_duration_seconds": scan_result.scan_duration_seconds,
        "statistics": {
            "total_vulnerabilities": total,
            "by_severity": severity_breakdown,
            "by_type": type_breakdown,
            "pages_crawled": scan_result.pages_crawled,
            "endpoints_tested": scan_result.endpoints_tested,
        },
        "remediation_plan": remediation,
        "vulnerabilities": [v.model_dump(mode="json") for v in scan_result.vulnerabilities],
    }


def _risk_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    elif score > 0:
        return "LOW"
    return "SECURE"
