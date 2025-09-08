#!/usr/bin/env python3
"""
Google Maps MCP Server - FastMCP version
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from fastmcp import FastMCP
from dotenv import load_dotenv
import googlemaps

# Load environment variables from .env file
load_dotenv()
from datetime import datetime
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

def _dry(name: str, **kwargs):
    logging.info("DRY_RUN: %s %s", name, kwargs)
    return {"dry_run": True, "tool": f"maps_{name}", "args": kwargs}

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
SCOPES = os.getenv("GOOGLE_MAPS_SCOPES", "https://www.googleapis.com/auth/mapsplatform.places,https://www.googleapis.com/auth/mapsplatform.directions,https://www.googleapis.com/auth/mapsplatform.elevation")

if not API_KEY:
    raise RuntimeError("Set GOOGLE_MAPS_API_KEY environment variable")

mcp = FastMCP("Google Maps MCP (native)")

def _client() -> googlemaps.Client:
    return googlemaps.Client(key=API_KEY)

# 1) search_nearby: Places Nearby Search [2][5]
@mcp.tool()
def maps_search_nearby(
    latitude: float,
    longitude: float,
    radius: int = 1000,
    keyword: Optional[str] = None,
    language: Optional[str] = None,
    min_rating: Optional[float] = None,
    open_now: Optional[bool] = None,
    type: Optional[str] = None
) -> Dict[str, Any]:
    """Search nearby places based on location with optional filters."""
    if DRY_RUN:
        return _dry("search_nearby", latitude=latitude, longitude=longitude, radius=radius, keyword=keyword,
                    language=language, min_rating=min_rating, open_now=open_now, type=type)
    try:
        gmaps = _client()
        location = (latitude, longitude)
        resp = gmaps.places_nearby(
            location=location,
            radius=radius,
            keyword=keyword,
            language=language,
            open_now=open_now,
            type=type
        )
        results = resp.get("results", [])
        if min_rating is not None:
            results = [r for r in results if r.get("rating", 0) >= float(min_rating)]
        return {
            "query": {"location": {"lat": latitude, "lng": longitude}, "radius": radius, "keyword": keyword, "type": type},
            "results": results,
            "count": len(results),
            "status": resp.get("status")
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed nearby search: {e}"}

# 2) get_place_details: Place Details [2][5]
@mcp.tool()
def maps_get_place_details(place_id: str, language: Optional[str] = None, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get detailed information for a place by place_id."""
    if DRY_RUN:
        return _dry("get_place_details", place_id=place_id, language=language, fields=fields)
    try:
        gmaps = _client()
        resp = gmaps.place(place_id=place_id, language=language, fields=fields)
        return {"place_id": place_id, "result": resp.get("result"), "status": resp.get("status")}
    except Exception as e:
        return {"status": "error", "message": f"Failed place details: {e}"}

# 3) maps_geocode: Geocoding API [2][5][7]
@mcp.tool()
def maps_geocode(address: str, language: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """Convert addresses to coordinates."""
    if DRY_RUN:
        return _dry("maps_geocode", address=address, language=language, region=region)
    try:
        gmaps = _client()
        res = gmaps.geocode(address, language=language, region=region)
        return {"address": address, "results": res, "count": len(res)}
    except Exception as e:
        return {"status": "error", "message": f"Failed geocode: {e}"}

# 4) maps_reverse_geocode: Reverse Geocoding API [2][5]
@mcp.tool()
def maps_reverse_geocode(latitude: float, longitude: float, language: Optional[str] = None) -> Dict[str, Any]:
    """Convert coordinates to an address."""
    if DRY_RUN:
        return _dry("maps_reverse_geocode", latitude=latitude, longitude=longitude, language=language)
    try:
        gmaps = _client()
        res = gmaps.reverse_geocode((latitude, longitude), language=language)
        return {"location": {"lat": latitude, "lng": longitude}, "results": res, "count": len(res)}
    except Exception as e:
        return {"status": "error", "message": f"Failed reverse geocode: {e}"}

# 5) maps_distance_matrix: Distance Matrix API [3][5][10]
@mcp.tool()
def maps_distance_matrix(
    origins: List[str],
    destinations: List[str],
    mode: Optional[str] = None,  # driving, walking, bicycling, transit
    language: Optional[str] = None,
    units: Optional[str] = None,  # metric/imperial
    arrival_time: Optional[int] = None,
    departure_time: Optional[int] = None
) -> Dict[str, Any]:
    """Calculate travel distances and durations between origins and destinations."""
    if DRY_RUN:
        return _dry("maps_distance_matrix", origins=origins, destinations=destinations, mode=mode,
                    language=language, units=units, arrival_time=arrival_time, departure_time=departure_time)
    try:
        gmaps = _client()
        resp = gmaps.distance_matrix(
            origins=origins,
            destinations=destinations,
            mode=mode,
            language=language,
            units=units,
            arrival_time=arrival_time,
            departure_time=departure_time
        )
        return {"origins": resp.get("origin_addresses"), "destinations": resp.get("destination_addresses"),
                "rows": resp.get("rows"), "status": resp.get("status")}
    except Exception as e:
        return {"status": "error", "message": f"Failed distance matrix: {e}"}

# 6) maps_directions: Directions API [2][5]
@mcp.tool()
def maps_directions(
    origin: str,
    destination: str,
    mode: Optional[str] = None,  # driving, walking, bicycling, transit
    language: Optional[str] = None,
    departure_time: Optional[int] = None
) -> Dict[str, Any]:
    """Get turn-by-turn directions between two locations."""
    if DRY_RUN:
        return _dry("maps_directions", origin=origin, destination=destination, mode=mode, language=language, departure_time=departure_time)
    try:
        gmaps = _client()
        resp = gmaps.directions(
            origin=origin,
            destination=destination,
            mode=mode,
            language=language,
            departure_time=departure_time
        )
        return {"routes": resp, "count": len(resp)}
    except Exception as e:
        return {"status": "error", "message": f"Failed directions: {e}"}

# 7) maps_elevation: Elevation API [2][5]
@mcp.tool()
def maps_elevation(locations: List[Dict[str, float]]) -> Dict[str, Any]:
    """Get elevation data for specific locations."""
    if DRY_RUN:
        return _dry("maps_elevation", locations=locations)
    try:
        gmaps = _client()
        coords = [(loc["lat"], loc["lng"]) for loc in locations if "lat" in loc and "lng" in loc]
        res = gmaps.elevation(coords)
        return {"results": res, "count": len(res)}
    except Exception as e:
        return {"status": "error", "message": f"Failed elevation: {e}"}

if __name__ == "__main__":
    mcp.run()
