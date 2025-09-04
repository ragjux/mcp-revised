#!/usr/bin/env python3
"""
Zoom MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Zoom API.
"""
import os
import base64
import asyncio
from typing import Any, Dict, Optional
from fastmcp import FastMCP
import httpx
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

ZOOM_API_KEY = os.getenv("ZOOM_API_KEY")
ZOOM_API_SECRET = os.getenv("ZOOM_API_SECRET")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")

if not ZOOM_API_KEY or not ZOOM_API_SECRET or not ZOOM_ACCOUNT_ID:
    raise RuntimeError("Set ZOOM_API_KEY, ZOOM_API_SECRET, and ZOOM_ACCOUNT_ID environment variables")

TOKEN_URL = "https://zoom.us/oauth/token"
API_BASE_URL = "https://api.zoom.us/v2"

mcp = FastMCP("Zoom MCP (native)")

class ZoomAuth:
    def __init__(self):
        self._access_token = None
        self._token_expires_at = 0

    async def get_access_token(self) -> str:
        import time
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        auth_str = f"{ZOOM_API_KEY}:{ZOOM_API_SECRET}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_auth}"
        }
        params = {
            "grant_type": "account_credentials",
            "account_id": ZOOM_ACCOUNT_ID
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(TOKEN_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in
            return self._access_token

zoom_auth = ZoomAuth()

async def _make_request(endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None,
                        json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return {"dry_run": True, "method": method, "endpoint": endpoint, "params": params, "json": json_data}
    token = await zoom_auth.get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(method, url, headers=headers, params=params, json=json_data)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def zoom_get_current_user() -> Dict[str, Any]:
    """Get information about the authenticated Zoom user."""
    if DRY_RUN:
        return _dry("get_current_user")
    return await _make_request("/users/me")

@mcp.tool()
async def zoom_list_meetings(user_id: str, page_size: int = 30, page_number: int = 1) -> Dict[str, Any]:
    """List meetings for a Zoom user."""
    if DRY_RUN:
        return _dry("list_meetings", user_id=user_id, page_size=page_size, page_number=page_number)
    params = {"page_size": page_size, "page_number": page_number}
    return await _make_request(f"/users/{user_id}/meetings", params=params)

@mcp.tool()
async def zoom_get_meeting(meeting_id: str) -> Dict[str, Any]:
    """Get details of a Zoom meeting."""
    if DRY_RUN:
        return _dry("get_meeting", meeting_id=meeting_id)
    return await _make_request(f"/meetings/{meeting_id}")

@mcp.tool()
async def zoom_get_meeting_recordings(meeting_id: str) -> Dict[str, Any]:
    """Get recording files for a meeting."""
    if DRY_RUN:
        return _dry("get_meeting_recordings", meeting_id=meeting_id)
    return await _make_request(f"/meetings/{meeting_id}/recordings")

@mcp.tool()
async def zoom_list_users(page_size: int = 30, page_number: int = 1) -> Dict[str, Any]:
    """List Zoom users in the account."""
    if DRY_RUN:
        return _dry("list_users", page_size=page_size, page_number=page_number)
    params = {"page_size": page_size, "page_number": page_number}
    return await _make_request("/users", params=params)


if __name__ == "__main__":
    mcp.run()
