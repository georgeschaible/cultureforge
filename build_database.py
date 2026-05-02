"""Build data/cultureforge.db from downloaded MediaDive + BacDive files.

Inputs:
  data/mediadive/media/<mid>.json            — medium + solutions + recipe
  data/mediadive/medium_strains/<mid>.json   — list of strains per medium
  data/bacdive/strains/<bid>.json            — BacDive strain detail (partial OK)

Schema mirrors CLAUDE.md §2.3 with small practical additions.
"""

import glob
import json
import os
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DB = str(PROJECT_ROOT / "data" / "cultureforge.db")


def open_db(rebuild=False):
    """Open (or create) the database. If tables exist and --rebuild is not
    set, abort to prevent accidentally destroying downstream data."""
    conn = sqlite3.connect(DB)

    # Safety check: if core tables already have data, require --rebuild
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='media'"
    ).fetchone()
    if existing and not rebuild:
        n = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
        if n > 0:
            print(f"ERROR: database already contains {n} media rows. "
                  f"Use --rebuild to drop and recreate all tables.",
                  file=sys.stderr)
            conn.close()
            sys.exit(1)

    conn.executescript("""
        DROP TABLE IF EXISTS media_compounds;
        DROP TABLE IF EXISTS organism_media;
        DROP TABLE IF EXISTS media;
        DROP TABLE IF EXISTS compounds;
        DROP TABLE IF EXISTS organisms;

        CREATE TABLE media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT UNIQUE,
            name TEXT NOT NULL,
            source TEXT,
            complex_medium TEXT,
            min_ph REAL,
            max_ph REAL,
            link TEXT,
            description TEXT
        );
        CREATE TABLE compounds (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE media_compounds (
            media_id INTEGER,
            compound_id INTEGER,
            solution_name TEXT,
            amount REAL,
            unit TEXT,
            g_per_L REAL,
            optional INTEGER,
            FOREIGN KEY (media_id) REFERENCES media(id),
            FOREIGN KEY (compound_id) REFERENCES compounds(id)
        );
        CREATE TABLE organisms (
            id INTEGER PRIMARY KEY,            -- BacDive ID when known
            species TEXT,
            ccno TEXT,
            domain TEXT,
            ncbi_taxid INTEGER,
            genus TEXT,
            family TEXT,
            phylum TEXT,
            optimal_temp REAL,
            optimal_ph REAL,
            oxygen_requirement TEXT,
            description TEXT
        );
        CREATE TABLE organism_media (
            organism_id INTEGER,
            media_id INTEGER,
            growth INTEGER,
            FOREIGN KEY (organism_id) REFERENCES organisms(id),
            FOREIGN KEY (media_id) REFERENCES media(id)
        );
        CREATE INDEX idx_mc_media ON media_compounds(media_id);
        CREATE INDEX idx_mc_compound ON media_compounds(compound_id);
        CREATE INDEX idx_om_org ON organism_media(organism_id);
        CREATE INDEX idx_om_med ON organism_media(media_id);
        CREATE INDEX idx_om_growth ON organism_media(growth);
        CREATE INDEX idx_org_taxid ON organisms(ncbi_taxid);
        CREATE INDEX idx_org_species ON organisms(species);
    """)
    return conn


def load_media(conn):
    source_to_db = {}  # source_id (str) -> db id (int)
    compound_cache = {}

    def compound_id(name):
        if not name:
            return None
        if name in compound_cache:
            return compound_cache[name]
        cur = conn.execute("INSERT OR IGNORE INTO compounds(name) VALUES (?)", (name,))
        cur = conn.execute("SELECT id FROM compounds WHERE name=?", (name,))
        cid = cur.fetchone()[0]
        compound_cache[name] = cid
        return cid

    n_media = n_rows = 0
    for path in glob.glob("data/mediadive/media/*.json"):
        with open(path) as f:
            detail = json.load(f)
        m = detail.get("medium") or {}
        mid = m.get("id")
        if mid is None:
            continue
        conn.execute("""
            INSERT OR REPLACE INTO media
              (source_id, name, source, complex_medium, min_ph, max_ph, link, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(mid), m.get("name", ""), m.get("source"),
            m.get("complex_medium"), m.get("min_pH"), m.get("max_pH"),
            m.get("link"), m.get("description"),
        ))
        db_mid = conn.execute(
            "SELECT id FROM media WHERE source_id=?", (str(mid),)
        ).fetchone()[0]
        source_to_db[str(mid)] = db_mid
        n_media += 1
        for sol in detail.get("solutions") or []:
            sol_name = sol.get("name")
            for r in sol.get("recipe") or []:
                cid = compound_id(r.get("compound"))
                if cid is None:
                    continue
                conn.execute("""
                    INSERT INTO media_compounds
                      (media_id, compound_id, solution_name, amount, unit, g_per_L, optional)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    db_mid, cid, sol_name, r.get("amount"), r.get("unit"),
                    r.get("g_l"), r.get("optional") or 0,
                ))
                n_rows += 1
    conn.commit()
    print(f"  media: {n_media} rows, media_compounds: {n_rows} rows, "
          f"compounds: {len(compound_cache)}")
    return source_to_db


