"""CultureForge confidence scoring framework.

Every prediction in CultureForge carries a 0.0-1.0 confidence score with
explainable rationale and provenance. Scores propagate through composite
predictions and combine into final recipe-level confidence.

This module is the single source of truth for scoring. Per CLAUDE.md addendum 3:
    "Build this as a central Python module that all other components import.
     Every component that generates predictions must call into this module
     rather than inventing its own scoring."

Public API:
    score(source, metric_type, raw_value, context=None) -> ConfidenceScore
    combine(method, scores, weights=None, agreement_bonus=False) -> ConfidenceScore
    explain(conf) -> str
    category(value) -> str
    populate_source_table(conn) -> None     # one-time DB seed
    record(conn, prediction_type, confidence_score, related_table=None,
           related_id=None) -> int          # log to prediction_confidences

Confidence categories (from addendum 3):
    LOW       < 0.60
    MEDIUM    0.60 - 0.80
    HIGH      0.80 - 0.95
    VERY HIGH ≥ 0.95
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List


# ---------------------------------------------------------------- data model

@dataclass
class ConfidenceScore:
    """A single 0-1 confidence score with explainable rationale and provenance.

    Attributes:
        value:      0.0 to 1.0 inclusive
        source:     short tag for the data source / tool ("phylo_16s", "gapseq", ...)
        rationale:  one-sentence human-readable explanation
        context:    optional dict of structured metadata (raw values, IDs, ...)
    """

    value: float
    source: str
    rationale: str
    context: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"confidence value must be numeric, got {type(self.value)}")
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"confidence value {self.value} outside [0.0, 1.0]")

    @property
    def category(self) -> str:
        return category(self.value)

    def to_dict(self) -> dict:
        return asdict(self)


def category(value: float) -> str:
    """Map a 0-1 confidence to one of the four named categories."""
    if value >= 0.95:
        return "VERY HIGH"
    if value >= 0.80:
        return "HIGH"
    if value >= 0.60:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------- baselines

# Source baselines as defined in CLAUDE.md addendum 3.
# Single value = fixed baseline. Tuple (lo, hi) = range scaled by raw_value
# (interpreted as 0-1 quality fraction).
SOURCE_BASELINES: dict[str, object] = {
    "mediadive":              0.95,
    "bacdive_experimental":   0.90,
    "bacdive_inferred":       0.70,
    "tempura_experimental":   0.85,
    "tempura_predicted":      0.65,
    "gapseq":                (0.50, 0.95),
    "genomespot":            (0.50, 0.95),
    "mebipred":              (0.50, 0.90),
    "brenda":                 0.90,
    "esmfold":               (0.30, 0.95),
    "foldseek":              (0.40, 0.95),
    "alphafold":             (0.50, 0.95),
    "hhpred":                (0.40, 0.95),
    "amend_shock":            0.90,
    "user_supplied":          0.95,
}

SOURCE_RATIONALES: dict[str, str] = {
    "mediadive":            "Expert-curated from published protocols",
    "bacdive_experimental": "Direct experimental observations",
    "bacdive_inferred":     "Predicted from related strains",
    "tempura_experimental": "Literature-sourced growth temperatures",
    "tempura_predicted":    "Model-inferred growth temperatures",
    "gapseq":               "gapseq metabolic prediction (scales with completeness % and bitscore)",
    "genomespot":           "GenomeSPOT growth condition prediction (scales with reported probability)",
    "mebipred":             "MeBiPred metal-binding prediction (~90% baseline accuracy)",
    "brenda":               "Experimentally characterized enzyme data",
    "esmfold":              "ESMFold structure prediction (uses pLDDT)",
    "foldseek":             "Foldseek structural homology (probability + TM-score)",
    "alphafold":            "AlphaFold DB structure (uses pLDDT)",
    "hhpred":               "HHPred profile-profile match (uses probability)",
    "amend_shock":          "Peer-reviewed thermodynamic measurements",
    "user_supplied":        "User-supplied — trust the experimentalist",
}


# ---------------------------------------------------------------- scoring rules

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _score_phylo_identity(identity: float, context: dict) -> ConfidenceScore:
    """16S identity-based score per CLAUDE.md addendum 3 brackets:
       ≥97 → 0.90-0.95, 90-97 → 0.70-0.90, 85-90 → 0.50-0.70, <85 → 0.30-0.50."""
    if identity >= 97:
        v = 0.90 + 0.05 * _clamp((identity - 97) / 3, 0, 1)
        rat = (f"16S identity {identity:.1f}% — species-level match, "
               f"reliable phylogenetic placement")
    elif identity >= 90:
        v = 0.70 + 0.20 * (identity - 90) / 7
        rat = (f"16S identity {identity:.1f}% — genus-level match, "
               f"reasonably reliable")
    elif identity >= 85:
        v = 0.50 + 0.20 * (identity - 85) / 5
        rat = (f"16S identity {identity:.1f}% — family-level match, "
               f"moderate confidence")
    else:
        # <85% — clamp to 0.30 floor; recommend Tier 2/3
        v = _clamp(0.30 + 0.20 * (identity - 70) / 15, 0.30, 0.50)
        rat = (f"16S identity {identity:.1f}% — phylum-level at best; "
               f"consider Tier 2/3 structural analysis")
    return ConfidenceScore(value=v, source="phylo_16s", rationale=rat,
                           context=context)


def _score_gapseq_pathway(completeness: float, context: dict) -> ConfidenceScore:
    """gapseq pathway prediction. Uses both completeness % and the strict
    `predicted` flag (in context). Brackets per addendum 3."""
    predicted = bool(context.get("predicted", False))
    c = completeness
    if c >= 90 and predicted:
        v = 0.90 + 0.05 * _clamp((c - 90) / 10, 0, 1)
        rat = (f"gapseq pathway completeness {c:.0f}% with key enzymes "
               f"(predicted=true)")
    elif c >= 75 or predicted:
        # 0.70 floor when either: completeness>=75 OR predicted=true
        base = 0.70
        if c >= 75:
            base += 0.20 * _clamp((c - 75) / 15, 0, 1)
        if predicted:
            base = max(base, 0.80)
        v = _clamp(base, 0.70, 0.90)
        rat = (f"gapseq pathway completeness {c:.0f}% "
               f"(predicted={'true' if predicted else 'false'})")
    elif c >= 50:
        v = 0.40 + 0.30 * (c - 50) / 25
        rat = f"gapseq pathway completeness {c:.0f}% — partial evidence"
    else:
        v = 0.20 + 0.20 * c / 50
        rat = f"gapseq pathway completeness {c:.0f}% — weak evidence"
    return ConfidenceScore(value=_clamp(v, 0.20, 0.95),
                           source="gapseq", rationale=rat, context=context)


def _score_gapseq_transporter(bitscore: float, pident: float,
                              context: dict) -> ConfidenceScore:
    """Transporter prediction confidence from BLAST evidence."""
    # bitscore is the primary indicator; pident is secondary
    if bitscore is None:
        v = 0.50
        rat = "transporter prediction with no BLAST evidence"
    else:
        # bitscore 200 → 0.70, 500 → 0.85, 1000+ → 0.95
        b_score = _clamp(0.70 + (bitscore - 200) / 1600, 0.50, 0.95)
        # pident bonus: 0 at 50%, +0.05 at 100%
        p_bonus = _clamp((pident - 50) / 1000, 0, 0.05) if pident else 0
        v = _clamp(b_score + p_bonus, 0.50, 0.95)
        rat = (f"transporter via BLAST (bitscore={bitscore:.0f}, "
               f"pident={pident:.1f}%)")
    return ConfidenceScore(value=v, source="gapseq", rationale=rat,
                           context=context)


def _score_thermal_match(query_class: Optional[str], hit_class: Optional[str],
                         context: dict) -> ConfidenceScore:
    """Confidence that a hit's media will be appropriate for the query thermally."""
    classes = ["psychrophile", "mesophile", "thermophile", "hyperthermophile"]
    if query_class is None or hit_class is None:
        v = 0.70
        rat = "thermal match unknown (no T_opt data)"
    else:
        qi = classes.index(query_class)
        hi = classes.index(hit_class)
        dist = abs(qi - hi)
        # 0 → 0.95, 1 → 0.70, 2 → 0.40, 3 → 0.25
        v = max(0.25, 0.95 - 0.25 * dist)
        rat = (f"thermal match query={query_class} hit={hit_class} "
               f"(distance={dist})")
    return ConfidenceScore(value=v, source="thermal_inference",
                           rationale=rat, context=context)


