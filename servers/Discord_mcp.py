#!/usr/bin/env python3
"""
Discord MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Discord.
"""

import os
import asyncio
import logging
from typing import Any, Dict, Optional, List

from fastmcp import FastMCP
from dotenv import load_dotenv

import discord
from discord import Intents, TextChannel, CategoryChannel, Forbidden, NotFound, HTTPException

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"discord_{name}", "args": kwargs}

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DEFAULT_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")

if not DISCORD_TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN environment variable")

mcp = FastMCP("Discord MCP (native)")

# ---- Discord client bootstrap ----
intents = Intents.default()
# Enable intents as needed to match tool coverage
intents.guilds = True
intents.members = True  # Requires Server Members Intent enabled in Developer Portal
intents.messages = True
intents.message_content = True  # Requires Message Content Intent enabled
intents.reactions = True
intents.dm_messages = True

discord_client = discord.Client(intents=intents)
ready_event = asyncio.Event()

@discord_client.event
async def on_ready():
    logging.info("Discord bot connected as %s", discord_client.user)
    ready_event.set()

async def ensure_ready():
    if not discord_client.is_ready():
        await ready_event.wait()

# Start discord client in background
_loop = asyncio.get_event_loop()
_loop.create_task(discord_client.start(DISCORD_TOKEN))

# ---- Helper functions ----

def _get_guild_id(guild_id: Optional[str]) -> Optional[int]:
    if guild_id:
        try:
            return int(guild_id)
        except ValueError:
            return None
    if DEFAULT_GUILD_ID:
        try:
            return int(DEFAULT_GUILD_ID)
        except ValueError:
            return None
    return None

async def _find_channel(guild: discord.Guild, name_or_id: str) -> Optional[TextChannel]:
    # Try by ID
    try:
        cid = int(name_or_id)
        ch = guild.get_channel(cid)
        if isinstance(ch, TextChannel):
            return ch
    except ValueError:
        pass
    # Try by name (first match)
    for ch in guild.text_channels:
        if ch.name == name_or_id:
            return ch
    return None

async def _find_category(guild: discord.Guild, name_or_id: str) -> Optional[CategoryChannel]:
    try:
        cid = int(name_or_id)
        cat = guild.get_channel(cid)
        if isinstance(cat, CategoryChannel):
            return cat
    except ValueError:
        pass
    for cat in guild.categories:
        if cat.name == name_or_id:
            return cat
    return None

async def _get_user_by_name(guild: discord.Guild, username: str) -> Optional[discord.Member]:
    # username can be name#discriminator or display name (limited)
    # Prefer exact match on name; iterate members (requires members intent)
    async for member in guild.fetch_members(limit=None):
        full = f"{member.name}#{member.discriminator}"
        if username == full or username == member.name or username == member.display_name:
            return member
    return None

# ---- Tools ----

