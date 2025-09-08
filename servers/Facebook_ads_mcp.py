#!/usr/bin/env python3
"""
Meta (Facebook) Ads MCP Server - FastMCP version
Implements read tools for accounts, objects, collections, insights, activities, and pagination URL fetch.
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
    return {"dry_run": True, "tool": f"meta_{name}", "args": kwargs}

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v22.0")

if not ACCESS_TOKEN:
    raise RuntimeError("Set META_ACCESS_TOKEN")

BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

mcp = FastMCP("Meta Ads MCP (native)")

def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}

async def _get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("GET", url=url, params=params)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()

# -------- Account & Object Read --------

@mcp.tool()
async def meta_list_ad_accounts(fields: str = "id,account_id,name") -> Dict[str, Any]:
    """List ad accounts linked to the token."""
    params = {"fields": fields}
    return await _get(f"{BASE}/me/adaccounts", params=params)  # requires ads_read [2][10]

@mcp.tool()
async def meta_get_details_of_ad_account(ad_account_id: str, fields: str = "id,account_id,name,currency,timezone_id") -> Dict[str, Any]:
    """Get details for a specific ad account (use 'act_<id>')."""
    params = {"fields": fields}
    return await _get(f"{BASE}/{ad_account_id}", params=params)

@mcp.tool()
async def meta_get_campaign_by_id(campaign_id: str, fields: str = "id,name,status,objective,created_time,updated_time") -> Dict[str, Any]:
    params = {"fields": fields}
    return await _get(f"{BASE}/{campaign_id}", params=params)

@mcp.tool()
async def meta_get_adset_by_id(adset_id: str, fields: str = "id,name,status,campaign_id,daily_budget,start_time,end_time") -> Dict[str, Any]:
    params = {"fields": fields}
    return await _get(f"{BASE}/{adset_id}", params=params)

@mcp.tool()
async def meta_get_ad_by_id(ad_id: str, fields: str = "id,name,status,adset_id,campaign_id,created_time,updated_time") -> Dict[str, Any]:
    params = {"fields": fields}
    return await _get(f"{BASE}/{ad_id}", params=params)

@mcp.tool()
async def meta_get_ad_creative_by_id(creative_id: str, fields: str = "id,name,object_story_spec,thumbnail_url") -> Dict[str, Any]:
    params = {"fields": fields}
    return await _get(f"{BASE}/{creative_id}", params=params)

@mcp.tool()
async def meta_get_adsets_by_ids(ids_csv: str, fields: str = "id,name,status,campaign_id") -> Dict[str, Any]:
    """Batch get multiple ad sets by IDs (comma-separated)."""
    params = {"ids": ids_csv, "fields": fields}
    return await _get(f"{BASE}", params=params)

# -------- Collections --------

@mcp.tool()
async def meta_get_campaigns_by_adaccount(ad_account_id: str, fields: str = "id,name,status", limit: int = 50, after: Optional[str] = None, before: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    if before: params["before"] = before
    return await _get(f"{BASE}/{ad_account_id}/campaigns", params=params)

@mcp.tool()
async def meta_get_adsets_by_adaccount(ad_account_id: str, fields: str = "id,name,status,campaign_id", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{ad_account_id}/adsets", params=params)

@mcp.tool()
async def meta_get_ads_by_adaccount(ad_account_id: str, fields: str = "id,name,status,adset_id,campaign_id", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{ad_account_id}/ads", params=params)

@mcp.tool()
async def meta_get_adsets_by_campaign(campaign_id: str, fields: str = "id,name,status,campaign_id", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{campaign_id}/adsets", params=params)

@mcp.tool()
async def meta_get_ads_by_campaign(campaign_id: str, fields: str = "id,name,status,adset_id,campaign_id", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{campaign_id}/ads", params=params)

@mcp.tool()
async def meta_get_ads_by_adset(adset_id: str, fields: str = "id,name,status,adset_id,campaign_id", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{adset_id}/ads", params=params)

@mcp.tool()
async def meta_get_ad_creatives_by_ad_id(ad_id: str, fields: str = "id,name,object_story_spec,thumbnail_url", limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
    params = {"fields": fields, "limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{ad_id}/adcreatives", params=params)

# -------- Insights & Performance --------

@mcp.tool()
async def meta_get_adaccount_insights(ad_account_id: str, fields: str, time_range: Optional[str] = None, level: Optional[str] = None, breakdowns: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """fields is comma-separated insights metrics; time_range JSON string e.g. {"since":"2025-08-01","until":"2025-08-31"}; level (campaign,adset,ad)."""
    params: Dict[str, Any] = {"fields": fields, "limit": limit}
    if time_range: params["time_range"] = time_range
    if level: params["level"] = level
    if breakdowns: params["breakdowns"] = breakdowns
    return await _get(f"{BASE}/{ad_account_id}/insights", params=params)  # [3][5]

@mcp.tool()
async def meta_get_campaign_insights(campaign_id: str, fields: str, time_range: Optional[str] = None, breakdowns: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    params: Dict[str, Any] = {"fields": fields, "limit": limit}
    if time_range: params["time_range"] = time_range
    if breakdowns: params["breakdowns"] = breakdowns
    return await _get(f"{BASE}/{campaign_id}/insights", params=params)

@mcp.tool()
async def meta_get_adset_insights(adset_id: str, fields: str, time_range: Optional[str] = None, breakdowns: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    params: Dict[str, Any] = {"fields": fields, "limit": limit}
    if time_range: params["time_range"] = time_range
    if breakdowns: params["breakdowns"] = breakdowns
    return await _get(f"{BASE}/{adset_id}/insights", params=params)

@mcp.tool()
async def meta_get_ad_insights(ad_id: str, fields: str, time_range: Optional[str] = None, breakdowns: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    params: Dict[str, Any] = {"fields": fields, "limit": limit}
    if time_range: params["time_range"] = time_range
    if breakdowns: params["breakdowns"] = breakdowns
    return await _get(f"{BASE}/{ad_id}/insights", params=params)

@mcp.tool()
async def meta_fetch_pagination_url(url: str) -> Dict[str, Any]:
    """Fetch data from a next/previous pagination URL returned by Graph API."""
    if DRY_RUN:
        return _dry("fetch_pagination_url", url=url)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()

# -------- Activity / Change History --------

@mcp.tool()
async def meta_get_activities_by_adaccount(ad_account_id: str, limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {"limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{ad_account_id}/activities", params=params)

@mcp.tool()
async def meta_get_activities_by_adset(adset_id: str, limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {"limit": limit}
    if after: params["after"] = after
    return await _get(f"{BASE}/{adset_id}/activities", params=params)

if __name__ == "__main__":
    mcp.run()
