"""Integrate TEMPURA temperature data into the CultureForge database.

TEMPURA provides Tmin/Topt/Tmax for 8,639 prokaryotic strains, each linked to
NCBI tax ID and (mostly) a 16S accession. Strategy:

1. Add columns: min_temp, max_temp, temp_source to organisms table
2. Match TEMPURA records to existing organisms by NCBI tax ID first, then
   by exact species name as fallback
3. For matched organisms: fill in Tmin/Tmax always; fill optimal_temp only
   if BacDive didn't provide one
4. For unmatched TEMPURA records: insert as new "tempura-only" organisms
   so their 16S sequences and traits become available to the matcher
5. Save the new 16S accessions to a list for downstream fetching
"""

import csv
import json
import os
import sqlite3
from pathlib import Path

_ROOT = Path(__file__).parent

DB = str(_ROOT / "data" / "cultureforge.db")
TEMPURA_CSV = str(_ROOT / "data" / "tempura" / "tempura.csv")
NEW_ACCESSIONS_OUT = str(_ROOT / "data" / "tempura" / "new_16s_accessions.json")


def add_columns(conn):
    """Add TEMPURA-derived columns if not already present."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(organisms)")}
    if "min_temp" not in cols:
        conn.execute("ALTER TABLE organisms ADD COLUMN min_temp REAL")
    if "max_temp" not in cols:
        conn.execute("ALTER TABLE organisms ADD COLUMN max_temp REAL")
    if "temp_source" not in cols:
        conn.execute("ALTER TABLE organisms ADD COLUMN temp_source TEXT")
    # C-6 fix: add a 'data_source' column to distinguish BacDive-linked
    # organisms from TEMPURA-only entries, avoiding ID-range collision risk.
    if "data_source" not in cols:
        conn.execute("ALTER TABLE organisms ADD COLUMN data_source TEXT DEFAULT 'bacdive'")
    conn.commit()


def parse_temp(val):
    """Parse a temperature string, return float or None."""
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def aggregate_tempura(rows):
    """TEMPURA has duplicate species (different studies). Aggregate by tax_id:
    take median for Topt, min of Tmin, max of Tmax."""
    by_taxid = {}  # taxid -> {tmin, topt_list, tmax, species, ...}
    for r in rows:
        try:
            taxid = int(r["taxonomy_id"]) if r["taxonomy_id"] else None
        except ValueError:
            taxid = None
        if taxid is None:
            continue

        tmin = parse_temp(r["Tmin"])
        topt = parse_temp(r["Topt_ave"])
        tmax = parse_temp(r["Tmax"])

        species = r["genus_and_species"].strip().strip('"').strip("'")
        # Strip surrounding quotes from candidate names like '"Geogemma barossii"'

        if taxid not in by_taxid:
            by_taxid[taxid] = {
                "species": species,
                "domain": r["superkingdom"],
                "phylum": r["phylum"],
                "family": r["family"],
                "genus": r["genus"],
                "tmins": [],
                "topts": [],
                "tmaxs": [],
                "accessions_16s": set(),
            }

        entry = by_taxid[taxid]
        if tmin is not None:
            entry["tmins"].append(tmin)
        if topt is not None:
            entry["topts"].append(topt)
        if tmax is not None:
            entry["tmaxs"].append(tmax)
        if r["16S_accssion"] and r["16S_accssion"].strip():
            entry["accessions_16s"].add(r["16S_accssion"].strip())

    # Reduce lists to single values
    for taxid, entry in by_taxid.items():
        entry["tmin"] = min(entry["tmins"]) if entry["tmins"] else None
        entry["tmax"] = max(entry["tmaxs"]) if entry["tmaxs"] else None
        # Median for Topt
        if entry["topts"]:
            sorted_t = sorted(entry["topts"])
            entry["topt"] = sorted_t[len(sorted_t) // 2]
        else:
            entry["topt"] = None

    return by_taxid


def merge_into_existing(conn, tempura_by_taxid):
    """For organisms already in the DB (by NCBI tax ID or species name),
    fill in temperature data. Returns set of taxids that were merged."""
    matched_taxids = set()

    # Build lookup tables
    by_taxid = {row[0]: row[1:] for row in conn.execute(
        "SELECT ncbi_taxid, id, optimal_temp, species FROM organisms WHERE ncbi_taxid IS NOT NULL"
    )}
    by_species = {row[0]: row[1:] for row in conn.execute(
        "SELECT species, id, optimal_temp FROM organisms WHERE species IS NOT NULL"
    )}

    n_taxid_match = 0
    n_species_match = 0
    n_filled_topt = 0
    n_added_minmax = 0

    for taxid, entry in tempura_by_taxid.items():
        org_id = None
        existing_topt = None

        if taxid in by_taxid:
            org_id, existing_topt, _ = by_taxid[taxid]
            n_taxid_match += 1
        elif entry["species"] in by_species:
            org_id, existing_topt = by_species[entry["species"]]
            n_species_match += 1

        if org_id is None:
            continue

        matched_taxids.add(taxid)

        # Fill optimal_temp if BacDive didn't provide one
        new_topt = existing_topt
        if existing_topt is None and entry["topt"] is not None:
            new_topt = entry["topt"]
            n_filled_topt += 1

        # Always fill min/max (BacDive doesn't really track these well)
        conn.execute("""
            UPDATE organisms
               SET optimal_temp = ?,
                   min_temp = ?,
                   max_temp = ?,
                   temp_source = COALESCE(temp_source || '+TEMPURA', 'TEMPURA')
             WHERE id = ?
        """, (new_topt, entry["tmin"], entry["tmax"], org_id))

        if entry["tmin"] is not None or entry["tmax"] is not None:
            n_added_minmax += 1

    conn.commit()
    print(f"  Matched by NCBI tax ID: {n_taxid_match}")
    print(f"  Matched by species name: {n_species_match}")
    print(f"  Filled optimal_temp gaps: {n_filled_topt}")
    print(f"  Added min/max temp: {n_added_minmax}")

    return matched_taxids


def insert_new_organisms(conn, tempura_by_taxid, matched_taxids):
    """Insert TEMPURA-only organisms (not in BacDive) as new entries.
    These get pseudo-IDs in a separate range (negative or > 1M to avoid collision)."""
    # Find max existing ID
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM organisms").fetchone()[0]
    next_id = max(max_id + 1, 10_000_000)  # use 10M+ range to clearly mark TEMPURA-only

    n_inserted = 0
    new_accessions = {}  # accession -> pseudo organism id

    for taxid, entry in tempura_by_taxid.items():
        if taxid in matched_taxids:
            # Even matched entries may have new 16S accessions to fetch
            existing_acc_count = conn.execute(
                "SELECT id FROM organisms WHERE ncbi_taxid=?", (taxid,)
            ).fetchone()
            if existing_acc_count:
                org_id = existing_acc_count[0]
                for acc in entry["accessions_16s"]:
                    new_accessions[acc] = org_id
            continue

        org_id = next_id
        next_id += 1

        conn.execute("""
            INSERT INTO organisms
              (id, species, ccno, domain, ncbi_taxid, genus, family, phylum,
               optimal_temp, optimal_ph, oxygen_requirement, description,
               min_temp, max_temp, temp_source, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_id, entry["species"], None,
            "A" if entry["domain"] == "Archaea" else "B",
            taxid, entry["genus"], entry["family"], entry["phylum"],
            entry["topt"], None, None,
            f"TEMPURA-only entry for {entry['species']}",
            entry["tmin"], entry["tmax"], "TEMPURA", "tempura_only",
        ))
        n_inserted += 1

        for acc in entry["accessions_16s"]:
            new_accessions[acc] = org_id

    conn.commit()
    print(f"  Inserted TEMPURA-only organisms: {n_inserted}")

    # Save new accessions for downstream fetching
    with open(NEW_ACCESSIONS_OUT, "w") as f:
        json.dump(new_accessions, f, indent=2)
    print(f"  New 16S accessions to fetch: {len(new_accessions)} -> {NEW_ACCESSIONS_OUT}")


