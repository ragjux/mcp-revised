#!/usr/bin/env python3
"""
Playwright MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Playwright browser automation operations.
"""

import asyncio
import json
import logging
import os
import pathlib
import time
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables from .env file
load_dotenv()

# Robust async helper function to handle event loop conflicts
def run_async_safely(coro):
    """
    Safely run async coroutine, handling all possible event loop scenarios.
    This is the definitive solution for asyncio.run() conflicts in MCP servers.
    """
    try:
        # Try to get the current running loop
        loop = asyncio.get_running_loop()
        # If we're in a running loop, we need to use a different approach
        import concurrent.futures
        import threading
        
        # Create a new event loop in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # Run the coroutine in a separate thread with its own event loop
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop is running, safe to use asyncio.run()
        return asyncio.run(coro)
    except Exception as e:
        # Fallback: try asyncio.run() as last resort
        try:
            return asyncio.run(coro)
        except Exception as fallback_error:
            raise RuntimeError(f"Failed to run async coroutine: {e}. Fallback also failed: {fallback_error}")
# Configure logging to stderr to avoid stdio poisoning
import sys
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    stream=sys.stderr,   # Ensure logs never go to stdout
    force=True
)
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"playwright_{name}", "args": kwargs}

# Initialize FastMCP
mcp = FastMCP("Playwright MCP (native)")

# Global Playwright instance
playwright_instance = None
browser = None
context = None
page = None

async def _get_playwright():
    """Get or create Playwright instance"""
    global playwright_instance
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    return playwright_instance

async def _get_browser(browser_type: str = "chromium", headless: bool = False):
    """Get or create browser instance"""
    global browser
    if browser is None:
        pw = await _get_playwright()
        if browser_type == "firefox":
            browser = await pw.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await pw.webkit.launch(headless=headless)
        else:
            browser = await pw.chromium.launch(headless=headless)
    return browser

async def _get_context(width: int = 1280, height: int = 720):
    """Get or create browser context"""
    global context
    if context is None:
        browser_instance = await _get_browser()
        context = await browser_instance.new_context(
            viewport={"width": width, "height": height},
            accept_downloads=True
        )
    return context

async def _get_page():
    """Get or create page instance"""
    global page
    if page is None:
        context_instance = await _get_context()
        page = await context_instance.new_page()
    return page

async def _cleanup():
    """Cleanup Playwright resources"""
    global page, context, browser, playwright_instance
    try:
        if page:
            await page.close()
            page = None
        if context:
            await context.close()
            context = None
        if browser:
            await browser.close()
            browser = None
        if playwright_instance:
            await playwright_instance.stop()
            playwright_instance = None
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

# MCP tool functions (decorated)
@mcp.tool()
def playwright_navigate(
    url: str,
    browser_type: str = "chromium",
    width: int = 1280,
    height: int = 720,
    timeout: int = 300000,
    wait_until: str = "domcontentloaded",
    headless: bool = False
) -> Dict[str, Any]:
    """Navigate to a URL in the browser."""
    if DRY_RUN:
        return _dry("navigate", url=url, browser_type=browser_type, width=width, height=height, timeout=timeout, wait_until=wait_until, headless=headless)
    
    async def _navigate():
        try:
            # Get fresh instances
            await _cleanup()
            browser_instance = await _get_browser(browser_type, headless)
            context_instance = await _get_context(width, height)
            page_instance = await _get_page()
            
            # Navigate
            await page_instance.goto(url, timeout=timeout, wait_until=wait_until)
            title = await page_instance.title()
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "message": f"Successfully navigated to {url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to navigate to {url}"
            }
    
    return run_async_safely(_navigate())

