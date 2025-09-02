# gateway.py
import os, inspect, pathlib, sys, asyncio
from dotenv import load_dotenv
from fastmcp import FastMCP, Client

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent
WA_SERVER = str(BASE_DIR / "servers" / "meta_whatsapp_mcp.py")
GS_SERVER = str(BASE_DIR / "servers" / "google_sheets_mcp.py")
GMAIL_SERVER = str(BASE_DIR / "servers" / "gmail_mcp.py")
CHAT_SERVER = str(BASE_DIR / "servers" / "google_chat_mcp.py")
DRIVE_SERVER = str(BASE_DIR / "servers" / "google_drive_mcp.py")
DOCS_SERVER = str(BASE_DIR / "servers" / "google_docs_mcp.py")
CALENDAR_SERVER = str(BASE_DIR / "servers" / "calender_mcp.py")
HUBSPOT_SERVER = str(BASE_DIR / "servers" / "hubspot_mcp.py")
PY = sys.executable  # launch sub-servers with the same venv interpreter

MCP_CONFIG = {
    "mcpServers": {
        "whatsapp": {
            "command": PY,
            "args": [WA_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "META_WA_ACCESS_TOKEN": os.environ.get("META_WA_ACCESS_TOKEN", ""),
                "META_WA_PHONE_NUMBER_ID": os.environ.get("META_WA_PHONE_NUMBER_ID", ""),
                "META_WA_API_VERSION": os.environ.get("META_WA_API_VERSION", "v21.0"),
            },
        },
        "sheets": {
            "command": PY,
            "args": [GS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICE_ACCOUNT_PATH": os.environ.get("SERVICE_ACCOUNT_PATH", ""),
                "GOOGLE_SCOPES": os.environ.get("GOOGLE_SCOPES", ""),
                "GSUITE_DELEGATED_EMAIL": os.environ.get("GSUITE_DELEGATED_EMAIL", ""),
            },
        },
        "gmail": {
            "command": PY,
            "args": [GMAIL_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
                "SMTP_HOST": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                "SMTP_PORT": os.environ.get("SMTP_PORT", "587"),
                "IMAP_HOST": os.environ.get("IMAP_HOST", "imap.gmail.com"),
                "SMTP_USERNAME": os.environ.get("SMTP_USERNAME", ""),
                "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
            },
        },
        "chat": {
            "command": PY,
            "args": [CHAT_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICE_ACCOUNT_PATH": os.environ.get("SERVICE_ACCOUNT_PATH", ""),
                "GOOGLE_SCOPES": os.environ.get("GOOGLE_SCOPES", ""),
                "GSUITE_DELEGATED_EMAIL": os.environ.get("GSUITE_DELEGATED_EMAIL", ""),
            },
        },
        "drive": {
            "command": PY,
            "args": [DRIVE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICE_ACCOUNT_PATH": os.environ.get("SERVICE_ACCOUNT_PATH", ""),
                "GOOGLE_SCOPES": os.environ.get("GOOGLE_SCOPES", ""),
                "GSUITE_DELEGATED_EMAIL": os.environ.get("GSUITE_DELEGATED_EMAIL", ""),
            },
        },
        "docs": {
            "command": PY,
            "args": [DOCS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICE_ACCOUNT_PATH": os.environ.get("SERVICE_ACCOUNT_PATH", ""),
                "GOOGLE_SCOPES": os.environ.get("GOOGLE_SCOPES", ""),
                "GSUITE_DELEGATED_EMAIL": os.environ.get("GSUITE_DELEGATED_EMAIL", ""),
            },
        },
        "calendar": {
            "command": PY,
            "args": [CALENDAR_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICE_ACCOUNT_PATH": os.environ.get("SERVICE_ACCOUNT_PATH", ""),
                "GOOGLE_SCOPES": os.environ.get("GOOGLE_SCOPES", ""),
                "GSUITE_DELEGATED_EMAIL": os.environ.get("GSUITE_DELEGATED_EMAIL", ""),
            },
        },
        "hubspot": {
            "command": PY,
            "args": [HUBSPOT_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "HUBSPOT_ACCESS_TOKEN": os.environ.get("HUBSPOT_ACCESS_TOKEN", ""),
            },
        },
    }
}

def build_proxy_sync():
    """Create the composite proxy. If as_proxy is awaitable in your version,
    await it in a *temporary* event loop, then close that loop before run()."""
    client = Client(MCP_CONFIG)
    maybe_proxy = FastMCP.as_proxy(client, name="Unified Gateway")

    if inspect.isawaitable(maybe_proxy):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            proxy = loop.run_until_complete(maybe_proxy)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return proxy
    else:
        return maybe_proxy

if __name__ == "__main__":
    proxy = build_proxy_sync()
    proxy.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        path="/mcp",
    )
