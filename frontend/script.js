// MCP Gateway UI JavaScript
class MCPGatewayUI {
    constructor() {
        this.baseUrl = 'http://localhost:8080/mcp';
        this.protocolVersion = '2025-06-18';
        this.sessionId = null;
        this.isConnected = false;
        this.availableTools = {};
        this.currentTool = null;
        this.testRunner = null;
        
        this.initializeEventListeners();
        this.loadToolDefinitions();
    }

    initializeEventListeners() {
        // Connection button
        document.getElementById('connectBtn').addEventListener('click', () => {
            if (this.isConnected) {
                this.disconnect();
            } else {
                this.connect();
            }
        });

        // Clear chat button
        document.getElementById('clearChatBtn').addEventListener('click', () => {
            this.clearChat();
        });

        // Execute button
        document.getElementById('executeBtn').addEventListener('click', () => {
            this.executeCurrentTool();
        });

        // Modal close
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal on outside click
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('responseModal');
            if (event.target === modal) {
                this.closeModal();
            }
        });

        // Test runner buttons
        document.getElementById('runAllTestsBtn').addEventListener('click', () => {
            this.runAllTests();
        });

        document.getElementById('runCategoryTestsBtn').addEventListener('click', () => {
            this.showCategorySelector();
        });

        document.getElementById('runSelectedCategoryBtn').addEventListener('click', () => {
            this.runCategoryTests();
        });
    }

    async connect() {
        try {
            this.showLoading('Connecting to MCP Gateway...');
            
            // Initialize session
            const initResponse = await this.makeRequest('initialize', {
                protocolVersion: this.protocolVersion,
                capabilities: { tools: {} },
                clientInfo: { name: 'MCP Gateway UI', version: '1.0.0' }
            });

            // Send initialized notification
            await this.makeRequest('notifications/initialized', {});

            // Get available tools
            const toolsResponse = await this.makeRequest('tools/list', {});
            
            this.sessionId = initResponse.headers['mcp-session-id'];
            this.availableTools = this.parseTools(toolsResponse.result?.tools || []);
            this.isConnected = true;

            this.updateConnectionStatus();
            this.populateToolsList();
            this.addSystemMessage('Successfully connected to MCP Gateway!');
            
        } catch (error) {
            this.addErrorMessage(`Connection failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    disconnect() {
        this.sessionId = null;
        this.isConnected = false;
        this.availableTools = {};
        this.currentTool = null;
        
        this.updateConnectionStatus();
        this.clearToolsList();
        this.hideToolInterface();
        this.addSystemMessage('Disconnected from MCP Gateway');
    }

    async makeRequest(method, params = {}) {
        const request = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: method,
            params: params
        };

        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/event-stream',
            'MCP-Protocol-Version': this.protocolVersion
        };

        if (this.sessionId) {
            headers['Mcp-Session-Id'] = this.sessionId;
        }

        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const text = await response.text();
        const lines = text.split('\n');
        let result = null;

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    result = JSON.parse(line.substring(6));
                    break;
                } catch (e) {
                    // Continue to next line
                }
            }
        }

        if (!result) {
            throw new Error('Invalid response format');
        }

        return { result, headers: Object.fromEntries(response.headers.entries()) };
    }

    parseTools(tools) {
        const categorized = {
            sheets: [],
            slides: [],
            whatsapp: [],
            forms: []
        };

        tools.forEach(tool => {
            const name = tool.name.toLowerCase();
            if (name.includes('sheets') || name.includes('gs_')) {
                categorized.sheets.push(tool);
            } else if (name.includes('slides') || name.includes('gs_')) {
                categorized.slides.push(tool);
            } else if (name.includes('whatsapp') || name.includes('wa_')) {
                categorized.whatsapp.push(tool);
            } else if (name.includes('forms') || name.includes('gf_')) {
                categorized.forms.push(tool);
            }
        });

        return categorized;
    }

    populateToolsList() {
        const categories = {
            sheets: document.getElementById('sheetsTools'),
            slides: document.getElementById('slidesTools'),
            whatsapp: document.getElementById('whatsappTools'),
            forms: document.getElementById('formsTools')
        };

        Object.keys(categories).forEach(category => {
            const container = categories[category];
            container.innerHTML = '';

            this.availableTools[category]?.forEach(tool => {
                const toolElement = document.createElement('div');
                toolElement.className = 'tool-item';
                toolElement.textContent = tool.name;
                toolElement.addEventListener('click', () => {
                    this.selectTool(tool);
                });
                container.appendChild(toolElement);
            });
        });
    }

    clearToolsList() {
        const containers = ['sheetsTools', 'slidesTools', 'whatsappTools', 'formsTools'];
        containers.forEach(id => {
            document.getElementById(id).innerHTML = '';
        });
    }

    selectTool(tool) {
        // Remove active class from all tools
        document.querySelectorAll('.tool-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to selected tool
        event.target.classList.add('active');

        this.currentTool = tool;
        this.showToolInterface(tool);
    }

    showToolInterface(tool) {
        document.getElementById('toolSelection').style.display = 'none';
        document.getElementById('toolInterface').style.display = 'block';

        document.getElementById('selectedToolName').textContent = tool.name;
        document.getElementById('toolDescription').textContent = tool.description || 'No description available.';

        this.createParameterForm(tool);
    }

    hideToolInterface() {
        document.getElementById('toolSelection').style.display = 'block';
        document.getElementById('toolInterface').style.display = 'none';
        document.querySelectorAll('.tool-item').forEach(item => {
            item.classList.remove('active');
        });
    }

    createParameterForm(tool) {
        const form = document.getElementById('parametersForm');
        form.innerHTML = '';

        if (!tool.inputSchema?.properties) {
            form.innerHTML = '<p>No parameters required for this tool.</p>';
            return;
        }

        Object.entries(tool.inputSchema.properties).forEach(([key, prop]) => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';

            const label = document.createElement('label');
            label.textContent = prop.title || key;
            label.setAttribute('for', key);

            let input;
            if (prop.type === 'boolean') {
                input = document.createElement('select');
                input.innerHTML = '<option value="true">True</option><option value="false">False</option>';
            } else if (prop.type === 'array') {
                input = document.createElement('textarea');
                input.placeholder = 'Enter JSON array format: ["item1", "item2"]';
            } else if (prop.type === 'object') {
                input = document.createElement('textarea');
                input.placeholder = 'Enter JSON object format: {"key": "value"}';
            } else {
                input = document.createElement('input');
                input.type = prop.type === 'integer' ? 'number' : 'text';
            }

            input.id = key;
            input.name = key;
            input.required = tool.inputSchema.required?.includes(key) || false;

            if (prop.default !== undefined) {
                input.value = prop.default;
            }

            if (prop.description) {
                const help = document.createElement('div');
                help.className = 'form-help';
                help.textContent = prop.description;
                formGroup.appendChild(help);
            }

            formGroup.appendChild(label);
            formGroup.appendChild(input);
            form.appendChild(formGroup);
        });
    }

    async executeCurrentTool() {
        if (!this.currentTool) {
            this.addErrorMessage('No tool selected');
            return;
        }

        try {
            this.showLoading('Executing tool...');

            const formData = new FormData(document.getElementById('parametersForm'));
            const parameters = {};

            for (const [key, value] of formData.entries()) {
                parameters[key] = this.parseParameterValue(value);
            }

            this.addRequestMessage(this.currentTool.name, parameters);

            const response = await this.makeRequest('tools/call', {
                name: this.currentTool.name,
                arguments: parameters
            });

            this.addResponseMessage(this.currentTool.name, response.result);
            this.showResponseModal(response.result);

        } catch (error) {
            this.addErrorMessage(`Tool execution failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    parseParameterValue(value) {
        // Try to parse as JSON for arrays and objects
        if (value.startsWith('[') || value.startsWith('{')) {
            try {
                return JSON.parse(value);
            } catch (e) {
                return value;
            }
        }

        // Convert string numbers to numbers
        if (!isNaN(value) && value !== '') {
            return Number(value);
        }

        // Convert string booleans to booleans
        if (value === 'true') return true;
        if (value === 'false') return false;

        return value;
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        const buttonElement = document.getElementById('connectBtn');
        const sessionElement = document.getElementById('sessionId');

        if (this.isConnected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-connected';
            buttonElement.textContent = 'Disconnect';
            sessionElement.textContent = this.sessionId || 'Unknown';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status-disconnected';
            buttonElement.textContent = 'Connect';
            sessionElement.textContent = 'Not connected';
        }
    }

    addSystemMessage(message) {
        this.addMessage('system', 'System', message);
    }

    addRequestMessage(toolName, parameters) {
        this.addMessage('request', `Request: ${toolName}`, JSON.stringify(parameters, null, 2));
    }

    addResponseMessage(toolName, response) {
        this.addMessage('response', `Response: ${toolName}`, JSON.stringify(response, null, 2));
    }

    addErrorMessage(message) {
        this.addMessage('error', 'Error', message);
    }

    addMessage(type, header, body) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;

        const icon = this.getMessageIcon(type);
        const timestamp = new Date().toLocaleTimeString();

        messageElement.innerHTML = `
            <i class="${icon}"></i>
            <div class="message-content">
                <div class="message-header">${header} - ${timestamp}</div>
                <div class="message-body">${body}</div>
            </div>
        `;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getMessageIcon(type) {
        const icons = {
            system: 'fas fa-info-circle',
            request: 'fas fa-paper-plane',
            response: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle'
        };
        return icons[type] || 'fas fa-info-circle';
    }

    clearChat() {
        document.getElementById('chatMessages').innerHTML = `
            <div class="message system-message">
                <i class="fas fa-info-circle"></i>
                <span>Chat cleared. Ready for new requests.</span>
            </div>
        `;
    }

    showResponseModal(response) {
        document.getElementById('responseContent').textContent = JSON.stringify(response, null, 2);
        document.getElementById('responseModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('responseModal').style.display = 'none';
    }

    showLoading(message) {
        document.querySelector('#loadingOverlay p').textContent = message;
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    loadToolDefinitions() {
        // This would typically load from a configuration file
        // For now, we'll rely on the dynamic tool discovery from the MCP server
    }

    // Test Runner Methods
    async runAllTests() {
        if (!this.isConnected) {
            this.addErrorMessage('Please connect to MCP Gateway first');
            return;
        }

        if (!this.testRunner) {
            this.testRunner = new TestRunner(this);
        }

        try {
            await this.testRunner.runAllTests();
        } catch (error) {
            this.addErrorMessage(`Test execution failed: ${error.message}`);
        }
    }

    showCategorySelector() {
        const selector = document.getElementById('testCategorySelector');
        selector.style.display = selector.style.display === 'none' ? 'block' : 'none';
    }

    async runCategoryTests() {
        const category = document.getElementById('testCategorySelect').value;
        if (!category) {
            this.addErrorMessage('Please select a test category');
            return;
        }

        if (!this.isConnected) {
            this.addErrorMessage('Please connect to MCP Gateway first');
            return;
        }

        if (!this.testRunner) {
            this.testRunner = new TestRunner(this);
        }

        try {
            await this.testRunner.runCategoryTests(category);
        } catch (error) {
            this.addErrorMessage(`Category test execution failed: ${error.message}`);
        }
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.mcpUI = new MCPGatewayUI();
});

// Add some sample test data for demonstration
const sampleTestData = {
    'google_sheets_mcp_gs_create_spreadsheet': {
        title: 'Test Spreadsheet'
    },
    'google_sheets_mcp_gs_values_update': {
        spreadsheet_id: '1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8',
        range_a1: 'A1:B2',
        values: [['Name', 'Age'], ['Aman', '25']]
    },
    'whatsapp_wa_send_text': {
        to: '919910792473',
        text: 'Hello from MCP Gateway UI!',
        preview_url: false
    },
    'google_forms_mcp_gf_create_form': {
        title: 'Test Form',
        document_title: 'Test Form Document'
    }
};

// Add test data to window for easy access
window.sampleTestData = sampleTestData;
