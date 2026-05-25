"""
Security Headers Scanner — Checks for missing or misconfigured HTTP security headers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("zerotrust.scanners.headers")


@dataclass
class HeaderCheckResult:
    """Result of checking a single security header."""
    header_name: str
    present: bool
    value: str
    is_secure: bool
    severity: str
    recommendation: str


@dataclass
class HeaderScanResult:
    """Complete result of scanning all security headers for a URL."""
    url: str
    checks: list[HeaderCheckResult] = field(default_factory=list)
    missing_count: int = 0
    insecure_count: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Header definitions with expected values and recommendations
# ─────────────────────────────────────────────────────────────────────────────

SECURITY_HEADERS = [
    {
        "name": "Content-Security-Policy",
        "severity": "high",
        "recommendation": (
            "Add a Content-Security-Policy header to prevent XSS and data injection attacks. "
            "Example: Content-Security-Policy: default-src 'self'; script-src 'self'"
        ),
        "insecure_values": ["unsafe-inline", "unsafe-eval", "*"],
    },
    {
        "name": "X-Frame-Options",
        "severity": "medium",
        "recommendation": (
            "Add X-Frame-Options header to prevent clickjacking attacks. "
            "Set to DENY or SAMEORIGIN."
        ),
        "insecure_values": ["ALLOWALL"],
    },
    {
        "name": "X-Content-Type-Options",
        "severity": "medium",
        "recommendation": (
            "Add X-Content-Type-Options: nosniff to prevent MIME-type sniffing attacks."
        ),
        "insecure_values": [],
    },
    {
        "name": "Strict-Transport-Security",
        "severity": "high",
        "recommendation": (
            "Add Strict-Transport-Security (HSTS) header to enforce HTTPS. "
            "Example: Strict-Transport-Security: max-age=31536000; includeSubDomains"
        ),
        "insecure_values": [],
    },
    {
        "name": "X-XSS-Protection",
        "severity": "low",
        "recommendation": (
            "Add X-XSS-Protection: 1; mode=block to enable the browser's XSS filter. "
            "Note: Modern browsers are deprecating this in favour of CSP."
        ),
        "insecure_values": ["0"],
    },
    {
        "name": "Referrer-Policy",
        "severity": "low",
        "recommendation": (
            "Add Referrer-Policy header to control referrer information. "
            "Recommended: Referrer-Policy: strict-origin-when-cross-origin"
        ),
        "insecure_values": ["unsafe-url", "no-referrer-when-downgrade"],
    },
    {
        "name": "Permissions-Policy",
        "severity": "low",
        "recommendation": (
            "Add Permissions-Policy header to control browser feature access. "
            "Example: Permissions-Policy: geolocation=(), camera=(), microphone=()"
        ),
        "insecure_values": [],
    },
    {
        "name": "Cache-Control",
        "severity": "info",
        "recommendation": (
            "Set appropriate Cache-Control headers for sensitive pages. "
            "Example: Cache-Control: no-store, no-cache, must-revalidate"
        ),
        "insecure_values": [],
    },
]

# Headers that leak server information
INFO_DISCLOSURE_HEADERS = [
    "Server",
    "X-Powered-By",
    "X-AspNet-Version",
    "X-AspNetMvc-Version",
    "X-Runtime",
    "X-Version",
    "X-Debug",
]


class HeaderScanner:
    """Scans HTTP response headers for security issues."""

    def __init__(self, custom_headers: dict[str, str] | None = None) -> None:
        self.custom_headers = custom_headers or {}

    async def scan(self, url: str) -> HeaderScanResult:
        """
        Fetch the URL and analyze its response headers.

        Args:
            url: The URL to check headers for.

        Returns:
            HeaderScanResult with all findings.
        """
        result = HeaderScanResult(url=url)

        try:
            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=True, verify=False,
                headers={"User-Agent": "Mozilla/5.0", **self.custom_headers},
            ) as client:
                resp = await client.get(url)
        except Exception as exc:
            logger.warning("Failed to fetch %s for header scan: %s", url, exc)
            return result

        headers = resp.headers

        # Check security headers
        for header_def in SECURITY_HEADERS:
            name = header_def["name"]
            value = headers.get(name, "")
            present = bool(value)

            is_secure = present
            if present and header_def["insecure_values"]:
                for bad_val in header_def["insecure_values"]:
                    if bad_val.lower() in value.lower():
                        is_secure = False
                        break

            if not present:
                result.missing_count += 1
            if not is_secure:
                result.insecure_count += 1

            result.checks.append(HeaderCheckResult(
                header_name=name,
                present=present,
                value=value,
                is_secure=is_secure,
                severity=header_def["severity"] if not is_secure else "info",
                recommendation=header_def["recommendation"] if not is_secure else "",
            ))

        # Check for information disclosure headers
        for header_name in INFO_DISCLOSURE_HEADERS:
            value = headers.get(header_name, "")
            if value:
                result.checks.append(HeaderCheckResult(
                    header_name=header_name,
                    present=True,
                    value=value,
                    is_secure=False,
                    severity="low",
                    recommendation=(
                        f"Remove or suppress the '{header_name}' header to prevent "
                        f"server technology disclosure. Current value: '{value}'"
                    ),
                ))
                result.insecure_count += 1

        logger.info(
            "Header scan on %s: %d missing, %d insecure",
            url, result.missing_count, result.insecure_count,
        )
        return result
