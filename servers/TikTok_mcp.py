#!/usr/bin/env python3
"""
TikTok MCP Server - FastMCP version (unofficial, via TikTokApi)
Implements: health, search (hashtags), cleanup.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
from TikTokApi import TikTokApi  # pip install TikTokApi
# Requires playwright: pip install playwright && python -m playwright install

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

MS_TOKEN = os.getenv("ms_token", "")
PROXY = os.getenv("TIKTOK_PROXY", "")

mcp = FastMCP("TikTok MCP (native)")

_api: Optional[TikTokApi] = None
_sessions_created = False

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"tiktok_{name}", "args": kwargs}

async def _ensure_api():
    global _api, _sessions_created
    if _api is None:
        _api = TikTokApi()
    if not _sessions_created:
        # create a few sessions for resilience; ms_token optional [5]
        ms_tokens = [MS_TOKEN] if MS_TOKEN else []
        await _api.create_sessions(num_sessions=max(1, len(ms_tokens) or 3), ms_tokens=ms_tokens, proxy=PROXY or None)
        _sessions_created = True

# ---------- Health ----------

@mcp.tool()
async def tiktok_health() -> Dict[str, Any]:
    """Health check."""
    if DRY_RUN:
        return _dry("health")
    try:
        await _ensure_api()
        return {
            "status": "running",
            "api_initialized": True,
            "service": {"name": "TikTok MCP Service", "version": "0.1.0", "description": "TikTok video search by hashtags"}
        }
    except Exception as e:
        return {"status": "error", "api_initialized": False, "message": str(e)}

# ---------- Search by hashtags ----------

@mcp.tool()
async def tiktok_search(search_terms: List[str], count: int = 30) -> Dict[str, Any]:
    """
    Search for videos with hashtags.
    Returns video URLs, descriptions, and engagement stats where available.
    """
    if DRY_RUN:
        return _dry("search", search_terms=search_terms, count=count)
    await _ensure_api()
    results: List[Dict[str, Any]] = []
    try:
        for term in search_terms:
            hashtag = (term or "").lstrip("#")
            # byHashtag returns a list of tiktoks [7]
            vids = _api.byHashtag(hashtag, count=count, proxy=PROXY or None)
            for v in vids:
                try:
                    stats = v.get("stats", {})
                    author = v.get("author", {})
                    item = {
                        "url": f'https://www.tiktok.com/@{author.get("uniqueId","")}/video/{v.get("id","")}',
                        "id": v.get("id"),
                        "desc": v.get("desc"),
                        "author": author.get("uniqueId"),
                        "createTime": v.get("createTime"),
                        "duration": v.get("video", {}).get("duration"),
                        "engagement": {
                            "playCount": stats.get("playCount"),
                            "diggCount": stats.get("diggCount"),
                            "commentCount": stats.get("commentCount"),
                            "shareCount": stats.get("shareCount"),
                            "collectCount": stats.get("collectCount"),
                        },
                        "hashtag": hashtag
                    }
                    results.append(item)
                except Exception:
                    continue
        return {"count": len(results), "items": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Cleanup ----------

@mcp.tool()
async def tiktok_cleanup() -> Dict[str, Any]:
    """Clean up resources and API sessions."""
    if DRY_RUN:
        return _dry("cleanup")
    global _api, _sessions_created
    try:
        if _api:
            await _api.close_sessions()
        _api = None
        _sessions_created = False
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()
