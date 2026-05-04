"""Generic genome registration for CultureForge (Phase 4.1).

Replaces the hardcoded behavior in load_*.py scripts with functions
that register any genome based on user-provided metadata. Test-set genomes
(gid 7-32) and sentinel genomes (gid 900-903) are protected by a gid-range
safeguard in deregister_genome().

The Phase 4.1 design contract:

  - register_genome() refuses to insert when an accession is already registered
    (raises ValueError). This prevents the silent overwrite that caused the
    pre-Phase-4.1 gid=904 incident, where load_gapseq.py's "idempotent reload"
    silently dropped the test-set E. coli row (gid=32) and reinserted as gid=904.

  - deregister_genome() refuses to delete gids < 1000. The test set and
    sentinels live below gid 1000; this safeguard makes accidental destruction
    of validated data impossible via this entry point.

  - User-loaded genomes always go to gid >= 1000 (gid_min default).

Usage:

    from register_genome import register_genome, deregister_genome

    gid = register_genome(
        db_path="data/cultureforge.db",
        accession="GCF_000196135.1",
        file_path="data/user_genomes/wolinella/genome.fna",
        notes="User-loaded genome: Wolinella succinogenes",
        biomass_template="Gram_neg",
    )

    # Later, if the load fails partway:
    deregister_genome("data/cultureforge.db", gid)
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

# Tables that reference genomes.id via a genome_id column.
# Determined empirically from the Phase 4.1 schema scan (see
# data/release/phase4_1_cleanup_notes.md). Tables that do not exist in
# older databases are tolerated (OperationalError on DELETE is swallowed).
_GENOME_ID_TABLES = (
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

USER_GID_MIN = 1000  # User-loaded genomes start here; below = test set / sentinels


def _genome_length_bp(file_path: str) -> int:
    """Compute total bp by streaming the FASTA. Returns 0 if file unreadable."""
    n = 0
    p = Path(file_path)
    if not p.exists():
        return 0
    with p.open() as f:
        for line in f:
            if not line.startswith(">"):
                n += len(line.strip())
    return n


def register_genome(
    db_path: str,
    accession: str,
    file_path: str,
    notes: str = "",
    biomass_template: str = "Gram_neg",
    source: str = "user_input",
    organism_id: Optional[int] = None,
    n_unique_genes: Optional[int] = None,
    gid_min: int = USER_GID_MIN,
) -> int:
    """Register a new genome and return the assigned gid.

    Args:
        db_path: SQLite database path.
        accession: Unique accession identifier (NCBI accession or arbitrary
            string for novel genomes). Refused if already present.
        file_path: Path to the genome FASTA, used for length computation
            and as the canonical file pointer for downstream loaders.
        notes: Free-text notes column on the genomes row.
        biomass_template: Gram_neg / Gram_pos / Archaea — passed to gapseq
            and other downstream tools.
        source: Free-text origin label (e.g., "NCBI_RefSeq", "user_input",
            "MAG_isolate").
        organism_id: Optional FK into the organisms table (typically NULL
            for user-loaded genomes that don't have a BacDive/MediaDive entry).
        n_unique_genes: Optional gene count (populated post-prodigal).
        gid_min: Minimum gid to assign. Default 1000 places user genomes
            above the test set (7-32) and sentinels (900-903).

    Returns:
        The assigned gid as an int.

    Raises:
        ValueError: If `accession` is already registered. The user must
            explicitly deregister the existing entry first (a loud failure
            mode, by design — see Phase 4.1 cleanup_notes for context).
        FileNotFoundError: If `file_path` does not exist.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Genome FASTA not found: {file_path}")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Check for accession duplicate
        cursor.execute(
            "SELECT id, notes FROM genomes WHERE accession = ?", (accession,)
        )
        existing = cursor.fetchone()
        if existing:
            raise ValueError(
                f"Accession '{accession}' is already registered as gid={existing[0]} "
                f"(notes: {existing[1] or '(none)'}). Refusing to create duplicate. "
                f"To replace, first call deregister_genome(db_path, {existing[0]}) "
                f"— but note that this is refused for gids < {USER_GID_MIN} "
                f"(test set and sentinels)."
            )

        # Find next available gid >= gid_min
        cursor.execute(
            "SELECT COALESCE(MAX(id), ?) + 1 FROM genomes WHERE id >= ?",
            (gid_min - 1, gid_min),
        )
        new_gid = cursor.fetchone()[0]

        length_bp = _genome_length_bp(file_path)

        cursor.execute(
            """
            INSERT INTO genomes (
                id, organism_id, accession, source, file_path,
                length_bp, biomass_template, n_unique_genes,
                gapseq_version, gapseq_run_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_gid,
                organism_id,
                accession,
                source,
                file_path,
                length_bp,
                biomass_template,
                n_unique_genes,
                None,  # gapseq_version filled in by load_gapseq later
                None,  # gapseq_run_date filled in later
                notes,
            ),
        )
        conn.commit()
        return new_gid
    finally:
        conn.close()


def deregister_genome(db_path: str, gid: int) -> dict:
    """Remove a genome and all its associated rows.

    Args:
        db_path: SQLite database path.
        gid: The genome id to remove. MUST be >= USER_GID_MIN (1000) —
            test-set and sentinel gids are protected.

    Returns:
        Dict mapping table names to the number of rows deleted, plus
        a 'genomes' key for the parent row deletion (0 or 1).

    Raises:
        ValueError: If gid < USER_GID_MIN. This safeguard prevents the
            existing 26 test-set genomes (gids 7-32) and 4 sentinels
            (gids 900-903) from being destroyed via this entry point.
    """
    if gid < USER_GID_MIN:
        raise ValueError(
            f"Refusing to deregister gid={gid}. User-loaded genomes start at "
            f"gid={USER_GID_MIN}; gids below that are the test set (7-32) and "
            f"sentinels (900-903), which are protected. If you need to modify "
            f"those, do it via direct SQL after explicitly understanding the "
            f"impact on V12 validation."
        )

    deleted: dict = {}
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for table in _GENOME_ID_TABLES:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE genome_id = ?", (gid,))
                deleted[table] = cursor.rowcount
            except sqlite3.OperationalError:
                # Table may not exist in older schema variants
                pass
        cursor.execute("DELETE FROM genomes WHERE id = ?", (gid,))
        deleted["genomes"] = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def update_genome_metadata(
    db_path: str,
    gid: int,
    n_unique_genes: Optional[int] = None,
    gapseq_version: Optional[str] = None,
    gapseq_run_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
    """Update mutable metadata fields after pipeline stages complete.

    Used by the wrapper to fill in n_unique_genes (after prodigal),
    gapseq_version + gapseq_run_date (after gapseq), and optionally
    extend notes with run summaries.
    """
    if gid < USER_GID_MIN:
        raise ValueError(
            f"Refusing to update gid={gid} metadata via update_genome_metadata; "
            f"user-loaded genomes start at gid={USER_GID_MIN}."
        )

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        if n_unique_genes is not None:
            cursor.execute(
                "UPDATE genomes SET n_unique_genes = ? WHERE id = ?",
                (n_unique_genes, gid),
            )
        if gapseq_version is not None:
            cursor.execute(
                "UPDATE genomes SET gapseq_version = ? WHERE id = ?",
                (gapseq_version, gid),
            )
        if gapseq_run_date is not None:
            cursor.execute(
                "UPDATE genomes SET gapseq_run_date = ? WHERE id = ?",
                (gapseq_run_date, gid),
            )
        elif gapseq_version is not None:
            # If a version was set but no date was specified, default to today
            cursor.execute(
                "UPDATE genomes SET gapseq_run_date = ? WHERE id = ?",
                (str(date.today()), gid),
            )
        if notes is not None:
            cursor.execute(
                "UPDATE genomes SET notes = ? WHERE id = ?",
                (notes, gid),
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    # Smoke test (run as module): register + deregister a fake entry.
    import argparse
    import sys
    import tempfile

    parser = argparse.ArgumentParser(description="register_genome smoke test")
    parser.add_argument("--db", default="data/cultureforge.db")
    args = parser.parse_args()

    # Create a fake FASTA so the length-bp computation has something to read
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fna", delete=False) as fh:
        fh.write(">test_seq\nACGTACGTACGT\n")
        fake_path = fh.name

    try:
        gid = register_genome(
            db_path=args.db,
            accession="TEST_ACC_001",
            file_path=fake_path,
            notes="register_genome smoke test — DELETE ME",
        )
        print(f"OK: registered gid={gid}")

        # Try to register the same accession again — should raise
        try:
            register_genome(
                db_path=args.db,
                accession="TEST_ACC_001",
                file_path=fake_path,
                notes="duplicate — should refuse",
            )
            print("FAIL: duplicate registration did not raise")
            sys.exit(1)
        except ValueError as e:
            print(f"OK: duplicate refused — {str(e).splitlines()[0]}")

        # Deregister
        result = deregister_genome(args.db, gid)
        print(f"OK: deregistered gid={gid}, deleted rows: {result}")

        # Try to deregister a test-set gid — should refuse
        try:
            deregister_genome(args.db, 8)
            print("FAIL: deregister of test-set gid did not raise")
            sys.exit(1)
        except ValueError as e:
            print(f"OK: test-set gid protected — {str(e).splitlines()[0]}")
    finally:
        Path(fake_path).unlink(missing_ok=True)
