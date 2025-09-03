# gateway.py
import os, inspect, pathlib, sys, asyncio
from dotenv import load_dotenv
from fastmcp import FastMCP, Client

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent
WA_SERVER = str(BASE_DIR / "servers" / "meta_whatsapp_mcp.py")
GS_SERVER = str(BASE_DIR / "servers" / "google_sheets_mcp.py")
GSLIDES_SERVER = str(BASE_DIR / "servers" / "google_slide_mcp.py")
PY = sys.executable  # launch sub-servers with the same venv interpreter

MCP_CONFIG = {
    "mcpServers": {
        "whatsapp": {
            "command": PY,
            "args": [WA_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
                "META_WA_ACCESS_TOKEN": os.environ.get("META_WA_ACCESS_TOKEN", ""),
                "META_WA_PHONE_NUMBER_ID": os.environ.get("META_WA_PHONE_NUMBER_ID", ""),
                "META_WA_API_VERSION": os.environ.get("META_WA_API_VERSION", "v21.0"),
            },
        },
        "google_sheets_mcp": {
            "command": PY,
            "args": [GS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
                "GSHEETS_ACCESS_TOKEN": os.environ.get("GSHEETS_ACCESS_TOKEN", ""),
                "GSHEETS_REFRESH_TOKEN": os.environ.get("GSHEETS_REFRESH_TOKEN", ""),
            },
        },
        "google_slides_mcp": {
            "command": PY,
            "args": [GSLIDES_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
                "GSLIDES_ACCESS_TOKEN": os.environ.get("GSLIDES_ACCESS_TOKEN", ""),
                "GSLIDES_REFRESH_TOKEN": os.environ.get("GSLIDES_REFRESH_TOKEN", ""),
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
