#!/usr/bin/env python3
"""
HubSpot MCP Server - FastMCP version
A Model Context Protocol (MCP) server for HubSpot CRM operations.
"""

import os
import json
from typing import Any, Dict, List, Optional
import httpx
from fastmcp import FastMCP

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"hubspot_{name}", "args": kwargs}

HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
HUBSPOT_BASE = "https://api.hubapi.com"

if not HUBSPOT_TOKEN:
    raise RuntimeError("Set HUBSPOT_ACCESS_TOKEN environment variable")

mcp = FastMCP("HubSpot MCP (native)")

def _auth_header() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

@mcp.tool()
def hubspot_create_contact(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a HubSpot contact. Prevent duplicates by email.
    properties: {"email": "...", "firstname": "...", ...}
    """
    if DRY_RUN:
        return _dry("create_contact", properties=properties)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts"
    body = {"properties": properties}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json=body)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_create_company(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a HubSpot company. Prevent duplicates by domain.
    properties: {"name": "...", "domain": "...", ...}
    """
    if DRY_RUN:
        return _dry("create_company", properties=properties)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies"
    body = {"properties": properties}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json=body)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_active_contacts(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve most recently active contacts.
    """
    if DRY_RUN:
        return _dry("get_active_contacts", limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts"
    params = {"limit": limit, "properties": "email,firstname,lastname,hs_lastmodifieddate", "sorts": "-hs_lastmodifieddate"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_active_companies(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve most recently active companies.
    """
    if DRY_RUN:
        return _dry("get_active_companies", limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies"
    params = {"limit": limit, "properties": "name,domain,hs_lastmodifieddate", "sorts": "-hs_lastmodifieddate"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_company_contacts(company_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve contacts associated with a specific company.
    """
    if DRY_RUN:
        return _dry("get_company_contacts", company_id=company_id, limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies/{company_id}/associations/contacts"
    params = {"limit": limit}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_company_deals(company_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve deals associated with a specific company.
    """
    if DRY_RUN:
        return _dry("get_company_deals", company_id=company_id, limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies/{company_id}/associations/deals"
    params = {"limit": limit}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_search_companies(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for companies by name or domain.
    """
    if DRY_RUN:
        return _dry("search_companies", query=query, limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies"
    params = {"search": query, "limit": limit, "properties": "name,domain,industry"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_search_contacts(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for contacts by name or email.
    """
    if DRY_RUN:
        return _dry("search_contacts", query=query, limit=limit)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts"
    params = {"search": query, "limit": limit, "properties": "email,firstname,lastname"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_company_details(company_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific company.
    """
    if DRY_RUN:
        return _dry("get_company_details", company_id=company_id)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/companies/{company_id}"
    params = {"properties": "name,domain,industry,description,phone,address,website,lifecyclestage"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def hubspot_get_contact_details(contact_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific contact.
    """
    if DRY_RUN:
        return _dry("get_contact_details", contact_id=contact_id)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}"
    params = {"properties": "email,firstname,lastname,phone,company,lifecyclestage"}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