def summary(conn):
    n_total = conn.execute("SELECT COUNT(*) FROM organisms").fetchone()[0]
    n_topt = conn.execute("SELECT COUNT(*) FROM organisms WHERE optimal_temp IS NOT NULL").fetchone()[0]
    n_tempura = conn.execute("SELECT COUNT(*) FROM organisms WHERE temp_source LIKE '%TEMPURA%'").fetchone()[0]
    n_tmin = conn.execute("SELECT COUNT(*) FROM organisms WHERE min_temp IS NOT NULL").fetchone()[0]
    n_tempura_only = conn.execute("SELECT COUNT(*) FROM organisms WHERE id >= 10000000").fetchone()[0]
    print(f"\n  organisms total: {n_total:,}")
    print(f"  with optimal_temp: {n_topt:,}")
    print(f"  with min/max temp: {n_tmin:,}")
    print(f"  with TEMPURA contribution: {n_tempura:,}")
    print(f"  TEMPURA-only entries: {n_tempura_only:,}")


def main():
    if not os.path.exists(TEMPURA_CSV):
        raise SystemExit(f"TEMPURA CSV not found at {TEMPURA_CSV}")

    print("Loading TEMPURA CSV...")
    with open(TEMPURA_CSV) as f:
        rows = list(csv.DictReader(f))
    print(f"  {len(rows)} raw rows")

    print("Aggregating by NCBI tax ID...")
    tempura_by_taxid = aggregate_tempura(rows)
    print(f"  {len(tempura_by_taxid)} unique tax IDs")

    conn = sqlite3.connect(DB)
    print("Adding columns to organisms table...")
    add_columns(conn)

    print("Merging into existing organisms...")
    matched_taxids = merge_into_existing(conn, tempura_by_taxid)

    print("Inserting TEMPURA-only organisms...")
    insert_new_organisms(conn, tempura_by_taxid, matched_taxids)

    print("\nSummary:")
    summary(conn)
    conn.close()
    print(f"\nDatabase updated: {DB}")


if __name__ == "__main__":
    main()