def bacdive_trait(rec):
    """Extract a few common fields defensively; BacDive schemas vary."""
    out = {
        "ncbi_taxid": None, "genus": None, "family": None, "phylum": None,
        "optimal_temp": None, "optimal_ph": None, "oxygen_requirement": None,
        "description": None,
    }
    if not isinstance(rec, dict):
        return out
    gen = rec.get("General") or {}
    out["description"] = gen.get("description")
    taxids = gen.get("NCBI tax id") or []
    if isinstance(taxids, dict):
        taxids = [taxids]
    for t in taxids:
        if t.get("Matching level") in ("species", "strain"):
            out["ncbi_taxid"] = t.get("NCBI tax id")
            break
    name = rec.get("Name and taxonomic classification") or {}
    if isinstance(name, dict):
        out["genus"] = name.get("genus")
        out["family"] = name.get("family")
        out["phylum"] = name.get("phylum")
    cond = rec.get("Culture and growth conditions") or {}
    temps = cond.get("culture temp") or []
    if isinstance(temps, dict):
        temps = [temps]
    for t in temps:
        if t.get("type") == "optimum" and t.get("temperature"):
            try:
                out["optimal_temp"] = float(str(t["temperature"]).split("-")[0])
                break
            except (TypeError, ValueError):
                pass
    phs = cond.get("culture pH") or []
    if isinstance(phs, dict):
        phs = [phs]
    for p in phs:
        if p.get("ability") == "optimum" and p.get("pH"):
            try:
                out["optimal_ph"] = float(str(p["pH"]).split("-")[0])
                break
            except (TypeError, ValueError):
                pass
    morph = rec.get("Morphology") or {}
    cell = morph.get("cell morphology")
    if isinstance(cell, dict):
        out["oxygen_requirement"] = cell.get("oxygen tolerance")
    return out


def load_organisms_and_links(conn, source_to_db):
    # First pass: read medium_strains to collect species/ccno/domain per bacdive_id
    org_meta = {}
    links = []
    for path in glob.glob("data/mediadive/medium_strains/*.json"):
        source_mid = os.path.splitext(os.path.basename(path))[0]
        db_mid = source_to_db.get(source_mid)
        if db_mid is None:
            continue
        with open(path) as f:
            rows = json.load(f)
        for r in rows:
            bid = r.get("bacdive_id")
            if not bid:
                continue
            bid = int(bid)
            if bid not in org_meta:
                org_meta[bid] = {
                    "species": r.get("species"),
                    "ccno": r.get("ccno"),
                    "domain": r.get("domain"),
                }
            links.append((bid, db_mid, r.get("growth")))

    # Second pass: merge BacDive traits when available
    for bid, meta in org_meta.items():
        bd_path = f"data/bacdive/strains/{bid}.json"
        if os.path.exists(bd_path):
            with open(bd_path) as fh:
                traits = bacdive_trait(json.load(fh))
        else:
            traits = bacdive_trait(None)
        conn.execute("""
            INSERT OR REPLACE INTO organisms
              (id, species, ccno, domain, ncbi_taxid, genus, family, phylum,
               optimal_temp, optimal_ph, oxygen_requirement, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bid, meta["species"], meta["ccno"], meta["domain"],
            traits["ncbi_taxid"], traits["genus"], traits["family"], traits["phylum"],
            traits["optimal_temp"], traits["optimal_ph"],
            traits["oxygen_requirement"], traits["description"],
        ))
    conn.executemany(
        "INSERT INTO organism_media (organism_id, media_id, growth) VALUES (?, ?, ?)",
        links,
    )
    conn.commit()
    print(f"  organisms: {len(org_meta)}, organism_media: {len(links)}")


def summary(conn):
    for tbl in ("media", "compounds", "media_compounds",
                "organisms", "organism_media"):
        n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"    {tbl}: {n}")


def main():
    rebuild = "--rebuild" in sys.argv
    conn = open_db(rebuild=rebuild)
    print("Loading media + recipes…")
    source_to_db = load_media(conn)
    print("Loading organisms + links…")
    load_organisms_and_links(conn, source_to_db)
    print("\nFinal counts:")
    summary(conn)
    conn.close()
    print(f"\nDatabase: {DB}")


if __name__ == "__main__":
    main()
