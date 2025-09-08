#!/usr/bin/env python3
"""
Firecrawl MCP Server - FastMCP version
tools: scrape, batch_scrape (+status), map, search, extract, crawl (+status).
"""

import os
import time
import math
from typing import Any, Dict, List, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "true"

API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
BASE = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v2").rstrip("/")

if not API_KEY and "api.firecrawl.dev" in BASE:
    raise RuntimeError("Set FIRECRAWL_API_KEY for cloud usage")

# Retry/backoff config
MAX_ATTEMPTS = int(os.getenv("FIRECRAWL_RETRY_MAX_ATTEMPTS", "3"))
INITIAL_DELAY = int(os.getenv("FIRECRAWL_RETRY_INITIAL_DELAY", "1000"))
MAX_DELAY = int(os.getenv("FIRECRAWL_RETRY_MAX_DELAY", "10000"))
BACKOFF = float(os.getenv("FIRECRAWL_RETRY_BACKOFF_FACTOR", "2"))

# Credit thresholds (warnings only)
CREDIT_WARN = int(os.getenv("FIRECRAWL_CREDIT_WARNING_THRESHOLD", "1000"))
CREDIT_CRIT = int(os.getenv("FIRECRAWL_CREDIT_CRITICAL_THRESHOLD", "100"))

