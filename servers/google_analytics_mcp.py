#!/usr/bin/env python3
"""
Google Analytics MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Analytics operations.
"""

import os
from typing import Any, Dict, Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
TOKEN_PATH = os.getenv("GANALYTICS_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GANALYTICS_CREDENTIALS_PATH", "credentials.json")

if not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
    raise RuntimeError("Provide a valid GANALYTICS_CREDENTIALS_PATH to your OAuth client secrets JSON file")

mcp = FastMCP("Google Analytics MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"analytics_{name}", "args": kwargs}

def _get_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return creds

def _build_analytics_service():
    creds = _get_credentials()
    return build("analyticsadmin", "v1alpha", credentials=creds)

def _build_data_service():
    creds = _get_credentials()
    return build("analyticsdata", "v1beta", credentials=creds)

@mcp.tool()
async def analytics_get_account_summaries() -> Dict[str, Any]:
    """Retrieve information about the user's Google Analytics accounts and properties."""
    if DRY_RUN:
        return _dry("get_account_summaries")
    try:
        service = _build_analytics_service()
        response = service.accounts().list().execute()
        accounts = response.get("accounts", [])
        return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get account summaries: {e}"}

@mcp.tool()
async def analytics_get_property_details(property_id: str) -> Dict[str, Any]:
    """Returns details about a specific Google Analytics property."""
    if DRY_RUN:
        return _dry("get_property_details", property_id=property_id)
    try:
        service = _build_analytics_service()
        response = service.properties().get(name=property_id).execute()
        return {"property": response}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get property details: {e}"}

@mcp.tool()
async def analytics_list_google_ads_links(property_id: str) -> Dict[str, Any]:
    """Returns a list of links to Google Ads accounts for a property."""
    if DRY_RUN:
        return _dry("list_google_ads_links", property_id=property_id)
    try:
        service = _build_analytics_service()
        response = service.properties().googleAdsLinks().list(parent=property_id).execute()
        links = response.get("googleAdsLinks", [])
        return {"googleAdsLinks": links, "count": len(links)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list Google Ads links: {e}"}

@mcp.tool()
async def analytics_run_report(property_id: str, 
                               dimensions: Optional[list] = None, 
                               metrics: Optional[list] = None,
                               date_ranges: Optional[list] = None,
                               limit: int = 10) -> Dict[str, Any]:
    """
    Runs a Google Analytics report using the Data API.
    - property_id: Google Analytics property resource name (e.g. properties/1234)
    - dimensions: List of dimension objects [{'name': 'city'}]
    - metrics: List of metric objects [{'name': 'activeUsers'}]
    - date_ranges: List of date range objects [{'startDate': '2023-01-01', 'endDate': 'today'}]
    - limit: Number of rows to return
    """
    if DRY_RUN:
        return _dry("run_report", property_id=property_id, dimensions=dimensions, metrics=metrics, date_ranges=date_ranges, limit=limit)
    try:
        service = _build_data_service()
        body = {
            "dimensions": dimensions or [],
            "metrics": metrics or [],
            "dateRanges": date_ranges or [{"startDate": "2023-01-01", "endDate": "today"}],
            "limit": limit
        }
        response = service.properties().runReport(property=property_id, body=body).execute()
        return {"report": response}
    except Exception as e:
        return {"status": "error", "message": f"Failed to run report: {e}"}

@mcp.tool()
async def analytics_get_custom_dimensions_and_metrics(property_id: str) -> Dict[str, Any]:
    """Retrieves custom dimensions and metrics for a specific property."""
    if DRY_RUN:
        return _dry("get_custom_dimensions_and_metrics", property_id=property_id)
    try:
        service = _build_analytics_service()
        dimensions_resp = service.properties().customDimensions().list(parent=property_id).execute()
        metrics_resp = service.properties().customMetrics().list(parent=property_id).execute()
        return {
            "customDimensions": dimensions_resp.get("customDimensions", []),
            "customMetrics": metrics_resp.get("customMetrics", [])
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get custom dimensions and metrics: {e}"}

@mcp.tool()
async def analytics_run_realtime_report(property_id: str, 
                                        dimensions: Optional[list] = None,
                                        metrics: Optional[list] = None) -> Dict[str, Any]:
    """
    Runs a Google Analytics realtime report using the Data API.
    """
    if DRY_RUN:
        return _dry("run_realtime_report", property_id=property_id, dimensions=dimensions, metrics=metrics)
    try:
        service = _build_data_service()
        body = {
            "dimensions": dimensions or [],
            "metrics": metrics or []
        }
        response = service.properties().runRealtimeReport(property=property_id, body=body).execute()
        return {"realtimeReport": response}
    except Exception as e:
        return {"status": "error", "message": f"Failed to run realtime report: {e}"}

if __name__ == "__main__":
    mcp.run()
