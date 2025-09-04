#!/usr/bin/env python3
"""
Google Ads MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Ads operations.
"""

import os
import json
from typing import Any, Dict, Optional
from fastmcp import FastMCP
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# OAuth and Service Account scopes for Google Ads API
SCOPES = ["https://www.googleapis.com/auth/adwords"]

TOKEN_PATH = os.getenv("GOOGLE_ADS_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GOOGLE_ADS_CREDENTIALS_PATH", "credentials.json")
AUTH_TYPE = os.getenv("GOOGLE_ADS_AUTH_TYPE", "service_account")
DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", None)

if not DEVELOPER_TOKEN:
    raise RuntimeError("Set GOOGLE_ADS_DEVELOPER_TOKEN environment variable")

mcp = FastMCP("Google Ads MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"googleads_{name}", "args": kwargs}

def _get_credentials():
    creds = None
    if AUTH_TYPE == "service_account":
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )
    elif AUTH_TYPE == "oauth":
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
    else:
        raise RuntimeError(f"Unsupported auth type: {AUTH_TYPE}")
    return creds

def _build_service():
    creds = _get_credentials()
    return build('googleads', 'v14', credentials=creds)

def _get_headers():
    headers = {
        "developer-token": DEVELOPER_TOKEN
    }
    if LOGIN_CUSTOMER_ID:
        headers["login-customer-id"] = LOGIN_CUSTOMER_ID
    return headers

@mcp.tool()
def googleads_list_accounts() -> Dict[str, Any]:
    """List all Google Ads accounts."""
    if DRY_RUN:
        return _dry("list_accounts")
    try:
        service = _build_service()
        customer_service = service.customers()
        response = customer_service.list_accessible_customers().execute()
        accounts = response.get('resourceNames', [])
        return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def googleads_execute_gaql_query(account_id: str, query: str) -> Dict[str, Any]:
    """Run a Google Ads Query Language (GAQL) query."""
    if DRY_RUN:
        return _dry("execute_gaql_query", account_id=account_id, query=query)
    try:
        service = _build_service()
        ga_service = service.googleAds()
        request = ga_service.search_stream(
            customerId=account_id,
            body={"query": query},
            headers=_get_headers()
        )
        results = []
        for batch in request:
            for row in batch.results:
                results.append(json.loads(str(row)))
        return {"results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def googleads_get_campaign_performance(account_id: str,
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get campaign performance metrics."""
    if DRY_RUN:
        return _dry("get_campaign_performance", account_id=account_id, start_date=start_date, end_date=end_date)
    try:
        if not start_date:
            start_date = "2023-01-01"
        if not end_date:
            end_date = "2023-12-31"
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
            ORDER BY metrics.clicks DESC
            LIMIT 50
        """
        return googleads_execute_gaql_query(account_id, query)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def googleads_get_ad_performance(account_id: str,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get ad creative performance metrics."""
    if DRY_RUN:
        return _dry("get_ad_performance", account_id=account_id, start_date=start_date, end_date=end_date)
    try:
        if not start_date:
            start_date = "2023-01-01"
        if not end_date:
            end_date = "2023-12-31"
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc
            FROM ad_group_ad
            WHERE segments.date >= '{start_date}' AND segments.date <= '{end_date}'
            ORDER BY metrics.impressions DESC
            LIMIT 50
        """
        return googleads_execute_gaql_query(account_id, query)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def googleads_run_gaql(account_id: str, query: str, output_format: Optional[str] = "json") -> Dict[str, Any]:
    """Run custom GAQL query and format results."""
    if DRY_RUN:
        return _dry("run_gaql", account_id=account_id, query=query, output_format=output_format)
    try:
        response = googleads_execute_gaql_query(account_id, query)
        if "status" in response and response["status"] == "error":
            return response
        if output_format == "json":
            return response
        elif output_format == "table":
            # Placeholder for formatting table output
            return {"table": response.get("results", [])}
        elif output_format == "csv":
            import csv
            import io
            output = io.StringIO()
            results = response.get("results", [])
            if not results:
                return {"csv": ""}
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            for row in results:
                writer.writerow(row)
            return {"csv": output.getvalue()}
        else:
            return {"status": "error", "message": "Unsupported output_format"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()
