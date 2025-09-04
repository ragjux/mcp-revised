import os
import json
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"sheets_{name}", "args": kwargs}

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GOOGLE_SHEETS_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GOOGLE_SHEETS_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GOOGLE_SHEETS_ACCESS_TOKEN and GOOGLE_SHEETS_REFRESH_TOKEN environment variables")

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

mcp = FastMCP("Google Sheets MCP (Token-only)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

@mcp.tool()
def gs_create_spreadsheet(title: str) -> Dict[str, Any]:
    """Create a spreadsheet. Returns spreadsheetId and URL."""
    if DRY_RUN:
        return _dry("gs_create_spreadsheet", title=title)
    
    payload = {"properties": {"title": title}}
    with httpx.Client(timeout=30) as c:
        r = c.post(SHEETS_BASE, headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_values_get(spreadsheet_id: str, range_a1: str,
                  value_render_option: str = "UNFORMATTED_VALUE") -> Dict[str, Any]:
    """Read values from a range."""
    if DRY_RUN:
        return _dry("gs_values_get", spreadsheet_id=spreadsheet_id, range_a1=range_a1, value_render_option=value_render_option)
    
    url = f"{SHEETS_BASE}/{spreadsheet_id}/values/{range_a1}"
    params = {"valueRenderOption": value_render_option}
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_values_update(spreadsheet_id: str, range_a1: str, values: List[List[Any]],
                     value_input_option: str = "USER_ENTERED") -> Dict[str, Any]:
    """Set values in a range."""
    if DRY_RUN:
        return _dry("gs_values_update", spreadsheet_id=spreadsheet_id, range_a1=range_a1, values=values, value_input_option=value_input_option)
    
    url = f"{SHEETS_BASE}/{spreadsheet_id}/values/{range_a1}"
    params = {"valueInputOption": value_input_option, "includeValuesInResponse": "true"}
    body = {"values": values}
    with httpx.Client(timeout=30) as c:
        r = c.put(url, headers=_auth_header(), params=params, json=body)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_values_append(spreadsheet_id: str, range_a1: str, values: List[List[Any]],
                     value_input_option: str = "USER_ENTERED",
                     insert_data_option: str = "INSERT_ROWS") -> Dict[str, Any]:
    """Append rows to a table."""
    if DRY_RUN:
        return _dry("gs_values_append", spreadsheet_id=spreadsheet_id, range_a1=range_a1, values=values, value_input_option=value_input_option, insert_data_option=insert_data_option)
    
    url = f"{SHEETS_BASE}/{spreadsheet_id}/values/{range_a1}:append"
    params = {"valueInputOption": value_input_option, "insertDataOption": insert_data_option,
              "includeValuesInResponse": "true"}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), params=params, json={"values": values})
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_values_clear(spreadsheet_id: str, range_a1: str) -> Dict[str, Any]:
    """Clear values in a range (keeps formatting & validation)."""
    if DRY_RUN:
        return _dry("gs_values_clear", spreadsheet_id=spreadsheet_id, range_a1=range_a1)
    
    url = f"{SHEETS_BASE}/{spreadsheet_id}/values/{range_a1}:clear"
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json={})
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_add_sheet(spreadsheet_id: str, title: str, index: Optional[int] = None) -> Dict[str, Any]:
    """Add a new sheet (tab). Returns new sheetId."""
    if DRY_RUN:
        return _dry("gs_add_sheet", spreadsheet_id=spreadsheet_id, title=title, index=index)
    
    req = {"addSheet": {"properties": {"title": title}}}
    if index is not None:
        req["addSheet"]["properties"]["index"] = index
    url = f"{SHEETS_BASE}/{spreadsheet_id}:batchUpdate"
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json={"requests": [req]})
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_delete_sheet(spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
    """Delete a sheet by numeric sheetId."""
    if DRY_RUN:
        return _dry("gs_delete_sheet", spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)
    
    req = {"deleteSheet": {"sheetId": sheet_id}}
    url = f"{SHEETS_BASE}/{spreadsheet_id}:batchUpdate"
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json={"requests": [req]})
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_get_spreadsheet(spreadsheet_id: str) -> Dict[str, Any]:
    """Get spreadsheet metadata including sheet information."""
    if DRY_RUN:
        return _dry("gs_get_spreadsheet", spreadsheet_id=spreadsheet_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(SHEETS_BASE + f"/{spreadsheet_id}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gs_batch_update(spreadsheet_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute multiple operations in a single batch update."""
    if DRY_RUN:
        return _dry("gs_batch_update", spreadsheet_id=spreadsheet_id, requests=requests)
    
    url = f"{SHEETS_BASE}/{spreadsheet_id}:batchUpdate"
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json={"requests": requests})
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
