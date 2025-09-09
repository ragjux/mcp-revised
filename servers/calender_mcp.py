#!/usr/bin/env python3
"""
Google Calendar MCP Server - Token-only authentication
A Model Context Protocol (MCP) server for Google Calendar operations.
"""

import os
import json
import httpx
import datetime
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
    return {"dry_run": True, "tool": f"calendar_{name}", "args": kwargs}

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GCALENDAR_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GCALENDAR_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GCALENDAR_ACCESS_TOKEN and GCALENDAR_REFRESH_TOKEN environment variables")

CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"

mcp = FastMCP("Google Calendar MCP (Token-only)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

@mcp.tool()
def calendar_list_events(calendar_id: str = 'primary', max_results: int = 10) -> Dict[str, Any]:
    """List events from a calendar."""
    if DRY_RUN:
        return _dry("calendar_list_events", calendar_id=calendar_id, max_results=max_results)
    
    params = {
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CALENDAR_BASE}/calendars/{calendar_id}/events", 
                 headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_get_event(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Get a specific event by ID."""
    if DRY_RUN:
        return _dry("calendar_get_event", calendar_id=calendar_id, event_id=event_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CALENDAR_BASE}/calendars/{calendar_id}/events/{event_id}", 
                 headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_create_event(calendar_id: str, summary: str, start_time: str, 
                         end_time: str, description: Optional[str] = None,
                         location: Optional[str] = None) -> Dict[str, Any]:
    """Create a new event."""
    if DRY_RUN:
        return _dry("calendar_create_event", calendar_id=calendar_id, summary=summary, 
                   start_time=start_time, end_time=end_time, description=description, location=location)
    
    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        }
    }
    
    if description:
        event["description"] = description
    if location:
        event["location"] = location
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CALENDAR_BASE}/calendars/{calendar_id}/events", 
                  headers=_auth_header(), json=event)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_update_event(calendar_id: str, event_id: str, summary: Optional[str] = None,
                         start_time: Optional[str] = None, end_time: Optional[str] = None,
                         description: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing event."""
    if DRY_RUN:
        return _dry("calendar_update_event", calendar_id=calendar_id, event_id=event_id, 
                   summary=summary, start_time=start_time, end_time=end_time, 
                   description=description, location=location)
    
    # First get the existing event
    existing_event = calendar_get_event(calendar_id, event_id)
    
    # Update fields if provided
    if summary:
        existing_event["summary"] = summary
    if start_time:
        existing_event["start"] = {
            "dateTime": start_time,
            "timeZone": "UTC"
        }
    if end_time:
        existing_event["end"] = {
            "dateTime": end_time,
            "timeZone": "UTC"
        }
    if description:
        existing_event["description"] = description
    if location:
        existing_event["location"] = location
    
    with httpx.Client(timeout=30) as c:
        r = c.put(f"{CALENDAR_BASE}/calendars/{calendar_id}/events/{event_id}", 
                 headers=_auth_header(), json=existing_event)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_delete_event(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Delete an event."""
    if DRY_RUN:
        return _dry("calendar_delete_event", calendar_id=calendar_id, event_id=event_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.delete(f"{CALENDAR_BASE}/calendars/{calendar_id}/events/{event_id}", 
                    headers=_auth_header())
        r.raise_for_status()
        return {"success": True, "event_id": event_id}

@mcp.tool()
def calendar_list_calendars() -> Dict[str, Any]:
    """List all calendars."""
    if DRY_RUN:
        return _dry("calendar_list_calendars")
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CALENDAR_BASE}/users/me/calendarList", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_get_calendar(calendar_id: str) -> Dict[str, Any]:
    """Get calendar details."""
    if DRY_RUN:
        return _dry("calendar_get_calendar", calendar_id=calendar_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CALENDAR_BASE}/calendars/{calendar_id}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_create_calendar(summary: str, description: Optional[str] = None, 
                           time_zone: str = "UTC") -> Dict[str, Any]:
    """Create a new calendar."""
    if DRY_RUN:
        return _dry("calendar_create_calendar", summary=summary, description=description, time_zone=time_zone)
    
    calendar = {
        "summary": summary,
        "timeZone": time_zone
    }
    
    if description:
        calendar["description"] = description
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CALENDAR_BASE}/calendars", headers=_auth_header(), json=calendar)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_search_events(calendar_id: str, query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for events in a calendar."""
    if DRY_RUN:
        return _dry("calendar_search_events", calendar_id=calendar_id, query=query, max_results=max_results)
    
    params = {
        "q": query,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{CALENDAR_BASE}/calendars/{calendar_id}/events", 
                 headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def calendar_get_free_busy(calendar_ids: List[str], time_min: str, time_max: str) -> Dict[str, Any]:
    """Get free/busy information for calendars."""
    if DRY_RUN:
        return _dry("calendar_get_free_busy", calendar_ids=calendar_ids, time_min=time_min, time_max=time_max)
    
    payload = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cal_id} for cal_id in calendar_ids]
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{CALENDAR_BASE}/freeBusy", headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
