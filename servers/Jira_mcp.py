#!/usr/bin/env python3
"""
Jira MCP Server - FastMCP version
"""

import os
import base64
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"jira_{name}", "args": kwargs}

JIRA_HOST = os.getenv("JIRA_HOST", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

if not (JIRA_HOST and JIRA_EMAIL and JIRA_API_TOKEN):
    raise RuntimeError("Set JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN")

BASE_URL = f"https://{JIRA_HOST}" if not JIRA_HOST.startswith("https://") else JIRA_HOST
API_PREFIX = "/rest/api/3"

mcp = FastMCP("Jira MCP (native)")

def _headers() -> Dict[str, str]:
    # Basic Auth via email:api_token [2][7]
    raw = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()
    token = base64.b64encode(raw).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("GET", path=path, params=params)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{BASE_URL}{API_PREFIX}{path}", headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()

async def _post(path: str, json: Dict[str, Any]) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("POST", path=path, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE_URL}{API_PREFIX}{path}", headers=_headers(), json=json)
        r.raise_for_status()
        return r.json()

async def _put(path: str, json: Dict[str, Any]) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("PUT", path=path, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.put(f"{BASE_URL}{API_PREFIX}{path}", headers=_headers(), json=json)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

async def _delete(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("DELETE", path=path, params=params)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.delete(f"{BASE_URL}{API_PREFIX}{path}", headers=_headers(), params=params)
        if r.status_code not in (200, 204):
            r.raise_for_status()
        return {"status": "success", "code": r.status_code}

# 1) User Management: get user account ID by email (GDPR-safe endpoint)
@mcp.tool()
async def jira_get_user_account_id(email: str) -> Dict[str, Any]:
    """Get user's account ID by email."""
    # GET /user/search?query=<email> (v3) [3][11]
    if DRY_RUN:
        return _dry("get_user_account_id", email=email)
    users = await _get("/user/search", params={"query": email})
    account_id = users["accountId"] if users else None
    return {"email": email, "accountId": account_id, "matches": users}

# 2) Issue Type Management
@mcp.tool()
async def jira_list_issue_types() -> Dict[str, Any]:
    """List all available issue types."""
    if DRY_RUN:
        return _dry("list_issue_types")
    return await _get("/issuetype")

# 3) Issue Link Types
@mcp.tool()
async def jira_list_link_types() -> Dict[str, Any]:
    """List all available issue link types."""
    if DRY_RUN:
        return _dry("list_link_types")
    return await _get("/issueLinkType")

# 4a) Get all issues in a project (simple)
@mcp.tool()
async def jira_get_project_issues(projectKey: str, jql: Optional[str] = None, maxResults: int = 50) -> Dict[str, Any]:
    """Get issues in a project with optional JQL filter."""
    if DRY_RUN:
        return _dry("get_project_issues", projectKey=projectKey, jql=jql, maxResults=maxResults)
    # Search API: /search with JQL [3][11]
    final_jql = jql or f'project = "{projectKey}" ORDER BY created DESC'
    return await _get("/search", params={"jql": final_jql, "maxResults": maxResults})

# 4b) Create issue (and subtask by setting issueType accordingly)
@mcp.tool()
async def jira_create_issue(
    projectKey: str,
    summary: str,
    issueType: str,
    description: Optional[str] = None,
    assignee_accountId: Optional[str] = None,
    labels: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
    priority: Optional[str] = None,
    parentIssueKey: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standard issue or subtask (if parentIssueKey provided and issueType='Sub-task')."""
    if DRY_RUN:
        return _dry("create_issue", projectKey=projectKey, summary=summary, issueType=issueType, description=description,
                    assignee_accountId=assignee_accountId, labels=labels, components=components, priority=priority,
                    parentIssueKey=parentIssueKey)
    fields: Dict[str, Any] = {
        "project": {"key": projectKey},
        "summary": summary,
        "issuetype": {"name": issueType}
    }
    if description:
        # For simplicity, send plain text; Jira also supports ADF document structure
        fields["description"] = description
    if assignee_accountId:
        fields["assignee"] = {"accountId": assignee_accountId}
    if labels:
        fields["labels"] = labels
    if components:
        fields["components"] = [{"name": c} for c in components]
    if priority:
        fields["priority"] = {"name": priority}
    if parentIssueKey:
        fields["parent"] = {"key": parentIssueKey}

    payload = {"fields": fields}
    return await _post("/issue", payload)

# 4c) Update issue fields
@mcp.tool()
async def jira_update_issue(
    issueKey: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    assignee_accountId: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Update issue fields; status change uses transition if provided."""
    if DRY_RUN:
        return _dry("update_issue", issueKey=issueKey, summary=summary, description=description,
                    assignee_accountId=assignee_accountId, status=status, priority=priority, labels=labels)
    updates: Dict[str, Any] = {"fields": {}}
    if summary is not None:
        updates["fields"]["summary"] = summary
    if description is not None:
        updates["fields"]["description"] = description
    if assignee_accountId is not None:
        updates["fields"]["assignee"] = {"accountId": assignee_accountId}
    if priority is not None:
        updates["fields"]["priority"] = {"name": priority}
    if labels is not None:
        updates["fields"]["labels"] = labels

    result = await _put(f"/issue/{issueKey}", updates)

    # If status provided, perform transition
    if status:
        # Find transition id matching status name
        trans = await _get(f"/issue/{issueKey}/transitions")
        tid = None
        for t in trans.get("transitions", []):
            if t.get("to", {}).get("name") == status:
                tid = t.get("id")
                break
        if tid:
            await _post(f"/issue/{issueKey}/transitions", {"transition": {"id": tid}})
        else:
            return {"status": "error", "message": f"Transition to status '{status}' not found"}
    return result

# 4d) Create issue link (dependencies)
@mcp.tool()
async def jira_create_issue_link(linkType: str, inwardIssueKey: str, outwardIssueKey: str) -> Dict[str, Any]:
    """Create an issue link (e.g., Blocks, Relates)."""
    if DRY_RUN:
        return _dry("create_issue_link", linkType=linkType, inwardIssueKey=inwardIssueKey, outwardIssueKey=outwardIssueKey)
    payload = {
        "type": {"name": linkType},
        "inwardIssue": {"key": inwardIssueKey},
        "outwardIssue": {"key": outwardIssueKey}
    }
    # POST /issueLink returns 201 with no body; handle empty text
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE_URL}{API_PREFIX}/issueLink", headers=_headers(), json=payload)
        if r.status_code not in (200, 201, 204):
            r.raise_for_status()
    return {"status": "success"}

# 4e) Delete issue (optional delete subtasks)
@mcp.tool()
async def jira_delete_issue(issueKey: str, deleteSubtasks: bool = False) -> Dict[str, Any]:
    """Delete issue; can cascade to subtasks."""
    if DRY_RUN:
        return _dry("delete_issue", issueKey=issueKey, deleteSubtasks=deleteSubtasks)
    return await _delete(f"/issue/{issueKey}", params={"deleteSubtasks": str(deleteSubtasks).lower()})

if __name__ == "__main__":
    mcp.run()
