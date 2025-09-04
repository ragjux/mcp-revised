#!/usr/bin/env python3
"""
Google Forms MCP Server - Token-only authentication
A Model Context Protocol (MCP) server for Google Forms operations.
"""

import os
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP

# --- Configuration ---
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GFORMS_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GFORMS_REFRESH_TOKEN", "") # Kept for completeness, though not used in this script

if not ACCESS_TOKEN:
    raise RuntimeError("Set the GFORMS_ACCESS_TOKEN environment variable")

# --- Constants and MCP Initialization ---
FORMS_BASE_URL = "https://forms.googleapis.com/v1/forms"
DRIVE_BASE_URL = "https://www.googleapis.com/drive/v3/files"

mcp = FastMCP("Google Forms MCP (Token-only)")

def _dry(name: str, **kwargs: Any) -> Dict[str, Any]:
    """Logs a dry run action and returns a mock response."""
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"forms_{name}", "args": kwargs}

def _auth_header() -> Dict[str, str]:
    """Creates the authorization header using the access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

# --- Generic, Powerful Tools ---

@mcp.tool()
def gf_batch_update(form_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs a batch of updates on a form. The core function for modifying a form's structure.
    """
    if DRY_RUN:
        return _dry("batch_update", form_id=form_id, requests=requests)

    url = f"{FORMS_BASE_URL}/{form_id}:batchUpdate"
    payload = {"requests": requests}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

# --- High-Level Convenience Tools ---

@mcp.tool()
def gf_create_form(title: str, document_title: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new, empty Google Form."""
    if DRY_RUN:
        return _dry("create_form", title=title, document_title=document_title)
    
    payload = {
        "info": {
            "title": title,
            "documentTitle": document_title or title
        }
    }
    with httpx.Client(timeout=30) as c:
        r = c.post(FORMS_BASE_URL, headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gf_get_form(form_id: str) -> Dict[str, Any]:
    """Retrieves the full JSON representation of a Google Form."""
    if DRY_RUN:
        return _dry("get_form", form_id=form_id)
    
    url = f"{FORMS_BASE_URL}/{form_id}"
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def gf_add_question(form_id: str, title: str, question_type: str, index: int = 0, options: Optional[List[str]] = None) -> Dict[str, Any]:
    """Adds a single new question to a form."""
    if DRY_RUN:
        return _dry("add_question", form_id=form_id, title=title, question_type=question_type, index=index, options=options)

    question_body = {"question": {"required": False}}
    if question_type in ["RADIO", "CHECKBOX", "DROP_DOWN"]:
        question_body["question"]["choiceQuestion"] = {
            "type": question_type,
            "options": [{"value": opt} for opt in (options or [])]
        }
    else: # Default to a simple text question
        question_body["question"]["textQuestion"] = {"paragraph": False}

    request = {
        "createItem": {
            "item": {
                "title": title,
                "questionItem": question_body
            },
            "location": {"index": index}
        }
    }
    return gf_batch_update(form_id, [request])

@mcp.tool()
def gf_delete_question(form_id: str, location_index: int) -> Dict[str, Any]:
    """Deletes a question or item from a form based on its index."""
    if DRY_RUN:
        return _dry("delete_question", form_id=form_id, location_index=location_index)
        
    request = {
        "deleteItem": {
            "location": {"index": location_index}
        }
    }
    return gf_batch_update(form_id, [request])

@mcp.tool()
def gf_get_responses(form_id: str) -> Dict[str, Any]:
    """Retrieves all responses from a Google Form."""
    if DRY_RUN:
        return _dry("get_responses", form_id=form_id)
        
    url = f"{FORMS_BASE_URL}/{form_id}/responses"
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header())
        r.raise_for_status()
        return r.json()

# --- Drive API Tools for Form Management ---

@mcp.tool()
def gf_drive_list_forms(page_size: int = 10, page_token: Optional[str] = None) -> Dict[str, Any]:
    """Lists your Google Forms by searching Google Drive."""
    if DRY_RUN:
        return _dry("drive_list_forms", page_size=page_size, page_token=page_token)
    
    params = {
        "q": "mimeType='application/vnd.google-apps.form'",
        "pageSize": page_size,
        "fields": "nextPageToken, files(id, name, modifiedTime, webViewLink)"
    }
    if page_token:
        params["pageToken"] = page_token

    with httpx.Client(timeout=30) as c:
        r = c.get(DRIVE_BASE_URL, headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

# --- Main Execution ---

if __name__ == "__main__":
    mcp.run()