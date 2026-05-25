"""
Application configuration loaded from environment variables.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application settings, read from env vars / .env file."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # AI / LLM
    gemini_api_key: str = ""

    # Scanning
    max_crawl_depth: int = 3
    max_pages: int = 50
    request_timeout: int = 15
    max_concurrent_requests: int = 10
    scan_delay_ms: int = 150

    # Rate limiting
    max_concurrent_scans: int = 5

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "chrome-extension://*",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
