#!/usr/bin/env python3
"""
monday.com MCP Server - FastMCP version.
"""

import os
import json
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"monday_{name}", "args": kwargs}

TOKEN = os.getenv("MONDAY_API_TOKEN", "")
API_VERSION = os.getenv("MONDAY_API_VERSION", "")
READ_ONLY = os.getenv("MONDAY_READ_ONLY", "false").lower() == "true"

if not TOKEN:
    raise RuntimeError("Set MONDAY_API_TOKEN")

GQL_URL = "https://api.monday.com/v2"

mcp = FastMCP("monday.com MCP (native)")

def _headers() -> Dict[str, str]:
    h = {"Authorization": TOKEN, "Content-Type": "application/json"}
    if API_VERSION:
        h["Api-Version"] = API_VERSION
    return h

async def _graphql(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if DRY_RUN:
        return _dry("graphql", query=query, variables=variables)
    payload = {"query": query, "variables": variables or {}}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GQL_URL, headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()

# ========== Item Operations ========== [5][6]

@mcp.tool()
async def monday_create_item(board_id: int, group_id: str, item_name: str, column_values_json: Optional[str] = None) -> Dict[str, Any]:
    """Create a new item on a board. column_values_json is a JSON string per Monday docs."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("create_item", board_id=board_id, group_id=group_id, item_name=item_name, column_values_json=column_values_json)
    # column_values must be a JSON string [6]
    query = """
    mutation ($board_id: Int!, $group_id: String!, $item_name: String!, $column_values: JSON) {
      create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values) {
        id
        name
      }
    }"""
    vars = {"board_id": board_id, "group_id": group_id, "item_name": item_name}
    if column_values_json:
        vars["column_values"] = column_values_json
    return await _graphql(query, vars)

@mcp.tool()
async def monday_delete_item(item_id: int) -> Dict[str, Any]:
    """Delete an item permanently."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("delete_item", item_id=item_id)
    query = """
    mutation ($item_id: Int!) {
      delete_item (item_id: $item_id) {
        id
      }
    }"""
    return await _graphql(query, {"item_id": item_id})

@mcp.tool()
async def monday_get_board_items_by_name(board_id: int, term: str, limit: int = 25) -> Dict[str, Any]:
    """Search for items by board and term/name."""
    if DRY_RUN:
        return _dry("get_board_items_by_name", board_id=board_id, term=term, limit=limit)
    query = """
    query ($board_id: [Int], $term: String, $limit: Int) {
      items_page (query_params: {boards: $board_id, term: $term}, limit: $limit) {
        items { id name state updated_at }
      }
    }"""
    return await _graphql(query, {"board_id": [board_id], "term": term, "limit": limit})

@mcp.tool()
async def monday_create_update(item_id: int, body: str) -> Dict[str, Any]:
    """Add an update/comment to an item."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("create_update", item_id=item_id, body=body)
    query = """
    mutation ($item_id: Int!, $body: String!) {
      create_update (item_id: $item_id, body: $body) {
        id
        body
      }
    }"""
    return await _graphql(query, {"item_id": item_id, "body": body})

@mcp.tool()
async def monday_change_item_column_values(item_id: int, column_values_json: str) -> Dict[str, Any]:
    """Modify column values of an item. column_values_json must be JSON string."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("change_item_column_values", item_id=item_id, column_values_json=column_values_json)
    query = """
    mutation ($item_id: Int!, $column_values: JSON!) {
      change_multiple_column_values (item_id: $item_id, column_values: $column_values) {
        id
      }
    }"""
    return await _graphql(query, {"item_id": item_id, "column_values": column_values_json})

@mcp.tool()
async def monday_move_item_to_group(item_id: int, group_id: str) -> Dict[str, Any]:
    """Move item to a different group within the same board."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("move_item_to_group", item_id=item_id, group_id=group_id)
    query = """
    mutation ($item_id: Int!, $group_id: String!) {
      move_item_to_group (item_id: $item_id, group_id: $group_id) {
        id
      }
    }"""
    return await _graphql(query, {"item_id": item_id, "group_id": group_id})

# ========== Board Operations ========== [11][2]

@mcp.tool()
async def monday_create_board(board_name: str, board_kind: str = "public") -> Dict[str, Any]:
    """Create a new board with specified name and kind (public, private, share)."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("create_board", board_name=board_name, board_kind=board_kind)
    query = """
    mutation ($board_name: String!, $board_kind: BoardKind!) {
      create_board (board_name: $board_name, board_kind: $board_kind) {
        id
        name
        state
      }
    }"""
    return await _graphql(query, {"board_name": board_name, "board_kind": board_kind})

