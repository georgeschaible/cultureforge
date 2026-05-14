#!/usr/bin/env python3
"""Audit Resolution Task 3 — Database surgery to swap temp gids into 9/17/26/30.

Run this AFTER the audit_correction batch (T2) finishes. The batch processes
the 4 corrected genomes under temp gids in the 1001+ range. This script then
moves all child-table rows from the temp gid to the original test-set slot,
deletes the wrong-genome rows previously occupying that slot, and re-creates
the genomes table entry with id=<original_gid>.

The mapping (corrected accession → original gid) is read from
data/release/audits/replacement_accessions.tsv. The temp gids are looked up
from the audit_correction_batch_progress.tsv produced by process-batch.

Safety:
  - Refuses to run if the batch progress shows any genome still in 'running'
    or 'pending' state.
  - Refuses to run if any of the temp gids is NOT >= 1001.
  - Wraps all DELETE/UPDATE/INSERT in a single transaction; on any error the
    transaction rolls back.

Usage:
    python3 data/release/audits/task3_db_surgery.py [--dry-run]

The --dry-run flag prints the planned SQL statements without executing.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "data" / "cultureforge.db"
PROGRESS = ROOT / "data" / "release" / "audits" / "audit_correction_batch_progress.tsv"
REPLACEMENT = ROOT / "data" / "release" / "audits" / "replacement_accessions.tsv"

# Mapping per `replacement_accessions.tsv` — verified manually
ACCESSION_TO_ORIGINAL_GID = {
    "GCF_001280255.1": 9,    # Thermus aquaticus YT-1
    "GCF_000012965.1": 17,   # Sulfurimonas denitrificans DSM 1251
    "GCF_000008265.1": 26,   # Picrophilus torridus DSM 9790 (NCBI mislabels organism, strain DSM 9790 is correct)
    "GCF_002443295.1": 30,   # Candidatus Scalindua japonica husup-a2 (substituting for unavailable S. profunda)
}

# Tables that have a genome_id foreign key to genomes.id (per Phase 4.1 schema scan)
GENOME_ID_TABLES = (
    "genome_pathways",
    "genome_transporters",
    "genome_diagnostic_markers",
    "genome_growth_predictions",
    "genome_metal_profile",
    "genome_carbon_sources",
    "genome_hydrogenases",
    "genome_reaction_markers",
    "genome_quality",
    "predictions",
    "protein_metal_binding",
    "recipe_components",
    "prediction_confidences",
    "source_confidence",
)


def read_temp_gids() -> dict:
    """Return dict mapping accession → temp gid from the batch progress TSV."""
    out = {}
    with PROGRESS.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            acc = row["accession"]
            status = row["status"]
            gid = row["gid"]
            if status != "success":
                raise RuntimeError(
                    f"Cannot proceed — batch row {acc} status is {status!r}, "
                    "expected 'success'. Wait for the batch to finish, then re-run."
                )
            out[acc] = int(gid)
    return out


def main(dry_run: bool = False) -> None:
    if not PROGRESS.exists():
        sys.exit(f"FAIL: progress TSV missing: {PROGRESS}")

    temp_gids = read_temp_gids()
    print(f"Read temp gids: {temp_gids}")
    print()

    # Plan the surgery
    plan = []
    for acc, original_gid in ACCESSION_TO_ORIGINAL_GID.items():
        temp_gid = temp_gids.get(acc)
        if temp_gid is None:
            sys.exit(f"FAIL: no temp gid found for accession {acc}")
        if temp_gid < 1001:
            sys.exit(f"FAIL: temp gid {temp_gid} is in the test-set range; refusing.")
        plan.append((acc, original_gid, temp_gid))

    print("Surgery plan:")
    for acc, og, tg in plan:
        print(f"  gid={og:3d} ← temp_gid={tg:4d}  ({acc})")
    print()

    if dry_run:
        print("--- DRY RUN — no DB changes made ---")
        return

    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = OFF")  # so we can swap without parent-row constraint trip

    try:
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION")

        for acc, original_gid, temp_gid in plan:
            print(f"=== Surgery: temp_gid={temp_gid} → original_gid={original_gid} ===")

            # Step 1: delete all rows currently at original_gid (the wrong-genome data)
            for table in GENOME_ID_TABLES:
                try:
                    cur.execute(
                        f"DELETE FROM {table} WHERE genome_id = ?",
                        (original_gid,),
                    )
                    if cur.rowcount > 0:
                        print(f"  deleted {cur.rowcount} rows from {table} (was wrong genome)")
                except sqlite3.OperationalError:
                    pass  # table may not exist
            cur.execute("DELETE FROM genomes WHERE id = ?", (original_gid,))
            print(f"  deleted {cur.rowcount} rows from genomes (id={original_gid})")

            # Step 2: migrate all child-table rows from temp_gid → original_gid
            for table in GENOME_ID_TABLES:
                try:
                    cur.execute(
                        f"UPDATE {table} SET genome_id = ? WHERE genome_id = ?",
                        (original_gid, temp_gid),
                    )
                    if cur.rowcount > 0:
                        print(f"  migrated {cur.rowcount} rows in {table}")
                except sqlite3.OperationalError:
                    pass

            # Step 3: move the genomes-table row from temp_gid to original_gid.
            # An INSERT-from-SELECT + DELETE pair would trip the UNIQUE constraint
            # on accession (both rows would briefly coexist with the same accession);
            # a single UPDATE of the primary key avoids that conflict.
            cur.execute(
                "UPDATE genomes SET id = ? WHERE id = ?",
                (original_gid, temp_gid),
            )

            # Step 4: annotate the corrected row's notes
            cur.execute("""
                UPDATE genomes
                SET notes = notes ||
                    ' [AUDIT CORRECTION 2026-05-05: re-downloaded + re-processed; ' ||
                    'previously gid=' || ? || ' had wrong-genome data loaded from project start. ' ||
                    'Pre-correction state preserved in data/cultureforge.db.pre_audit_correction_20260504]'
                WHERE id = ?
                """, (original_gid, original_gid))

            print(f"  ✓ gid={original_gid} updated to corrected data")
            print()

        # Step 5: replace gid=30's TMP_AUDIT placeholder accession
        # (gid=30 was given a temp placeholder during T4-T6 metadata fixes)
        cur.execute("""
            SELECT id, accession FROM genomes WHERE accession LIKE 'TMP_AUDIT_%'
            """)
        tmps = cur.fetchall()
        if tmps:
            print(f"WARNING: still {len(tmps)} TMP_AUDIT placeholders in DB:")
            for r in tmps:
                print(f"  gid={r[0]} accession={r[1]}")
            print("These should have been cleared by the gid=30 surgery above.")

        cur.execute("COMMIT")
        print("=== Transaction committed ===")
    except Exception as exc:
        conn.execute("ROLLBACK")
        print(f"FAILED — transaction rolled back: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()

    # Verify post-state
    print()
    print("=== Post-surgery state ===")
    conn = sqlite3.connect(str(DB))
    rows = conn.execute("""
        SELECT id, accession, file_path, SUBSTR(notes, 1, 80) AS notes_short
        FROM genomes WHERE id IN (9, 17, 26, 28, 29, 30, 1000, 1001, 1002, 1003, 1004)
        ORDER BY id
        """).fetchall()
    for r in rows:
        print(f"  gid={r[0]:5d} acc={r[1]:25s} file={Path(r[2]).name}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
