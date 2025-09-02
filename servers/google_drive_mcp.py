#!/usr/bin/env python3
"""
Google Drive MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Google Drive operations.
"""

import os
import json
import io
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"drive_{name}", "args": kwargs}

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', '')

if not CREDENTIALS_PATH and not SERVICE_ACCOUNT_PATH:
    raise RuntimeError("Set CREDENTIALS_PATH or SERVICE_ACCOUNT_PATH environment variable")

mcp = FastMCP("Google Drive MCP (native)")

def _get_drive_service():
    """Get authenticated Drive service."""
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
    
    return build('drive', 'v3', credentials=creds)

@mcp.tool()
def drive_search_files(query: str, max_results: int = 20) -> Dict[str, Any]:
    """Search for files in Google Drive."""
    if DRY_RUN:
        return _dry("search_files", query=query, max_results=max_results)
    
    try:
        service = _get_drive_service()
        
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        file_list = []
        for file in files:
            file_list.append({
                "id": file['id'],
                "name": file['name'],
                "mime_type": file['mimeType'],
                "modified_time": file.get('modifiedTime', 'N/A'),
                "size": file.get('size', 'N/A'),
                "web_view_link": file.get('webViewLink', '#')
            })
        
        return {"files": file_list, "count": len(file_list)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to search drive files: {e}"}

@mcp.tool()
def drive_list_files(query: str = "", max_results: int = 20) -> Dict[str, Any]:
    """List files from Google Drive."""
    if DRY_RUN:
        return _dry("list_files", query=query, max_results=max_results)
    
    try:
        service = _get_drive_service()
        
        search_query = query if query else "trashed=false"
        
        results = service.files().list(
            q=search_query,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        
        file_list = []
        for file in files:
            file_list.append({
                "id": file['id'],
                "name": file['name'],
                "mime_type": file['mimeType'],
                "modified_time": file['modifiedTime']
            })
        
        return {"files": file_list, "count": len(file_list)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list drive files: {e}"}

@mcp.tool()
def drive_get_file_content(file_id: str) -> Dict[str, Any]:
    """Get content from a Google Drive file."""
    if DRY_RUN:
        return _dry("get_file_content", file_id=file_id)
    
    try:
        service = _get_drive_service()
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get('mimeType', '')
        
        content = ""
        if 'google-apps' in mime_type:
            # For Google Docs, Sheets, etc., export
            if 'document' in mime_type:
                content = service.files().export(
                    fileId=file_id, mimeType='text/plain'
                ).execute()
                content = content.decode('utf-8')
            elif 'spreadsheet' in mime_type:
                content = service.files().export(
                    fileId=file_id, mimeType='text/csv'
                ).execute()
                content = content.decode('utf-8')
            else:
                return {"status": "error", "message": f"File type {mime_type} not supported for content extraction"}
        else:
            # For regular files, download content
            request = service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            content = file.getvalue().decode('utf-8', errors='ignore')
        
        return {
            "file_id": file_id,
            "name": file_metadata.get('name', 'Untitled'),
            "content": content
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get file content: {e}"}

@mcp.tool()
def drive_list_folder_items(folder_id: str = None, max_results: int = 20) -> Dict[str, Any]:
    """List items in a Google Drive folder."""
    if DRY_RUN:
        return _dry("list_folder_items", folder_id=folder_id, max_results=max_results)
    
    try:
        service = _get_drive_service()
        
        # Build query
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        else:
            query += " and 'root' in parents"
        
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
        ).execute()
        
        files = results.get('files', [])
        
        file_list = []
        for file in files:
            file_list.append({
                "id": file['id'],
                "name": file['name'],
                "mime_type": file['mimeType'],
                "modified_time": file.get('modifiedTime', 'N/A'),
                "size": file.get('size', 'N/A'),
                "web_view_link": file.get('webViewLink', '#')
            })
        
        return {"files": file_list, "count": len(file_list)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list drive items: {e}"}

@mcp.tool()
def drive_create_file(name: str, content: str, mime_type: str = 'text/plain') -> Dict[str, Any]:
    """Create a new file in Google Drive."""
    if DRY_RUN:
        return _dry("create_file", name=name, content=content, mime_type=mime_type)
    
    try:
        service = _get_drive_service()
        
        file_metadata = {
            'name': name,
            'mimeType': mime_type
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode('utf-8')),
            mimetype=mime_type,
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return {"status": "success", "file_id": file.get('id')}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create file: {e}"}

@mcp.tool()
def drive_get_file_permissions(file_id: str) -> Dict[str, Any]:
    """Get permissions for a Google Drive file."""
    if DRY_RUN:
        return _dry("get_file_permissions", file_id=file_id)
    
    try:
        service = _get_drive_service()
        
        permissions = service.permissions().list(fileId=file_id).execute()
        permission_list = permissions.get('permissions', [])
        
        permissions_data = []
        for permission in permission_list:
            permissions_data.append({
                "id": permission.get('id', 'Unknown'),
                "role": permission.get('role', 'Unknown'),
                "type": permission.get('type', 'Unknown'),
                "email_address": permission.get('emailAddress', 'N/A')
            })
        
        return {"permissions": permissions_data, "count": len(permissions_data)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get file permissions: {e}"}

@mcp.tool()
def drive_check_public_access(file_id: str) -> Dict[str, Any]:
    """Check if a Google Drive file has public access."""
    if DRY_RUN:
        return _dry("check_public_access", file_id=file_id)
    
    try:
        service = _get_drive_service()
        
        # Get file metadata
        file_metadata = service.files().get(
            fileId=file_id,
            fields='id,name,webViewLink'
        ).execute()
        
        # Check for public access
        permissions = service.permissions().list(fileId=file_id).execute()
        permission_list = permissions.get('permissions', [])
        
        public_access = False
        for permission in permission_list:
            if permission.get('type') == 'anyone':
                public_access = True
                break
        
        return {
            "file_id": file_id,
            "name": file_metadata.get('name', 'Unknown'),
            "public_access": public_access,
            "web_view_link": file_metadata.get('webViewLink', 'N/A')
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to check public access: {e}"}

if __name__ == "__main__":
    mcp.run()