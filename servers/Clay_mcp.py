#!/usr/bin/env python3
"""
Clay MCP Server - FastMCP version
Minimal read-style tools for people/companies and enrichment using the Clay API.
"""

import os
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "true"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"clay_{name}", "args": kwargs}

CLAY_API_KEY = os.getenv("CLAY_API_KEY", "")
if not CLAY_API_KEY:
    raise RuntimeError("Set CLAY_API_KEY")

BASE = "https://api.clay.run"  # Clay REST base

mcp = FastMCP("Clay MCP (native)")

def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {CLAY_API_KEY}",
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

# People

@mcp.tool()
async def clay_find_person_by_email(email: str) -> Dict[str, Any]:
    """Find a person by email (enrichment)."""
    return await _request("GET", "/v1/people/find", params={"email": email})

@mcp.tool()
async def clay_search_people(query: str, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
    """Search people by a query string."""
    return await _request("GET", "/v1/people/search", params={"q": query, "page": page, "per_page": per_page})

# Companies

@mcp.tool()
async def clay_find_company_by_domain(domain: str) -> Dict[str, Any]:
    """Find a company by domain (enrichment)."""
    return await _request("GET", "/v1/companies/find", params={"domain": domain})

@mcp.tool()
async def clay_search_companies(query: str, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
    """Search companies by a query string."""
    return await _request("GET", "/v1/companies/search", params={"q": query, "page": page, "per_page": per_page})

# Lists/Workflows (read-only)

@mcp.tool()
async def clay_list_projects() -> Dict[str, Any]:
    """List Clay projects available to the API key."""
    return await _request("GET", "/v1/projects")

@mcp.tool()
async def clay_list_workflows(project_id: str) -> Dict[str, Any]:
    """List workflows in a project."""
    return await _request("GET", f"/v1/projects/{project_id}/workflows")

@mcp.tool()
async def clay_get_workflow_runs(project_id: str, workflow_id: str, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
    """Get workflow run history."""
    return await _request("GET", f"/v1/projects/{project_id}/workflows/{workflow_id}/runs",
                          params={"page": page, "per_page": per_page})

if __name__ == "__main__":
    mcp.run()
