#!/usr/bin/env python3
"""
WooCommerce MCP Server - FastMCP version.
"""

import os
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
from base64 import b64encode

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "1"

SITE = os.getenv("WORDPRESS_SITE_URL", "").rstrip("/")
CK = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
CS = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")
WP_USER = os.getenv("WORDPRESS_USERNAME", "")
WP_PASS = os.getenv("WORDPRESS_PASSWORD", "")
QS_AUTH = os.getenv("WOO_QUERY_STRING_AUTH", "false").lower() == "true"

if not SITE or not CK or not CS:
    raise RuntimeError("Set WORDPRESS_SITE_URL, WOOCOMMERCE_CONSUMER_KEY, WOOCOMMERCE_CONSUMER_SECRET")

WC_BASE = f"{SITE}/wp-json/wc/v3"
WP_BASE = f"{SITE}/wp-json/wp/v2"

mcp = FastMCP("WooCommerce MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"woo_{name}", "args": kwargs}

def _wc_params(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = dict(params or {})
    if QS_AUTH:
        p["consumer_key"] = CK
        p["consumer_secret"] = CS
    return p

def _wc_headers() -> Dict[str, str]:
    if QS_AUTH:
        return {"Accept": "application/json", "Content-Type": "application/json"}
    token = b64encode(f"{CK}:{CS}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Accept": "application/json", "Content-Type": "application/json"}

def _wp_headers() -> Dict[str, str]:
    if WP_USER and WP_PASS:
        token = b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
        return {"Authorization": f"Basic {token}", "Accept": "application/json", "Content-Type": "application/json"}
    return {"Accept": "application/json", "Content-Type": "application/json"}

async def _req(method: str, url: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
    if DRY:
        return _dry("HTTP", method=method, url=url, params=params, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, params=params, json=json, headers=headers)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

# -------- WordPress Content -------- [4]

@mcp.tool()
async def wp_create_post(title: str, content: str, status: str = "publish") -> Dict[str, Any]:
    """Create a new WordPress post (requires WP_USER/WP_PASS)."""
    return await _req("POST", f"{WP_BASE}/posts", json={"title": title, "content": content, "status": status}, headers=_wp_headers())

@mcp.tool()
async def wp_get_posts(per_page: int = 10, page: int = 1) -> Dict[str, Any]:
    """Retrieve WordPress posts."""
    return await _req("GET", f"{WP_BASE}/posts", params={"per_page": per_page, "page": page}, headers=_wp_headers())

@mcp.tool()
async def wp_update_post(post_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update a WordPress post (fields dict)."""
    return await _req("POST", f"{WP_BASE}/posts/{post_id}", json=fields, headers=_wp_headers())

@mcp.tool()
async def wp_get_post_meta(post_id: int) -> Dict[str, Any]:
    """Get post meta (requires meta endpoints enabled or plugins)."""
    return await _req("GET", f"{WP_BASE}/posts/{post_id}/meta", headers=_wp_headers())

@mcp.tool()
async def wp_update_post_meta(post_id: int, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Update post meta dictionary (plugin-dependent)."""
    return await _req("POST", f"{WP_BASE}/posts/{post_id}/meta", json=meta, headers=_wp_headers())

# -------- WooCommerce: Products (sample; pattern repeats) -------- [2][4]

@mcp.tool()
async def wc_get_products(per_page: int = 10, page: int = 1, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve products with paging and optional filters (e.g., category, status)."""
    params = {"per_page": per_page, "page": page, **(filters or {})}
    return await _req("GET", f"{WC_BASE}/products", params=_wc_params(params), headers=_wc_headers())

@mcp.tool()
async def wc_get_product(product_id: int) -> Dict[str, Any]:
    """Get a single product by ID."""
    return await _req("GET", f"{WC_BASE}/products/{product_id}", params=_wc_params(), headers=_wc_headers())

@mcp.tool()
async def wc_create_product(productData: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new product."""
    return await _req("POST", f"{WC_BASE}/products", params=_wc_params(), json=productData, headers=_wc_headers())

@mcp.tool()
async def wc_update_product(product_id: int, productData: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing product."""
    return await _req("PUT", f"{WC_BASE}/products/{product_id}", params=_wc_params(), json=productData, headers=_wc_headers())

@mcp.tool()
async def wc_delete_product(product_id: int, force: bool = True) -> Dict[str, Any]:
    """Delete a product; force=true to bypass trash."""
    return await _req("DELETE", f"{WC_BASE}/products/{product_id}", params=_wc_params({"force": str(force).lower()}), headers=_wc_headers())

@mcp.tool()
async def wc_get_product_meta(product_id: int) -> Dict[str, Any]:
    """Get product meta via the product"""
