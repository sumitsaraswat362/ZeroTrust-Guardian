"""
Prompt Injection Agent — Tests discovered AI endpoints for prompt injection.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.vulnerability import Vulnerability, VulnerabilityType, SeverityLevel
from app.scanners.prompt_injection import PromptInjectionScanner
from app.scanners.crawler import CrawlResult
from app.utils.helpers import generate_id, ws_manager

logger = logging.getLogger("zerotrust.agents.prompt_injection")

SEVERITY_MAP = {
    "critical": SeverityLevel.CRITICAL,
    "high": SeverityLevel.HIGH,
    "medium": SeverityLevel.MEDIUM,
    "low": SeverityLevel.LOW,
    "info": SeverityLevel.INFO,
}


class PromptInjectionAgent:
    """
    Agent 2: Prompt Injection Testing.

    Takes discovered AI endpoints from recon and fires 50+ prompt injection
    payloads against each one, analyzing responses for signs of:
    - System prompt leakage
    - Jailbreak success
    - Credential/data extraction
    - Safety bypass
    """

    def __init__(
        self,
        scan_id: str,
        custom_headers: dict[str, str] | None = None,
    ) -> None:
        self.scan_id = scan_id
        self.scanner = PromptInjectionScanner(custom_headers=custom_headers)

    async def run(self, crawl_result: CrawlResult) -> list[Vulnerability]:
        """Test all discovered AI endpoints for prompt injection."""
        vulnerabilities: list[Vulnerability] = []

        ai_endpoints = crawl_result.ai_endpoints
        if not ai_endpoints:
            await ws_manager.send_progress(
                self.scan_id,
                phase="prompt_injection",
                message="⚠️ No AI/LLM endpoints discovered — skipping prompt injection tests",
                progress=0.45,
            )
            logger.info("[PromptInjectionAgent] No AI endpoints found, skipping")
            return vulnerabilities

        await ws_manager.send_progress(
            self.scan_id,
            phase="prompt_injection",
            message=f"🎯 Testing {len(ai_endpoints)} AI endpoint(s) for prompt injection",
            progress=0.25,
        )

        for i, endpoint in enumerate(ai_endpoints):
            logger.info("[PromptInjectionAgent] Testing %s", endpoint.url)
            await ws_manager.send_progress(
                self.scan_id,
                phase="prompt_injection",
                message=f"🧪 Testing AI endpoint: {endpoint.url}",
                progress=0.25 + (0.20 * (i + 1) / len(ai_endpoints)),
            )

            # Try common message field names
            for msg_field in ["message", "query", "prompt", "input", "text", "q", "question"]:
                try:
                    results = await self.scanner.scan_endpoint(
                        endpoint_url=endpoint.url,
                        method=endpoint.method,
                        message_field=msg_field,
                    )

                    vulnerable_results = [r for r in results if r.is_vulnerable]
                    if vulnerable_results:
                        logger.info(
                            "[PromptInjectionAgent] Found %d vulnerabilities on %s (field=%s)",
                            len(vulnerable_results), endpoint.url, msg_field,
                        )

                        for result in vulnerable_results:
                            vuln = Vulnerability(
                                id=generate_id("vuln"),
                                type=VulnerabilityType.PROMPT_INJECTION,
                                severity=SEVERITY_MAP.get(result.severity, SeverityLevel.MEDIUM),
                                title=f"Prompt Injection: {result.payload.name}",
                                description=(
                                    f"The AI endpoint at {endpoint.url} is vulnerable to "
                                    f"'{result.payload.category}' prompt injection attack "
                                    f"'{result.payload.name}'. "
                                    f"Matched indicators: {', '.join(result.matched_indicators[:5])}"
                                ),
                                endpoint=endpoint.url,
                                evidence=result.response_text[:300],
                                remediation=(
                                    "Implement input sanitization and prompt hardening. "
                                    "Use system prompt isolation, output filtering, and "
                                    "consider using a prompt firewall (e.g., Azure AI Content Safety). "
                                    "Never include secrets in system prompts."
                                ),
                                payload_used=result.payload.payload[:200],
                                timestamp=datetime.now(timezone.utc),
                            )
                            vulnerabilities.append(vuln)
                            await ws_manager.send_vulnerability(
                                self.scan_id, vuln.model_dump(mode="json"),
                            )

                        break  # Found working field, don't try others

                except Exception as exc:
                    logger.debug("Error testing %s with field %s: %s", endpoint.url, msg_field, exc)
                    continue

        await ws_manager.send_progress(
            self.scan_id,
            phase="prompt_injection",
            message=f"✅ Prompt injection testing complete — {len(vulnerabilities)} vulnerabilities found",
            progress=0.45,
        )

        return vulnerabilities
