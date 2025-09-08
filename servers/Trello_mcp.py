#!/usr/bin/env python3
"""
Trello MCP Server - FastMCP version.
"""

import os
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "true"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"trello_{name}", "args": kwargs}

API_KEY = os.getenv("TRELLO_API_KEY", "")
TOKEN = os.getenv("TRELLO_TOKEN", "")

DEFAULT_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
DEFAULT_WORKSPACE_ID = os.getenv("TRELLO_WORKSPACE_ID", "")

if not API_KEY or not TOKEN:
    raise RuntimeError("Set TRELLO_API_KEY and TRELLO_TOKEN")

BASE = "https://api.trello.com/1"

mcp = FastMCP("Trello MCP (native)")

def _auth(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = params.copy() if params else {}
    p["key"] = API_KEY
    p["token"] = TOKEN
    return p

async def _request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, path=path, params=params, json=json)
    url = f"{BASE}{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, params=_auth(params), json=json)
        r.raise_for_status()
        if r.text and r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return {"status": "success", "code": r.status_code}

def _board_id(bid: Optional[str]) -> str:
    return bid or DEFAULT_BOARD_ID

def _workspace_id(wid: Optional[str]) -> str:
    return wid or DEFAULT_WORKSPACE_ID

# ---------- Workspaces and Boards ----------

@mcp.tool()
async def trello_list_workspaces() -> Dict[str, Any]:
    """List all workspaces the user has access to."""
    return await _request("GET", "/members/me/organizations")

@mcp.tool()
async def trello_list_boards() -> Dict[str, Any]:
    """List all boards the user has access to."""
    return await _request("GET", "/members/me/boards", params={"fields": "name,shortUrl,idOrganization,closed"})

@mcp.tool()
async def trello_list_boards_in_workspace(workspaceId: Optional[str] = None) -> Dict[str, Any]:
    """List boards in a workspace."""
    wid = _workspace_id(workspaceId)
    if not wid:
        return {"status": "error", "message": "workspaceId not set and TRELLO_WORKSPACE_ID not configured"}
    return await _request("GET", f"/organizations/{wid}/boards", params={"fields": "name,shortUrl,closed"})

@mcp.tool()
async def trello_get_active_board_info(boardId: Optional[str] = None) -> Dict[str, Any]:
    """Get info for the active or specified board."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    return await _request("GET", f"/boards/{bid}", params={"fields": "name,url,prefs,closed"})

# State (active board/workspace) persistence is left to client or environment to match 'no new changes' directive.

# ---------- Lists and Cards ----------

@mcp.tool()
async def trello_get_lists(boardId: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve all lists from a board."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    return await _request("GET", f"/boards/{bid}/lists", params={"cards": "none", "fields": "name,closed"})

@mcp.tool()
async def trello_add_list_to_board(name: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Add a new list to a board."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    return await _request("POST", "/lists", params={"name": name, "idBoard": bid})

@mcp.tool()
async def trello_archive_list(listId: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Archive a list."""
    return await _request("PUT", f"/lists/{listId}/closed", params={"value": "true"})

