"""Phase 2d Task 2.3 — populate SQLite cache tables from existing local JSONs.

Reads:
  - data/mediadive/media/*.json           (3,336 medium recipes)
  - data/mediadive/medium_strains/*.json  (2,705 medium → strain mappings)
  - data/bacdive/strains/*.json           (30,538 BacDive strain records)

Writes (in data/cultureforge.db):
  - mediadive_cache              — raw + parsed-summary per medium
  - bacdive_cache                — raw + parsed-summary per strain
  - organism_to_bacdive          — CultureForge genome_id → bacdive_id (when matched)
  - organism_to_published_media  — CultureForge genome_id → MediaDive medium_id

The reverse `bacdive_id → list[medium_id]` index is built into
`organism_to_published_media` via the matching pass.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cultureforge.db"
MEDIA_DIR = ROOT / "data" / "mediadive" / "media"
MS_DIR = ROOT / "data" / "mediadive" / "medium_strains"
BACDIVE_DIR = ROOT / "data" / "bacdive" / "strains"


SCHEMA = """
CREATE TABLE IF NOT EXISTS mediadive_cache (
    medium_id TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    response_json TEXT NOT NULL,
    medium_name TEXT,
    source TEXT,
    min_pH REAL,
    max_pH REAL,
    medium_notes TEXT
);

CREATE TABLE IF NOT EXISTS bacdive_cache (
    bacdive_id INTEGER PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    response_json TEXT NOT NULL,
    species_name TEXT,
    strain_designation TEXT,
    domain TEXT,
    dsm_number TEXT,
    ncbi_taxid INTEGER
);

CREATE TABLE IF NOT EXISTS organism_to_bacdive (
    cultureforge_genome_id INTEGER NOT NULL,
    bacdive_id INTEGER NOT NULL,
    match_method TEXT NOT NULL,  -- 'species_name_exact', 'genus_species_match', 'manual'
    match_confidence REAL,
    PRIMARY KEY (cultureforge_genome_id, bacdive_id)
);

CREATE TABLE IF NOT EXISTS organism_to_published_media (
    cultureforge_genome_id INTEGER NOT NULL,
    medium_id TEXT NOT NULL,
    relationship TEXT NOT NULL,  -- 'direct' (same species) | 'functional_neighbor'
    similarity_score REAL,
    bacdive_id INTEGER,           -- which BacDive strain linked the medium (when known)
    PRIMARY KEY (cultureforge_genome_id, medium_id, relationship)
);

