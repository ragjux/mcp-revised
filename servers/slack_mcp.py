#!/usr/bin/env python3
"""
Slack MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Slack operations.
"""

import os
import json
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"slack_{name}", "args": kwargs}

# Environment variables for Slack authentication
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")

if not SLACK_BOT_TOKEN:
    raise RuntimeError("Set SLACK_BOT_TOKEN environment variable")

SLACK_BASE = "https://slack.com/api"

mcp = FastMCP("Slack MCP (Bot Token)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with bot token."""
    return {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

@mcp.tool()
def slack_list_channels() -> Dict[str, Any]:
    """List all channels in the workspace."""
    if DRY_RUN:
        return _dry("list_channels")
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{SLACK_BASE}/conversations.list", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def slack_send_message(channel: str, text: str) -> Dict[str, Any]:
    """Send a message to a channel."""
    if DRY_RUN:
        return _dry("send_message", channel=channel, text=text)
    
    payload = {
        "channel": channel,
        "text": text
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{SLACK_BASE}/chat.postMessage", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def slack_get_messages(channel: str, limit: int = 10) -> Dict[str, Any]:
    """Get messages from a channel."""
    if DRY_RUN:
        return _dry("get_messages", channel=channel, limit=limit)
    
    params = {
        "channel": channel,
        "limit": limit
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{SLACK_BASE}/conversations.history", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def slack_list_users() -> Dict[str, Any]:
    """List all users in the workspace."""
    if DRY_RUN:
        return _dry("list_users")
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{SLACK_BASE}/users.list", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def slack_get_workspace_info() -> Dict[str, Any]:
    """Get information about the workspace."""
    if DRY_RUN:
        return _dry("get_workspace_info")
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{SLACK_BASE}/team.info", headers=_auth_header())
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()