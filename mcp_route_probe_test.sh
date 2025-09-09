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

# Test Google Sheets tools
# Test 1: Create spreadsheet
# echo "Testing sheets_gs_create_spreadsheet..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_create_spreadsheet","arguments":{"title":"no MCP Spreadsheet"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 2: Get values
# echo "Testing sheets_gs_values_get..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_values_get","arguments":{"spreadsheet_id":"","range_a1":"A1:C3"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 3: Update values
# echo "Testing sheets_gs_values_update..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_values_update","arguments":{"spreadsheet_id":"1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8","range_a1":"A1:B2","values":[["Name","Age"],["Aman","25"]]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 4: Append values
# echo "Testing sheets_gs_values_append..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_values_append","arguments":{"spreadsheet_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","range_a1":"A1:B2","values":[["Jane","30"]]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 5: Clear values
# echo "Testing sheets_gs_values_clear..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_values_clear","arguments":{"spreadsheet_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","range_a1":"A1:B2"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 6: Add sheet
# echo "Testing sheets_gs_add_sheet..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_add_sheet","arguments":{"spreadsheet_id":"1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8","title":"New MCP testing Sheet"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 7: Delete sheet
# echo "Testing sheets_gs_delete_sheet..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"google_sheets_mcp_gs_delete_sheet","arguments":{"spreadsheet_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","sheet_id":2}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .


# # Test Google Slides tools
# # Test 1: Create presentation
# echo "Testing slides_gs_create_presentation..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"google_slides_mcp_gs_create_presentation","arguments":{"title":"MCP Test Presentation"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 2: Get presentation
# echo "Testing slides_gs_get_presentation..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"google_slides_mcp_gs_get_presentation","arguments":{"presentationId":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 3: Batch update presentation
# echo "Testing slides_gs_batch_update_presentation..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"google_slides_mcp_gs_batch_update_presentation","arguments":{"presentationId":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","requests":[{"createSlide":{"slideLayoutReference":{"predefinedLayout":"TITLE_AND_BODY"}}}]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 4: Get page
# echo "Testing slides_gs_get_page..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"google_slides_mcp_gs_get_page","arguments":{"presentationId":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","pageObjectId":"slide1"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 5: Summarize presentation
# echo "Testing slides_gs_summarize_presentation..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"google_slides_mcp_gs_summarize_presentation","arguments":{"presentationId":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","include_notes":false}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .


# # Test WhatsApp tools
# # Test 1: Send text message
# echo "Testing whatsapp_wa_send_text..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":15,"method":"tools/call","params":{"name":"whatsapp_wa_send_text","arguments":{"to":"919910792473","text":"Hello JI!!","preview_url":false}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 2: Send template message
# echo "Testing whatsapp_wa_send_template..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":16,"method":"tools/call","params":{"name":"whatsapp_wa_send_template","arguments":{"to":"919650305671","template_name":"insurance_quotes_utility_02","language":"en","placeholders":["Anshuman","HDFC Plan (Quote - 123)","Cigna Plan (Quote - 123)","Go Digit (Quote - 122)"],"message_id":"test003"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 3: Send image URL
# echo "Testing whatsapp_wa_send_image_url..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":17,"method":"tools/call","params":{"name":"whatsapp_wa_send_image_url","arguments":{"to":"919910792473","image_url":"https://example.com/image.jpg","caption":"Check out this image!"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 4: Send document URL
# echo "Testing whatsapp_wa_send_document_url..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":18,"method":"tools/call","params":{"name":"whatsapp_wa_send_document_url","arguments":{"to":"919910792473","doc_url":"https://example.com/document.pdf","filename":"document.pdf"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 5: Send buttons
# echo "Testing whatsapp_wa_send_buttons..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":19,"method":"tools/call","params":{"name":"whatsapp_wa_send_buttons","arguments":{"to":"919910792473","header_text":"Choose an option","body_text":"Please select one of the following options:","buttons":[{"id":"btn1","title":"Yes"},{"id":"btn2","title":"No"}]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 6: Mark message as read
# echo "Testing whatsapp_wa_mark_read..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":20,"method":"tools/call","params":{"name":"whatsapp_wa_mark_read","arguments":{"message_id":"wamid.1234567890abcdef"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 7: Upload media
# echo "Testing whatsapp_wa_upload_media..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":21,"method":"tools/call","params":{"name":"whatsapp_wa_upload_media","arguments":{"file_path":"/path/to/your/file.jpg","mime_type":"image/jpeg"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .


# # Test Google Forms tools
# # Test 1: Create form
# echo "Testing forms_gf_create_form..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":22,"method":"tools/call","params":{"name":"google_forms_mcp_gf_create_form","arguments":{"title":"MCP Test Form","document_title":"MCP Test Form Document"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 2: Get form
# echo "Testing forms_gf_get_form..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":23,"method":"tools/call","params":{"name":"google_forms_mcp_gf_get_form","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 3: Add question
# echo "Testing forms_gf_add_question..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":24,"method":"tools/call","params":{"name":"google_forms_mcp_gf_add_question","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","title":"What is your name?","question_type":"TEXT","index":0}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 4: Add multiple choice question
# echo "Testing forms_gf_add_question (multiple choice)..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":25,"method":"tools/call","params":{"name":"google_forms_mcp_gf_add_question","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","title":"Choose your favorite color","question_type":"RADIO","index":1,"options":["Red","Blue","Green","Yellow"]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 5: Delete question
# echo "Testing forms_gf_delete_question..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":26,"method":"tools/call","params":{"name":"google_forms_mcp_gf_delete_question","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","location_index":0}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 6: Get responses
# echo "Testing forms_gf_get_responses..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":27,"method":"tools/call","params":{"name":"google_forms_mcp_gf_get_responses","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 7: List forms via Drive API
# echo "Testing forms_gf_drive_list_forms..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":28,"method":"tools/call","params":{"name":"google_forms_mcp_gf_drive_list_forms","arguments":{"page_size":5}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .

# # Test 8: Batch update form
# echo "Testing forms_gf_batch_update..."
# curl -sS "$BASE" \
#   -H "Content-Type: application/json" \
#   -H "Accept: application/json,text/event-stream" \
#   -H "MCP-Protocol-Version: $PROTO" \
#   -H "Mcp-Session-Id: $SESSION" \
#   -d '{"jsonrpc":"2.0","id":29,"method":"tools/call","params":{"name":"google_forms_mcp_gf_batch_update","arguments":{"form_id":"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms","requests":[{"updateFormInfo":{"info":{"title":"Updated MCP Test Form"},"updateMask":"title"}}]}}}' \
# | awk '/^data:/{sub(/^data:[ ]*/,"");print}' | jq .