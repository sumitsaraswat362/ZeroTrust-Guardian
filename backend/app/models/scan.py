"""
Scan request / response data models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.vulnerability import Vulnerability


class ScanStatus(str, Enum):
    """Lifecycle states of a scan."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanConfig(BaseModel):
    """User-supplied configuration for a scan run."""
    max_depth: int = Field(default=3, ge=1, le=10, description="Max crawl depth")
    max_pages: int = Field(default=50, ge=1, le=500, description="Max pages to crawl")
    scan_headers: bool = Field(default=True, description="Check security headers")
    scan_cors: bool = Field(default=True, description="Check CORS policy")
    scan_xss: bool = Field(default=True, description="Test for XSS")
    scan_sqli: bool = Field(default=True, description="Test for SQL injection")
    scan_prompt_injection: bool = Field(
        default=True, description="Test AI endpoints for prompt injection"
    )
    custom_headers: dict[str, str] = Field(
        default_factory=dict, description="Extra headers to send with requests"
    )


class ScanRequest(BaseModel):
    """Incoming request to start a new scan."""
    target_url: str = Field(..., description="URL to scan")
    scan_config: ScanConfig = Field(default_factory=ScanConfig)


class ScanResult(BaseModel):
    """Full result object for a completed (or in-progress) scan."""

    id: str
    target_url: str
    status: ScanStatus = ScanStatus.QUEUED
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    pages_crawled: int = 0
    endpoints_tested: int = 0
    scan_duration_seconds: float = 0.0
    risk_score: float = 0.0
    summary: dict = Field(default_factory=dict)

    def compute_risk_score(self) -> float:
        """Calculate a 0-100 risk score based on vulnerability counts and severities."""
        weights = {
            "critical": 25.0,
            "high": 15.0,
            "medium": 8.0,
            "low": 3.0,
            "info": 1.0,
        }
        raw = sum(weights.get(v.severity.value, 0) for v in self.vulnerabilities)
        # Sigmoid-like clamping to [0, 100]
        score = min(100.0, raw)
        return round(score, 1)

    def build_summary(self) -> dict:
        """Build a stats breakdown by severity and type."""
        by_severity: dict[str, int] = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
        }
        by_type: dict[str, int] = {}
        for v in self.vulnerabilities:
            by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1
            by_type[v.type.value] = by_type.get(v.type.value, 0) + 1
        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": by_severity,
            "by_type": by_type,
            "pages_crawled": self.pages_crawled,
            "endpoints_tested": self.endpoints_tested,
        }
