#!/usr/bin/env python3
"""
Freshdesk MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Freshdesk API.
"""

import os
import httpx
from typing import Any, Dict, Optional
from fastmcp import FastMCP
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY", "")
FRESHDESK_DOMAIN = os.getenv("FRESHDESK_DOMAIN", "")

if not FRESHDESK_API_KEY or not FRESHDESK_DOMAIN:
    raise RuntimeError("Set FRESHDESK_API_KEY and FRESHDESK_DOMAIN environment variables")

BASE_URL = f"https://{FRESHDESK_DOMAIN}/api/v2"

mcp = FastMCP("Freshdesk MCP (native)")

def _dry(name: str, **kwargs):
    logging.info(f"DRY RUN: {name} with args {kwargs}")
    return {"dry_run": True, "tool": f"freshdesk_{name}", "args": kwargs}

def _auth_header() -> Dict[str, str]:
    # Basic Auth with API key and 'X' as password
    import base64
    token = f"{FRESHDESK_API_KEY}:X"
    encoded = base64.b64encode(token.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json"
    }

async def _make_request(method: str, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry(method, endpoint=endpoint, json_data=json_data, params=params)
    url = f"{BASE_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(method, url, headers=_auth_header(), json=json_data, params=params)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def freshdesk_create_ticket(subject: str, description: str, source: int, priority: int, status: int,
                                 email: Optional[str] = None, requester_id: Optional[int] = None,
                                 custom_fields: Optional[Dict] = None, additional_fields: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new ticket."""
    body = {
        "subject": subject,
        "description": description,
        "source": source,
        "priority": priority,
        "status": status,
    }
    if email:
        body["email"] = email
    if requester_id:
        body["requester_id"] = requester_id
    if custom_fields:
        body["custom_fields"] = custom_fields
    if additional_fields:
        body.update(additional_fields)
    payload = {"helpdesk_ticket": body}
    return await _make_request("POST", "/tickets", json_data=payload)

@mcp.tool()
async def freshdesk_update_ticket(ticket_id: int, ticket_fields: Dict) -> Dict[str, Any]:
    """Update an existing ticket."""
    payload = {"helpdesk_ticket": ticket_fields}
    return await _make_request("PUT", f"/tickets/{ticket_id}", json_data=payload)

@mcp.tool()
async def freshdesk_delete_ticket(ticket_id: int) -> Dict[str, Any]:
    """Delete a ticket."""
    return await _make_request("DELETE", f"/tickets/{ticket_id}")

@mcp.tool()
async def freshdesk_search_tickets(query: str) -> Dict[str, Any]:
    """Search tickets based on query string."""
    params = {"query": query}
    return await _make_request("GET", "/search/tickets", params=params)

@mcp.tool()
async def freshdesk_get_ticket_fields() -> Dict[str, Any]:
    """Get all ticket fields."""
    return await _make_request("GET", "/ticket_fields")

@mcp.tool()
async def freshdesk_get_tickets(page: Optional[int] = 1, per_page: Optional[int] = 30) -> Dict[str, Any]:
    """Get tickets with pagination."""
    params = {"page": page, "per_page": per_page}
    return await _make_request("GET", "/tickets", params=params)

@mcp.tool()
async def freshdesk_get_ticket(ticket_id: int) -> Dict[str, Any]:
    """Get a single ticket by ID."""
    return await _make_request("GET", f"/tickets/{ticket_id}")

@mcp.tool()
async def freshdesk_get_ticket_conversation(ticket_id: int) -> Dict[str, Any]:
    """Get conversation for a ticket."""
    return await _make_request("GET", f"/tickets/{ticket_id}/conversations")

@mcp.tool()
async def freshdesk_create_ticket_reply(ticket_id: int, body: str) -> Dict[str, Any]:
    """Reply to a ticket."""
    payload = {"body": body}
    return await _make_request("POST", f"/tickets/{ticket_id}/reply", json_data=payload)

@mcp.tool()
async def freshdesk_create_ticket_note(ticket_id: int, body: str) -> Dict[str, Any]:
    """Add note to a ticket."""
    payload = {"body": body}
    return await _make_request("POST", f"/tickets/{ticket_id}/notes", json_data=payload)

@mcp.tool()
async def freshdesk_get_agents(page: Optional[int] = 1, per_page: Optional[int] = 30) -> Dict[str, Any]:
    """Get all agents."""
    params = {"page": page, "per_page": per_page}
    return await _make_request("GET", "/agents", params=params)

@mcp.tool()
async def freshdesk_view_agent(agent_id: int) -> Dict[str, Any]:
    """Get a single agent."""
    return await _make_request("GET", f"/agents/{agent_id}")

@mcp.tool()
async def freshdesk_search_agents(query: str) -> Dict[str, Any]:
    """Search agents by query."""
    params = {"query": query}
    return await _make_request("GET", "/search/agents", params=params)

# Additional tools can be added similarly...

if __name__ == "__main__":
    mcp.run()
