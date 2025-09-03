#!/usr/bin/env python3
import os
import json
import asyncio
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastmcp import FastMCP, tool

# Load environment variables from .env file
load_dotenv()

# Environment variables for authentication
ACCESS_TOKEN = os.getenv("GSLIDES_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("GSLIDES_REFRESH_TOKEN")

def get_slides_service():
    """Initialize and return the Google Slides service."""
    # Check if we have the required tokens
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        print("Warning: GSLIDES_ACCESS_TOKEN and GSLIDES_REFRESH_TOKEN not set - using mock service", file=sys.stderr)
        return None
    
    try:
        # Create credentials using only access and refresh tokens
        credentials = Credentials(
            token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/presentations']
        )
        return build("slides", "v1", credentials=credentials)
    except Exception as e:
        print(f"Warning: Failed to initialize Google Slides service: {e}", file=sys.stderr)
        return None

slides_app = FastMCP(
    title="Google Slides MCP",
    version="0.1.0",
    description="A tool-calling server for interacting with Google Slides."
)

@slides_app.tool()
def create_presentation(title: str) -> Dict[str, Any]:
    """Create a new Google Slides presentation."""
    try:
        service = get_slides_service()
        if not service:
            return {"success": False, "error": "Google Slides service not available - please configure OAuth credentials"}
        
        presentation = service.presentations().create(
            body={"title": title}
        ).execute()
        return {"success": True, "data": presentation}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(slides_app)
def get_presentation(presentationId: str) -> Dict[str, Any]:
    """Get details about a Google Slides presentation."""
    try:
        service = get_slides_service()
        if not service:
            return {"success": False, "error": "Google Slides service not available - please configure OAuth credentials"}
        
        presentation = service.presentations().get(
            presentationId=presentationId
        ).execute()
        return {"success": True, "data": presentation}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(slides_app)
def batch_update_presentation(presentationId: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply a batch of updates to a Google Slides presentation."""
    try:
        service = get_slides_service()
        if not service:
            return {"success": False, "error": "Google Slides service not available - please configure OAuth credentials"}
        
        response = service.presentations().batchUpdate(
            presentationId=presentationId,
            body={"requests": requests}
        ).execute()
        return {"success": True, "data": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(slides_app)
def get_page(presentationId: str, pageObjectId: str) -> Dict[str, Any]:
    """Get details about a specific page (slide) in a presentation."""
    try:
        service = get_slides_service()
        if not service:
            return {"success": False, "error": "Google Slides service not available - please configure OAuth credentials"}
        
        presentation = service.presentations().get(
            presentationId=presentationId
        ).execute()
        
        # Find the specific page
        page = next(
            (p for p in presentation.get("slides", []) if p.get("objectId") == pageObjectId),
            None
        )
        
        if not page:
            return {"success": False, "error": f"Page with ID {pageObjectId} not found"}
        
        return {"success": True, "data": page}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(slides_app)
def summarize_presentation(presentationId: str, include_notes: bool = False) -> Dict[str, Any]:
    """Extract text content from all slides in a presentation.
    
    Args:
        presentationId: The ID of the presentation to summarize.
        include_notes: Optional. Whether to include speaker notes in the summary.
    """
    try:
        service = get_slides_service()
        if not service:
            return {"success": False, "error": "Google Slides service not available - please configure OAuth credentials"}
        
        presentation = service.presentations().get(
            presentationId=presentationId
        ).execute()
        
        summary = {
            "title": presentation.get("title", "Untitled"),
            "slides": []
        }
        
        for slide in presentation.get("slides", []):
            slide_content = {
                "objectId": slide.get("objectId"),
                "text": []
            }
            
            # Extract text from text boxes and shapes
            for element in slide.get("pageElements", []):
                if "shape" in element and "text" in element["shape"]:
                    text_content = element["shape"]["text"].get("textElements", [])
                    for text_element in text_content:
                        if "textRun" in text_element:
                            slide_content["text"].append(text_element["textRun"].get("content", ""))
            
            # Include speaker notes if requested
            if include_notes and "slideProperties" in slide and "notesPage" in slide["slideProperties"]:
                notes_page = slide["slideProperties"]["notesPage"]
                if "pageElements" in notes_page:
                    for element in notes_page["pageElements"]:
                        if "shape" in element and "text" in element["shape"]:
                            text_content = element["shape"]["text"].get("textElements", [])
                            for text_element in text_content:
                                if "textRun" in text_element:
                                    slide_content["text"].append(
                                        f"[Speaker Note]: {text_element['textRun'].get('content', '')}"
                                    )
            
            summary["slides"].append(slide_content)
        
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    """Main function to run the MCP server."""
    # Check required environment variables
    if not all([ACCESS_TOKEN, REFRESH_TOKEN]):
        print("Warning: Missing Google OAuth tokens - server will run in mock mode", file=sys.stderr)
        print("To enable full functionality, set: GSLIDES_ACCESS_TOKEN, GSLIDES_REFRESH_TOKEN", file=sys.stderr)
        
    await slides_app.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())