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

# HUBSPOT----------------------------------------


# Create Company

# curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 2,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_create_company",
#       "arguments": {
#         "properties": {
#           "name": "My Test Company",
#           "domain": "mytestcompany.com",
#           "industry": "INFORMATION_TECHNOLOGY_AND_SERVICES",
#           "description": "Company created via curl"
#         }
#       }
#     }
#   }'

# # Get Active Companies

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 3,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_active_companies",
#       "arguments": {
#         "limit": 10
#       }
#     }
#   }'

# # Search Companies


#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 4,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_search_companies",
#       "arguments": {
#         "query": "test",
#         "limit": 5
#       }
#     }
#   }'

# # Get Company Details

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 5,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_company_details",
#       "arguments": {
#         "company_id": "149629634269"
#       }
#     }
#   }'

# # Get Company Contacts

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 6,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_company_contacts",
#       "arguments": {
#         "company_id": "149629634269",
#         "limit": 10
#       }
#     }
#   }'

# # Get Company Deals


#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 7,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_company_deals",
#       "arguments": {
#         "company_id": "149629634269",
#         "limit": 10
#       }
#     }
#   }'

# # Create Contact

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 8,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_create_contact",
#       "arguments": {
#         "properties": {
#           "email": "test@example.com",
#           "firstname": "John",
#           "lastname": "Doe",
#           "phone": "+1-555-123-4567"
#         }
#       }
#     }
#   }'

# # Get Active Contacts

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 9,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_active_contacts",
#       "arguments": {
#         "limit": 10
#       }
#     }
#   }'

# # Search Contacts

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 10,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_search_contacts",
#       "arguments": {
#         "query": "john",
#         "limit": 5
#       }
#     }
#   }'

# # Get Contact Details

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 11,
#     "method": "tools/call",
#     "params": {
#       "name": "hubspot_hubspot_get_contact_details",
#       "arguments": {
#         "contact_id": "231948434116"
#       }
#     }
#   }'

# # GMAIL----------------------------------------

# # Send Email

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 2,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_send_email",
#       "arguments": {
#         "recipient": "recipient@example.com",
#         "subject": "Test Email from MCP",
#         "body": "This is a test email sent via MCP Gateway."
#       }
#     }
#   }'

# # Send Email with Attachment

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 3,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_send_email",
#       "arguments": {
#         "recipient": "recipient@example.com",
#         "subject": "Email with Attachment",
#         "body": "Please find the attached file.",
#         "attachment_path": "/path/to/your/file.pdf"
#       }
#     }
#   }'

# # Send Email with URL Attachment
#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 4,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_send_email_with_url_attachment",
#       "arguments": {
#         "recipient": "recipient@example.com",
#         "subject": "Email with URL Attachment",
#         "body": "Please find the attached file downloaded from URL.",
#         "attachment_url": "https://example.com/document.pdf",
#         "attachment_filename": "document.pdf"
#       }
#     }
#   }'

# # Send Email with Pre-staged Attachment

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 5,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_send_email_with_prestaged_attachment",
#       "arguments": {
#         "recipient": "recipient@example.com",
#         "subject": "Email with Pre-staged Attachment",
#         "body": "Please find the pre-staged attachment.",
#         "attachment_name": "prestaged_file.pdf"
#       }
#     }
#   }'

# # Fetch Recent Emails

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 6,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_fetch_recent_emails",
#       "arguments": {
#         "folder": "INBOX",
#         "limit": 10
#       }
#     }
#   }'

# # Fetch Recent Emails from Sent Folder

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 7,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_fetch_recent_emails",
#       "arguments": {
#         "folder": "SENT",
#         "limit": 5
#       }
#     }
#   }'

# # Download Attachment From URL

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 8,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_download_attachment",
#       "arguments": {
#         "attachment_url": "https://example.com/document.pdf",
#         "attachment_filename": "downloaded_document.pdf"
#       }
#     }
#   }'

# # Get Pre-staged Attachment

#   curl -X POST "http://localhost:8080/mcp" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: 2025-06-18" \
#   -H "Mcp-Session-Id: YOUR_SESSION_ID_HERE" \
#   -d '{
#     "jsonrpc": "2.0",
#     "id": 9,
#     "method": "tools/call",
#     "params": {
#       "name": "gmail_gmail_get_prestaged_attachment",
#       "arguments": {
#         "attachment_name": "prestaged_file.pdf"
#       }
#     }
#   }'
  