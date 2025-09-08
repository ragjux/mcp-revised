#!/usr/bin/env python3
"""
Apollo.io MCP Server - FastMCP version
Implements Apollo.io tools: people_enrichment, organization_enrichment, people_search,
organization_search, organization_job_postings.
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
    return {"dry_run": True, "tool": f"apollo_{name}", "args": kwargs}

APOLLO_API_KEY = os.getenv("APOLLO_IO_API_KEY", "")
if not APOLLO_API_KEY:
    raise RuntimeError("Set APOLLO_IO_API_KEY")

BASE = "https://api.apollo.io/v1"

mcp = FastMCP("Apollo.io MCP (native)")

def _headers() -> Dict[str, str]:
    # Apollo uses X-Api-Key header for auth. [11]
    return {
        "X-Api-Key": APOLLO_API_KEY,
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

# 1) people_enrichment
@mcp.tool()
async def apollo_people_enrichment(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    domain: Optional[str] = None,
    organization_name: Optional[str] = None
) -> Dict[str, Any]:
    """Use the People Enrichment endpoint to enrich data for 1 person."""
    # People enrichment typically POST to /people/match with available identifiers. [2][6]
    body: Dict[str, Any] = {}
    if first_name: body["first_name"] = first_name
    if last_name: body["last_name"] = last_name
    if email: body["email"] = email
    if domain: body["domain"] = domain
    if organization_name: body["organization_name"] = organization_name
    return await _request("POST", "/people/match", json=body)

# 2) organization_enrichment
@mcp.tool()
async def apollo_organization_enrichment(
    domain: Optional[str] = None,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """Use the Organization Enrichment endpoint to enrich data for 1 company."""
    # Organization enrichment/match. Many clients use /organizations/match. [5]
    body: Dict[str, Any] = {}
    if domain: body["domain"] = domain
    if name: body["name"] = name
    return await _request("POST", "/organizations/match", json=body)

# 3) people_search
@mcp.tool()
async def apollo_people_search(
    q_organization_domains_list: Optional[List[str]] = None,
    person_titles: Optional[List[str]] = None,
    person_seniorities: Optional[List[str]] = None,
    page: int = 1,
    per_page: int = 25
) -> Dict[str, Any]:
    """Use the People Search endpoint to find people."""
    # People search commonly POST to /people/search with filters. [7]
    body: Dict[str, Any] = {"page": page, "per_page": per_page}
    if q_organization_domains_list is not None:
        body["q_organization_domains_list"] = q_organization_domains_list
    if person_titles is not None:
        body["person_titles"] = person_titles
    if person_seniorities is not None:
        body["person_seniorities"] = person_seniorities
    return await _request("POST", "/people/search", json=body)

# 4) organization_search
@mcp.tool()
async def apollo_organization_search(
    q_organization_domains_list: Optional[List[str]] = None,
    organization_locations: Optional[List[str]] = None,
    page: int = 1,
    per_page: int = 25
) -> Dict[str, Any]:
    """Use the Organization Search endpoint to find organizations."""
    body: Dict[str, Any] = {"page": page, "per_page": per_page}
    if q_organization_domains_list is not None:
        body["q_organization_domains_list"] = q_organization_domains_list
    if organization_locations is not None:
        body["organization_locations"] = organization_locations
    return await _request("POST", "/organizations/search", json=body)

# 5) organization_job_postings
@mcp.tool()
async def apollo_organization_job_postings(
    organization_id: str,
    page: int = 1,
    per_page: int = 25
) -> Dict[str, Any]:
    """Use the Organization Job Postings endpoint to find job postings for a specific organization."""
    # Jobs often under /organizations/{id}/jobs or similar; use search param if required by API. [10]
    params = {"page": page, "per_page": per_page}
    return await _request("GET", f"/organizations/{organization_id}/jobs", params=params)

if __name__ == "__main__":
    mcp.run()
