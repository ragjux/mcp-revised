# selenium_server.py

import base64
import os
import platform
import subprocess
import sys
from enum import Enum
from typing import List, Optional, Union

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# ==============================================================================
# 1. GLOBAL STATE & MCP INITIALIZATION
# ==============================================================================

class ServerState:
    """Manages the state of active browser sessions."""
    def __init__(self):
        self.drivers = {}
        self.current_session = None

# Global state instance to hold drivers and the current session
state = ServerState()

mcp = FastMCP("MCP-Selenium")

# ==============================================================================
# 2. REQUEST TYPE MODELS
# ==============================================================================

class LocatorStrategy(str, Enum):
    ID = "id"
    CSS = "css"
    XPATH = "xpath"
    NAME = "name"
    TAG = "tag"
    CLASS = "class"
    LINK_TEXT = "link_text"
    PARTIAL_LINK_TEXT = "partial_link_text"

class BrowserType(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"

class BrowserOptions(BaseModel):
    headless: bool = False
    arguments: Optional[List[str]] = []
    # window_size removed - always use 1920,1080

class StartBrowserRequest(BaseModel):
    browser: BrowserType
    options: Optional[BrowserOptions] = None

class NavigateRequest(BaseModel):
    url: str

class ElementLocator(BaseModel):
    by: LocatorStrategy
    value: str
    timeout: int = 10000  # Default timeout in milliseconds

class SendKeysRequest(ElementLocator):
    text: str

class KeyPressRequest(BaseModel):
    key: str

class LocalStorageRequest(BaseModel):
    key: str = Field(..., description="Key in local storage")
    value: Optional[str] = Field(None, description="Value to set (if operation is 'set')")
    operation: str = Field("get", description="Operation to perform (get, set, or remove)")

class ScreenshotRequest(BaseModel):
    """Screenshot request - always saves to mcp-revised/data/selenium/ss.png"""
    pass

class IFrameRequest(BaseModel):
    type: str = Field(..., description="Selector type: 'index', 'id', 'name', or 'element'")
    value: Optional[Union[str, int]] = Field(None, description="Value for the iframe selector.")
    element_by: Optional[LocatorStrategy] = Field(None, description="If type is 'element', the locator strategy.")
    element_value: Optional[str] = Field(None, description="If type is 'element', the locator value.")

class ScrollRequest(BaseModel):
    direction: str = Field("down", description="Scroll direction: 'up' or 'down'")
    pixels: Optional[int] = Field(None, description="Number of pixels to scroll.")

# ==============================================================================
# 3. SERVICE LAYER
# ==============================================================================

class SeleniumService:
    """Encapsulates all core logic for Selenium browser automation."""

    def _get_driver(self):
        """Retrieves the currently active WebDriver instance from global state."""
        if state.current_session and state.current_session in state.drivers:
            return state.drivers[state.current_session]
        raise Exception("No active browser session found. Please start a browser first.")

    def _get_locator(self, by_strategy: LocatorStrategy, value: str):
        """Converts a string strategy into a Selenium `By` object."""
        mapping = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT,
        }
        return mapping[by_strategy.lower()], value

    def _check_browser_installation(self, browser_type: BrowserType):
        """Check if the browser is installed on the system."""
        try:
            if browser_type == BrowserType.CHROME:
                # Check if Chrome is installed
                if platform.system() == "Darwin":  # macOS
                    # Check common Chrome locations on macOS
                    chrome_paths = [
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                        "/Applications/Chromium.app/Contents/MacOS/Chromium"
                    ]
                    chrome_found = False
                    for path in chrome_paths:
                        if os.path.exists(path):
                            chrome_found = True
                            break
                    
                    if not chrome_found:
                        # Fallback to PATH check
                        result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
                        if result.returncode != 0:
                            result = subprocess.run(["which", "chromium"], capture_output=True, text=True)
                        if result.returncode != 0:
                            raise Exception("Chrome browser not found. Please install Google Chrome or Chromium.")
                            
                elif platform.system() == "Linux":
                    result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
                    if result.returncode != 0:
                        result = subprocess.run(["which", "chromium-browser"], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception("Chrome browser not found. Please install Google Chrome or Chromium.")
                else:  # Windows
                    result = subprocess.run(["where", "chrome"], capture_output=True, text=True, shell=True)
                    if result.returncode != 0:
                        raise Exception("Chrome browser not found. Please install Google Chrome or Chromium.")
                    
            elif browser_type == BrowserType.FIREFOX:
                if platform.system() == "Darwin":  # macOS
                    # Check common Firefox locations on macOS
                    firefox_paths = [
                        "/Applications/Firefox.app/Contents/MacOS/firefox"
                    ]
                    firefox_found = False
                    for path in firefox_paths:
                        if os.path.exists(path):
                            firefox_found = True
                            break
                    
                    if not firefox_found:
                        # Fallback to PATH check
                        result = subprocess.run(["which", "firefox"], capture_output=True, text=True)
                        if result.returncode != 0:
                            raise Exception("Firefox browser not found. Please install Firefox.")
                            
                elif platform.system() == "Linux":
                    result = subprocess.run(["which", "firefox"], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception("Firefox browser not found. Please install Firefox.")
                else:  # Windows
                    result = subprocess.run(["where", "firefox"], capture_output=True, text=True, shell=True)
                    if result.returncode != 0:
                        raise Exception("Firefox browser not found. Please install Firefox.")
        except Exception as e:
            raise Exception(f"Browser installation check failed: {str(e)}")

    def start_browser(self, browser_type: BrowserType, options: BrowserOptions):
        """Initializes and starts a new WebDriver instance."""
        try:
            # Check if browser is already running
            if state.current_session and state.current_session in state.drivers:
                existing_driver = state.drivers[state.current_session]
                try:
                    # Test if the existing driver is still responsive
                    existing_driver.current_url
                    return f"Browser session already active: {state.current_session}"
                except:
                    # Clean up dead session
                    try:
                        existing_driver.quit()
                    except:
                        pass
                    del state.drivers[state.current_session]
                    state.current_session = None

            # Check browser installation
            self._check_browser_installation(browser_type)

            if browser_type == BrowserType.CHROME:
                chrome_options = ChromeOptions()
                if options.headless:
                    chrome_options.add_argument("--headless=new")
                else:
                    # Add some useful options for headed mode
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                    chrome_options.add_argument("--disable-gpu")
                
                # Set window size (always 1920,1080)
                chrome_options.add_argument("--window-size=1920,1080")
                
                # Add any custom arguments
                if options.arguments:
                    for arg in options.arguments:
                        chrome_options.add_argument(arg)
                
                # Use webdriver-manager to handle ChromeDriver
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
            elif browser_type == BrowserType.FIREFOX:
                firefox_options = FirefoxOptions()
                if options.headless:
                    firefox_options.add_argument("--headless")
                
                # Add any custom arguments
                if options.arguments:
                    for arg in options.arguments:
                        firefox_options.add_argument(arg)
                
                # Use webdriver-manager to handle GeckoDriver
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=firefox_options)
                
                # Set window size for Firefox (always 1920,1080)
                driver.set_window_size(1920, 1080)
            else:
                raise ValueError("Unsupported browser type")

            session_id = f"{browser_type.value}_{id(driver)}"
            state.drivers[session_id] = driver
            state.current_session = session_id
            return f"Browser started successfully with session_id: {session_id}"

        except WebDriverException as e:
            raise Exception(f"WebDriver error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to start browser: {str(e)}")

    def click_element(self, by: LocatorStrategy, value: str, timeout: int):
        """Finds a clickable element and clicks it."""
        driver = self._get_driver()
        by_strategy, selector = self._get_locator(by, value)
        element = WebDriverWait(driver, timeout / 1000).until(
            EC.element_to_be_clickable((by_strategy, selector))
        )
        element.click()
        return "Element clicked successfully."

    def send_keys(self, by: LocatorStrategy, value: str, timeout: int, text: str):
        """Finds an element, clears it, and sends keys to it."""
        driver = self._get_driver()
        by_strategy, selector = self._get_locator(by, value)
        element = WebDriverWait(driver, timeout / 1000).until(
            EC.element_to_be_clickable((by_strategy, selector))
        )
        element.clear()
        element.send_keys(text)
        return f'Text "{text}" entered into element.'

    def get_element_text(self, by: LocatorStrategy, value: str, timeout: int):
        """Gets the text content of an element."""
        driver = self._get_driver()
        by_strategy, selector = self._get_locator(by, value)
        element = WebDriverWait(driver, timeout / 1000).until(
            EC.presence_of_element_located((by_strategy, selector))
        )
        return element.text or "Element found, but it has no text content."

    def get_page_content(self):
        """Gets the HTML source of the current page."""
        driver = self._get_driver()
        return driver.page_source

    def take_screenshot(self):
        """Captures a screenshot and saves it to mcp-revised/data/selenium/ss.png"""
        driver = self._get_driver()
        # Always save to mcp-revised/data/selenium/ss.png
        base_dir = os.path.dirname(os.path.dirname(__file__))
        screenshot_path = os.path.join(base_dir, 'data', 'selenium', 'ss.png')
        driver.get_screenshot_as_file(screenshot_path)
        return f"Screenshot saved to {screenshot_path}"
    
    def close_session(self):
        """Closes the current browser and cleans up the session state."""
        driver = self._get_driver()
        session_id = state.current_session
        driver.quit()
        del state.drivers[state.current_session]
        state.current_session = None
        return f"Browser session {session_id} closed."

# ==============================================================================
# 4. MCP TOOL DEFINITIONS (The 'Controller' Layer)
# ==============================================================================

def _handle_request(func, **kwargs):
    """Generic request handler to wrap service calls with error handling."""
    try:
        result = func(**kwargs)
        return {"content": [{"type": "text", "text": str(result)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
async def start_browser(request: StartBrowserRequest):
    """Launches a new browser session (Chrome or Firefox)."""
    service = SeleniumService()
    options = request.options or BrowserOptions()
    # Force headless to False for testing - ignore any request setting
    options.headless = False
    return _handle_request(
        service.start_browser,
        browser_type=request.browser,
        options=options
    )

@mcp.tool()
async def navigate(request: NavigateRequest):
    """Navigates the current browser session to a specified URL."""
    service = SeleniumService()
    try:
        driver = service._get_driver()
        driver.get(request.url)
        return {"content": [{"type": "text", "text": f"Successfully navigated to {request.url}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Navigation failed: {str(e)}"}]}


@mcp.tool()
async def click_element(request: ElementLocator):
    """Finds an element by a locator and clicks it."""
    service = SeleniumService()
    return _handle_request(service.click_element, **request.model_dump())

@mcp.tool()
async def send_keys(request: SendKeysRequest):
    """Sends a sequence of keys to an element."""
    service = SeleniumService()
    return _handle_request(service.send_keys, **request.model_dump())

@mcp.tool()
async def get_element_text(request: ElementLocator):
    """Retrieves the text content of an element."""
    service = SeleniumService()
    return _handle_request(service.get_element_text, **request.model_dump())

@mcp.tool()
async def get_page_content():
    """Retrieves the full HTML source of the current page."""
    service = SeleniumService()
    # Truncate for safety in response
    content = service.get_page_content()[:20000]
    return {"content": [{"type": "text", "text": content}]}

@mcp.tool()
async def take_screenshot():
    """Captures a screenshot of the current page and saves it to mcp-revised/data/selenium/ss.png"""
    service = SeleniumService()
    return _handle_request(service.take_screenshot)

@mcp.tool()
async def close_session():
    """Closes the current browser session and WebDriver."""
    service = SeleniumService()
    return _handle_request(service.close_session)

# ==============================================================================
# 5. SERVER EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("Starting Selenium MCP Server...")
    mcp.run()