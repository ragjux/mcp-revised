#!/usr/bin/env python3
"""
Hyperbrowser MCP Server - FastMCP version
tools for scrape, crawl, extract, search, and profile management.
"""

import os
import time
from typing import Any, Dict, List, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
# Optional: use hyperbrowser SDK if installed. Otherwise use REST.
USE_SDK = os.getenv("HYPERBROWSER_USE_SDK", "true").lower() == "true"
try:
    if USE_SDK:
        from hyperbrowser import Hyperbrowser
        from hyperbrowser.models import StartScrapeJobParams  # type: ignore
        SDK_OK = True
    else:
        SDK_OK = False
except Exception:
    SDK_OK = False

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "true"

API_KEY = os.getenv("HYPERBROWSER_API_KEY", "")
if not API_KEY:
    raise RuntimeError("Set HYPERBROWSER_API_KEY")

BASE = "https://api.hyperbrowser.ai/api"

mcp = FastMCP("Hyperbrowser MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"hyper_{name}", "args": kwargs}

def _headers() -> Dict[str, str]:
    return {"x-api-key": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}

# If SDK available, initialize
_client = Hyperbrowser(api_key=API_KEY) if SDK_OK else None

# ---------- Scrape ---------- [5][7][10]

@mcp.tool()
async def scrape_webpage(url: str) -> Dict[str, Any]:
    """Extract page content (markdown and metadata) for a single URL."""
    if DRY:
        return _dry("scrape_webpage", url=url)
    if SDK_OK and _client:
        res = _client.scrape.start_and_wait(StartScrapeJobParams(url=url))
        # SDK is sync; wrap in dict
        return {"result": res.model_dump() if hasattr(res, "model_dump") else res}
    # REST fallback: start job then poll
    async with httpx.AsyncClient(timeout=60) as client:
        start = await client.post(f"{BASE}/scrape", headers=_headers(), json={"url": url})
        start.raise_for_status()
        job = start.json()
        job_id = job.get("id") or job.get("jobId") or job.get("job_id")
        # Poll until done
        for _ in range(60):
            stat = await client.get(f"{BASE}/scrape/{job_id}", headers=_headers())
            stat.raise_for_status()
            data = stat.json()
            status = data.get("status")
            if status in ("completed", "failed"):
                return data
            time.sleep(1)
        return {"status": "timeout", "job_id": job_id}

# ---------- Crawl (multi-page) ---------- [6]

@mcp.tool()
async def crawl_webpages(url: str, maxPages: int = 10, followLinks: bool = True,
                         includePatterns: Optional[List[str]] = None,
                         excludePatterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Crawl starting URL and return markdown data; pass include/exclude patterns for control."""
    if DRY:
        return _dry("crawl_webpages", url=url, maxPages=maxPages, followLinks=followLinks,
                    includePatterns=includePatterns, excludePatterns=excludePatterns)
    payload: Dict[str, Any] = {
        "url": url,
        "maxPages": maxPages,
        "followLinks": followLinks,
        "includePatterns": includePatterns or [],
        "excludePatterns": excludePatterns or []
    }
    async with httpx.AsyncClient(timeout=60) as client:
        start = await client.post(f"{BASE}/crawl", headers=_headers(), json=payload)
        start.raise_for_status()
        job = start.json()
        job_id = job.get("id") or job.get("jobId")
        for _ in range(120):
            stat = await client.get(f"{BASE}/crawl/{job_id}", headers=_headers())
            stat.raise_for_status()
            data = stat.json()
            status = data.get("status")
            if status in ("completed", "failed"):
                return data
            time.sleep(1)
        return {"status": "timeout", "job_id": job_id}

# ---------- Extract structured data ---------- [2][7]

@mcp.tool()
async def extract_structured_data(urls: List[str], schema: Optional[Dict[str, Any]] = None,
                                  prompt: Optional[str] = None, maxLinks: int = 0,
                                  waitFor: int = 0, sessionOptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convert messy HTML into structured JSON using schema/prompt. Add /* to allow per-origin crawl context."""
    if DRY:
        return _dry("extract_structured_data", urls=urls, schema=schema, prompt=prompt, maxLinks=maxLinks,
                    waitFor=waitFor, sessionOptions=sessionOptions)
    payload: Dict[str, Any] = {
        "urls": urls,
        "maxLinks": maxLinks,
        "waitFor": waitFor
    }
    if schema is not None:
        payload["schema"] = schema
    if prompt is not None:
        payload["prompt"] = prompt
    if sessionOptions is not None:
        payload["sessionOptions"] = sessionOptions
    async with httpx.AsyncClient(timeout=60) as client:
        start = await client.post(f"{BASE}/extract", headers=_headers(), json=payload)
        start.raise_for_status()
        job = start.json()
        job_id = job.get("id") or job.get("jobId")
        for _ in range(180):
            stat = await client.get(f"{BASE}/extract/{job_id}", headers=_headers())
            stat.raise_for_status()
            data = stat.json()
            status = data.get("status")
            if status in ("completed", "failed"):
                return data
            time.sleep(1)
        return {"status": "timeout", "job_id": job_id}

# ---------- Search with Bing (parity helper) ---------- [8][11]

@mcp.tool()
async def search_with_bing(query: str, count: int = 10) -> Dict[str, Any]:
    """Simple Bing search fallback; replace with Hyperbrowser search if available."""
    if DRY:
        return _dry("search_with_bing", query=query, count=count)
    # Minimal SERP scraping; not for production scale
    import urllib.parse
    import bs4  # pip install beautifulsoup4
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&rdr=1"
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        out = []
        for li in soup.select("li.b_algo")[:count]:
            a = li.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            link = a.get("href")
            desc_el = li.select_one("div.b_caption")
            desc = desc_el.get_text(" ", strip=True) if desc_el else ""
            out.append({"title": title, "link": link, "snippet": desc})
        return {"results": out, "count": len(out)}

# ---------- Agents (stubs to respect parity; assume server-side orchestration) ----------

@mcp.tool()
async def browser_use_agent(task: str, url: Optional[str] = None) -> Dict[str, Any]:
    """Fast, lightweight browser automation. This is a stub passthrough; implement via Hyperbrowser agent if available."""
    if DRY:
        return _dry("browser_use_agent", task=task, url=url)
    return {"status": "not_implemented", "message": "Agent routing handled by Hyperbrowser server"}

@mcp.tool()
async def openai_computer_use_agent(task: str) -> Dict[str, Any]:
    if DRY:
        return _dry("openai_computer_use_agent", task=task)
    return {"status": "not_implemented", "message": "Agent routing handled by Hyperbrowser server"}

@mcp.tool()
async def claude_computer_use_agent(task: str) -> Dict[str, Any]:
    if DRY:
        return _dry("claude_computer_use_agent", task=task)
    return {"status": "not_implemented", "message": "Agent routing handled by Hyperbrowser server"}

# ---------- Profiles ----------

@mcp.tool()
async def create_profile(name: str) -> Dict[str, Any]:
    """Create a new persistent Hyperbrowser profile."""
    if DRY:
        return _dry("create_profile", name=name)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE}/profiles", headers=_headers(), json={"name": name})
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def delete_profile(profile_id: str) -> Dict[str, Any]:
    """Delete an existing persistent Hyperbrowser profile."""
    if DRY:
        return _dry("delete_profile", profile_id=profile_id)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(f"{BASE}/profiles/{profile_id}", headers=_headers())
        r.raise_for_status()
        return {"status": "success"}

@mcp.tool()
async def list_profiles() -> Dict[str, Any]:
    """List existing persistent Hyperbrowser profiles."""
    if DRY:
        return _dry("list_profiles")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/profiles", headers=_headers())
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
