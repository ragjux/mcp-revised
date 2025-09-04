// Test Scenarios for MCP Gateway UI
// Based on the test cases from mcp_route_probe_test.sh

const testScenarios = {
    // Google Sheets Tests
    sheets: [
        {
            name: 'Create Spreadsheet',
            tool: 'google_sheets_mcp_gs_create_spreadsheet',
            description: 'Create a new Google Spreadsheet',
            parameters: {
                title: 'MCP Test Spreadsheet'
            }
        },
        {
            name: 'Get Values',
            tool: 'google_sheets_mcp_gs_values_get',
            description: 'Read values from a spreadsheet range',
            parameters: {
                spreadsheet_id: '1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8',
                range_a1: 'A1:C3',
                value_render_option: 'UNFORMATTED_VALUE'
            }
        },
        {
            name: 'Update Values',
            tool: 'google_sheets_mcp_gs_values_update',
            description: 'Update values in a spreadsheet range',
            parameters: {
                spreadsheet_id: '1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8',
                range_a1: 'A1:B2',
                values: [['Name', 'Age'], ['Aman', '25']],
                value_input_option: 'USER_ENTERED'
            }
        },
        {
            name: 'Append Values',
            tool: 'google_sheets_mcp_gs_values_append',
            description: 'Append new rows to a spreadsheet',
            parameters: {
                spreadsheet_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                range_a1: 'A1:B2',
                values: [['Jane', '30']],
                value_input_option: 'USER_ENTERED',
                insert_data_option: 'INSERT_ROWS'
            }
        },
        {
            name: 'Clear Values',
            tool: 'google_sheets_mcp_gs_values_clear',
            description: 'Clear values in a spreadsheet range',
            parameters: {
                spreadsheet_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                range_a1: 'A1:B2'
            }
        },
        {
            name: 'Add Sheet',
            tool: 'google_sheets_mcp_gs_add_sheet',
            description: 'Add a new sheet to a spreadsheet',
            parameters: {
                spreadsheet_id: '1Yid5t5iBOljim_uBvovyllctO9nlKUURtSeMnEwaMC8',
                title: 'New MCP Testing Sheet'
            }
        },
        {
            name: 'Delete Sheet',
            tool: 'google_sheets_mcp_gs_delete_sheet',
            description: 'Delete a sheet from a spreadsheet',
            parameters: {
                spreadsheet_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                sheet_id: 2
            }
        }
    ],

    // Google Slides Tests
    slides: [
        {
            name: 'Create Presentation',
            tool: 'google_slides_mcp_gs_create_presentation',
            description: 'Create a new Google Slides presentation',
            parameters: {
                title: 'MCP Test Presentation'
            }
        },
        {
            name: 'Get Presentation',
            tool: 'google_slides_mcp_gs_get_presentation',
            description: 'Get details about a presentation',
            parameters: {
                presentationId: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
            }
        },
        {
            name: 'Batch Update Presentation',
            tool: 'google_slides_mcp_gs_batch_update_presentation',
            description: 'Apply batch updates to a presentation',
            parameters: {
                presentationId: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                requests: [{
                    createSlide: {
                        slideLayoutReference: {
                            predefinedLayout: 'TITLE_AND_BODY'
                        }
                    }
                }]
            }
        },
        {
            name: 'Get Page',
            tool: 'google_slides_mcp_gs_get_page',
            description: 'Get details about a specific slide',
            parameters: {
                presentationId: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                pageObjectId: 'slide1'
            }
        },
        {
            name: 'Summarize Presentation',
            tool: 'google_slides_mcp_gs_summarize_presentation',
            description: 'Extract text content from all slides',
            parameters: {
                presentationId: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                include_notes: false
            }
        }
    ],

    // WhatsApp Tests
    whatsapp: [
        {
            name: 'Send Text Message',
            tool: 'whatsapp_wa_send_text',
            description: 'Send a text message via WhatsApp',
            parameters: {
                to: '919910792473',
                text: 'Hello from MCP Gateway UI!',
                preview_url: false
            }
        },
        {
            name: 'Send Template Message',
            tool: 'whatsapp_wa_send_template',
            description: 'Send an approved template message',
            parameters: {
                to: '919910792473',
                template_name: 'hello_world',
                language: 'en_US'
            }
        },
        {
            name: 'Send Image URL',
            tool: 'whatsapp_wa_send_image_url',
            description: 'Send an image via URL',
            parameters: {
                to: '919910792473',
                image_url: 'https://example.com/image.jpg',
                caption: 'Check out this image!'
            }
        },
        {
            name: 'Send Document URL',
            tool: 'whatsapp_wa_send_document_url',
            description: 'Send a document via URL',
            parameters: {
                to: '919910792473',
                doc_url: 'https://example.com/document.pdf',
                filename: 'document.pdf'
            }
        },
        {
            name: 'Send Buttons',
            tool: 'whatsapp_wa_send_buttons',
            description: 'Send an interactive button message',
            parameters: {
                to: '919910792473',
                header_text: 'Choose an option',
                body_text: 'Please select one of the following options:',
                buttons: [
                    { id: 'btn1', title: 'Yes' },
                    { id: 'btn2', title: 'No' }
                ]
            }
        },
        {
            name: 'Mark Message as Read',
            tool: 'whatsapp_wa_mark_read',
            description: 'Mark an inbound message as read',
            parameters: {
                message_id: 'wamid.1234567890abcdef'
            }
        },
        {
            name: 'Upload Media',
            tool: 'whatsapp_wa_upload_media',
            description: 'Upload media to WhatsApp Cloud API',
            parameters: {
                file_path: '/path/to/your/file.jpg',
                mime_type: 'image/jpeg'
            }
        }
    ],

    // Google Forms Tests
    forms: [
        {
            name: 'Create Form',
            tool: 'google_forms_mcp_gf_create_form',
            description: 'Create a new Google Form',
            parameters: {
                title: 'MCP Test Form',
                document_title: 'MCP Test Form Document'
            }
        },
        {
            name: 'Get Form',
            tool: 'google_forms_mcp_gf_get_form',
            description: 'Get details about a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
            }
        },
        {
            name: 'Add Text Question',
            tool: 'google_forms_mcp_gf_add_question',
            description: 'Add a text question to a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                title: 'What is your name?',
                question_type: 'TEXT',
                index: 0
            }
        },
        {
            name: 'Add Multiple Choice Question',
            tool: 'google_forms_mcp_gf_add_question',
            description: 'Add a multiple choice question to a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                title: 'Choose your favorite color',
                question_type: 'RADIO',
                index: 1,
                options: ['Red', 'Blue', 'Green', 'Yellow']
            }
        },
        {
            name: 'Delete Question',
            tool: 'google_forms_mcp_gf_delete_question',
            description: 'Delete a question from a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                location_index: 0
            }
        },
        {
            name: 'Get Responses',
            tool: 'google_forms_mcp_gf_get_responses',
            description: 'Get all responses from a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
            }
        },
        {
            name: 'List Forms via Drive',
            tool: 'google_forms_mcp_gf_drive_list_forms',
            description: 'List all forms via Google Drive API',
            parameters: {
                page_size: 5
            }
        },
        {
            name: 'Batch Update Form',
            tool: 'google_forms_mcp_gf_batch_update',
            description: 'Apply batch updates to a form',
            parameters: {
                form_id: '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
                requests: [{
                    updateFormInfo: {
                        info: {
                            title: 'Updated MCP Test Form'
                        },
                        updateMask: 'title'
                    }
                }]
            }
        }
    ]
};

