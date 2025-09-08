import os, json, pathlib
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"whatsapp_{name}", "args": kwargs}

WA_TOKEN = os.getenv("META_WA_ACCESS_TOKEN", "")
WA_PHONE_NUMBER_ID = os.getenv("META_WA_PHONE_NUMBER_ID", "")
WA_API_VERSION = os.getenv("META_WA_API_VERSION", "v21.0")

if not (WA_TOKEN and WA_PHONE_NUMBER_ID):
    raise RuntimeError("Set META_WA_ACCESS_TOKEN and META_WA_PHONE_NUMBER_ID in the environment")

BASE = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}"
HEADERS_JSON = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}

mcp = FastMCP("Meta WhatsApp MCP")

def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=HEADERS_JSON, json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def wa_send_text(to: str, text: str, preview_url: bool = False) -> Dict[str, Any]:
    """Send a WhatsApp text message (Meta Cloud API /{PHONE_NUMBER_ID}/messages)."""
    if DRY_RUN:
        return _dry("wa_send_text", to=to, text=text, preview_url=preview_url)
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": preview_url, "body": text},
    }
    return _post_json(f"{BASE}/messages", payload)

@mcp.tool()
def wa_send_template(to: str, template_name: str, language: str = "en_US",
                     components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Send an approved template message."""
    if DRY_RUN:
        return _dry("wa_send_template", to=to, template_name=template_name, language=language, components=components)
    t = {"name": template_name, "language": {"code": language}}
    if components: t["components"] = components
    return _post_json(f"{BASE}/messages", {
        "messaging_product": "whatsapp", "to": to, "type": "template", "template": t
    })

@mcp.tool()
def wa_send_image_url(to: str, image_url: str, caption: str = "") -> Dict[str, Any]:
    """Send an image by URL."""
    if DRY_RUN:
        return _dry("wa_send_image_url", to=to, image_url=image_url, caption=caption)
    return _post_json(f"{BASE}/messages", {
        "messaging_product": "whatsapp", "to": to, "type": "image",
        "image": {"link": image_url, **({"caption": caption} if caption else {})}
    })

@mcp.tool()
def wa_send_document_url(to: str, doc_url: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Send a document by URL."""
    if DRY_RUN:
        return _dry("wa_send_document_url", to=to, doc_url=doc_url, filename=filename)
    doc = {"link": doc_url}
    if filename: doc["filename"] = filename
    return _post_json(f"{BASE}/messages", {
        "messaging_product": "whatsapp", "to": to, "type": "document", "document": doc
    })

@mcp.tool()
def wa_send_buttons(to: str, header_text: str, body_text: str,
                    buttons: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Send an interactive 'button' message.
    buttons: list of {id: 'btn1', title: 'Yes'} items (max 3).
    """
    if DRY_RUN:
        return _dry("wa_send_buttons", to=to, header_text=header_text, body_text=body_text, buttons=buttons)
    inter = {
        "type": "button",
        "header": {"type": "text", "text": header_text},
        "body": {"text": body_text},
        "action": {"buttons": [{"type":"reply","reply":b} for b in buttons]}
    }
    return _post_json(f"{BASE}/messages", {
        "messaging_product": "whatsapp", "to": to, "type": "interactive", "interactive": inter
    })

@mcp.tool()
def wa_mark_read(message_id: str) -> Dict[str, Any]:
    """Mark an inbound message as read (blue ticks)."""
    if DRY_RUN:
        return _dry("wa_mark_read", message_id=message_id)
    return _post_json(f"{BASE}/messages", {
        "messaging_product": "whatsapp", "status": "read", "message_id": message_id
    })

@mcp.tool()
def wa_upload_media(file_path: str, mime_type: str) -> Dict[str, Any]:
    """
    Upload media to Cloud API; returns media ID. Use the media ID in later messages.
    """
    if DRY_RUN:
        return _dry("wa_upload_media", file_path=file_path, mime_type=mime_type)
    p = pathlib.Path(file_path)
    if not p.exists(): raise FileNotFoundError(file_path)
    headers = {"Authorization": f"Bearer {WA_TOKEN}"}
    with httpx.Client(timeout=60) as c, p.open("rb") as f:
        r = c.post(f"{BASE}/media", headers=headers,
                   files={"file": (p.name, f, mime_type)})
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    mcp.run()
