import os
import json
import smtplib
import imaplib
import email
import requests
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from email.mime.text import MIMEText

# Load environment variables from .env file
load_dotenv()
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"gmail_{name}", "args": kwargs}

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

if not SMTP_USERNAME or not SMTP_PASSWORD:
    raise RuntimeError("Set SMTP_USERNAME and SMTP_PASSWORD environment variables")

mcp = FastMCP("Gmail MCP (native)")

def _smtp_connection():
    """Create and authenticate SMTP connection."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    return server

def _imap_connection():
    """Create and authenticate IMAP connection."""
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(SMTP_USERNAME, SMTP_PASSWORD)
    return mail

# Internal helper functions (not decorated)
def _send_email_internal(recipient: str, subject: str, body: str, 
                        attachment_path: Optional[str] = None) -> Dict[str, Any]:
    """Internal function to send email."""
    if DRY_RUN:
        return _dry("send_email", recipient=recipient, subject=subject, body=body, attachment_path=attachment_path)
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
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
        
        server = _smtp_connection()
        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
        server.quit()
        
        return {"status": "success", "message": "Email sent successfully"}
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
    """Send an email via Gmail SMTP."""
    return _send_email_internal(recipient, subject, body, attachment_path)

@mcp.tool()
def gmail_fetch_recent_emails(folder: str = "INBOX", limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails from Gmail."""
    if DRY_RUN:
        return _dry("fetch_recent_emails", folder=folder, limit=limit)
    
    try:
        mail = _imap_connection()
        mail.select(folder)
        result, data = mail.search(None, "ALL")
        
        if not data or not data[0]:
            return {"emails": [], "message": "No emails found"}
        
        email_ids = data[0].split()
        latest_email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        emails = []
        
        for email_id in reversed(latest_email_ids):
            result, data = mail.fetch(email_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            emails.append({
                "id": email_id.decode(),
                "from": msg.get("From", ""),
                "subject": subject,
                "date": msg.get("Date", "")
            })
        
        mail.close()
        mail.logout()
        
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

if __name__ == "__main__":
    mcp.run()
