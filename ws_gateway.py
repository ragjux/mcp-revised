#!/usr/bin/env python3
import asyncio, json, os, time, uuid, logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from langfuse.openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Config (env-driven)
# -------------------------
MCP_BASE      = os.getenv("MCP_BASE", "http://localhost:8080/mcp")
MCP_PROTO     = os.getenv("MCP_PROTO", "2025-06-18")
OPENAI_MODEL  = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_APIKEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT_S     = float(os.getenv("HTTP_TIMEOUT", "45"))

# -------------------------
# Setup
# -------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ws-mcp-chat")

app = FastAPI()
oai = OpenAI(api_key=OPENAI_APIKEY)

# -------------------------
# Minimal event schema sent to clients
# -------------------------
def ws_event(event: str, **payload) -> str:
    return json.dumps({"event": event, **payload}, ensure_ascii=False)

# -------------------------
# MCP client (HTTP SSE over /mcp)
# -------------------------
class MCPClient:
    def __init__(self, base: str, proto: str):
        self.base = base.rstrip("/")
        self.proto = proto
        self.session_id: Optional[str] = None
        self.http = httpx.Client(timeout=TIMEOUT_S)

    def _headers(self, include_session=True) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json,text/event-stream",
            "MCP-Protocol-Version": self.proto,
        }
        if include_session and self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        return h

    def initialize(self) -> None:
        # 1) initialize
        init_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.proto,
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "ws-gateway", "version": "0.0.1"},
            },
        }
        r = self.http.post(self.base, headers=self._headers(include_session=False), json=init_body)
        r.raise_for_status()
        self.session_id = r.headers.get("mcp-session-id") or r.headers.get("Mcp-Session-Id")
        if not self.session_id:
            raise RuntimeError("MCP server did not return mcp-session-id header")

        # 2) notifications/initialized
        n = self.http.post(self.base, headers=self._headers(), json={
            "jsonrpc":"2.0","method":"notifications/initialized","params":{}
        })
        n.raise_for_status()

    def _sse_json(self, body: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Send a JSON-RPC request; parse Server-Sent Events ('data: ...') lines;
        return a list of decoded JSON payloads in order.
        """
        out: List[Dict[str, Any]] = []
        with self.http.stream("POST", self.base, headers=self._headers(), json=body) as resp:
            resp.raise_for_status()

            # Accumulate one SSE message across multiple "data:" lines until a blank line.
            buf: List[str] = []

            for line in resp.iter_lines():
                # HTTPX yields *text* lines (str). Coerce defensively.
                if isinstance(line, (bytes, bytearray)):
                    s = line.decode("utf-8", "ignore")
                else:
                    s = line or ""

                s = s.rstrip("\r\n")

                if not s:
                    # End of one SSE event -> dispatch buffer
                    if buf:
                        try:
                            # Concatenate all data lines per SSE spec.
                            data_payload = "\n".join(buf)
                            out.append(json.loads(data_payload))
                        except Exception:
                            # Non-JSON keepalives or partials: ignore safely
                            pass
                        buf.clear()
                    continue

                # Comment/keepalive lines start with ":" per SSE spec — ignore.
                if s.startswith(":"):
                    continue

                if s.startswith("data:"):
                    # Strip leading "data:" and any one following space.
                    buf.append(s[5:].lstrip())

            # Flush trailing buffer (in case stream ended without a blank line)
            if buf:
                try:
                    out.append(json.loads("\n".join(buf)))
                except Exception:
                    pass

        return out

    def tools_list(self) -> Dict[str, Any]:
        evts = self._sse_json({"jsonrpc":"2.0","id":2,"method":"tools/list"})
        # the last event should include "result"
        for j in reversed(evts):
            if "result" in j:
                return j["result"]
        raise RuntimeError("tools/list had no result")

    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        body = {"jsonrpc":"2.0","id":str(uuid.uuid4()),"method":"tools/call","params":{
            "name": name, "arguments": arguments
        }}
        evts = self._sse_json(body)
        # Collect incremental text/plain outputs and the final result
        acc_text, final = [], None
        for j in evts:
            if "params" in j and "data" in j["params"]:
                d = j["params"]["data"]
                if isinstance(d, dict) and d.get("type") == "text":
                    acc_text.append(d.get("text",""))
            if "result" in j:
                final = j["result"]
        return {"stream_text": "".join(acc_text), "result": final}

# -------------------------
# Tool mapping: MCP -> OpenAI function tools
# -------------------------
def mcp_tools_to_oai_tools(mcp_tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert MCP tools/list result to Responses API function tools.
    Required by Responses API:
      - top-level keys: type, name, description, parameters
    """
    items = mcp_tools.get("tools") or mcp_tools.get("items") or []
    oai_tools: List[Dict[str, Any]] = []

    for t in items:
        name = t["name"]
        desc = t.get("description", f"MCP tool {name}")
        params = t.get("inputSchema") or {}
        # Ensure minimally valid JSON Schema
        if "type" not in params:
            params["type"] = "object"
        if "properties" not in params:
            params["properties"] = {}

        oai_tools.append({
            "type": "function",
            "name": name,
            "description": desc,
            "parameters": params,
        })
    return oai_tools


# -------------------------
# LLM orchestration
# -------------------------
SYSTEM_INSTRUCTIONS = (
    "You are an orchestration assistant. "
    "Use the provided tools when needed. "
    "Always explain what you're doing briefly, then do it. "
    "Prefer precise function arguments. Return user-friendly results."
)

def _extract_tool_calls(resp) -> list[dict]:
    calls = []
    for item in getattr(resp, "output", []) or []:
        if getattr(item, "type", None) in ("function_call", "tool_call"):
            args = getattr(item, "arguments", {}) or {}
            if isinstance(args, str):
                try: args = json.loads(args)
                except Exception: args = {"_raw": args}
            calls.append({
                "name": getattr(item, "name", None),
                "arguments": args,
                "call_id": getattr(item, "call_id", None)
            })
    return calls

def _collect_text(resp) -> str:
    chunks = []
    for item in getattr(resp, "output", []) or []:
        if getattr(item, "type", None) == "message":
            for c in getattr(item, "content", []) or []:
                if getattr(c, "type", None) == "output_text":
                    chunks.append(c.text)
    return "\n".join(chunks).strip()

async def run_llm_tool_loop(user_text, tools, call_tool, model):
    # First turn
    resp = oai.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_INSTRUCTIONS}]},
            {"role": "user",   "content": [{"type": "input_text", "text": user_text}]},
        ],
        tools=tools,
        tool_choice="auto",
    )

    while True:
        calls = _extract_tool_calls(resp)
        if calls:
            # Execute all tool calls
            fco_inputs = []  # function_call_output items
            for tc in calls:
                name = tc["name"]
                args = tc.get("arguments") or {}
                call_id = tc.get("call_id")
                
                tool_res = call_tool(name, args)

                # Build a STRING output for the function_call_output
                if isinstance(tool_res, dict):
                    summary = tool_res.get("stream_text") or ""
                    raw_json = tool_res.get("result", tool_res)
                else:
                    summary, raw_json = "", tool_res
                output_str = (f"{name} completed. {summary}\n"
                              f"RAW_JSON:\n{json.dumps(raw_json, ensure_ascii=False)}").strip()

                fco_inputs.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": output_str,
                })

            # Chain the response with the tool outputs
            resp = oai.responses.create(
                model=model,
                previous_response_id=resp.id,   # <-- key point
                input=fco_inputs,
                tools=tools,                    # keep tools available in case model chains more calls
                tool_choice="auto",
            )
            # Loop again in case the model wants to call more tools
            continue

        # No more tool calls → return conversational text
        text = _collect_text(resp) or "[No text output]"
        return text, []