@mcp.tool()
async def trello_get_cards_by_list_id(listId: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Fetch all cards from a list."""
    return await _request("GET", f"/lists/{listId}/cards", params={"fields": "name,desc,due,start,labels,idChecklists,idMembers,badges"})

@mcp.tool()
async def trello_add_card_to_list(listId: str, name: str, description: Optional[str] = None,
                                  dueDate: Optional[str] = None, start: Optional[str] = None,
                                  labels: Optional[List[str]] = None, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Add a new card to a list."""
    params: Dict[str, Any] = {"idList": listId, "name": name}
    if description is not None:
        params["desc"] = description
    if dueDate is not None:
        params["due"] = dueDate  # ISO8601 with time
    if start is not None:
        params["start"] = start  # YYYY-MM-DD per Trello rules
    if labels:
        params["idLabels"] = ",".join(labels)
    return await _request("POST", "/cards", params=params)

@mcp.tool()
async def trello_update_card_details(cardId: str, name: Optional[str] = None, description: Optional[str] = None,
                                     dueDate: Optional[str] = None, start: Optional[str] = None,
                                     dueComplete: Optional[bool] = None, labels: Optional[List[str]] = None,
                                     boardId: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing card's details."""
    params: Dict[str, Any] = {}
    if name is not None: params["name"] = name
    if description is not None: params["desc"] = description
    if dueDate is not None: params["due"] = dueDate
    if start is not None: params["start"] = start
    if dueComplete is not None: params["dueComplete"] = "true" if dueComplete else "false"
    if labels is not None: params["idLabels"] = ",".join(labels)
    return await _request("PUT", f"/cards/{cardId}", params=params)

@mcp.tool()
async def trello_archive_card(cardId: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Archive a card."""
    return await _request("PUT", f"/cards/{cardId}/closed", params={"value": "true"})

@mcp.tool()
async def trello_move_card(cardId: str, listId: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Move a card to a different list."""
    return await _request("PUT", f"/cards/{cardId}", params={"idList": listId})

@mcp.tool()
async def trello_attach_image_to_card(cardId: str, imageUrl: str, name: Optional[str] = None, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Attach an image by URL to a card."""
    params: Dict[str, Any] = {"url": imageUrl}
    if name: params["name"] = name
    return await _request("POST", f"/cards/{cardId}/attachments", params=params)

@mcp.tool()
async def trello_get_recent_activity(boardId: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Fetch recent actions on a board."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    return await _request("GET", f"/boards/{bid}/actions", params={"limit": limit})

@mcp.tool()
async def trello_get_my_cards() -> Dict[str, Any]:
    """Fetch cards assigned to the current token user."""
    return await _request("GET", "/members/me/cards", params={"fields": "name,idList,idBoard,labels,due"})

# ---------- Card details (comprehensive) ----------

@mcp.tool()
async def trello_get_card(cardId: str, includeMarkdown: bool = False) -> Dict[str, Any]:
    """Get comprehensive card data including checklists, attachments, labels, members, comments, badges."""
    params = {
        "fields": "name,desc,due,start,labels,badges,cover,idBoard,idList",
        "attachments": "true",
        "attachment_fields": "name,url,bytes,date,edgeColor,previews",
        "members": "true",
        "member_fields": "fullName,username,avatarUrl",
        "checklists": "all",
        "list": "true",
        "board": "true",
        "actions": "commentCard,updateCard:idList,addAttachmentToCard",
        "action_fields": "data,date,idMemberCreator"
    }
    card = await _request("GET", f"/cards/{cardId}", params=params)
    if includeMarkdown and isinstance(card, dict):
        md = [f"# {card.get('name','')}", ""]
        if card.get("desc"): md += ["## Description", card["desc"], ""]
        md += ["## Labels", ", ".join([lbl.get("name","") or lbl.get("color","") for lbl in card.get("labels", [])]) or "None", ""]
        md += ["## Due", str(card.get("due") or "None"), ""]
        if card.get("checklists"):
            md.append("## Checklists")
            for cl in card["checklists"]:
                md.append(f"- {cl.get('name','')}")
                for it in cl.get("checkItems", []):
                    mark = "x" if it.get("state") == "complete" else " "
                    md.append(f"  - [{mark}] {it.get('name','')}")
            md.append("")
        if card.get("attachments"):
            md.append("## Attachments")
            for att in card["attachments"]:
                md.append(f"- {att.get('name','file')} - {att.get('url','')}")
            md.append("")
        card["markdown"] = "\n".join(md)
    return card

# ---------- Checklist Suite ----------

async def _find_checklist_by_name_on_board(board_id: str, name: str) -> Optional[Dict[str, Any]]:
    # Trello does not provide board-level checklist search; scan cards on board
    cards = await _request("GET", f"/boards/{board_id}/cards", params={"fields": "name"})
    for c in cards:
        chks = await _request("GET", f"/cards/{c['id']}/checklists")
        for chk in chks:
            if chk.get("name") == name:
                return {"cardId": c["id"], "checklist": chk}
    return None

@mcp.tool()
async def trello_get_checklist_items(name: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve all items from any checklist by name (scans board cards)."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    found = await _find_checklist_by_name_on_board(bid, name)
    if not found:
        return {"status": "error", "message": "Checklist not found"}
    items = found["checklist"].get("checkItems", [])
    return {"boardId": bid, "cardId": found["cardId"], "items": items, "count": len(items)}

@mcp.tool()
async def trello_add_checklist_item(text: str, checkListName: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Add new item to an existing checklist by name."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    found = await _find_checklist_by_name_on_board(bid, checkListName)
    if not found:
        return {"status": "error", "message": "Checklist not found"}
    chk_id = found["checklist"]["id"]
    return await _request("POST", f"/checklists/{chk_id}/checkItems", params={"name": text})

@mcp.tool()
async def trello_find_checklist_items_by_description(description: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Search checklist items by text content across board."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    matches = []
    cards = await _request("GET", f"/boards/{bid}/cards", params={"fields": "name"})
    for c in cards:
        chks = await _request("GET", f"/cards/{c['id']}/checklists")
        for chk in chks:
            for it in chk.get("checkItems", []):
                if description.lower() in (it.get("name","").lower()):
                    matches.append({"cardId": c["id"], "checklistId": chk["id"], "item": it})
    return {"boardId": bid, "matches": matches, "count": len(matches)}

@mcp.tool()
async def trello_get_acceptance_criteria(boardId: Optional[str] = None) -> Dict[str, Any]:
    """Convenience: get items from 'Acceptance Criteria' checklists."""
    return await trello_get_checklist_items(name="Acceptance Criteria", boardId=boardId)

@mcp.tool()
async def trello_get_checklist_by_name(name: str, boardId: Optional[str] = None) -> Dict[str, Any]:
    """Get a complete checklist and completion percentage by name."""
    bid = _board_id(boardId)
    if not bid:
        return {"status": "error", "message": "boardId not set and TRELLO_BOARD_ID not configured"}
    found = await _find_checklist_by_name_on_board(bid, name)
    if not found:
        return {"status": "error", "message": "Checklist not found"}
    chk = found["checklist"]
    items = chk.get("checkItems", [])
    done = sum(1 for i in items if i.get("state") == "complete")
    pct = int((done / len(items)) * 100) if items else 0
    return {"boardId": bid, "cardId": found["cardId"], "checklist": chk, "percentComplete": pct}

if __name__ == "__main__":
    mcp.run()
