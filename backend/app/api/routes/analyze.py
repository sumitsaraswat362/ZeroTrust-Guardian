"""
Quick Analysis API — Lightweight endpoint for the Chrome Extension.

Receives a URL, runs fast heuristic checks + optional AI analysis,
and returns a trust score with threat details in <10 seconds.

PHILOSOPHY: Only flag things that are REAL threats to everyday users.
Missing CSP headers or local SSL cert chain issues are NOT scams.
"""

from __future__ import annotations

import asyncio
import logging
import re
import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger("zerotrust.api.analyze")
router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="URL to analyze")


class ThreatDetail(BaseModel):
    type: str
    title: str
    severity: str  # critical, high, medium, low, info
    description: str


class AnalyzeResponse(BaseModel):
    url: str
    status: str  # safe, warning, danger, scam
    trust_score: int  # 0-100
    reason: str
    threats: list[ThreatDetail] = []
    details: dict = {}
    analyzed_at: str


# ─── Suspicious URL patterns ────────────────────────────────────────────────
PHISHING_KEYWORDS = re.compile(
    r"(login|signin|verify|secure|account|update|confirm|banking|paypal|amazon|apple|microsoft|google|facebook|instagram|password|credential|billing|suspend|unlock|restore|support|helpdesk|wallet|crypto|prize|winner|lottery|claim|reward|bonus|free|gift|urgent|limited|expire|act-now|click-here|congratulations)",
    re.IGNORECASE,
)

SUSPICIOUS_TLD = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".buzz", ".top", ".xyz",
    ".icu", ".club", ".work", ".click", ".link", ".loan",
    ".racing", ".download", ".stream", ".win", ".bid", ".trade",
    ".date", ".faith", ".review", ".party", ".science",
}

DARK_PATTERN_SIGNALS = [
    # These regexes are intentionally strict — one false positive ruins trust
    (r"(?:only|just)\s*\d+\s*(?:left|remaining|available)\s*!?", "Artificial scarcity"),
    (r"\d+\s*(?:people|users|visitors)\s+(?:are\s+)?(?:currently\s+)?(?:viewing|watching|looking\s+at)\s+this", "Social pressure"),
    (r"(?:hurry|rush|act\s+now|don.t\s+miss\s+out|limited\s+time\s+offer|expires?\s+in\s+\d)", "False urgency"),
    (r"(?:congratulations|you.ve\s+(?:been\s+)?(?:selected|chosen|won))\s*[!.]", "Fake reward"),
    (r"(?:your\s+(?:computer|device|phone|mac|pc|account)\s+(?:is|has\s+been)\s+(?:infected|compromised|hacked|locked|at\s+risk))", "Scare tactic"),
    (r"(?:call\s+(?:us\s+)?(?:now|immediately|right\s+away)\s+at|(?:toll[- ]?free)\s*:?\s*\+?1?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})", "Tech support scam"),
]


