#!/usr/bin/env python3
"""
Intercom MCP Server - FastMCP version
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
from datetime import datetime

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"intercom_{name}", "args": kwargs}

ACCESS_TOKEN = os.getenv("INTERCOM_ACCESS_TOKEN", "")
if not ACCESS_TOKEN:
    raise RuntimeError("Set INTERCOM_ACCESS_TOKEN")

BASE = "https://api.intercom.io"

mcp = FastMCP("Intercom MCP (native)")

def _headers() -> Dict[str, str]:
    # Optionally include specific version header: 'Intercom-Version': '2.11'
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

async def _request(method: str, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, json=json, params=params)
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=_headers(), json=json, params=params)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

def _parse_ddmmyyyy(d: str) -> int:
    # Intercom expects unix timestamps for created_at filters. [8]
    return int(datetime.strptime(d, "%d/%m/%Y").timestamp())

def _date_range_query(startDate: Optional[str], endDate: Optional[str], field: str = "created_at") -> List[Dict[str, Any]]:
    filters: List[Dict[str, Any]] = []
    if startDate:
        filters.append({"field": field, "operator": ">", "value": _parse_ddmmyyyy(startDate)})
    if endDate:
        # include the end day up to 23:59:59
        ts = _parse_ddmmyyyy(endDate) + 86399
        filters.append({"field": field, "operator": "<", "value": ts})
    return filters

# 1) list_conversations
@mcp.tool()
async def intercom_list_conversations(
    startDate: str,
    endDate: str,
    keyword: Optional[str] = None,
    exclude: Optional[str] = None,
    starting_after: Optional[str] = None,
    per_page: int = 50
) -> Dict[str, Any]:
    """Retrieve conversations within a date range with optional content include/exclude."""
    if DRY_RUN:
        return _dry("list_conversations", startDate=startDate, endDate=endDate, keyword=keyword, exclude=exclude, starting_after=starting_after, per_page=per_page)
    # Build query: (created_at range) AND (source.body ~ keyword) AND (source.body !~ exclude)
    base_filters = _date_range_query(startDate, endDate, field="created_at")
    if keyword:
        base_filters.append({"field": "source.body", "operator": "~", "value": keyword})
    if exclude:
        base_filters.append({"field": "source.body", "operator": "!~", "value": exclude})
    body: Dict[str, Any] = {"query": {"operator": "AND", "value": base_filters}, "pagination": {"per_page": per_page}}
    if starting_after:
        body["pagination"]["starting_after"] = starting_after
    return await _request("POST", "/conversations/search", json=body)  # [8][2]

# 2) search_conversations_by_customer
@mcp.tool()
async def intercom_search_conversations_by_customer(
    customerIdentifier: str,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    starting_after: Optional[str] = None,
    per_page: int = 50
) -> Dict[str, Any]:
    """Find conversations for a customer by email or Intercom contact id, with optional date/keyword filters."""
    if DRY_RUN:
        return _dry("search_conversations_by_customer", customerIdentifier=customerIdentifier, startDate=startDate, endDate=endDate, keywords=keywords, starting_after=starting_after, per_page=per_page)
    filters: List[Dict[str, Any]] = []
    # If looks like an email, search source.body contains email as a fallback; otherwise try contact_ids equals
    if "@" in customerIdentifier:
        # Include email in body to catch email-only mentions when no contact exists
        filters.append({"field": "source.body", "operator": "~", "value": customerIdentifier})
    else:
        filters.append({"field": "contact_ids", "operator": "=", "value": customerIdentifier})
    filters += _date_range_query(startDate, endDate, field="created_at")
    if keywords:
        # Combine multiple keywords with OR then AND with other filters
        kw_or = {"operator": "OR", "value": [{"field": "source.body", "operator": "~", "value": k} for k in keywords]}
        query = {"operator": "AND", "value": filters + [kw_or]}
    else:
        query = {"operator": "AND", "value": filters}
    body: Dict[str, Any] = {"query": query, "pagination": {"per_page": per_page}}
    if starting_after:
        body["pagination"]["starting_after"] = starting_after
    return await _request("POST", "/conversations/search", json=body)  # [8][2]

# 3) search_tickets_by_status
@mcp.tool()
async def intercom_search_tickets_by_status(
    status: str,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    starting_after: Optional[str] = None,
    per_page: int = 50
) -> Dict[str, Any]:
    """Retrieve tickets by status with optional date range."""
    if DRY_RUN:
        return _dry("search_tickets_by_status", status=status, startDate=startDate, endDate=endDate, starting_after=starting_after, per_page=per_page)
    filters: List[Dict[str, Any]] = [{"field": "status", "operator": "=", "value": status}]
    filters += _date_range_query(startDate, endDate, field="created_at")
    body: Dict[str, Any] = {"query": {"operator": "AND", "value": filters}, "pagination": {"per_page": per_page}}
    if starting_after:
        body["pagination"]["starting_after"] = starting_after
    return await _request("POST", "/tickets/search", json=body)  # [3]

# 4) search_tickets_by_customer
@mcp.tool()
async def intercom_search_tickets_by_customer(
    customerIdentifier: str,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    starting_after: Optional[str] = None,
    per_page: int = 50
) -> Dict[str, Any]:
    """Find tickets associated with a customer by email content or contact id."""
    if DRY_RUN:
        return _dry("search_tickets_by_customer", customerIdentifier=customerIdentifier, startDate=startDate, endDate=endDate, starting_after=starting_after, per_page=per_page)
    filters: List[Dict[str, Any]] = []
    if "@" in customerIdentifier:
        # Search conversations’ source.body is not available for tickets; use contact email field if present in ticket schema,
        # otherwise search via linked_objects requires joining; here we filter by contact_ids when given id else fallback to subject/body text if indexed.
        filters.append({"field": "contact_email", "operator": "=", "value": customerIdentifier})
    else:
        filters.append({"field": "contact_ids", "operator": "=", "value": customerIdentifier})
    filters += _date_range_query(startDate, endDate, field="created_at")
    body: Dict[str, Any] = {"query": {"operator": "AND", "value": filters}, "pagination": {"per_page": per_page}}
    if starting_after:
        body["pagination"]["starting_after"] = starting_after
    return await _request("POST", "/tickets/search", json=body)  # [3][6]

if __name__ == "__main__":
    mcp.run()
