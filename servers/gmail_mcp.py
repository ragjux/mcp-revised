"""
Gmail MCP Server - Gmail API Integration

This server provides Gmail functionality using the Gmail API with OAuth2 authentication.
It requires the following environment variables:
- GMAIL_ACCESS_TOKEN: OAuth2 access token for Gmail API
- GMAIL_REFRESH_TOKEN: OAuth2 refresh token for Gmail API

The server uses only Gmail API endpoints and does not require SMTP/IMAP credentials.
Note: This simplified version requires manual token refresh when the access token expires.
"""

import os
import json
import base64
import requests
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables from .env file
load_dotenv()

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"gmail_{name}", "args": kwargs}

ACCESS_TOKEN = os.getenv("GMAIL_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GMAIL_ACCESS_TOKEN and GMAIL_REFRESH_TOKEN environment variables")

mcp = FastMCP("Gmail MCP (native)")

def _get_valid_access_token():
    """Get a valid access token.
    
    Note: This simplified version uses the provided access token directly.
    When the access token expires, you'll need to manually refresh it using
    the refresh token and update the GMAIL_ACCESS_TOKEN environment variable.
    """
    return ACCESS_TOKEN

def _make_gmail_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None):
    """Make authenticated request to Gmail API."""
    access_token = _get_valid_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://gmail.googleapis.com/gmail/v1/{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    response.raise_for_status()
    return response.json()

# Internal helper functions (not decorated)
def _send_email_internal(recipient: str, subject: str, body: str, 
                        attachment_path: Optional[str] = None) -> Dict[str, Any]:
    """Internal function to send email using Gmail API."""
    if DRY_RUN:
        return _dry("send_email", recipient=recipient, subject=subject, body=body, attachment_path=attachment_path)
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)
        
        # Encode the message for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        # Send via Gmail API
        data = {
            "raw": raw_message
        }
        
        result = _make_gmail_api_request("users/me/messages/send", "POST", data)
        
        return {"status": "success", "message": "Email sent successfully", "message_id": result.get("id")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email: {e}"}

def _download_attachment_internal(attachment_url: str, attachment_filename: str) -> Dict[str, Any]:
    """Internal function to download attachment."""
    if DRY_RUN:
        return _dry("download_attachment", attachment_url=attachment_url, attachment_filename=attachment_filename)
    
    try:
        temp_dir = "temp_attachments"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, attachment_filename)
        
        response = requests.get(attachment_url, timeout=30)
        response.raise_for_status()
        
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        return {"status": "error", "message": f"Failed to download attachment: {e}"}

def _get_prestaged_attachment_internal(attachment_name: str) -> Dict[str, Any]:
    """Internal function to get prestaged attachment."""
    if DRY_RUN:
        return _dry("get_prestaged_attachment", attachment_name=attachment_name)
    
    attachment_dir = "available_attachments"
    file_path = os.path.join(attachment_dir, attachment_name)
    
    if os.path.exists(file_path):
        return {"status": "success", "file_path": file_path}
    else:
        return {"status": "error", "message": f"Attachment '{attachment_name}' not found"}

# MCP tool functions (decorated)
@mcp.tool()
def gmail_send_email(recipient: str, subject: str, body: str, 
                    attachment_path: Optional[str] = None) -> Dict[str, Any]:
    """Send an email via Gmail API."""
    return _send_email_internal(recipient, subject, body, attachment_path)

