"""Genome quality gate for CultureForge metabolic analysis.

Evaluates genome completeness and contamination against MIMAG thresholds
before any metabolic analysis runs.  When a diagnostic marker is absent in
a high-quality genome, its absence is real evidence.  When absent in a
fragmentary genome, its absence is uninformative.

Usage:
    from qc_gate import evaluate_genome_quality, QualityVerdict
    verdict = evaluate_genome_quality(genome_id, conn)
    if verdict.verdict == "REJECT":
        print(f"Genome rejected: {verdict.rationale}")
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from media_constants import GENOME_QC_THRESHOLDS


@dataclass
class QualityVerdict:
    """Result of genome quality assessment."""
    verdict: str          # PROCEED, PROCEED_WITH_FLAG, ESCALATE_STRUCTURAL, REJECT
    completeness: Optional[float]
    contamination: Optional[float]
    genome_size: Optional[int] = None
    gc_content: Optional[float] = None
    n50: Optional[int] = None
    rationale: str = ""
    escalation_reason: Optional[str] = None
    absence_is_evidence: bool = True  # True for high-quality genomes


def evaluate_genome_quality(genome_id: int,
                            conn: sqlite3.Connection) -> QualityVerdict:
    """Evaluate genome quality and return a verdict.

    Returns one of:
      - PROCEED: high quality, all detectors valid, absence is evidence
      - PROCEED_WITH_FLAG: medium quality, absences of markers are uncertain
      - REJECT: below 50% completeness or above 15% contamination
      - NO_QC: CheckM was not run; proceed with caution

    Note: ESCALATE_STRUCTURAL is determined post-detection by the
    capability orchestrator (when QC passes but zero capabilities are
    detected), not here.
    """
    row = conn.execute("""
        SELECT completeness, contamination, strain_heterogeneity,
               genome_size, gc_content, n50
          FROM genome_quality
         WHERE genome_id = ?
    """, (genome_id,)).fetchone()

    if row is None:
        # No QC data — CheckM wasn't run.  Proceed but flag.
        return QualityVerdict(
            verdict="NO_QC",
            completeness=None,
            contamination=None,
            rationale="No CheckM data available. Metabolic analysis will proceed "
                      "but marker absence cannot be interpreted as true absence.",
            absence_is_evidence=False,
        )

    completeness, contamination, strain_het, genome_size, gc, n50 = row

    # Handle case where CheckM wasn't available (quality values are None)
    if completeness is None:
        return QualityVerdict(
            verdict="NO_QC",
            completeness=None,
            contamination=None,
            genome_size=genome_size,
            gc_content=gc,
            n50=n50,
            rationale="CheckM not available — genome stats only. "
                      "Marker absence is not interpretable.",
            absence_is_evidence=False,
        )

    thresholds = GENOME_QC_THRESHOLDS

    # Reject
    if (completeness < thresholds["low_quality"]["completeness"]
            or contamination > thresholds["low_quality"]["contamination"]):
        return QualityVerdict(
            verdict="REJECT",
            completeness=completeness,
            contamination=contamination,
            genome_size=genome_size,
            gc_content=gc,
            n50=n50,
            rationale=(f"Genome quality below minimum: "
                       f"completeness {completeness:.1f}% "
                       f"(min {thresholds['low_quality']['completeness']}%), "
                       f"contamination {contamination:.1f}% "
                       f"(max {thresholds['low_quality']['contamination']}%)"),
            absence_is_evidence=False,
        )

    # High quality
    if (completeness >= thresholds["high_quality"]["completeness"]
            and contamination <= thresholds["high_quality"]["contamination"]):
        return QualityVerdict(
            verdict="PROCEED",
            completeness=completeness,
            contamination=contamination,
            genome_size=genome_size,
            gc_content=gc,
            n50=n50,
            rationale=(f"High-quality genome: "
                       f"completeness {completeness:.1f}%, "
                       f"contamination {contamination:.1f}%"),
            absence_is_evidence=True,
        )

    # Medium quality
    return QualityVerdict(
        verdict="PROCEED_WITH_FLAG",
        completeness=completeness,
        contamination=contamination,
        genome_size=genome_size,
        gc_content=gc,
        n50=n50,
        rationale=(f"Medium-quality genome: "
                   f"completeness {completeness:.1f}%, "
                   f"contamination {contamination:.1f}%. "
                   f"Marker absence may reflect genome incompleteness, "
                   f"not true biological absence."),
        absence_is_evidence=False,
    )