@router.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest):
    """
    Fast analysis endpoint for the Chrome Extension.

    Only flags REAL consumer threats:
    - Phishing URLs (suspicious keywords, IP hostnames, typosquatting)
    - Dark patterns in page content (fake urgency, scare tactics)
    - Hidden iframes (credential theft)
    - Password fields on HTTP pages
    - Genuinely invalid/expired SSL certificates (NOT local chain issues)

    Does NOT penalize for:
    - Missing optional security headers (CSP, HSTS, X-Frame-Options)
    - Local SSL certificate chain verification errors
    """
    url = request.url.strip()
    if not url.startswith("http"):
        url = f"https://{url}"

    parsed = urlparse(url)
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid URL")

    threats: list[ThreatDetail] = []
    trust_score = 100  # Start at 100, deduct for REAL issues only
    details = {}

    domain = parsed.hostname.lower()
    parts = domain.split(".")
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain

    # ── Check 1: URL pattern analysis ────────────────────────────────────
    # Only flag phishing keywords in the PATH, not the domain itself
    path_and_query = parsed.path + "?" + (parsed.query or "")
    phishing_matches = PHISHING_KEYWORDS.findall(path_and_query)
    if len(phishing_matches) >= 3:
        trust_score -= 20
        threats.append(ThreatDetail(
            type="phishing_url",
            title="Suspicious URL pattern",
            severity="high",
            description=f"URL path contains multiple phishing-related keywords: {', '.join(set(m.lower() for m in phishing_matches[:5]))}",
        ))
    elif len(phishing_matches) == 2:
        trust_score -= 8
        threats.append(ThreatDetail(
            type="phishing_url",
            title="Unusual URL keywords",
            severity="medium",
            description=f"URL path contains keywords often seen in phishing: {', '.join(set(m.lower() for m in phishing_matches))}",
        ))

    # IP address as hostname — strong phishing signal
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        trust_score -= 25
        threats.append(ThreatDetail(
            type="ip_hostname",
            title="IP address used instead of domain",
            severity="high",
            description="Legitimate sites use domain names, not raw IP addresses. This is a common phishing technique.",
        ))

    # Suspicious TLD
    tld = "." + parts[-1] if parts else ""
    if tld in SUSPICIOUS_TLD:
        trust_score -= 10
        threats.append(ThreatDetail(
            type="suspicious_tld",
            title=f"High-risk domain extension ({tld})",
            severity="medium",
            description=f"The domain uses '{tld}' which is frequently associated with spam and phishing sites.",
        ))

    # Typosquatting patterns
    if any(brand in domain for brand in ["g00gle", "app1e", "amaz0n", "paypa1", "micros0ft", "faceb00k"]):
        trust_score -= 30
        threats.append(ThreatDetail(
            type="typosquatting",
            title="Potential typosquatting domain",
            severity="critical",
            description="This domain appears to mimic a well-known brand using character substitutions.",
        ))

    # Excessive subdomains (> 4 levels) — e.g. secure.login.paypal.verify.evil.com
    if len(parts) > 4:
        trust_score -= 10
        threats.append(ThreatDetail(
            type="excessive_subdomains",
            title="Unusually deep subdomain",
            severity="medium",
            description=f"Domain has {len(parts)} levels — phishing sites often use deep subdomains to hide the real domain.",
        ))

    # ── Check 2: SSL — only flag REAL certificate problems ───────────────
    ssl_result = await _check_ssl(parsed.hostname)
    if isinstance(ssl_result, dict):
        details["ssl"] = ssl_result
        reason = ssl_result.get("reason", "")
        is_local_issue = "unable to get local issuer" in reason or "certificate verify failed" in reason
        
        if not ssl_result.get("valid", True) and not is_local_issue:
            # Genuinely expired or self-signed cert
            trust_score -= 15
            threats.append(ThreatDetail(
                type="ssl_issue",
                title="SSL certificate problem",
                severity="medium",
                description=reason,
            ))

    # ── Check 3: Page content analysis (dark patterns, real threats) ─────
    content_result = await _check_page_content(url)
    if isinstance(content_result, dict):
        details["content_signals"] = content_result.get("content_signals", [])

        for ct in content_result.get("content_threats", []):
            threats.append(ct)
            if ct.severity == "critical":
                trust_score -= 25
            elif ct.severity == "high":
                trust_score -= 15
            elif ct.severity == "medium":
                trust_score -= 8

    # ── Check 4: AI analysis (only if there are real threats) ────────────
    real_threats = [t for t in threats if t.severity in ("critical", "high", "medium")]
    if settings.gemini_api_key and real_threats:
        try:
            ai_summary = await _ai_threat_summary(url, real_threats)
            if ai_summary:
                details["ai_analysis"] = ai_summary
        except Exception as e:
            logger.warning("AI summary failed: %s", e)

    # ── Compute final status ─────────────────────────────────────────────
    trust_score = max(0, min(100, trust_score))

    has_critical = any(t.severity == "critical" for t in threats)
    has_high = any(t.severity == "high" for t in threats)

    if has_critical or trust_score < 30:
        status = "danger"
    elif has_high or trust_score < 60:
        status = "warning"
    else:
        status = "safe"

    reason = _generate_reason(status, threats, trust_score, root_domain)

    return AnalyzeResponse(
        url=url,
        status=status,
        trust_score=trust_score,
        reason=reason,
        threats=[t for t in threats if t.severity != "info"],  # Hide info-level noise
        details=details,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )


