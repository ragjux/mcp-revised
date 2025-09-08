#!/usr/bin/env python3
"""
CAPTCHA Solver MCP Server - FastMCP version
A Model Context Protocol (MCP) server for solving various types of CAPTCHAs using Google Gemini AI.
"""

import asyncio
import base64
import io
import json
import logging
import os
from typing import Any, Dict, Optional, Union

import google.generativeai as genai
import PIL.Image
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"captcha_{name}", "args": kwargs}

# Environment variables for Google Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY environment variable")

# Configure Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)

mcp = FastMCP("CAPTCHA Solver MCP")

class CaptchaSolver:
    """Core CAPTCHA solving functionality using Gemini AI"""
    
    def __init__(self):
        logging.info("Initializing CaptchaSolver with Gemini AI models")
        try:
            self.math_model = genai.GenerativeModel('gemini-2.5-pro')
            self.text_model = genai.GenerativeModel('gemini-2.5-pro')
            logging.info("Successfully initialized Gemini AI models: gemini-2.5-flash-image-preview and gemini-2.5-flash-image-preview")
        except Exception as e:
            logging.error(f"Error initializing Gemini AI models: {e}")
            raise
    
    def solve_math_captcha(self, image: PIL.Image.Image) -> Optional[str]:
        """Solve math-based CAPTCHA using Gemini 2.5 Flash Image Preview"""
        logging.info("Starting math CAPTCHA solving process")
        
        try:
            response = self.math_model.generate_content(
                [
                    "This is a math captcha. Calculate and return ONLY the numeric result.",
                    image
                ],
                generation_config={"temperature": 0}
            )
            
            captcha_text = response.text.strip()
            logging.info(f"Extracted math result: '{captcha_text}'")
            
            if captcha_text.isdigit():
                logging.info(f"Math CAPTCHA solved successfully: '{captcha_text}'")
                return captcha_text
            else:
                logging.warning(f"Extracted text '{captcha_text}' is not numeric")
                return None
                
        except Exception as e:
            logging.error(f"Error solving math captcha: {e}")
            return None
    
    def solve_text_captcha(self, image: PIL.Image.Image) -> Optional[str]:
        """Solve alphanumeric text CAPTCHA using Gemini 2.5 Flash Image Preview"""
        logging.info("Starting text CAPTCHA solving process")
        
        try:
            response = self.text_model.generate_content(
                [
                    "OCR task: Analyze this CAPTCHA image and only output the alphanumeric text you see, nothing else. Here is the image: ",
                    image
                ],
                generation_config={
                    "temperature": 0,
                    "max_output_tokens": 1000,
                }
            )
            
            captcha_text = response.text.strip()
            logging.info(f"Extracted CAPTCHA text: '{captcha_text}'")
            
            if captcha_text.isalnum():
                logging.info(f"CAPTCHA solved successfully: '{captcha_text}'")
                return captcha_text
            else:
                logging.warning(f"Extracted text '{captcha_text}' is not alphanumeric")
                return None
                
        except Exception as e:
            logging.error(f"Error solving text captcha: {e}")
            return None
    
    def solve_auto_captcha(self, image: PIL.Image.Image, captcha_type: str = "auto") -> Optional[str]:
        """Auto-detect CAPTCHA type and solve accordingly"""
        logging.info(f"Starting auto CAPTCHA solving with type: '{captcha_type}'")
        
        if captcha_type == "math":
            return self.solve_math_captcha(image)
        elif captcha_type == "text":
            return self.solve_text_captcha(image)
        else:
            # Try text first (more common), then math
            result = self.solve_text_captcha(image)
            if result is not None:
                return result
            else:
                return self.solve_math_captcha(image)

# Initialize CAPTCHA solver
captcha_solver = CaptchaSolver()