@mcp.tool()
async def get_server_info(guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed Discord server information."""
    if DRY_RUN:
        return _dry("get_server_info", guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Bot not in the specified guild or guild not found"}
    data = {
        "id": guild.id,
        "name": guild.name,
        "member_count": guild.member_count,
        "owner_id": getattr(guild.owner_id, "real", guild.owner_id),
        "channels": [{"id": c.id, "name": c.name, "type": str(c.type)} for c in guild.channels],
    }
    return {"guild": data}

@mcp.tool()
async def get_user_id_by_name(username: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Get a user's ID by username in a guild (for ping usage <@id>)."""
    if DRY_RUN:
        return _dry("get_user_id_by_name", username=username, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    member = await _get_user_by_name(guild, username)
    if not member:
        return {"status": "error", "message": "User not found"}
    return {"user_id": str(member.id), "mention": f"<@{member.id}>"}

@mcp.tool()
async def send_private_message(user_id: str, content: str) -> Dict[str, Any]:
    """Send a private message to a specific user."""
    if DRY_RUN:
        return _dry("send_private_message", user_id=user_id, content=content)
    await ensure_ready()
    try:
        user = await discord_client.fetch_user(int(user_id))
        dm = await user.create_dm()
        msg = await dm.send(content)
        return {"status": "success", "message_id": str(msg.id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def read_private_messages(user_id: str, limit: int = 20) -> Dict[str, Any]:
    """Read recent direct messages with a specific user (bot's DM channel)."""
    if DRY_RUN:
        return _dry("read_private_messages", user_id=user_id, limit=limit)
    await ensure_ready()
    try:
        user = await discord_client.fetch_user(int(user_id))
        dm = await user.create_dm()
        messages = []
        async for m in dm.history(limit=limit):
            messages.append({"id": str(m.id), "author_id": str(m.author.id), "content": m.content, "created_at": m.created_at.isoformat()})
        messages.reverse()
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def send_message(channel: str, content: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Send a message to a specific channel (by name or ID)."""
    if DRY_RUN:
        return _dry("send_message", channel=channel, content=content, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    msg = await ch.send(content)
    return {"status": "success", "message_id": str(msg.id)}

@mcp.tool()
async def edit_message(channel: str, message_id: str, new_content: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Edit a message in a specific channel."""
    if DRY_RUN:
        return _dry("edit_message", channel=channel, message_id=message_id, new_content=new_content, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    try:
        msg = await ch.fetch_message(int(message_id))
        await msg.edit(content=new_content)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def delete_message(channel: str, message_id: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a message from a specific channel."""
    if DRY_RUN:
        return _dry("delete_message", channel=channel, message_id=message_id, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    try:
        msg = await ch.fetch_message(int(message_id))
        await msg.delete()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def read_messages(channel: str, limit: int = 50, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Read recent messages from a specific channel."""
    if DRY_RUN:
        return _dry("read_messages", channel=channel, limit=limit, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    msgs = []
    async for m in ch.history(limit=limit):
        msgs.append({"id": str(m.id), "author_id": str(m.author.id), "content": m.content, "created_at": m.created_at.isoformat()})
    msgs.reverse()
    return {"messages": msgs, "count": len(msgs)}

@mcp.tool()
async def add_reaction(channel: str, message_id: str, emoji: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Add a reaction to a message."""
    if DRY_RUN:
        return _dry("add_reaction", channel=channel, message_id=message_id, emoji=emoji, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    msg = await ch.fetch_message(int(message_id))
    await msg.add_reaction(emoji)
    return {"status": "success"}

@mcp.tool()
async def remove_reaction(channel: str, message_id: str, emoji: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Remove a specific reaction from a message."""
    if DRY_RUN:
        return _dry("remove_reaction", channel=channel, message_id=message_id, emoji=emoji, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    ch = await _find_channel(guild, channel) if guild else None
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    msg = await ch.fetch_message(int(message_id))
    await msg.clear_reaction(emoji)
    return {"status": "success"}

@mcp.tool()
async def create_text_channel(name: str, guild_id: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Create a text channel."""
    if DRY_RUN:
        return _dry("create_text_channel", name=name, guild_id=guild_id, category=category)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    if gid is None:
        return {"status": "error", "message": "Guild ID not provided and DISCORD_GUILD_ID not set"}
    guild = discord_client.get_guild(gid)
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    cat = await _find_category(guild, category) if category else None
    ch = await guild.create_text_channel(name=name, category=cat)
    return {"status": "success", "channel_id": str(ch.id), "name": ch.name}

@mcp.tool()
async def delete_channel(channel: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a channel."""
    if DRY_RUN:
        return _dry("delete_channel", channel=channel, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, channel)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    await ch.delete()
    return {"status": "success"}

@mcp.tool()
async def find_channel(name: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Find a channel by name and return type+ID."""
    if DRY_RUN:
        return _dry("find_channel", name=name, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    ch = await _find_channel(guild, name)
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    return {"id": str(ch.id), "name": ch.name, "type": str(ch.type)}

@mcp.tool()
async def list_channels(guild_id: Optional[str] = None) -> Dict[str, Any]:
    """List channels in a guild."""
    if DRY_RUN:
        return _dry("list_channels", guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    items = [{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in guild.channels]
    return {"channels": items, "count": len(items)}

@mcp.tool()
async def create_category(name: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a category."""
    if DRY_RUN:
        return _dry("create_category", name=name, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    cat = await guild.create_category(name=name)
    return {"status": "success", "category_id": str(cat.id), "name": cat.name}

@mcp.tool()
async def delete_category(category: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Delete a category."""
    if DRY_RUN:
        return _dry("delete_category", category=category, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    if not guild:
        return {"status": "error", "message": "Guild not found"}
    cat = await _find_category(guild, category)
    if not cat:
        return {"status": "error", "message": "Category not found"}
    await cat.delete()
    return {"status": "success"}

@mcp.tool()
async def list_channels_in_category(category: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """List channels within a category."""
    if DRY_RUN:
        return _dry("list_channels_in_category", category=category, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    cat = await _find_category(guild, category) if guild else None
    if not cat:
        return {"status": "error", "message": "Category not found"}
    items = [{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in cat.channels]
    return {"channels": items, "count": len(items)}

# Webhook management (basic)
@mcp.tool()
async def create_webhook(channel: str, name: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a webhook on a specific channel."""
    if DRY_RUN:
        return _dry("create_webhook", channel=channel, name=name, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    ch = await _find_channel(guild, channel) if guild else None
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    webhook = await ch.create_webhook(name=name)
    return {"status": "success", "webhook_id": str(webhook.id), "url": webhook.url}

@mcp.tool()
async def delete_webhook(webhook_id: str) -> Dict[str, Any]:
    """Delete a webhook."""
    if DRY_RUN:
        return _dry("delete_webhook", webhook_id=webhook_id)
    await ensure_ready()
    try:
        webhook = await discord.Webhook.from_url(f"https://discord.com/api/webhooks/{webhook_id}", client=discord_client)
        await webhook.delete()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def list_webhooks(channel: str, guild_id: Optional[str] = None) -> Dict[str, Any]:
    """List webhooks on a channel."""
    if DRY_RUN:
        return _dry("list_webhooks", channel=channel, guild_id=guild_id)
    await ensure_ready()
    gid = _get_guild_id(guild_id)
    guild = discord_client.get_guild(gid) if gid else None
    ch = await _find_channel(guild, channel) if guild else None
    if not ch:
        return {"status": "error", "message": "Channel not found"}
    hooks = await ch.webhooks()
    items = [{"id": str(w.id), "name": w.name, "url": w.url} for w in hooks]
    return {"webhooks": items, "count": len(items)}

@mcp.tool()
async def send_webhook_message(webhook_url: str, content: str) -> Dict[str, Any]:
    """Send a message via webhook URL."""
    if DRY_RUN:
        return _dry("send_webhook_message", webhook_url=webhook_url, content=content)
    await ensure_ready()
    try:
        webhook = discord.SyncWebhook.from_url(webhook_url)
        webhook.send(content)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()
