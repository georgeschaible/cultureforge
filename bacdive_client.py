"""BacDive client (Phase 2d Task 2.2).

Thin wrapper around the cached BacDive data with optional live-API fallback.
Cache layer: data/bacdive/strains/*.json + the `bacdive_cache` SQLite table.
Live API: https://api.bacdive.dsmz.de

Most calls hit the cache. Live API fetches only happen when:
  - The bacdive_id isn't in the local cache (gaps in the Phase 1 download)
  - Caller passes use_live=True to force a refresh
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Tuple

import requests

_ROOT = Path(__file__).parent
_API_BASE = "https://api.bacdive.dsmz.de"
_CACHE_DIR = _ROOT / "data" / "bacdive" / "strains"
_TIMEOUT = 15
_SLEEP = 0.2


def fetch_strain_details(bacdive_id: int,
                          conn: Optional[sqlite3.Connection] = None,
                          use_live: bool = False) -> Optional[dict]:
    """Fetch full strain detail. Returns the strain document (unwrapped from
    the API's `results[bid]` envelope when needed). Cache-primary.
    """
    bid_str = str(bacdive_id)
    if not use_live:
        # 1. SQLite cache
        if conn is not None:
            row = conn.execute(
                "SELECT response_json FROM bacdive_cache WHERE bacdive_id = ?",
                (bacdive_id,)
            ).fetchone()
            if row:
                doc = json.loads(row[0])
                # Cache stores already-unwrapped documents in most cases
                if isinstance(doc, dict) and "results" in doc and bid_str in doc["results"]:
                    return doc["results"][bid_str]
                return doc
        # 2. Filesystem JSON
        path = _CACHE_DIR / f"{bacdive_id}.json"
        if path.exists():
            doc = json.loads(path.read_text())
            if isinstance(doc, dict) and "results" in doc and bid_str in doc["results"]:
                return doc["results"][bid_str]
            return doc
    # 3. Live API
    time.sleep(_SLEEP)
    try:
        r = requests.get(f"{_API_BASE}/fetch/{bacdive_id}", timeout=_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        if "results" in payload and bid_str in payload["results"]:
            return payload["results"][bid_str]
        return payload
    except Exception:
        return None


def search_strain_by_name(species_name: str,
                            conn: sqlite3.Connection) -> List[Tuple[int, str]]:
    """Search the local bacdive_cache for strains matching a species name.

    Returns list of (bacdive_id, species_name) tuples. Substring match.
    The BacDive REST API does not expose a species-name search, so this is
    cache-only by design.
    """
    return conn.execute("""
        SELECT bacdive_id, species_name FROM bacdive_cache
        WHERE species_name LIKE ?
        ORDER BY bacdive_id
    """, (f"%{species_name}%",)).fetchall()


def fetch_strains_by_taxon(taxon_name: str) -> List[int]:
    """Hit the live API's /taxon/{name} endpoint for genus-level enumeration.

    Returns a list of BacDive IDs. Used when the local cache has no entries
    for an organism (rare; only occurs for the 5 ambient-uncultivated organisms
    in the dev/blind set).
    """
    try:
        time.sleep(_SLEEP)
        url = f"{_API_BASE}/taxon/{taxon_name.replace(' ', '%20')}"
        r = requests.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Helper: list BacDive IDs matched to a CultureForge genome
# ---------------------------------------------------------------------------

def get_matched_bacdive_ids(genome_id: int,
                              conn: sqlite3.Connection) -> List[Tuple[int, str, float]]:
    """Return [(bacdive_id, match_method, confidence), ...] for a genome."""
    return conn.execute("""
        SELECT bacdive_id, match_method, match_confidence
        FROM organism_to_bacdive
        WHERE cultureforge_genome_id = ?
        ORDER BY match_confidence DESC
    """, (genome_id,)).fetchall()
