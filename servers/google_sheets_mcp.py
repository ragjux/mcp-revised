import os, json
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GARequest

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"sheets_{name}", "args": kwargs}

SCOPES = os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file").split()
SA_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "")
DELEGATED = os.getenv("GSUITE_DELEGATED_EMAIL", "")  # optional for domain-wide delegation

if not SA_PATH:
    raise RuntimeError("Set SERVICE_ACCOUNT_PATH to your service-account JSON file")

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

mcp = FastMCP("Google Sheets MCP (native)")

def _auth_header() -> Dict[str, str]:
    creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    if DELEGATED:
        creds = creds.with_subject(DELEGATED)
    creds.refresh(GARequest())
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

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

if __name__ == "__main__":
    mcp.run()