@mcp.tool()
def gmail_fetch_recent_emails(folder: str = "INBOX", limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails from Gmail using Gmail API."""
    if DRY_RUN:
        return _dry("fetch_recent_emails", folder=folder, limit=limit)
    
    try:
        # Map folder names to Gmail API query
        folder_queries = {
            "INBOX": "in:inbox",
            "SENT": "in:sent",
            "DRAFT": "in:draft",
            "TRASH": "in:trash",
            "SPAM": "in:spam"
        }
        
        query = folder_queries.get(folder.upper(), "in:inbox")
        
        # Get list of messages
        params = {
            "q": query,
            "maxResults": limit
        }
        
        messages_result = _make_gmail_api_request("users/me/messages", params=params)
        
        if not messages_result.get("messages"):
            return {"emails": [], "message": "No emails found"}
        
        emails = []
        
        # Fetch details for each message
        for message in messages_result["messages"]:
            message_id = message["id"]
            message_detail = _make_gmail_api_request(f"users/me/messages/{message_id}")
            
            headers = message_detail.get("payload", {}).get("headers", [])
            header_dict = {header["name"]: header["value"] for header in headers}
            
            emails.append({
                "id": message_id,
                "from": header_dict.get("From", ""),
                "subject": header_dict.get("Subject", ""),
                "date": header_dict.get("Date", ""),
                "snippet": message_detail.get("snippet", "")
            })
        
        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch emails: {e}"}

@mcp.tool()
def gmail_download_attachment(attachment_url: str, attachment_filename: str) -> Dict[str, Any]:
    """Download an attachment from URL."""
    return _download_attachment_internal(attachment_url, attachment_filename)

@mcp.tool()
def gmail_send_email_with_url_attachment(recipient: str, subject: str, body: str, 
                                       attachment_url: str, attachment_filename: str) -> Dict[str, Any]:
    """Send email with attachment downloaded from URL."""
    if DRY_RUN:
        return _dry("send_email_with_url_attachment", recipient=recipient, subject=subject, 
                   body=body, attachment_url=attachment_url, attachment_filename=attachment_filename)
    
    try:
        # Download attachment first using internal function
        download_result = _download_attachment_internal(attachment_url, attachment_filename)
        if download_result.get("status") == "error":
            return download_result
        
        # Send email with downloaded attachment using internal function
        return _send_email_internal(recipient, subject, body, download_result["file_path"])
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email with URL attachment: {e}"}

@mcp.tool()
def gmail_get_prestaged_attachment(attachment_name: str) -> Dict[str, Any]:
    """Get path of pre-staged attachment."""
    return _get_prestaged_attachment_internal(attachment_name)

@mcp.tool()
def gmail_send_email_with_prestaged_attachment(recipient: str, subject: str, body: str, 
                                             attachment_name: str) -> Dict[str, Any]:
    """Send email with pre-staged attachment."""
    if DRY_RUN:
        return _dry("send_email_with_prestaged_attachment", recipient=recipient, subject=subject, 
                   body=body, attachment_name=attachment_name)
    
    try:
        # Get pre-staged attachment using internal function
        attachment_result = _get_prestaged_attachment_internal(attachment_name)
        if attachment_result.get("status") == "error":
            return attachment_result
        
        # Send email with attachment using internal function
        return _send_email_internal(recipient, subject, body, attachment_result["file_path"])
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email with pre-staged attachment: {e}"}

@mcp.tool()
def gmail_get_profile() -> Dict[str, Any]:
    """Get Gmail user profile information."""
    if DRY_RUN:
        return _dry("get_profile")
    
    try:
        profile = _make_gmail_api_request("users/me/profile")
        return {
            "status": "success",
            "profile": {
                "email_address": profile.get("emailAddress", ""),
                "messages_total": profile.get("messagesTotal", 0),
                "threads_total": profile.get("threadsTotal", 0),
                "history_id": profile.get("historyId", "")
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get profile: {e}"}

@mcp.tool()
def gmail_search_emails(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search emails using Gmail search syntax."""
    if DRY_RUN:
        return _dry("search_emails", query=query, max_results=max_results)
    
    try:
        params = {
            "q": query,
            "maxResults": max_results
        }
        
        messages_result = _make_gmail_api_request("users/me/messages", params=params)
        
        if not messages_result.get("messages"):
            return {"emails": [], "message": "No emails found matching query"}
        
        emails = []
        
        # Fetch details for each message
        for message in messages_result["messages"]:
            message_id = message["id"]
            message_detail = _make_gmail_api_request(f"users/me/messages/{message_id}")
            
            headers = message_detail.get("payload", {}).get("headers", [])
            header_dict = {header["name"]: header["value"] for header in headers}
            
            emails.append({
                "id": message_id,
                "from": header_dict.get("From", ""),
                "subject": header_dict.get("Subject", ""),
                "date": header_dict.get("Date", ""),
                "snippet": message_detail.get("snippet", "")
            })
        
        return {"emails": emails, "count": len(emails), "query": query}
    except Exception as e:
        return {"status": "error", "message": f"Failed to search emails: {e}"}

if __name__ == "__main__":
    mcp.run()
