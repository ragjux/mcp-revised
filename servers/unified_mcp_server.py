# servers/unified_mcp_server.py - Unified MCP Server with all tools
import os
from fastmcp import FastMCP

app = FastMCP("Unified MCP Server")

def register_all_tools():
    """Register all available tools based on environment variables"""
    
    # WhatsApp tools
    if os.getenv("META_WA_ACCESS_TOKEN") and os.getenv("META_WA_APP_NAME") and os.getenv("META_WA_FROM_NUMBER"):
        try:
            from meta_whatsapp_mcp import register_whatsapp_tools
            register_whatsapp_tools(app)
            print("✅ WhatsApp tools registered")
        except Exception as e:
            print(f"❌ Failed to register WhatsApp tools: {e}")
    
    # Google Sheets tools
    if os.getenv("GSHEETS_ACCESS_TOKEN") and os.getenv("GSHEETS_REFRESH_TOKEN"):
        try:
            from google_sheets_mcp import register_sheets_tools
            register_sheets_tools(app)
            print("✅ Google Sheets tools registered")
        except Exception as e:
            print(f"❌ Failed to register Google Sheets tools: {e}")
    
    # Gmail tools
    if os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"):
        try:
            from gmail_mcp import register_gmail_tools
            register_gmail_tools(app)
            print("✅ Gmail tools registered")
        except Exception as e:
            print(f"❌ Failed to register Gmail tools: {e}")
    
    # HubSpot tools
    if os.getenv("HUBSPOT_ACCESS_TOKEN"):
        try:
            from hubspot_mcp import register_hubspot_tools
            register_hubspot_tools(app)
            print("✅ HubSpot tools registered")
        except Exception as e:
            print(f"❌ Failed to register HubSpot tools: {e}")
    
    # Slack tools
    if os.getenv("SLACK_BOT_TOKEN"):
        try:
            from slack_mcp import register_slack_tools
            register_slack_tools(app)
            print("✅ Slack tools registered")
        except Exception as e:
            print(f"❌ Failed to register Slack tools: {e}")
    
    # Airtable tools
    if os.getenv("AIRTABLE_API_KEY"):
        try:
            from Airtable_mcp import register_airtable_tools
            register_airtable_tools(app)
            print("✅ Airtable tools registered")
        except Exception as e:
            print(f"❌ Failed to register Airtable tools: {e}")
    
    # Notion tools
    if os.getenv("NOTION_API_KEY"):
        try:
            from Notion_mcp import register_notion_tools
            register_notion_tools(app)
            print("✅ Notion tools registered")
        except Exception as e:
            print(f"❌ Failed to register Notion tools: {e}")
    
    # Asana tools
    if os.getenv("ASANA_ACCESS_TOKEN"):
        try:
            from Asana_mcp import register_asana_tools
            register_asana_tools(app)
            print("✅ Asana tools registered")
        except Exception as e:
            print(f"❌ Failed to register Asana tools: {e}")
    
    # Zoom tools
    if os.getenv("ZOOM_API_KEY") and os.getenv("ZOOM_API_SECRET") and os.getenv("ZOOM_ACCOUNT_ID"):
        try:
            from Zoom_mcp import register_zoom_tools
            register_zoom_tools(app)
            print("✅ Zoom tools registered")
        except Exception as e:
            print(f"❌ Failed to register Zoom tools: {e}")
    
    # Databricks tools
    if os.getenv("DATABRICKS_HOST") and os.getenv("DATABRICKS_TOKEN"):
        try:
            from Databricks_mcp import register_databricks_tools
            register_databricks_tools(app)
            print("✅ Databricks tools registered")
        except Exception as e:
            print(f"❌ Failed to register Databricks tools: {e}")
    
    # Discord tools
    if os.getenv("DISCORD_TOKEN"):
        try:
            from Discord_mcp import register_discord_tools
            register_discord_tools(app)
            print("✅ Discord tools registered")
        except Exception as e:
            print(f"❌ Failed to register Discord tools: {e}")
    
    # Firecrawl tools
    if os.getenv("FIRECRAWL_API_KEY"):
        try:
            from FireCrawl_mcp import register_firecrawl_tools
            register_firecrawl_tools(app)
            print("✅ Firecrawl tools registered")
        except Exception as e:
            print(f"❌ Failed to register Firecrawl tools: {e}")
    
    # Hyperbrowser tools
    if os.getenv("HYPERBROWSER_API_KEY"):
        try:
            from HyperBrowser_mcp import register_hyperbrowser_tools
            register_hyperbrowser_tools(app)
            print("✅ Hyperbrowser tools registered")
        except Exception as e:
            print(f"❌ Failed to register Hyperbrowser tools: {e}")
    
    # Reddit tools
    if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
        try:
            from Reddit_mcp import register_reddit_tools
            register_reddit_tools(app)
            print("✅ Reddit tools registered")
        except Exception as e:
            print(f"❌ Failed to register Reddit tools: {e}")
    
    # Zendesk tools
    if os.getenv("ZENDESK_EMAIL") and os.getenv("ZENDESK_TOKEN") and os.getenv("ZENDESK_SUBDOMAIN"):
        try:
            from Zendesk_mcp import register_zendesk_tools
            register_zendesk_tools(app)
            print("✅ Zendesk tools registered")
        except Exception as e:
            print(f"❌ Failed to register Zendesk tools: {e}")
    
    # CAPTCHA Solver tools
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from captcha_solver import register_captcha_tools
            register_captcha_tools(app)
            print("✅ CAPTCHA Solver tools registered")
        except Exception as e:
            print(f"❌ Failed to register CAPTCHA Solver tools: {e}")
    
    # Playwright tools (no API key required)
    try:
        from playwright_mcp import register_playwright_tools
        register_playwright_tools(app)
        print("✅ Playwright tools registered")
    except Exception as e:
        print(f"❌ Failed to register Playwright tools: {e}")

# Register all available tools
register_all_tools()

if __name__ == "__main__":
    app.run()