mcp = FastMCP("Firecrawl MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"firecrawl_{name}", "args": kwargs}

def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h

async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY:
        return _dry("HTTP", method=method, path=path, params=params, json=json)
    url = f"{BASE}{path}"
    attempt = 0
    delay = INITIAL_DELAY / 1000.0
    async with httpx.AsyncClient(timeout=120) as client:
        while True:
            try:
                r = await client.request(method, url, headers=_headers(), params=params, json=json)
                # Retry on 429 / 5xx
                if r.status_code in (429, 500, 502, 503, 504) and attempt < MAX_ATTEMPTS:
                    attempt += 1
                    time.sleep(min(delay, MAX_DELAY / 1000.0))
                    delay = min(delay * BACKOFF, MAX_DELAY / 1000.0)
                    continue
                r.raise_for_status()
                # Capture credits header if present
                remaining = r.headers.get("X-Credits-Remaining") or r.headers.get("x-credits-remaining")
                if remaining:
                    rem = int(remaining)
                    if rem <= CREDIT_CRIT:
                        logging.error("Firecrawl credits critical: %s", rem)
                    elif rem <= CREDIT_WARN:
                        logging.warning("Firecrawl credits low: %s", rem)
                return r.json() if r.text else {"status": "success"}
            except httpx.HTTPStatusError as e:
                if attempt < MAX_ATTEMPTS and e.response is not None and e.response.status_code in (429, 500, 502, 503, 504):
                    attempt += 1
                    time.sleep(min(delay, MAX_DELAY / 1000.0))
                    delay = min(delay * BACKOFF, MAX_DELAY / 1000.0)
                    continue
                raise

# ---------- scrape ---------- [2][5]

@mcp.tool()
async def firecrawl_scrape(url: str, formats: Optional[List[str]] = None, onlyMainContent: Optional[bool] = None,
                           actions: Optional[List[Dict[str, Any]]] = None, waitFor: Optional[int] = None,
                           timeout: Optional[int] = None, mobile: Optional[bool] = None,
                           includeTags: Optional[List[str]] = None, excludeTags: Optional[List[str]] = None,
                           skipTlsVerification: Optional[bool] = None, location: Optional[Dict[str, Any]] = None,
                           maxAge: Optional[int] = None, storeInCache: Optional[bool] = None,
                           prompt: Optional[str] = None) -> Dict[str, Any]:
    """Scrape a single URL; supports actions, caching, location, and output formats."""
    payload: Dict[str, Any] = {"url": url}
    if formats is not None: payload["formats"] = formats
    if onlyMainContent is not None: payload["onlyMainContent"] = onlyMainContent
    if actions is not None: payload["actions"] = actions
    if waitFor is not None: payload["waitFor"] = waitFor
    if timeout is not None: payload["timeout"] = timeout
    if mobile is not None: payload["mobile"] = mobile
    if includeTags is not None: payload["includeTags"] = includeTags
    if excludeTags is not None: payload["excludeTags"] = excludeTags
    if skipTlsVerification is not None: payload["skipTlsVerification"] = skipTlsVerification
    if location is not None: payload["location"] = location
    if maxAge is not None: payload["maxAge"] = maxAge
    if storeInCache is not None: payload["storeInCache"] = storeInCache
    if prompt is not None: payload["prompt"] = prompt
    return await _request("POST", "/scrape", json=payload)

# ---------- batch_scrape + status ---------- [7]

@mcp.tool()
async def firecrawl_batch_scrape(urls: List[str], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Start a batch scrape for multiple URLs; returns job id."""
    payload = {"urls": urls}
    if options: payload["options"] = options
    return await _request("POST", "/batch/scrape", json=payload)

@mcp.tool()
async def firecrawl_check_batch_status(id: str) -> Dict[str, Any]:
    """Check the status of a batch scrape job."""
    return await _request("GET", f"/batch/scrape/{id}")

# ---------- map ---------- [8]

@mcp.tool()
async def firecrawl_map(url: str, search: Optional[str] = None) -> Dict[str, Any]:
    """Discover URLs on a site; optionally filter with a search term."""
    payload: Dict[str, Any] = {"url": url}
    if search: payload["search"] = search
    return await _request("POST", "/map", json=payload)

# ---------- crawl + status ---------- [5]

@mcp.tool()
async def firecrawl_crawl(url: str, maxDepth: Optional[int] = None, limit: Optional[int] = None,
                          allowExternalLinks: Optional[bool] = None, deduplicateSimilarURLs: Optional[bool] = None) -> Dict[str, Any]:
    """Start a crawl across multiple pages; returns job id."""
    payload: Dict[str, Any] = {"url": url}
    if maxDepth is not None: payload["maxDepth"] = maxDepth
    if limit is not None: payload["limit"] = limit
    if allowExternalLinks is not None: payload["allowExternalLinks"] = allowExternalLinks
    if deduplicateSimilarURLs is not None: payload["deduplicateSimilarURLs"] = deduplicateSimilarURLs
    return await _request("POST", "/crawl", json=payload)

@mcp.tool()
async def firecrawl_check_crawl_status(id: str) -> Dict[str, Any]:
    """Check the status of a crawl job."""
    return await _request("GET", f"/crawl/{id}")

# ---------- search ---------- [6]

@mcp.tool()
async def firecrawl_search(query: str, limit: int = 5, lang: Optional[str] = None, country: Optional[str] = None,
                           tbs: Optional[str] = None, scrapeOptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Search the web; optionally scrape results directly."""
    payload: Dict[str, Any] = {"query": query, "limit": limit}
    if lang is not None: payload["lang"] = lang
    if country is not None: payload["country"] = country
    if tbs is not None: payload["tbs"] = tbs
    if scrapeOptions is not None: payload["scrapeOptions"] = scrapeOptions
    return await _request("POST", "/search", json=payload)

# ---------- extract ---------- [4]

@mcp.tool()
async def firecrawl_extract(urls: List[str], prompt: Optional[str] = None, systemPrompt: Optional[str] = None,
                            schema: Optional[Dict[str, Any]] = None, allowExternalLinks: Optional[bool] = None,
                            enableWebSearch: Optional[bool] = None, includeSubdomains: Optional[bool] = None) -> Dict[str, Any]:
    """Extract structured info using prompt and/or schema; supports wildcards like /* and optional web search."""
    payload: Dict[str, Any] = {"urls": urls}
    if prompt is not None: payload["prompt"] = prompt
    if systemPrompt is not None: payload["systemPrompt"] = systemPrompt
    if schema is not None: payload["schema"] = schema
    if allowExternalLinks is not None: payload["allowExternalLinks"] = allowExternalLinks
    if enableWebSearch is not None: payload["enableWebSearch"] = enableWebSearch
    if includeSubdomains is not None: payload["includeSubdomains"] = includeSubdomains
    return await _request("POST", "/extract", json=payload)

if __name__ == "__main__":
    mcp.run()
