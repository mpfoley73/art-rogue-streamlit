"""Utilities to query museum APIs (CMA and MET) and normalize results.

This is a small, defensive port of the R helpers in ../art-rogue/R/*.R
"""
from __future__ import annotations

import random
from typing import Any, Dict, List
import requests
from urllib.parse import quote_plus

CMA_API = "https://openaccess-api.clevelandart.org/api/artworks/"
MET_API = "https://collectionapi.metmuseum.org/public/collection/v1/"

CMA_LABEL = "Cleveland (CMA)"
MET_LABEL = "Metropolitan (MMA)"


def fx_search_cma(q: str = "", highlight: bool = False) -> List[Dict[str, Any]]:
    if q == "*":
        q = ""
    highlight_q = "&highlight=1" if highlight else ""
    url = f"{CMA_API}?q={quote_plus(q)}&has_image=1&limit=100{highlight_q}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data", []) or []
    if not data:
        return []
    k = min(5, len(data))
    try:
        sampled = random.sample(data, k=k)
    except ValueError:
        sampled = data[:k]
    return sampled


def fx_search_met(q: str = "*", highlight: bool = False) -> List[Dict[str, Any]]:
    # Build search url. The MET API returns objectIDs for the query.
    highlight_q = "&isHighlight=true" if highlight else ""
    url = (
        f"{MET_API}search?isHighlight=true&isOnView=true&hasImages=true&q={quote_plus(q)}{highlight_q}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    result_set = resp.json()
    object_ids = result_set.get("objectIDs") or []
    if not object_ids:
        return []
    k = min(5, len(object_ids))
    sampled_ids = random.sample(object_ids, k=k)
    artworks = []
    for obj_id in sampled_ids:
        try:
            obj_url = f"{MET_API}objects/{obj_id}"
            r = requests.get(obj_url, timeout=10)
            r.raise_for_status()
            art = r.json()
            artworks.append(art)
        except Exception:
            # Skip problematic IDs
            continue
    return artworks


def fx_search(api_label: str, q: str, highlight: bool = False) -> List[Dict[str, Any]]:
    if api_label == CMA_LABEL:
        return fx_search_cma(q, highlight=highlight)
    if api_label == MET_LABEL:
        return fx_search_met(q, highlight=highlight)
    return []


def fx_search_result(api_label: str, artwork: Dict[str, Any]) -> Dict[str, str]:
    # Normalize a couple of common fields for display in the UI.
    if not artwork:
        return {"img_url": "", "title": "", "artist": "", "creation_date": ""}

    if api_label == CMA_LABEL:
        img_url = artwork.get("images", {}).get("web", {}).get("url", "")
        title = artwork.get("title", "")
        creators = artwork.get("creators") or []
        artist = ""
        if creators and isinstance(creators, list) and len(creators) > 0:
            first = creators[0]
            artist = first.get("description") or first.get("display") or ""
        creation_date = artwork.get("creation_date", "")
    elif api_label == MET_LABEL:
        img_url = artwork.get("primaryImageSmall", "")
        title = artwork.get("title", "")
        artist = artwork.get("artist", "")
        creation_date = artwork.get("objectDate", "")
    else:
        img_url = ""
        title = ""
        artist = ""
        creation_date = ""

    return {
        "img_url": img_url or "",
        "title": title or "",
        "artist": artist or "",
        "creation_date": creation_date or "",
    }
