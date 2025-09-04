# gateway.py
import os, inspect, pathlib, sys, asyncio, logging
from dotenv import load_dotenv
from fastmcp import FastMCP, Client

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration to override any existing logging setup
)
log = logging.getLogger("mcp-gateway")
log.setLevel(logging.INFO)

BASE_DIR = pathlib.Path(__file__).resolve().parent
PY = sys.executable  # launch sub-servers with the same venv interpreter

# Server file paths
SERVER_PATHS = {
    "whatsapp": str(BASE_DIR / "servers" / "meta_whatsapp_mcp.py"),
    "sheets": str(BASE_DIR / "servers" / "google_sheets_mcp.py"),
    "google_slides_mcp": str(BASE_DIR / "servers" / "google_slide_mcp.py"),
    "google_forms_mcp": str(BASE_DIR / "servers" / "google_form_mcp.py"),
    "gmail": str(BASE_DIR / "servers" / "gmail_mcp.py"),
    "chat": str(BASE_DIR / "servers" / "google_chat_mcp.py"),
    "drive": str(BASE_DIR / "servers" / "google_drive_mcp.py"),
    "docs": str(BASE_DIR / "servers" / "google_docs_mcp.py"),
    "calendar": str(BASE_DIR / "servers" / "calender_mcp.py"),
    "hubspot": str(BASE_DIR / "servers" / "hubspot_mcp.py"),
    "slack": str(BASE_DIR / "servers" / "slack_mcp.py"),
    "airtable": str(BASE_DIR / "servers" / "Airtable_mcp.py"),
    "notion": str(BASE_DIR / "servers" / "Notion_mcp.py"),
    "wordpress": str(BASE_DIR / "servers" / "Wordpress_mcp.py"),
    "calendly": str(BASE_DIR / "servers" / "calendly_mcp.py"),
    "asana": str(BASE_DIR / "servers" / "Asana_mcp.py"),
    "freshdesk": str(BASE_DIR / "servers" / "Freshdesk_mcp.py"),
    "salesforce": str(BASE_DIR / "servers" / "Salesforce_mcp.py"),
    "hygen": str(BASE_DIR / "servers" / "Hygen_mcp.py"),
    "sendgrid": str(BASE_DIR / "servers" / "Sendgrid_mcp.py"),
    "zoom": str(BASE_DIR / "servers" / "Zoom_mcp.py"),
    "google_ads": str(BASE_DIR / "servers" / "google_ads_mcp.py"),
    "google_analytics": str(BASE_DIR / "servers" / "google_analytics_mcp.py"),
    "google_task": str(BASE_DIR / "servers" / "google_task_mcp.py"),
}

def has_required_tokens(required_vars: list) -> bool:
    """Check if all required environment variables are set for a server"""
    log.debug(f"Checking required tokens: {required_vars}")
    for var in required_vars:
        if not os.getenv(var, "").strip():
            log.debug(f"Missing token: {var}")
            return False
    log.debug("All required tokens found")
    return True

