#!/usr/bin/env python3
"""
Airtable MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Airtable operations.
"""

import os
import httpx
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import re
import json
from datetime import datetime

import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"airtable_{name}", "args": kwargs}

AIRTABLE_TOKEN = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE = "https://api.airtable.com/v0"

if not AIRTABLE_TOKEN:
    raise RuntimeError("Set AIRTABLE_API_KEY environment variable")

mcp = FastMCP("Airtable MCP (native)")

def _auth_header() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

def _validate_base_id(base_id: str) -> str:
    """Validate Airtable base ID format."""
    if not base_id or not isinstance(base_id, str):
        raise ValueError("Base ID must be a non-empty string")
    
    base_pattern = re.compile(r'^app[a-zA-Z0-9]{14}$')
    if not base_pattern.match(base_id):
        raise ValueError("Invalid base ID format. Must be 'app' followed by 14 alphanumeric characters")
    
    return base_id

def _validate_table_id(table_id: str) -> str:
    """Validate Airtable table ID format."""
    if not table_id or not isinstance(table_id, str):
        raise ValueError("Table ID must be a non-empty string")
    
    table_pattern = re.compile(r'^tbl[a-zA-Z0-9]{14}$')
    if not table_pattern.match(table_id):
        raise ValueError("Invalid table ID format. Must be 'tbl' followed by 14 alphanumeric characters")
    
    return table_id

def _validate_max_records(max_records: int) -> int:
    """Validate max_records parameter."""
    if not isinstance(max_records, int):
        max_records = 100
    
    if max_records < 1:
        max_records = 1
    elif max_records > 1000:
        max_records = 1000
    
    return max_records

def _parse_date_filter(date_str: str) -> tuple:
    """Parse date strings like 'May 2024' or '2024-05' into date range."""
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    date_str_lower = date_str.lower().strip()
    
    # Try to parse "Month Year" format
    for month_name, month_num in months.items():
        if month_name in date_str_lower:
            year_str = date_str_lower.replace(month_name, '').strip()
            try:
                year = int(year_str)
                if year < 1900 or year > 2100:
                    raise ValueError(f"Year out of reasonable range: {year}")
                
                start_date = datetime(year, month_num, 1)
                # Get last day of month
                if month_num == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month_num + 1, 1)
                return start_date, end_date
            except ValueError:
                pass
    
    # Try ISO format YYYY-MM
    try:
        parts = date_str.split('-')
        if len(parts) == 2:
            year, month = int(parts[0]), int(parts[1])
            
            if year < 1900 or year > 2100:
                raise ValueError(f"Year out of reasonable range: {year}")
            if month < 1 or month > 12:
                raise ValueError(f"Month out of range: {month}")
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            return start_date, end_date
    except (ValueError, IndexError):
        pass
    
    # Default to current month if parsing fails
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1)
    else:
        end_date = datetime(now.year, now.month + 1, 1)
    
    return start_date, end_date

