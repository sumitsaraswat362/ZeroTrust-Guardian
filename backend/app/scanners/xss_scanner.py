"""
XSS (Cross-Site Scripting) Scanner — Tests forms and input fields for reflected XSS.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger("zerotrust.scanners.xss")


# XSS test payloads — escalating from simple to advanced
XSS_PAYLOADS = [
    # Basic script injection
    '<script>alert("ZT_XSS_1")</script>',
    "<script>alert('ZT_XSS_2')</script>",
    '<script>document.location="http://evil.com"</script>',
    # Event handlers
    '<img src=x onerror=alert("ZT_XSS_3")>',
    '<svg onload=alert("ZT_XSS_4")>',
    '<body onload=alert("ZT_XSS_5")>',
    '<div onmouseover=alert("ZT_XSS_6")>hover</div>',
    '<input onfocus=alert("ZT_XSS_7") autofocus>',
    '<details open ontoggle=alert("ZT_XSS_8")>',
    '<marquee onstart=alert("ZT_XSS_9")>',
    # Attribute injection
    '" onmouseover="alert(\'ZT_XSS_10\')" x="',
    "' onfocus='alert(1)' autofocus='",
    '" onfocus="alert(1)" autofocus="',
    # JavaScript URI
    'javascript:alert("ZT_XSS_11")',
    '<a href="javascript:alert(1)">click</a>',
    # Encoded payloads
    '%3Cscript%3Ealert("ZT_XSS_12")%3C/script%3E',
    '&#60;script&#62;alert("ZT_XSS_13")&#60;/script&#62;',
    # Template literal injection
    '${alert("ZT_XSS_14")}',
    '{{constructor.constructor("return alert(1)")()}}',
]

# Markers we can look for in the response to confirm reflection
_REFLECTION_MARKERS = [
    re.compile(r'<script>alert\(["\']ZT_XSS_', re.IGNORECASE),
    re.compile(r'onerror\s*=\s*alert', re.IGNORECASE),
    re.compile(r'onload\s*=\s*alert', re.IGNORECASE),
    re.compile(r'onmouseover\s*=\s*alert', re.IGNORECASE),
    re.compile(r'onfocus\s*=\s*alert', re.IGNORECASE),
    re.compile(r'ontoggle\s*=\s*alert', re.IGNORECASE),
    re.compile(r'onstart\s*=\s*alert', re.IGNORECASE),
    re.compile(r'javascript\s*:\s*alert', re.IGNORECASE),
    re.compile(r'<svg[^>]*onload', re.IGNORECASE),
    re.compile(r'<img[^>]*onerror', re.IGNORECASE),
]


@dataclass
class XSSResult:
    """Result of a single XSS test."""
    url: str
    parameter: str
    payload: str
    reflected: bool
    evidence: str
    method: str


class XSSScanner:
    """Tests forms and URL parameters for reflected XSS vulnerabilities."""

    def __init__(self, custom_headers: dict[str, str] | None = None) -> None:
        self.custom_headers = custom_headers or {}

    async def scan_form(
        self,
        action_url: str,
        method: str,
        fields: list[dict],
    ) -> list[XSSResult]:
        """
        Test a form for XSS by injecting payloads into each field.

        Args:
            action_url: Form action URL
            method: GET or POST
            fields: List of dicts with 'name' and 'field_type'
        """
        results: list[XSSResult] = []
        text_fields = [
            f for f in fields
            if f.get("field_type", "text") in ("text", "search", "email", "textarea", "url", "hidden", "password")
        ]

        if not text_fields:
            return results

        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, verify=False,
            headers={"User-Agent": "Mozilla/5.0", **self.custom_headers},
        ) as client:
            for field_info in text_fields:
                field_name = field_info["name"]
                for payload in XSS_PAYLOADS:
                    try:
                        result = await self._test_xss(
                            client, action_url, method, field_name, payload, fields,
                        )
                        if result.reflected:
                            results.append(result)
                            # Found one, skip remaining payloads for this field
                            break
                    except Exception as exc:
                        logger.debug("XSS test error on %s/%s: %s", action_url, field_name, exc)

        logger.info("XSS scan on %s: found %d reflected payloads", action_url, len(results))
        return results

    async def scan_url_params(self, url: str, params: list[str]) -> list[XSSResult]:
        """Test URL query parameters for reflected XSS."""
        results: list[XSSResult] = []

        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, verify=False,
            headers={"User-Agent": "Mozilla/5.0", **self.custom_headers},
        ) as client:
            for param in params:
                for payload in XSS_PAYLOADS[:8]:  # Use top payloads for URL params
                    try:
                        resp = await client.get(url, params={param: payload})
                        reflected = self._check_reflection(resp.text, payload)
                        if reflected:
                            results.append(XSSResult(
                                url=url,
                                parameter=param,
                                payload=payload,
                                reflected=True,
                                evidence=self._extract_evidence(resp.text, payload),
                                method="GET",
                            ))
                            break
                    except Exception as exc:
                        logger.debug("XSS URL param test error: %s", exc)

        return results

    async def _test_xss(
        self,
        client: httpx.AsyncClient,
        action_url: str,
        method: str,
        target_field: str,
        payload: str,
        all_fields: list[dict],
    ) -> XSSResult:
        """Send a single XSS payload and check if it's reflected."""
        # Build form data with payload in target field, benign values elsewhere
        form_data = {}
        for f in all_fields:
            if f["name"] == target_field:
                form_data[f["name"]] = payload
            else:
                form_data[f["name"]] = f.get("value", "") or "test"

        if method.upper() == "POST":
            resp = await client.post(action_url, data=form_data)
        else:
            resp = await client.get(action_url, params=form_data)

        reflected = self._check_reflection(resp.text, payload)

        return XSSResult(
            url=action_url,
            parameter=target_field,
            payload=payload,
            reflected=reflected,
            evidence=self._extract_evidence(resp.text, payload) if reflected else "",
            method=method,
        )

    def _check_reflection(self, response_body: str, payload: str) -> bool:
        """Check if the XSS payload is reflected in the response body."""
        # Direct reflection check
        if payload in response_body:
            return True

        # Check known markers via regex
        for marker_re in _REFLECTION_MARKERS:
            if marker_re.search(response_body):
                return True

        return False

    def _extract_evidence(self, body: str, payload: str, context_size: int = 100) -> str:
        """Extract the surrounding context where the payload was reflected."""
        idx = body.find(payload)
        if idx == -1:
            # Try to find any XSS marker
            for marker_re in _REFLECTION_MARKERS:
                m = marker_re.search(body)
                if m:
                    idx = m.start()
                    break
        if idx == -1:
            return ""
        start = max(0, idx - context_size)
        end = min(len(body), idx + len(payload) + context_size)
        return f"...{body[start:end]}..."
