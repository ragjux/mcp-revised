import os, json
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s(%s)", name, kwargs)
    return {"dry_run": True, "tool": f"slides_{name}", "args": kwargs}

ACCESS_TOKEN = os.getenv("GSLIDES_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("GSLIDES_REFRESH_TOKEN")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    raise RuntimeError("Set GSLIDES_ACCESS_TOKEN and GSLIDES_REFRESH_TOKEN")

mcp = FastMCP("Google Slides MCP (native)")

def get_slides_service():
    """Initialize and return the Google Slides service."""
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
        logging.error(f"Failed to initialize Google Slides service: {e}")
        raise RuntimeError(f"Failed to initialize Google Slides service: {e}")

@mcp.tool()
def gs_create_presentation(title: str) -> Dict[str, Any]:
    """Create a new Google Slides presentation."""
    if DRY_RUN:
        return _dry("gs_create_presentation", title=title)
    try:
        logging.info(f"Creating presentation: {title}")
        service = get_slides_service()
        presentation = service.presentations().create(
            body={"title": title}
        ).execute()
        return presentation
    except Exception as e:
        logging.error(f"Error creating presentation: {e}")
        raise

@mcp.tool()
def gs_get_presentation(presentationId: str) -> Dict[str, Any]:
    """Get details about a Google Slides presentation."""
    if DRY_RUN:
        return _dry("gs_get_presentation", presentationId=presentationId)
    try:
        service = get_slides_service()
        presentation = service.presentations().get(
            presentationId=presentationId
        ).execute()
        return presentation
    except Exception as e:
        logging.error(f"Error getting presentation: {e}")
        raise

@mcp.tool()
def gs_batch_update_presentation(presentationId: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply a batch of updates to a Google Slides presentation."""
    if DRY_RUN:
        return _dry("gs_batch_update_presentation", presentationId=presentationId, requests=requests)
    try:
        service = get_slides_service()
        response = service.presentations().batchUpdate(
            presentationId=presentationId,
            body={"requests": requests}
        ).execute()
        return response
    except Exception as e:
        logging.error(f"Error batch updating presentation: {e}")
        raise

@mcp.tool()
def gs_get_page(presentationId: str, pageObjectId: str) -> Dict[str, Any]:
    """Get details about a specific page (slide) in a presentation."""
    if DRY_RUN:
        return _dry("gs_get_page", presentationId=presentationId, pageObjectId=pageObjectId)
    try:
        service = get_slides_service()
        presentation = service.presentations().get(
            presentationId=presentationId
        ).execute()
        
        # Find the specific page
        page = next(
            (p for p in presentation.get("slides", []) if p.get("objectId") == pageObjectId),
            None
        )
        
        if not page:
            raise ValueError(f"Page with ID {pageObjectId} not found")
        
        return page
    except Exception as e:
        logging.error(f"Error getting page: {e}")
        raise

@mcp.tool()
def gs_summarize_presentation(presentationId: str, include_notes: bool = False) -> Dict[str, Any]:
    """Extract text content from all slides in a presentation.
    
    Args:
        presentationId: The ID of the presentation to summarize.
        include_notes: Optional. Whether to include speaker notes in the summary.
    """
    if DRY_RUN:
        return _dry("gs_summarize_presentation", presentationId=presentationId, include_notes=include_notes)
    try:
        service = get_slides_service()
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
        
        return summary
    except Exception as e:
        logging.error(f"Error summarizing presentation: {e}")
        raise

if __name__ == "__main__":
    mcp.run()