# ─── SSL Certificate Check ──────────────────────────────────────────────────
async def _check_ssl(hostname: str) -> dict:
    """Check SSL certificate validity."""
    try:
        def _verify():
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.settimeout(5)
                s.connect((hostname, 443))
                cert = s.getpeercert()
                return {
                    "valid": True,
                    "issuer": dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "Unknown"),
                    "expires": cert.get("notAfter", "Unknown"),
                }
        return await asyncio.to_thread(_verify)
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "reason": str(e.verify_message)}
    except Exception as e:
        return {"valid": False, "reason": str(e)[:120]}


# ─── Page Content Analysis ───────────────────────────────────────────────────
async def _check_page_content(url: str) -> dict:
    """Fetch the page and analyze content for REAL consumer threats only."""
    result = {
        "content_threats": [],
        "content_signals": [],
    }

    try:
        async with httpx.AsyncClient(
            timeout=8.0,
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            },
        ) as client:
            resp = await client.get(url)
    except Exception as e:
        logger.warning("Could not fetch %s: %s", url, e)
        return result

    body = resp.text[:50000]

    # ── Dark pattern / scam content detection ────────────────────────
    for pattern, signal_name in DARK_PATTERN_SIGNALS:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            result["content_signals"].append(signal_name)
            severity = "high" if signal_name in ("Fake reward", "Scare tactic", "Tech support scam") else "medium"
            result["content_threats"].append(ThreatDetail(
                type="dark_pattern",
                title=f"Dark pattern: {signal_name}",
                severity=severity,
                description=f"Page contains manipulative language: '{signal_name}'. Found {len(matches)} instance(s).",
            ))

    # ── Hidden iframes (credential theft) ────────────────────────────
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")

    hidden_iframes = soup.find_all("iframe", style=re.compile(
        r"display\s*:\s*none|visibility\s*:\s*hidden|width\s*:\s*0|height\s*:\s*0", re.IGNORECASE
    ))
    if hidden_iframes:
        result["content_threats"].append(ThreatDetail(
            type="hidden_iframe",
            title="Hidden iframe detected",
            severity="high",
            description=f"Page contains {len(hidden_iframes)} hidden iframe(s), commonly used for credential theft.",
        ))

    # ── Password field on HTTP (critical) ────────────────────────────
    if urlparse(url).scheme == "http":
        pw_fields = soup.find_all("input", {"type": "password"})
        if pw_fields:
            result["content_threats"].append(ThreatDetail(
                type="insecure_password",
                title="Password field on unencrypted page",
                severity="critical",
                description="This page collects passwords over HTTP. Anyone on your network can see what you type.",
            ))

    return result


# ─── AI Threat Summary ──────────────────────────────────────────────────────
async def _ai_threat_summary(url: str, threats: list[ThreatDetail]) -> str | None:
    """Use Gemini to generate a concise, consumer-friendly threat summary."""
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

        threat_text = "\n".join(f"- [{t.severity.upper()}] {t.title}: {t.description}" for t in threats[:8])

        prompt = (
            "You are a digital safety advisor for everyday internet users.\n"
            "Write a brief 1-2 sentence summary explaining the safety concerns "
            "found on this website. Use simple, non-technical language.\n"
            "Be direct but not alarmist.\n\n"
            f"Website: {url}\n"
            f"Issues found:\n{threat_text}\n\n"
            "Summary (1-2 sentences, plain English):"
        )

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.warning("AI summary generation failed: %s", e)
        return None


# ─── Human-Readable Reason Generator ────────────────────────────────────────
def _generate_reason(
    status: str,
    threats: list[ThreatDetail],
    trust_score: int,
    domain: str,
) -> str:
    """Generate a consumer-friendly reason string."""
    real_threats = [t for t in threats if t.severity in ("critical", "high", "medium")]

    if not real_threats:
        return f"{domain} looks safe. No threats detected."

    if status == "danger":
        top = next((t for t in threats if t.severity in ("critical", "high")), threats[0])
        return f"⚠️ {top.title}. This site may not be safe — proceed with extreme caution."

    if status == "warning":
        return f"{len(real_threats)} concern(s) detected. Review details before sharing personal information."

    return f"{domain} looks safe. Trust score: {trust_score}/100."
