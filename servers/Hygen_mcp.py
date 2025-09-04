#!/usr/bin/env python3
"""
HeyGen MCP Server - FastMCP version
A Model Context Protocol (MCP) server for HeyGen.
"""

import os
import httpx
from typing import Any, Dict, Optional
from fastmcp import FastMCP
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"heygen_{name}", "args": kwargs}

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_BASE_URL = "https://api.heygen.com/v1"

if not HEYGEN_API_KEY:
    raise RuntimeError("Set HEYGEN_API_KEY environment variable")

mcp = FastMCP("HeyGen MCP (native)")

def _auth_header() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {HEYGEN_API_KEY}",
        "Content-Type": "application/json"
    }

async def _make_request(endpoint: str, method: str = "GET", json_data: Optional[Dict] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return {"dry_run": True, "endpoint": endpoint, "method": method, "json": json_data}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            f"{HEYGEN_BASE_URL}{endpoint}",
            headers=_auth_header(),
            json=json_data,
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def heygen_get_remaining_credits() -> Dict[str, Any]:
    """Retrieve remaining credits in HeyGen account."""
    if DRY_RUN:
        return _dry("get_remaining_credits")
    try:
        data = await _make_request("/credits")
        return {"credits": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get remaining credits: {e}"}

@mcp.tool()
async def heygen_get_voices() -> Dict[str, Any]:
    """Retrieve list of available voices (limited to first 100)."""
    if DRY_RUN:
        return _dry("get_voices")
    try:
        data = await _make_request("/voices?limit=100")
        return {"voices": data.get("voices", [])}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get voices: {e}"}

@mcp.tool()
async def heygen_get_avatar_groups() -> Dict[str, Any]:
    """Retrieve list of HeyGen avatar groups."""
    if DRY_RUN:
        return _dry("get_avatar_groups")
    try:
        data = await _make_request("/avatar-groups")
        return {"avatar_groups": data.get("avatarGroups", [])}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get avatar groups: {e}"}

@mcp.tool()
async def heygen_get_avatars_in_avatar_group(avatar_group_id: str) -> Dict[str, Any]:
    """Retrieve avatars in a specific avatar group."""
    if DRY_RUN:
        return _dry("get_avatars_in_avatar_group", avatar_group_id=avatar_group_id)
    try:
        data = await _make_request(f"/avatar-groups/{avatar_group_id}/avatars")
        return {"avatars": data.get("avatars", [])}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get avatars in group: {e}"}

@mcp.tool()
async def heygen_generate_avatar_video(avatar_id: str, text: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a new avatar video with specified avatar, text, and voice."""
    if DRY_RUN:
        return _dry("generate_avatar_video", avatar_id=avatar_id, text=text, voice_id=voice_id)
    try:
        payload = {
            "avatarId": avatar_id,
            "script": {"type": "text", "input": text}
        }
        if voice_id:
            payload["voiceId"] = voice_id
        data = await _make_request("/videos", method="POST", json_data=payload)
        return {"video": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate avatar video: {e}"}

@mcp.tool()
async def heygen_get_avatar_video_status(video_id: str) -> Dict[str, Any]:
    """Retrieve status of a generated avatar video."""
    if DRY_RUN:
        return _dry("get_avatar_video_status", video_id=video_id)
    try:
        data = await _make_request(f"/videos/{video_id}")
        return {"video_status": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get avatar video status: {e}"}

if __name__ == "__main__":
    mcp.run()
