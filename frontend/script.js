class MCPChatInterface {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.initializeElements();
        this.setupEventListeners();
        this.connect();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.toolStatus = document.getElementById('toolStatus');
        this.toolStatusText = document.getElementById('toolStatusText');
        this.toolsCount = document.getElementById('toolsCount');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.welcomeTime = document.getElementById('welcomeTime');
    }

    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        // Set welcome message time
        this.welcomeTime.textContent = new Date().toLocaleTimeString();
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:9090/ws');
            this.updateConnectionStatus('connecting', 'Connecting...');
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', 'Connected');
                this.hideLoadingOverlay();
                console.log('Connected to MCP WebSocket');
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', 'Disconnected');
                this.hideLoadingOverlay();
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected', 'Connection Error');
            };

        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.showErrorMessage('Unable to connect to the MCP server. Please check if ws_gateway.py is running.');
        }
    }

    handleMessage(data) {
        console.log('Received message:', data);
        
        switch (data.event) {
            case 'status':
                this.handleStatusMessage(data);
                break;
            case 'tools':
                this.handleToolsMessage(data);
                break;
            case 'user_message':
                this.addUserMessage(data.text);
                break;
            case 'ai_message':
                this.addBotMessage(data.text, data.latency_ms);
                this.hideToolStatus();
                break;
            case 'tool_call':
                this.showToolStatus(`Calling tool: ${data.name}`);
                break;
            case 'tool_result':
                this.showToolStatus(`Tool completed: ${data.name}`);
                break;
            case 'error':
                this.handleErrorMessage(data);
                break;
            default:
                console.log('Unknown message type:', data.event);
        }
    }

    handleStatusMessage(data) {
        if (data.message === 'connecting_mcp') {
            this.showToolStatus('Connecting to MCP services...');
        }
    }

    handleToolsMessage(data) {
        this.toolsCount.textContent = `${data.count} tools loaded`;
        this.showToolStatus(`Loaded ${data.count} tools: ${data.tools.join(', ')}`);
        
        // Hide tool status after 3 seconds
        setTimeout(() => {
            this.hideToolStatus();
        }, 3000);
    }

    handleErrorMessage(data) {
        console.error('Error from server:', data);
        this.addBotMessage(`❌ Error: ${data.detail}`, null, true);
        this.hideToolStatus();
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;

        // Clear input immediately for better UX
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();

        // Send to server - user message will be displayed when server echoes it back
        try {
            this.ws.send(JSON.stringify({ message: message }));
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addBotMessage('❌ Failed to send message. Please try again.', null, true);
        }
    }

    addUserMessage(text) {
        const messageElement = this.createMessageElement('user', text);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    addBotMessage(text, latency = null, isError = false) {
        const messageElement = this.createMessageElement('bot', text, latency, isError);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    createMessageElement(type, text, latency = null, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = this.formatMessage(text);
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        if (latency) {
            timeDiv.textContent += ` (${latency}ms)`;
        }
        
        content.appendChild(textDiv);
        content.appendChild(timeDiv);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        return messageDiv;
    }

    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    showToolStatus(text) {
        this.toolStatusText.textContent = text;
        this.toolStatus.style.display = 'block';
    }

    hideToolStatus() {
        this.toolStatus.style.display = 'none';
    }

    updateConnectionStatus(status, text) {
        this.connectionStatus.className = `connection-status ${status}`;
        this.connectionStatus.querySelector('span').textContent = text;
        
        const icon = this.connectionStatus.querySelector('i');
        switch (status) {
            case 'connected':
                icon.style.color = '#4ade80';
                break;
            case 'connecting':
                icon.style.color = '#fbbf24';
                break;
            case 'disconnected':
                icon.style.color = '#f87171';
                break;
        }
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || !this.isConnected;
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    hideLoadingOverlay() {
        setTimeout(() => {
            this.loadingOverlay.classList.add('hidden');
        }, 500);
    }

    showErrorMessage(message) {
        this.addBotMessage(message, null, true);
    }
}

// Initialize the chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MCPChatInterface();
});

// Handle page visibility changes to reconnect if needed
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.mcpChat && !window.mcpChat.isConnected) {
        window.mcpChat.connect();
    }
});