CREATE INDEX IF NOT EXISTS idx_o2b_bacdive ON organism_to_bacdive(bacdive_id);
CREATE INDEX IF NOT EXISTS idx_o2pm_medium ON organism_to_published_media(medium_id);
"""


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def populate_mediadive_cache(conn: sqlite3.Connection) -> int:
    """Populate `mediadive_cache` from local JSONs."""
    n = 0
    for fn in sorted(os.listdir(MEDIA_DIR)):
        if not fn.endswith(".json"):
            continue
        mid = fn[:-5]
        try:
            d = json.load(open(MEDIA_DIR / fn))
        except Exception:
            continue
        med = d.get("medium", {})
        # Some Phase 1 saves wrapped the response under "data"; normalize
        if not med and isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
            inner = d["data"]
            if "medium" in inner:
                med = inner["medium"]
        conn.execute(
            "INSERT OR REPLACE INTO mediadive_cache "
            "(medium_id, fetched_at, response_json, medium_name, source, min_pH, max_pH, medium_notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, _utcnow(), json.dumps(d),
             med.get("name"), med.get("source"),
             med.get("min_pH"), med.get("max_pH"),
             med.get("description") or med.get("reference")),
        )
        n += 1
    conn.commit()
    return n


def _bacdive_summary_fields(d: dict) -> dict:
    """Extract summary fields from a BacDive strain JSON."""
    gen = d.get("General", {}) or {}
    nt = d.get("Name and taxonomic classification", {}) or {}
    species = nt.get("species") or nt.get("full scientific name")
    strain = nt.get("strain designation")
    domain = nt.get("domain")
    dsm = gen.get("DSM-Number")
    if isinstance(dsm, list):
        dsm = dsm[0] if dsm else None
    ncbi = gen.get("NCBI tax id")
    if isinstance(ncbi, list):
        # NCBI tax id is sometimes a list of {Matching level, NCBI tax id} dicts
        for item in ncbi:
            if isinstance(item, dict) and "NCBI tax id" in item:
                ncbi = item["NCBI tax id"]
                break
        else:
            ncbi = ncbi[0] if ncbi else None
    if isinstance(ncbi, dict):
        ncbi = ncbi.get("NCBI tax id")
    try:
        ncbi = int(ncbi) if ncbi else None
    except (TypeError, ValueError):
        ncbi = None
    return {"species": species, "strain": strain, "domain": domain,
            "dsm": str(dsm) if dsm is not None else None, "ncbi": ncbi}


def populate_bacdive_cache(conn: sqlite3.Connection) -> int:
    """Populate `bacdive_cache` from local JSONs."""
    n = 0
    files = sorted(os.listdir(BACDIVE_DIR))
    for i, fn in enumerate(files, 1):
        if not fn.endswith(".json"):
            continue
        bid = int(fn[:-5])
        try:
            d = json.load(open(BACDIVE_DIR / fn))
        except Exception:
            continue
        # The /fetch/{id} response wraps the strain under results[id]; some
        # of the Phase 1 saves are the un-wrapped strain doc directly.
        strain = d
        if isinstance(d, dict) and "results" in d and str(bid) in d["results"]:
            strain = d["results"][str(bid)]
        f = _bacdive_summary_fields(strain)
        conn.execute(
            "INSERT OR REPLACE INTO bacdive_cache "
            "(bacdive_id, fetched_at, response_json, species_name, strain_designation, "
            " domain, dsm_number, ncbi_taxid) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (bid, _utcnow(), json.dumps(strain),
             f["species"], f["strain"], f["domain"], f["dsm"], f["ncbi"]),
        )
        n += 1
        if i % 5000 == 0:
            conn.commit()
            print(f"  bacdive_cache: {i}/{len(files)} loaded")
    conn.commit()
    return n


def build_reverse_index() -> dict:
    """Build bacdive_id → list[(medium_id, growth)] from local medium_strains JSONs."""
    rev: dict = defaultdict(list)
    for fn in os.listdir(MS_DIR):
        if not fn.endswith(".json"):
            continue
        mid = fn[:-5]
        try:
            d = json.load(open(MS_DIR / fn))
        except Exception:
            continue
        for s in d:
            bid = s.get("bacdive_id")
            if bid:
                rev[bid].append((mid, s.get("growth", 1)))
    return rev


# Genus reclassification synonyms — keys are the older / CultureForge name,
# values are the newer name now used in BacDive. Add new entries here when
# species-name mismatches surface during validation.
_GENUS_SYNONYMS = {
    "Methanococcus jannaschii": "Methanocaldococcus jannaschii",
    "Lactobacillus plantarum": "Lactiplantibacillus plantarum",
    "Desulfovibrio vulgaris": "Nitratidesulfovibrio vulgaris",
}


def match_genomes_to_bacdive(conn: sqlite3.Connection) -> int:
    """Match each CultureForge genome to BacDive entries by species name.

    Two-pass matching:
      1. Look up species in MediaDive's medium_strains data (gives strains
         that are explicitly media-linked; preferred for direct comparison).
      2. If nothing found, fall back to bacdive_cache (full BacDive corpus
         including strains not in MediaDive's medium_strains index — these
         are still useful as functional neighbors).
    """
    # Pass 1 source: MediaDive medium_strains
    sp_to_bd_md: dict = defaultdict(set)
    for fn in os.listdir(MS_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            d = json.load(open(MS_DIR / fn))
        except Exception:
            continue
        for s in d:
            sp = (s.get("species") or "").strip()
            bid = s.get("bacdive_id")
            if sp and bid:
                sp_to_bd_md[sp].add(bid)

    # Pass 2 source: bacdive_cache (full corpus). Build species → bacdive_id map
    # from the table (faster than re-reading 30k JSONs).
    sp_to_bd_full: dict = defaultdict(set)
    for bid, sp in conn.execute(
        "SELECT bacdive_id, species_name FROM bacdive_cache WHERE species_name IS NOT NULL"
    ).fetchall():
        sp_to_bd_full[sp].add(bid)

    rows = conn.execute("""
        SELECT g.id, COALESCE(o.species, g.notes, g.accession)
        FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
    """).fetchall()
    n_matched = 0
    for gid, raw_species in rows:
        if not raw_species:
            continue
        sp = raw_species
        for prefix in ("Validation organism: ", "Blind validation: ", "Blind v2: "):
            sp = sp.replace(prefix, "")
        sp = sp.replace("_", " ")
        sp_clean = sp.split(" subsp.")[0].split(" str.")[0].strip()

        # Build candidate name list (priority order)
        candidate_names = [sp_clean]
        if sp_clean in _GENUS_SYNONYMS:
            candidate_names.append(_GENUS_SYNONYMS[sp_clean])
        if sp_clean.startswith("Candidatus "):
            candidate_names.append(sp_clean[len("Candidatus "):])

        seen_bids: set = set()
        # Pass 1: MediaDive medium_strains (highest confidence — these have media links)
        for q in candidate_names:
            for bid in sp_to_bd_md.get(q, set()):
                if bid in seen_bids: continue
                seen_bids.add(bid)
                method = ("species_name_exact" if q == sp_clean
                          else "genus_reclassification_synonym")
                conn.execute(
                    "INSERT OR REPLACE INTO organism_to_bacdive "
                    "(cultureforge_genome_id, bacdive_id, match_method, match_confidence) "
                    "VALUES (?, ?, ?, ?)", (gid, bid, method, 0.95))
                n_matched += 1
        # Pass 2: bacdive_cache (broader coverage; includes subspecies)
        for q in candidate_names:
            # Exact + substring (for 'Geobacter sulfurreducens subsp. X' case)
            bids: set = set(sp_to_bd_full.get(q, set()))
            for sp_full, bset in sp_to_bd_full.items():
                if sp_full != q and sp_full.startswith(q + " "):
                    bids |= bset
            for bid in bids:
                if bid in seen_bids: continue
                seen_bids.add(bid)
                method = ("bacdive_cache_substring" if q != sp_clean else
                          "bacdive_cache_exact")
                conn.execute(
                    "INSERT OR REPLACE INTO organism_to_bacdive "
                    "(cultureforge_genome_id, bacdive_id, match_method, match_confidence) "
                    "VALUES (?, ?, ?, ?)", (gid, bid, method, 0.85))
                n_matched += 1
    conn.commit()
    return n_matched


def populate_published_media_links(conn: sqlite3.Connection) -> int:
    """For every (genome → bacdive) match, link to that strain's MediaDive media."""
    rev = build_reverse_index()
    n = 0
    for gid, bid in conn.execute(
        "SELECT cultureforge_genome_id, bacdive_id FROM organism_to_bacdive"
    ).fetchall():
        for mid, growth in rev.get(bid, []):
            if growth != 1:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO organism_to_published_media "
                "(cultureforge_genome_id, medium_id, relationship, similarity_score, bacdive_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (gid, str(mid), "direct", 1.0, bid),
            )
            n += 1
    conn.commit()
    return n


