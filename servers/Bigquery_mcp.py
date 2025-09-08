#!/usr/bin/env python3
"""
Google BigQuery MCP Server - FastMCP version (read-only).
"""

import os
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import bigquery
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"bigquery_{name}", "args": kwargs}

# Auth options:
# BIGQUERY_AUTH_TYPE = service_account | oauth
# BIGQUERY_CREDENTIALS_PATH points to service account json (for service_account)
# or OAuth client secrets (for oauth). TOKEN_PATH stores user token (for oauth).
AUTH_TYPE = os.getenv("BIGQUERY_AUTH_TYPE", "service_account").lower()
CREDENTIALS_PATH = os.getenv("BIGQUERY_CREDENTIALS_PATH", "")
TOKEN_PATH = os.getenv("BIGQUERY_TOKEN_PATH", "bq_token.json")
PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "")  # required by BigQuery client
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "")  # optional default dataset

if not PROJECT_ID:
    raise RuntimeError("Set BIGQUERY_PROJECT_ID")

# Scopes needed for read-only querying
SCOPES = ["https://www.googleapis.com/auth/bigquery.readonly"]

mcp = FastMCP("BigQuery MCP (read-only)")

def _get_bq_client():
    if AUTH_TYPE == "service_account":
        if not CREDENTIALS_PATH:
            raise RuntimeError("Service account requires BIGQUERY_CREDENTIALS_PATH")
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    elif AUTH_TYPE == "oauth":
        creds: Optional[Credentials] = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_PATH:
                    raise RuntimeError("OAuth requires BIGQUERY_CREDENTIALS_PATH (client secrets)")
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
    else:
        raise RuntimeError(f"Unsupported BIGQUERY_AUTH_TYPE: {AUTH_TYPE}")
    return bigquery.Client(project=PROJECT_ID, credentials=creds)

@mcp.tool()
def bigquery_get_tables(dataset_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve list of tables in a dataset."""
    if DRY_RUN:
        return _dry("get_tables", dataset_id=dataset_id)
    try:
        client = _get_bq_client()
        ds = dataset_id or DATASET_ID
        if not ds:
            return {"status": "error", "message": "Dataset not specified (set BIGQUERY_DATASET_ID or pass dataset_id)"}
        tables_iter = client.list_tables(ds)
        tables = [{"table_id": t.table_id, "full_table_id": f"{t.project}.{t.dataset_id}.{t.table_id}"} for t in tables_iter]
        return {"dataset": ds, "tables": tables, "count": len(tables)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list tables: {e}"}

@mcp.tool()
def bigquery_get_columns(table: str, dataset_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve list of columns for a table."""
    if DRY_RUN:
        return _dry("get_columns", table=table, dataset_id=dataset_id)
    try:
        client = _get_bq_client()
        ds = dataset_id or DATASET_ID
        if not ds:
            return {"status": "error", "message": "Dataset not specified (set BIGQUERY_DATASET_ID or pass dataset_id)"}
        table_ref = f"{PROJECT_ID}.{ds}.{table}"
        tbl = client.get_table(table_ref)
        cols = [{"name": s.name, "type": s.field_type, "mode": s.mode, "description": s.description} for s in tbl.schema]
        return {"table": table_ref, "columns": cols, "count": len(cols)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get columns: {e}"}

@mcp.tool()
def bigquery_run_query(sql: str) -> Dict[str, Any]:
    """Execute a SQL SELECT query (read-only)."""
    if DRY_RUN:
        return _dry("run_query", sql=sql)
    try:
        client = _get_bq_client()
        job = client.query(sql)
        rows = list(job.result())
        # Convert to list of dicts
        results: List[Dict[str, Any]] = [dict(row) for row in rows]
        return {"rows": results, "count": len(results)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to run query: {e}"}

if __name__ == "__main__":
    mcp.run()
