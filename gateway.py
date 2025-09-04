# gateway.py
import os, inspect, pathlib, sys, asyncio
from dotenv import load_dotenv
from fastmcp import FastMCP, Client

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent
WA_SERVER = str(BASE_DIR / "servers" / "meta_whatsapp_mcp.py")
GMAIL_SERVER = str(BASE_DIR / "servers" / "gmail_mcp.py")
CHAT_SERVER = str(BASE_DIR / "servers" / "google_chat_mcp.py")
DRIVE_SERVER = str(BASE_DIR / "servers" / "google_drive_mcp.py")
DOCS_SERVER = str(BASE_DIR / "servers" / "google_docs_mcp.py")
CALENDAR_SERVER = str(BASE_DIR / "servers" / "calender_mcp.py")
HUBSPOT_SERVER = str(BASE_DIR / "servers" / "hubspot_mcp.py")
SLACK_SERVER = str(BASE_DIR / "servers" / "slack_mcp.py")
AIRTABLE_SERVER = str(BASE_DIR / "servers" / "Airtable_mcp.py")
NOTION_SERVER = str(BASE_DIR / "servers" / "Notion_mcp.py")
WORDPRESS_SERVER = str(BASE_DIR / "servers" / "Wordpress_mcp.py")
CALENDLY_SERVER = str(BASE_DIR / "servers" / "calendly_mcp.py")
ASANA_SERVER = str(BASE_DIR / "servers" / "Asana_mcp.py")
FRESHDESK_SERVER = str(BASE_DIR / "servers" / "Freshdesk_mcp.py")
SALESFORCE_SERVER = str(BASE_DIR / "servers" / "Salesforce_mcp.py")
HYGEN_SERVER = str(BASE_DIR / "servers" / "Hygen_mcp.py")
SENDGRID_SERVER = str(BASE_DIR / "servers" / "Sendgrid_mcp.py")
ZOOM_SERVER = str(BASE_DIR / "servers" / "Zoom_mcp.py")
GOOGLE_ADS_SERVER = str(BASE_DIR / "servers" / "google_ads_mcp.py")
GOOGLE_ANALYTICS_SERVER = str(BASE_DIR / "servers" / "google_analytics_mcp.py")
GOOGLE_TASK_SERVER = str(BASE_DIR / "servers" / "google_task_mcp.py")
GS_SERVER = str(BASE_DIR / "servers" / "google_sheets_mcp.py")
GSLIDES_SERVER = str(BASE_DIR / "servers" / "google_slide_mcp.py")
GFORMS_SERVER = str(BASE_DIR / "servers" / "google_form_mcp.py")
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
                "GCHAT_ACCESS_TOKEN": os.environ.get("GCHAT_ACCESS_TOKEN", ""),
                "GCHAT_REFRESH_TOKEN": os.environ.get("GCHAT_REFRESH_TOKEN", ""),
            },
        },
        "drive": {
            "command": PY,
            "args": [DRIVE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GDRIVE_ACCESS_TOKEN": os.environ.get("GDRIVE_ACCESS_TOKEN", ""),
                "GDRIVE_REFRESH_TOKEN": os.environ.get("GDRIVE_REFRESH_TOKEN", ""),
            },
        },
        "docs": {
            "command": PY,
            "args": [DOCS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GDOCS_ACCESS_TOKEN": os.environ.get("GDOCS_ACCESS_TOKEN", ""),
                "GDOCS_REFRESH_TOKEN": os.environ.get("GDOCS_REFRESH_TOKEN", ""),
            },
        },
        "calendar": {
            "command": PY,
            "args": [CALENDAR_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_CALENDAR_ACCESS_TOKEN": os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN", ""),
                "GOOGLE_CALENDAR_REFRESH_TOKEN": os.environ.get("GOOGLE_CALENDAR_REFRESH_TOKEN", ""),
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
        "slack": {
            "command": PY,
            "args": [SLACK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN", ""),
            },
        },
        "airtable": {
            "command": PY,
            "args": [AIRTABLE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "AIRTABLE_API_KEY": os.environ.get("AIRTABLE_API_KEY", ""),
            },
        },
        "notion": {
            "command": PY,
            "args": [NOTION_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "NOTION_API_KEY": os.environ.get("NOTION_API_KEY", ""),
            },
        },
        "wordpress": {
            "command": PY,
            "args": [WORDPRESS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "WP_SITE_URL": os.environ.get("WP_SITE_URL", ""),
                "WP_USERNAME": os.environ.get("WP_USERNAME", ""),
                "WP_APP_PASSWORD": os.environ.get("WP_APP_PASSWORD", ""),
            },
        },
        "calendly": {
            "command": PY,
            "args": [CALENDLY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "CALENDLY_API_KEY": os.environ.get("CALENDLY_API_KEY", ""),
                "CALENDLY_ACCESS_TOKEN": os.environ.get("CALENDLY_ACCESS_TOKEN", ""),
                "CALENDLY_CLIENT_ID": os.environ.get("CALENDLY_CLIENT_ID", ""),
                "CALENDLY_CLIENT_SECRET": os.environ.get("CALENDLY_CLIENT_SECRET", ""),
                "CALENDLY_REFRESH_TOKEN": os.environ.get("CALENDLY_REFRESH_TOKEN", ""),
                "CALENDLY_USER_URI": os.environ.get("CALENDLY_USER_URI", ""),
                "CALENDLY_ORGANIZATION_URI": os.environ.get("CALENDLY_ORGANIZATION_URI", ""),
            },
        },
        "asana": {
            "command": PY,
            "args": [ASANA_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "ASANA_ACCESS_TOKEN": os.environ.get("ASANA_ACCESS_TOKEN", ""),
            },
        },
        "freshdesk": {
            "command": PY,
            "args": [FRESHDESK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "FRESHDESK_API_KEY": os.environ.get("FRESHDESK_API_KEY", ""),
                "FRESHDESK_DOMAIN": os.environ.get("FRESHDESK_DOMAIN", ""),
            },
        },
        "salesforce": {
            "command": PY,
            "args": [SALESFORCE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SALESFORCE_ENV": os.environ.get("SALESFORCE_ENV", "User_Password"),
                "SALESFORCE_USERNAME": os.environ.get("SALESFORCE_USERNAME", ""),
                "SALESFORCE_PASSWORD": os.environ.get("SALESFORCE_PASSWORD", ""),
                "SALESFORCE_TOKEN": os.environ.get("SALESFORCE_TOKEN", ""),
                "SALESFORCE_CLIENT_ID": os.environ.get("SALESFORCE_CLIENT_ID", ""),
                "SALESFORCE_CLIENT_SECRET": os.environ.get("SALESFORCE_CLIENT_SECRET", ""),
                "SALESFORCE_REFRESH_TOKEN": os.environ.get("SALESFORCE_REFRESH_TOKEN", ""),
                "SALESFORCE_INSTANCE_URL": os.environ.get("SALESFORCE_INSTANCE_URL", ""),
            },
        },
        "hygen": {
            "command": PY,
            "args": [HYGEN_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "HEYGEN_API_KEY": os.environ.get("HEYGEN_API_KEY", ""),
            },
        },
        "sendgrid": {
            "command": PY,
            "args": [SENDGRID_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY", ""),
                "FROM_EMAIL": os.environ.get("FROM_EMAIL", ""),
            },
        },
        "zoom": {
            "command": PY,
            "args": [ZOOM_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "ZOOM_API_KEY": os.environ.get("ZOOM_API_KEY", ""),
                "ZOOM_API_SECRET": os.environ.get("ZOOM_API_SECRET", ""),
                "ZOOM_ACCOUNT_ID": os.environ.get("ZOOM_ACCOUNT_ID", ""),
            },
        },
        "google_ads": {
            "command": PY,
            "args": [GOOGLE_ADS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GADS_TOKEN_PATH": os.environ.get("GADS_TOKEN_PATH", "token.json"),
                "GADS_CREDENTIALS_PATH": os.environ.get("GADS_CREDENTIALS_PATH", "credentials.json"),
                "GADS_AUTH_TYPE": os.environ.get("GADS_AUTH_TYPE", "service_account"),
                "GADS_DEVELOPER_TOKEN": os.environ.get("GADS_DEVELOPER_TOKEN", ""),
                "GADS_LOGIN_CUSTOMER_ID": os.environ.get("GADS_LOGIN_CUSTOMER_ID", ""),
            },
        },
        "google_analytics": {
            "command": PY,
            "args": [GOOGLE_ANALYTICS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GANALYTICS_TOKEN_PATH": os.environ.get("GANALYTICS_TOKEN_PATH", "token.json"),
                "GANALYTICS_CREDENTIALS_PATH": os.environ.get("GANALYTICS_CREDENTIALS_PATH", "credentials.json"),
            },
        },
        "google_task": {
            "command": PY,
            "args": [GOOGLE_TASK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GTASKS_TOKEN_PATH": os.environ.get("GTASKS_TOKEN_PATH", "gcp-oauth.keys.json"),
                "GTASKS_CREDENTIALS_PATH": os.environ.get("GTASKS_CREDENTIALS_PATH", "credentials.json"),
            },
        },
        "google_sheets": {
            "command": PY,
            "args": [GS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GSHEETS_ACCESS_TOKEN": os.environ.get("GSHEETS_ACCESS_TOKEN", ""),
                "GSHEETS_REFRESH_TOKEN": os.environ.get("GSHEETS_REFRESH_TOKEN", ""),
            },
        },
        "google_slides": {
            "command": PY,
            "args": [GSLIDES_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GSLIDES_ACCESS_TOKEN": os.environ.get("GSLIDES_ACCESS_TOKEN", ""),
                "GSLIDES_REFRESH_TOKEN": os.environ.get("GSLIDES_REFRESH_TOKEN", ""),
            },
        },
        "google_forms": {
            "command": PY,
            "args": [GFORMS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GFORMS_ACCESS_TOKEN": os.environ.get("GFORMS_ACCESS_TOKEN", ""),
                "GFORMS_REFRESH_TOKEN": os.environ.get("GFORMS_REFRESH_TOKEN", ""),
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