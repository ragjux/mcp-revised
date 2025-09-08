#!/usr/bin/env python3
"""
Google Docs MCP Server - Token-only authentication
A Model Context Protocol (MCP) server for Google Docs operations.
"""

import os
import json
import httpx
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
    return {"dry_run": True, "tool": f"docs_{name}", "args": kwargs}

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GDOCS_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GDOCS_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GDOCS_ACCESS_TOKEN and GDOCS_REFRESH_TOKEN environment variables")

DOCS_BASE = "https://docs.googleapis.com/v1/documents"
DRIVE_BASE = "https://www.googleapis.com/drive/v3"

mcp = FastMCP("Google Docs MCP (Token-only)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

@mcp.tool()
def docs_get_document(document_id: str) -> Dict[str, Any]:
    """Get a Google Document by ID."""
    if DRY_RUN:
        return _dry("docs_get_document", document_id=document_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{DOCS_BASE}/{document_id}", headers=_auth_header())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def docs_create_document(title: str) -> Dict[str, Any]:
    """Create a new Google Document."""
    if DRY_RUN:
        return _dry("docs_create_document", title=title)
    
    payload = {"title": title}
    with httpx.Client(timeout=30) as c:
        r = c.post(DOCS_BASE, headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def docs_batch_update(document_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply one or more updates to the document."""
    if DRY_RUN:
        return _dry("docs_batch_update", document_id=document_id, requests=requests)
    
    url = f"{DOCS_BASE}/{document_id}:batchUpdate"
    payload = {"requests": requests}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=_auth_header(), json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def docs_insert_text(document_id: str, text: str, location_index: int = 1) -> Dict[str, Any]:
    """Insert text at a specific location in the document."""
    if DRY_RUN:
        return _dry("docs_insert_text", document_id=document_id, text=text, location_index=location_index)
    
    request = {
        "insertText": {
            "location": {"index": location_index},
            "text": text
        }
    }
    return docs_batch_update(document_id, [request])

@mcp.tool()
def docs_delete_text(document_id: str, start_index: int, end_index: int) -> Dict[str, Any]:
    """Delete text from the document."""
    if DRY_RUN:
        return _dry("docs_delete_text", document_id=document_id, start_index=start_index, end_index=end_index)
    
    request = {
        "deleteContentRange": {
            "range": {
                "startIndex": start_index,
                "endIndex": end_index
            }
        }
    }
    return docs_batch_update(document_id, [request])

@mcp.tool()
def docs_format_text(document_id: str, start_index: int, end_index: int, 
                    bold: Optional[bool] = None, italic: Optional[bool] = None,
                    underline: Optional[bool] = None, font_size: Optional[float] = None) -> Dict[str, Any]:
    """Format text in the document."""
    if DRY_RUN:
        return _dry("docs_format_text", document_id=document_id, start_index=start_index, end_index=end_index, 
                   bold=bold, italic=italic, underline=underline, font_size=font_size)
    
    text_style = {}
    if bold is not None:
        text_style["bold"] = bold
    if italic is not None:
        text_style["italic"] = italic
    if underline is not None:
        text_style["underline"] = underline
    if font_size is not None:
        text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
    
    request = {
        "updateTextStyle": {
            "range": {
                "startIndex": start_index,
                "endIndex": end_index
            },
            "textStyle": text_style,
            "fields": ",".join(text_style.keys())
        }
    }
    return docs_batch_update(document_id, [request])

@mcp.tool()
def docs_search_replace(document_id: str, search_text: str, replace_text: str) -> Dict[str, Any]:
    """Search and replace text in the document."""
    if DRY_RUN:
        return _dry("docs_search_replace", document_id=document_id, search_text=search_text, replace_text=replace_text)
    
    request = {
        "replaceAllText": {
            "containsText": {
                "text": search_text,
                "matchCase": False
            },
            "replaceText": replace_text
        }
    }
    return docs_batch_update(document_id, [request])

@mcp.tool()
def docs_create_paragraph(document_id: str, text: str, location_index: int = 1) -> Dict[str, Any]:
    """Create a new paragraph in the document."""
    if DRY_RUN:
        return _dry("docs_create_paragraph", document_id=document_id, text=text, location_index=location_index)
    
    request = {
        "insertText": {
            "location": {"index": location_index},
            "text": text + "\n"
        }
    }
    return docs_batch_update(document_id, [request])

@mcp.tool()
def docs_create_heading(document_id: str, text: str, level: int = 1, location_index: int = 1) -> Dict[str, Any]:
    """Create a heading in the document."""
    if DRY_RUN:
        return _dry("docs_create_heading", document_id=document_id, text=text, level=level, location_index=location_index)
    
    # Insert text first
    insert_request = {
        "insertText": {
            "location": {"index": location_index},
            "text": text + "\n"
        }
    }
    
    # Then format as heading
    format_request = {
        "updateParagraphStyle": {
            "range": {
                "startIndex": location_index,
                "endIndex": location_index + len(text)
            },
            "paragraphStyle": {
                "namedStyleType": f"HEADING_{level}"
            },
            "fields": "namedStyleType"
        }
    }
    
    return docs_batch_update(document_id, [insert_request, format_request])

@mcp.tool()
def docs_create_bullet_list(document_id: str, items: List[str], location_index: int = 1) -> Dict[str, Any]:
    """Create a bullet list in the document."""
    if DRY_RUN:
        return _dry("docs_create_bullet_list", document_id=document_id, items=items, location_index=location_index)
    
    requests = []
    current_index = location_index
    
    for item in items:
        # Insert text
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": f"• {item}\n"
            }
        })
        current_index += len(f"• {item}\n")
    
    return docs_batch_update(document_id, requests)

@mcp.tool()
def docs_create_numbered_list(document_id: str, items: List[str], location_index: int = 1) -> Dict[str, Any]:
    """Create a numbered list in the document."""
    if DRY_RUN:
        return _dry("docs_create_numbered_list", document_id=document_id, items=items, location_index=location_index)
    
    requests = []
    current_index = location_index
    
    for i, item in enumerate(items, 1):
        # Insert text
        requests.append({
            "insertText": {
                "location": {"index": current_index},
                "text": f"{i}. {item}\n"
            }
        })
        current_index += len(f"{i}. {item}\n")
    
    return docs_batch_update(document_id, requests)

@mcp.tool()
def docs_export_document(document_id: str, format: str = "pdf") -> Dict[str, Any]:
    """Export document in various formats (pdf, docx, html, txt)."""
    if DRY_RUN:
        return _dry("docs_export_document", document_id=document_id, format=format)
    
    url = f"{DRIVE_BASE}/files/{document_id}/export"
    params = {"mimeType": f"application/{format}"}
    
    with httpx.Client(timeout=30) as c:
        r = c.get(url, headers=_auth_header(), params=params)
        r.raise_for_status()
        return {"content": r.content, "format": format}

if __name__ == "__main__":
    mcp.run()
