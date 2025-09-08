#!/usr/bin/env python3
"""
QuickBooks Online MCP Server - FastMCP version
"""

import os
import time
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"qbo_{name}", "args": kwargs}

QBO_CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID", "")
QBO_CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET", "")
QBO_REFRESH_TOKEN = os.getenv("QUICKBOOKS_REFRESH_TOKEN", "")
QBO_COMPANY_ID = os.getenv("QUICKBOOKS_COMPANY_ID", "")
QBO_ENV = os.getenv("QUICKBOOKS_ENV", "sandbox").lower()  # sandbox | production

if not (QBO_CLIENT_ID and QBO_CLIENT_SECRET and QBO_REFRESH_TOKEN and QBO_COMPANY_ID):
    raise RuntimeError("Set QUICKBOOKS_CLIENT_ID, QUICKBOOKS_CLIENT_SECRET, QUICKBOOKS_REFRESH_TOKEN, QUICKBOOKS_COMPANY_ID")

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
if QBO_ENV not in ("sandbox", "production"):
    raise RuntimeError("QUICKBOOKS_ENV must be 'sandbox' or 'production'")

BASE_URL = "https://sandbox-quickbooks.api.intuit.com" if QBO_ENV == "sandbox" else "https://quickbooks.api.intuit.com"

mcp = FastMCP("QuickBooks MCP (native)")

_access_token: Optional[str] = None
_expiry_ts: float = 0

async def _get_access_token() -> str:
    global _access_token, _expiry_ts
    now = time.time()
    if _access_token and now < _expiry_ts - 60:
        return _access_token
    auth = (QBO_CLIENT_ID, QBO_CLIENT_SECRET)
    data = {
        "grant_type": "refresh_token",
        "refresh_token": QBO_REFRESH_TOKEN,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(TOKEN_URL, data=data, auth=auth)
        resp.raise_for_status()
        tok = resp.json()
        _access_token = tok.get("access_token")
        expires_in = tok.get("expires_in", 3600)
        _expiry_ts = now + int(expires_in)
        return _access_token

async def _qbo_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("GET", path=path, params=params)
    token = await _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/v3/company/{QBO_COMPANY_ID}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

async def _qbo_post(path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("POST", path=path, json=json_body)
    token = await _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/v3/company/{QBO_COMPANY_ID}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=json_body)
        resp.raise_for_status()
        return resp.json()

# -------------------- Query endpoints --------------------

@mcp.tool()
async def qbo_query(select: str) -> Dict[str, Any]:
    """Run a SQL-like QBO query, e.g., 'select * from Account'. """
    if DRY_RUN:
        return _dry("query", select=select)
    params = {"query": select, "minorversion": "70"}
    # Query endpoint
    return await _qbo_get("/query", params=params)

@mcp.tool()
async def qbo_get_accounts() -> Dict[str, Any]:
    """Get all Accounts."""
    if DRY_RUN:
        return _dry("get_accounts")
    return await qbo_query("select * from Account")

@mcp.tool()
async def qbo_get_customers() -> Dict[str, Any]:
    """Get all Customers."""
    if DRY_RUN:
        return _dry("get_customers")
    return await qbo_query("select * from Customer")

@mcp.tool()
async def qbo_get_bills_after(date_yyyy_mm_dd: str) -> Dict[str, Any]:
    """Get Bills created after a date (YYYY-MM-DD)."""
    if DRY_RUN:
        return _dry("get_bills_after", date=date_yyyy_mm_dd)
    q = f"select * from Bill where MetaData.CreateTime > '{date_yyyy_mm_dd}'"
    return await qbo_query(q)

# -------------------- Create/Update examples --------------------

@mcp.tool()
async def qbo_create_customer(DisplayName: str, PrimaryEmailAddr: Optional[str] = None, PrimaryPhone: Optional[str] = None) -> Dict[str, Any]:
    """Create a Customer (minimal fields)."""
    if DRY_RUN:
        return _dry("create_customer", DisplayName=DisplayName, PrimaryEmailAddr=PrimaryEmailAddr, PrimaryPhone=PrimaryPhone)
    body: Dict[str, Any] = {
        "Customer": {
            "DisplayName": DisplayName
        }
    }
    if PrimaryEmailAddr:
        body["Customer"]["PrimaryEmailAddr"] = {"Address": PrimaryEmailAddr}
    if PrimaryPhone:
        body["Customer"]["PrimaryPhone"] = {"FreeFormNumber": PrimaryPhone}
    return await _qbo_post("/customer", body)

@mcp.tool()
async def qbo_update_customer(Id: str, SyncToken: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update a Customer by Id/SyncToken; fields merged into payload."""
    if DRY_RUN:
        return _dry("update_customer", Id=Id, SyncToken=SyncToken, fields=fields)
    payload = {
        "Customer": {
            "Id": Id,
            "SyncToken": SyncToken,
            **fields
        }
    }
    return await _qbo_post("/customer", payload)

if __name__ == "__main__":
    mcp.run()
