#!/usr/bin/env python3
"""
Outlook MCP Server (Microsoft Graph) - FastMCP version. auth helpers + email + calendar tools.
"""

import os
import time
from typing import Any, Dict, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging
import urllib.parse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "1"

AUTHORITY = os.getenv("MS_AUTHORITY", "https://login.microsoftonline.com")
TENANT = os.getenv("MS_TENANT_ID", "common")
CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://localhost:3333/auth/callback")
SCOPES = os.getenv("MS_SCOPES", "offline_access User.Read Mail.Read Mail.Send Calendars.Read Calendars.ReadWrite Contacts.Read")

TOKEN_URL = f"{AUTHORITY}/{TENANT}/oauth2/v2.0/token"
AUTH_URL = f"{AUTHORITY}/{TENANT}/oauth2/v2.0/authorize"
GRAPH = "https://graph.microsoft.com/v1.0"

ACCESS_TOKEN = os.getenv("MS_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("MS_REFRESH_TOKEN", "")
EXPIRY = float(os.getenv("MS_TOKEN_EXPIRY", "0"))

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Set MS_CLIENT_ID and MS_CLIENT_SECRET")

mcp = FastMCP("Outlook MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"outlook_{name}", "args": kwargs}

def _auth_header(t: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {t}", "Accept": "application/json", "Content-Type": "application/json"}

async def _token() -> str:
    """Return a valid access token, refreshing if necessary."""
    global ACCESS_TOKEN, REFRESH_TOKEN, EXPIRY
    now = time.time()
    if ACCESS_TOKEN and now < EXPIRY - 60:
        return ACCESS_TOKEN
    if not REFRESH_TOKEN:
        raise RuntimeError("No tokens available. Call outlook_get_auth_url then outlook_exchange_code.")
    async with httpx.AsyncClient(timeout=30) as client:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "scope": SCOPES
        }
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        tok = r.json()
        ACCESS_TOKEN = tok.get("access_token", "")
        REFRESH_TOKEN = tok.get("refresh_token", REFRESH_TOKEN)
        EXPIRY = time.time() + int(tok.get("expires_in", 3600))
        return ACCESS_TOKEN

# ---------- Auth helpers ---------- [2]

@mcp.tool()
def outlook_get_auth_url(state: Optional[str] = None) -> Dict[str, Any]:
    """Construct the Authorization URL for OAuth 2.0 authorization code flow."""
    st = state or str(int(time.time()))
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": SCOPES,
        "state": st
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url, "state": st}

@mcp.tool()
async def outlook_exchange_code(code: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens."""
    global ACCESS_TOKEN, REFRESH_TOKEN, EXPIRY
    if DRY:
        return _dry("exchange_code", code=code)
    async with httpx.AsyncClient(timeout=30) as client:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        tok = r.json()
        ACCESS_TOKEN = tok.get("access_token", "")
        REFRESH_TOKEN = tok.get("refresh_token", "")
        EXPIRY = time.time() + int(tok.get("expires_in", 3600))
        return {"access_token": ACCESS_TOKEN, "refresh_token": REFRESH_TOKEN, "expires_in": tok.get("expires_in")}

# ---------- Email tools ---------- [2][6]

@mcp.tool()
async def outlook_list_emails(folder: str = "inbox", top: int = 25, select: str = "subject,from,receivedDateTime", orderby: str = "receivedDateTime DESC", filter: Optional[str] = None) -> Dict[str, Any]:
    """List emails from a folder using OData params."""
    if DRY:
        return _dry("list_emails", folder=folder, top=top, select=select, orderby=orderby, filter=filter)
    token = await _token()
    params: Dict[str, str] = {"$top": str(top), "$select": select, "$orderby": orderby}
    if filter:
        params["$filter"] = filter
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{GRAPH}/me/mailFolders/{folder}/messages", headers=_auth_header(token), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def outlook_search_emails(query: str, top: int = 25, select: str = "subject,from,receivedDateTime") -> Dict[str, Any]:
    """Search emails using the search header/parameter; uses /messages with $search."""
    if DRY:
        return _dry("search_emails", query=query, top=top, select=select)
    token = await _token()
    params = {"$search": f"\"{query}\"", "$top": str(top), "$select": select}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{GRAPH}/me/messages", headers={**_auth_header(token), "ConsistencyLevel": "eventual"}, params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def outlook_read_email(message_id: str) -> Dict[str, Any]:
    """Read a single email by message id."""
    if DRY:
        return _dry("read_email", message_id=message_id)
    token = await _token()
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{GRAPH}/me/messages/{message_id}", headers=_auth_header(token))
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def outlook_send_email(subject: str, body_html: str, to_recipients: str) -> Dict[str, Any]:
    """Send an email. to_recipients is a comma-separated list of addresses."""
    if DRY:
        return _dry("send_email", subject=subject, to_recipients=to_recipients)
    token = await _token()
    recipients = [{"emailAddress": {"address": a.strip()}} for a in to_recipients.split(",") if a.strip()]
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_html},
            "toRecipients": recipients
        },
        "saveToSentItems": True
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/sendMail", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return {"status": "success"}

# ---------- Calendar tools ---------- [2]

@mcp.tool()
async def outlook_list_events(start_datetime: Optional[str] = None, end_datetime: Optional[str] = None, top: int = 25, select: str = "subject,organizer,start,end,location") -> Dict[str, Any]:
    """List events in the primary calendar; optionally bound by start/end in ISO 8601 UTC."""
    if DRY:
        return _dry("list_events", start_datetime=start_datetime, end_datetime=end_datetime, top=top, select=select)
    token = await _token()
    params: Dict[str, str] = {"$top": str(top), "$select": select, "$orderby": "start/dateTime"}
    if start_datetime and end_datetime:
        params["startDateTime"] = start_datetime
        params["endDateTime"] = end_datetime
        url = f"{GRAPH}/me/calendarView"
    else:
        url = f"{GRAPH}/me/events"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=_auth_header(token), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def outlook_create_event(subject: str, start_datetime: str, end_datetime: str, timezone: str = "UTC",
                               body_html: Optional[str] = None, attendees_csv: Optional[str] = None, location_display_name: Optional[str] = None) -> Dict[str, Any]:
    """Create an event in the primary calendar."""
    if DRY:
        return _dry("create_event", subject=subject, start_datetime=start_datetime, end_datetime=end_datetime)
    token = await _token()
    attendees = [{"emailAddress": {"address": a.strip()}, "type": "required"} for a in (attendees_csv or "").split(",") if a.strip()]
    payload = {
        "subject": subject,
        "start": {"dateTime": start_datetime, "timeZone": timezone},
        "end": {"dateTime": end_datetime, "timeZone": timezone}
    }
    if body_html: payload["body"] = {"contentType": "HTML", "content": body_html}
    if attendees: payload["attendees"] = attendees
    if location_display_name: payload["location"] = {"displayName": location_display_name}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/events", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def outlook_delete_event(event_id: str) -> Dict[str, Any]:
    """Delete an event."""
    if DRY:
        return _dry("delete_event", event_id=event_id)
    token = await _token()
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.delete(f"{GRAPH}/me/events/{event_id}", headers=_auth_header(token))
        r.raise_for_status()
        return {"status": "success"}

@mcp.tool()
async def outlook_cancel_event(event_id: str, comment: Optional[str] = None) -> Dict[str, Any]:
    """Cancel an event (sends cancellation message)."""
    if DRY:
        return _dry("cancel_event", event_id=event_id, comment=comment)
    token = await _token()
    payload = {"Comment": comment or ""}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/events/{event_id}/cancel", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return {"status": "success"}

@mcp.tool()
async def outlook_accept_event(event_id: str, comment: Optional[str] = None, sendResponse: bool = True) -> Dict[str, Any]:
    """Accept an event invitation."""
    if DRY:
        return _dry("accept_event", event_id=event_id)
    token = await _token()
    payload = {"comment": comment or "", "sendResponse": sendResponse}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/events/{event_id}/accept", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return {"status": "success"}

@mcp.tool()
async def outlook_tentative_event(event_id: str, comment: Optional[str] = None, sendResponse: bool = True) -> Dict[str, Any]:
    """Tentatively accept an event invitation."""
    if DRY:
        return _dry("tentative_event", event_id=event_id)
    token = await _token()
    payload = {"comment": comment or "", "sendResponse": sendResponse}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/events/{event_id}/tentativelyAccept", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return {"status": "success"}

@mcp.tool()
async def outlook_decline_event(event_id: str, comment: Optional[str] = None, sendResponse: bool = True) -> Dict[str, Any]:
    """Decline an event invitation."""
    if DRY:
        return _dry("decline_event", event_id=event_id)
    token = await _token()
    payload = {"comment": comment or "", "sendResponse": sendResponse}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{GRAPH}/me/events/{event_id}/decline", headers=_auth_header(token), json=payload)
        r.raise_for_status()
        return {"status": "success"}

if __name__ == "__main__":
    mcp.run()
