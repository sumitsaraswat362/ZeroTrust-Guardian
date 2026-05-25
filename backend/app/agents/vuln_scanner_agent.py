"""
Vulnerability Scanner Agent — Tests for classic web vulnerabilities (XSS, SQLi, Headers, CORS).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.vulnerability import Vulnerability, VulnerabilityType, SeverityLevel
from app.scanners.xss_scanner import XSSScanner
from app.scanners.sqli_scanner import SQLiScanner
from app.scanners.header_scanner import HeaderScanner
from app.scanners.cors_scanner import CORSScanner
from app.scanners.crawler import CrawlResult
from app.utils.helpers import generate_id, ws_manager

logger = logging.getLogger("zerotrust.agents.vuln_scanner")


class VulnScannerAgent:
    """
    Agent 3: Traditional Vulnerability Scanner.

    Tests the target for classic web vulnerabilities:
    - XSS (reflected/stored)
    - SQL Injection
    - Missing/misconfigured security headers
    - CORS misconfigurations
    """

    def __init__(
        self,
        scan_id: str,
        scan_xss: bool = True,
        scan_sqli: bool = True,
        scan_headers: bool = True,
        scan_cors: bool = True,
        custom_headers: dict[str, str] | None = None,
    ) -> None:
        self.scan_id = scan_id
        self.scan_xss = scan_xss
        self.scan_sqli = scan_sqli
        self.scan_headers = scan_headers
        self.scan_cors = scan_cors
        self.custom_headers = custom_headers or {}

    async def run(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Run all enabled vulnerability scans."""
        vulnerabilities: list[Vulnerability] = []

        await ws_manager.send_progress(
            self.scan_id,
            phase="vuln_scan",
            message="🛡️ Starting vulnerability scanning phase",
            progress=0.50,
        )

        # ── XSS Scanning ────────────────────────────────────────────────
        if self.scan_xss and crawl_result.forms:
            await ws_manager.send_progress(
                self.scan_id,
                phase="vuln_scan",
                message=f"⚡ Testing {len(crawl_result.forms)} form(s) for XSS",
                progress=0.52,
            )
            xss_vulns = await self._scan_xss(crawl_result)
            vulnerabilities.extend(xss_vulns)

        # ── SQL Injection Scanning ───────────────────────────────────────
        if self.scan_sqli and crawl_result.forms:
            await ws_manager.send_progress(
                self.scan_id,
                phase="vuln_scan",
                message=f"💉 Testing {len(crawl_result.forms)} form(s) for SQL injection",
                progress=0.60,
            )
            sqli_vulns = await self._scan_sqli(crawl_result)
            vulnerabilities.extend(sqli_vulns)

        # ── Security Headers ─────────────────────────────────────────────
        if self.scan_headers and crawl_result.pages:
            await ws_manager.send_progress(
                self.scan_id,
                phase="vuln_scan",
                message="🔒 Checking security headers",
                progress=0.70,
            )
            header_vulns = await self._scan_headers(crawl_result)
            vulnerabilities.extend(header_vulns)

        # ── CORS ─────────────────────────────────────────────────────────
        if self.scan_cors and crawl_result.pages:
            await ws_manager.send_progress(
                self.scan_id,
                phase="vuln_scan",
                message="🌐 Testing CORS configuration",
                progress=0.78,
            )
            cors_vulns = await self._scan_cors(crawl_result)
            vulnerabilities.extend(cors_vulns)

        await ws_manager.send_progress(
            self.scan_id,
            phase="vuln_scan",
            message=f"✅ Vulnerability scan complete — {len(vulnerabilities)} issues found",
            progress=0.85,
        )

        return vulnerabilities

    async def _scan_xss(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Run XSS tests on all discovered forms."""
        vulns: list[Vulnerability] = []
        scanner = XSSScanner(custom_headers=self.custom_headers)

        for form in crawl_result.forms:
            try:
                fields_dicts = [
                    {"name": f.name, "field_type": f.field_type, "value": f.value}
                    for f in form.fields
                ]
                results = await scanner.scan_form(form.action, form.method, fields_dicts)

                for result in results:
                    vuln = Vulnerability(
                        id=generate_id("vuln"),
                        type=VulnerabilityType.XSS,
                        severity=SeverityLevel.HIGH,
                        title=f"Reflected XSS in '{result.parameter}' parameter",
                        description=(
                            f"The form at {form.page_url} (action: {result.url}) is vulnerable "
                            f"to Cross-Site Scripting (XSS). The '{result.parameter}' parameter "
                            f"reflects user input without proper sanitization or encoding."
                        ),
                        endpoint=result.url,
                        evidence=result.evidence[:300],
                        remediation=(
                            "Encode all user-supplied output using context-aware encoding "
                            "(HTML entity encoding, JavaScript encoding, URL encoding). "
                            "Implement a Content-Security-Policy header. "
                            "Use frameworks that auto-escape output (React, Angular)."
                        ),
                        payload_used=result.payload[:200],
                        timestamp=datetime.now(timezone.utc),
                    )
                    vulns.append(vuln)
                    await ws_manager.send_vulnerability(
                        self.scan_id, vuln.model_dump(mode="json"),
                    )

            except Exception as exc:
                logger.warning("XSS scan error on form %s: %s", form.action, exc)

        return vulns

    async def _scan_sqli(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Run SQL injection tests on all discovered forms."""
        vulns: list[Vulnerability] = []
        scanner = SQLiScanner(custom_headers=self.custom_headers)

        for form in crawl_result.forms:
            try:
                fields_dicts = [
                    {"name": f.name, "field_type": f.field_type, "value": f.value}
                    for f in form.fields
                ]
                results = await scanner.scan_form(form.action, form.method, fields_dicts)

                for result in results:
                    severity = SeverityLevel.CRITICAL if result.info_leaked else SeverityLevel.HIGH

                    vuln = Vulnerability(
                        id=generate_id("vuln"),
                        type=VulnerabilityType.SQLI,
                        severity=severity,
                        title=f"SQL Injection in '{result.parameter}' parameter",
                        description=(
                            f"The form at {result.url} is vulnerable to SQL injection "
                            f"via the '{result.parameter}' parameter. "
                            f"{'Database information was leaked in error messages. ' if result.info_leaked else ''}"
                            f"Matched patterns: {', '.join(result.matched_patterns[:5])}"
                        ),
                        endpoint=result.url,
                        evidence=result.evidence[:300],
                        remediation=(
                            "Use parameterized queries / prepared statements instead of "
                            "string concatenation. Implement input validation. "
                            "Use an ORM layer. Suppress detailed error messages in production."
                        ),
                        payload_used=result.payload[:200],
                        timestamp=datetime.now(timezone.utc),
                    )
                    vulns.append(vuln)
                    await ws_manager.send_vulnerability(
                        self.scan_id, vuln.model_dump(mode="json"),
                    )

            except Exception as exc:
                logger.warning("SQLi scan error on form %s: %s", form.action, exc)

        return vulns

    async def _scan_headers(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Check security headers on the main page."""
        vulns: list[Vulnerability] = []
        scanner = HeaderScanner(custom_headers=self.custom_headers)

        # Only check the first page (main URL) to avoid duplicates
        target_url = crawl_result.pages[0] if crawl_result.pages else None
        if not target_url:
            return vulns

        try:
            result = await scanner.scan(target_url)

            for check in result.checks:
                if not check.is_secure:
                    vuln = Vulnerability(
                        id=generate_id("vuln"),
                        type=VulnerabilityType.MISSING_HEADERS,
                        severity=SeverityLevel(check.severity) if check.severity != "info" else SeverityLevel.INFO,
                        title=f"{'Missing' if not check.present else 'Insecure'} header: {check.header_name}",
                        description=(
                            f"The response from {target_url} is {'missing' if not check.present else 'has an insecure value for'} "
                            f"the '{check.header_name}' security header."
                            f"{f' Current value: {check.value}' if check.value else ''}"
                        ),
                        endpoint=target_url,
                        evidence=f"Header: {check.header_name}, Value: '{check.value or '(not set)'}', Secure: {check.is_secure}",
                        remediation=check.recommendation,
                        payload_used="",
                        timestamp=datetime.now(timezone.utc),
                    )
                    vulns.append(vuln)
                    await ws_manager.send_vulnerability(
                        self.scan_id, vuln.model_dump(mode="json"),
                    )

        except Exception as exc:
            logger.warning("Header scan error on %s: %s", target_url, exc)

        return vulns

    async def _scan_cors(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Check CORS configuration."""
        vulns: list[Vulnerability] = []
        scanner = CORSScanner(custom_headers=self.custom_headers)

        target_url = crawl_result.pages[0] if crawl_result.pages else None
        if not target_url:
            return vulns

        try:
            result = await scanner.scan(target_url)

            for check in result.checks:
                if check.is_vulnerable:
                    vuln = Vulnerability(
                        id=generate_id("vuln"),
                        type=VulnerabilityType.CORS_MISCONFIGURATION,
                        severity=SeverityLevel(check.severity),
                        title=f"CORS Misconfiguration: {check.test_name}",
                        description=(
                            f"{check.description} "
                            f"Origin sent: {check.origin_sent}. "
                            f"ACAO received: {check.acao_received}. "
                            f"ACAC received: {check.acac_received}."
                        ),
                        endpoint=target_url,
                        evidence=(
                            f"Access-Control-Allow-Origin: {check.acao_received}\n"
                            f"Access-Control-Allow-Credentials: {check.acac_received}"
                        ),
                        remediation=(
                            "Configure CORS to allow only specific, trusted origins. "
                            "Never use 'Access-Control-Allow-Origin: *' with credentials. "
                            "Validate the Origin header server-side against an allow-list."
                        ),
                        payload_used=f"Origin: {check.origin_sent}",
                        timestamp=datetime.now(timezone.utc),
                    )
                    vulns.append(vuln)
                    await ws_manager.send_vulnerability(
                        self.scan_id, vuln.model_dump(mode="json"),
                    )

        except Exception as exc:
            logger.warning("CORS scan error on %s: %s", target_url, exc)

        return vulns
