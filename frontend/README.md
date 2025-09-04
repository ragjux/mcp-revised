# MCP Gateway UI

A modern web interface for testing and interacting with the MCP Gateway that provides access to Google Workspace services (Sheets, Slides, Forms) and WhatsApp.

## Features

### 🔌 Connection Management
- **Session Management**: Automatically handles MCP session initialization
- **Connection Status**: Real-time connection status indicator
- **Protocol Support**: Full MCP protocol v2025-06-18 support

### 🛠️ Tool Testing
- **Dynamic Tool Discovery**: Automatically discovers all available MCP tools
- **Categorized Interface**: Tools organized by service (Sheets, Slides, WhatsApp, Forms)
- **Parameter Forms**: Dynamic forms generated based on tool schemas
- **Real-time Execution**: Execute tools with custom parameters

### 💬 Chat Interface
- **Request/Response Logging**: Complete history of all tool calls
- **JSON Formatting**: Pretty-printed JSON responses
- **Error Handling**: Clear error messages and debugging info
- **Timestamped Messages**: All interactions timestamped

### 🧪 Test Runner
- **Comprehensive Test Suite**: 29 pre-configured test scenarios
- **Category Testing**: Run tests for specific services
- **Batch Execution**: Run all tests with detailed reporting
- **Test Results**: Detailed pass/fail reporting with error details

## Getting Started

### Prerequisites
1. **MCP Gateway Running**: Ensure your MCP gateway is running on `http://localhost:8080`
2. **Environment Variables**: Set up all required API tokens and credentials
3. **Modern Browser**: Chrome, Firefox, Safari, or Edge with JavaScript enabled

### Setup
1. **Start the Gateway**: Run your MCP gateway server
   ```bash
   python gateway.py
   ```

2. **Open the UI**: Open `index.html` in your web browser
   ```bash
   open index.html  # macOS
   # or simply double-click the file
   ```

3. **Connect**: Click the "Connect" button to establish a session

## Usage Guide

### Basic Workflow
1. **Connect**: Click "Connect" to initialize MCP session
2. **Select Tool**: Choose a tool from the sidebar categories
3. **Fill Parameters**: Complete the dynamic parameter form
4. **Execute**: Click "Execute" to run the tool
5. **View Results**: Check the chat log and response modal

### Test Runner
1. **Run All Tests**: Click "Run All Tests" to execute the complete test suite
2. **Category Tests**: Click "Run Category Tests" and select a specific service
3. **View Results**: Check the detailed test report in the modal

### Available Services

#### Google Sheets
- Create spreadsheets
- Read/write cell values
- Manage sheets (add/delete)
- Batch operations

#### Google Slides
- Create presentations
- Manage slides
- Extract text content
- Batch updates

#### WhatsApp
- Send text messages
- Send media (images, documents)
- Interactive buttons
- Template messages

#### Google Forms
- Create forms
- Add/delete questions
- Get responses
- Batch updates

## Configuration

### Environment Variables
The UI connects to the MCP gateway which requires these environment variables:

```bash
# WhatsApp
META_WA_ACCESS_TOKEN=your_token
META_WA_PHONE_NUMBER_ID=your_phone_id
META_WA_API_VERSION=v21.0

# Google Sheets
GSHEETS_ACCESS_TOKEN=your_token
GSHEETS_REFRESH_TOKEN=your_refresh_token

# Google Slides
GSLIDES_ACCESS_TOKEN=your_token
GSLIDES_REFRESH_TOKEN=your_refresh_token

# Google Forms
GFORMS_ACCESS_TOKEN=your_token
GFORMS_REFRESH_TOKEN=your_refresh_token

# Gateway
PORT=8080
LOG_LEVEL=INFO
DRY_RUN=0
```

### Customization
- **Base URL**: Modify `baseUrl` in `script.js` to point to different gateway
- **Protocol Version**: Update `protocolVersion` for different MCP versions
- **Test Data**: Edit `test-scenarios.js` to modify test parameters

## File Structure

```
frontend/
├── index.html          # Main UI interface
├── styles.css          # Styling and responsive design
├── script.js           # Core UI functionality
├── test-scenarios.js   # Test definitions and runner
└── README.md          # This documentation
```

## Troubleshooting

### Connection Issues
- **Check Gateway**: Ensure `gateway.py` is running on port 8080
- **CORS**: If running from file://, use a local server
- **Network**: Check firewall and network connectivity

### Tool Execution Errors
- **Authentication**: Verify all API tokens are valid
- **Parameters**: Check parameter formats (JSON for arrays/objects)
- **Permissions**: Ensure API credentials have required scopes

### Test Failures
- **Credentials**: Verify all service credentials are configured
- **Test Data**: Update test IDs in `test-scenarios.js` with valid IDs
- **Rate Limits**: Add delays between tests if hitting API limits

## Development

### Adding New Tools
1. **Update Gateway**: Add new MCP server to `gateway.py`
2. **Test Scenarios**: Add test cases to `test-scenarios.js`
3. **UI Updates**: Tools are automatically discovered and categorized

### Customizing UI
- **Styling**: Modify `styles.css` for visual changes
- **Functionality**: Extend `MCPGatewayUI` class in `script.js`
- **Tests**: Add new scenarios to `testScenarios` object

## Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## Security Notes

- **Local Only**: This UI is designed for local development/testing
- **No Credentials**: UI doesn't store or transmit credentials
- **HTTPS**: Use HTTPS in production environments
- **CORS**: Configure CORS properly for cross-origin requests

## Support

For issues or questions:
1. Check the browser console for JavaScript errors
2. Verify MCP gateway logs
3. Test individual tools manually
4. Check API credentials and permissions

---

**Note**: This UI is designed for development and testing purposes. For production use, implement proper authentication, error handling, and security measures.