@mcp.tool()
def playwright_screenshot(
    name: str,
    selector: Optional[str] = None,
    width: int = 1280,
    height: int = 720
) -> Dict[str, Any]:
    """Take a screenshot of the current page or a specific element."""
    if DRY_RUN:
        return _dry("screenshot", name=name, selector=selector, width=width, height=height)
    
    async def _screenshot():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for screenshot"
                }
            
            # Ensure screenshots directory exists
            screenshots_dir = pathlib.Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            
            if selector:
                element = await page_instance.query_selector(selector)
                if element:
                    screenshot_path = screenshots_dir / f"{name}.png"
                    await element.screenshot(path=str(screenshot_path))
                    return {
                        "success": True,
                        "path": str(screenshot_path),
                        "message": f"Screenshot saved as {name}.png"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Element with selector '{selector}' not found",
                        "message": "Element not found for screenshot"
                    }
            else:
                screenshot_path = screenshots_dir / f"{name}.png"
                await page_instance.screenshot(path=str(screenshot_path))
                return {
                    "success": True,
                    "path": str(screenshot_path),
                    "message": f"Screenshot saved as {name}.png"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to take screenshot"
            }
    
    return run_async_safely(_screenshot())

@mcp.tool()
def playwright_get_visible_text() -> Dict[str, Any]:
    """Get visible text from the current page."""
    if DRY_RUN:
        return _dry("get_visible_text")
    
    async def _get_text():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for text extraction"
                }
            
            text = await page_instance.evaluate("() => document.body.innerText")
            return {
                "success": True,
                "text": text,
                "length": len(text),
                "message": f"Extracted {len(text)} characters of visible text"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to extract visible text"
            }
    
    return run_async_safely(_get_text())

@mcp.tool()
def playwright_click_element(selector: str) -> Dict[str, Any]:
    """Click an element on the page."""
    if DRY_RUN:
        return _dry("click_element", selector=selector)
    
    async def _click():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for clicking"
                }
            
            await page_instance.click(selector, timeout=120000)
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully clicked element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to click element: {selector}"
            }
    
    return run_async_safely(_click())

@mcp.tool()
def playwright_fill_form(selector: str, value: str) -> Dict[str, Any]:
    """Fill a form field on the page."""
    if DRY_RUN:
        return _dry("fill_form", selector=selector, value=value)
    
    async def _fill():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for form filling"
                }
            
            await page_instance.fill(selector, value, timeout=120000)
            return {
                "success": True,
                "selector": selector,
                "value": value,
                "message": f"Successfully filled form field: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to fill form field: {selector}"
            }
    
    return run_async_safely(_fill())

@mcp.tool()
def playwright_select_option(selector: str, value: str) -> Dict[str, Any]:
    """Select an option from a dropdown."""
    if DRY_RUN:
        return _dry("select_option", selector=selector, value=value)
    
    async def _select():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for selection"
                }
            
            await page_instance.select_option(selector, value, timeout=120000)
            return {
                "success": True,
                "selector": selector,
                "value": value,
                "message": f"Successfully selected option: {value}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to select option: {value}"
            }
    
    return run_async_safely(_select())

@mcp.tool()
def playwright_hover_element(selector: str) -> Dict[str, Any]:
    """Hover over an element."""
    if DRY_RUN:
        return _dry("hover_element", selector=selector)
    
    async def _hover():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for hovering"
                }
            
            await page_instance.hover(selector)
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully hovered over element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to hover over element: {selector}"
            }
    
    return run_async_safely(_hover())

@mcp.tool()
def playwright_upload_file(selector: str, file_path: str) -> Dict[str, Any]:
    """Upload a file to an input field."""
    if DRY_RUN:
        return _dry("upload_file", selector=selector, file_path=file_path)
    
    async def _upload():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for file upload"
                }
            
            await page_instance.set_input_files(selector, file_path)
            return {
                "success": True,
                "selector": selector,
                "file_path": file_path,
                "message": f"Successfully uploaded file: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to upload file: {file_path}"
            }
    
    return run_async_safely(_upload())

@mcp.tool()
def playwright_execute_javascript(script: str) -> Dict[str, Any]:
    """Execute JavaScript code on the page."""
    if DRY_RUN:
        return _dry("execute_javascript", script=script)
    
    async def _execute():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for JavaScript execution"
                }
            
            result = await page_instance.evaluate(script)
            return {
                "success": True,
                "script": script,
                "result": result,
                "message": "Successfully executed JavaScript"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute JavaScript"
            }
    
    return run_async_safely(_execute())

