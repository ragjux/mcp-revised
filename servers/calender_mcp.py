#!/usr/bin/env python3
"""
Google Calendar MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Calendar operations.
"""

import os
import json
import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"calendar_{name}", "args": kwargs}

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar'
]

TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', '')

if not CREDENTIALS_PATH and not SERVICE_ACCOUNT_PATH:
    raise RuntimeError("Set CREDENTIALS_PATH or SERVICE_ACCOUNT_PATH environment variable")

mcp = FastMCP("Google Calendar MCP (native)")

def _get_calendar_service():
    """Get authenticated Calendar service."""
    creds = None
    
    # Try service account first
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH, scopes=SCOPES
        )
    else:
        # OAuth flow
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as token:
                creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

@mcp.tool()
def calendar_list_events(calendar_id: str = 'primary', max_results: int = 10) -> Dict[str, Any]:
    """List upcoming calendar events."""
    if DRY_RUN:
        return _dry("list_events", calendar_id=calendar_id, max_results=max_results)
    
    try:
        service = _get_calendar_service()
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({
                "id": event['id'],
                "summary": event.get('summary', 'No title'),
                "start": start,
                "end": event['end'].get('dateTime', event['end'].get('date'))
            })
        
        return {"events": event_list, "count": len(event_list)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list calendar events: {e}"}

@mcp.tool()
def calendar_create_event(
    summary: str, 
    start_time: str, 
    end_time: str, 
    description: str = "",
    calendar_id: str = 'primary'
) -> Dict[str, Any]:
    """Create a new calendar event."""
    if DRY_RUN:
        return _dry("create_event", summary=summary, start_time=start_time, 
                   end_time=end_time, description=description, calendar_id=calendar_id)
    
    try:
        service = _get_calendar_service()
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        
        result = service.events().insert(
            calendarId=calendar_id, body=event
        ).execute()
        
        return {"status": "success", "event_id": result.get('id')}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create calendar event: {e}"}

@mcp.tool()
def calendar_list_calendars() -> Dict[str, Any]:
    """List all accessible calendars."""
    if DRY_RUN:
        return _dry("list_calendars")
    
    try:
        service = _get_calendar_service()
        
        calendars = service.calendarList().list().execute()
        calendar_list = calendars.get('items', [])
        
        calendars_data = []
        for calendar in calendar_list:
            calendars_data.append({
                "id": calendar['id'],
                "summary": calendar.get('summary', 'No title'),
                "primary": calendar.get('primary', False),
                "access_role": calendar.get('accessRole', 'Unknown')
            })
        
        return {"calendars": calendars_data, "count": len(calendars_data)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list calendars: {e}"}

@mcp.tool()
def calendar_modify_event(
    event_id: str,
    summary: str = None,
    description: str = None,
    start_time: str = None,
    end_time: str = None,
    calendar_id: str = 'primary'
) -> Dict[str, Any]:
    """Modify an existing calendar event."""
    if DRY_RUN:
        return _dry("modify_event", event_id=event_id, summary=summary,
                   description=description, start_time=start_time, 
                   end_time=end_time, calendar_id=calendar_id)
    
    try:
        service = _get_calendar_service()
        
        # Get existing event
        event = service.events().get(
            calendarId=calendar_id, eventId=event_id
        ).execute()
        
        # Update fields if provided
        if summary:
            event['summary'] = summary
        if description is not None:
            event['description'] = description
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time
        
        # Update event
        result = service.events().update(
            calendarId=calendar_id, eventId=event_id, body=event
        ).execute()
        
        return {"status": "success", "event_id": result.get('id')}
    except Exception as e:
        return {"status": "error", "message": f"Failed to modify calendar event: {e}"}

@mcp.tool()
def calendar_delete_event(event_id: str, calendar_id: str = 'primary') -> Dict[str, Any]:
    """Delete a calendar event."""
    if DRY_RUN:
        return _dry("delete_event", event_id=event_id, calendar_id=calendar_id)
    
    try:
        service = _get_calendar_service()
        
        service.events().delete(
            calendarId=calendar_id, eventId=event_id
        ).execute()
        
        return {"status": "success", "message": "Event deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete calendar event: {e}"}

if __name__ == "__main__":
    mcp.run()