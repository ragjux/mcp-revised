#!/usr/bin/env python3
"""
Databricks MCP Server - FastMCP version
"""

import os
from typing import Any, Dict, Optional, List
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
import base64

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"databricks_{name}", "args": kwargs}

HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
TOKEN = os.getenv("DATABRICKS_TOKEN", "")

if not HOST or not TOKEN:
    raise RuntimeError("Set DATABRICKS_HOST and DATABRICKS_TOKEN")

# Base paths (workspace-level APIs)
API = f"{HOST}/api/2.0"
SQL_API = f"{HOST}/api/2.0/sql/statements"

mcp = FastMCP("Databricks MCP (native)")

def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

async def _request(method: str, url: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None):
    if DRY_RUN:
        return _dry(method, url=url, params=params, json=json)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=_headers(), params=params, json=json)
        r.raise_for_status()
        return r.json() if r.text else {"status": "success"}

# -------- Clusters -------- [10]

@mcp.tool()
async def databricks_list_clusters() -> Dict[str, Any]:
    """List all Databricks clusters."""
    return await _request("GET", f"{API}/clusters/list")

@mcp.tool()
async def databricks_get_cluster(cluster_id: str) -> Dict[str, Any]:
    """Get information about a specific cluster."""
    return await _request("GET", f"{API}/clusters/get", params={"cluster_id": cluster_id})

@mcp.tool()
async def databricks_create_cluster(
    cluster_name: str,
    node_type: str = "i3.xlarge",
    num_workers: int = 2,
    spark_version: str = "16.4.x-cpu-ml-scala2.12",
    autotermination_minutes: int = 60,
    autoscale_min_workers: int = 1,
    autoscale_max_workers: int = 3,
    enable_autoscaling: bool = False
) -> Dict[str, Any]:
    """Create a new Databricks cluster with sensible defaults."""
    if DRY_RUN:
        return _dry("create_cluster", cluster_name=cluster_name, node_type=node_type, num_workers=num_workers)
    
    # Build cluster spec
    cluster_spec = {
        "cluster_name": cluster_name,
        "spark_version": spark_version,
        "node_type_id": node_type,
        "autotermination_minutes": autotermination_minutes,
        "spark_conf": {
            "spark.databricks.cluster.profile": "singleNode" if num_workers == 0 else "serverless"
        }
    }
    
    if enable_autoscaling:
        cluster_spec["autoscale"] = {
            "min_workers": autoscale_min_workers,
            "max_workers": autoscale_max_workers
        }
    else:
        cluster_spec["num_workers"] = num_workers
    
    return await _request("POST", f"{API}/clusters/create", json=cluster_spec)

@mcp.tool()
async def databricks_create_cluster_advanced(cluster_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new cluster with custom cluster spec (advanced users)."""
    if DRY_RUN:
        return _dry("create_cluster_advanced", cluster_spec=cluster_spec)
    return await _request("POST", f"{API}/clusters/create", json=cluster_spec)

@mcp.tool()
async def databricks_terminate_cluster(cluster_id: str) -> Dict[str, Any]:
    """Terminate a cluster."""
    return await _request("POST", f"{API}/clusters/delete", json={"cluster_id": cluster_id})

@mcp.tool()
async def databricks_start_cluster(cluster_id: str) -> Dict[str, Any]:
    """Start a terminated cluster."""
    return await _request("POST", f"{API}/clusters/start", json={"cluster_id": cluster_id})

# -------- Jobs -------- [4]

@mcp.tool()
async def databricks_list_jobs(limit: int = 25, offset: int = 0) -> Dict[str, Any]:
    """List jobs in the workspace."""
    return await _request("GET", f"{API}/jobs/list", params={"limit": limit, "offset": offset})

@mcp.tool()
async def databricks_run_job(job_id: int, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run a Databricks job by job_id; pass parameters in 'job_parameters' if required by job config."""
    body: Dict[str, Any] = {"job_id": job_id}
    if parameters:
        body["job_parameters"] = parameters
    return await _request("POST", f"{API}/jobs/run-now", json=body)

# -------- Workspace (Notebooks) -------- [2]

@mcp.tool()
async def databricks_list_notebooks(path: str = "/") -> Dict[str, Any]:
    """List workspace objects under a given path."""
    return await _request("GET", f"{API}/workspace/list", params={"path": path})

@mcp.tool()
async def databricks_export_notebook(path: str, format: str = "SOURCE") -> Dict[str, Any]:
    """Export a notebook from the workspace. format: SOURCE|HTML|JUPYTER|DBC."""
    # Returns base64-encoded content for non-JSON; handle generically
    res = await _request("GET", f"{API}/workspace/export", params={"path": path, "format": format})
    return res

# -------- DBFS --------

@mcp.tool()
async def databricks_list_files(dbfs_path: str) -> Dict[str, Any]:
    """List files and directories under a DBFS path (e.g., dbfs:/FileStore)."""
    return await _request("GET", f"{API}/dbfs/list", params={"path": dbfs_path})

# -------- SQL Statement Execution API -------- [7]

@mcp.tool()
async def databricks_execute_sql(warehouse_id: str, statement: str, wait: bool = True) -> Dict[str, Any]:
    """Execute a SQL statement on a SQL warehouse; optionally wait for completion."""
    # POST /api/2.0/sql/statements
    create_body = {"warehouse_id": warehouse_id, "statement": statement}
    created = await _request("POST", SQL_API, json=create_body)
    statement_id = created.get("statement_id") or created.get("id") or created.get("statement", {}).get("statement_id")
    if not wait or not statement_id:
        return created
    # Poll for completion
    status = created
    for _ in range(60):  # up to ~60s
        status = await _request("GET", f"{SQL_API}/{statement_id}")
        state = status.get("status", {}).get("state") or status.get("status")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "ERROR"):
            break
        import asyncio
        await asyncio.sleep(1)
    return status

if __name__ == "__main__":
    mcp.run()
