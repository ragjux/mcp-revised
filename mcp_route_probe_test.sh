set -euo pipefail

BASE="${BASE:-http://localhost:8080/mcp}"
PROTO="${PROTO:-2025-06-18}"

# --- Init: capture Mcp-Session-Id (case-insensitive) ---
echo "→ Initializing session..."

# Dump *only* headers (-D -) and discard the body (-o /dev/null).
SESSION=$(
  curl -sS -D - -o /dev/null "$BASE" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json,text/event-stream" \
    -H "MCP-Protocol-Version: $PROTO" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
          "protocolVersion":"'"$PROTO"'",
          "capabilities":{"tools":{}},
          "clientInfo":{"name":"curl","version":"0.0.1"}
        }}' \
  | tr -d '\r' \
  | awk 'BEGIN{IGNORECASE=1} /^mcp-session-id:[[:space:]]*/{sub(/^[^:]+:[[:space:]]*/,"");print;exit}'
)

echo "✔ Session: $SESSION"
echo

curl -sS "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -H "MCP-Protocol-Version: $PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
| awk '/^data:/{sub(/^data:[ ]*/,"");print}'


curl -sS "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -H "MCP-Protocol-Version: $PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
| awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

