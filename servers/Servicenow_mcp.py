#!/usr/bin/env python3
"""
ServiceNow MCP Server - FastMCP version
A Model Context Protocol (MCP) server for ServiceNow.
"""

import os
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
import base64

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"servicenow_{name}", "args": kwargs}

# Required environment variables
SERVICENOW_INSTANCE_URL = os.getenv("SERVICENOW_INSTANCE_URL", "").rstrip("/")
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME", "")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")

if not SERVICENOW_INSTANCE_URL or not SERVICENOW_USERNAME or not SERVICENOW_PASSWORD:
    raise RuntimeError("Set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD environment variables")

mcp = FastMCP("ServiceNow MCP (native)")

class SNAuth:
    def __init__(self):
        pass

    def get_headers(self) -> Dict[str, str]:
        """Get basic authentication headers."""
        b64 = base64.b64encode(f"{SERVICENOW_USERNAME}:{SERVICENOW_PASSWORD}".encode()).decode()
        return {"Authorization": f"Basic {b64}", "Content-Type": "application/json"}

auth = SNAuth()

async def _sn_request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, params=params, json=json_data)
    headers = auth.get_headers()
    url = f"{SERVICENOW_INSTANCE_URL}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.request(method, url, headers=headers, params=params, json=json_data)
        resp.raise_for_status()
        # ServiceNow responses may be plain text for some endpoints; try JSON
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

# Incident Management
@mcp.tool()
async def servicenow_create_incident(short_description: str, description: Optional[str] = None, urgency: Optional[str] = None, impact: Optional[str] = None) -> Dict[str, Any]:
    """Create a new incident (table: incident)."""
    if DRY_RUN:
        return _dry("create_incident", short_description=short_description, description=description, urgency=urgency, impact=impact)
    body = {"short_description": short_description}
    if description: body["description"] = description
    if urgency: body["urgency"] = urgency
    if impact: body["impact"] = impact
    return await _sn_request("POST", "/api/now/table/incident", json_data=body)

@mcp.tool()
async def servicenow_update_incident(sys_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing incident by sys_id."""
    if DRY_RUN:
        return _dry("update_incident", sys_id=sys_id, fields=fields)
    return await _sn_request("PATCH", f"/api/now/table/incident/{sys_id}", json_data=fields)

@mcp.tool()
async def servicenow_add_comment(sys_id: str, comment: str) -> Dict[str, Any]:
    """Add a comment (work_notes) to an incident."""
    if DRY_RUN:
        return _dry("add_comment", sys_id=sys_id, comment=comment)
    return await _sn_request("PATCH", f"/api/now/table/incident/{sys_id}", json_data={"work_notes": comment})

@mcp.tool()
async def servicenow_resolve_incident(sys_id: str, close_notes: Optional[str] = None) -> Dict[str, Any]:
    """Resolve an incident by updating state/close notes."""
    if DRY_RUN:
        return _dry("resolve_incident", sys_id=sys_id, close_notes=close_notes)
    body = {"state": "6"}  # Resolved
    if close_notes:
        body["close_notes"] = close_notes
    return await _sn_request("PATCH", f"/api/now/table/incident/{sys_id}", json_data=body)

@mcp.tool()
async def servicenow_list_incidents(query: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """List incidents with optional encoded query."""
    if DRY_RUN:
        return _dry("list_incidents", query=query, limit=limit)
    params = {"sysparm_limit": str(limit)}
    if query:
        params["sysparm_query"] = query
    return await _sn_request("GET", "/api/now/table/incident", params=params)

# Generic Table Access
@mcp.tool()
async def servicenow_get_record(table: str, sys_id: str) -> Dict[str, Any]:
    """Get a record by sys_id from a table."""
    if DRY_RUN:
        return _dry("get_record", table=table, sys_id=sys_id)
    return await _sn_request("GET", f"/api/now/table/{table}/{sys_id}")

@mcp.tool()
async def servicenow_query_table(table: str, query: Optional[str] = None, fields: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Query a table with optional sysparm_query and fields."""
    if DRY_RUN:
        return _dry("query_table", table=table, query=query, fields=fields, limit=limit)
    params = {"sysparm_limit": str(limit)}
    if query:
        params["sysparm_query"] = query
    if fields:
        params["sysparm_fields"] = fields
    return await _sn_request("GET", f"/api/now/table/{table}", params=params)

@mcp.tool()
async def servicenow_create_record(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a record in a table."""
    if DRY_RUN:
        return _dry("create_record", table=table, data=data)
    return await _sn_request("POST", f"/api/now/table/{table}", json_data=data)

@mcp.tool()
async def servicenow_update_record(table: str, sys_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a record by sys_id."""
    if DRY_RUN:
        return _dry("update_record", table=table, sys_id=sys_id, data=data)
    return await _sn_request("PATCH", f"/api/now/table/{table}/{sys_id}", json_data=data)

@mcp.tool()
async def servicenow_delete_record(table: str, sys_id: str) -> Dict[str, Any]:
    """Delete a record by sys_id."""
    if DRY_RUN:
        return _dry("delete_record", table=table, sys_id=sys_id)
    return await _sn_request("DELETE", f"/api/now/table/{table}/{sys_id}")

# Service Catalog (examples)
@mcp.tool()
async def servicenow_list_catalog_items(limit: int = 50) -> Dict[str, Any]:
    """List service catalog items (sc_cat_item)."""
    if DRY_RUN:
        return _dry("list_catalog_items", limit=limit)
    return await _sn_request("GET", "/api/now/table/sc_cat_item", params={"sysparm_limit": str(limit)})

@mcp.tool()
async def servicenow_get_catalog_item(sys_id: str) -> Dict[str, Any]:
    """Get a specific catalog item."""
    if DRY_RUN:
        return _dry("get_catalog_item", sys_id=sys_id)
    return await _sn_request("GET", f"/api/now/table/sc_cat_item/{sys_id}")

if __name__ == "__main__":
    mcp.run()
