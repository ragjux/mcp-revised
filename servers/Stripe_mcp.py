#!/usr/bin/env python3
"""
Stripe MCP Server - FastMCP version
Implements minimal tools for Payment Links, Products, and Prices, gated by env flags.
"""

import os
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
import stripe

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"stripe_{name}", "args": kwargs}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_ACCOUNT = os.getenv("STRIPE_ACCOUNT", "")

ENABLE_PAYMENT_LINKS_CREATE = os.getenv("STRIPE_ENABLE_PAYMENT_LINKS_CREATE", "false").lower() == "true"
ENABLE_PRODUCTS_CREATE = os.getenv("STRIPE_ENABLE_PRODUCTS_CREATE", "false").lower() == "true"
ENABLE_PRICES_CREATE = os.getenv("STRIPE_ENABLE_PRICES_CREATE", "false").lower() == "true"

if not STRIPE_SECRET_KEY:
    raise RuntimeError("Set STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_SECRET_KEY

mcp = FastMCP("Stripe MCP (native)")

def _request_opts() -> Dict[str, Any]:
    return {"stripe_account": STRIPE_ACCOUNT} if STRIPE_ACCOUNT else {}

# ---------- Payment Links ----------

@mcp.tool()
def stripe_payment_links_list(limit: int = 10) -> Dict[str, Any]:
    """List payment links."""
    if DRY_RUN:
        return _dry("payment_links_list", limit=limit)
    pls = stripe.PaymentLink.list(limit=limit, **_request_opts())
    return {"data": [pl.to_dict() for pl in pls.data], "has_more": pls.get("has_more", False)}

@mcp.tool()
def stripe_payment_links_create(price_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Create a payment link for a single line item."""
    if DRY_RUN:
        return _dry("payment_links_create", price_id=price_id, quantity=quantity)
    if not ENABLE_PAYMENT_LINKS_CREATE:
        return {"status": "error", "message": "payment_links.create not enabled by configuration"}
    pl = stripe.PaymentLink.create(
        line_items=[{"price": price_id, "quantity": quantity}],
        **_request_opts()
    )
    return {"payment_link": pl.to_dict()}

# ---------- Products ----------

@mcp.tool()
def stripe_products_list(limit: int = 10, active: Optional[bool] = None) -> Dict[str, Any]:
    """List products."""
    if DRY_RUN:
        return _dry("products_list", limit=limit, active=active)
    params: Dict[str, Any] = {"limit": limit}
    if active is not None:
        params["active"] = active
    prods = stripe.Product.list(**params, **_request_opts())
    return {"data": [p.to_dict() for p in prods.data], "has_more": prods.get("has_more", False)}

@mcp.tool()
def stripe_products_create(name: str, description: Optional[str] = None, active: Optional[bool] = True) -> Dict[str, Any]:
    """Create a product."""
    if DRY_RUN:
        return _dry("products_create", name=name, description=description, active=active)
    if not ENABLE_PRODUCTS_CREATE:
        return {"status": "error", "message": "products.create not enabled by configuration"}
    payload: Dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    if active is not None:
        payload["active"] = active
    prod = stripe.Product.create(**payload, **_request_opts())
    return {"product": prod.to_dict()}

# ---------- Prices ----------

@mcp.tool()
def stripe_prices_list(limit: int = 10, product: Optional[str] = None, active: Optional[bool] = None) -> Dict[str, Any]:
    """List prices, optionally by product."""
    if DRY_RUN:
        return _dry("prices_list", limit=limit, product=product, active=active)
    params: Dict[str, Any] = {"limit": limit}
    if product:
        params["product"] = product
    if active is not None:
        params["active"] = active
    prices = stripe.Price.list(**params, **_request_opts())
    return {"data": [p.to_dict() for p in prices.data], "has_more": prices.get("has_more", False)}

@mcp.tool()
def stripe_prices_create(
    product: str,
    unit_amount: int,
    currency: str = "usd",
    recurring_interval: Optional[str] = None
) -> Dict[str, Any]:
    """Create a price for a product; unit_amount in the smallest currency unit."""
    if DRY_RUN:
        return _dry("prices_create", product=product, unit_amount=unit_amount, currency=currency, recurring_interval=recurring_interval)
    if not ENABLE_PRICES_CREATE:
        return {"status": "error", "message": "prices.create not enabled by configuration"}
    payload: Dict[str, Any] = {
        "product": product,
        "unit_amount": unit_amount,
        "currency": currency
    }
    if recurring_interval:
        payload["recurring"] = {"interval": recurring_interval}
    price = stripe.Price.create(**payload, **_request_opts())
    return {"price": price.to_dict()}

if __name__ == "__main__":
    mcp.run()