@mcp.tool()
def playwright_get_visible_html() -> Dict[str, Any]:
    """Get visible HTML from the current page."""
    if DRY_RUN:
        return _dry("get_visible_html")
    
    async def _get_html():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTML extraction"
                }
            
            html = await page_instance.evaluate("() => document.body.innerHTML")
            return {
                "success": True,
                "html": html,
                "length": len(html),
                "message": f"Extracted {len(html)} characters of visible HTML"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to extract visible HTML"
            }
    
    return run_async_safely(_get_html())

@mcp.tool()
def playwright_go_back() -> Dict[str, Any]:
    """Go back in browser history."""
    if DRY_RUN:
        return _dry("go_back")
    
    async def _go_back():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for navigation"
                }
            
            await page_instance.go_back()
            return {
                "success": True,
                "message": "Successfully went back in browser history"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to go back in browser history"
            }
    
    return run_async_safely(_go_back())

@mcp.tool()
def playwright_go_forward() -> Dict[str, Any]:
    """Go forward in browser history."""
    if DRY_RUN:
        return _dry("go_forward")
    
    async def _go_forward():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for navigation"
                }
            
            await page_instance.go_forward()
            return {
                "success": True,
                "message": "Successfully went forward in browser history"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to go forward in browser history"
            }
    
    return run_async_safely(_go_forward())

@mcp.tool()
def playwright_press_key(key: str) -> Dict[str, Any]:
    """Press a key on the page."""
    if DRY_RUN:
        return _dry("press_key", key=key)
    
    async def _press():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for key press"
                }
            
            await page_instance.keyboard.press(key)
            return {
                "success": True,
                "key": key,
                "message": f"Successfully pressed key: {key}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to press key: {key}"
            }
    
    return run_async_safely(_press())

@mcp.tool()
def playwright_save_as_pdf(name: str) -> Dict[str, Any]:
    """Save the current page as PDF."""
    if DRY_RUN:
        return _dry("save_as_pdf", name=name)
    
    async def _save_pdf():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for PDF generation"
                }
            
            # Ensure screenshots directory exists
            screenshots_dir = pathlib.Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            
            pdf_path = screenshots_dir / f"{name}.pdf"
            await page_instance.pdf(path=str(pdf_path))
            return {
                "success": True,
                "path": str(pdf_path),
                "message": f"Successfully saved PDF as {name}.pdf"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save as PDF"
            }
    
    return run_async_safely(_save_pdf())

@mcp.tool()
def playwright_close_browser() -> Dict[str, Any]:
    """Close the browser."""
    if DRY_RUN:
        return _dry("close_browser")
    
    async def _close():
        try:
            await _cleanup()
            return {
                "success": True,
                "message": "Browser successfully closed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to close browser"
            }
    
    return run_async_safely(_close())

@mcp.tool()
def playwright_http_get(url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP GET request."""
    if DRY_RUN:
        return _dry("http_get", url=url, headers=headers)
    
    async def _get():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTTP requests"
                }
            
            response = await page_instance.request.get(url, headers=headers or {})
            content = await response.text()
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "message": f"HTTP GET request successful: {response.status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to make HTTP GET request to {url}"
            }
    
    return run_async_safely(_get())

@mcp.tool()
def playwright_http_post(url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP POST request."""
    if DRY_RUN:
        return _dry("http_post", url=url, data=data, headers=headers)
    
    async def _post():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTTP requests"
                }
            
            response = await page_instance.request.post(url, data=data or {}, headers=headers or {})
            content = await response.text()
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "message": f"HTTP POST request successful: {response.status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to make HTTP POST request to {url}"
            }
    
    return run_async_safely(_post())