// Test Runner Class
class TestRunner {
    constructor(mcpUI) {
        this.mcpUI = mcpUI;
        this.currentTestIndex = 0;
        this.currentCategory = null;
        this.isRunning = false;
        this.results = [];
    }

    async runAllTests() {
        if (this.isRunning) {
            this.mcpUI.addErrorMessage('Tests are already running');
            return;
        }

        this.isRunning = true;
        this.results = [];
        this.mcpUI.addSystemMessage('Starting comprehensive test suite...');

        const categories = Object.keys(testScenarios);
        
        for (const category of categories) {
            await this.runCategoryTests(category);
        }

        this.isRunning = false;
        this.showTestSummary();
    }

    async runCategoryTests(category) {
        this.currentCategory = category;
        const tests = testScenarios[category];
        
        this.mcpUI.addSystemMessage(`Running ${category} tests (${tests.length} tests)...`);

        for (let i = 0; i < tests.length; i++) {
            this.currentTestIndex = i;
            const test = tests[i];
            
            try {
                this.mcpUI.addSystemMessage(`Running test ${i + 1}/${tests.length}: ${test.name}`);
                
                // Find the tool in available tools
                const tool = this.findTool(test.tool);
                if (!tool) {
                    this.results.push({
                        category,
                        test: test.name,
                        success: false,
                        error: `Tool ${test.tool} not found`
                    });
                    continue;
                }

                // Execute the test
                const result = await this.executeTest(tool, test.parameters);
                
                this.results.push({
                    category,
                    test: test.name,
                    success: true,
                    result: result
                });

                // Small delay between tests
                await this.delay(1000);

            } catch (error) {
                this.results.push({
                    category,
                    test: test.name,
                    success: false,
                    error: error.message
                });
                this.mcpUI.addErrorMessage(`Test failed: ${test.name} - ${error.message}`);
            }
        }
    }

    findTool(toolName) {
        const allTools = [
            ...this.mcpUI.availableTools.sheets,
            ...this.mcpUI.availableTools.slides,
            ...this.mcpUI.availableTools.whatsapp,
            ...this.mcpUI.availableTools.forms
        ];
        
        return allTools.find(tool => tool.name === toolName);
    }

    async executeTest(tool, parameters) {
        // Temporarily store current tool
        const originalTool = this.mcpUI.currentTool;
        
        try {
            // Set the tool and execute
            this.mcpUI.currentTool = tool;
            
            const response = await this.mcpUI.makeRequest('tools/call', {
                name: tool.name,
                arguments: parameters
            });

            this.mcpUI.addResponseMessage(tool.name, response.result);
            return response.result;

        } finally {
            // Restore original tool
            this.mcpUI.currentTool = originalTool;
        }
    }

    showTestSummary() {
        const totalTests = this.results.length;
        const successfulTests = this.results.filter(r => r.success).length;
        const failedTests = totalTests - successfulTests;

        this.mcpUI.addSystemMessage(`Test Summary: ${successfulTests}/${totalTests} tests passed`);
        
        if (failedTests > 0) {
            this.mcpUI.addErrorMessage(`${failedTests} tests failed:`);
            this.results.filter(r => !r.success).forEach(result => {
                this.mcpUI.addErrorMessage(`- ${result.category}: ${result.test} - ${result.error}`);
            });
        }

        // Show detailed results in modal
        this.showDetailedResults();
    }

    showDetailedResults() {
        const summary = {
            total: this.results.length,
            passed: this.results.filter(r => r.success).length,
            failed: this.results.filter(r => !r.success).length,
            results: this.results
        };

        this.mcpUI.showResponseModal(summary);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    getTestScenarios() {
        return testScenarios;
    }
}

// Export for use in main script
window.testScenarios = testScenarios;
window.TestRunner = TestRunner;
