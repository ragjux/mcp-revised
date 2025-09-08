#!/usr/bin/env python3
"""
Shopify MCP Server - FastMCP version
"""

import os
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import httpx

# Load environment variables from .env file
load_dotenv()
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"shopify_{name}", "args": kwargs}

SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
MYSHOPIFY_DOMAIN = os.getenv("MYSHOPIFY_DOMAIN", "")

if not SHOPIFY_ACCESS_TOKEN or not MYSHOPIFY_DOMAIN:
    raise RuntimeError("Set SHOPIFY_ACCESS_TOKEN and MYSHOPIFY_DOMAIN environment variables")

GRAPHQL_URL = f"https://{MYSHOPIFY_DOMAIN}/admin/api/2024-07/graphql.json"

mcp = FastMCP("Shopify MCP (native)")

async def _graphql(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("graphql", query=query, variables=variables)
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables or {}})
        # Shopify returns 200 on GraphQL errors; parse JSON always
        data = resp.json()
        return data

# -------------------- Product Management --------------------

@mcp.tool()
async def shopify_get_products(searchTitle: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Get products or search by title."""
    if DRY_RUN:
        return _dry("get-products", searchTitle=searchTitle, limit=limit)
    # Use productConnection with query param for title
    query = """
    query ($first: Int!, $query: String) {
      products(first: $first, query: $query) {
        edges {
          node {
            id
            title
            status
            vendor
            productType
            tags
            createdAt
            updatedAt
          }
        }
      }
    }
    """
    q = None
    if searchTitle:
        # title filter syntax
        q = f'title:*{searchTitle}*'
    variables = {"first": int(limit), "query": q}
    data = await _graphql(query, variables)
    return data

@mcp.tool()
async def shopify_get_product_by_id(productId: str) -> Dict[str, Any]:
    """Get a specific product by global ID (gid://shopify/Product/...)."""
    if DRY_RUN:
        return _dry("get-product-by-id", productId=productId)
    query = """
    query ($id: ID!) {
      product(id: $id) {
        id
        title
        status
        vendor
        productType
        tags
        createdAt
        updatedAt
        variants(first: 50) {
          edges { node { id title sku price } }
        }
      }
    }
    """
    data = await _graphql(query, {"id": productId})
    return data

@mcp.tool()
async def shopify_createProduct(
    title: str,
    descriptionHtml: Optional[str] = None,
    vendor: Optional[str] = None,
    productType: Optional[str] = None,
    tags: Optional[str] = None,
    status: Optional[str] = "DRAFT"
) -> Dict[str, Any]:
    """Create a new product."""
    if DRY_RUN:
        return _dry("createProduct", title=title, descriptionHtml=descriptionHtml, vendor=vendor, productType=productType, tags=tags, status=status)
    mutation = """
    mutation ($input: ProductInput!) {
      productCreate(input: $input) {
        product { id title status }
        userErrors { field message }
      }
    }
    """
    input_obj: Dict[str, Any] = {"title": title}
    if descriptionHtml is not None: input_obj["descriptionHtml"] = descriptionHtml
    if vendor is not None: input_obj["vendor"] = vendor
    if productType is not None: input_obj["productType"] = productType
    if tags is not None: input_obj["tags"] = tags
    if status is not None: input_obj["status"] = status
    data = await _graphql(mutation, {"input": input_obj})
    return data

# -------------------- Customer Management --------------------

@mcp.tool()
async def shopify_get_customers(searchQuery: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Get customers or search by name/email."""
    if DRY_RUN:
        return _dry("get-customers", searchQuery=searchQuery, limit=limit)
    query = """
    query ($first: Int!, $query: String) {
      customers(first: $first, query: $query) {
        edges {
          node {
            id
            displayName
            email
            phone
            tags
            createdAt
            updatedAt
          }
        }
      }
    }
    """
    variables = {"first": int(limit), "query": searchQuery}
    data = await _graphql(query, variables)
    return data

@mcp.tool()
async def shopify_update_customer(
    id: str,
    firstName: Optional[str] = None,
    lastName: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    tags: Optional[List[str]] = None,
    note: Optional[str] = None,
    taxExempt: Optional[bool] = None,
    metafields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update a customer's fields."""
    if DRY_RUN:
        return _dry("update-customer", id=id, firstName=firstName, lastName=lastName, email=email, phone=phone, tags=tags, note=note, taxExempt=taxExempt, metafields=metafields)
    mutation = """
    mutation ($input: CustomerInput!) {
      customerUpdate(input: $input) {
        customer { id displayName email phone tags }
        userErrors { field message }
      }
    }
    """
    input_obj: Dict[str, Any] = {"id": id}
    if firstName is not None: input_obj["firstName"] = firstName
    if lastName is not None: input_obj["lastName"] = lastName
    if email is not None: input_obj["email"] = email
    if phone is not None: input_obj["phone"] = phone
    if tags is not None: input_obj["tags"] = tags
    if note is not None: input_obj["note"] = note
    if taxExempt is not None: input_obj["taxExempt"] = taxExempt
    if metafields is not None: input_obj["metafields"] = metafields
    data = await _graphql(mutation, {"input": input_obj})
    return data

@mcp.tool()
async def shopify_get_customer_orders(customerId: str, limit: int = 10) -> Dict[str, Any]:
    """Get orders for a specific numeric customer ID (coerce to gid)."""
    if DRY_RUN:
        return _dry("get-customer-orders", customerId=customerId, limit=limit)
    # Convert numeric ID to gid
    gid = f"gid://shopify/Customer/{customerId}"
    query = """
    query ($id: ID!, $first: Int!) {
      customer(id: $id) {
        id
        orders(first: $first) {
          edges {
            node {
              id
              name
              email
              processedAt
              tags
              totalPriceSet { shopMoney { amount currencyCode } }
              fulfillments { status }
            }
          }
        }
      }
    }
    """
    data = await _graphql(query, {"id": gid, "first": int(limit)})
    return data

# -------------------- Order Management --------------------

@mcp.tool()
async def shopify_get_orders(status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Get orders with optional filter by status."""
    if DRY_RUN:
        return _dry("get-orders", status=status, limit=limit)
    # Build query string for orders (e.g., status:open)
    q = None
    if status:
        q = f"status:{status}"
    query = """
    query ($first: Int!, $query: String) {
      orders(first: $first, query: $query) {
        edges {
          node {
            id
            name
            email
            processedAt
            tags
            displayFinancialStatus
            displayFulfillmentStatus
            totalPriceSet { shopMoney { amount currencyCode } }
          }
        }
      }
    }
    """
    data = await _graphql(query, {"first": int(limit), "query": q})
    return data

@mcp.tool()
async def shopify_get_order_by_id(orderId: str) -> Dict[str, Any]:
    """Get a specific order by global ID (gid://shopify/Order/...)."""
    if DRY_RUN:
        return _dry("get-order-by-id", orderId=orderId)
    query = """
    query ($id: ID!) {
      order(id: $id) {
        id
        name
        email
        processedAt
        tags
        displayFinancialStatus
        displayFulfillmentStatus
        totalPriceSet { shopMoney { amount currencyCode } }
        lineItems(first: 50) { edges { node { name quantity } } }
      }
    }
    """
    data = await _graphql(query, {"id": orderId})
    return data

@mcp.tool()
async def shopify_update_order(
    id: str,
    tags: Optional[List[str]] = None,
    email: Optional[str] = None,
    note: Optional[str] = None,
    customAttributes: Optional[List[Dict[str, Any]]] = None,
    metafields: Optional[List[Dict[str, Any]]] = None,
    shippingAddress: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update an order."""
    if DRY_RUN:
        return _dry("update-order", id=id, tags=tags, email=email, note=note, customAttributes=customAttributes, metafields=metafields, shippingAddress=shippingAddress)
    mutation = """
    mutation ($input: OrderInput!) {
      orderUpdate(input: $input) {
        order { id name email tags note }
        userErrors { field message }
      }
    }
    """
    input_obj: Dict[str, Any] = {"id": id}
    if tags is not None: input_obj["tags"] = tags
    if email is not None: input_obj["email"] = email
    if note is not None: input_obj["note"] = note
    if customAttributes is not None: input_obj["customAttributes"] = customAttributes
    if metafields is not None: input_obj["metafields"] = metafields
    if shippingAddress is not None: input_obj["shippingAddress"] = shippingAddress
    data = await _graphql(mutation, {"input": input_obj})
    return data

if __name__ == "__main__":
    mcp.run()
