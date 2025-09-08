#!/usr/bin/env python3
"""
X (Twitter) Ads MCP Server - FastMCP version (read-only parity)
Implements get_tables, get_columns, run_query analogs for Ads API objects.
"""

import os
import time
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
import httpx
import hmac, hashlib, base64, random, urllib.parse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"twitterads_{name}", "args": kwargs}

# Environment
CK = os.getenv("TWITTER_ADS_CONSUMER_KEY", "")
CS = os.getenv("TWITTER_ADS_CONSUMER_SECRET", "")
AT = os.getenv("TWITTER_ADS_ACCESS_TOKEN", "")
ATS = os.getenv("TWITTER_ADS_ACCESS_TOKEN_SECRET", "")
BEARER = os.getenv("TWITTER_ADS_BEARER_TOKEN", "")
ACCOUNT_ID = os.getenv("TWITTER_ADS_ACCOUNT_ID", "")

ADS_BASE = "https://ads-api.x.com/11"

if not ((CK and CS and AT and ATS) or BEARER):
    raise RuntimeError("Set OAuth 1.0a creds (TWITTER_ADS_CONSUMER_KEY/SECRET + ACCESS_TOKEN/SECRET) or TWITTER_ADS_BEARER_TOKEN")

mcp = FastMCP("Twitter Ads MCP (read-only)")

def _oauth1_header(method: str, url: str, params: Dict[str, Any]) -> str:
    oauth_params = {
        "oauth_consumer_key": CK,
        "oauth_nonce": "".join([str(random.randint(0, 9)) for _ in range(32)]),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": AT,
        "oauth_version": "1.0"
    }
    all_params = {**params, **oauth_params}
    # Percent-encode and sort
    def enc(x): return urllib.parse.quote(str(x), safe="~")
    base_param_str = "&".join(f"{enc(k)}={enc(all_params[k])}" for k in sorted(all_params))
    base_elems = [method.upper(), enc(url), enc(base_param_str)]
    base_str = "&".join(base_elems)
    signing_key = f"{enc(CS)}&{enc(ATS)}"
    sig = hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()
    oauth_params["oauth_signature"] = base64.b64encode(sig).decode()
    # Build header
    header_kv = ", ".join(f'{enc(k)}="{enc(v)}"' for k, v in oauth_params.items())
    return f"OAuth {header_kv}"

async def _ads_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{ADS_BASE}{path}"
    q = params.copy() if params else {}
    if DRY:
        return _dry("GET", url=url, params=q)
    headers = {}
    async with httpx.AsyncClient(timeout=60) as client:
        if BEARER:
            headers["Authorization"] = f"Bearer {BEARER}"
        else:
            headers["Authorization"] = _oauth1_header("GET", url, q)
        r = await client.get(url, headers=headers, params=q)
        r.raise_for_status()
        return r.json()

# "Tables" mapping: Ads API objects
TABLES = {
    "accounts": {"endpoint": "/accounts", "desc": "Ad accounts accessible to authorized user"},
    "campaigns": {"endpoint": "/accounts/{account_id}/campaigns", "desc": "Campaigns in ad account"},
    "line_items": {"endpoint": "/accounts/{account_id}/line_items", "desc": "Line items (ad groups)"},
    "promoted_tweets": {"endpoint": "/accounts/{account_id}/promoted_tweets", "desc": "Promoted Tweets"},
    "creatives_cards": {"endpoint": "/accounts/{account_id}/cards", "desc": "Cards/creatives"},
    "stats": {"endpoint": "/stats/jobs/accounts/{account_id}", "desc": "Async stats jobs metadata"},
}

COLUMNS = {
    "accounts": ["id", "name", "timezone", "created_at", "updated_at", "approval_status", "deleted"],
    "campaigns": ["id", "name", "entity_status", "objective", "daily_budget_amount_local_micro", "start_time", "end_time"],
    "line_items": ["id", "campaign_id", "name", "entity_status", "product_type", "placements", "objective"],
    "promoted_tweets": ["id", "tweet_id", "line_item_id", "paused"],
    "creatives_cards": ["id", "name", "card_type", "created_at", "updated_at"],
    "stats": ["id", "status", "url", "created_at", "updated_at"]
}

@mcp.tool()
async def twitterads_get_tables() -> Dict[str, Any]:
    """Retrieve list of available logical tables for Ads API."""
    return {"tables": [{"name": k, "description": v["desc"]} for k, v in TABLES.items()]}

@mcp.tool()
async def twitterads_get_columns(table: str) -> Dict[str, Any]:
    """Retrieve list of columns for a given logical table."""
    cols = COLUMNS.get(table)
    if not cols:
        return {"status": "error", "message": f"Unknown table '{table}'"}
    return {"table": table, "columns": cols}

@mcp.tool()
async def twitterads_run_query(table: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a read-only query mapped to Ads API GET.
    - For accounts, no account_id required.
    - For others, pass account_id in params or set TWITTER_ADS_ACCOUNT_ID.
    Additional filters can be passed through params.
    """
    params = params or {}
    meta = TABLES.get(table)
    if not meta:
        return {"status": "error", "message": f"Unknown table '{table}'"}
    endpoint = meta["endpoint"]
    acct = params.get("account_id") or ACCOUNT_ID
    if "{account_id}" in endpoint:
        if not acct:
            return {"status": "error", "message": "account_id required (or set TWITTER_ADS_ACCOUNT_ID)"}
        endpoint = endpoint.replace("{account_id}", acct)
    # Basic pagination params passthrough (count, cursor, etc.)
    data = await _ads_get(endpoint, params)
    return {"table": table, "endpoint": endpoint, "result": data}

if __name__ == "__main__":
    mcp.run()
