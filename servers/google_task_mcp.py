#!/usr/bin/env python3
"""
Google Tasks MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Tasks operations.
"""

import os
import json
import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials

# Load environment variables from .env file
load_dotenv()
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"gtasks_{name}", "args": kwargs}

SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_PATH = os.getenv("GTASKS_TOKEN_PATH", "gcp-oauth.keys.json")
CREDENTIALS_PATH = os.getenv("GTASKS_CREDENTIALS_PATH", "credentials.json")

if not os.path.exists(CREDENTIALS_PATH):
    raise RuntimeError("Place credentials.json (OAuth client) in the repo root")

mcp = FastMCP("Google Tasks MCP (native)")

def _get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("tasks", "v1", credentials=creds)

@mcp.tool()
async def gtasks_list(task_list_id: Optional[str] = "@default", cursor: Optional[str] = None) -> Dict[str, Any]:
    """List all tasks in a Google Tasks list."""
    if DRY_RUN:
        return _dry("list", task_list_id=task_list_id, cursor=cursor)
    service = _get_service()
    params = {}
    if cursor:
        params["pageToken"] = cursor
    result = service.tasks().list(tasklist=task_list_id, **params).execute()
    return {"tasks": result.get("items", []), "nextPageToken": result.get("nextPageToken")}

@mcp.tool()
async def gtasks_search(query: str) -> Dict[str, Any]:
    """Search for tasks matching a query."""
    if DRY_RUN:
        return _dry("search", query=query)
    service = _get_service()
    all_tasks = []
    page_token = None
    while True:
        resp = service.tasks().list(tasklist="@default", pageToken=page_token).execute()
        for t in resp.get("items", []):
            if query.lower() in t.get("title", "").lower() or query.lower() in t.get("notes", "").lower():
                all_tasks.append(t)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return {"tasks": all_tasks, "count": len(all_tasks)}

@mcp.tool()
async def gtasks_create(
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    task_list_id: Optional[str] = "@default"
) -> Dict[str, Any]:
    """Create a new Google task."""
    if DRY_RUN:
        return _dry("create", title=title, notes=notes, due=due, task_list_id=task_list_id)
    service = _get_service()
    body = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = due
    result = service.tasks().insert(tasklist=task_list_id, body=body).execute()
    return {"status": "success", "task": result}

@mcp.tool()
async def gtasks_update(
    id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[str] = None,
    due: Optional[str] = None,
    task_list_id: Optional[str] = "@default"
) -> Dict[str, Any]:
    """Update an existing task."""
    if DRY_RUN:
        return _dry("update", id=id, title=title, notes=notes, status=status, due=due, task_list_id=task_list_id)
    service = _get_service()
    task = service.tasks().get(tasklist=task_list_id, task=id).execute()
    if title is not None:
        task["title"] = title
    if notes is not None:
        task["notes"] = notes
    if status is not None:
        task["status"] = status
    if due is not None:
        task["due"] = due
    result = service.tasks().update(tasklist=task_list_id, task=id, body=task).execute()
    return {"status": "success", "task": result}

@mcp.tool()
async def gtasks_delete(id: str, task_list_id: Optional[str] = "@default") -> Dict[str, Any]:
    """Delete a task."""
    if DRY_RUN:
        return _dry("delete", id=id, task_list_id=task_list_id)
    service = _get_service()
    service.tasks().delete(tasklist=task_list_id, task=id).execute()
    return {"status": "success", "message": "Task deleted"}

@mcp.tool()
async def gtasks_clear(task_list_id: Optional[str] = "@default") -> Dict[str, Any]:
    """Clear completed tasks."""
    if DRY_RUN:
        return _dry("clear", task_list_id=task_list_id)
    service = _get_service()
    service.tasks().clear(tasklist=task_list_id).execute()
    return {"status": "success", "message": "Completed tasks cleared"}

if __name__ == "__main__":
    mcp.run()
