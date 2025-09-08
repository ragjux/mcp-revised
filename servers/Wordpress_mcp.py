#!/usr/bin/env python3
"""
WordPress MCP Server - FastMCP version
A Model Context Protocol (MCP) server for WordPress.
"""

import os
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"wordpress_{name}", "args": kwargs}

# Required environment variables:
# WP_SITE_URL: Base URL of your WordPress site (e.g. https://example.com)
# WP_USERNAME: WordPress username
# WP_APP_PASSWORD: WordPress application password (generated in WP admin)
WP_SITE_URL = os.getenv("WP_SITE_URL", "").rstrip("/")
WP_USERNAME = os.getenv("WP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

if not WP_SITE_URL or not WP_USERNAME or not WP_APP_PASSWORD:
    raise RuntimeError("Set WP_SITE_URL, WP_USERNAME, and WP_APP_PASSWORD environment variables")

mcp = FastMCP("WordPress MCP (native)")

def _auth_header() -> Dict[str, str]:
    token = httpx._models.utils.to_bytes(f"{WP_USERNAME}:{WP_APP_PASSWORD}")
    basic = httpx._auth._basic_auth_str(WP_USERNAME, WP_APP_PASSWORD)
    return {"Authorization": basic, "Content-Type": "application/json"}

async def _make_request(method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return {"dry_run": True, "method": method, "endpoint": endpoint, "json": json_data}
    url = f"{WP_SITE_URL}/wp-json{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(method, url, headers=_auth_header(), json=json_data)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def wordpress_get_posts(per_page: int = 10) -> Dict[str, Any]:
    """Fetch recent posts."""
    if DRY_RUN:
        return _dry("get_posts", per_page=per_page)
    data = await _make_request("GET", f"/wp/v2/posts?per_page={per_page}")
    return {"posts": data, "count": len(data)}

@mcp.tool()
async def wordpress_create_post(title: str, content: str, status: str = "draft") -> Dict[str, Any]:
    """Create a new post."""
    if DRY_RUN:
        return _dry("create_post", title=title, content=content, status=status)
    body = {"title": title, "content": content, "status": status}
    data = await _make_request("POST", "/wp/v2/posts", json_data=body)
    return {"status": "success", "post": data}

# Pages
@mcp.tool()
async def wordpress_get_pages(per_page: int = 10) -> Dict[str, Any]:
    """Fetch recent pages."""
    if DRY_RUN:
        return _dry("get_pages", per_page=per_page)
    data = await _make_request("GET", f"/wp/v2/pages?per_page={per_page}")
    return {"pages": data, "count": len(data)}

@mcp.tool()
async def wordpress_create_page(title: str, content: str, status: str = "draft") -> Dict[str, Any]:
    """Create a new page."""
    if DRY_RUN:
        return _dry("create_page", title=title, content=content, status=status)
    body = {"title": title, "content": content, "status": status}
    data = await _make_request("POST", "/wp/v2/pages", json_data=body)
    return {"status": "success", "page": data}


@mcp.tool()
async def wordpress_upload_media(file_url: str, filename: str) -> Dict[str, Any]:
    """Upload media from a URL."""
    if DRY_RUN:
        return _dry("upload_media", file_url=file_url, filename=filename)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(file_url)
        resp.raise_for_status()
        files = {"file": (filename, resp.content)}
        headers = _auth_header()
        headers.pop("Content-Type", None)
        r = await client.post(f"{WP_SITE_URL}/wp-json/wp/v2/media", files=files, headers=headers)
        r.raise_for_status()
        return r.json()

# WooCommerce Products
@mcp.tool()
async def wordpress_list_products(per_page: int = 10) -> Dict[str, Any]:
    """List WooCommerce products."""
    if DRY_RUN:
        return _dry("list_products", per_page=per_page)
    data = await _make_request("GET", f"/wc/v3/products?per_page={per_page}")
    return {"products": data, "count": len(data)}

@mcp.tool()
async def wordpress_create_product(name: str, regular_price: str) -> Dict[str, Any]:
    """Create a new WooCommerce product."""
    if DRY_RUN:
        return _dry("create_product", name=name, regular_price=regular_price)
    body = {"name": name, "regular_price": regular_price}
    data = await _make_request("POST", "/wc/v3/products", json_data=body)
    return {"status": "success", "product": data}

# System Info
@mcp.tool()
async def wordpress_get_status() -> Dict[str, Any]:
    """Get WordPress site status."""
    if DRY_RUN:
        return _dry("get_status")
    data = await _make_request("GET", "/")
    return {"status": "success", "data": data}

if __name__ == "__main__":
    mcp.run()
