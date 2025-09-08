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
WA_SERVER = str(BASE_DIR / "servers" / "meta_whatsapp_mcp.py")
GS_SERVER = str(BASE_DIR / "servers" / "google_sheets_mcp.py")
<<<<<<<<< Temporary merge branch 1
GSLIDES_SERVER = str(BASE_DIR / "servers" / "google_slide_mcp.py")
GFORMS_SERVER = str(BASE_DIR / "servers" / "google_form_mcp.py")
=========
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
>>>>>>>>> Temporary merge branch 2
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
    "apollo": str(BASE_DIR / "servers" / "Apollo.io_mcp.py"),
    "bigquery": str(BASE_DIR / "servers" / "Bigquery_mcp.py"),
    "clay": str(BASE_DIR / "servers" / "Clay_mcp.py"),
    "clickup": str(BASE_DIR / "servers" / "Clickup_mcp.py"),
    "databricks": str(BASE_DIR / "servers" / "Databricks_mcp.py"),
    "discord": str(BASE_DIR / "servers" / "Discord_mcp.py"),
    "facebook_ads": str(BASE_DIR / "servers" / "Facebook_ads_mcp.py"),
    "firecrawl": str(BASE_DIR / "servers" / "FireCrawl_mcp.py"),
    "googlemaps": str(BASE_DIR / "servers" / "Googlemaps_mcp.py"),
    "hyperbrowser": str(BASE_DIR / "servers" / "HyperBrowser_mcp.py"),
    "instantly": str(BASE_DIR / "servers" / "Instantly_mcp.py"),
    "intercom": str(BASE_DIR / "servers" / "Intercom_mcp.py"),
    "jira": str(BASE_DIR / "servers" / "Jira_mcp.py"),
    "linkedin_ads": str(BASE_DIR / "servers" / "LinkdinAds_mcp.py"),
    "mailchimp": str(BASE_DIR / "servers" / "Mailchimp_mcp.py"),
    "monday": str(BASE_DIR / "servers" / "Monday_mcpy.py"),
    "msword": str(BASE_DIR / "servers" / "MSWord_mcp.py"),
    "odoo": str(BASE_DIR / "servers" / "Odoo_mcp.py"),
    "outlook": str(BASE_DIR / "servers" / "Outlook_mcp.py"),
    "pipedrive": str(BASE_DIR / "servers" / "Pipedrive_mcp.py"),
    "quickbooks": str(BASE_DIR / "servers" / "Quickbooks_mcp.py"),
    "reddit": str(BASE_DIR / "servers" / "Reddit_mcp.py"),
    "servicenow": str(BASE_DIR / "servers" / "Servicenow_mcp.py"),
    "shopify": str(BASE_DIR / "servers" / "Shopify_mcp.py"),
    "stripe": str(BASE_DIR / "servers" / "Stripe_mcp.py"),
    "telegram": str(BASE_DIR / "servers" / "Telegram_mcp.py"),
    "tiktok": str(BASE_DIR / "servers" / "TikTok_mcp.py"),
    "trello": str(BASE_DIR / "servers" / "Trello_mcp.py"),
    "twitter_ads": str(BASE_DIR / "servers" / "Twitterads_mcp.py"),
    "woocommerce": str(BASE_DIR / "servers" / "Woocommerce_mcp.py"),
    "youtube_analytics": str(BASE_DIR / "servers" / "Youtube_analytics_mcp.py"),
    "zendesk": str(BASE_DIR / "servers" / "Zendesk_mcp.py"),
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
            "command": PY,
            "args": [WA_SERVER],
            "transport": "stdio",
            "env": {
<<<<<<<<< Temporary merge branch 1
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
=========
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
>>>>>>>>> Temporary merge branch 2
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
<<<<<<<<< Temporary merge branch 1
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
        "google_forms_mcp": {
            "command": PY,
            "args": [GFORMS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": "0", "LOG_LEVEL": "INFO",
                "GFORMS_ACCESS_TOKEN": os.environ.get("GFORMS_ACCESS_TOKEN", ""),
                "GFORMS_REFRESH_TOKEN": os.environ.get("GFORMS_REFRESH_TOKEN", ""),
=========
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_SHEETS_ACCESS_TOKEN": os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN", ""),
                "GOOGLE_SHEETS_REFRESH_TOKEN": os.environ.get("GOOGLE_SHEETS_REFRESH_TOKEN", ""),
            },
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
            "command": PY,
            "args": [CHAT_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_CHAT_ACCESS_TOKEN": os.environ.get("GOOGLE_CHAT_ACCESS_TOKEN", ""),
                "GOOGLE_CHAT_REFRESH_TOKEN": os.environ.get("GOOGLE_CHAT_REFRESH_TOKEN", ""),
            },
        },
        "drive": {
            "command": PY,
            "args": [DRIVE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_DRIVE_ACCESS_TOKEN": os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", ""),
                "GOOGLE_DRIVE_REFRESH_TOKEN": os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN", ""),
            },
        },
        "docs": {
            "command": PY,
            "args": [DOCS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_DOCS_ACCESS_TOKEN": os.environ.get("GOOGLE_DOCS_ACCESS_TOKEN", ""),
                "GOOGLE_DOCS_REFRESH_TOKEN": os.environ.get("GOOGLE_DOCS_REFRESH_TOKEN", ""),
            },
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
                "GOOGLE_ADS_TOKEN_PATH": os.environ.get("GOOGLE_ADS_TOKEN_PATH", "token.json"),
                "GOOGLE_ADS_CREDENTIALS_PATH": os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH", "credentials.json"),
                "GOOGLE_ADS_AUTH_TYPE": os.environ.get("GOOGLE_ADS_AUTH_TYPE", "service_account"),
                "GOOGLE_ADS_DEVELOPER_TOKEN": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
                "GOOGLE_ADS_LOGIN_CUSTOMER_ID": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
            },
        },
        "google_analytics": {
            "command": PY,
            "args": [GOOGLE_ANALYTICS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "TOKEN_PATH": os.environ.get("TOKEN_PATH", "token.json"),
                "CREDENTIALS_PATH": os.environ.get("CREDENTIALS_PATH", "credentials.json"),
            },
        },
        "google_task": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TOKEN_PATH": os.environ.get("TOKEN_PATH", "gcp-oauth.keys.json"),
            "CREDENTIALS_PATH": os.environ.get("CREDENTIALS_PATH", "credentials.json"),
        },
        "apollo": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "APOLLO_IO_API_KEY": os.environ.get("APOLLO_IO_API_KEY", ""),
        },
        "bigquery": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "BIGQUERY_AUTH_TYPE": os.environ.get("BIGQUERY_AUTH_TYPE", "service_account"),
            "BIGQUERY_CREDENTIALS_PATH": os.environ.get("BIGQUERY_CREDENTIALS_PATH", ""),
            "BIGQUERY_TOKEN_PATH": os.environ.get("BIGQUERY_TOKEN_PATH", "bq_token.json"),
            "BIGQUERY_PROJECT_ID": os.environ.get("BIGQUERY_PROJECT_ID", ""),
            "BIGQUERY_DATASET_ID": os.environ.get("BIGQUERY_DATASET_ID", ""),
        },
        "clay": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "CLAY_API_KEY": os.environ.get("CLAY_API_KEY", ""),
        },
        "clickup": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "CLICKUP_API_TOKEN": os.environ.get("CLICKUP_API_TOKEN", ""),
        },
        "databricks": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST", ""),
            "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN", ""),
        },
        "discord": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "DISCORD_TOKEN": os.environ.get("DISCORD_TOKEN", ""),
            "DISCORD_GUILD_ID": os.environ.get("DISCORD_GUILD_ID", ""),
        },
        "facebook_ads": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "FACEBOOK_ACCESS_TOKEN": os.environ.get("FACEBOOK_ACCESS_TOKEN", ""),
            "FACEBOOK_AD_ACCOUNT_ID": os.environ.get("FACEBOOK_AD_ACCOUNT_ID", ""),
        },
        "firecrawl": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", ""),
        },
        "googlemaps": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "GOOGLE_MAPS_API_KEY": os.environ.get("GOOGLE_MAPS_API_KEY", ""),
        },
        "hyperbrowser": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "HYPERBROWSER_API_KEY": os.environ.get("HYPERBROWSER_API_KEY", ""),
        },
        "instantly": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "INSTANTLY_API_KEY": os.environ.get("INSTANTLY_API_KEY", ""),
        },
        "intercom": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "INTERCOM_ACCESS_TOKEN": os.environ.get("INTERCOM_ACCESS_TOKEN", ""),
        },
        "jira": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "JIRA_HOST": os.environ.get("JIRA_HOST", ""),
            "JIRA_EMAIL": os.environ.get("JIRA_EMAIL", ""),
            "JIRA_API_TOKEN": os.environ.get("JIRA_API_TOKEN", ""),
        },
        "linkedin_ads": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "LINKEDIN_ADS_ACCESS_TOKEN": os.environ.get("LINKEDIN_ADS_ACCESS_TOKEN", ""),
            "LINKEDIN_ADS_ACCOUNT_ID": os.environ.get("LINKEDIN_ADS_ACCOUNT_ID", ""),
        },
        "mailchimp": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "MAILCHIMP_API_KEY": os.environ.get("MAILCHIMP_API_KEY", ""),
            "MAILCHIMP_SERVER_PREFIX": os.environ.get("MAILCHIMP_SERVER_PREFIX", ""),
        },
        "monday": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "MONDAY_API_TOKEN": os.environ.get("MONDAY_API_TOKEN", ""),
        },
        "msword": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "MSWORD_CLIENT_ID": os.environ.get("MSWORD_CLIENT_ID", ""),
            "MSWORD_CLIENT_SECRET": os.environ.get("MSWORD_CLIENT_SECRET", ""),
            "MSWORD_TENANT_ID": os.environ.get("MSWORD_TENANT_ID", ""),
        },
        "odoo": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "ODOO_URL": os.environ.get("ODOO_URL", ""),
            "ODOO_DATABASE": os.environ.get("ODOO_DATABASE", ""),
            "ODOO_USERNAME": os.environ.get("ODOO_USERNAME", ""),
            "ODOO_PASSWORD": os.environ.get("ODOO_PASSWORD", ""),
        },
        "outlook": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "OUTLOOK_CLIENT_ID": os.environ.get("OUTLOOK_CLIENT_ID", ""),
            "OUTLOOK_CLIENT_SECRET": os.environ.get("OUTLOOK_CLIENT_SECRET", ""),
            "OUTLOOK_TENANT_ID": os.environ.get("OUTLOOK_TENANT_ID", ""),
        },
        "pipedrive": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "PIPEDRIVE_API_TOKEN": os.environ.get("PIPEDRIVE_API_TOKEN", ""),
        },
        "quickbooks": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "QUICKBOOKS_CLIENT_ID": os.environ.get("QUICKBOOKS_CLIENT_ID", ""),
            "QUICKBOOKS_CLIENT_SECRET": os.environ.get("QUICKBOOKS_CLIENT_SECRET", ""),
            "QUICKBOOKS_REALM_ID": os.environ.get("QUICKBOOKS_REALM_ID", ""),
            "QUICKBOOKS_ACCESS_TOKEN": os.environ.get("QUICKBOOKS_ACCESS_TOKEN", ""),
            "QUICKBOOKS_REFRESH_TOKEN": os.environ.get("QUICKBOOKS_REFRESH_TOKEN", ""),
        },
        "reddit": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "REDDIT_CLIENT_ID": os.environ.get("REDDIT_CLIENT_ID", ""),
            "REDDIT_CLIENT_SECRET": os.environ.get("REDDIT_CLIENT_SECRET", ""),
            "REDDIT_USERNAME": os.environ.get("REDDIT_USERNAME", ""),
            "REDDIT_PASSWORD": os.environ.get("REDDIT_PASSWORD", ""),
        },
        "servicenow": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "SERVICENOW_INSTANCE": os.environ.get("SERVICENOW_INSTANCE", ""),
            "SERVICENOW_USERNAME": os.environ.get("SERVICENOW_USERNAME", ""),
            "SERVICENOW_PASSWORD": os.environ.get("SERVICENOW_PASSWORD", ""),
        },
        "shopify": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "SHOPIFY_ACCESS_TOKEN": os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
            "MYSHOPIFY_DOMAIN": os.environ.get("MYSHOPIFY_DOMAIN", ""),
        },
        "stripe": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", ""),
            "STRIPE_ACCOUNT": os.environ.get("STRIPE_ACCOUNT", ""),
        },
        "telegram": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TELEGRAM_API_ID": os.environ.get("TELEGRAM_API_ID", ""),
            "TELEGRAM_API_HASH": os.environ.get("TELEGRAM_API_HASH", ""),
            "TELEGRAM_PHONE": os.environ.get("TELEGRAM_PHONE", ""),
            "TELEGRAM_SESSION": os.environ.get("TELEGRAM_SESSION", "telegram.session"),
        },
        "tiktok": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TIKTOK_ACCESS_TOKEN": os.environ.get("TIKTOK_ACCESS_TOKEN", ""),
            "TIKTOK_ADVERTISER_ID": os.environ.get("TIKTOK_ADVERTISER_ID", ""),
        },
        "trello": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TRELLO_API_KEY": os.environ.get("TRELLO_API_KEY", ""),
            "TRELLO_TOKEN": os.environ.get("TRELLO_TOKEN", ""),
            "TRELLO_BOARD_ID": os.environ.get("TRELLO_BOARD_ID", ""),
            "TRELLO_WORKSPACE_ID": os.environ.get("TRELLO_WORKSPACE_ID", ""),
        },
        "twitter_ads": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "TWITTER_ADS_BEARER_TOKEN": os.environ.get("TWITTER_ADS_BEARER_TOKEN", ""),
            "TWITTER_ADS_ACCOUNT_ID": os.environ.get("TWITTER_ADS_ACCOUNT_ID", ""),
        },
        "woocommerce": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "WOOCOMMERCE_URL": os.environ.get("WOOCOMMERCE_URL", ""),
            "WOOCOMMERCE_CONSUMER_KEY": os.environ.get("WOOCOMMERCE_CONSUMER_KEY", ""),
            "WOOCOMMERCE_CONSUMER_SECRET": os.environ.get("WOOCOMMERCE_CONSUMER_SECRET", ""),
        },
        "youtube_analytics": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "YOUTUBE_ANALYTICS_CLIENT_ID": os.environ.get("YOUTUBE_ANALYTICS_CLIENT_ID", ""),
            "YOUTUBE_ANALYTICS_CLIENT_SECRET": os.environ.get("YOUTUBE_ANALYTICS_CLIENT_SECRET", ""),
            "YOUTUBE_ANALYTICS_REFRESH_TOKEN": os.environ.get("YOUTUBE_ANALYTICS_REFRESH_TOKEN", ""),
        },
        "zendesk": {
            "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
            "ZENDESK_EMAIL": os.environ.get("ZENDESK_EMAIL", ""),
            "ZENDESK_TOKEN": os.environ.get("ZENDESK_TOKEN", ""),
            "ZENDESK_SUBDOMAIN": os.environ.get("ZENDESK_SUBDOMAIN", ""),
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
        "apollo": ["APOLLO_IO_API_KEY"],
        "bigquery": ["BIGQUERY_PROJECT_ID"],
        "clay": ["CLAY_API_KEY"],
        "clickup": ["CLICKUP_API_TOKEN"],
        "databricks": ["DATABRICKS_HOST", "DATABRICKS_TOKEN"],
        "discord": ["DISCORD_TOKEN"],
        "facebook_ads": ["FACEBOOK_ACCESS_TOKEN"],
        "firecrawl": ["FIRECRAWL_API_KEY"],
        "googlemaps": ["GOOGLE_MAPS_API_KEY"],
        "hyperbrowser": ["HYPERBROWSER_API_KEY"],
        "instantly": ["INSTANTLY_API_KEY"],
        "intercom": ["INTERCOM_ACCESS_TOKEN"],
        "jira": ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN"],
        "linkedin_ads": ["LINKEDIN_ADS_ACCESS_TOKEN"],
        "mailchimp": ["MAILCHIMP_API_KEY"],
        "monday": ["MONDAY_API_TOKEN"],
        "msword": ["MSWORD_CLIENT_ID", "MSWORD_CLIENT_SECRET"],
        "odoo": ["ODOO_URL", "ODOO_USERNAME", "ODOO_PASSWORD"],
        "outlook": ["OUTLOOK_CLIENT_ID", "OUTLOOK_CLIENT_SECRET"],
        "pipedrive": ["PIPEDRIVE_API_TOKEN"],
        "quickbooks": ["QUICKBOOKS_CLIENT_ID", "QUICKBOOKS_CLIENT_SECRET"],
        "reddit": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
        "servicenow": ["SERVICENOW_INSTANCE", "SERVICENOW_USERNAME", "SERVICENOW_PASSWORD"],
        "shopify": ["SHOPIFY_ACCESS_TOKEN", "MYSHOPIFY_DOMAIN"],
        "stripe": ["STRIPE_SECRET_KEY"],
        "telegram": ["TELEGRAM_API_ID", "TELEGRAM_API_HASH"],
        "tiktok": ["TIKTOK_ACCESS_TOKEN"],
        "trello": ["TRELLO_API_KEY", "TRELLO_TOKEN"],
        "twitter_ads": ["TWITTER_ADS_BEARER_TOKEN"],
        "woocommerce": ["WOOCOMMERCE_URL", "WOOCOMMERCE_CONSUMER_KEY", "WOOCOMMERCE_CONSUMER_SECRET"],
        "youtube_analytics": ["YOUTUBE_ANALYTICS_CLIENT_ID", "YOUTUBE_ANALYTICS_CLIENT_SECRET"],
        "zendesk": ["ZENDESK_EMAIL", "ZENDESK_TOKEN", "ZENDESK_SUBDOMAIN"],
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