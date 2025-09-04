#!/usr/bin/env python
"""
Salesforce MCP Server - Python FastMCP version
Provides Salesforce CRM API access with Model Control Protocol.
"""

import os
import json
from typing import Any, Dict, Optional, List
import httpx
from fastmcp import FastMCP

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# Required environment variables:
# SALESFORCE_ENV: 'User_Password' or 'OAuth'
# SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_TOKEN (for User_Password)
# SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_REFRESH_TOKEN (for OAuth)
# SALESFORCE_INSTANCE_URL - like https://yourdomain.my.salesforce.com

SALESFORCE_ENV = os.getenv("SALESFORCE_ENV", "User_Password").lower()
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SALESFORCE_TOKEN = os.getenv("SALESFORCE_TOKEN")
SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
SALESFORCE_REFRESH_TOKEN = os.getenv("SALESFORCE_REFRESH_TOKEN")
SALESFORCE_INSTANCE_URL = os.getenv("SALESFORCE_INSTANCE_URL")
API_VERSION = "v57.0"

if SALESFORCE_ENV not in ("user_password", "oauth"):
    raise ValueError("SALESFORCE_ENV must be either 'User_Password' or 'OAuth'")

if SALESFORCE_ENV == "user_password":
    if not all([SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_TOKEN, SALESFORCE_INSTANCE_URL]):
        raise RuntimeError("Set SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_TOKEN, SALESFORCE_INSTANCE_URL for User_Password auth")
else:
    if not all([SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_REFRESH_TOKEN, SALESFORCE_INSTANCE_URL]):
        raise RuntimeError("Set SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_REFRESH_TOKEN, SALESFORCE_INSTANCE_URL for OAuth auth")


mcp = FastMCP("salesforce")


def _debug_log(message):
    if DRY_RUN:
        logging.info(f"[DRY_RUN] {message}")


async def _get_oauth_token():
    url = f"https://login.salesforce.com/services/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": SALESFORCE_CLIENT_ID,
        "client_secret": SALESFORCE_CLIENT_SECRET,
        "refresh_token": SALESFORCE_REFRESH_TOKEN,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        token_info = resp.json()
        return token_info["access_token"]


async def _get_auth_header():
    if SALESFORCE_ENV == "user_password":
        # Build basic auth header with username, password+token
        # NOTE: Salesforce REST API expects OAuth tokens, so user-password flow normally not for REST
        # For simplicity, treat as error here
        raise NotImplementedError("User-password auth not implemented in this MCP server.")
    else:
        token = await _get_oauth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return headers


async def _request(method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None):
    if DRY_RUN:
        return {"dry_run": True, "endpoint": endpoint, "method": method, "params": params, "json": json_data}
    url = f"{SALESFORCE_INSTANCE_URL}/services/data/{API_VERSION}/{endpoint}"
    headers = await _get_auth_header()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=headers, params=params, json=json_data)
        resp.raise_for_status()
        return resp.json()


@mcp.tool
async def salesforce_list_modules() -> Dict[str, Any]:
    """List available Salesforce modules (objects)."""
    return await _request("GET", "sobjects")


@mcp.tool
async def salesforce_describe_object(object_api_name: str) -> Dict[str, Any]:
    """Get detailed schema for a Salesforce object."""
    return await _request("GET", f"sobjects/{object_api_name}/describe")


@mcp.tool
async def salesforce_query(query: str) -> Dict[str, Any]:
    """Run SOQL query on Salesforce."""
    params = {"q": query}
    return await _request("GET", "query", params=params)


@mcp.tool
async def salesforce_aggregate_query(aggregate_soql: str) -> Dict[str, Any]:
    """Run aggregate SOQL query."""
    params = {"q": aggregate_soql}
    return await _request("GET", "query", params=params)


@mcp.tool
async def salesforce_get_record(object_api_name: str, record_id: str) -> Dict[str, Any]:
    """Get a single Salesforce record by id."""
    return await _request("GET", f"sobjects/{object_api_name}/{record_id}")


@mcp.tool
async def salesforce_create_record(object_api_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Salesforce record."""
    return await _request("POST", f"sobjects/{object_api_name}", json_data=data)


@mcp.tool
async def salesforce_update_record(object_api_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing Salesforce record."""
    return await _request("PATCH", f"sobjects/{object_api_name}/{record_id}", json_data=data)


@mcp.tool
async def salesforce_delete_record(object_api_name: str, record_id: str) -> Dict[str, Any]:
    """Delete Salesforce record."""
    return await _request("DELETE", f"sobjects/{object_api_name}/{record_id}")


if __name__ == "__main__":
    mcp.run()