@mcp.tool()
def airtable_list_bases() -> Dict[str, Any]:
    """List all accessible Airtable bases."""
    if DRY_RUN:
        return _dry("list_bases")
    
    try:
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/meta/bases", headers=_auth_header())
            r.raise_for_status()
            data = r.json()
            
            bases = data.get("bases", [])
            return {"bases": bases, "count": len(bases)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list bases: {e}"}

@mcp.tool()
def airtable_list_tables(base_id: str) -> Dict[str, Any]:
    """List all tables in a specific base."""
    if DRY_RUN:
        return _dry("list_tables", base_id=base_id)
    
    try:
        validated_base_id = _validate_base_id(base_id)
        
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/meta/bases/{validated_base_id}/tables", headers=_auth_header())
            r.raise_for_status()
            data = r.json()
            
            tables = data.get("tables", [])
            return {"base_id": validated_base_id, "tables": tables, "count": len(tables)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list tables: {e}"}

@mcp.tool()
def airtable_search_records(
    base_id: str,
    table_id: str,
    filter_by_formula: Optional[str] = None,
    search_field: Optional[str] = None,
    search_value: Optional[str] = None,
    date_field: Optional[str] = None,
    date_range: Optional[str] = None,
    max_records: int = 100,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Search and filter records with advanced options."""
    if DRY_RUN:
        return _dry("search_records", base_id=base_id, table_id=table_id,
                   filter_by_formula=filter_by_formula, search_field=search_field,
                   search_value=search_value, date_field=date_field,
                   date_range=date_range, max_records=max_records, fields=fields)
    
    try:
        validated_base_id = _validate_base_id(base_id)
        validated_table_id = _validate_table_id(table_id)
        validated_max_records = _validate_max_records(max_records)
        
        # Build parameters
        params = {"maxRecords": validated_max_records}
        
        # Build filter formula
        formulas = []
        
        if filter_by_formula:
            formulas.append(filter_by_formula)
        
        if search_field and search_value:
            # Escape single quotes in search value
            escaped_value = search_value.replace("'", "''")
            formulas.append(f"FIND(LOWER('{escaped_value}'), LOWER({{{search_field}}}))")
        
        if date_field and date_range:
            start_date, end_date = _parse_date_filter(date_range)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            formulas.append(f"AND(IS_AFTER({{{date_field}}}, '{start_str}'), IS_BEFORE({{{date_field}}}, '{end_str}'))")
        
        if formulas:
            if len(formulas) == 1:
                params["filterByFormula"] = formulas[0]
            else:
                params["filterByFormula"] = f"AND({', '.join(formulas)})"
        
        if fields:
            params["fields[]"] = fields
        
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/{validated_base_id}/{validated_table_id}", 
                     headers=_auth_header(), params=params)
            r.raise_for_status()
            data = r.json()
            
            records = data.get("records", [])
            return {
                "base_id": validated_base_id,
                "table_id": validated_table_id,
                "records": records,
                "count": len(records)
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to search records: {e}"}

@mcp.tool()
def airtable_aggregate_records(
    base_id: str,
    table_id: str,
    operation: str,
    field: Optional[str] = None,
    filter_by_formula: Optional[str] = None,
    group_by: Optional[str] = None,
    date_field: Optional[str] = None,
    date_range: Optional[str] = None
) -> Dict[str, Any]:
    """Aggregate data with sum, count, average operations."""
    if DRY_RUN:
        return _dry("aggregate_records", base_id=base_id, table_id=table_id,
                   operation=operation, field=field, filter_by_formula=filter_by_formula,
                   group_by=group_by, date_field=date_field, date_range=date_range)
    
    try:
        validated_base_id = _validate_base_id(base_id)
        validated_table_id = _validate_table_id(table_id)
        
        valid_operations = {"sum", "count", "avg", "average", "min", "max"}
        if operation not in valid_operations:
            return {"status": "error", "message": f"Invalid operation: {operation}"}
        
        # Build parameters for fetching records
        params = {"maxRecords": 1000}
        
        formulas = []
        if filter_by_formula:
            formulas.append(filter_by_formula)
        
        if date_field and date_range:
            start_date, end_date = _parse_date_filter(date_range)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            formulas.append(f"AND(IS_AFTER({{{date_field}}}, '{start_str}'), IS_BEFORE({{{date_field}}}, '{end_str}'))")
        
        if formulas:
            if len(formulas) == 1:
                params["filterByFormula"] = formulas[0]
            else:
                params["filterByFormula"] = f"AND({', '.join(formulas)})"
        
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/{validated_base_id}/{validated_table_id}", 
                     headers=_auth_header(), params=params)
            r.raise_for_status()
            data = r.json()
            
            records = data.get("records", [])
            
            # Perform aggregation
            if group_by:
                # Group by field
                groups = {}
                for record in records:
                    group_value = record.get("fields", {}).get(group_by, "Unknown")
                    group_key = str(group_value) if group_value is not None else "Unknown"
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(record)
                
                # Aggregate by group
                results = {}
                for group_name, group_records in groups.items():
                    results[group_name] = _aggregate_records(group_records, operation, field)
                
                return {
                    "base_id": validated_base_id,
                    "table_id": validated_table_id,
                    "operation": operation,
                    "field": field,
                    "group_by": group_by,
                    "results": results,
                    "total_records": len(records)
                }
            else:
                # Single aggregation
                result = _aggregate_records(records, operation, field)
                return {
                    "base_id": validated_base_id,
                    "table_id": validated_table_id,
                    "operation": operation,
                    "field": field,
                    "result": result,
                    "total_records": len(records)
                }
    except Exception as e:
        return {"status": "error", "message": f"Failed to aggregate records: {e}"}

def _aggregate_records(records: List[Dict], operation: str, field: str) -> Any:
    """Helper function to aggregate records by operation."""
    if not records:
        return 0 if operation in ['sum', 'count'] else None
    
    if operation == 'count':
        return len(records)
    
    values = []
    for record in records:
        value = record.get("fields", {}).get(field)
        if value is not None:
            if isinstance(value, (int, float)):
                values.append(value)
            elif isinstance(value, str):
                try:
                    values.append(float(value))
                except ValueError:
                    pass
    
    if operation == 'sum':
        return sum(values)
    elif operation in ['avg', 'average']:
        return sum(values) / len(values) if values else 0
    elif operation == 'min':
        return min(values) if values else None
    elif operation == 'max':
        return max(values) if values else None
    
    return None

@mcp.tool()
def airtable_get_field_values(
    base_id: str,
    table_id: str,
    field: str,
    unique: bool = True
) -> Dict[str, Any]:
    """Get distinct values from a field."""
    if DRY_RUN:
        return _dry("get_field_values", base_id=base_id, table_id=table_id, 
                   field=field, unique=unique)
    
    try:
        validated_base_id = _validate_base_id(base_id)
        validated_table_id = _validate_table_id(table_id)
        
        params = {"maxRecords": 1000, "fields[]": [field]}
        
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/{validated_base_id}/{validated_table_id}", 
                     headers=_auth_header(), params=params)
            r.raise_for_status()
            data = r.json()
            
            records = data.get("records", [])
            values = []
            
            for record in records:
                value = record.get("fields", {}).get(field)
                if value is not None:
                    if isinstance(value, list):
                        values.extend(value)
                    else:
                        values.append(value)
            
            if unique:
                unique_values = list(set(str(v) for v in values))
                unique_values.sort()
                values = unique_values
            
            return {
                "base_id": validated_base_id,
                "table_id": validated_table_id,
                "field": field,
                "values": values,
                "count": len(values),
                "total_records": len(records)
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get field values: {e}"}

@mcp.tool()
def airtable_get_table_schema(base_id: str, table_id: str) -> Dict[str, Any]:
    """Get detailed schema information about a table."""
    if DRY_RUN:
        return _dry("get_table_schema", base_id=base_id, table_id=table_id)
    
    try:
        validated_base_id = _validate_base_id(base_id)
        validated_table_id = _validate_table_id(table_id)
        
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{AIRTABLE_BASE}/meta/bases/{validated_base_id}/tables", headers=_auth_header())
            r.raise_for_status()
            data = r.json()
            
            tables = data.get("tables", [])
            target_table = None
            
            for table in tables:
                if table.get("id") == validated_table_id:
                    target_table = table
                    break
            
            if not target_table:
                return {"status": "error", "message": f"Table {validated_table_id} not found"}
            
            return {
                "base_id": validated_base_id,
                "table_id": validated_table_id,
                "table": target_table
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get table schema: {e}"}

if __name__ == "__main__":
    mcp.run()