def base64_to_image(base64_data: str) -> PIL.Image.Image:
    """Convert base64 string to PIL Image"""
    logging.info("Starting base64 to image conversion")
    
    try:
        # Handle Playwright screenshot response format
        if "Base64 data: " in base64_data:
            base64_data = base64_data.split("Base64 data: ")[-1].strip()
        
        # Remove data URL prefix if present
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]
        
        image_data = base64.b64decode(base64_data)
        image = PIL.Image.open(io.BytesIO(image_data))
        logging.info(f"Successfully created image: {image.size}, mode: {image.mode}")
        
        return image
    except Exception as e:
        logging.error(f"Error converting base64 to image: {e}")
        raise

def load_image_from_file() -> PIL.Image.Image:
    """Load image from ss.png file written by screenshot tool"""
    logging.info("Starting image loading from file")
    
    try:
        # Look for ss.png in the data/selenium directory
        screenshot_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'selenium', 'ss.png')
        
        if not os.path.exists(screenshot_file_path):
            raise FileNotFoundError(f"ss.png not found: {screenshot_file_path}")
        
        image = PIL.Image.open(screenshot_file_path)
        logging.info(f"Successfully loaded image from {screenshot_file_path}: {image.size}, mode: {image.mode}")
        return image
        
    except Exception as e:
        logging.error(f"Error loading image from file: {e}")
        raise

def delete_temp_image():
    """Delete the temporary ss.png file after processing"""
    try:
        screenshot_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'selenium', 'ss.png')
        if os.path.exists(screenshot_file_path):
            os.remove(screenshot_file_path)
            logging.debug(f"Deleted temporary file: {screenshot_file_path}")
    except Exception as e:
        logging.warning(f"Failed to delete temporary file: {e}")

@mcp.tool()
def captcha_solve_math() -> Dict[str, Any]:
    """Solve math-based CAPTCHA (e.g., '5 + 3 = ?'). Reads image from ss.png file. Returns only the numeric result."""
    if DRY_RUN:
        return _dry("solve_math")
    
    try:
        image = load_image_from_file()
        result = captcha_solver.solve_math_captcha(image)
        delete_temp_image()
        
        if result:
            return {"status": "success", "result": result, "type": "math"}
        else:
            return {"status": "error", "message": "Failed to solve math CAPTCHA"}
    except Exception as e:
        delete_temp_image()
        return {"status": "error", "message": f"Error: {str(e)}"}

@mcp.tool()
def captcha_solve_text() -> Dict[str, Any]:
    """Solve alphanumeric text CAPTCHA using OCR. Reads image from ss.png file. Returns only the text characters."""
    if DRY_RUN:
        return _dry("solve_text")
    
    try:
        image = load_image_from_file()
        result = captcha_solver.solve_text_captcha(image)
        delete_temp_image()
        
        if result:
            return {"status": "success", "result": result, "type": "text"}
        else:
            return {"status": "error", "message": "Failed to solve text CAPTCHA"}
    except Exception as e:
        delete_temp_image()
        return {"status": "error", "message": f"Error: {str(e)}"}

@mcp.tool()
def captcha_solve_auto(captcha_type: str = "auto") -> Dict[str, Any]:
    """Auto-detect CAPTCHA type and solve accordingly. Reads image from ss.png file. Tries text recognition first, then math if needed."""
    if DRY_RUN:
        return _dry("solve_auto", captcha_type=captcha_type)
    
    try:
        image = load_image_from_file()
        result = captcha_solver.solve_auto_captcha(image, captcha_type)
        delete_temp_image()
        
        if result:
            return {"status": "success", "result": result, "type": "auto"}
        else:
            return {"status": "error", "message": "Failed to solve CAPTCHA"}
    except Exception as e:
        delete_temp_image()
        return {"status": "error", "message": f"Error: {str(e)}"}

@mcp.tool()
def captcha_solve_from_base64(base64_data: str, captcha_type: str = "auto") -> Dict[str, Any]:
    """Solve CAPTCHA from base64 image data. Supports math, text, and auto-detection."""
    if DRY_RUN:
        return _dry("solve_from_base64", captcha_type=captcha_type)
    
    try:
        image = base64_to_image(base64_data)
        result = captcha_solver.solve_auto_captcha(image, captcha_type)
        
        if result:
            return {"status": "success", "result": result, "type": captcha_type}
        else:
            return {"status": "error", "message": "Failed to solve CAPTCHA"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
