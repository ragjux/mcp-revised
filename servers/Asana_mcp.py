#!/usr/bin/env python3
"""
Asana MCP Server - Python FastMCP version
Provides read/write access to Asana via Model Control Protocol.
"""

import os
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

ASANA_TOKEN = os.getenv("ASANA_ACCESS_TOKEN")
if not ASANA_TOKEN:
    raise RuntimeError("ASANA_ACCESS_TOKEN environment variable is required")

headers = {
    'Authorization': f'Bearer {ASANA_TOKEN}',
    'Content-Type': 'application/json'
}

ASANA_API_BASE = "https://app.asana.com/api/1.0"

mcp = FastMCP("asana")


def _dry(name: str, **kwargs):
    logging.info(f"DRY RUN trigger for {name} with args {kwargs}")
    return {"dry_run": True, "tool": f"asana_{name}", "args": kwargs}


async def _request(method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None):
    if DRY_RUN:
        return _dry(method, endpoint=endpoint, params=params, json_data=json_data)
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{ASANA_API_BASE}/{endpoint}"
        response = await client.request(method, url, headers=headers, params=params, json=json_data)
        response.raise_for_status()
        return response.json()


@mcp.tool
async def asana_list_workspaces() -> Dict[str, Any]:
    """List all Asana workspaces accessible to the token."""
    return await _request("GET", "workspaces")


@mcp.tool
async def asana_search_projects(workspace: str, name_pattern: str, archived: bool = False) -> Dict[str, Any]:
    """
    Search projects in given workspace by name regex.
    """
    params = {'archived': str(archived).lower()}
    projects = await _request("GET", f"workspaces/{workspace}/projects", params=params)
    filtered = [p for p in projects['data'] if name_pattern in p.get('name', '')]
    return {"projects": filtered}


@mcp.tool
async def asana_get_task(task_id: str, opt_fields: Optional[str] = None) -> Dict[str, Any]:
    """Get details for a task."""
    params = {'opt_fields': opt_fields} if opt_fields else None
    return await _request("GET", f"tasks/{task_id}", params=params)


@mcp.tool
async def asana_create_task(project_id: str, name: str, notes: Optional[str] = None,
                           due_on: Optional[str] = None, assignee: Optional[str] = None,
                           completed: Optional[bool] = None) -> Dict[str, Any]:
    """Create a task in a specific project."""
    data = {
        "projects": [project_id],
        "name": name
    }
    if notes:
        data["notes"] = notes
    if due_on:
        data["due_on"] = due_on
    if assignee:
        data["assignee"] = assignee
    if completed is not None:
        data["completed"] = completed
    json_data = {"data": data}
    return await _request("POST", "tasks", json_data=json_data)


@mcp.tool
async def asana_update_task(task_id: str, name: Optional[str] = None, notes: Optional[str] = None,
                           due_on: Optional[str] = None, assignee: Optional[str] = None,
                           completed: Optional[bool] = None) -> Dict[str, Any]:
    """Update task fields."""
    data = {}
    if name is not None:
        data["name"] = name
    if notes is not None:
        data["notes"] = notes
    if due_on is not None:
        data["due_on"] = due_on
    if assignee is not None:
        data["assignee"] = assignee
    if completed is not None:
        data["completed"] = completed
    json_data = {"data": data}
    return await _request("PUT", f"tasks/{task_id}", json_data=json_data)


@mcp.tool
async def asana_delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    return await _request("DELETE", f"tasks/{task_id}")


@mcp.tool
async def asana_list_task_stories(task_id: str, opt_fields: Optional[str] = None) -> Dict[str, Any]:
    """List comments/stories for a task."""
    params = {'opt_fields': opt_fields} if opt_fields else None
    return await _request("GET", f"tasks/{task_id}/stories", params=params)


if __name__ == "__main__":
    mcp.run()
