#!/usr/bin/env python3
"""
Pipedrive MCP Server - FastMCP version
Read-only tools for deals, persons, organizations, pipelines, stages, and search.
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

PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN", "")
if not PIPEDRIVE_API_TOKEN:
    raise RuntimeError("Set PIPEDRIVE_API_TOKEN")

BASE = "https://api.pipedrive.com"

mcp = FastMCP("Pipedrive MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"pipedrive_{name}", "args": kwargs}

def _params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = {"api_token": PIPEDRIVE_API_TOKEN}
    if extra:
        p.update(extra)
    return p

async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("GET", path=path, params=params)
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, params=_params(params))
        r.raise_for_status()
        return r.json()

# ---------- Deals ----------

@mcp.tool()
async def pipedrive_get_deals(filter_id: Optional[int] = None, owner_id: Optional[int] = None,
                              person_id: Optional[int] = None, org_id: Optional[int] = None,
                              pipeline_id: Optional[int] = None, stage_id: Optional[int] = None,
                              status: Optional[str] = None, start: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Get deals (includes custom fields)."""
    params: Dict[str, Any] = {"start": start, "limit": limit}
    if filter_id is not None: params["filter_id"] = filter_id
    if owner_id is not None: params["owner_id"] = owner_id
    if person_id is not None: params["person_id"] = person_id
    if org_id is not None: params["org_id"] = org_id
    if pipeline_id is not None: params["pipeline_id"] = pipeline_id
    if stage_id is not None: params["stage_id"] = stage_id
    if status is not None: params["status"] = status
    return await _get("/api/v2/deals", params=params)  # v2 stable [7][2]

@mcp.tool()
async def pipedrive_get_deal(deal_id: int) -> Dict[str, Any]:
    """Get a specific deal by ID."""
    return await _get(f"/api/v2/deals/{deal_id}")  # v2 stable [7]

@mcp.tool()
async def pipedrive_search_deals(term: str, limit: int = 50) -> Dict[str, Any]:
    """Search deals by term."""
    return await _get("/api/v2/deals/search", params={"term": term, "limit": limit})  # v2 stable [7]

# ---------- Persons ----------

@mcp.tool()
async def pipedrive_get_persons(filter_id: Optional[int] = None, owner_id: Optional[int] = None,
                                org_id: Optional[int] = None, updated_since: Optional[str] = None,
                                start: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Get all persons (includes custom fields)."""
    params: Dict[str, Any] = {"start": start, "limit": limit}
    if filter_id is not None: params["filter_id"] = filter_id
    if owner_id is not None: params["owner_id"] = owner_id
    if org_id is not None: params["org_id"] = org_id
    if updated_since is not None: params["updated_since"] = updated_since
    return await _get("/api/v2/persons", params=params)  # v2 stable [5][7]

@mcp.tool()
async def pipedrive_get_person(person_id: int) -> Dict[str, Any]:
    """Get a specific person by ID."""
    return await _get(f"/api/v2/persons/{person_id}")  # v2 stable [7]

@mcp.tool()
async def pipedrive_search_persons(term: str, limit: int = 50) -> Dict[str, Any]:
    """Search persons by term."""
    return await _get("/api/v2/persons/search", params={"term": term, "limit": limit})  # v2 stable [7]

# ---------- Organizations ----------

@mcp.tool()
async def pipedrive_get_organizations(filter_id: Optional[int] = None, owner_id: Optional[int] = None,
                                      start: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Get all organizations (includes custom fields)."""
    params: Dict[str, Any] = {"start": start, "limit": limit}
    if filter_id is not None: params["filter_id"] = filter_id
    if owner_id is not None: params["owner_id"] = owner_id
    return await _get("/api/v2/organizations", params=params)  # v2 stable [4][7]

@mcp.tool()
async def pipedrive_get_organization(org_id: int) -> Dict[str, Any]:
    """Get a specific organization by ID."""
    return await _get(f"/api/v2/organizations/{org_id}")  # v2 stable [7]

@mcp.tool()
async def pipedrive_search_organizations(term: str, limit: int = 50) -> Dict[str, Any]:
    """Search organizations by term."""
    return await _get("/api/v2/organizations/search", params={"term": term, "limit": limit})  # v2 stable [7]

# ---------- Pipelines and Stages ----------

@mcp.tool()
async def pipedrive_get_pipelines() -> Dict[str, Any]:
    """Get all pipelines."""
    return await _get("/api/v2/pipelines")  # v2 stable [7]

@mcp.tool()
async def pipedrive_get_pipeline(pipeline_id: int) -> Dict[str, Any]:
    """Get a specific pipeline by ID."""
    return await _get(f"/api/v2/pipelines/{pipeline_id}")  # v2 stable [7]

@mcp.tool()
async def pipedrive_get_stages() -> Dict[str, Any]:
    """Get all stages (across pipelines)."""
    return await _get("/api/v2/stages")  # v2 stable [7][8]

# ---------- Leads and Global Search ----------

@mcp.tool()
async def pipedrive_search_leads(term: str, limit: int = 50) -> Dict[str, Any]:
    """Search leads by term."""
    return await _get("/api/v2/leads/search", params={"term": term, "limit": limit})  # v2 stable [7]

@mcp.tool()
async def pipedrive_search_all(term: str, item_types: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Global search across items (deals, persons, organizations, etc.). item_types is comma-separated types."""
    params = {"term": term, "limit": limit}
    if item_types:
        params["item_types"] = item_types
    return await _get("/api/v2/itemSearch", params=params)  # v2 stable [7]

if __name__ == "__main__":
    mcp.run()