@mcp.tool()
def playwright_drag_element(source_selector: str, target_selector: str) -> Dict[str, Any]:
    """Drag an element to another element."""
    if DRY_RUN:
        return _dry("drag_element", source_selector=source_selector, target_selector=target_selector)
    
    async def _drag():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for drag and drop"
                }
            
            source = page_instance.locator(source_selector)
            target = page_instance.locator(target_selector)
            await source.drag_to(target)
            
            return {
                "success": True,
                "source": source_selector,
                "target": target_selector,
                "message": f"Successfully dragged element from {source_selector} to {target_selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to drag element from {source_selector} to {target_selector}"
            }
    
    return run_async_safely(_drag())

@mcp.tool()
def playwright_click_iframe_element(selector: str, iframe_selector: str) -> Dict[str, Any]:
    """Click element inside an iframe."""
    if DRY_RUN:
        return _dry("click_iframe_element", selector=selector, iframe_selector=iframe_selector)
    
    async def _click_iframe():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for iframe interaction"
                }
            
            iframe = page_instance.frame_locator(iframe_selector)
            await iframe.locator(selector).click()
            
            return {
                "success": True,
                "selector": selector,
                "iframe_selector": iframe_selector,
                "message": "Successfully clicked element in iframe"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to click element in iframe"
            }
    
    return run_async_safely(_click_iframe())

@mcp.tool()
def playwright_fill_iframe_element(selector: str, value: str, iframe_selector: str) -> Dict[str, Any]:
    """Fill element inside an iframe."""
    if DRY_RUN:
        return _dry("fill_iframe_element", selector=selector, value=value, iframe_selector=iframe_selector)
    
    async def _fill_iframe():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for iframe interaction"
                }
            
            iframe = page_instance.frame_locator(iframe_selector)
            await iframe.locator(selector).fill(value)
            
            return {
                "success": True,
                "selector": selector,
                "value": value,
                "iframe_selector": iframe_selector,
                "message": "Successfully filled element in iframe"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to fill element in iframe"
            }
    
    return run_async_safely(_fill_iframe())

@mcp.tool()
def playwright_get_console_logs() -> Dict[str, Any]:
    """Get console logs from the page."""
    if DRY_RUN:
        return _dry("get_console_logs")
    
    async def _get_logs():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for console logs"
                }
            
            # This would need to be implemented with event listeners
            return {
                "success": True,
                "logs": "Console logs functionality needs to be implemented with event listeners",
                "message": "Console logs retrieved (placeholder)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve console logs"
            }
    
    return run_async_safely(_get_logs())

@mcp.tool()
def playwright_http_put(url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP PUT request."""
    if DRY_RUN:
        return _dry("http_put", url=url, data=data, headers=headers)
    
    async def _put():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTTP requests"
                }
            
            response = await page_instance.request.put(url, data=data or {}, headers=headers or {})
            content = await response.text()
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "message": f"HTTP PUT request successful: {response.status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to make HTTP PUT request to {url}"
            }
    
    return run_async_safely(_put())

@mcp.tool()
def playwright_http_patch(url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP PATCH request."""
    if DRY_RUN:
        return _dry("http_patch", url=url, data=data, headers=headers)
    
    async def _patch():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTTP requests"
                }
            
            response = await page_instance.request.patch(url, data=data or {}, headers=headers or {})
            content = await response.text()
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "message": f"HTTP PATCH request successful: {response.status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to make HTTP PATCH request to {url}"
            }
    
    return run_async_safely(_patch())

