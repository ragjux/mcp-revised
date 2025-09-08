#!/usr/bin/env python3
"""
Zendesk MCP Server - FastMCP version ticket CRUD, search, comments/notes, and linked incidents.
"""

import os
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
from base64 import b64encode
import logging

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "true"

EMAIL = os.getenv("ZENDESK_EMAIL", "")
TOKEN = os.getenv("ZENDESK_TOKEN", "")
SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN", "")

if not (EMAIL and TOKEN and SUBDOMAIN):
    raise RuntimeError("Set ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_SUBDOMAIN")

BASE = f"https://{SUBDOMAIN}.zendesk.com/api/v2"

mcp = FastMCP("Zendesk MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"zendesk_{name}", "args": kwargs}

def _headers() -> Dict[str, str]:
    # Basic auth with email/token:token per Zendesk docs. [3][2]
    cred = f"{EMAIL}/token:{TOKEN}"
    auth = b64encode(cred.encode()).decode()
    return {"Authorization": f"Basic {auth}", "Content-Type": "application/json", "Accept": "application/json"}

async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY:
        return _dry("GET", path=path, params=params)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{BASE}{path}", headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()

async def _post(path: str, json: Dict[str, Any]) -> Dict[str, Any]:
    if DRY:
        return _dry("POST", path=path, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE}{path}", headers=_headers(), json=json)
        r.raise_for_status()
        return r.json()

async def _put(path: str, json: Dict[str, Any]) -> Dict[str, Any]:
    if DRY:
        return _dry("PUT", path=path, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.put(f"{BASE}{path}", headers=_headers(), json=json)
        r.raise_for_status()
        return r.json()

# -------- Tickets -------- [11]

@mcp.tool()
async def zendesk_get_ticket(ticket_id: int) -> Dict[str, Any]:
    """Retrieve a ticket by ID."""
    return await _get(f"/tickets/{ticket_id}.json")

@mcp.tool()
async def zendesk_get_ticket_details(ticket_id: int, include_comments: bool = True) -> Dict[str, Any]:
    """Get ticket with comments if include_comments is true."""
    if include_comments:
        # Incremental audit/comments API can be used as well; here use comments endpoint.
        ticket = await _get(f"/tickets/{ticket_id}.json")
        comments = await _get(f"/tickets/{ticket_id}/comments.json")
        return {"ticket": ticket.get("ticket"), "comments": comments.get("comments")}
    return await _get(f"/tickets/{ticket_id}.json")

@mcp.tool()
async def zendesk_search(query: str, page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
    """Search tickets using Zendesk query syntax."""
    params: Dict[str, Any] = {"query": query}
    if page is not None: params["page"] = page
    if per_page is not None: params["per_page"] = per_page
    return await _get("/search.json", params=params)

@mcp.tool()
async def zendesk_create_ticket(subject: str, comment: str, requester_email: Optional[str] = None,
                                priority: Optional[str] = None, tags: Optional[list] = None) -> Dict[str, Any]:
    """Create a new ticket."""
    payload: Dict[str, Any] = {"ticket": {"subject": subject, "comment": {"body": comment}}}
    if requester_email: payload["ticket"]["requester"] = {"email": requester_email}
    if priority: payload["ticket"]["priority"] = priority
    if tags: payload["ticket"]["tags"] = tags
    return await _post("/tickets.json", payload)

@mcp.tool()
async def zendesk_update_ticket(ticket_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update ticket properties; fields mapped into ticket object."""
    return await _put(f"/tickets/{ticket_id}.json", {"ticket": fields})

# -------- Comments / Notes --------

@mcp.tool()
async def zendesk_add_private_note(ticket_id: int, body: str) -> Dict[str, Any]:
    """Add an internal (private) note to a ticket."""
    return await _post(f"/tickets/{ticket_id}.json", {"ticket": {"comment": {"body": body, "public": False}}})

@mcp.tool()
async def zendesk_add_public_note(ticket_id: int, body: str) -> Dict[str, Any]:
    """Add a public reply to a ticket."""
    return await _post(f"/tickets/{ticket_id}.json", {"ticket": {"comment": {"body": body, "public": True}}})

# -------- Linked incidents --------

@mcp.tool()
async def zendesk_get_linked_incidents(problem_ticket_id: int) -> Dict[str, Any]:
    """Get incident tickets linked to a problem ticket."""
    return await _get(f"/problems/{problem_ticket_id}/incidents.json")

if __name__ == "__main__":
    mcp.run()
