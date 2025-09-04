#!/usr/bin/env python3
"""
Calendly MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Calendly operations.
"""

import os
import httpx
import base64
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from urllib.parse import urlencode

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"calendly_{name}", "args": kwargs}

CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY", "")
CALENDLY_ACCESS_TOKEN = os.getenv("CALENDLY_ACCESS_TOKEN", "")
CALENDLY_CLIENT_ID = os.getenv("CALENDLY_CLIENT_ID", "")
CALENDLY_CLIENT_SECRET = os.getenv("CALENDLY_CLIENT_SECRET", "")
CALENDLY_REFRESH_TOKEN = os.getenv("CALENDLY_REFRESH_TOKEN", "")
CALENDLY_USER_URI = os.getenv("CALENDLY_USER_URI", "")
CALENDLY_ORGANIZATION_URI = os.getenv("CALENDLY_ORGANIZATION_URI", "")

CALENDLY_BASE_URL = "https://api.calendly.com"
CALENDLY_AUTH_URL = "https://auth.calendly.com"

if not CALENDLY_API_KEY and not CALENDLY_ACCESS_TOKEN:
    raise RuntimeError("Set CALENDLY_API_KEY or CALENDLY_ACCESS_TOKEN environment variable")

mcp = FastMCP("Calendly MCP (native)")

def _auth_header() -> Dict[str, str]:
    """Get authentication header for Calendly API."""
    token = CALENDLY_ACCESS_TOKEN if CALENDLY_ACCESS_TOKEN else CALENDLY_API_KEY
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