def get_server_config(server_name: str) -> dict:
    """Generate MCP server configuration with environment variables"""
    log.debug(f"Getting configuration for server: {server_name}")
    server_path = SERVER_PATHS[server_name]
    
    # Define environment variables for each server
    server_envs = {
        "whatsapp": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "META_WA_ACCESS_TOKEN": os.environ.get("META_WA_ACCESS_TOKEN", ""),
            "META_WA_PHONE_NUMBER_ID": os.environ.get("META_WA_PHONE_NUMBER_ID", ""),
            "META_WA_API_VERSION": os.environ.get("META_WA_API_VERSION", "v21.0"),
        },
        "sheets": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_SHEETS_ACCESS_TOKEN": os.environ.get("GSHEETS_ACCESS_TOKEN", ""),
            "GOOGLE_SHEETS_REFRESH_TOKEN": os.environ.get("GSHEETS_REFRESH_TOKEN", ""),
        },
        "google_slides_mcp": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GSLIDES_ACCESS_TOKEN": os.environ.get("GSLIDES_ACCESS_TOKEN", ""),
            "GSLIDES_REFRESH_TOKEN": os.environ.get("GSLIDES_REFRESH_TOKEN", ""),
        },
        "google_forms_mcp": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GFORMS_ACCESS_TOKEN": os.environ.get("GFORMS_ACCESS_TOKEN", ""),
            "GFORMS_REFRESH_TOKEN": os.environ.get("GFORMS_REFRESH_TOKEN", ""),
        },
        "gmail": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "SMTP_HOST": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            "SMTP_PORT": os.environ.get("SMTP_PORT", "587"),
            "IMAP_HOST": os.environ.get("IMAP_HOST", "imap.gmail.com"),
            "SMTP_USERNAME": os.environ.get("SMTP_USERNAME", ""),
            "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
        },
        "chat": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_CHAT_ACCESS_TOKEN": os.environ.get("GOOGLE_CHAT_ACCESS_TOKEN", ""),
            "GOOGLE_CHAT_REFRESH_TOKEN": os.environ.get("GOOGLE_CHAT_REFRESH_TOKEN", ""),
        },
        "drive": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_DRIVE_ACCESS_TOKEN": os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", ""),
            "GOOGLE_DRIVE_REFRESH_TOKEN": os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN", ""),
        },
        "docs": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_DOCS_ACCESS_TOKEN": os.environ.get("GOOGLE_DOCS_ACCESS_TOKEN", ""),
            "GOOGLE_DOCS_REFRESH_TOKEN": os.environ.get("GOOGLE_DOCS_REFRESH_TOKEN", ""),
        },
        "calendar": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_CALENDAR_ACCESS_TOKEN": os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN", ""),
            "GOOGLE_CALENDAR_REFRESH_TOKEN": os.environ.get("GOOGLE_CALENDAR_REFRESH_TOKEN", ""),
        },
        "hubspot": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "HUBSPOT_ACCESS_TOKEN": os.environ.get("HUBSPOT_ACCESS_TOKEN", ""),
        },
        "slack": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN", ""),
        },
        "airtable": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "AIRTABLE_API_KEY": os.environ.get("AIRTABLE_API_KEY", ""),
        },
        "notion": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "NOTION_API_KEY": os.environ.get("NOTION_API_KEY", ""),
        },
        "wordpress": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "WP_SITE_URL": os.environ.get("WP_SITE_URL", ""),
            "WP_USERNAME": os.environ.get("WP_USERNAME", ""),
            "WP_APP_PASSWORD": os.environ.get("WP_APP_PASSWORD", ""),
        },
        "calendly": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "CALENDLY_API_KEY": os.environ.get("CALENDLY_API_KEY", ""),
            "CALENDLY_ACCESS_TOKEN": os.environ.get("CALENDLY_ACCESS_TOKEN", ""),
            "CALENDLY_CLIENT_ID": os.environ.get("CALENDLY_CLIENT_ID", ""),
            "CALENDLY_CLIENT_SECRET": os.environ.get("CALENDLY_CLIENT_SECRET", ""),
            "CALENDLY_REFRESH_TOKEN": os.environ.get("CALENDLY_REFRESH_TOKEN", ""),
            "CALENDLY_USER_URI": os.environ.get("CALENDLY_USER_URI", ""),
            "CALENDLY_ORGANIZATION_URI": os.environ.get("CALENDLY_ORGANIZATION_URI", ""),
        },
        "asana": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "ASANA_ACCESS_TOKEN": os.environ.get("ASANA_ACCESS_TOKEN", ""),
        },
        "freshdesk": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "FRESHDESK_API_KEY": os.environ.get("FRESHDESK_API_KEY", ""),
            "FRESHDESK_DOMAIN": os.environ.get("FRESHDESK_DOMAIN", ""),
        },
        "salesforce": {
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
        "hygen": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "HEYGEN_API_KEY": os.environ.get("HEYGEN_API_KEY", ""),
        },
        "sendgrid": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY", ""),
            "FROM_EMAIL": os.environ.get("FROM_EMAIL", ""),
        },
        "zoom": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "ZOOM_API_KEY": os.environ.get("ZOOM_API_KEY", ""),
            "ZOOM_API_SECRET": os.environ.get("ZOOM_API_SECRET", ""),
            "ZOOM_ACCOUNT_ID": os.environ.get("ZOOM_ACCOUNT_ID", ""),
        },
        "google_ads": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_ADS_TOKEN_PATH": os.environ.get("GOOGLE_ADS_TOKEN_PATH", "token.json"),
            "GOOGLE_ADS_CREDENTIALS_PATH": os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH", "credentials.json"),
            "GOOGLE_ADS_AUTH_TYPE": os.environ.get("GOOGLE_ADS_AUTH_TYPE", "service_account"),
            "GOOGLE_ADS_DEVELOPER_TOKEN": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
        },
        "google_analytics": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TOKEN_PATH": os.environ.get("TOKEN_PATH", "token.json"),
            "CREDENTIALS_PATH": os.environ.get("CREDENTIALS_PATH", "credentials.json"),
        },
        "google_task": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TOKEN_PATH": os.environ.get("TOKEN_PATH", "gcp-oauth.keys.json"),
            "CREDENTIALS_PATH": os.environ.get("CREDENTIALS_PATH", "credentials.json"),
        },
    }
    
    config = {
        "command": PY,
        "args": [server_path],
        "transport": "stdio",
        "env": server_envs[server_name]
    }
    log.debug(f"Generated config for {server_name}: {server_path}")
    return config

