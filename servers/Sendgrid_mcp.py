#!/usr/bin/env python3
"""
SendGrid MCP Server - FastMCP version
Provides a tool to send emails via SendGrid API.
"""

import os
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"sendgrid_{name}", "args": kwargs}

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")

if not SENDGRID_API_KEY or not FROM_EMAIL:
    raise RuntimeError("Set SENDGRID_API_KEY and FROM_EMAIL environment variables")

mcp = FastMCP("sendgrid")

@mcp.tool
async def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email via SendGrid."""
    if DRY_RUN:
        return _dry("send_email", to=to, subject=subject, body=body)

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data)
        if resp.status_code in (200, 202):
            return {"status": "success", "message": "Email sent successfully"}
        else:
            return {
                "status": "error",
                "message": f"Failed to send email: {resp.status_code} {resp.text}",
            }

if __name__ == "__main__":
    mcp.run()
