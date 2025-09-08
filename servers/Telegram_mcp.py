#!/usr/bin/env python3
"""
Telegram MCP Server - FastMCP version (read-only)
"""

import os
import asyncio
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
from telethon import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon.errors import SessionPasswordNeededError

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"telegram_{name}", "args": kwargs}

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")
SESSION_NAME = os.getenv("TELEGRAM_SESSION", "telegram.session")

if not API_ID or not API_HASH:
    raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH. Optionally TELEGRAM_PHONE for first sign-in.")

mcp = FastMCP("Telegram MCP (native)")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
_client_ready = False

async def _ensure_connected():
    global _client_ready
    if _client_ready:
        return
    await client.connect()
    if not await client.is_user_authorized():
        if not PHONE:
            raise RuntimeError("First-time sign-in requires TELEGRAM_PHONE to request code")
        # Request code and log in
        try:
            await client.send_code_request(PHONE)
            code = os.environ.get("TELEGRAM_LOGIN_CODE")
            if not code:
                raise RuntimeError("Set TELEGRAM_LOGIN_CODE with the code received from Telegram for initial sign-in")
            await client.sign_in(PHONE, code)
        except SessionPasswordNeededError:
            pwd = os.environ.get("TELEGRAM_2FA_PASSWORD")
            if not pwd:
                raise RuntimeError("Account has 2FA enabled; set TELEGRAM_2FA_PASSWORD for initial sign-in")
            await client.sign_in(password=pwd)
    _client_ready = True

# 1) List dialogs (chats, channels, groups), with optional unread filter
@mcp.tool()
async def telegram_list_dialogs(unread_only: bool = False, limit: int = 50) -> Dict[str, Any]:
    """List dialogs (chats/channels/groups)."""
    if DRY_RUN:
        return _dry("list_dialogs", unread_only=unread_only, limit=limit)
    await _ensure_connected()
    dialogs_info = []
    async for dialog in client.iter_dialogs(limit=limit):
        if unread_only and dialog.unread_count == 0:
            continue
        dialogs_info.append({
            "name": dialog.name,
            "entity_id": dialog.entity.id if hasattr(dialog.entity, "id") else None,
            "is_channel": getattr(dialog.entity, "broadcast", False) or getattr(dialog.entity, "megagroup", False),
            "unread_count": dialog.unread_count,
            "pinned": dialog.pinned
        })
    return {"dialogs": dialogs_info, "count": len(dialogs_info)}

