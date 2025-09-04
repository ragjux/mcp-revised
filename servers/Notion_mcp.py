#!/usr/bin/env python3
"""
Notion MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Notion operations.
"""

import os
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"notion_{name}", "args": kwargs}

NOTION_TOKEN = os.getenv("NOTION_API_KEY", "")
NOTION_BASE_URL = "https://api.notion.com/v1"

if not NOTION_TOKEN:
    raise RuntimeError("Set NOTION_API_KEY environment variable")

mcp = FastMCP("Notion MCP (native)")

def _auth_header() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }

async def _make_request(method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return {"dry_run": True, "method": method, "endpoint": endpoint, "params": params, "json": json_data}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            f"{NOTION_BASE_URL}{endpoint}",
            headers=_auth_header(),
            params=params,
            json=json_data
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def notion_list_databases() -> Dict[str, Any]:
    """List all Notion databases shared with the integration."""
    if DRY_RUN:
        return _dry("list_databases")
    try:
        data = await _make_request("GET", "/databases")
        databases = data.get("results", [])
        return {"databases": databases, "count": len(databases)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list databases: {e}"}

@mcp.tool()
async def notion_query_database(database_id: str, filter: Optional[Dict] = None, sorts: Optional[List[Dict]] = None, page_size: int = 100) -> Dict[str, Any]:
    """
    Query a Notion database.
    - database_id: ID of the database to query
    - filter: Optional filter object
    - sorts: Optional list of sort objects
    - page_size: Number of results per page
    """
    if DRY_RUN:
        return _dry("query_database", database_id=database_id, filter=filter, sorts=sorts, page_size=page_size)
    try:
        body = {"page_size": page_size}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        data = await _make_request("POST", f"/databases/{database_id}/query", json_data=body)
        pages = data.get("results", [])
        return {"database_id": database_id, "pages": pages, "count": len(pages)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to query database: {e}"}

@mcp.tool()
async def notion_create_page(parent_database_id: str, properties: Dict[str, Any], children: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Create a new page in a Notion database.
    - parent_database_id: ID of the parent database
    - properties: Page properties dictionary
    - children: Optional list of block children
    """
    if DRY_RUN:
        return _dry("create_page", parent_database_id=parent_database_id, properties=properties, children=children)
    try:
        body = {
            "parent": {"database_id": parent_database_id},
            "properties": properties
        }
        if children:
            body["children"] = children
        data = await _make_request("POST", "/pages", json_data=body)
        return {"status": "success", "page": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create page: {e}"}

@mcp.tool()
async def notion_update_page(page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update properties of an existing Notion page.
    - page_id: ID of the page to update
    - properties: Updated properties dictionary
    """
    if DRY_RUN:
        return _dry("update_page", page_id=page_id, properties=properties)
    try:
        body = {"properties": properties}
        data = await _make_request("PATCH", f"/pages/{page_id}", json_data=body)
        return {"status": "success", "page": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update page: {e}"}

@mcp.tool()
async def notion_search(query: str, page_size: int = 20) -> Dict[str, Any]:
    """
    Search across the Notion workspace.
    - query: Search query string
    - page_size: Number of results to return
    """
    if DRY_RUN:
        return _dry("search", query=query, page_size=page_size)
    try:
        body = {"query": query, "page_size": page_size}
        data = await _make_request("POST", "/search", json_data=body)
        results = data.get("results", [])
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to search workspace: {e}"}

@mcp.tool()
async def notion_get_database(database_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a Notion database.
    - database_id: ID of the database
    """
    if DRY_RUN:
        return _dry("get_database", database_id=database_id)
    try:
        data = await _make_request("GET", f"/databases/{database_id}")
        return {"database_id": database_id, "database": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get database details: {e}"}

@mcp.tool()
async def notion_get_block_children(block_id: str, page_size: int = 50) -> Dict[str, Any]:
    """
    Retrieve children blocks of a Notion block.
    - block_id: ID of the parent block
    - page_size: Number of child blocks to retrieve
    """
    if DRY_RUN:
        return _dry("get_block_children", block_id=block_id, page_size=page_size)
    try:
        params = {"page_size": page_size}
        data = await _make_request("GET", f"/blocks/{block_id}/children", params=params)
        children = data.get("results", [])
        return {"block_id": block_id, "children": children, "count": len(children)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get block children: {e}"}

if __name__ == "__main__":
    mcp.run()
