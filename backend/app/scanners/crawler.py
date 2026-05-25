"""
Web crawler — discovers pages, forms, input fields, and potential API endpoints.

Uses Playwright (async) to render JavaScript and discover dynamic SPAs.
Production-hardened with retry logic, user-agent rotation, and parallel crawling.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, BrowserContext, Error as PlaywrightError

from app.config import settings

logger = logging.getLogger("zerotrust.crawler")


@dataclass
class FormField:
    """An HTML input / textarea / select inside a <form>."""
    name: str
    field_type: str  # text, password, hidden, email, textarea, select …
    value: str = ""


@dataclass
class DiscoveredForm:
    """A <form> element found on a page."""
    action: str
    method: str  # GET / POST
    page_url: str
    fields: list[FormField] = field(default_factory=list)


@dataclass
class DiscoveredEndpoint:
    """An API-like endpoint discovered from links, scripts, or fetch calls."""
    url: str
    method: str = "GET"
    source: str = ""  # where it was found


@dataclass
class CrawlResult:
    """Everything the crawler discovered."""
    pages: list[str] = field(default_factory=list)
    forms: list[DiscoveredForm] = field(default_factory=list)
    endpoints: list[DiscoveredEndpoint] = field(default_factory=list)
    ai_endpoints: list[DiscoveredEndpoint] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)


# Patterns that hint at AI / LLM endpoints
_AI_PATH_PATTERNS = re.compile(
    r"(chat|completion|generate|predict|inference|ai|llm|gpt|prompt|ask|query|bot|assistant|copilot|openai|anthropic|gemini)",
    re.IGNORECASE,
)

# Common API path patterns
_API_PATH_PATTERNS = re.compile(
    r"(/api/|/v[0-9]+/|/graphql|/rest/|/rpc/)", re.IGNORECASE
)

# Script-embedded URL patterns (fetch/axios/XHR)
_SCRIPT_URL_RE = re.compile(
    r"""(?:fetch|axios\.(?:get|post|put|delete|patch)|\.open\s*\(\s*['"][A-Z]+['"]\s*,)\s*\(?['"]([^'"]+)['"]""",
    re.IGNORECASE,
)

# Email pattern
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Realistic browser user-agents for rotation
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# File extensions to skip crawling
_SKIP_EXTENSIONS = frozenset({
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".mp4", ".mp3", ".avi", ".mov", ".wmv", ".flv",
    ".zip", ".rar", ".tar", ".gz", ".7z",
    ".css", ".woff", ".woff2", ".ttf", ".eot",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
})


class Crawler:
    """Async web crawler using Playwright to map the attack surface of a target (including SPAs)."""

    def __init__(
        self,
        target_url: str,
        max_depth: int | None = None,
        max_pages: int | None = None,
        custom_headers: dict[str, str] | None = None,
    ) -> None:
        self.target_url = target_url.rstrip("/")
        parsed = urlparse(self.target_url)
        self.base_domain = parsed.netloc
        self.scheme = parsed.scheme or "https"
        self.max_depth = max_depth or settings.max_crawl_depth
        self.max_pages = max_pages or settings.max_pages
        self.custom_headers = custom_headers or {}

        self._visited: set[str] = set()
        self._result = CrawlResult()
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self._lock = asyncio.Lock()

    # ── public API ───────────────────────────────────────────────────────
    async def crawl(self) -> CrawlResult:
        """Run the full crawl and return results."""
        logger.info("Starting Playwright crawl of %s (depth=%d, max_pages=%d)",
                     self.target_url, self.max_depth, self.max_pages)

        user_agent = random.choice(_USER_AGENTS)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                ignore_https_errors=True,
                user_agent=user_agent,
                extra_http_headers={
                    **self.custom_headers,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
            )

            # Disable unnecessary resource loading for speed
            await context.route(
                re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|ico|woff|woff2|ttf|eot|mp4|mp3|avi|css)$", re.IGNORECASE),
                lambda route: route.abort(),
            )

            await self._crawl_page(context, self.target_url, depth=0)

            await context.close()
            await browser.close()

        logger.info(
            "Crawl complete: %d pages, %d forms, %d endpoints, %d AI endpoints, %d emails",
            len(self._result.pages),
            len(self._result.forms),
            len(self._result.endpoints),
            len(self._result.ai_endpoints),
            len(self._result.emails),
        )
        return self._result

    # ── internal ─────────────────────────────────────────────────────────
    async def _crawl_page(self, context: BrowserContext, url: str, depth: int) -> None:
        """Recursively crawl a single page using Playwright."""
        normalised = self._normalise(url)

        # Thread-safe visited check
        async with self._lock:
            if normalised in self._visited:
                return
            if len(self._visited) >= self.max_pages:
                return
            if depth > self.max_depth:
                return
            if not self._is_same_domain(normalised):
                return
            if self._is_static_asset(normalised):
                return
            self._visited.add(normalised)

        links: list[str] = []

        async with self._semaphore:
            page = await context.new_page()
            try:
                # Try to load with networkidle, fall back to domcontentloaded on timeout
                try:
                    response = await page.goto(
                        normalised,
                        wait_until="networkidle",
                        timeout=min(settings.request_timeout * 1000, 30000),
                    )
                except PlaywrightError:
                    logger.debug("networkidle timed out for %s, retrying with domcontentloaded", normalised)
                    try:
                        response = await page.goto(
                            normalised,
                            wait_until="domcontentloaded",
                            timeout=15000,
                        )
                    except PlaywrightError as retry_err:
                        logger.warning("Failed to load %s even with fallback: %s", normalised, retry_err)
                        return

                if response:
                    status = response.status
                    # Skip error pages
                    if status >= 400:
                        logger.debug("Skipping %s (HTTP %d)", normalised, status)
                        return
                    self._detect_tech(response.headers)

                # Wait a bit for dynamic content to render
                await page.wait_for_timeout(500)

                # Get the fully rendered HTML
                html = await page.content()

                async with self._lock:
                    self._result.pages.append(normalised)

                soup = BeautifulSoup(html, "lxml")

                # Extract forms
                self._extract_forms(soup, normalised)

                # Extract API / AI endpoints from inline scripts
                self._extract_script_endpoints(soup, normalised)

                # Extract emails
                self._extract_emails(html)

                # Discover links
                links = self._extract_links(soup, normalised)

                # Also try to discover links from button onclick handlers
                self._extract_onclick_links(soup, normalised, links)

            except Exception as exc:
                logger.warning("Failed to fetch/render %s: %s", normalised, exc)
            finally:
                await page.close()

        # Recurse into discovered links — parallel with semaphore control
        tasks = []
        for link in links:
            async with self._lock:
                should_crawl = link not in self._visited and len(self._visited) < self.max_pages
            if should_crawl:
                tasks.append(self._crawl_page(context, link, depth + 1))

        if tasks:
            # Run child pages concurrently (semaphore limits parallelism)
            await asyncio.gather(*tasks, return_exceptions=True)

        # Small politeness delay
        await asyncio.sleep(settings.scan_delay_ms / 1000.0)

    def _extract_links(self, soup: BeautifulSoup, base: str) -> list[str]:
        """Pull all navigable links from the page."""
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            # Skip javascript:, mailto:, tel:, #anchors
            if href.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
                continue
            full = urljoin(base, href)
            full = self._normalise(full)
            if self._is_same_domain(full) and full not in self._visited and not self._is_static_asset(full):
                links.append(full)
        return links

    def _extract_onclick_links(self, soup: BeautifulSoup, base: str, links: list[str]) -> None:
        """Extract URLs from onclick handlers and data attributes."""
        for tag in soup.find_all(attrs={"onclick": True}):
            onclick = tag.get("onclick", "")
            # Match patterns like window.location='...' or location.href='...'
            urls = re.findall(r"(?:window\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]", onclick)
            for url in urls:
                full = urljoin(base, url)
                full = self._normalise(full)
                if self._is_same_domain(full) and full not in self._visited:
                    links.append(full)

        # Also check data-href, data-url attributes
        for attr in ("data-href", "data-url", "data-link"):
            for tag in soup.find_all(attrs={attr: True}):
                href = tag[attr]
                full = urljoin(base, href)
                full = self._normalise(full)
                if self._is_same_domain(full) and full not in self._visited:
                    links.append(full)

    def _extract_forms(self, soup: BeautifulSoup, page_url: str) -> None:
        """Find <form> elements and their fields."""
        for form_tag in soup.find_all("form"):
            action = urljoin(page_url, form_tag.get("action", page_url))
            method = (form_tag.get("method") or "GET").upper()

            fields: list[FormField] = []
            for inp in form_tag.find_all(["input", "textarea", "select"]):
                name = inp.get("name", "")
                if not name:
                    continue
                ftype = inp.get("type", "text") if inp.name == "input" else inp.name
                value = inp.get("value", "")
                fields.append(FormField(name=name, field_type=ftype, value=value))

            if fields:
                df = DiscoveredForm(
                    action=action, method=method, page_url=page_url, fields=fields
                )
                self._result.forms.append(df)

                # Check if the form posts to an AI-like endpoint
                if _AI_PATH_PATTERNS.search(action):
                    self._result.ai_endpoints.append(
                        DiscoveredEndpoint(url=action, method=method, source=f"form on {page_url}")
                    )

    def _extract_script_endpoints(self, soup: BeautifulSoup, page_url: str) -> None:
        """Find API URLs embedded in <script> tags."""
        for script in soup.find_all("script"):
            text = script.string or ""
            for match in _SCRIPT_URL_RE.findall(text):
                full = urljoin(page_url, match)
                ep = DiscoveredEndpoint(url=full, method="POST", source=f"script on {page_url}")

                if _AI_PATH_PATTERNS.search(full):
                    if ep.url not in {e.url for e in self._result.ai_endpoints}:
                        self._result.ai_endpoints.append(ep)
                elif _API_PATH_PATTERNS.search(full):
                    if ep.url not in {e.url for e in self._result.endpoints}:
                        self._result.endpoints.append(ep)

        # Also check <script src="..."> for API base hints
        for script in soup.find_all("script", src=True):
            src = urljoin(page_url, script["src"])
            if _API_PATH_PATTERNS.search(src):
                ep = DiscoveredEndpoint(url=src, method="GET", source=f"script src on {page_url}")
                if ep.url not in {e.url for e in self._result.endpoints}:
                    self._result.endpoints.append(ep)

    def _extract_emails(self, html: str) -> None:
        """Extract email addresses from page content."""
        for email in _EMAIL_RE.findall(html):
            if email not in self._result.emails and not email.endswith((".png", ".jpg", ".js", ".css")):
                self._result.emails.append(email)

    def _detect_tech(self, headers: dict[str, str]) -> None:
        """Guess server technologies from response headers."""
        # Convert header keys to lowercase for safe lookups
        lower_headers = {k.lower(): v for k, v in headers.items()}
        server = lower_headers.get("server", "")
        powered = lower_headers.get("x-powered-by", "")
        for val in (server, powered):
            if val and val not in self._result.technologies:
                self._result.technologies.append(val)

        # Detect framework-specific headers
        tech_headers = {
            "x-drupal-cache": "Drupal",
            "x-generator": lower_headers.get("x-generator", ""),
            "x-django-version": "Django",
            "x-aspnet-version": "ASP.NET",
        }
        for header_key, tech_name in tech_headers.items():
            val = lower_headers.get(header_key, "")
            if val:
                label = tech_name if tech_name != val else val
                if label and label not in self._result.technologies:
                    self._result.technologies.append(label)

    # ── helpers ──────────────────────────────────────────────────────────
    def _normalise(self, url: str) -> str:
        parsed = urlparse(url)
        # Strip fragment and query for deduplication, keep path
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    def _is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self.base_domain

    def _is_static_asset(self, url: str) -> bool:
        """Check if URL points to a static file that shouldn't be crawled."""
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        return any(path_lower.endswith(ext) for ext in _SKIP_EXTENSIONS)
