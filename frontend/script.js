class MCPChatInterface {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.authToken = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.showAuthModal();
    }

    initializeElements() {
        // Auth modal elements
        this.authModal = document.getElementById('authModal');
        this.tokenInput = document.getElementById('tokenInput');
        this.connectButton = document.getElementById('connectButton');
        this.authError = document.getElementById('authError');
        this.authErrorMessage = document.getElementById('authErrorMessage');
        this.disconnectButton = document.getElementById('disconnectButton');
        
        // Chat elements
        this.chatContainer = document.getElementById('chatContainer');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearButton');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.toolStatus = document.getElementById('toolStatus');
        this.toolStatusText = document.getElementById('toolStatusText');
        this.toolsCount = document.getElementById('toolsCount');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.welcomeTime = document.getElementById('welcomeTime');
    }

    setupEventListeners() {
        // Auth modal events
        this.connectButton.addEventListener('click', () => this.handleConnect());
        this.disconnectButton.addEventListener('click', () => this.handleDisconnect());
        
        // Enter key in token input
        this.tokenInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handleConnect();
            }
        });

        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Clear button click
        this.clearButton.addEventListener('click', () => this.clearChat());
        
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
        if (!this.authToken) {
            this.showAuthError('No authentication token provided');
            return;
        }

        try {
            this.ws = new WebSocket(`ws://localhost:9090/ws?token=${encodeURIComponent(this.authToken)}`);
            this.updateConnectionStatus('connecting', 'Connecting...');
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', 'Connected');
                this.hideLoadingOverlay();
                this.hideAuthModal();
                
                // Clear connection timeout
                if (this.connectionTimeout) {
                    clearTimeout(this.connectionTimeout);
                    this.connectionTimeout = null;
                }
                
                console.log('Connected to MCP WebSocket');
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onclose = (event) => {
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', 'Disconnected');
                this.hideLoadingOverlay();
                
                // Clear connection timeout
                if (this.connectionTimeout) {
                    clearTimeout(this.connectionTimeout);
                    this.connectionTimeout = null;
                }
                
                // Check if it's an authentication error
                if (event.code === 1008) {
                    this.showAuthError('Invalid agent token. Please check your token and try again.');
                    this.connectButton.disabled = false;
                    this.connectButton.innerHTML = '<i class="fas fa-plug"></i> Connect';
                } else {
                    // If connection was closed unexpectedly (not by user disconnect), reset to auth
                    if (this.authToken && event.code !== 1000) {
                        this.handleDisconnect();
                    } else {
                        this.attemptReconnect();
                    }
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected', 'Connection Error');
                this.hideLoadingOverlay();
                
                // Clear connection timeout
                if (this.connectionTimeout) {
                    clearTimeout(this.connectionTimeout);
                    this.connectionTimeout = null;
                }
            };

        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.hideLoadingOverlay();
            
            // Clear connection timeout
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
                this.connectionTimeout = null;
            }
            
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && this.authToken) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.hideLoadingOverlay();
            if (!this.authToken) {
                this.showAuthError('Connection lost. Please reconnect with your token.');
            } else {
                this.showErrorMessage('Unable to connect to the MCP server. Please check if ws_gateway.py is running.');
            }
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
                // User message is already displayed immediately when sent
                // Server echo is ignored to prevent duplicates
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
        switch (data.message) {
            case 'connecting_mcp':
                this.showToolStatus('Connecting to MCP services...');
                break;
            case 'initializing_mcp_session':
                this.showToolStatus('Initializing MCP session...');
                break;
            case 'loading_tools':
                this.showToolStatus('Loading available tools...');
                break;
            default:
                this.showToolStatus(data.message);
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

        // Show user message immediately for better UX
        this.addUserMessage(message);

        // Clear input immediately for better UX
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();

        // Send to server
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

    // Authentication methods
    showAuthModal() {
        this.authModal.style.display = 'flex';
        this.chatContainer.style.display = 'none';
        this.hideLoadingOverlay();
        this.tokenInput.focus();
    }

    hideAuthModal() {
        this.authModal.style.display = 'none';
        this.chatContainer.style.display = 'flex';
    }

    showAuthError(message) {
        this.authErrorMessage.textContent = message;
        this.authError.style.display = 'flex';
        
        // Always reset button state
        this.connectButton.disabled = false;
        this.connectButton.innerHTML = '<i class="fas fa-plug"></i> Connect';
        
        // Hide loading overlay and reset connection status
        this.hideLoadingOverlay();
        this.updateConnectionStatus('disconnected', 'Authentication Failed');
        
        // Clear any existing auth token
        this.authToken = null;
    }

    hideAuthError() {
        this.authError.style.display = 'none';
    }

    handleConnect() {
        const token = this.tokenInput.value.trim();
        
        if (!token) {
            this.showAuthError('Please enter your agent token');
            return;
        }

        this.hideAuthError();
        this.connectButton.disabled = true;
        this.connectButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';

        this.authToken = token;
        
        // Set a timeout to prevent button from getting stuck
        this.connectionTimeout = setTimeout(() => {
            if (!this.isConnected) {
                this.showAuthError('Connection timeout. Please check your token and try again.');
            }
        }, 10000); // 10 second timeout
        
        this.connect();
    }

    handleDisconnect() {
        // Close WebSocket connection
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        // Reset connection state
        this.isConnected = false;
        this.authToken = null;
        
        // Clear token input
        this.tokenInput.value = '';
        
        // Clear chat messages
        this.chatMessages.innerHTML = '';
        
        // Reset connection status
        this.updateConnectionStatus('disconnected');
        
        // Hide tool status
        this.hideToolStatus();
        
        // Reset tools count
        this.toolsCount.textContent = 'Loading...';
        
        // Show authentication modal
        this.showAuthModal();
        
        // Hide chat interface
        this.chatContainer.style.display = 'none';
    }

    clearChat() {
        // Clear all messages except the welcome message
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        this.chatMessages.innerHTML = '';
        if (welcomeMessage) {
            this.chatMessages.appendChild(welcomeMessage);
        }
        
        // Hide any tool status
        this.hideToolStatus();
        
        // Scroll to top
        this.chatMessages.scrollTop = 0;
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