@mcp.tool()
async def monday_get_board_schema(board_id: int) -> Dict[str, Any]:
    """Retrieve columns and groups for a board."""
    if DRY_RUN:
        return _dry("get_board_schema", board_id=board_id)
    query = """
    query ($board_id: [Int]) {
      boards (ids: $board_id) {
        id
        name
        groups { id title }
        columns { id title type settings_str }
      }
    }"""
    return await _graphql(query, {"board_id": [board_id]})

@mcp.tool()
async def monday_create_column(board_id: int, title: str, column_type: str) -> Dict[str, Any]:
    """Add a new column to an existing board."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("create_column", board_id=board_id, title=title, column_type=column_type)
    query = """
    mutation ($board_id: Int!, $title: String!, $column_type: ColumnType!) {
      create_column(board_id: $board_id, title: $title, column_type: $column_type) {
        id
        title
        type
      }
    }"""
    return await _graphql(query, {"board_id": board_id, "title": title, "column_type": column_type})

@mcp.tool()
async def monday_delete_column(board_id: int, column_id: str) -> Dict[str, Any]:
    """Remove a column from a board."""
    if READ_ONLY:
        return {"status": "error", "message": "READ_ONLY mode enabled"}
    if DRY_RUN:
        return _dry("delete_column", board_id=board_id, column_id=column_id)
    query = """
    mutation ($board_id: Int!, $column_id: String!) {
      delete_column (board_id: $board_id, column_id: $column_id) {
        id
      }
    }"""
    return await _graphql(query, {"board_id": board_id, "column_id": column_id})

# ========== Account Operations (example) ==========

@mcp.tool()
async def monday_get_users_by_name(term: str, limit: int = 25) -> Dict[str, Any]:
    """Retrieve users by name or partial name."""
    if DRY_RUN:
        return _dry("get_users_by_name", term=term, limit=limit)
    query = """
    query ($term: String, $limit: Int) {
      users (kind: all, limit: $limit, query: $term) {
        id
        name
        email
      }
    }"""
    return await _graphql(query, {"term": term, "limit": limit})

# ========== Dynamic API Tools ========== [2][7]

@mcp.tool()
async def monday_all_monday_api(query: str, variables_json: Optional[str] = None) -> Dict[str, Any]:
    """Execute any GraphQL query or mutation. variables_json is a JSON string."""
    if READ_ONLY and "mutation" in query.replace(" ", "").lower():
        return {"status": "error", "message": "READ_ONLY mode enabled; mutations are blocked"}
    if DRY_RUN:
        return _dry("all_monday_api", query=query, variables_json=variables_json)
    variables = json.loads(variables_json) if variables_json else None
    return await _graphql(query, variables)

@mcp.tool()
async def monday_get_graphql_schema() -> Dict[str, Any]:
    """Fetch monday.com's GraphQL schema via introspection."""
    if DRY_RUN:
        return _dry("get_graphql_schema")
    introspection = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        types {
          kind name
          fields(includeDeprecated:true){ name args{ name type{ kind name ofType{ kind name } } } type{ kind name ofType{ kind name } } }
          inputFields{ name type{ kind name ofType{ kind name } } }
          interfaces{ name }
          enumValues(includeDeprecated:true){ name }
          possibleTypes{ name }
        }
      }
    }"""
    return await _graphql(introspection, None)

@mcp.tool()
async def monday_get_type_details(type_name: str) -> Dict[str, Any]:
    """Retrieve details about a specific GraphQL type."""
    if DRY_RUN:
        return _dry("get_type_details", type_name=type_name)
    q = """
    query ($name: String!) {
      __type(name: $name) {
        kind name
        fields(includeDeprecated:true){ name type{ kind name ofType{ kind name ofType{ kind name } } } }
        inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } }
        enumValues(includeDeprecated:true){ name }
        interfaces{ name }
        possibleTypes{ name }
      }
    }"""
    return await _graphql(q, {"name": type_name})

if __name__ == "__main__":
    mcp.run()