async def _make_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP request to Calendly API."""
    if DRY_RUN:
        return {"dry_run": True, "endpoint": endpoint, "method": method, "data": data}
    
    headers = _auth_header()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=method,
                url=f"{CALENDLY_BASE_URL}{endpoint}",
                headers=headers,
                json=data if data else None
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# OAuth Tools
@mcp.tool()
def calendly_get_oauth_url(redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
    """Generate OAuth authorization URL for user authentication."""
    if DRY_RUN:
        return _dry("get_oauth_url", redirect_uri=redirect_uri, state=state)
    
    try:
        if not CALENDLY_CLIENT_ID:
            return {"status": "error", "message": "CALENDLY_CLIENT_ID environment variable is required for OAuth"}
        
        params = {
            "client_id": CALENDLY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri
        }
        
        if state:
            params["state"] = state
        
        oauth_url = f"{CALENDLY_AUTH_URL}/oauth/authorize?{urlencode(params)}"
        
        return {
            "status": "success",
            "oauth_url": oauth_url,
            "redirect_uri": redirect_uri,
            "state": state
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate OAuth URL: {e}"}

@mcp.tool()
async def calendly_exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""
    if DRY_RUN:
        return _dry("exchange_code_for_tokens", code=code, redirect_uri=redirect_uri)
    
    try:
        if not CALENDLY_CLIENT_ID or not CALENDLY_CLIENT_SECRET:
            return {"status": "error", "message": "CALENDLY_CLIENT_ID and CALENDLY_CLIENT_SECRET required for OAuth"}
        
        # Create basic auth header
        credentials = base64.b64encode(f"{CALENDLY_CLIENT_ID}:{CALENDLY_CLIENT_SECRET}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CALENDLY_AUTH_URL}/oauth/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            token_data = response.json()
            
            return {
                "status": "success",
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in")
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to exchange code for tokens: {e}"}

@mcp.tool()
async def calendly_refresh_access_token(refresh_token: Optional[str] = None) -> Dict[str, Any]:
    """Refresh access token using refresh token."""
    if DRY_RUN:
        return _dry("refresh_access_token", refresh_token=refresh_token)
    
    try:
        if not CALENDLY_CLIENT_ID or not CALENDLY_CLIENT_SECRET:
            return {"status": "error", "message": "CALENDLY_CLIENT_ID and CALENDLY_CLIENT_SECRET required for OAuth"}
        
        token_to_use = refresh_token if refresh_token else CALENDLY_REFRESH_TOKEN
        if not token_to_use:
            return {"status": "error", "message": "No refresh token available"}
        
        # Create basic auth header
        credentials = base64.b64encode(f"{CALENDLY_CLIENT_ID}:{CALENDLY_CLIENT_SECRET}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token_to_use
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CALENDLY_AUTH_URL}/oauth/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            token_data = response.json()
            
            return {
                "status": "success",
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in")
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to refresh access token: {e}"}

# API Tools
@mcp.tool()
async def calendly_get_current_user() -> Dict[str, Any]:
    """Get information about the currently authenticated user."""
    if DRY_RUN:
        return _dry("get_current_user")
    
    try:
        data = await _make_request("/users/me")
        if "error" in data:
            return {"status": "error", "message": data["error"]}
        
        return {"status": "success", "user": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get current user: {e}"}

@mcp.tool()
async def calendly_list_events(
    user_uri: Optional[str] = None,
    organization_uri: Optional[str] = None,
    status: Optional[str] = None,
    max_start_time: Optional[str] = None,
    min_start_time: Optional[str] = None,
    count: int = 20
) -> Dict[str, Any]:
    """List scheduled events with optional filtering."""
    if DRY_RUN:
        return _dry("list_events", user_uri=user_uri, organization_uri=organization_uri,
                   status=status, max_start_time=max_start_time, min_start_time=min_start_time, count=count)
    
    try:
        params = {}
        
        # Use provided user_uri or fall back to config default
        effective_user_uri = user_uri if user_uri else CALENDLY_USER_URI
        if effective_user_uri:
            params["user"] = effective_user_uri
        
        if organization_uri:
            params["organization"] = organization_uri
        if status:
            params["status"] = status
        if max_start_time:
            params["max_start_time"] = max_start_time
        if min_start_time:
            params["min_start_time"] = min_start_time
        if count:
            params["count"] = str(count)
        
        query_string = urlencode(params) if params else ""
        endpoint = f"/scheduled_events?{query_string}" if query_string else "/scheduled_events"
        
        data = await _make_request(endpoint)
        if "error" in data:
            return {"status": "error", "message": data["error"]}
        
        events = data.get("collection", [])
        return {
            "status": "success",
            "events": events,
            "count": len(events),
            "pagination": data.get("pagination", {})
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list events: {e}"}

@mcp.tool()
async def calendly_get_event(event_uuid: str) -> Dict[str, Any]:
    """Get details of a specific event."""
    if DRY_RUN:
        return _dry("get_event", event_uuid=event_uuid)
    
    try:
        data = await _make_request(f"/scheduled_events/{event_uuid}")
        if "error" in data:
            return {"status": "error", "message": data["error"]}
        
        return {"status": "success", "event": data.get("resource", {})}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get event: {e}"}

@mcp.tool()
async def calendly_list_event_invitees(
    event_uuid: str,
    status: Optional[str] = None,
    email: Optional[str] = None,
    count: int = 20
) -> Dict[str, Any]:
    """List invitees for a specific event."""
    if DRY_RUN:
        return _dry("list_event_invitees", event_uuid=event_uuid, status=status, email=email, count=count)
    
    try:
        params = {}
        
        if status:
            params["status"] = status
        if email:
            params["email"] = email
        if count:
            params["count"] = str(count)
        
        query_string = urlencode(params) if params else ""
        endpoint = f"/scheduled_events/{event_uuid}/invitees"
        if query_string:
            endpoint += f"?{query_string}"
        
        data = await _make_request(endpoint)
        if "error" in data:
            return {"status": "error", "message": data["error"]}
        
        invitees = data.get("collection", [])
        return {
            "status": "success",
            "event_uuid": event_uuid,
            "invitees": invitees,
            "count": len(invitees),
            "pagination": data.get("pagination", {})
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list event invitees: {e}"}

@mcp.tool()
async def calendly_cancel_event(event_uuid: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Cancel a specific event."""
    if DRY_RUN:
        return _dry("cancel_event", event_uuid=event_uuid, reason=reason)
    
    try:
        data = {
            "reason": reason if reason else "Canceled via API"
        }
        
        result = await _make_request(f"/scheduled_events/{event_uuid}/cancellation", "POST", data)
        if "error" in result:
            return {"status": "error", "message": result["error"]}
        
        return {
            "status": "success",
            "event_uuid": event_uuid,
            "cancellation": result.get("resource", {}),
            "message": "Event canceled successfully"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to cancel event: {e}"}

@mcp.tool()
async def calendly_list_organization_memberships(
    user_uri: Optional[str] = None,
    organization_uri: Optional[str] = None,
    email: Optional[str] = None,
    count: int = 20
) -> Dict[str, Any]:
    """List organization memberships for the authenticated user."""
    if DRY_RUN:
        return _dry("list_organization_memberships", user_uri=user_uri, 
                   organization_uri=organization_uri, email=email, count=count)
    
    try:
        params = {}
        
        # Use provided user_uri or fall back to config default
        effective_user_uri = user_uri if user_uri else CALENDLY_USER_URI
        if effective_user_uri:
            params["user"] = effective_user_uri
        
        if organization_uri:
            params["organization"] = organization_uri
        if email:
            params["email"] = email
        if count:
            params["count"] = str(count)
        
        query_string = urlencode(params) if params else ""
        endpoint = f"/organization_memberships?{query_string}" if query_string else "/organization_memberships"
        
        data = await _make_request(endpoint)
        if "error" in data:
            return {"status": "error", "message": data["error"]}
        
        memberships = data.get("collection", [])
        return {
            "status": "success",
            "memberships": memberships,
            "count": len(memberships),
            "pagination": data.get("pagination", {})
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list organization memberships: {e}"}

if __name__ == "__main__":
    mcp.run()