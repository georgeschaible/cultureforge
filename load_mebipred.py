"""Load MeBiPred per-protein predictions + aggregate into a genome metal profile.

Adds two tables:
    protein_metal_binding   — one row per (protein × metal) prediction
    genome_metal_profile    — aggregated per (genome × metal) with confidence

Every prediction is routed through the confidence module so scores land in
the MeBiPred baseline band (0.50-0.90 per CLAUDE.md addendum 3), with the
multi-protein boost (+0.05 to +0.10, capped at 0.95) applied at the genome
aggregation level per the addendum rules.

Usage:
    python load_mebipred.py <genome_accession> <predictions.tsv>

Example:
    python load_mebipred.py NC_000913.3 data/mebipred/ecoli/ecoli_predictions.tsv
"""

import csv
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import confidence

_ROOT = Path(__file__).parent

DB = str(_ROOT / "data" / "cultureforge.db")

# MeBiPred's trained classifiers (from mymetal.mbp). Note: the addendum
# mentions Mo but the actual trained model doesn't include it — only these 10.
METALS = ["Ca", "Co", "Cu", "Fe", "K", "Mg", "Mn", "Na", "Ni", "Zn"]

# Thresholds per the MeBiPred paper / docs
P_POSITIVE = 0.50   # "binds this metal"
P_HIGH_CONF = 0.75  # "highly confident prediction" per their readme

# Media mapping per CLAUDE.md addendum 2 Translation-to-Media-Components table.
# Pair each metal with a canonical salt + concentration range for later synthesis.
MEDIA_IMPLICATION = {
    "Fe": ("FeSO4·7H2O or FeCl2·4H2O (anaerobic) / FeCl3·6H2O (aerobic)",
           "0.001-0.01 g/L"),
    "Zn": ("ZnSO4·7H2O",        "0.0001-0.001 g/L"),
    "Mn": ("MnCl2·4H2O or MnSO4·H2O", "0.0001-0.001 g/L"),
    "Cu": ("CuSO4·5H2O or CuCl2·2H2O", "0.00001-0.0001 g/L"),
    "Co": ("CoCl2·6H2O",        "0.00001-0.0001 g/L"),
    "Ni": ("NiCl2·6H2O",        "0.00001-0.0001 g/L"),
    "Mg": ("MgSO4·7H2O or MgCl2·6H2O", "0.1-1.0 g/L"),
    "Ca": ("CaCl2·2H2O",        "0.01-0.1 g/L"),
    "K":  ("KCl or K2HPO4",     "0.1-1.0 g/L (usually via buffer)"),
    "Na": ("NaCl",              "0.1-5 g/L (varies widely by organism)"),
}

# Typical bacterial proteome fractions (rough reference). Anything >= this × 1.5
# or a metal-specific ceiling below flags as unusually abundant (anomaly).
# These are heuristic — the addendum calls out W/V/Se as true anomaly targets;
# for the 10 metals the model covers, flagging is best-effort.
TYPICAL_FRACTION_CEILING = {
    "Mg": 0.35,  # Mg is the most common cofactor; only flag extreme cases
    "Fe": 0.20,
    "Zn": 0.12,
    "Mn": 0.15,
    "Ca": 0.25,  # can be high in prokaryotes via non-specific Ca-binding loops
    "K":  0.20,
    "Na": 0.20,
    "Cu": 0.10,
    "Ni": 0.10,
    "Co": 0.08,
}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS protein_metal_binding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    protein_id TEXT NOT NULL,            -- FASTA id (e.g., NC_000913.3_42)
    metal_ion TEXT NOT NULL,
    binding_probability REAL NOT NULL,   -- raw MeBiPred T2<metal> output
    above_threshold INTEGER NOT NULL,    -- 1 if p >= 0.50
    high_confidence INTEGER NOT NULL,    -- 1 if p >= 0.75
    confidence REAL NOT NULL,            -- mapped through confidence.py
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, protein_id, metal_ion)
);

CREATE INDEX IF NOT EXISTS idx_pmb_genome_metal
    ON protein_metal_binding(genome_id, metal_ion);
CREATE INDEX IF NOT EXISTS idx_pmb_above
    ON protein_metal_binding(genome_id, metal_ion, above_threshold);

