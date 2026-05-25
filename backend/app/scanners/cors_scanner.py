"""
CORS Misconfiguration Scanner — Checks for overly permissive CORS policies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("zerotrust.scanners.cors")


@dataclass
class CORSCheckResult:
    """Result of a single CORS check."""
    test_name: str
    origin_sent: str
    acao_received: str  # Access-Control-Allow-Origin
    acac_received: str  # Access-Control-Allow-Credentials
    is_vulnerable: bool
    severity: str
    description: str


@dataclass
class CORSScanResult:
    """Complete CORS scan result for a URL."""
    url: str
    checks: list[CORSCheckResult] = field(default_factory=list)
    is_vulnerable: bool = False


class CORSScanner:
    """Tests for CORS misconfigurations that could allow cross-origin attacks."""

    def __init__(self, custom_headers: dict[str, str] | None = None) -> None:
        self.custom_headers = custom_headers or {}

    async def scan(self, url: str) -> CORSScanResult:
        """Run all CORS misconfiguration checks against a URL."""
        result = CORSScanResult(url=url)

        test_cases = [
            {
                "name": "Wildcard origin with credentials",
                "origin": "https://evil-attacker.com",
                "description": (
                    "Server reflects arbitrary Origin and allows credentials, "
                    "enabling any website to make authenticated cross-origin requests."
                ),
                "severity": "critical",
            },
            {
                "name": "Null origin allowed",
                "origin": "null",
                "description": (
                    "Server allows 'null' Origin, which can be exploited via "
                    "sandboxed iframes to bypass same-origin policy."
                ),
                "severity": "high",
            },
            {
                "name": "Subdomain wildcard reflection",
                "origin": "https://evil.target.com",
                "description": (
                    "Server reflects subdomain origins without proper validation, "
                    "vulnerable to subdomain takeover attacks."
                ),
                "severity": "high",
            },
            {
                "name": "HTTP origin on HTTPS endpoint",
                "origin": "http://evil.com",
                "description": (
                    "HTTPS endpoint allows HTTP origins, enabling "
                    "man-in-the-middle attacks on CORS requests."
                ),
                "severity": "medium",
            },
            {
                "name": "Origin suffix bypass",
                "origin": "https://notlegit-example.com",
                "description": (
                    "Server validates Origin by suffix matching, "
                    "allowing attacker-controlled domains that end with the target domain."
                ),
                "severity": "high",
            },
        ]

        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, verify=False,
            headers={"User-Agent": "Mozilla/5.0", **self.custom_headers},
        ) as client:
            for test in test_cases:
                try:
                    check = await self._check_cors(client, url, test)
                    result.checks.append(check)
                    if check.is_vulnerable:
                        result.is_vulnerable = True
                except Exception as exc:
                    logger.debug("CORS check error on %s: %s", url, exc)

            # Also check if wildcard * is used
            try:
                check = await self._check_wildcard(client, url)
                result.checks.append(check)
                if check.is_vulnerable:
                    result.is_vulnerable = True
            except Exception as exc:
                logger.debug("CORS wildcard check error: %s", exc)

        logger.info("CORS scan on %s: vulnerable=%s", url, result.is_vulnerable)
        return result

    async def _check_cors(
        self, client: httpx.AsyncClient, url: str, test: dict,
    ) -> CORSCheckResult:
        """Send a request with a crafted Origin header and analyze the CORS response."""
        resp = await client.get(
            url,
            headers={"Origin": test["origin"], **self.custom_headers},
        )

        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        acac = resp.headers.get("Access-Control-Allow-Credentials", "")

        # Check if the origin is reflected
        is_vulnerable = False
        if acao == test["origin"]:
            is_vulnerable = True
        if acao == "*" and acac.lower() == "true":
            is_vulnerable = True
        if test["origin"] == "null" and acao == "null":
            is_vulnerable = True

        return CORSCheckResult(
            test_name=test["name"],
            origin_sent=test["origin"],
            acao_received=acao,
            acac_received=acac,
            is_vulnerable=is_vulnerable,
            severity=test["severity"] if is_vulnerable else "info",
            description=test["description"] if is_vulnerable else "Passed",
        )

    async def _check_wildcard(
        self, client: httpx.AsyncClient, url: str,
    ) -> CORSCheckResult:
        """Check if the server uses Access-Control-Allow-Origin: * (wildcard)."""
        resp = await client.get(url)
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        acac = resp.headers.get("Access-Control-Allow-Credentials", "")

        is_vulnerable = acao == "*"
        severity = "medium" if is_vulnerable else "info"

        # Wildcard + credentials is critical
        if is_vulnerable and acac.lower() == "true":
            severity = "critical"

        return CORSCheckResult(
            test_name="Wildcard Access-Control-Allow-Origin",
            origin_sent="(none)",
            acao_received=acao,
            acac_received=acac,
            is_vulnerable=is_vulnerable,
            severity=severity,
            description=(
                "Server uses Access-Control-Allow-Origin: * which allows any website to "
                "read responses from this endpoint. Combined with Allow-Credentials, "
                "this enables full cross-origin data theft."
            ) if is_vulnerable else "Passed",
        )
