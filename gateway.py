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
SERVICENOW_SERVER = str(BASE_DIR / "servers" / "Servicenow_mcp.py")
DISCORD_SERVER = str(BASE_DIR / "servers" / "Discord_mcp.py")
REDDIT_SERVER = str(BASE_DIR / "servers" / "Reddit_mcp.py")
BIGQUERY_SERVER = str(BASE_DIR / "servers" / "Bigquery_mcp.py")
GOOGLEMAPS_SERVER = str(BASE_DIR / "servers" / "Googlemaps_mcp.py")
JIRA_SERVER = str(BASE_DIR / "servers" / "Jira_mcp.py")
TELEGRAM_SERVER = str(BASE_DIR / "servers" / "Telegram_mcp.py")
SHOPIFY_SERVER = str(BASE_DIR / "servers" / "Shopify_mcp.py")
QUICKBOOKS_SERVER = str(BASE_DIR / "servers" / "Quickbooks_mcp.py")
TRELLO_SERVER = str(BASE_DIR / "servers" / "Trello_mcp.py")
STRIPE_SERVER = str(BASE_DIR / "servers" / "Stripe_mcp.py")
CLICKUP_SERVER = str(BASE_DIR / "servers" / "Clickup_mcp.py")
PIPEDRIVE_SERVER = str(BASE_DIR / "servers" / "Pipedrive_mcp.py")
CLAY_SERVER = str(BASE_DIR / "servers" / "Clay_mcp.py")
APOLLO_SERVER = str(BASE_DIR / "servers" / "Apollo.io_mcp.py")
DATABRICKS_SERVER = str(BASE_DIR / "servers" / "Databricks_mcp.py")
INTERCOM_SERVER = str(BASE_DIR / "servers" / "Intercom_mcp.py")
INSTANTLY_SERVER = str(BASE_DIR / "servers" / "Instantly_mcp.py")
YOUTUBE_ANALYTICS_SERVER = str(BASE_DIR / "servers" / "Youtube_analytics_mcp.py")
FACEBOOK_ADS_SERVER = str(BASE_DIR / "servers" / "Facebook_ads_mcp.py")
FIRECRAWL_SERVER = str(BASE_DIR / "servers" / "FireCrawl_mcp.py")
HYPERBROWSER_SERVER = str(BASE_DIR / "servers" / "HyperBrowser_mcp.py")
LINKEDIN_ADS_SERVER = str(BASE_DIR / "servers" / "LinkdinAds_mcp.py")
MAILCHIMP_SERVER = str(BASE_DIR / "servers" / "Mailchimp_mcp.py")
MONDAY_SERVER = str(BASE_DIR / "servers" / "Monday_mcpy.py")
MSWORD_SERVER = str(BASE_DIR / "servers" / "MSWord_mcp.py")
ODOO_SERVER = str(BASE_DIR / "servers" / "Odoo_mcp.py")
OUTLOOK_SERVER = str(BASE_DIR / "servers" / "Outlook_mcp.py")
TIKTOK_SERVER = str(BASE_DIR / "servers" / "TikTok_mcp.py")
TWITTER_ADS_SERVER = str(BASE_DIR / "servers" / "Twitterads_mcp.py")
WOCOMMERCE_SERVER = str(BASE_DIR / "servers" / "Woocommerce_mcp.py")
ZENDESK_SERVER = str(BASE_DIR / "servers" / "Zendesk_mcp.py")
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
                "ZOOM_ACCESS_TOKEN": os.environ.get("ZOOM_ACCESS_TOKEN", ""),
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
        "servicenow": {
            "command": PY,
            "args": [SERVICENOW_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SERVICENOW_INSTANCE_URL": os.environ.get("SERVICENOW_INSTANCE_URL", ""),
                "SERVICENOW_USERNAME": os.environ.get("SERVICENOW_USERNAME", ""),
                "SERVICENOW_PASSWORD": os.environ.get("SERVICENOW_PASSWORD", ""),
            },
        },
        "discord": {
            "command": PY,
            "args": [DISCORD_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "DISCORD_TOKEN": os.environ.get("DISCORD_TOKEN", ""),
                "DISCORD_GUILD_ID": os.environ.get("DISCORD_GUILD_ID", ""),
            },
        },
        "reddit": {
            "command": PY,
            "args": [REDDIT_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "REDDIT_CLIENT_ID": os.environ.get("REDDIT_CLIENT_ID", ""),
                "REDDIT_CLIENT_SECRET": os.environ.get("REDDIT_CLIENT_SECRET", ""),
                "REDDIT_USERNAME": os.environ.get("REDDIT_USERNAME", ""),
                "REDDIT_PASSWORD": os.environ.get("REDDIT_PASSWORD", ""),
                "REDDIT_USER_AGENT": os.environ.get("REDDIT_USER_AGENT", "reddit-mcp-fastmcp/1.0"),
            },
        },
        "bigquery": {
            "command": PY,
            "args": [BIGQUERY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                "BIGQUERY_PROJECT_ID": os.environ.get("BIGQUERY_PROJECT_ID", ""),
            },
        },
        "googlemaps": {
            "command": PY,
            "args": [GOOGLEMAPS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "GOOGLE_MAPS_API_KEY": os.environ.get("GOOGLE_MAPS_API_KEY", ""),
                "GOOGLE_MAPS_SCOPES": os.environ.get("GOOGLE_MAPS_SCOPES", "https://www.googleapis.com/auth/mapsplatform.places,https://www.googleapis.com/auth/mapsplatform.directions,https://www.googleapis.com/auth/mapsplatform.elevation"),
            },
        },
        "jira": {
            "command": PY,
            "args": [JIRA_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "JIRA_URL": os.environ.get("JIRA_URL", ""),
                "JIRA_EMAIL": os.environ.get("JIRA_EMAIL", ""),
                "JIRA_API_TOKEN": os.environ.get("JIRA_API_TOKEN", ""),
            },
        },
        "telegram": {
            "command": PY,
            "args": [TELEGRAM_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            },
        },
        "shopify": {
            "command": PY,
            "args": [SHOPIFY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "SHOPIFY_SHOP_DOMAIN": os.environ.get("SHOPIFY_SHOP_DOMAIN", ""),
                "SHOPIFY_ACCESS_TOKEN": os.environ.get("SHOPIFY_ACCESS_TOKEN", ""),
            },
        },
        "quickbooks": {
            "command": PY,
            "args": [QUICKBOOKS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "QUICKBOOKS_CLIENT_ID": os.environ.get("QUICKBOOKS_CLIENT_ID", ""),
                "QUICKBOOKS_CLIENT_SECRET": os.environ.get("QUICKBOOKS_CLIENT_SECRET", ""),
                "QUICKBOOKS_REFRESH_TOKEN": os.environ.get("QUICKBOOKS_REFRESH_TOKEN", ""),
                "QUICKBOOKS_REALM_ID": os.environ.get("QUICKBOOKS_REALM_ID", ""),
            },
        },
        "trello": {
            "command": PY,
            "args": [TRELLO_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "TRELLO_API_KEY": os.environ.get("TRELLO_API_KEY", ""),
                "TRELLO_API_TOKEN": os.environ.get("TRELLO_API_TOKEN", ""),
            },
        },
        "stripe": {
            "command": PY,
            "args": [STRIPE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", ""),
                "STRIPE_PUBLISHABLE_KEY": os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
            },
        },
        "clickup": {
            "command": PY,
            "args": [CLICKUP_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "CLICKUP_API_TOKEN": os.environ.get("CLICKUP_API_TOKEN", ""),
            },
        },
        "pipedrive": {
            "command": PY,
            "args": [PIPEDRIVE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "PIPEDRIVE_API_TOKEN": os.environ.get("PIPEDRIVE_API_TOKEN", ""),
            },
        },
        "clay": {
            "command": PY,
            "args": [CLAY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "CLAY_API_KEY": os.environ.get("CLAY_API_KEY", ""),
            },
        },
        "apollo": {
            "command": PY,
            "args": [APOLLO_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "APOLLO_API_KEY": os.environ.get("APOLLO_API_KEY", ""),
            },
        },
        "databricks": {
            "command": PY,
            "args": [DATABRICKS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST", ""),
                "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN", ""),
            },
        },
        "intercom": {
            "command": PY,
            "args": [INTERCOM_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "INTERCOM_ACCESS_TOKEN": os.environ.get("INTERCOM_ACCESS_TOKEN", ""),
            },
        },
        "instantly": {
            "command": PY,
            "args": [INSTANTLY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "INSTANTLY_API_KEY": os.environ.get("INSTANTLY_API_KEY", ""),
            },
        },
        "youtube_analytics": {
            "command": PY,
            "args": [YOUTUBE_ANALYTICS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "YOUTUBE_API_KEY": os.environ.get("YOUTUBE_API_KEY", ""),
                "YOUTUBE_CLIENT_ID": os.environ.get("YOUTUBE_CLIENT_ID", ""),
                "YOUTUBE_CLIENT_SECRET": os.environ.get("YOUTUBE_CLIENT_SECRET", ""),
                "YOUTUBE_REFRESH_TOKEN": os.environ.get("YOUTUBE_REFRESH_TOKEN", ""),
            },
        },
        "facebook_ads": {
            "command": PY,
            "args": [FACEBOOK_ADS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "FACEBOOK_ACCESS_TOKEN": os.environ.get("FACEBOOK_ACCESS_TOKEN", ""),
                "FACEBOOK_APP_ID": os.environ.get("FACEBOOK_APP_ID", ""),
                "FACEBOOK_APP_SECRET": os.environ.get("FACEBOOK_APP_SECRET", ""),
            },
        },
        "firecrawl": {
            "command": PY,
            "args": [FIRECRAWL_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "FIRECRAWL_API_KEY": os.environ.get("FIRECRAWL_API_KEY", ""),
            },
        },
        "hyperbrowser": {
            "command": PY,
            "args": [HYPERBROWSER_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "HYPERBROWSER_API_KEY": os.environ.get("HYPERBROWSER_API_KEY", ""),
            },
        },
        "linkedin_ads": {
            "command": PY,
            "args": [LINKEDIN_ADS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "LINKEDIN_ACCESS_TOKEN": os.environ.get("LINKEDIN_ACCESS_TOKEN", ""),
                "LINKEDIN_CLIENT_ID": os.environ.get("LINKEDIN_CLIENT_ID", ""),
                "LINKEDIN_CLIENT_SECRET": os.environ.get("LINKEDIN_CLIENT_SECRET", ""),
            },
        },
        "mailchimp": {
            "command": PY,
            "args": [MAILCHIMP_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "MAILCHIMP_API_KEY": os.environ.get("MAILCHIMP_API_KEY", ""),
                "MAILCHIMP_SERVER_PREFIX": os.environ.get("MAILCHIMP_SERVER_PREFIX", ""),
            },
        },
        "monday": {
            "command": PY,
            "args": [MONDAY_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "MONDAY_API_TOKEN": os.environ.get("MONDAY_API_TOKEN", ""),
            },
        },
        "msword": {
            "command": PY,
            "args": [MSWORD_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "MSWORD_CLIENT_ID": os.environ.get("MSWORD_CLIENT_ID", ""),
                "MSWORD_CLIENT_SECRET": os.environ.get("MSWORD_CLIENT_SECRET", ""),
                "MSWORD_TENANT_ID": os.environ.get("MSWORD_TENANT_ID", ""),
            },
        },
        "odoo": {
            "command": PY,
            "args": [ODOO_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "ODOO_URL": os.environ.get("ODOO_URL", ""),
                "ODOO_DATABASE": os.environ.get("ODOO_DATABASE", ""),
                "ODOO_USERNAME": os.environ.get("ODOO_USERNAME", ""),
                "ODOO_PASSWORD": os.environ.get("ODOO_PASSWORD", ""),
            },
        },
        "outlook": {
            "command": PY,
            "args": [OUTLOOK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "OUTLOOK_CLIENT_ID": os.environ.get("OUTLOOK_CLIENT_ID", ""),
                "OUTLOOK_CLIENT_SECRET": os.environ.get("OUTLOOK_CLIENT_SECRET", ""),
                "OUTLOOK_TENANT_ID": os.environ.get("OUTLOOK_TENANT_ID", ""),
            },
        },
        "tiktok": {
            "command": PY,
            "args": [TIKTOK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "TIKTOK_ACCESS_TOKEN": os.environ.get("TIKTOK_ACCESS_TOKEN", ""),
                "TIKTOK_APP_ID": os.environ.get("TIKTOK_APP_ID", ""),
                "TIKTOK_APP_SECRET": os.environ.get("TIKTOK_APP_SECRET", ""),
            },
        },
        "twitter_ads": {
            "command": PY,
            "args": [TWITTER_ADS_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "TWITTER_API_KEY": os.environ.get("TWITTER_API_KEY", ""),
                "TWITTER_API_SECRET": os.environ.get("TWITTER_API_SECRET", ""),
                "TWITTER_ACCESS_TOKEN": os.environ.get("TWITTER_ACCESS_TOKEN", ""),
                "TWITTER_ACCESS_TOKEN_SECRET": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
            },
        },
        "woocommerce": {
            "command": PY,
            "args": [WOCOMMERCE_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "WOOCOMMERCE_URL": os.environ.get("WOOCOMMERCE_URL", ""),
                "WOOCOMMERCE_CONSUMER_KEY": os.environ.get("WOOCOMMERCE_CONSUMER_KEY", ""),
                "WOOCOMMERCE_CONSUMER_SECRET": os.environ.get("WOOCOMMERCE_CONSUMER_SECRET", ""),
            },
        },
        "zendesk": {
            "command": PY,
            "args": [ZENDESK_SERVER],
            "transport": "stdio",
            "env": {
                "DRY_RUN": os.environ.get("DRY_RUN", "0"), "LOG_LEVEL": "INFO",
                "ZENDESK_SUBDOMAIN": os.environ.get("ZENDESK_SUBDOMAIN", ""),
                "ZENDESK_EMAIL": os.environ.get("ZENDESK_EMAIL", ""),
                "ZENDESK_TOKEN": os.environ.get("ZENDESK_TOKEN", ""),
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