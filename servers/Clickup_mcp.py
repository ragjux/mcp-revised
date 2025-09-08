#!/usr/bin/env python3
"""
ClickUp MCP Server - FastMCP version
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

CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN", "")
if not CLICKUP_API_TOKEN:
    raise RuntimeError("Set CLICKUP_API_TOKEN")

BASE_URL = "https://api.clickup.com/api/v2"

mcp = FastMCP("ClickUp MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"clickup_{name}", "args": kwargs}

def _headers() -> Dict[str, str]:
    # Personal token placed directly in Authorization header per docs. [4][7]
    return {"Authorization": CLICKUP_API_TOKEN, "Content-Type": "application/json"}

async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, params=params, json=json)
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=_headers(), params=params, json=json)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

# ------------- Workspaces (Teams) -------------

@mcp.tool()
async def clickup_get_workspaces() -> Dict[str, Any]:
    """Get list of workspaces (teams)."""
    return await _request("GET", "/team")

# ------------- Spaces -------------

@mcp.tool()
async def clickup_get_spaces(team_id: str) -> Dict[str, Any]:
    """Get spaces within a workspace (team)."""
    return await _request("GET", f"/team/{team_id}/space", params={"archived": "false"})

# ------------- Folders -------------

@mcp.tool()
async def clickup_create_folder(space_id: str, name: str) -> Dict[str, Any]:
    """Create a new folder in a space."""
    return await _request("POST", f"/space/{space_id}/folder", json={"name": name})

# ------------- Lists -------------

@mcp.tool()
async def clickup_get_lists(space_id: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """Get lists in a folder or space."""
    if folder_id:
        return await _request("GET", f"/folder/{folder_id}/list")
    if space_id:
        return await _request("GET", f"/space/{space_id}/list")
    return {"status": "error", "message": "Provide folder_id or space_id"}

@mcp.tool()
async def clickup_create_list(parent_id: str, name: str, parent_type: str = "folder") -> Dict[str, Any]:
    """Create a new list in a folder or space. parent_type: folder|space"""
    if parent_type not in ("folder", "space"):
        return {"status": "error", "message": "parent_type must be 'folder' or 'space'"}
    return await _request("POST", f"/{parent_type}/{parent_id}/list", json={"name": name})

# ------------- Tasks -------------

@mcp.tool()
async def clickup_get_tasks(list_id: str, page: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get tasks from a list (paginated)."""
    params = {"page": page, "limit": limit}
    return await _request("GET", f"/list/{list_id}/task", params=params)

@mcp.tool()
async def clickup_create_task(list_id: str, name: str, description: Optional[str] = None, status: Optional[str] = None,
                              assignees: Optional[list] = None, due_date: Optional[int] = None, start_date: Optional[int] = None,
                              priority: Optional[int] = None) -> Dict[str, Any]:
    """Create a new task in a list."""
    body: Dict[str, Any] = {"name": name}
    if description is not None: body["description"] = description
    if status is not None: body["status"] = status
    if assignees is not None: body["assignees"] = assignees
    if due_date is not None: body["due_date"] = due_date
    if start_date is not None: body["start_date"] = start_date
    if priority is not None: body["priority"] = priority
    return await _request("POST", f"/list/{list_id}/task", json=body)

@mcp.tool()
async def clickup_update_task(task_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing task."""
    return await _request("PUT", f"/task/{task_id}", json=fields)

# ------------- Docs -------------

@mcp.tool()
async def clickup_get_docs_from_workspace(team_id: str) -> Dict[str, Any]:
    """Get all docs from a workspace."""
    # ClickUp Docs v3 endpoints: /team/{team_id}/doc (subject to availability)
    # If not available, users may need to use Docs 2.0 endpoints or the spaces/folders approach.
    return await _request("GET", f"/team/{team_id}/doc")

# ------------- Comments (basic) -------------

@mcp.tool()
async def clickup_get_task_comments(task_id: str) -> Dict[str, Any]:
    """Get comments for a task."""
    return await _request("GET", f"/task/{task_id}/comment")

@mcp.tool()
async def clickup_create_task_comment(task_id: str, comment_text: str) -> Dict[str, Any]:
    """Create a comment on a task."""
    return await _request("POST", f"/task/{task_id}/comment", json={"comment_text": comment_text})

# ------------- Checklists (basic) -------------

@mcp.tool()
async def clickup_create_checklist(task_id: str, name: str) -> Dict[str, Any]:
    """Create a checklist on a task."""
    return await _request("POST", f"/task/{task_id}/checklist", json={"name": name})

@mcp.tool()
async def clickup_add_checklist_item(checklist_id: str, name: str) -> Dict[str, Any]:
    """Add an item to a checklist."""
    return await _request("POST", f"/checklist/{checklist_id}/checklist_item", json={"name": name})

if __name__ == "__main__":
    mcp.run()
