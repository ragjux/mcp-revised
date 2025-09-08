#!/usr/bin/env python3
"""
Odoo MCP Server - FastMCP version
Implements: execute_method, search_employee, search_holidays, and resource-style handlers via XML-RPC.
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
import xmlrpc.client

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY = os.getenv("DRY_RUN", "0") == "1"

ODOO_URL = os.getenv("ODOO_URL", "").rstrip("/")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
ODOO_TIMEOUT = int(os.getenv("ODOO_TIMEOUT", "30"))

if not (ODOO_URL and ODOO_DB and ODOO_USERNAME and ODOO_PASSWORD):
    raise RuntimeError("Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD")

mcp = FastMCP("Odoo MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"odoo_{name}", "args": kwargs}

def _common():
    t = xmlrpc.client.Transport()
    t.timeout = ODOO_TIMEOUT
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", transport=t, allow_none=True)

def _models():
    t = xmlrpc.client.Transport()
    t.timeout = ODOO_TIMEOUT
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", transport=t, allow_none=True)

def _auth_uid() -> int:
    uid = _common().authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    if not uid:
        raise RuntimeError("Authentication failed")
    return uid

def _parse_domain(domain: Union[str, List, Dict]) -> List:
    # Accept list, JSON string of list, or {"conditions":[...]}
    if isinstance(domain, list):
        return domain
    if isinstance(domain, dict) and "conditions" in domain:
        return [[c["field"], c["operator"], c["value"]] for c in domain.get("conditions", [])]
    if isinstance(domain, str):
        try:
            obj = json.loads(domain)
            return _parse_domain(obj)
        except Exception:
            raise ValueError("Invalid domain string; must be JSON list or object with conditions")
    raise ValueError("Unsupported domain format")

def _parse_fields(fields: Union[str, List[str], None]) -> Optional[List[str]]:
    if fields is None:
        return None
    if isinstance(fields, list):
        return fields
    if isinstance(fields, str):
        try:
            arr = json.loads(fields)
            if isinstance(arr, list):
                return arr
        except Exception:
            # single field name
            return [fields]
    return None

# ---------- Tools ----------

@mcp.tool()
def odoo_execute_method(model: str, method: str, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a custom method on an Odoo model via execute_kw."""
    if DRY:
        return _dry("execute_method", model=model, method=method, args=args, kwargs=kwargs)
    uid = _auth_uid()
    res = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, method, args or [], kwargs or {})
    return {"success": True, "result": res}

@mcp.tool()
def odoo_search_employee(name: str, limit: int = 20) -> Dict[str, Any]:
    """Search for employees by name, returns ids and names."""
    if DRY:
        return _dry("search_employee", name=name, limit=limit)
    uid = _auth_uid()
    domain = [["name", "ilike", name]]
    ids = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "hr.employee", "search", [domain], {"limit": limit})
    records = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "hr.employee", "read", [ids], {"fields": ["name"]})
    return {"success": True, "employees": [{"id": r["id"], "name": r["name"]} for r in records]}

@mcp.tool()
def odoo_search_holidays(start_date: str, end_date: str, employee_id: Optional[int] = None) -> Dict[str, Any]:
    """Search leaves/holidays in date range, optionally filtered by employee_id."""
    if DRY:
        return _dry("search_holidays", start_date=start_date, end_date=end_date, employee_id=employee_id)
    uid = _auth_uid()
    domain = [["date_from", "<=", end_date], ["date_to", ">=", start_date]]
    if employee_id:
        domain.append(["employee_id", "=", employee_id])
    ids = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "hr.leave", "search", [domain])
    fields = ["name", "employee_id", "date_from", "date_to", "state", "holiday_status_id"]
    recs = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "hr.leave", "read", [ids], {"fields": fields})
    return {"success": True, "holidays": recs}

# ---------- Resource-style helpers ----------

@mcp.tool()
def odoo_list_models() -> Dict[str, Any]:
    """Resource: odoo://models - List models."""
    if DRY:
        return _dry("list_models")
    uid = _auth_uid()
    ids = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "ir.model", "search", [[["state", "=", "base"]]])
    fields = ["model", "name", "state"]
    recs = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, "ir.model", "read", [ids], {"fields": fields})
    return {"success": True, "models": recs}

@mcp.tool()
def odoo_get_model(model_name: str) -> Dict[str, Any]:
    """Resource: odoo://model/{model_name} - Get model fields metadata."""
    if DRY:
        return _dry("get_model", model_name=model_name)
    uid = _auth_uid()
    fields = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model_name, "fields_get", [[], ["string", "type", "required"]])
    return {"success": True, "model": model_name, "fields": fields}

@mcp.tool()
def odoo_get_record(model_name: str, record_id: int, fields: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """Resource: odoo://record/{model}/{id} - Get a single record by id."""
    if DRY:
        return _dry("get_record", model_name=model_name, record_id=record_id, fields=fields)
    uid = _auth_uid()
    flist = _parse_fields(fields)
    recs = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model_name, "read", [[record_id]], {"fields": flist} if flist else {})
    return {"success": True, "record": recs if recs else None}

@mcp.tool()
def odoo_search(model_name: str, domain: Union[str, List, Dict], limit: int = 10, offset: int = 0, fields: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """Resource: odoo://search/{model}/{domain} - Search by domain; supports list/object/json string formats."""
    if DRY:
        return _dry("search", model_name=model_name, domain=domain, limit=limit, offset=offset, fields=fields)
    uid = _auth_uid()
    d = _parse_domain(domain)
    ids = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model_name, "search", [d], {"limit": limit, "offset": offset})
    flist = _parse_fields(fields)
    recs = _models().execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model_name, "read", [ids], {"fields": flist} if flist else {})
    return {"success": True, "records": recs, "ids": ids}

if __name__ == "__main__":
    mcp.run()
