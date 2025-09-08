#!/usr/bin/env python3
"""
YouTube MCP Server - FastMCP version
Implements YouTube Data API v3 tools for videos, channels, playlists, and transcripts.
"""

import os
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()
from googleapiclient.discovery import build  # pip install google-api-python-client

# Optional transcripts: pip install youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    HAS_TRANSCRIPTS = True
except Exception:
    HAS_TRANSCRIPTS = False

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

API_KEY = os.getenv("YOUTUBE_API_KEY", "")
DEFAULT_TRANSCRIPT_LANG = os.getenv("YOUTUBE_TRANSCRIPT_LANG", "en")

if not API_KEY:
    raise RuntimeError("Set YOUTUBE_API_KEY")

mcp = FastMCP("YouTube MCP (native)")

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"youtube_{name}", "args": kwargs}

def _yt():
    return build("youtube", "v3", developerKey=API_KEY)

# ---------- Videos ----------

@mcp.tool()
def youtube_get_video_details(video_id: str) -> Dict[str, Any]:
    """Get video details including snippet, contentDetails, statistics."""
    if DRY_RUN:
        return _dry("get_video_details", video_id=video_id)
    yt = _yt()
    resp = yt.videos().list(part="snippet,contentDetails,statistics", id=video_id).execute()
    return resp

@mcp.tool()
def youtube_get_video_statistics(video_id: str) -> Dict[str, Any]:
    """Get video statistics."""
    if DRY_RUN:
        return _dry("get_video_statistics", video_id=video_id)
    yt = _yt()
    resp = yt.videos().list(part="statistics", id=video_id).execute()
    return resp

@mcp.tool()
def youtube_search_videos(query: str, max_results: int = 10, page_token: Optional[str] = None) -> Dict[str, Any]:
    """Search videos across YouTube; returns IDs and snippets. Use youtube_get_video_details for durations/stats."""
    if DRY_RUN:
        return _dry("search_videos", query=query, max_results=max_results, page_token=page_token)
    yt = _yt()
    resp = yt.search().list(q=query, type="video", part="snippet", maxResults=max_results, pageToken=page_token).execute()
    return resp  # duration not included per API; fetch via videos.list [6]

# ---------- Transcripts ----------

@mcp.tool()
def youtube_get_transcript(video_id: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve video transcript with timestamps if available."""
    if DRY_RUN:
        return _dry("get_transcript", video_id=video_id, language=language)
    if not HAS_TRANSCRIPTS:
        return {"status": "error", "message": "youtube-transcript-api not installed"}
    lang = language or DEFAULT_TRANSCRIPT_LANG
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en"])
        return {"video_id": video_id, "language": lang, "transcript": transcript}
    except TranscriptsDisabled:
        return {"status": "error", "message": "Transcripts disabled for this video"}
    except NoTranscriptFound:
        return {"status": "error", "message": "No transcript found for requested languages"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------- Channels ----------

@mcp.tool()
def youtube_get_channel_details(channel_id: str) -> Dict[str, Any]:
    """Get channel details including statistics."""
    if DRY_RUN:
        return _dry("get_channel_details", channel_id=channel_id)
    yt = _yt()
    resp = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    return resp

@mcp.tool()
def youtube_list_channel_videos(channel_id: str, max_results: int = 50, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List channel videos via search endpoint filtered by channelId."""
    if DRY_RUN:
        return _dry("list_channel_videos", channel_id=channel_id, max_results=max_results, page_token=page_token)
    yt = _yt()
    resp = yt.search().list(channelId=channel_id, part="snippet", type="video", order="date",
                            maxResults=max_results, pageToken=page_token).execute()
    return resp

# ---------- Playlists ----------

@mcp.tool()
def youtube_get_playlist_details(playlist_id: str) -> Dict[str, Any]:
    """Get playlist details."""
    if DRY_RUN:
        return _dry("get_playlist_details", playlist_id=playlist_id)
    yt = _yt()
    resp = yt.playlists().list(part="snippet,contentDetails", id=playlist_id).execute()
    return resp

@mcp.tool()
def youtube_list_playlist_items(playlist_id: str, max_results: int = 50, page_token: Optional[str] = None) -> Dict[str, Any]:
    """List playlist items; follow nextPageToken to get all."""
    if DRY_RUN:
        return _dry("list_playlist_items", playlist_id=playlist_id, max_results=max_results, page_token=page_token)
    yt = _yt()
    resp = yt.playlistItems().list(part="snippet,contentDetails", playlistId=playlist_id,
                                   maxResults=max_results, pageToken=page_token).execute()
    return resp  # use nextPageToken to paginate all items [8]

if __name__ == "__main__":
    mcp.run()
