#!/usr/bin/env python3
"""
Reddit MCP Server - FastMCP version
A Model Context Protocol (MCP) server for Reddit.
"""

import os
from typing import Any, Dict, Optional, List
from fastmcp import FastMCP
from dotenv import load_dotenv
import praw

# Load environment variables from .env file
load_dotenv()
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"reddit_{name}", "args": kwargs}

# Required ENV
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# Optional ENV (only required for authenticated operations)
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")  # optional for write ops
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")  # optional for write ops
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-mcp-fastmcp/1.0")

if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    raise RuntimeError("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")

mcp = FastMCP("Reddit MCP (native)")

def _get_reddit(authenticated: bool = False):
    """
    Create PRAW Reddit client.
    - If authenticated=True, requires username and password (script flow).
    - Otherwise, creates a read-only client using client credentials.
    """
    if authenticated:
        if not (REDDIT_USERNAME and REDDIT_PASSWORD):
            raise RuntimeError("Authenticated operations require REDDIT_USERNAME and REDDIT_PASSWORD")
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )
    else:
        # Read-only via client credentials; PRAW treats read as application-only if no username/password
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
    return reddit

# ---------- Read-only tools (client credentials only) ----------

@mcp.tool()
def reddit_get_user_info(username: str) -> Dict[str, Any]:
    """Get detailed user information with basic engagement info."""
    if DRY_RUN:
        return _dry("get_user_info", username=username)
    try:
        reddit = _get_reddit(False)
        user = reddit.redditor(username)
        data = {
            "name": user.name,
            "id": getattr(user, "id", None),
            "comment_karma": getattr(user, "comment_karma", None),
            "link_karma": getattr(user, "link_karma", None),
            "created_utc": getattr(user, "created_utc", None),
            "is_mod": getattr(user, "is_mod", None),
            "is_gold": getattr(user, "is_gold", None),
        }
        return {"user": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch user info: {e}"}

@mcp.tool()
def reddit_get_top_posts(subreddit: str, time_filter: str = "week", limit: int = 10) -> Dict[str, Any]:
    """Get and analyze top posts from a subreddit (time_filter: hour, day, week, month, year, all)."""
    if DRY_RUN:
        return _dry("get_top_posts", subreddit=subreddit, time_filter=time_filter, limit=limit)
    try:
        reddit = _get_reddit(False)
        sr = reddit.subreddit(subreddit)
        posts = []
        for s in sr.top(time_filter=time_filter, limit=limit):
            posts.append({
                "id": s.id,
                "title": s.title,
                "score": s.score,
                "num_comments": s.num_comments,
                "url": s.url,
                "permalink": f"https://www.reddit.com{s.permalink}",
                "created_utc": s.created_utc,
                "author": str(s.author) if s.author else None,
            })
        return {"subreddit": subreddit, "time_filter": time_filter, "posts": posts, "count": len(posts)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch top posts: {e}"}

@mcp.tool()
def reddit_get_subreddit_stats(subreddit: str) -> Dict[str, Any]:
    """Get comprehensive subreddit info: subscribers, active users, etc."""
    if DRY_RUN:
        return _dry("get_subreddit_stats", subreddit=subreddit)
    try:
        reddit = _get_reddit(False)
        sr = reddit.subreddit(subreddit)
        info = {
            "display_name": sr.display_name,
            "title": sr.title,
            "subscribers": getattr(sr, "subscribers", None),
            "active_user_count": getattr(sr, "active_user_count", None),
            "description": getattr(sr, "public_description", None),
            "created_utc": getattr(sr, "created_utc", None),
            "over18": getattr(sr, "over18", None),
        }
        return {"subreddit": subreddit, "stats": info}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch subreddit stats: {e}"}

@mcp.tool()
def reddit_get_trending_subreddits(limit: int = 10) -> Dict[str, Any]:
    """Get trending subreddits (Reddit's featured/trending listing)."""
    if DRY_RUN:
        return _dry("get_trending_subreddits", limit=limit)
    try:
        reddit = _get_reddit(False)
        trending = []
        for s in reddit.subreddits.popular(limit=limit):
            trending.append({
                "display_name": s.display_name,
                "subscribers": getattr(s, "subscribers", None),
                "description": getattr(s, "public_description", None),
                "url": f"https://www.reddit.com/r/{s.display_name}/",
            })
        return {"trending": trending, "count": len(trending)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch trending subreddits: {e}"}

@mcp.tool()
def reddit_get_submission_by_url(url: str) -> Dict[str, Any]:
    """Get a Reddit submission by URL."""
    if DRY_RUN:
        return _dry("get_submission_by_url", url=url)
    try:
        reddit = _get_reddit(False)
        sub = reddit.submission(url=url)
        data = {
            "id": sub.id,
            "title": sub.title,
            "score": sub.score,
            "num_comments": sub.num_comments,
            "author": str(sub.author) if sub.author else None,
            "created_utc": sub.created_utc,
            "permalink": f"https://www.reddit.com{sub.permalink}"
        }
        return {"submission": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch submission: {e}"}

@mcp.tool()
def reddit_get_submission_by_id(submission_id: str) -> Dict[str, Any]:
    """Get a Reddit submission by ID."""
    if DRY_RUN:
        return _dry("get_submission_by_id", submission_id=submission_id)
    try:
        reddit = _get_reddit(False)
        sub = reddit.submission(id=submission_id)
        data = {
            "id": sub.id,
            "title": sub.title,
            "score": sub.score,
            "num_comments": sub.num_comments,
            "author": str(sub.author) if sub.author else None,
            "created_utc": sub.created_utc,
            "permalink": f"https://www.reddit.com{sub.permalink}"
        }
        return {"submission": data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch submission: {e}"}

# ---------- Authenticated tools (require username/password) ----------

@mcp.tool()
def reddit_who_am_i() -> Dict[str, Any]:
    """Get information about the currently authenticated user."""
    if DRY_RUN:
        return _dry("who_am_i")
    try:
        reddit = _get_reddit(True)
        me = reddit.user.me()
        return {"user": {"name": me.name, "id": getattr(me, "id", None)}}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get current user: {e}"}

@mcp.tool()
def reddit_create_post(subreddit: str, title: str, content: Optional[str] = None, flair: Optional[str] = None, is_self: bool = True) -> Dict[str, Any]:
    """Create a post in a subreddit (authenticated)."""
    if DRY_RUN:
        return _dry("create_post", subreddit=subreddit, title=title, content=content, flair=flair, is_self=is_self)
    try:
        reddit = _get_reddit(True)
        sr = reddit.subreddit(subreddit)
        if is_self:
            submission = sr.submit(title=title, selftext=content or "")
        else:
            submission = sr.submit(title=title, url=content or "")
        if flair:
            # flair by name may require flair templates; this sets flair text if supported
            try:
                submission.flair.select(text=flair)
            except Exception:
                pass
        return {"status": "success", "post_id": submission.id, "permalink": f"https://www.reddit.com{submission.permalink}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create post: {e}"}

@mcp.tool()
def reddit_reply_to_post(post_id: str, content: str, subreddit: Optional[str] = None) -> Dict[str, Any]:
    """Reply to a post (authenticated)."""
    if DRY_RUN:
        return _dry("reply_to_post", post_id=post_id, content=content, subreddit=subreddit)
    try:
        reddit = _get_reddit(True)
        sub = reddit.submission(id=post_id)
        comment = sub.reply(content)
        return {"status": "success", "comment_id": comment.id, "permalink": f"https://www.reddit.com{comment.permalink}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to reply to post: {e}"}

@mcp.tool()
def reddit_reply_to_comment(comment_id: str, content: str, subreddit: Optional[str] = None) -> Dict[str, Any]:
    """Reply to a comment (authenticated)."""
    if DRY_RUN:
        return _dry("reply_to_comment", comment_id=comment_id, content=content, subreddit=subreddit)
    try:
        reddit = _get_reddit(True)
        comment = reddit.comment(id=comment_id)
        reply = comment.reply(content)
        return {"status": "success", "comment_id": reply.id, "permalink": f"https://www.reddit.com{reply.permalink}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to reply to comment: {e}"}

if __name__ == "__main__":
    mcp.run()
