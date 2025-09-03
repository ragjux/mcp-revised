#!/usr/bin/env python3
"""
Google Drive MCP Server - Token-only authentication
A Model Context Protocol (MCP) server for Google Drive operations.
"""

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
    return {"dry_run": True, "tool": f"drive_{name}", "args": kwargs}

# Environment variables for token-only authentication
ACCESS_TOKEN = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GOOGLE_DRIVE_ACCESS_TOKEN and GOOGLE_DRIVE_REFRESH_TOKEN environment variables")

DRIVE_BASE = "https://www.googleapis.com/drive/v3"

mcp = FastMCP("Google Drive MCP (Token-only)")

def _auth_header() -> Dict[str, str]:
    """Get authorization header with access token."""
    return {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

@mcp.tool()
def drive_search_files(query: str, max_results: int = 20) -> Dict[str, Any]:
    """Search for files in Google Drive."""
    if DRY_RUN:
        return _dry("drive_search_files", query=query, max_results=max_results)
    
    params = {
        "q": query,
        "pageSize": max_results,
        "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink)"
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.get(DRIVE_BASE + "/files", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_list_files(max_results: int = 20, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """List files in Google Drive."""
    if DRY_RUN:
        return _dry("drive_list_files", max_results=max_results, folder_id=folder_id)
    
    params = {
        "pageSize": max_results,
        "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink)"
    }
    
    if folder_id:
        params["q"] = f"'{folder_id}' in parents"
    
    with httpx.Client(timeout=30) as c:
        r = c.get(DRIVE_BASE + "/files", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_get_file(file_id: str) -> Dict[str, Any]:
    """Get file metadata by ID."""
    if DRY_RUN:
        return _dry("drive_get_file", file_id=file_id)
    
    params = {"fields": "id,name,mimeType,size,createdTime,modifiedTime,webViewLink,parents"}
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{DRIVE_BASE}/files/{file_id}", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_download_file(file_id: str) -> Dict[str, Any]:
    """Download file content."""
    if DRY_RUN:
        return _dry("drive_download_file", file_id=file_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{DRIVE_BASE}/files/{file_id}?alt=media", headers=_auth_header())
        r.raise_for_status()
        return {"content": r.content, "file_id": file_id}

@mcp.tool()
def drive_create_folder(name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new folder."""
    if DRY_RUN:
        return _dry("drive_create_folder", name=name, parent_id=parent_id)
    
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    
    if parent_id:
        metadata["parents"] = [parent_id]
    
    with httpx.Client(timeout=30) as c:
        r = c.post(DRIVE_BASE + "/files", headers=_auth_header(), json=metadata)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_upload_file(name: str, content: str, mime_type: str = "text/plain", 
                     parent_id: Optional[str] = None) -> Dict[str, Any]:
    """Upload a file to Google Drive."""
    if DRY_RUN:
        return _dry("drive_upload_file", name=name, content=content, mime_type=mime_type, parent_id=parent_id)
    
    metadata = {
        "name": name,
        "mimeType": mime_type
    }
    
    if parent_id:
        metadata["parents"] = [parent_id]
    
    # Create multipart upload
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    # Create the multipart body
    body_parts = []
    
    # Add metadata part
    body_parts.append(f"--{boundary}")
    body_parts.append("Content-Disposition: form-data; name=\"metadata\"")
    body_parts.append("Content-Type: application/json")
    body_parts.append("")
    body_parts.append(json.dumps(metadata))
    
    # Add file content part
    body_parts.append(f"--{boundary}")
    body_parts.append(f"Content-Disposition: form-data; name=\"file\"; filename=\"{name}\"")
    body_parts.append(f"Content-Type: {mime_type}")
    body_parts.append("")
    body_parts.append(content)
    body_parts.append(f"--{boundary}--")
    
    multipart_body = "\r\n".join(body_parts)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.post(DRIVE_BASE + "/files?uploadType=multipart", 
                  headers=headers, content=multipart_body.encode())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_update_file(file_id: str, content: str, mime_type: str = "text/plain") -> Dict[str, Any]:
    """Update an existing file."""
    if DRY_RUN:
        return _dry("drive_update_file", file_id=file_id, content=content, mime_type=mime_type)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": mime_type
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.patch(f"{DRIVE_BASE}/files/{file_id}?uploadType=media", 
                   headers=headers, content=content.encode())
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_delete_file(file_id: str) -> Dict[str, Any]:
    """Delete a file."""
    if DRY_RUN:
        return _dry("drive_delete_file", file_id=file_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.delete(f"{DRIVE_BASE}/files/{file_id}", headers=_auth_header())
        r.raise_for_status()
        return {"success": True, "file_id": file_id}

@mcp.tool()
def drive_copy_file(file_id: str, new_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
    """Copy a file."""
    if DRY_RUN:
        return _dry("drive_copy_file", file_id=file_id, new_name=new_name, parent_id=parent_id)
    
    metadata = {"name": new_name}
    if parent_id:
        metadata["parents"] = [parent_id]
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{DRIVE_BASE}/files/{file_id}/copy", headers=_auth_header(), json=metadata)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_move_file(file_id: str, new_parent_id: str) -> Dict[str, Any]:
    """Move a file to a different folder."""
    if DRY_RUN:
        return _dry("drive_move_file", file_id=file_id, new_parent_id=new_parent_id)
    
    # First get current parents
    file_info = drive_get_file(file_id)
    current_parents = file_info.get("parents", [])
    
    # Update parents
    params = {
        "addParents": new_parent_id,
        "removeParents": ",".join(current_parents)
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.patch(f"{DRIVE_BASE}/files/{file_id}", headers=_auth_header(), params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_share_file(file_id: str, email: str, role: str = "reader") -> Dict[str, Any]:
    """Share a file with a specific email address."""
    if DRY_RUN:
        return _dry("drive_share_file", file_id=file_id, email=email, role=role)
    
    permission = {
        "type": "user",
        "role": role,
        "emailAddress": email
    }
    
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{DRIVE_BASE}/files/{file_id}/permissions", 
                  headers=_auth_header(), json=permission)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def drive_list_permissions(file_id: str) -> Dict[str, Any]:
    """List permissions for a file."""
    if DRY_RUN:
        return _dry("drive_list_permissions", file_id=file_id)
    
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{DRIVE_BASE}/files/{file_id}/permissions", headers=_auth_header())
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
