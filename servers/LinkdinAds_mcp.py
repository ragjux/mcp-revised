#!/usr/bin/env python3
"""
LinkedIn MCP Server - FastMCP version
Implements two tools: search_people and get_profile, using LinkedIn REST APIs.
OAuth 2.0 (3-legged) member authorization is supported.
"""

import os
import time
import json
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging
import urllib.parse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"linkedin_{name}", "args": kwargs}

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "")
SCOPES = os.getenv("LINKEDIN_SCOPES", "profile email")

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("LINKEDIN_REFRESH_TOKEN", "")
TOKEN_EXPIRY = float(os.getenv("LINKEDIN_TOKEN_EXPIRY", "0"))

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
API_BASE = "https://api.linkedin.com/v2"

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET")

mcp = FastMCP("LinkedIn MCP (native)")

async def _token() -> str:
    global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY
    now = time.time()
    if ACCESS_TOKEN and now < TOKEN_EXPIRY - 60:
        return ACCESS_TOKEN
    if REFRESH_TOKEN:
        # Try refresh (only for apps/products supporting refresh)
        async with httpx.AsyncClient(timeout=30) as client:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            }
            r = await client.post(TOKEN_URL, data=data)
            r.raise_for_status()
            tok = r.json()
            ACCESS_TOKEN = tok.get("access_token", "")
            expires_in = int(tok.get("expires_in", 3600))
            TOKEN_EXPIRY = now + expires_in
            return ACCESS_TOKEN
    # If no refresh token, signal need for interactive code exchange
    raise RuntimeError("No valid access token. Use linkedin_get_auth_url and linkedin_exchange_code to authorize.")

def _auth_header(t: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {t}", "X-Restli-Protocol-Version": "2.0.0"}

@mcp.tool()
def linkedin_get_auth_url(state: Optional[str] = None) -> Dict[str, Any]:
    """Generate the OAuth 2.0 authorization URL for user consent."""
    st = state or str(int(time.time()))
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": st
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url, "state": st}

@mcp.tool()
async def linkedin_exchange_code(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access (and optionally refresh) token."""
    global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY
    if DRY_RUN:
        return _dry("exchange_code", code=code)
    async with httpx.AsyncClient(timeout=30) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        tok = r.json()
        ACCESS_TOKEN = tok.get("access_token", "")
        REFRESH_TOKEN = tok.get("refresh_token", "") or REFRESH_TOKEN
        TOKEN_EXPIRY = time.time() + int(tok.get("expires_in", 3600))
        return {"access_token": ACCESS_TOKEN, "refresh_token": REFRESH_TOKEN, "expires_in": tok.get("expires_in")}

# -------- Tools --------

@mcp.tool()
async def linkedin_get_profile(publicId: Optional[str] = None, urnId: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve profile information.
    - Without identifiers, returns the authorized member's own profile (/me).
    - With an identifier, requires product approval for People/Profile APIs.
    """
    if DRY_RUN:
        return _dry("get_profile", publicId=publicId, urnId=urnId)
    token = await _token()
    async with httpx.AsyncClient(timeout=60) as client:
        if not publicId and not urnId:
            # Basic member profile (own) [4]
            r = await client.get(f"{API_BASE}/me", headers=_auth_header(token))
            r.raise_for_status()
            return r.json()
        # Profile APIs for other members are product-gated; endpoint patterns vary by product access.
        # Example (subject to approval): /people/(urn:li:person:{id})
        target = urnId or publicId
        r = await client.get(f"{API_BASE}/people/(id:{urllib.parse.quote(target)})", headers=_auth_header(token))
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def linkedin_search_people(keywords: Optional[str] = None,
                                 currentCompany: Optional[List[str]] = None,
                                 industries: Optional[List[str]] = None,
                                 location: Optional[str] = None,
                                 start: int = 0, count: int = 25) -> Dict[str, Any]:
    """
    Search for LinkedIn profiles (requires appropriate product access/permissions).
    Parameters are mapped to query string where applicable; actual availability depends on approved APIs.
    """
    if DRY_RUN:
        return _dry("search_people", keywords=keywords, currentCompany=currentCompany, industries=industries, location=location, start=start, count=count)
    token = await _token()
    params: Dict[str, Any] = {"start": start, "count": count}
    if keywords: params["q"] = keywords
    # The exact parameters for people search are product-gated; placeholders shown.
    if location: params["location"] = location
    if currentCompany: params["currentCompany"] = ",".join(currentCompany)
    if industries: params["industries"] = ",".join(industries)
    async with httpx.AsyncClient(timeout=60) as client:
        # Endpoint path is illustrative; actual path depends on product access granted by LinkedIn. [3][4]
        r = await client.get(f"{API_BASE}/peopleSearch", headers=_auth_header(token), params=params)
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
