"""Data models package."""

from app.models.vulnerability import (
    SeverityLevel,
    VulnerabilityType,
    Vulnerability,
)
from app.models.scan import ScanStatus, ScanConfig, ScanRequest, ScanResult

__all__ = [
    "SeverityLevel",
    "VulnerabilityType",
    "Vulnerability",
    "ScanStatus",
    "ScanConfig",
    "ScanRequest",
    "ScanResult",
]