def _score_baseline(source: str, raw_value: float,
                    context: dict) -> ConfidenceScore:
    """Generic source baseline lookup. raw_value is interpreted as 0-1 quality
    if the source has a range baseline."""
    if source not in SOURCE_BASELINES:
        return ConfidenceScore(value=0.50, source=source,
                               rationale=f"unknown source '{source}', default 0.50",
                               context=context)
    baseline = SOURCE_BASELINES[source]
    rat = SOURCE_RATIONALES.get(source, source)
    if isinstance(baseline, tuple):
        lo, hi = baseline
        # raw_value is treated as 0-1 quality fraction within the baseline range
        q = _clamp(raw_value if raw_value is not None else 0.5, 0, 1)
        v = lo + (hi - lo) * q
        rat = f"{rat} (quality {q:.2f} → {v:.2f})"
    else:
        v = baseline
    return ConfidenceScore(value=v, source=source, rationale=rat,
                           context=context)


# Map (source, metric_type) → handler function. The fallback is _score_baseline.
_HANDLERS = {
    ("phylo_16s", "identity_pct"):           lambda rv, ctx: _score_phylo_identity(rv, ctx),
    ("gapseq",    "pathway_completeness"):    lambda rv, ctx: _score_gapseq_pathway(rv, ctx),
    ("gapseq",    "transporter_bitscore"):    lambda rv, ctx: _score_gapseq_transporter(rv, ctx.get("pident", 0), ctx),
    ("thermal",   "class_match"):             lambda rv, ctx: _score_thermal_match(ctx.get("query_class"), ctx.get("hit_class"), ctx),
}


