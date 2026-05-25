"""
Recon Agent — Crawls the target and maps its attack surface.
"""

from __future__ import annotations

import logging

from app.scanners.crawler import Crawler, CrawlResult
from app.utils.helpers import ws_manager

logger = logging.getLogger("zerotrust.agents.recon")


class ReconAgent:
    """
    Agent 1: Reconnaissance.

    Autonomously crawls the target website to discover:
    - All accessible pages
    - HTML forms with input fields
    - API endpoints referenced in scripts
    - AI/LLM endpoints (chatbots, completion APIs)
    - Server technologies
    """

    def __init__(
        self,
        target_url: str,
        scan_id: str,
        max_depth: int = 3,
        max_pages: int = 50,
        custom_headers: dict[str, str] | None = None,
    ) -> None:
        self.target_url = target_url
        self.scan_id = scan_id
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.custom_headers = custom_headers or {}

    async def run(self) -> CrawlResult:
        """Execute the recon phase."""
        logger.info("[ReconAgent] Starting recon on %s", self.target_url)

        await ws_manager.send_progress(
            self.scan_id,
            phase="recon",
            message=f"🔍 Starting reconnaissance on {self.target_url}",
            progress=0.05,
        )

        crawler = Crawler(
            target_url=self.target_url,
            max_depth=self.max_depth,
            max_pages=self.max_pages,
            custom_headers=self.custom_headers,
        )

        result = await crawler.crawl()

        await ws_manager.send_progress(
            self.scan_id,
            phase="recon",
            message=(
                f"✅ Recon complete: {len(result.pages)} pages, "
                f"{len(result.forms)} forms, {len(result.endpoints)} API endpoints, "
                f"{len(result.ai_endpoints)} AI endpoints discovered"
            ),
            progress=0.20,
            data={
                "pages_found": len(result.pages),
                "forms_found": len(result.forms),
                "api_endpoints": len(result.endpoints),
                "ai_endpoints": len(result.ai_endpoints),
                "technologies": result.technologies,
            },
        )

        logger.info(
            "[ReconAgent] Recon complete: pages=%d, forms=%d, endpoints=%d, ai_endpoints=%d",
            len(result.pages), len(result.forms),
            len(result.endpoints), len(result.ai_endpoints),
        )
        return result
