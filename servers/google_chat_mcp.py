#!/usr/bin/env python3
"""
Google-Chat MCP Server – Google Chat Provider
A Model Context Protocol (MCP) server for Google-Chat operations.
"""

import os
import json
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"


def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"chat_{name}", "args": kwargs}


SCOPES = [
    "https://www.googleapis.com/auth/chat.spaces",
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.bot"
]

TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credentials.json")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "")

if not CREDENTIALS_PATH and not SERVICE_ACCOUNT_PATH:
    raise RuntimeError("Set CREDENTIALS_PATH or SERVICE_ACCOUNT_PATH environment variable")

mcp = FastMCP("Google Chat MCP (native)")


def _get_chat_service():
    """
    Get authenticated Google Chat service.
    """
    creds = None

    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH, scopes=SCOPES
        )
    else:
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as token:
                creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())

    return build("chat", "v1", credentials=creds)


@mcp.tool()
def chat_get_spaces() -> Dict[str, Any]:
    """
    List all Google Chat spaces the bot has access to.
    """
    if DRY_RUN:
        return _dry("get_spaces")

    try:
        service = _get_chat_service()
        response = service.spaces().list(pageSize=100).execute()
        spaces = response.get("spaces", [])
        return {"spaces": spaces, "count": len(spaces)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list spaces: {e}"}


@mcp.tool()
def chat_get_space_messages(
    space_name: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """
    List messages from a specific Google Chat space with optional time filtering.
    """
    if DRY_RUN:
        return _dry(
            "get_space_messages",
            space_name=space_name,
            start_time=start_time,
            end_time=end_time,
            max_results=max_results,
        )

    try:
        service = _get_chat_service()
        params: Dict[str, Any] = {"pageSize": max_results}
        filters: List[str] = []
        if start_time:
            filters.append(f"create_time>=\"{start_time}\"")
        if end_time:
            filters.append(f"create_time<=\"{end_time}\"")
        if filters:
            params["filter"] = " AND ".join(filters)

        response = service.spaces().messages().list(parent=space_name, **params).execute()
        messages = response.get("messages", [])
        return {"space": space_name, "messages": messages, "count": len(messages)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list messages: {e}"}


@mcp.tool()
def chat_send_message(
    space_name: str,
    text: str,
    thread_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to a Google Chat space.
    """
    if DRY_RUN:
        return _dry("send_message", space_name=space_name, text=text, thread_key=thread_key)

    try:
        service = _get_chat_service()
        body: Dict[str, Any] = {"text": text}
        if thread_key:
            body["threadKey"] = thread_key
        result = service.spaces().messages().create(parent=space_name, body=body).execute()
        return {"status": "success", "message": result}
    except Exception as e:
        return {"status": "error", "message": f"Failed to send message: {e}"}


@mcp.tool()
def chat_update_message(
    space_name: str,
    message_id: str,
    text: str
) -> Dict[str, Any]:
    """
    Update a message in a Google Chat space.
    """
    if DRY_RUN:
        return _dry("update_message", space_name=space_name, message_id=message_id, text=text)

    try:
        service = _get_chat_service()
        body = {"text": text}
        result = service.spaces().messages().update(
            name=f"{space_name}/messages/{message_id}", body=body
        ).execute()
        return {"status": "success", "message": result}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update message: {e}"}


@mcp.tool()
def chat_delete_message(
    space_name: str,
    message_id: str
) -> Dict[str, Any]:
    """
    Delete a message from a Google Chat space.
    """
    if DRY_RUN:
        return _dry("delete_message", space_name=space_name, message_id=message_id)

    try:
        service = _get_chat_service()
        service.spaces().messages().delete(name=f"{space_name}/messages/{message_id}").execute()
        return {"status": "success", "message": "Message deleted"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete message: {e}"}


if __name__ == "__main__":
    mcp.run()
