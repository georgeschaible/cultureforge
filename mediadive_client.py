"""MediaDive client (Phase 2d Task 2.1).

Thin wrapper around the cached MediaDive data with optional live-API fallback.
Cache layer: data/mediadive/media/*.json + the `mediadive_cache` SQLite table.
Live API: https://mediadive.dsmz.de/rest

Most calls hit the cache. Live API fetches only happen when:
  - The medium_id isn't in the local cache (uncommon)
  - Caller passes use_live=True to force a refresh
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

import requests

_ROOT = Path(__file__).parent
_API_BASE = "https://mediadive.dsmz.de/rest"
_CACHE_DIR = _ROOT / "data" / "mediadive" / "media"
_MS_CACHE_DIR = _ROOT / "data" / "mediadive" / "medium_strains"
_TIMEOUT = 15
_SLEEP = 0.2


def _live_get(path: str) -> dict:
    """Hit the live API with a small rate-limit delay. Returns parsed JSON."""
    time.sleep(_SLEEP)
    r = requests.get(f"{_API_BASE}/{path}", timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_medium_by_id(medium_id, conn: Optional[sqlite3.Connection] = None,
                        use_live: bool = False) -> dict:
    """Fetch a single medium recipe by MediaDive ID. Cache-primary."""
    mid = str(medium_id)
    if not use_live:
        # 1. SQLite cache
        if conn is not None:
            row = conn.execute(
                "SELECT response_json FROM mediadive_cache WHERE medium_id = ?",
                (mid,)
            ).fetchone()
            if row:
                return json.loads(row[0])
        # 2. Filesystem JSON
        path = _CACHE_DIR / f"{mid}.json"
        if path.exists():
            return json.loads(path.read_text())
    # 3. Live API
    payload = _live_get(f"medium/{mid}")
    # Normalize: live response wraps under "data"; legacy local files are unwrapped.
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
        return payload["data"]
    return payload


def fetch_media_for_strain(bacdive_id: int,
                             conn: Optional[sqlite3.Connection] = None) -> List[str]:
    """Return list of medium_ids that cultivate the given BacDive strain.

    The MediaDive REST API does NOT expose strain → media (forward only).
    This implementation derives the reverse from cached medium_strains data.
    """
    medium_ids: list = []
    if conn is not None:
        rows = conn.execute(
            "SELECT medium_id FROM organism_to_published_media "
            "WHERE bacdive_id = ?",
            (bacdive_id,)
        ).fetchall()
        if rows:
            return [r[0] for r in rows]
    # Fall back to scanning the local medium_strains files
    for fn in os.listdir(_MS_CACHE_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            d = json.load(open(_MS_CACHE_DIR / fn))
        except Exception:
            continue
        for s in d:
            if s.get("bacdive_id") == bacdive_id and s.get("growth") == 1:
                medium_ids.append(fn[:-5])
                break
    return medium_ids


def search_media_by_organism(species_name: str,
                              conn: Optional[sqlite3.Connection] = None) -> List[dict]:
    """Search MediaDive medium_strains data for media linked to a species name.

    Returns a list of `{medium_id, bacdive_id}` dicts. Uses cached data only.
    """
    out: list = []
    seen: set = set()
    for fn in os.listdir(_MS_CACHE_DIR):
        if not fn.endswith(".json"):
            continue
        mid = fn[:-5]
        try:
            d = json.load(open(_MS_CACHE_DIR / fn))
        except Exception:
            continue
        for s in d:
            if (s.get("species") == species_name and s.get("growth") == 1
                    and (mid, s.get("bacdive_id")) not in seen):
                seen.add((mid, s.get("bacdive_id")))
                out.append({"medium_id": mid, "bacdive_id": s.get("bacdive_id")})
    return out


def get_medium_ingredients(medium_id, conn: sqlite3.Connection) -> List[dict]:
    """Return ingredient list for a medium from the parsed `media_compounds`
    table (preferred — already normalized to per-1L g/L concentrations).
    Falls back to parsing the cached JSON if media_compounds is empty for this id.
    """
    ingredients = []
    # The DB stores media IDs as integers in `media_compounds.media_id` for
    # numeric IDs, but as strings (e.g., 'J232', '1a') for non-numeric IDs.
    # Try both.
    rows = []
    try:
        mid_int = int(str(medium_id))
        rows = conn.execute("""
            SELECT c.name, mc.g_per_L, mc.optional
            FROM media_compounds mc
            JOIN compounds c ON c.id = mc.compound_id
            WHERE mc.media_id = ?
            ORDER BY mc.g_per_L DESC
        """, (mid_int,)).fetchall()
    except (ValueError, TypeError):
        pass
    if not rows:
        rows = conn.execute("""
            SELECT c.name, mc.g_per_L, mc.optional
            FROM media_compounds mc
            JOIN compounds c ON c.id = mc.compound_id
            WHERE mc.media_id = ?
            ORDER BY mc.g_per_L DESC
        """, (str(medium_id),)).fetchall()
    if rows:
        for name, g_per_L, optional in rows:
            ingredients.append({
                "compound": name, "amount": g_per_L, "unit": "g/L",
                "optional": bool(optional) if optional is not None else False,
            })
        return ingredients
    # Fallback: parse the cached JSON
    medium = fetch_medium_by_id(medium_id, conn=conn)
    for sol in medium.get("solutions", []):
        for r in sol.get("recipe", []):
            ingredients.append({
                "compound": r.get("compound"),
                "amount": r.get("g_l", r.get("amount")),
                "unit": "g/L" if r.get("g_l") is not None else r.get("unit"),
                "optional": bool(r.get("optional")),
            })
    return ingredients