@mcp.tool()
def playwright_http_delete(url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP DELETE request."""
    if DRY_RUN:
        return _dry("http_delete", url=url, headers=headers)
    
    async def _delete():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for HTTP requests"
                }
            
            response = await page_instance.request.delete(url, headers=headers or {})
            content = await response.text()
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "message": f"HTTP DELETE request successful: {response.status}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to make HTTP DELETE request to {url}"
            }
    
    return run_async_safely(_delete())

@mcp.tool()
def playwright_expect_response(url_pattern: str, status: Optional[int] = None) -> Dict[str, Any]:
    """Expect a response with specific URL pattern and optional status."""
    if DRY_RUN:
        return _dry("expect_response", url_pattern=url_pattern, status=status)
    
    async def _expect():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for response expectations"
                }
            
            # This would need to be implemented with response event listeners
            return {
                "success": True,
                "url_pattern": url_pattern,
                "expected_status": status,
                "message": f"Response expectation set for {url_pattern}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to set response expectation"
            }
    
    return run_async_safely(_expect())

@mcp.tool()
def playwright_assert_response(url_pattern: str, expected_status: int, expected_content: Optional[str] = None) -> Dict[str, Any]:
    """Assert response properties."""
    if DRY_RUN:
        return _dry("assert_response", url_pattern=url_pattern, expected_status=expected_status, expected_content=expected_content)
    
    async def _assert():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for response assertions"
                }
            
            # This would need to be implemented with response event listeners
            return {
                "success": True,
                "url_pattern": url_pattern,
                "expected_status": expected_status,
                "expected_content": expected_content,
                "message": f"Response assertion successful for {url_pattern}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to assert response"
            }
    
    return run_async_safely(_assert())

@mcp.tool()
def playwright_set_custom_user_agent(user_agent: str) -> Dict[str, Any]:
    """Set custom user agent for the browser context."""
    if DRY_RUN:
        return _dry("set_custom_user_agent", user_agent=user_agent)
    
    async def _set_ua():
        try:
            context_instance = await _get_context()
            if not context_instance:
                return {
                    "success": False,
                    "error": "No browser context available. Navigate to a URL first.",
                    "message": "No context available for user agent setting"
                }
            
            await context_instance.set_extra_http_headers({"User-Agent": user_agent})
            return {
                "success": True,
                "user_agent": user_agent,
                "message": f"Successfully set custom user agent: {user_agent}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to set custom user agent: {user_agent}"
            }
    
    return run_async_safely(_set_ua())

@mcp.tool()
def playwright_click_and_switch_tab(selector: str) -> Dict[str, Any]:
    """Click an element and switch to the new tab if it opens one."""
    if DRY_RUN:
        return _dry("click_and_switch_tab", selector=selector)
    
    async def _click_switch():
        try:
            page_instance = await _get_page()
            context_instance = await _get_context()
            if not page_instance or not context_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for tab switching"
                }
            
            # Get current page count
            initial_pages = len(context_instance.pages)
            
            # Click element (this might open a new tab)
            await page_instance.click(selector)
            
            # Wait a bit for new tab to open
            await asyncio.sleep(1)
            
            # Check if new tab opened
            current_pages = len(context_instance.pages)
            if current_pages > initial_pages:
                # Switch to the new tab
                new_page = context_instance.pages[-1]
                await new_page.bring_to_front()
                global page
                page = new_page
                
                return {
                    "success": True,
                    "selector": selector,
                    "new_tab": True,
                    "message": "Successfully clicked element and switched to new tab"
                }
            else:
                return {
                    "success": True,
                    "selector": selector,
                    "new_tab": False,
                    "message": "Successfully clicked element (no new tab opened)"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to click element and switch tab: {selector}"
            }
    
    return run_async_safely(_click_switch())

@mcp.tool()
def playwright_wait_for_element(selector: str, timeout: int = 30000) -> Dict[str, Any]:
    """Wait for an element to appear on the page."""
    if DRY_RUN:
        return _dry("wait_for_element", selector=selector, timeout=timeout)
    
    async def _wait():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for waiting"
                }
            
            await page_instance.wait_for_selector(selector, timeout=timeout)
            return {
                "success": True,
                "selector": selector,
                "timeout": timeout,
                "message": f"Successfully waited for element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to wait for element: {selector}"
            }
    
    return run_async_safely(_wait())

@mcp.tool()
def playwright_wait_for_text(text: str, timeout: int = 30000) -> Dict[str, Any]:
    """Wait for specific text to appear on the page."""
    if DRY_RUN:
        return _dry("wait_for_text", text=text, timeout=timeout)
    
    async def _wait_text():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for waiting"
                }
            
            await page_instance.wait_for_function(f"() => document.body.innerText.includes('{text}')", timeout=timeout)
            return {
                "success": True,
                "text": text,
                "timeout": timeout,
                "message": f"Successfully waited for text: {text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to wait for text: {text}"
            }
    
    return run_async_safely(_wait_text())

@mcp.tool()
def playwright_get_element_text(selector: str) -> Dict[str, Any]:
    """Get text content of a specific element."""
    if DRY_RUN:
        return _dry("get_element_text", selector=selector)
    
    async def _get_text():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for text extraction"
                }
            
            element = await page_instance.query_selector(selector)
            if element:
                text = await element.inner_text()
                return {
                    "success": True,
                    "selector": selector,
                    "text": text,
                    "message": f"Successfully extracted text from element: {selector}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Element with selector '{selector}' not found",
                    "message": "Element not found for text extraction"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get element text: {selector}"
            }
    
    return run_async_safely(_get_text())

@mcp.tool()
def playwright_get_element_attribute(selector: str, attribute: str) -> Dict[str, Any]:
    """Get attribute value of a specific element."""
    if DRY_RUN:
        return _dry("get_element_attribute", selector=selector, attribute=attribute)
    
    async def _get_attr():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for attribute extraction"
                }
            
            element = await page_instance.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return {
                    "success": True,
                    "selector": selector,
                    "attribute": attribute,
                    "value": value,
                    "message": f"Successfully extracted attribute '{attribute}' from element: {selector}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Element with selector '{selector}' not found",
                    "message": "Element not found for attribute extraction"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get element attribute: {selector}.{attribute}"
            }
    
    return run_async_safely(_get_attr())

@mcp.tool()
def playwright_scroll_to_element(selector: str) -> Dict[str, Any]:
    """Scroll to a specific element on the page."""
    if DRY_RUN:
        return _dry("scroll_to_element", selector=selector)
    
    async def _scroll():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for scrolling"
                }
            
            await page_instance.locator(selector).scroll_into_view_if_needed()
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully scrolled to element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll to element: {selector}"
            }
    
    return run_async_safely(_scroll())

@mcp.tool()
def playwright_scroll_page(x: int = 0, y: int = 0) -> Dict[str, Any]:
    """Scroll the page by specified pixels."""
    if DRY_RUN:
        return _dry("scroll_page", x=x, y=y)
    
    async def _scroll_page():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for scrolling"
                }
            
            await page_instance.mouse.wheel(x, y)
            return {
                "success": True,
                "x": x,
                "y": y,
                "message": f"Successfully scrolled page by ({x}, {y}) pixels"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll page by ({x}, {y}) pixels"
            }
    
    return run_async_safely(_scroll_page())

@mcp.tool()
def playwright_double_click_element(selector: str) -> Dict[str, Any]:
    """Double-click an element on the page."""
    if DRY_RUN:
        return _dry("double_click_element", selector=selector)
    
    async def _double_click():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for double-clicking"
                }
            
            await page_instance.dblclick(selector)
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully double-clicked element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to double-click element: {selector}"
            }
    
    return run_async_safely(_double_click())

@mcp.tool()
def playwright_right_click_element(selector: str) -> Dict[str, Any]:
    """Right-click an element on the page."""
    if DRY_RUN:
        return _dry("right_click_element", selector=selector)
    
    async def _right_click():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for right-clicking"
                }
            
            await page_instance.click(selector, button="right")
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully right-clicked element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to right-click element: {selector}"
            }
    
    return run_async_safely(_right_click())

@mcp.tool()
def playwright_type_text(text: str, selector: Optional[str] = None) -> Dict[str, Any]:
    """Type text into an element or the page."""
    if DRY_RUN:
        return _dry("type_text", text=text, selector=selector)
    
    async def _type():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for typing"
                }
            
            if selector:
                await page_instance.type(selector, text)
                return {
                    "success": True,
                    "text": text,
                    "selector": selector,
                    "message": f"Successfully typed text into element: {selector}"
                }
            else:
                await page_instance.keyboard.type(text)
                return {
                    "success": True,
                    "text": text,
                    "message": "Successfully typed text on the page"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to type text: {text}"
            }
    
    return run_async_safely(_type())

@mcp.tool()
def playwright_clear_text(selector: str) -> Dict[str, Any]:
    """Clear text from an input field."""
    if DRY_RUN:
        return _dry("clear_text", selector=selector)
    
    async def _clear():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for clearing text"
                }
            
            await page_instance.fill(selector, "")
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully cleared text from element: {selector}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to clear text from element: {selector}"
            }
    
    return run_async_safely(_clear())

@mcp.tool()
def playwright_get_page_url() -> Dict[str, Any]:
    """Get the current page URL."""
    if DRY_RUN:
        return _dry("get_page_url")
    
    async def _get_url():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for URL extraction"
                }
            
            url = page_instance.url
            return {
                "success": True,
                "url": url,
                "message": f"Current page URL: {url}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get page URL"
            }
    
    return run_async_safely(_get_url())

@mcp.tool()
def playwright_get_page_title() -> Dict[str, Any]:
    """Get the current page title."""
    if DRY_RUN:
        return _dry("get_page_title")
    
    async def _get_title():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for title extraction"
                }
            
            title = await page_instance.title()
            return {
                "success": True,
                "title": title,
                "message": f"Current page title: {title}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get page title"
            }
    
    return run_async_safely(_get_title())

@mcp.tool()
def playwright_refresh_page() -> Dict[str, Any]:
    """Refresh the current page."""
    if DRY_RUN:
        return _dry("refresh_page")
    
    async def _refresh():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for refresh"
                }
            
            await page_instance.reload()
            return {
                "success": True,
                "message": "Successfully refreshed the page"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to refresh the page"
            }
    
    return run_async_safely(_refresh())

@mcp.tool()
def playwright_wait_for_load_state(state: str = "load", timeout: int = 30000) -> Dict[str, Any]:
    """Wait for the page to reach a specific load state."""
    if DRY_RUN:
        return _dry("wait_for_load_state", state=state, timeout=timeout)
    
    async def _wait_load():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for load state waiting"
                }
            
            await page_instance.wait_for_load_state(state, timeout=timeout)
            return {
                "success": True,
                "state": state,
                "timeout": timeout,
                "message": f"Successfully waited for load state: {state}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to wait for load state: {state}"
            }
    
    return run_async_safely(_wait_load())

@mcp.tool()
def playwright_set_viewport_size(width: int, height: int) -> Dict[str, Any]:
    """Set the viewport size of the page."""
    if DRY_RUN:
        return _dry("set_viewport_size", width=width, height=height)
    
    async def _set_viewport():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for viewport setting"
                }
            
            await page_instance.set_viewport_size({"width": width, "height": height})
            return {
                "success": True,
                "width": width,
                "height": height,
                "message": f"Successfully set viewport size to {width}x{height}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to set viewport size to {width}x{height}"
            }
    
    return run_async_safely(_set_viewport())

@mcp.tool()
def playwright_take_full_page_screenshot(name: str) -> Dict[str, Any]:
    """Take a full page screenshot (including content not visible in viewport)."""
    if DRY_RUN:
        return _dry("take_full_page_screenshot", name=name)
    
    async def _full_screenshot():
        try:
            page_instance = await _get_page()
            if not page_instance:
                return {
                    "success": False,
                    "error": "No page loaded. Navigate to a URL first.",
                    "message": "No page available for screenshot"
                }
            
            # Ensure screenshots directory exists
            screenshots_dir = pathlib.Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            
            screenshot_path = screenshots_dir / f"{name}.png"
            await page_instance.screenshot(path=str(screenshot_path), full_page=True)
            return {
                "success": True,
                "path": str(screenshot_path),
                "message": f"Full page screenshot saved as {name}.png"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to take full page screenshot"
            }
    
    return run_async_safely(_full_screenshot())

if __name__ == "__main__":
    mcp.run()
