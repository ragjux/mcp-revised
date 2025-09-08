#!/usr/bin/env python3
"""
Mailchimp MCP Server - FastMCP version.
"""

import os
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"mailchimp_{name}", "args": kwargs}

TOKEN = os.getenv("MAILCHIMP_TOKEN", "")
DC = os.getenv("MAILCHIMP_DC", "")

if not TOKEN or not DC:
    raise RuntimeError("Set MAILCHIMP_TOKEN and MAILCHIMP_DC (e.g., us6)")

BASE = f"https://{DC}.api.mailchimp.com/3.0"

mcp = FastMCP("Mailchimp MCP (native)")

def _headers() -> Dict[str, str]:
    # Bearer accepted per docs; Basic also supported. [3]
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "Accept": "application/json"}

async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, params=params, json=json)
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=_headers(), params=params, json=json)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

# ---------- Audiences (Lists) ---------- [11]

@mcp.tool()
async def mailchimp_list_audiences(count: int = 10, offset: int = 0) -> Dict[str, Any]:
    """List audiences (lists)."""
    return await _request("GET", "/lists", params={"count": count, "offset": offset})

@mcp.tool()
async def mailchimp_get_audience(list_id: str) -> Dict[str, Any]:
    """Get a specific audience (list) by id."""
    return await _request("GET", f"/lists/{list_id}")

# ---------- Members ---------- [2]

@mcp.tool()
async def mailchimp_list_members(list_id: str, count: int = 10, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
    """List members of an audience; optional status filter (subscribed, unsubscribed, cleaned, pending)."""
    params: Dict[str, Any] = {"count": count, "offset": offset}
    if status:
        params["status"] = status
    return await _request("GET", f"/lists/{list_id}/members", params=params)

@mcp.tool()
async def mailchimp_get_member(list_id: str, subscriber_hash: str) -> Dict[str, Any]:
    """Get a member by subscriber_hash (lowercase MD5 of email)."""
    return await _request("GET", f"/lists/{list_id}/members/{subscriber_hash}")

# ---------- Segments ---------- [10]

@mcp.tool()
async def mailchimp_list_segments(list_id: str, count: int = 10, offset: int = 0) -> Dict[str, Any]:
    """List segments for an audience."""
    return await _request("GET", f"/lists/{list_id}/segments", params={"count": count, "offset": offset})

@mcp.tool()
async def mailchimp_get_segment(list_id: str, segment_id: str) -> Dict[str, Any]:
    """Get a specific segment."""
    return await _request("GET", f"/lists/{list_id}/segments/{segment_id}")

# ---------- Campaigns ---------- [11]

@mcp.tool()
async def mailchimp_list_campaigns(count: int = 10, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
    """List campaigns; optional status filter (save, paused, schedule, sending, sent, canceled)."""
    params: Dict[str, Any] = {"count": count, "offset": offset}
    if status:
        params["status"] = status
    return await _request("GET", "/campaigns", params=params)

@mcp.tool()
async def mailchimp_get_campaign(campaign_id: str) -> Dict[str, Any]:
    """Get a specific campaign."""
    return await _request("GET", f"/campaigns/{campaign_id}")

# ---------- Utilities ----------

@mcp.tool()
async def mailchimp_ping() -> Dict[str, Any]:
    """Ping the API root to verify connectivity and token/user role."""
    return await _request("GET", "/")

if __name__ == "__main__":
    mcp.run()
