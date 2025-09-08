#!/usr/bin/env python3
"""
Google Chat MCP Server - Token-only authentication
A Model Context Protocol (MCP) server for Google Chat operations.
"""

import os
import json
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"chat_{name}", "args": kwargs}

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GCHAT_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GCHAT_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GCHAT_ACCESS_TOKEN and GCHAT_REFRESH_TOKEN environment variables")

CHAT_BASE = "https://chat.googleapis.com/v1"

mcp = FastMCP("Google Chat MCP (Token-only)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

@mcp.tool()
def chat_get_spaces() -> Dict[str, Any]:
    """List all Google Chat spaces the bot has access to."""
    if DRY_RUN:
        return _dry("chat_get_spaces")
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/spaces", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_get_space(space_name: str) -> Dict[str, Any]:
    """Get details about a specific space."""
    if DRY_RUN:
        return _dry("chat_get_space", space_name=space_name)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/{space_name}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_list_messages(space_name: str, page_size: int = 50, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List messages in a space."""
    if DRY_RUN:
        return _dry("chat_list_messages", space_name=space_name, page_size=page_size, page_token=page_token)
    
    params = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/{space_name}/messages", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_get_message(message_name: str) -> Dict[str, Any]:
    """Get a specific message by name."""
    if DRY_RUN:
        return _dry("chat_get_message", message_name=message_name)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/{message_name}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_create_message(space_name: str, text: str, thread_key: Optional[str] = None) -> Dict[str, Any]:
    """Create a message in a space."""
    if DRY_RUN:
        return _dry("chat_create_message", space_name=space_name, text=text, thread_key=thread_key)
    
    payload = {
        "text": text
    }
    
    if thread_key:
        payload["thread"] = {"name": thread_key}
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CHAT_BASE}/{space_name}/messages", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_update_message(message_name: str, text: str) -> Dict[str, Any]:
    """Update an existing message."""
    if DRY_RUN:
        return _dry("chat_update_message", message_name=message_name, text=text)
    
    payload = {
        "text": text
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.put(f"{CHAT_BASE}/{message_name}", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_delete_message(message_name: str) -> Dict[str, Any]:
    """Delete a message."""
    if DRY_RUN:
        return _dry("chat_delete_message", message_name=message_name)
    
    with httpx.Client(timeout=30) as c:
        r = c.delete(f"{CHAT_BASE}/{message_name}", headers=_auth_header())
        r.raise_for_status()
        return {"success": True, "message_name": message_name}

@mcp.tool()
def chat_create_card_message(space_name: str, card_title: str, card_text: str, 
                           thread_key: Optional[str] = None) -> Dict[str, Any]:
    """Create a message with a card in a space."""
    if DRY_RUN:
        return _dry("chat_create_card_message", space_name=space_name, card_title=card_title, 
                   card_text=card_text, thread_key=thread_key)
    
    payload = {
        "cards": [{
            "header": {
                "title": card_title
            },
            "sections": [{
                "widgets": [{
                    "textParagraph": {
                        "text": card_text
                    }
                }]
            }]
        }]
    }
    
    if thread_key:
        payload["thread"] = {"name": thread_key}
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CHAT_BASE}/{space_name}/messages", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_create_thread(space_name: str, name: str) -> Dict[str, Any]:
    """Create a thread in a space."""
    if DRY_RUN:
        return _dry("chat_create_thread", space_name=space_name, name=name)
    
    payload = {
        "name": name
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CHAT_BASE}/{space_name}/threads", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_list_threads(space_name: str, page_size: int = 50, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List threads in a space."""
    if DRY_RUN:
        return _dry("chat_list_threads", space_name=space_name, page_size=page_size, page_token=page_token)
    
    params = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/{space_name}/threads", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def chat_get_thread(thread_name: str) -> Dict[str, Any]:
    """Get details about a specific thread."""
    if DRY_RUN:
        return _dry("chat_get_thread", thread_name=thread_name)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CHAT_BASE}/{thread_name}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
