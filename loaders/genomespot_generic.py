"""Generic GenomeSPOT output loader (Phase 4.1).

Wraps load_genomespot.py's gid-parameterized `load(conn, gid, tsv_path)`
function with a clean interface.

Phase 4.1 prohibition: do NOT modify load_genomespot.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from load_genomespot import load as _load_genomespot, SCHEMA_SQL


def load_genomespot_outputs(
    gid: int,
    predictions_tsv: str,
    db_path: str = "data/cultureforge.db",
    source_name: str = "GenomeSPOT",
) -> int:
    """Load GenomeSPOT predictions for a genome.

    Args:
        gid: Genome id (must already be registered).
        predictions_tsv: Path to GenomeSPOT's predictions.tsv output
            (typically named `<output_prefix>.predictions.tsv`).
        db_path: SQLite database path.
        source_name: Source label recorded with each row.

    Returns:
        Number of prediction rows loaded.
    """
    tsv_path = Path(predictions_tsv).resolve()
    if not tsv_path.exists():
        raise FileNotFoundError(
            f"GenomeSPOT predictions TSV missing: {tsv_path}. "
            f"Was GenomeSPOT run successfully?"
        )

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        n = _load_genomespot(conn, gid, str(tsv_path), source_name=source_name)
        conn.commit()
        return n
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    import sys
    from register_genome import register_genome, deregister_genome

    parser = argparse.ArgumentParser(description="genomespot_generic smoke test")
    parser.add_argument("--db", default="data/cultureforge.db")
    parser.add_argument(
        "--predictions-tsv",
        default="data/genomespot/ecoli/ecoli.predictions.tsv",
    )
    args = parser.parse_args()

    if not Path(args.predictions_tsv).exists():
        print(f"FAIL: smoke test predictions TSV missing: {args.predictions_tsv}")
        sys.exit(1)

    fasta = "data/genomes/ecoli_k12_mg1655.fasta"
    gid = register_genome(
        db_path=args.db,
        accession="TEST_GENOMESPOT_LOAD",
        file_path=fasta,
        notes="genomespot_generic smoke test — DELETE ME",
    )
    print(f"OK: registered gid={gid}")
    try:
        n = load_genomespot_outputs(gid, args.predictions_tsv, db_path=args.db)
        print(f"OK: loaded {n} GenomeSPOT predictions")
    finally:
        deregister_genome(args.db, gid)
        print(f"OK: deregistered gid={gid}")