def score(source: str, metric_type: str, raw_value, context: dict = None
          ) -> ConfidenceScore:
    """Compute a confidence score for a single prediction.

    Args:
        source:       short tag, e.g. "gapseq", "phylo_16s", "mebipred"
        metric_type:  what kind of metric raw_value represents
        raw_value:    the raw metric (identity %, completeness %, prob, etc.)
        context:      optional dict of related metadata (also stored in result)

    Returns: ConfidenceScore.
    """
    context = dict(context or {})
    handler = _HANDLERS.get((source, metric_type))
    if handler is not None:
        return handler(raw_value, context)
    return _score_baseline(source, raw_value, context)


# ---------------------------------------------------------------- combine

def combine(method: str, scores: List[ConfidenceScore],
            weights: List[float] = None,
            agreement_bonus: bool = False) -> ConfidenceScore:
    """Combine multiple ConfidenceScores into a single composite score.

    Methods:
        "min"            — take the lowest (conservative; for critical components)
        "mean"           — arithmetic mean
        "weighted_mean"  — weighted average (requires `weights` of same length)
        "independent"    — 1 - prod(1 - p) (probabilistic OR for independent
                           lines of evidence accumulating)

    agreement_bonus: when True and ≥2 scores all exceed the minimum by less than
        0.10 (i.e. they agree), add +0.05 (capped at 0.95). Per the addendum:
        "Multiple proteins binding same metal → +0.05 to +0.10 boost (cap at 0.95)"
    """
    if not scores:
        return ConfidenceScore(value=0.0, source="combined",
                               rationale="no scores supplied", context={"n": 0})
    if len(scores) == 1:
        return scores[0]

    values = [s.value for s in scores]
    sources = [s.source for s in scores]

    if method == "min":
        idx = min(range(len(values)), key=lambda i: values[i])
        v = values[idx]
        why = f"min of {len(scores)} ({sources[idx]} = {v:.2f})"
    elif method == "mean":
        v = sum(values) / len(values)
        why = f"mean of {len(scores)} sources"
    elif method == "weighted_mean":
        if weights is None or len(weights) != len(scores):
            raise ValueError("weighted_mean requires `weights` of equal length")
        total_w = sum(weights)
        if total_w <= 0:
            raise ValueError("weights must sum to a positive number")
        v = sum(s.value * w for s, w in zip(scores, weights)) / total_w
        why = f"weighted mean of {len(scores)} sources (w={weights})"
    elif method == "independent":
        prod = 1.0
        for x in values:
            prod *= (1.0 - x)
        v = 1.0 - prod
        why = f"independent combination of {len(scores)} sources"
    else:
        raise ValueError(f"unknown combine method: {method!r}")

    bonus = 0.0
    bonus_note = ""
    if agreement_bonus and len(scores) >= 2:
        lo, hi = min(values), max(values)
        if hi - lo < 0.10:
            bonus = 0.05
            bonus_note = " +0.05 agreement bonus"
    v = _clamp(v + bonus, 0.0, 0.95 if bonus > 0 else 1.0)

    return ConfidenceScore(
        value=v,
        source="combined",
        rationale=why + bonus_note,
        context={
            "method": method,
            "n_scores": len(scores),
            "contributing_sources": sources,
            "contributing_values": values,
            "agreement_bonus_applied": bonus > 0,
        },
    )


