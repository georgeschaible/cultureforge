"""Load GenomeSPOT predictions into the CultureForge database.

Adds table:
    genome_growth_predictions — one row per (genome, target) prediction, with
                                 value, error, novelty flag, warning, and
                                 confidence scored through confidence.py

Also records each prediction as a row in `prediction_confidences` so the
provenance is queryable alongside gapseq predictions.

Usage:
    python load_genomespot.py <genome_accession> <predictions.tsv>

Example:
    python load_genomespot.py NC_000913.3 data/genomespot/ecoli/ecoli.predictions.tsv
"""

import csv
import json
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import confidence

_ROOT = Path(__file__).parent

DB = str(_ROOT / "data" / "cultureforge.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS genome_growth_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    source TEXT NOT NULL,           -- e.g. "GenomeSPOT"
    target TEXT NOT NULL,           -- temperature_optimum, ph_optimum, etc.
    value TEXT NOT NULL,            -- numeric as string OR categorical
                                    -- ("tolerant"/"not tolerant" for oxygen)
    numeric_value REAL,             -- parsed if numeric, NULL if categorical
    error REAL,                     -- 1σ RMSE for continuous, probability for oxygen
    units TEXT,
    is_novel INTEGER,               -- 1 if genome features are unusual vs training
    warning TEXT,                   -- e.g. "min_exceeded"
    confidence REAL,                -- computed via confidence.score()
    created_at TEXT NOT NULL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, source, target)
);

CREATE INDEX IF NOT EXISTS idx_ggp_genome_target
    ON genome_growth_predictions(genome_id, target);
"""


def parse_tsv(path):
    with open(path) as f:
        # TSV with header: target, value, error, units, is_novel, warning
        rdr = csv.DictReader(f, delimiter="\t")
        return list(rdr)


def score_prediction(target, value, error, is_novel, warning):
    """Compute a ConfidenceScore for a single GenomeSPOT prediction.

    GenomeSPOT's own confidence signals:
      - For continuous predictions: `error` is RMSE (lower = more confident).
        Relative to the prediction value is a better normalised measure.
      - For oxygen (categorical): `error` is a probability 0.5-1.0.
      - `is_novel=True` → extrapolation flag → reduce confidence.
      - `warning` present → reduce confidence.

    Maps into the GenomeSPOT baseline band (0.50-0.95) per addendum 3.
    """
    context = {
        "raw_value": value,
        "error": error,
        "target": target,
        "is_novel": is_novel,
        "warning": warning,
    }

    if target == "oxygen":
        p = max(0.5, min(1.0, float(error)))
        quality = (p - 0.5) / 0.5
        conf = confidence.score("genomespot", "oxygen_probability",
                                quality, context=context)
        rationale = (f"GenomeSPOT oxygen probability {p:.2f} "
                     f"(baseline-scaled → {conf.value:.2f})")
        base_val = conf.value
    else:
        try:
            v = float(value)
            e = float(error) if error is not None else None
        except (TypeError, ValueError):
            v = e = None
        if v is None or e is None or v == 0:
            quality = 0.5
        else:
            rel = e / max(abs(v), 1.0)
            quality = max(0.0, min(1.0, 1.0 - rel))
        conf = confidence.score("genomespot", "prediction_error",
                                quality, context=context)
        rationale = (f"GenomeSPOT {target}={value}±{error} "
                     f"(quality {quality:.2f} → {conf.value:.2f})")
        base_val = conf.value

    # Apply penalties by constructing a NEW ConfidenceScore (never mutate)
    penalty = 0.0
    if is_novel:
        penalty += 0.10
        rationale += " [novel genome features: -0.10]"
    if warning:
        penalty += 0.05
        rationale += f" [warning: {warning}, -0.05]"

    final_val = max(0.50, base_val - penalty)
    return confidence.ConfidenceScore(
        value=final_val, source="genomespot",
        rationale=rationale, context=context,
    )


def load(conn, genome_id, tsv_path, source_name="GenomeSPOT"):
    conn.executescript(SCHEMA_SQL)
    # Ensure confidence tables exist (idempotent)
    confidence.populate_source_table(conn)

    rows = parse_tsv(tsv_path)
    print(f"  Loading {len(rows)} predictions from {tsv_path}")

    # Clear any prior records for this (genome, source) combination to keep the
    # loader idempotent without leaving stale confidence records behind.
    old_ids = [r[0] for r in conn.execute(
        "SELECT id FROM genome_growth_predictions "
        "WHERE genome_id=? AND source=?", (genome_id, source_name))]
    if old_ids:
        qmarks = ",".join("?" * len(old_ids))
        conn.execute(
            f"DELETE FROM prediction_confidences "
            f"WHERE related_table='genome_growth_predictions' "
            f"  AND related_id IN ({qmarks})", old_ids)
        conn.execute(
            "DELETE FROM genome_growth_predictions "
            "WHERE genome_id=? AND source=?", (genome_id, source_name))

    n_loaded = 0
    for r in rows:
        target = r["target"].strip()
        raw_val = r["value"].strip()
        try:
            numeric = float(raw_val)
        except ValueError:
            numeric = None
        try:
            err = float(r["error"]) if r.get("error") else None
        except ValueError:
            err = None
        units = r.get("units") or None
        is_novel = 1 if str(r.get("is_novel", "False")).lower() == "true" else 0
        warning = r.get("warning")
        if warning in (None, "", "None"):
            warning = None

        conf = score_prediction(target, raw_val, err, bool(is_novel), warning)

        conn.execute("""
            INSERT INTO genome_growth_predictions
                (genome_id, source, target, value, numeric_value,
                 error, units, is_novel, warning, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (genome_id, source_name, target, raw_val, numeric, err,
              units, is_novel, warning, conf.value,
              date.today().isoformat()))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        confidence.record(conn, "growth_prediction", conf,
                          related_table="genome_growth_predictions",
                          related_id=new_id)
        n_loaded += 1

    conn.commit()
    return n_loaded


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: load_genomespot.py <genome_accession> <predictions.tsv>")
    accession, tsv_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(tsv_path):
        sys.exit(f"not found: {tsv_path}")

    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT id FROM genomes WHERE accession=?", (accession,)
        ).fetchone()
        if not row:
            sys.exit(f"genome accession '{accession}' not found in genomes table")
        genome_id = row[0]
        print(f"  genome_id={genome_id} for accession {accession}")

        n = load(conn, genome_id, tsv_path)
        print(f"  Loaded {n} predictions")

        # Show what we loaded with confidence scores
        print()
        print("  GenomeSPOT predictions summary:")
        for r in conn.execute("""
            SELECT target, value, error, units, confidence, warning, is_novel
              FROM genome_growth_predictions
             WHERE genome_id=? AND source='GenomeSPOT'
          ORDER BY target
        """, (genome_id,)):
            w = f" ({r[5]})" if r[5] else ""
            n_flag = " [novel]" if r[6] else ""
            err = f"±{r[2]:.2f}" if r[2] is not None else ""
            print(f"    {r[0]:22s} {r[1]:>12s} {err:>8s} {r[3] or '':12s} "
                  f"conf={r[4]:.2f}{w}{n_flag}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