CREATE TABLE IF NOT EXISTS genome_metal_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    metal_ion TEXT NOT NULL,
    n_binding_proteins INTEGER NOT NULL,  -- p >= 0.5 count
    n_high_confidence INTEGER NOT NULL,   -- p >= 0.75 count
    max_probability REAL NOT NULL,
    fraction_of_proteome REAL NOT NULL,
    confidence REAL NOT NULL,             -- composite (max_prob → baseline + boost)
    is_anomaly INTEGER NOT NULL DEFAULT 0,
    anomaly_note TEXT,
    media_component TEXT,
    typical_concentration TEXT,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, metal_ion)
);

CREATE INDEX IF NOT EXISTS idx_gmp_genome ON genome_metal_profile(genome_id);
"""


def _protein_conf(prob):
    """Map a 0-1 per-protein MeBiPred probability to a ConfidenceScore in the
    MeBiPred baseline band (0.50-0.90). Below p=0.5 we still emit a score
    (capped near 0.50) but the `above_threshold` flag separates the positives."""
    quality = max(0.0, min(1.0, (prob - 0.5) / 0.5))
    return confidence.score(
        "mebipred", "binding_probability", quality,
        context={"raw_value": prob},
    )


def _genome_metal_confidence(max_prob, n_binding, n_high_conf):
    """Composite confidence for a (genome, metal) pair.

    Start with the per-protein baseline from the highest-probability hit,
    then apply the multi-protein boost from CLAUDE.md addendum 3:
      Multiple proteins binding same metal → +0.05 to +0.10 boost (cap 0.95)

    Uses n_binding>=2 → +0.05, n_binding>=5 → +0.10 as the discrete curve.
    """
    base_conf = _protein_conf(max_prob)
    bonus = 0.0
    if n_binding >= 5:
        bonus = 0.10
        note = f"+0.10 multi-protein boost ({n_binding} binders)"
    elif n_binding >= 2:
        bonus = 0.05
        note = f"+0.05 multi-protein boost ({n_binding} binders)"
    else:
        note = "single protein — no multi-protein boost"

    value = min(0.95, base_conf.value + bonus)
    rationale = (f"MeBiPred max_p={max_prob:.2f} across {n_binding} "
                 f"predicted binders (n_high_conf={n_high_conf}); {note}")
    return confidence.ConfidenceScore(
        value=value, source="mebipred",
        rationale=rationale,
        context={"max_probability": max_prob,
                 "n_binding_proteins": n_binding,
                 "n_high_confidence": n_high_conf,
                 "boost_applied": bonus},
    )


def _check_anomaly(metal, fraction, max_prob):
    """Simple anomaly rule: fraction exceeds typical ceiling OR maximally
    saturated single prediction on a rare metal (Cu/Co/Ni)."""
    ceiling = TYPICAL_FRACTION_CEILING.get(metal)
    if ceiling is not None and fraction > ceiling:
        return (1, f"fraction {fraction:.2f} > typical ceiling {ceiling:.2f} — "
                   "flag for review")
    if metal in {"Cu", "Co", "Ni"} and max_prob > 0.95:
        return (1, f"max_p {max_prob:.2f} on rare metal — verify with BRENDA")
    return (0, None)


def load(conn, genome_id, tsv_path):
    conn.executescript(SCHEMA_SQL)
    confidence.populate_source_table(conn)

    # Clear any prior records for this genome (idempotent reload)
    old_pmb_ids = [r[0] for r in conn.execute(
        "SELECT id FROM protein_metal_binding WHERE genome_id=?", (genome_id,))]
    old_gmp_ids = [r[0] for r in conn.execute(
        "SELECT id FROM genome_metal_profile WHERE genome_id=?", (genome_id,))]
    for table, ids in [("protein_metal_binding", old_pmb_ids),
                       ("genome_metal_profile", old_gmp_ids)]:
        if ids:
            qs = ",".join("?" * len(ids))
            conn.execute(
                f"DELETE FROM prediction_confidences "
                f"WHERE related_table=? AND related_id IN ({qs})",
                (table, *ids))
    conn.execute("DELETE FROM protein_metal_binding WHERE genome_id=?",
                 (genome_id,))
    conn.execute("DELETE FROM genome_metal_profile WHERE genome_id=?",
                 (genome_id,))

    with open(tsv_path) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    print(f"  loaded {len(rows)} protein predictions from {tsv_path}")

    # Per-protein, per-metal inserts
    n_bind = 0
    per_metal = {m: [] for m in METALS}  # metal -> list of raw probs
    for r in rows:
        pid = r["protein_id"]
        for metal in METALS:
            prob = float(r[metal])
            above = 1 if prob >= P_POSITIVE else 0
            high = 1 if prob >= P_HIGH_CONF else 0
            conf = _protein_conf(prob)
            conn.execute("""
                INSERT INTO protein_metal_binding
                  (genome_id, protein_id, metal_ion, binding_probability,
                   above_threshold, high_confidence, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (genome_id, pid, metal, prob, above, high, conf.value))
            new_id = conn.execute(
                "SELECT last_insert_rowid()").fetchone()[0]
            # Only record high-signal rows to prediction_confidences — would
            # otherwise explode to 43K rows per genome with mostly non-binders.
            if above:
                confidence.record(conn, "protein_metal_binding", conf,
                                  related_table="protein_metal_binding",
                                  related_id=new_id)
                n_bind += 1
            per_metal[metal].append(prob)

    # Genome-level aggregates
    n_proteome = len(rows)
    n_profile = 0
    for metal, probs in per_metal.items():
        n_bind_total = sum(1 for p in probs if p >= P_POSITIVE)
        n_hc = sum(1 for p in probs if p >= P_HIGH_CONF)
        max_p = max(probs) if probs else 0.0
        fraction = n_bind_total / n_proteome if n_proteome else 0.0
        gmc = _genome_metal_confidence(max_p, n_bind_total, n_hc)
        is_anomaly, note = _check_anomaly(metal, fraction, max_p)
        media_comp, conc = MEDIA_IMPLICATION.get(metal, (None, None))

        conn.execute("""
            INSERT INTO genome_metal_profile
              (genome_id, metal_ion, n_binding_proteins, n_high_confidence,
               max_probability, fraction_of_proteome, confidence,
               is_anomaly, anomaly_note, media_component, typical_concentration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (genome_id, metal, n_bind_total, n_hc, max_p, fraction,
              gmc.value, is_anomaly, note, media_comp, conc))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        confidence.record(conn, "genome_metal_profile", gmc,
                          related_table="genome_metal_profile",
                          related_id=new_id)
        n_profile += 1

    conn.commit()
    return n_proteome, n_bind, n_profile


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: load_mebipred.py <genome_accession> <predictions.tsv>")
    accession, tsv_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(tsv_path):
        sys.exit(f"not found: {tsv_path}")

    conn = sqlite3.connect(DB)
    try:
        row = conn.execute("SELECT id FROM genomes WHERE accession=?",
                           (accession,)).fetchone()
        if not row:
            sys.exit(f"genome accession '{accession}' not found in genomes table")
        genome_id = row[0]

        n_prot, n_bind, n_profile = load(conn, genome_id, tsv_path)
        print(f"  genome_id={genome_id}, proteins={n_prot:,}, "
              f"positive bindings={n_bind:,}, metal profile entries={n_profile}")

        # Display the profile
        print()
        print("  Genome metal profile (ordered by fraction_of_proteome desc):")
        print(f"    {'Metal':6s} {'n_bind':>7s} {'n_high':>7s} {'max_p':>6s} "
              f"{'frac%':>6s} {'conf':>5s}  anomaly")
        for r in conn.execute("""
            SELECT metal_ion, n_binding_proteins, n_high_confidence,
                   max_probability, fraction_of_proteome, confidence,
                   is_anomaly, anomaly_note, media_component, typical_concentration
              FROM genome_metal_profile
             WHERE genome_id=?
          ORDER BY fraction_of_proteome DESC
        """, (genome_id,)):
            flag = "  ⚠ " + r[7] if r[6] else ""
            print(f"    {r[0]:6s} {r[1]:>7d} {r[2]:>7d} {r[3]:>6.2f} "
                  f"{100*r[4]:>5.1f}% {r[5]:>5.2f}{flag}")
            if r[8]:
                print(f"           → media implication: {r[8]} ({r[9]})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