# ---------------------------------------------------------------- explain

def explain(conf: ConfidenceScore, brief: bool = False) -> str:
    """Render a ConfidenceScore as a one-line human-readable string."""
    pct = int(round(conf.value * 100))
    if brief:
        return f"{pct}% [{conf.category}]"
    return f"{pct}% [{conf.category}] — {conf.rationale}"


# ---------------------------------------------------------------- DB helpers

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS source_confidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    subtype TEXT,                       -- e.g. "experimental" / "predicted"
    baseline_min REAL NOT NULL,
    baseline_max REAL,                  -- NULL when fixed baseline
    rationale TEXT,
    last_updated TEXT,
    UNIQUE (source_name, subtype)
);

CREATE TABLE IF NOT EXISTS prediction_confidences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_type TEXT NOT NULL,      -- e.g. "pathway", "transporter", "phylo_hit"
    source TEXT NOT NULL,
    raw_value REAL,
    context_json TEXT,
    computed_confidence REAL NOT NULL,
    explanation TEXT,
    related_table TEXT,                 -- which row this attaches to
    related_id INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pc_type   ON prediction_confidences(prediction_type);
CREATE INDEX IF NOT EXISTS idx_pc_rel    ON prediction_confidences(related_table, related_id);
"""


def populate_source_table(conn: sqlite3.Connection) -> int:
    """Idempotently populate `source_confidence` from SOURCE_BASELINES.
    Returns number of rows inserted/updated."""
    conn.executescript(SCHEMA_SQL)
    now = datetime.utcnow().isoformat(timespec="seconds")
    n = 0
    for src, baseline in SOURCE_BASELINES.items():
        # Split sources with embedded subtype like "bacdive_experimental".
        # Use "" (not NULL) for absent subtype — SQLite treats NULLs as
        # distinct in UNIQUE constraints, which would break idempotency.
        if "_" in src and src.startswith(("bacdive_", "tempura_")):
            base, sub = src.split("_", 1)
            name = base
            subtype = sub
        else:
            name = src
            subtype = ""
        if isinstance(baseline, tuple):
            lo, hi = baseline
        else:
            lo, hi = baseline, None
        rationale = SOURCE_RATIONALES.get(src, "")
        conn.execute("""
            INSERT INTO source_confidence
                (source_name, subtype, baseline_min, baseline_max,
                 rationale, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_name, subtype) DO UPDATE SET
                baseline_min = excluded.baseline_min,
                baseline_max = excluded.baseline_max,
                rationale    = excluded.rationale,
                last_updated = excluded.last_updated
        """, (name, subtype, lo, hi, rationale, now))
        n += 1
    conn.commit()
    return n


def record(conn: sqlite3.Connection, prediction_type: str,
           confidence: ConfidenceScore,
           related_table: str = None, related_id: int = None) -> int:
    """Persist a ConfidenceScore to prediction_confidences. Returns the new row id."""
    conn.execute("""
        INSERT INTO prediction_confidences
            (prediction_type, source, raw_value, context_json,
             computed_confidence, explanation, related_table, related_id,
             created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prediction_type,
        confidence.source,
        confidence.context.get("raw_value"),
        json.dumps(confidence.context, default=str),
        confidence.value,
        confidence.rationale,
        related_table,
        related_id,
        datetime.utcnow().isoformat(timespec="seconds"),
    ))
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