def main() -> None:
    conn = sqlite3.connect(str(DB))
    conn.executescript(SCHEMA)

    print("Populating mediadive_cache from local JSONs...")
    n_md = populate_mediadive_cache(conn)
    print(f"  ✓ mediadive_cache: {n_md} rows")

    print("Populating bacdive_cache from local JSONs...")
    n_bd = populate_bacdive_cache(conn)
    print(f"  ✓ bacdive_cache: {n_bd} rows")

    print("Matching CultureForge genomes to BacDive IDs by species name...")
    n_match = match_genomes_to_bacdive(conn)
    print(f"  ✓ organism_to_bacdive: {n_match} mappings")

    print("Linking genomes to published media via BacDive mapping...")
    n_links = populate_published_media_links(conn)
    print(f"  ✓ organism_to_published_media: {n_links} links")

    print("\nSummary by genome:")
    for row in conn.execute("""
        SELECT g.id, COALESCE(o.species, g.notes, g.accession) AS sp,
               (SELECT COUNT(*) FROM organism_to_bacdive WHERE cultureforge_genome_id = g.id) AS n_bd,
               (SELECT COUNT(*) FROM organism_to_published_media
                  WHERE cultureforge_genome_id = g.id AND relationship = 'direct') AS n_media
        FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
        WHERE g.id BETWEEN 7 AND 32
        ORDER BY g.id
    """).fetchall():
        gid, sp, n_bd_, n_media = row
        sp_disp = (sp or "?").replace("Blind v2: ", "").replace("Validation organism: ", "").replace("_", " ")[:48]
        print(f"  gid={gid:2d}  bd={n_bd_:3d}  media={n_media:4d}  {sp_disp}")

    conn.close()


if __name__ == "__main__":
    main()