# -------------------------
# WebSocket endpoint
# -------------------------
class InMsg(BaseModel):
    message: str

@app.get("/healthz", response_class=PlainTextResponse)
def healthz(): return "ok"

@app.websocket("/ws")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    # 1) Connect to MCP and list tools (per-connection so each client gets fresh discovery)
    try:
        await ws.send_text(ws_event("status", message="connecting_mcp"))
        mcp = MCPClient(MCP_BASE, MCP_PROTO)
        mcp.initialize()
        tools_raw = mcp.tools_list()
        oai_tools = mcp_tools_to_oai_tools(tools_raw)
        await ws.send_text(ws_event("tools", count=len(oai_tools), tools=[t["name"] for t in oai_tools]))
    except Exception as e:
        await ws.send_text(ws_event("error", where="mcp_init", detail=str(e)))
        await ws.close(); return

    # helper to call tools
    def _call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            log.info(f"Calling tool {name} with args {args}")
            r = mcp.tools_call(name, args)
            return r
        except Exception as e:
            return {"error": str(e)}

    # 2) Chat loop
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = InMsg.model_validate_json(raw)
                user_text = payload.message.strip()
            except Exception:
                await ws.send_text(ws_event("error", where="input", detail="Invalid payload; expected {\"message\": \"...\"}"))
                continue

            await ws.send_text(ws_event("user_message", text=user_text))
            t0 = time.time()
            try:
                final_text, trace = await run_llm_tool_loop(
                    user_text=user_text,
                    tools=oai_tools,
                    call_tool=_call_tool,
                    model=OPENAI_MODEL,
                )
                # stream back trace (compact)
                for ev in trace:
                    if ev.get("stage") == "tool_call":
                        await ws.send_text(ws_event("tool_call", name=ev["name"], args=ev["args"]))
                        await ws.send_text(ws_event("tool_result", name=ev["name"], result=ev["result"]))
                dt = round((time.time()-t0)*1000)
                await ws.send_text(ws_event("ai_message", text=final_text, latency_ms=dt))
            except Exception as e:
                await ws.send_text(ws_event("error", where="llm", detail=str(e)))
    except WebSocketDisconnect:
        pass
