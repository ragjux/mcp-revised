import os, json
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"sheets_{name}", "args": kwargs}

ACCESS_TOKEN = os.getenv("GSHEETS_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("GSHEETS_REFRESH_TOKEN")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GSHEETS_ACCESS_TOKEN and GSHEETS_REFRESH_TOKEN")

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

mcp = FastMCP("Google Sheets MCP (native)")

def get_sheets_service():
    """Initialize and return the Google Sheets service."""
    try:
        # Create credentials using only access and refresh tokens
        credentials = Credentials(
            token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build("sheets", "v4", credentials=credentials)
    except Exception as e:
        logging.error(f"Failed to initialize Google Sheets service: {e}")
        raise RuntimeError(f"Failed to initialize Google Sheets service: {e}")

@mcp.tool()
def gs_create_spreadsheet(title: str) -> Dict[str, Any]:
    """Create a spreadsheet. Returns spreadsheetId and URL."""
    if DRY_RUN:
        return _dry("gs_create_spreadsheet", title=title)
    try:
        logging.info(f"Creating spreadsheet: {title}")
        service = get_sheets_service()
        spreadsheet = service.spreadsheets().create(
            body={"properties": {"title": title}}
        ).execute()
        return spreadsheet
    except Exception as e:
        logging.error(f"Error creating spreadsheet: {e}")
        raise

@mcp.tool()
def gs_values_get(spreadsheet_id: str, range_a1: str,
                  value_render_option: str = "UNFORMATTED_VALUE") -> Dict[str, Any]:
    """Read values from a range."""
    if DRY_RUN:
        return _dry("gs_values_get", spreadsheet_id=spreadsheet_id, range_a1=range_a1, value_render_option=value_render_option)
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueRenderOption=value_render_option
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error getting values: {e}")
        raise

@mcp.tool()
def gs_values_update(spreadsheet_id: str, range_a1: str, values: List[List[Any]],
                     value_input_option: str = "USER_ENTERED") -> Dict[str, Any]:
    """Set values in a range."""
    if DRY_RUN:
        return _dry("gs_values_update", spreadsheet_id=spreadsheet_id, range_a1=range_a1, values=values, value_input_option=value_input_option)
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption=value_input_option,
            includeValuesInResponse=True,
            body={"values": values}
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error updating values: {e}")
        raise

@mcp.tool()
def gs_values_append(spreadsheet_id: str, range_a1: str, values: List[List[Any]],
                     value_input_option: str = "USER_ENTERED",
                     insert_data_option: str = "INSERT_ROWS") -> Dict[str, Any]:
    """Append rows to a table."""
    if DRY_RUN:
        return _dry("gs_values_append", spreadsheet_id=spreadsheet_id, range_a1=range_a1, values=values, value_input_option=value_input_option, insert_data_option=insert_data_option)
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            includeValuesInResponse=True,
            body={"values": values}
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error appending values: {e}")
        raise

@mcp.tool()
def gs_values_clear(spreadsheet_id: str, range_a1: str) -> Dict[str, Any]:
    """Clear values in a range (keeps formatting & validation)."""
    if DRY_RUN:
        return _dry("gs_values_clear", spreadsheet_id=spreadsheet_id, range_a1=range_a1)
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_a1
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error clearing values: {e}")
        raise

@mcp.tool()
def gs_add_sheet(spreadsheet_id: str, title: str, index: Optional[int] = None) -> Dict[str, Any]:
    """Add a new sheet (tab). Returns new sheetId."""
    if DRY_RUN:
        return _dry("gs_add_sheet", spreadsheet_id=spreadsheet_id, title=title, index=index)
    try:
        service = get_sheets_service()
        req = {"addSheet": {"properties": {"title": title}}}
        if index is not None:
            req["addSheet"]["properties"]["index"] = index
        
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [req]}
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error adding sheet: {e}")
        raise

@mcp.tool()
def gs_delete_sheet(spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
    """Delete a sheet by numeric sheetId."""
    if DRY_RUN:
        return _dry("gs_delete_sheet", spreadsheet_id=spreadsheet_id, sheet_id=sheet_id)
    try:
        service = get_sheets_service()
        req = {"deleteSheet": {"sheetId": sheet_id}}
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [req]}
        ).execute()
        return result
    except Exception as e:
        logging.error(f"Error deleting sheet: {e}")
        raise

if __name__ == "__main__":
    mcp.run()
