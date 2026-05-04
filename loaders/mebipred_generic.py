"""Generic MeBiPred output loader (Phase 4.1, optional stage).

Wraps load_mebipred.py's gid-parameterized `load(conn, gid, tsv_path)`
function. MeBiPred is OPTIONAL — the wrapper proceeds without it if the
tool isn't installed; trace-element profile then defaults to the SL-10
baseline rather than organism-specific predictions.

Phase 4.1 prohibition: do NOT modify load_mebipred.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from load_mebipred import load as _load_mebipred, SCHEMA_SQL


def load_mebipred_outputs(
    gid: int,
    predictions_tsv: str,
    db_path: str = "data/cultureforge.db",
) -> dict:
    """Load MeBiPred per-protein predictions for a genome.

    Args:
        gid: Genome id (must already be registered).
        predictions_tsv: Path to MeBiPred's TSV output.
        db_path: SQLite database path.

    Returns:
        Dict with keys: protein_predictions_loaded, metal_profile_rows.
        (Mirrors what the existing load() returns as a flat tuple.)
    """
    tsv_path = Path(predictions_tsv).resolve()
    if not tsv_path.exists():
        raise FileNotFoundError(
            f"MeBiPred predictions TSV missing: {tsv_path}. "
            f"Was MeBiPred run successfully?"
        )

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        result = _load_mebipred(conn, gid, str(tsv_path))
        conn.commit()
    finally:
        conn.close()

    # The existing load() returns (n_proteins, n_confidence_rows, n_metals)
    if isinstance(result, tuple) and len(result) >= 3:
        return {
            "protein_predictions_loaded": result[0],
            "confidence_rows": result[1],
            "metal_profile_rows": result[2],
        }
    return {"raw": result}
