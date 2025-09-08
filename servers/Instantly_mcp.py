#!/usr/bin/env python3
"""
Instantly MCP Server - FastMCP version (API v2)
Implements tools for campaigns, analytics, accounts, leads, lead lists, emails, email verification, and API keys..
"""

import os
from typing import Any, Dict, Optional, List
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
    return {"dry_run": True, "tool": f"instantly_{name}", "args": kwargs}

API_KEY = os.getenv("INSTANTLY_API_KEY", "")
if not API_KEY:
    raise RuntimeError("Set INSTANTLY_API_KEY")

BASE = "https://api.instantly.ai/api/v2"

mcp = FastMCP("Instantly MCP (native)")

def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, params=params, json=json)
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=_headers(), params=params, json=json)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

# -------- Campaign Management -------- [5][3]

@mcp.tool()
async def instantly_list_campaigns(limit: int = 10, starting_after: Optional[str] = None, status: Optional[int] = None) -> Dict[str, Any]:
    """List campaigns with optional pagination and status filter."""
    params: Dict[str, Any] = {"limit": limit}
    if starting_after: params["starting_after"] = starting_after
    if status is not None: params["status"] = status
    return await _request("GET", "/campaigns", params=params)

@mcp.tool()
async def instantly_get_campaign(id: str) -> Dict[str, Any]:
    """Get a campaign by ID."""
    return await _request("GET", f"/campaigns/{id}")

@mcp.tool()
async def instantly_create_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new email campaign (pass API-compliant payload)."""
    return await _request("POST", "/campaigns", json=payload)

@mcp.tool()
async def instantly_update_campaign(id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing campaign."""
    return await _request("PATCH", f"/campaigns/{id}", json=payload)

@mcp.tool()
async def instantly_activate_campaign(id: str) -> Dict[str, Any]:
    """Activate a campaign."""
    return await _request("POST", f"/campaigns/{id}/activate")

# -------- Analytics -------- [3][6]

@mcp.tool()
async def instantly_get_campaign_analytics(id: Optional[str] = None, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
    """Get analytics for campaigns (optionally a specific campaign id) within a date range (YYYY-MM-DD)."""
    params: Dict[str, Any] = {}
    if id: params["id"] = id
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return await _request("GET", "/campaigns/analytics", params=params)

@mcp.tool()
async def instantly_get_campaign_analytics_overview(id: Optional[str] = None, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
    """Get analytics overview for all or a specific campaign (YYYY-MM-DD date range)."""
    params: Dict[str, Any] = {}
    if id: params["id"] = id
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    return await _request("GET", "/campaigns/analytics/overview", params=params)

# -------- Account Management -------- [6][8]

@mcp.tool()
async def instantly_list_accounts(limit: int = 10, starting_after: Optional[str] = None, search: Optional[str] = None,
                                  status: Optional[int] = None, provider_code: Optional[int] = None) -> Dict[str, Any]:
    """List sending accounts with optional filters and pagination."""
    params: Dict[str, Any] = {"limit": limit}
    if starting_after: params["starting_after"] = starting_after
    if search: params["search"] = search
    if status is not None: params["status"] = status
    if provider_code is not None: params["provider_code"] = provider_code
    return await _request("GET", "/accounts", params=params)

@mcp.tool()
async def instantly_create_account(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new sending account (payload as per API)."""
    return await _request("POST", "/accounts", json=payload)

@mcp.tool()
async def instantly_update_account(id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update a sending account."""
    return await _request("PATCH", f"/accounts/{id}", json=payload)

@mcp.tool()
async def instantly_get_warmup_analytics(emails: List[str]) -> Dict[str, Any]:
    """Get warmup analytics for email accounts."""
    return await _request("POST", "/accounts/warmup-analytics", json={"emails": emails})

# -------- Lead Management -------- [6][9]

@mcp.tool()
async def instantly_list_leads(campaign: Optional[str] = None, list_id: Optional[str] = None, limit: int = 25, starting_after: Optional[str] = None) -> Dict[str, Any]:
    """List leads with optional campaign/list filter and pagination."""
    body: Dict[str, Any] = {"limit": limit}
    if campaign: body["campaign"] = campaign
    if list_id: body["list_id"] = list_id
    if starting_after: body["starting_after"] = starting_after
    return await _request("POST", "/leads/list", json=body)

@mcp.tool()
async def instantly_create_lead(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new lead."""
    return await _request("POST", "/leads", json=payload)

@mcp.tool()
async def instantly_update_lead(id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update a lead."""
    return await _request("PATCH", f"/leads/{id}", json=payload)

@mcp.tool()
async def instantly_move_leads(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Move leads between campaigns or lists; payload per API (e.g., ids, source, destination)."""
    return await _request("POST", "/leads/move", json=payload)

# -------- Lead Lists --------

@mcp.tool()
async def instantly_list_lead_lists(limit: int = 25, starting_after: Optional[str] = None) -> Dict[str, Any]:
    """List lead lists with pagination."""
    params: Dict[str, Any] = {"limit": limit}
    if starting_after: params["starting_after"] = starting_after
    return await _request("GET", "/lead-lists", params=params)

@mcp.tool()
async def instantly_create_lead_list(name: str) -> Dict[str, Any]:
    """Create a new lead list."""
    return await _request("POST", "/lead-lists", json={"name": name})

# -------- Email Operations -------- [8]

@mcp.tool()
async def instantly_send_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a single email (payload per API: from, to, subject, body, etc.)."""
    return await _request("POST", "/emails/send", json=payload)

@mcp.tool()
async def instantly_list_emails(limit: int = 25, starting_after: Optional[str] = None, campaign_id: Optional[str] = None) -> Dict[str, Any]:
    """List emails with optional filters."""
    params: Dict[str, Any] = {"limit": limit}
    if starting_after: params["starting_after"] = starting_after
    if campaign_id: params["campaign_id"] = campaign_id
    return await _request("GET", "/emails", params=params)

# -------- Email Verification --------

@mcp.tool()
async def instantly_verify_email(email: str) -> Dict[str, Any]:
    """Verify if an email address is valid."""
    return await _request("POST", "/email-verification", json={"email": email})

# -------- API Key Management --------

@mcp.tool()
async def instantly_list_api_keys(limit: int = 25, starting_after: Optional[str] = None) -> Dict[str, Any]:
    """List API keys (requires appropriate scopes)."""
    params: Dict[str, Any] = {"limit": limit}
    if starting_after: params["starting_after"] = starting_after
    return await _request("GET", "/api-keys", params=params)

@mcp.tool()
async def instantly_create_api_key(name: str, scopes: List[str]) -> Dict[str, Any]:
    """Create a new API key with scopes."""
    return await _request("POST", "/api-keys", json={"name": name, "scopes": scopes})

if __name__ == "__main__":
    mcp.run()
