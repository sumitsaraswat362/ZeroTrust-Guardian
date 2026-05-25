"""
Report Agent — Generates structured security reports from scan findings.

Uses Google Gemini to produce intelligent, context-aware executive summaries
and remediation plans. Falls back gracefully when no API key is configured.
"""

from __future__ import annotations

import asyncio
import logging
import json
from datetime import datetime, timezone

from app.config import settings
from app.models.vulnerability import Vulnerability
from app.utils.helpers import ws_manager

logger = logging.getLogger("zerotrust.agents.report")


def _risk_level(score: float) -> str:
    """Map risk score to a human-readable level (shared utility)."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    elif score > 0:
        return "LOW"
    return "SECURE"


def _calculate_risk_score(vulnerabilities: list[Vulnerability]) -> float:
    """Calculate a 0-100 risk score based on findings."""
    weights = {
        "critical": 25.0,
        "high": 15.0,
        "medium": 8.0,
        "low": 3.0,
        "info": 1.0,
    }
    raw = sum(weights.get(v.severity.value, 0) for v in vulnerabilities)
    return min(100.0, round(raw, 1))


class ReportAgent:
    """
    Agent 4: Report Generation.

    Takes all vulnerabilities from the scan and produces a structured
    executive security report with:
    - Risk score calculation
    - Severity breakdown
    - Prioritized remediation steps
    - Executive summary (AI-generated when available)
    """

    def __init__(self, scan_id: str) -> None:
        self.scan_id = scan_id

    async def generate(
        self,
        target_url: str,
        vulnerabilities: list[Vulnerability],
        pages_crawled: int,
        endpoints_tested: int,
        scan_duration: float,
    ) -> dict:
        """Generate the final security report."""
        await ws_manager.send_progress(
            self.scan_id,
            phase="report",
            message="📋 Generating security report...",
            progress=0.90,
        )

        # Calculate risk score
        risk_score = _calculate_risk_score(vulnerabilities)

        # Build severity breakdown
        severity_breakdown = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
        }
        for v in vulnerabilities:
            severity_breakdown[v.severity.value] += 1

        # Build type breakdown
        type_breakdown: dict[str, int] = {}
        for v in vulnerabilities:
            type_breakdown[v.type.value] = type_breakdown.get(v.type.value, 0) + 1

        # Generate executive summary using LLM
        executive_summary = await self._generate_executive_summary(
            target_url, vulnerabilities, risk_score, severity_breakdown,
        )

        # Generate prioritized remediation plan
        remediation_plan = self._generate_remediation_plan(vulnerabilities)

        # Build the report
        report = {
            "target_url": target_url,
            "scan_id": self.scan_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "risk_score": risk_score,
            "risk_level": _risk_level(risk_score),
            "executive_summary": executive_summary,
            "statistics": {
                "total_vulnerabilities": len(vulnerabilities),
                "by_severity": severity_breakdown,
                "by_type": type_breakdown,
                "pages_crawled": pages_crawled,
                "endpoints_tested": endpoints_tested,
                "scan_duration_seconds": round(scan_duration, 2),
            },
            "remediation_plan": remediation_plan,
            "vulnerabilities": [v.model_dump(mode="json") for v in vulnerabilities],
        }

        await ws_manager.send_progress(
            self.scan_id,
            phase="report",
            message=f"✅ Report generated — Risk Score: {risk_score}/100 ({_risk_level(risk_score)})",
            progress=0.95,
        )

        logger.info(
            "[ReportAgent] Report generated for %s: score=%s, vulns=%d",
            target_url, risk_score, len(vulnerabilities),
        )

        return report

    async def _generate_executive_summary(
        self,
        target_url: str,
        vulnerabilities: list[Vulnerability],
        risk_score: float,
        severity: dict[str, int],
    ) -> str:
        """Generate a human-readable executive summary using an LLM."""
        total = len(vulnerabilities)
        if total == 0:
            return (
                f"Security scan of {target_url} completed successfully. "
                f"No vulnerabilities were discovered. The application appears to follow "
                f"security best practices based on the tests performed."
            )

        api_key = settings.gemini_api_key
        if not api_key:
            # Fallback to simple summary if no key
            level = _risk_level(risk_score)
            high_count = severity.get("critical", 0) + severity.get("high", 0)
            summary = (
                f"Security scan of {target_url} identified {total} vulnerability(ies) "
                f"with an overall risk score of {risk_score}/100 ({level}). "
            )
            if high_count > 0:
                summary += f"{high_count} high-severity issue(s) need urgent attention. "
            summary += "(Set GEMINI_API_KEY for AI-generated summaries.)"
            return summary

        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            # Prepare summary of findings for the prompt
            vuln_lines = []
            for v in vulnerabilities[:20]:
                vuln_lines.append(f"- {v.severity.value.upper()}: {v.title} ({v.type.value})")
            vuln_summary = "\n".join(vuln_lines)

            prompt = (
                "You are a Senior Application Security Engineer.\n"
                "Write a professional, concise executive summary (2-3 paragraphs) for a penetration testing report.\n"
                f"Target: {target_url}\n"
                f"Total Vulnerabilities: {total}\n"
                f"Risk Score: {risk_score}/100\n"
                f"Critical: {severity['critical']}, High: {severity['high']}, "
                f"Medium: {severity['medium']}, Low: {severity['low']}\n\n"
                f"Key findings sample:\n{vuln_summary}\n\n"
                "Write the summary focusing on business risk and high-level technical impact. "
                "Do not use markdown headers, just plain paragraphs."
            )

            # Run the blocking SDK call in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error("LLM generation failed: %s", e)
            level = _risk_level(risk_score)
            return (
                f"Security scan of {target_url} identified {total} vulnerability(ies) "
                f"with an overall risk score of {risk_score}/100 ({level})."
            )

    def _generate_remediation_plan(self, vulnerabilities: list[Vulnerability]) -> list[dict]:
        """Generate a prioritized remediation plan."""
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: severity_order.get(v.severity.value, 5),
        )

        # Deduplicate by type + remediation
        seen: set[str] = set()
        plan: list[dict] = []

        for v in sorted_vulns:
            key = f"{v.type.value}:{v.remediation[:50]}"
            if key in seen:
                continue
            seen.add(key)

            plan.append({
                "priority": len(plan) + 1,
                "severity": v.severity.value,
                "type": v.type.value,
                "title": v.title,
                "remediation": v.remediation,
                "affected_endpoints": [
                    vv.endpoint for vv in vulnerabilities
                    if vv.type == v.type
                ],
            })

        return plan
