#!/usr/bin/env python3
"""
Google Docs MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Docs operations.
"""

import os
import json
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
    return {"dry_run": True, "tool": f"docs_{name}", "args": kwargs}

SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# Service account credentials
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "")
GSUITE_DELEGATED_EMAIL = os.getenv("GSUITE_DELEGATED_EMAIL", "")

mcp = FastMCP("Google Docs MCP (native)")

def _get_docs_service():
    """Get authenticated Google Docs service."""
    if not SERVICE_ACCOUNT_PATH or not os.path.exists(SERVICE_ACCOUNT_PATH):
        raise RuntimeError("SERVICE_ACCOUNT_PATH not set or file not found")
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH, scopes=SCOPES
    )
    
    if GSUITE_DELEGATED_EMAIL:
        credentials = credentials.with_subject(GSUITE_DELEGATED_EMAIL)
    
    service = build('docs', 'v1', credentials=credentials)
    return service, credentials

@mcp.tool()
def docs_get_document(document_id: str) -> Dict[str, Any]:
    """Get a Google Document by ID."""
    if DRY_RUN:
        return _dry("get_document", document_id=document_id)
    
    try:
        docs_service, _ = _get_docs_service()
        document = docs_service.documents().get(documentId=document_id).execute()
        
        return {
            "status": "success",
            "document": {
                "title": document.get('title', ''),
                "document_id": document_id,
                "revision_id": document.get('revisionId', ''),
                "body": document.get('body', {})
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get document: {e}"}

@mcp.tool()
def docs_create_document(title: str) -> Dict[str, Any]:
    """Create a new Google Document."""
    if DRY_RUN:
        return _dry("create_document", title=title)
    
    try:
        docs_service, _ = _get_docs_service()
        
        document = {
            'title': title
        }
        
        doc = docs_service.documents().create(body=document).execute()
        
        return {
            "status": "success",
            "document_id": doc.get('documentId'),
            "title": doc.get('title'),
            "url": f"https://docs.google.com/document/d/{doc.get('documentId')}/edit"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create document: {e}"}

@mcp.tool()
def docs_insert_text(document_id: str, text: str, index: int = 1) -> Dict[str, Any]:
    """Insert text into a Google Document."""
    if DRY_RUN:
        return _dry("insert_text", document_id=document_id, text=text, index=index)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'insertText': {
                    'location': {'index': index},
                    'text': text
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Text inserted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to insert text: {e}"}

@mcp.tool()
def docs_delete_text(document_id: str, start_index: int, end_index: int) -> Dict[str, Any]:
    """Delete text from a Google Document."""
    if DRY_RUN:
        return _dry("delete_text", document_id=document_id, start_index=start_index, end_index=end_index)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'deleteContentRange': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    }
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Text deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete text: {e}"}

@mcp.tool()
def docs_format_text(document_id: str, start_index: int, end_index: int, 
                    bold: bool = False, italic: bool = False, 
                    underline: bool = False, font_size: Optional[int] = None) -> Dict[str, Any]:
    """Format text in a Google Document."""
    if DRY_RUN:
        return _dry("format_text", document_id=document_id, start_index=start_index, 
                   end_index=end_index, bold=bold, italic=italic, underline=underline, font_size=font_size)
    
    try:
        docs_service, _ = _get_docs_service()
        
        text_style = {}
        if bold:
            text_style['bold'] = True
        if italic:
            text_style['italic'] = True
        if underline:
            text_style['underline'] = True
        if font_size:
            text_style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        
        requests = [
            {
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': end_index
                    },
                    'textStyle': text_style,
                    'fields': ','.join(text_style.keys())
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Text formatted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to format text: {e}"}

@mcp.tool()
def docs_find_replace(document_id: str, find_text: str, replace_text: str) -> Dict[str, Any]:
    """Find and replace text in a Google Document."""
    if DRY_RUN:
        return _dry("find_replace", document_id=document_id, find_text=find_text, replace_text=replace_text)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': find_text
                    },
                    'replaceText': replace_text
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Find and replace completed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to find and replace text: {e}"}

@mcp.tool()
def docs_insert_table(document_id: str, index: int = 1, rows: int = 3, columns: int = 3) -> Dict[str, Any]:
    """Insert a table into a Google Document."""
    if DRY_RUN:
        return _dry("insert_table", document_id=document_id, index=index, rows=rows, columns=columns)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'insertTable': {
                    'location': {'index': index},
                    'rows': rows,
                    'columns': columns
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Table inserted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to insert table: {e}"}

@mcp.tool()
def docs_insert_page_break(document_id: str, index: int = 1) -> Dict[str, Any]:
    """Insert a page break into a Google Document."""
    if DRY_RUN:
        return _dry("insert_page_break", document_id=document_id, index=index)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'insertPageBreak': {
                    'location': {'index': index}
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": "Page break inserted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to insert page break: {e}"}

@mcp.tool()
def docs_batch_update(document_id: str, operations: List[Dict]) -> Dict[str, Any]:
    """Execute multiple operations on a Google Document."""
    if DRY_RUN:
        return _dry("batch_update", document_id=document_id, operations=operations)
    
    try:
        docs_service, _ = _get_docs_service()
        
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': operations}
        ).execute()
        
        return {"status": "success", "message": "Batch update completed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute batch update: {e}"}

if __name__ == "__main__":
    mcp.run()
