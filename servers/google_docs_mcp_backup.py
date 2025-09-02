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

TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', '')

if not CREDENTIALS_PATH and not SERVICE_ACCOUNT_PATH:
    raise RuntimeError("Set CREDENTIALS_PATH or SERVICE_ACCOUNT_PATH environment variable")

mcp = FastMCP("Google Docs MCP (native)")

def _get_docs_service():
    """Get authenticated Docs service."""
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
    
    return build('docs', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

@mcp.tool()
def docs_get_document_content(document_id: str) -> Dict[str, Any]:
    """Get content from a Google Document."""
    if DRY_RUN:
        return _dry("get_document_content", document_id=document_id)
    
    try:
        docs_service, _ = _get_docs_service()
        
        document = docs_service.documents().get(documentId=document_id).execute()
        
        # Extract text content
        content = document.get('body', {}).get('content', [])
        text_content = ""
        
        for element in content:
            if 'paragraph' in element:
                for para_element in element['paragraph']['elements']:
                    if 'textRun' in para_element:
                        text_content += para_element['textRun']['content']
        
        return {
            "document_id": document_id,
            "title": document.get('title', 'Untitled'),
            "content": text_content
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get document content: {e}"}

@mcp.tool()
def docs_create_document(title: str) -> Dict[str, Any]:
    """Create a new Google Document."""
    if DRY_RUN:
        return _dry("create_document", title=title)
    
    try:
        docs_service, _ = _get_docs_service()
        
        document = {'title': title}
        
        result = docs_service.documents().create(body=document).execute()
        document_id = result.get('documentId')
        document_url = f"https://docs.google.com/document/d/{document_id}/edit"
        
        return {
            "status": "success",
            "document_id": document_id,
            "title": title,
            "url": document_url
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create document: {e}"}

@mcp.tool()
def docs_search_documents(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for Google Documents by name."""
    if DRY_RUN:
        return _dry("search_documents", query=query, max_results=max_results)
    
    try:
        _, drive_service = _get_docs_service()
        
        query_string = f"name contains '{query}' and mimeType='application/vnd.google-apps.document' and trashed=false"
        results = drive_service.files().list(
            q=query_string,
            pageSize=max_results,
            fields="files(id, name, modifiedTime, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        documents = []
        for file in files:
            documents.append({
                "id": file['id'],
                "name": file['name'],
                "modified_time": file.get('modifiedTime', 'N/A'),
                "web_view_link": file.get('webViewLink', '#')
            })
        
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to search documents: {e}"}

@mcp.tool()
def docs_modify_text(document_id: str, text: str, index: int = 1) -> Dict[str, Any]:
    """Modify text in a Google Document."""
    if DRY_RUN:
        return _dry("modify_text", document_id=document_id, text=text, index=index)
    
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
        
        return {"status": "success", "message": "Document text modified successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to modify document text: {e}"}

@mcp.tool()
def docs_find_and_replace(document_id: str, find_text: str, replace_text: str) -> Dict[str, Any]:
    """Find and replace text in a Google Document."""
    if DRY_RUN:
        return _dry("find_and_replace", document_id=document_id, 
                   find_text=find_text, replace_text=replace_text)
    
    try:
        docs_service, _ = _get_docs_service()
        
        requests = [
            {
                'replaceAllText': {
                    'containsText': {'text': find_text},
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
def docs_insert_elements(document_id: str, element_type: str, 
                        index: int = 1, **kwargs) -> Dict[str, Any]:
    """Insert elements into a Google Document."""
    if DRY_RUN:
        return _dry("insert_elements", document_id=document_id, 
                   element_type=element_type, index=index, **kwargs)
    
    try:
        docs_service, _ = _get_docs_service()
        
        # Create request based on element type
        if element_type == 'table':
            rows = kwargs.get('rows', 3)
            columns = kwargs.get('columns', 3)
            requests = [
                {
                    'insertTable': {
                        'location': {'index': index},
                        'rows': rows,
                        'columns': columns
                    }
                }
            ]
        elif element_type == 'list':
            requests = [
                {
                    'insertText': {
                        'location': {'index': index},
                        'text': '• Item 1\n• Item 2\n• Item 3'
                    }
                }
            ]
        elif element_type == 'page_break':
            requests = [
                {
                    'insertPageBreak': {
                        'location': {'index': index}
                    }
                }
            ]
        else:
            return {"status": "error", "message": f"Unsupported element type: {element_type}"}
        
        # Execute request
        result = docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        return {"status": "success", "message": f"{element_type.title()} inserted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to insert element: {e}"}

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