def build_mcp_config():
    """Build MCP configuration dynamically - only load servers with valid tokens"""
    log.info("🔍 Checking available MCP servers...")
    
    # Define server requirements (required environment variables for each server)
    server_requirements = {
        "whatsapp": ["META_WA_ACCESS_TOKEN", "META_WA_PHONE_NUMBER_ID"],
        "sheets": ["GSHEETS_ACCESS_TOKEN", "GSHEETS_REFRESH_TOKEN"],
        "google_slides_mcp": ["GSLIDES_ACCESS_TOKEN", "GSLIDES_REFRESH_TOKEN"],
        "google_forms_mcp": ["GFORMS_ACCESS_TOKEN"],
        "gmail": ["SMTP_USERNAME", "SMTP_PASSWORD"],
        "chat": ["GOOGLE_CHAT_ACCESS_TOKEN", "GOOGLE_CHAT_REFRESH_TOKEN"],
        "drive": ["GOOGLE_DRIVE_ACCESS_TOKEN", "GOOGLE_DRIVE_REFRESH_TOKEN"],
        "docs": ["GOOGLE_DOCS_ACCESS_TOKEN", "GOOGLE_DOCS_REFRESH_TOKEN"],
        "calendar": ["GOOGLE_CALENDAR_ACCESS_TOKEN", "GOOGLE_CALENDAR_REFRESH_TOKEN"],
        "hubspot": ["HUBSPOT_ACCESS_TOKEN"],
        "slack": ["SLACK_BOT_TOKEN"],
        "airtable": ["AIRTABLE_API_KEY"],
        "notion": ["NOTION_API_KEY"],
        "wordpress": ["WP_SITE_URL", "WP_USERNAME", "WP_APP_PASSWORD"],
        "calendly": ["CALENDLY_API_KEY", "CALENDLY_ACCESS_TOKEN"],
        "asana": ["ASANA_ACCESS_TOKEN"],
        "freshdesk": ["FRESHDESK_API_KEY", "FRESHDESK_DOMAIN"],
        "salesforce": ["SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_TOKEN", "SALESFORCE_INSTANCE_URL"],
        "hygen": ["HEYGEN_API_KEY"],
        "sendgrid": ["SENDGRID_API_KEY", "FROM_EMAIL"],
        "zoom": ["ZOOM_API_KEY", "ZOOM_API_SECRET", "ZOOM_ACCOUNT_ID"],
        "google_ads": ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "google_analytics": ["TOKEN_PATH", "CREDENTIALS_PATH"],
        "google_task": ["TOKEN_PATH", "CREDENTIALS_PATH"],
    }
    
    config = {"mcpServers": {}}
    loaded_count = 0
    skipped_count = 0
    
    # Only add servers with valid tokens
    for server_name, required_vars in server_requirements.items():
        if has_required_tokens(required_vars):
            config["mcpServers"][server_name] = get_server_config(server_name)
            log.info(f"✅ Loaded {server_name} server")
            loaded_count += 1
        else:
            log.info(f"⏭️  Skipped {server_name} server (missing tokens)")
            skipped_count += 1
    
    log.info(f"📊 Summary: {loaded_count} servers loaded, {skipped_count} servers skipped")
    log.info(f"🚀 Starting MCP Gateway with {loaded_count} active servers")
    
    return config

def build_proxy_sync():
    """Create the MCP proxy with dynamic configuration and handle async/sync creation"""
    log.info("Building MCP proxy...")
    
    # Build dynamic configuration based on available tokens
    mcp_config = build_mcp_config()
    
    # Check if any servers are available
    if not mcp_config["mcpServers"]:
        log.error("❌ No MCP servers available! Please check your environment variables.")
        log.error("💡 Make sure to set the required tokens in your .env file.")
        sys.exit(1)
    
    log.info("Creating MCP client...")
    client = Client(mcp_config)
    log.info("Creating FastMCP proxy...")
    maybe_proxy = FastMCP.as_proxy(client, name="Unified Gateway")

    if inspect.isawaitable(maybe_proxy):
        log.info("Proxy is awaitable, creating event loop...")
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            proxy = loop.run_until_complete(maybe_proxy)
            log.info("Proxy created successfully via event loop")
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return proxy
    else:
        log.info("Proxy created successfully (synchronous)")
        return maybe_proxy

if __name__ == "__main__":
    """Start the MCP Gateway with dynamic server loading"""
    log.info("Starting MCP Gateway...")
    try:
        proxy = build_proxy_sync()
        port = int(os.getenv("PORT", "8080"))
        log.info(f"Starting server on port {port}...")
        proxy.run(
            transport="http",
            host="0.0.0.0",
            port=port,
            path="/mcp",
        )
    except Exception as e:
        log.error(f"Failed to start MCP Gateway: {e}")
        sys.exit(1)