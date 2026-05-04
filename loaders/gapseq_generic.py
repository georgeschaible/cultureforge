"""Generic gapseq output loader (Phase 4.1).

Wraps load_gapseq.py's gid-parameterized loader functions with conventions
about where gapseq's output files live for a given genome accession.

The existing load_gapseq.py expects a per-genome output directory containing
files named like:
    <accession>-all-Pathways.tbl
    <accession>-Transporter.tbl
    <accession>-all-Reactions.tbl
    <accession>-draft.xml      (used for n_unique_genes count via XML parsing
                                 in the original main(); not loaded into
                                 our generic path — the wrapper's prodigal
                                 step provides that count instead)

This module locates those files in a given directory and calls the existing
loader functions with explicit gid.

Phase 4.1 prohibition: do NOT modify load_gapseq.py. This module is a
thin façade.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Tuple

# Re-use existing loader functions
from load_gapseq import (
    SCHEMA_SQL,
    load_pathways,
    load_transporters,
    load_reaction_markers,
    populate_essential_compounds,
    get_gapseq_version_from_file,
)
from register_genome import update_genome_metadata


def _resolve_gapseq_files(
    gapseq_dir: Path, accession: Optional[str] = None
) -> Tuple[Path, Path, Path]:
    """Locate the three gapseq TSV outputs in a directory.

    Args:
        gapseq_dir: Directory containing gapseq output files.
        accession: Optional accession prefix. If None, glob for any *-all-Pathways.tbl
            in the directory and use that prefix.

    Returns:
        (pathways_tbl, transporter_tbl, reactions_tbl) as absolute Path objects.

    Raises:
        FileNotFoundError: If any of the three required files cannot be found.
    """
    if accession is not None:
        pathways = gapseq_dir / f"{accession}-all-Pathways.tbl"
        transporter = gapseq_dir / f"{accession}-Transporter.tbl"
        reactions = gapseq_dir / f"{accession}-all-Reactions.tbl"
    else:
        pathways_glob = list(gapseq_dir.glob("*-all-Pathways.tbl"))
        if not pathways_glob:
            raise FileNotFoundError(
                f"No *-all-Pathways.tbl found in {gapseq_dir}. "
                f"Was gapseq run successfully?"
            )
        pathways = pathways_glob[0]
        prefix = pathways.name.removesuffix("-all-Pathways.tbl")
        transporter = gapseq_dir / f"{prefix}-Transporter.tbl"
        reactions = gapseq_dir / f"{prefix}-all-Reactions.tbl"

    for required in (pathways, transporter, reactions):
        if not required.exists():
            raise FileNotFoundError(
                f"gapseq output missing: {required}. The Phase 4.1 wrapper "
                f"expects all three files (pathways, transporter, reactions) "
                f"to be present. Re-run gapseq for this genome."
            )
    return pathways, transporter, reactions


def load_gapseq_outputs(
    gid: int,
    gapseq_dir: str,
    db_path: str = "data/cultureforge.db",
    accession: Optional[str] = None,
    update_metadata: bool = True,
) -> dict:
    """Load all gapseq output for a genome.

    Args:
        gid: Genome id (must already be registered via register_genome).
        gapseq_dir: Directory containing gapseq TSV output files.
        db_path: SQLite database path.
        accession: Optional accession prefix for file resolution. If None,
            the directory is globbed for *-all-Pathways.tbl.
        update_metadata: If True (default), record gapseq version + run
            date on the genomes row.

    Returns:
        Dict with keys: pathways_loaded, transporters_loaded,
        reaction_markers_loaded, gapseq_version.
    """
    gapseq_dir_p = Path(gapseq_dir).resolve()
    if not gapseq_dir_p.is_dir():
        raise FileNotFoundError(f"gapseq_dir does not exist: {gapseq_dir_p}")

    pathways_tbl, transporter_tbl, reactions_tbl = _resolve_gapseq_files(
        gapseq_dir_p, accession
    )

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)

        n_pathways = load_pathways(conn, gid, str(pathways_tbl))
        n_transporters = load_transporters(conn, gid, str(transporter_tbl))
        n_reactions = load_reaction_markers(conn, gid, str(reactions_tbl))
        # populate_essential_compounds is reference-data; idempotent across runs
        populate_essential_compounds(conn)

        gapseq_version = get_gapseq_version_from_file(str(pathways_tbl))

        conn.commit()
    finally:
        conn.close()

    if update_metadata and gid >= 1000:
        update_genome_metadata(
            db_path=db_path,
            gid=gid,
            gapseq_version=gapseq_version,
        )

    # The existing loaders return tuples (e.g., load_pathways returns
    # (n_total, n_predicted, n_inserted)). Normalize to a flat dict.
    def _scalar(x):
        if isinstance(x, tuple):
            return x[0] if x else 0
        return x or 0

    return {
        "pathways_loaded": _scalar(n_pathways),
        "transporters_loaded": _scalar(n_transporters),
        "reaction_markers_loaded": _scalar(n_reactions),
        "gapseq_version": gapseq_version,
    }


if __name__ == "__main__":
    # Smoke test: re-load gapseq for an existing test genome to a temporary
    # gid in the user range, then deregister.
    import argparse
    import sys

    from register_genome import register_genome, deregister_genome

    parser = argparse.ArgumentParser(description="gapseq_generic smoke test")
    parser.add_argument("--db", default="data/cultureforge.db")
    parser.add_argument("--gapseq-dir", default="data/gapseq/ecoli")
    args = parser.parse_args()

    # Register a fake user genome with a fake-FASTA path that exists
    fasta_path = "data/genomes/ecoli_k12_mg1655.fasta"
    if not Path(fasta_path).exists():
        print(f"FAIL: smoke test FASTA missing: {fasta_path}")
        sys.exit(1)

    gid = register_genome(
        db_path=args.db,
        accession="TEST_GAPSEQ_LOAD",
        file_path=fasta_path,
        notes="gapseq_generic smoke test — DELETE ME",
    )
    print(f"OK: registered gid={gid}")
    try:
        result = load_gapseq_outputs(gid, args.gapseq_dir, db_path=args.db)
        print(f"OK: gapseq loaded — {result}")
    finally:
        deregister_genome(args.db, gid)
        print(f"OK: deregistered gid={gid}")
