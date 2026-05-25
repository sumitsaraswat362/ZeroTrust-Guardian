"""
Agent Orchestrator — Coordinates all agents in a multi-agent scanning pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.agents.recon_agent import ReconAgent
from app.agents.prompt_injection_agent import PromptInjectionAgent
from app.agents.vuln_scanner_agent import VulnScannerAgent
from app.agents.report_agent import ReportAgent
from app.models.scan import ScanResult, ScanStatus, ScanConfig
from app.models.vulnerability import Vulnerability
from app.utils.helpers import scan_store, ws_manager

logger = logging.getLogger("zerotrust.agents.orchestrator")


class Orchestrator:
    """
    Master orchestrator that coordinates the multi-agent scanning pipeline.

    Pipeline:
    1. ReconAgent     → Crawl & map attack surface
    2. PromptInjectionAgent → Test AI endpoints (parallel)
    3. VulnScannerAgent     → Test for XSS/SQLi/headers/CORS (parallel)
    4. ReportAgent    → Generate final report
    """

    def __init__(
        self,
        scan_id: str,
        target_url: str,
        config: ScanConfig,
    ) -> None:
        self.scan_id = scan_id
        self.target_url = target_url
        self.config = config

    async def run(self) -> ScanResult:
        """Execute the full scanning pipeline."""
        start_time = time.time()
        all_vulnerabilities: list[Vulnerability] = []

        # Update scan status to running
        scan_result = scan_store.get(self.scan_id)
        if scan_result:
            scan_result.status = ScanStatus.RUNNING

        logger.info("[Orchestrator] Starting scan %s on %s", self.scan_id, self.target_url)

        await ws_manager.send_progress(
            self.scan_id,
            phase="init",
            message=f"🚀 ZeroTrust scan initiated on {self.target_url}",
            progress=0.0,
        )

        try:
            # ── Phase 1: Reconnaissance ──────────────────────────────────
            recon_agent = ReconAgent(
                target_url=self.target_url,
                scan_id=self.scan_id,
                max_depth=self.config.max_depth,
                max_pages=self.config.max_pages,
                custom_headers=self.config.custom_headers,
            )
            crawl_result = await recon_agent.run()

            if scan_result:
                scan_result.pages_crawled = len(crawl_result.pages)

            # ── Phase 2 & 3: Run Prompt Injection + Vuln Scanner in parallel ─
            tasks: list[asyncio.Task] = []

            if self.config.scan_prompt_injection:
                pi_agent = PromptInjectionAgent(
                    scan_id=self.scan_id,
                    custom_headers=self.config.custom_headers,
                )
                tasks.append(asyncio.create_task(pi_agent.run(crawl_result)))

            vuln_agent = VulnScannerAgent(
                scan_id=self.scan_id,
                scan_xss=self.config.scan_xss,
                scan_sqli=self.config.scan_sqli,
                scan_headers=self.config.scan_headers,
                scan_cors=self.config.scan_cors,
                custom_headers=self.config.custom_headers,
            )
            tasks.append(asyncio.create_task(vuln_agent.run(crawl_result)))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_vulnerabilities.extend(result)
                elif isinstance(result, Exception):
                    logger.error("[Orchestrator] Agent error: %s", result)
                    await ws_manager.send_progress(
                        self.scan_id,
                        phase="error",
                        message=f"⚠️ Agent error: {result}",
                        progress=0.85,
                    )

            # Count endpoints tested
            endpoints_tested = (
                len(crawl_result.forms)
                + len(crawl_result.endpoints)
                + len(crawl_result.ai_endpoints)
            )

            # ── Phase 4: Report Generation ───────────────────────────────
            scan_duration = time.time() - start_time

            report_agent = ReportAgent(scan_id=self.scan_id)
            report = await report_agent.generate(
                target_url=self.target_url,
                vulnerabilities=all_vulnerabilities,
                pages_crawled=len(crawl_result.pages),
                endpoints_tested=endpoints_tested,
                scan_duration=scan_duration,
            )

            # ── Finalize ─────────────────────────────────────────────────
            if scan_result:
                scan_result.status = ScanStatus.COMPLETED
                scan_result.completed_at = datetime.now(timezone.utc)
                scan_result.vulnerabilities = all_vulnerabilities
                scan_result.endpoints_tested = endpoints_tested
                scan_result.scan_duration_seconds = round(scan_duration, 2)
                scan_result.risk_score = report["risk_score"]
                scan_result.summary = report["statistics"]

            await ws_manager.send_complete(self.scan_id, report["statistics"])
            await ws_manager.send_progress(
                self.scan_id,
                phase="complete",
                message=(
                    f"🏁 Scan complete! Found {len(all_vulnerabilities)} vulnerabilities. "
                    f"Risk Score: {report['risk_score']}/100"
                ),
                progress=1.0,
                data=report["statistics"],
            )

            logger.info(
                "[Orchestrator] Scan %s complete: %d vulns, score=%.1f, duration=%.1fs",
                self.scan_id, len(all_vulnerabilities),
                report["risk_score"], scan_duration,
            )

            return scan_result

        except Exception as exc:
            logger.exception("[Orchestrator] Scan %s failed: %s", self.scan_id, exc)
            if scan_result:
                scan_result.status = ScanStatus.FAILED
                scan_result.completed_at = datetime.now(timezone.utc)
                scan_result.scan_duration_seconds = round(time.time() - start_time, 2)

            await ws_manager.send_error(self.scan_id, str(exc))
            raise