# 2) Get messages in a dialog (by dialog name or ID)
@mcp.tool()
async def telegram_get_messages(dialog: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
    """Get recent messages in a dialog (chat/channel/group) by display name or numeric id."""
    if DRY_RUN:
        return _dry("get_messages", dialog=dialog, limit=limit, unread_only=unread_only)
    await _ensure_connected()
    # Resolve entity by name or id
    try:
        entity = await client.get_entity(dialog)
    except Exception:
        # If numeric id was passed as string, try int
        try:
            entity = await client.get_entity(int(dialog))
        except Exception as e:
            return {"status": "error", "message": f"Dialog not found: {e}"}
    msgs = []
    async for m in client.iter_messages(entity, limit=limit):
        if unread_only and m.read:
            continue
        msgs.append({
            "id": m.id,
            "date": m.date.isoformat() if m.date else None,
            "message": m.message,
            "sender_id": m.sender_id,
            "is_reply": bool(m.reply_to_msg_id),
            "media": bool(m.media),
        })
    msgs.reverse()
    return {"messages": msgs, "count": len(msgs)}

# 3) Mark dialog as read
@mcp.tool()
async def telegram_mark_read(dialog: str) -> Dict[str, Any]:
    """Mark a dialog as read."""
    if DRY_RUN:
        return _dry("mark_read", dialog=dialog)
    await _ensure_connected()
    try:
        entity = await client.get_entity(dialog)
    except Exception:
        try:
            entity = await client.get_entity(int(dialog))
        except Exception as e:
            return {"status": "error", "message": f"Dialog not found: {e}"}
    await client.send_read_acknowledge(entity)
    return {"status": "success"}

# 4) Retrieve messages by date/time (ISO8601 strings)
@mcp.tool()
async def telegram_get_messages_by_time(dialog: str, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Get messages in date range; pass ISO8601 strings for date_from/date_to."""
    if DRY_RUN:
        return _dry("get_messages_by_time", dialog=dialog, date_from=date_from, date_to=date_to, limit=limit)
    from datetime import datetime
    await _ensure_connected()
    try:
        entity = await client.get_entity(dialog)
    except Exception:
        try:
            entity = await client.get_entity(int(dialog))
        except Exception as e:
            return {"status": "error", "message": f"Dialog not found: {e}"}
    df = datetime.fromisoformat(date_from) if date_from else None
    dt = datetime.fromisoformat(date_to) if date_to else None
    msgs = []
    async for m in client.iter_messages(entity, offset_date=dt, reverse=True):
        if df and m.date < df:
            continue
        if dt and m.date > dt:
            continue
        msgs.append({
            "id": m.id,
            "date": m.date.isoformat() if m.date else None,
            "message": m.message,
            "sender_id": m.sender_id
        })
        if len(msgs) >= limit:
            break
    return {"messages": msgs, "count": len(msgs)}

# 5) Download media by message id into a folder
@mcp.tool()
async def telegram_download_media(dialog: str, message_id: int, download_dir: str = "./downloads") -> Dict[str, Any]:
    """Download media for a given message id into download_dir."""
    if DRY_RUN:
        return _dry("download_media", dialog=dialog, message_id=message_id, download_dir=download_dir)
    await _ensure_connected()
    os.makedirs(download_dir, exist_ok=True)
    try:
        entity = await client.get_entity(dialog)
    except Exception:
        try:
            entity = await client.get_entity(int(dialog))
        except Exception as e:
            return {"status": "error", "message": f"Dialog not found: {e}"}
    msg = await client.get_messages(entity, ids=message_id)
    if not msg or not msg.media:
        return {"status": "error", "message": "Message not found or contains no media"}
    file_path = await client.download_media(msg, file=download_dir)
    return {"status": "success", "path": file_path}

# 6) Get contacts
@mcp.tool()
async def telegram_get_contacts(limit: int = 1000) -> Dict[str, Any]:
    """Get contacts."""
    if DRY_RUN:
        return _dry("get_contacts", limit=limit)
    await _ensure_connected()
    contacts = []
    async for c in client.iter_contacts():
        contacts.append({
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "username": c.username,
            "phone": c.phone
        })
        if len(contacts) >= limit:
            break
    return {"contacts": contacts, "count": len(contacts)}

# 7) Draft a message (does not send)
@mcp.tool()
async def telegram_draft_message(dialog: str, text: str) -> Dict[str, Any]:
    """Create/update a draft message for the dialog (read-only behavior: not sending)."""
    if DRY_RUN:
        return _dry("draft_message", dialog=dialog, text=text)
    await _ensure_connected()
    try:
        entity = await client.get_entity(dialog)
    except Exception:
        try:
            entity = await client.get_entity(int(dialog))
        except Exception as e:
            return {"status": "error", "message": f"Dialog not found: {e}"}
    await client.edit_message(entity, 0, text)  # Telethon doesn't set per-chat drafts directly; store as self-draft workaround not ideal
    # Prefer using client(functions.messages.SaveDraftRequest(...)) for proper draft
    from telethon.tl.functions.messages import SaveDraftRequest
    await client(SaveDraftRequest(peer=entity, message=text))
    return {"status": "success", "draft_saved": True}

if __name__ == "__main__":
    # Telethon requires running within asyncio loop; FastMCP will manage tool calls
    mcp.run()
