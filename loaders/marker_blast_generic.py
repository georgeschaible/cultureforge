"""Generic marker-BLAST loader (Phase 4.1).

Wraps run_marker_blast.py's `blast_all_markers(proteome_path, gid, conn)`
function. The existing function already runs all configured marker BLAST
DBs against a proteome and inserts hits into genome_diagnostic_markers
with the provided gid.

Phase 4.1 prohibition: do NOT modify run_marker_blast.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from run_marker_blast import blast_all_markers, SCHEMA_SQL


def load_marker_blast_results(
    gid: int,
    proteome_path: str,
    db_path: str = "data/cultureforge.db",
) -> dict:
    """Run marker BLAST against a proteome and load hits for a genome.

    Args:
        gid: Genome id (must already be registered).
        proteome_path: Path to predicted proteome FASTA (.faa).
        db_path: SQLite database path.

    Returns:
        Dict mapping marker_name to a list of hit dicts (the existing
        `blast_all_markers` return value).
    """
    proteome_p = Path(proteome_path).resolve()
    if not proteome_p.exists():
        raise FileNotFoundError(
            f"Proteome FASTA missing: {proteome_p}. "
            f"Did prodigal succeed?"
        )

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        results = blast_all_markers(str(proteome_p), gid, conn)
        conn.commit()
        return results
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    import sys
    from register_genome import register_genome, deregister_genome

    parser = argparse.ArgumentParser(description="marker_blast_generic smoke test")
    parser.add_argument("--db", default="data/cultureforge.db")
    parser.add_argument(
        "--proteome",
        default="data/gapseq/ecoli/ecoli_proteins.faa",
    )
    args = parser.parse_args()

    if not Path(args.proteome).exists():
        print(f"FAIL: smoke test proteome missing: {args.proteome}")
        sys.exit(1)

    fasta = "data/genomes/ecoli_k12_mg1655.fasta"
    gid = register_genome(
        db_path=args.db,
        accession="TEST_MARKER_BLAST_LOAD",
        file_path=fasta,
        notes="marker_blast_generic smoke test — DELETE ME",
    )
    print(f"OK: registered gid={gid}")
    try:
        result = load_marker_blast_results(gid, args.proteome, db_path=args.db)
        n_markers = len(result)
        n_hits = sum(len(v) for v in result.values())
        print(f"OK: {n_markers} markers detected, {n_hits} total positive hits")
    finally:
        deregister_genome(args.db, gid)
        print(f"OK: deregistered gid={gid}")
