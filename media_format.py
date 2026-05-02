"""Physical media format prediction — recommend solid/liquid/semi-solid/etc.

Per CLAUDE.md Addendum 5, the format recommendation uses a decision tree
based on GenomeSPOT oxygen prediction, gapseq pathway annotations (flagella,
chemotaxis), growth temperature, and pH.

Public API:
    predict_format(conn, genome_id, temperature=None, ph=None) → dict
"""

from __future__ import annotations

import re
import sqlite3
from typing import Optional

import confidence


def _has_pathway_keyword(conn: sqlite3.Connection, genome_id: int,
                         keywords: list) -> bool:
    """Check if any predicted pathway name contains one of the keywords."""
    for kw in keywords:
        row = conn.execute("""
            SELECT 1 FROM genome_pathways
            WHERE genome_id = ? AND predicted = 1
              AND lower(pathway_name) LIKE ?
            LIMIT 1
        """, (genome_id, f"%{kw.lower()}%")).fetchone()
        if row:
            return True
    return False


def _get_genomespot_oxygen(conn: sqlite3.Connection, genome_id: int
                           ) -> Optional[str]:
    row = conn.execute("""
        SELECT value FROM genome_growth_predictions
        WHERE genome_id = ? AND target = 'oxygen'
    """, (genome_id,)).fetchone()
    return row[0] if row else None


def predict_format(conn: sqlite3.Connection, genome_id: int,
                   temperature: Optional[float] = None,
                   ph: Optional[float] = None) -> dict:
    """Recommend physical media format per CLAUDE.md addendum 5 decision tree.

    Returns {
        "primary_format": str,
        "primary_detail": str,
        "solidifying_agent": str,
        "solidifying_detail": str,
        "alternative": str | None,
        "warnings": list of str,
        "confidence": ConfidenceScore,
        "rationale": str,
    }
    """
    oxygen = _get_genomespot_oxygen(conn, genome_id)
    is_strict_anaerobe = (oxygen and "not tolerant" in oxygen.lower())

    # Get temperature from GenomeSPOT if not supplied
    if temperature is None:
        row = conn.execute("""
            SELECT numeric_value FROM genome_growth_predictions
            WHERE genome_id = ? AND target = 'temperature_optimum'
        """, (genome_id,)).fetchone()
        if row and row[0]:
            temperature = row[0]

    # Check for flagella / chemotaxis / motility genes
    has_flagella = _has_pathway_keyword(conn, genome_id,
        ["flagell", "motility", "fliC", "flgE", "motA", "motB"])
    has_chemotaxis = _has_pathway_keyword(conn, genome_id,
        ["chemotaxis", "cheA", "cheB", "cheY"])

    # Check for sulfide/iron oxidation pathways (gradient organisms)
    has_sulfide_oxidation = _has_pathway_keyword(conn, genome_id,
        ["sulfide oxidation", "sulfur oxidation", "thiosulfate oxidation"])
    has_iron_oxidation = _has_pathway_keyword(conn, genome_id,
        ["iron oxidation", "Fe(II) oxidation"])

    # Check carbon source diversity (oligotroph detection).
    # Table may not exist if carbon profile hasn't been loaded yet.
    try:
        n_carbon = conn.execute("""
            SELECT COUNT(*) FROM genome_carbon_sources WHERE genome_id = ?
        """, (genome_id,)).fetchone()[0]
    except sqlite3.OperationalError:
        n_carbon = 99  # assume not an oligotroph if we have no data

    warnings = []
    conf_val = 0.80

    # Check for sulfate reduction (SRBs should NOT get gradient tubes)
    is_sulfate_reducer = _has_pathway_keyword(conn, genome_id,
        ["sulfate reduction", "dissimilatory sulfat"])

    # Decision tree per addendum 5
    # 1. Strict anaerobe?
    if is_strict_anaerobe:
        primary = "Liquid in sealed tubes (Hungate/Balch technique)"
        detail = ("Strict anaerobe — requires O₂-free conditions. "
                  "Use Hungate tubes or Balch tubes with butyl rubber stoppers "
                  "and aluminum crimps. Prepare under N₂ or N₂:CO₂ atmosphere.")
        alternative = ("Roll tubes (anaerobic + solid surface) OR anaerobic "
                       "chamber + agar plates if colony isolation needed")
        warnings.append("STRICT ANAEROBE — all manipulation must use "
                        "Hungate technique or anaerobic glove box")
        conf_val = 0.90

        # Sub-check: gradient organism — but NOT if it's a sulfate reducer
        # (SRBs have sulfide-oxidation genes used in reverse; they don't
        # actually live at O₂/H₂S gradients)
        if (has_sulfide_oxidation or has_iron_oxidation) and not is_sulfate_reducer:
            primary = "Gradient tubes (0.15-0.3% agar, opposing gradients)"
            detail = ("Predicted sulfide/iron oxidizer at redox interface — "
                      "use gradient tube with reduced compound in bottom agar "
                      "and oxidant from top.")
            conf_val = 0.80

    # 2. Microaerophile? (detected via pathway annotations)
    elif _has_pathway_keyword(conn, genome_id,
                              ["microaeroph", "microoxic", "low oxygen"]):
        primary = "Semi-solid gradient media (0.2-0.3% agar)"
        detail = ("Predicted microaerophile — organism will form a band "
                  "at preferred O₂ tension in semi-solid medium.")
        alternative = "Sealed serum bottle with 2-5% O₂ in N₂"
        conf_val = 0.80

    # 3. Motile chemotactic organism?
    elif has_flagella and has_chemotaxis:
        primary = "Solid agar plates (1.5%) for isolation; semi-solid (0.3%) for enrichment"
        detail = ("Genome encodes flagellar biosynthesis + chemotaxis — "
                  "motile organism. Semi-solid media useful for enrichment "
                  "(organism spreads through agar, trackable).")
        alternative = "Liquid broth for routine cultivation"
        conf_val = 0.80

    # 4. Oligotroph?
    elif n_carbon < 5:
        primary = "Dilute liquid media or filter cultivation"
        detail = ("Very few carbon utilization pathways predicted (<5) — "
                  "possible oligotroph. Consider dilute media, extinction "
                  "dilution, or filter cultivation (0.2 µm membrane on agar).")
        alternative = "Standard agar plates with dilute nutrients (1/10 R2A)"
        conf_val = 0.70
        warnings.append("Possible oligotroph — standard rich media may inhibit growth")

    # 5. Default: standard aerobe
    else:
        primary = "Solid agar plates (1.5%) for isolation; liquid broth for cultivation"
        detail = "Standard aerobic/facultative organism — no special format needed."
        alternative = None
        conf_val = 0.85

    # Solidifying agent selection (addendum 5 table)
    if temperature and temperature > 65:
        solid_agent = "Gellan gum (Gelrite/Phytagel) 0.5-1.0%"
        solid_detail = ("Growth temperature >65°C — agar hydrolyzes at high "
                        "temperature. Gellan gum requires 1-3 mM divalent cation "
                        "(MgCl₂ or CaCl₂) for solidification.")
        warnings.append("HIGH TEMPERATURE — use gellan gum, NOT agar")
    elif ph and ph < 4:
        solid_agent = "Gellan gum (Gelrite) 0.5-0.8%"
        solid_detail = ("pH <4 — agar hydrolyzes at low pH during autoclaving. "
                        "Gellan gum + divalent cation.")
        warnings.append("LOW pH — use gellan gum, NOT agar")
    else:
        solid_agent = "Agar (Bacto or Noble) 1.2-2.0%"
        solid_detail = "Standard — works for most organisms at moderate T and pH."

    rationale_parts = []
    if is_strict_anaerobe:
        rationale_parts.append("GenomeSPOT: strict anaerobe")
    if has_flagella:
        rationale_parts.append("flagellar genes detected")
    if has_chemotaxis:
        rationale_parts.append("chemotaxis genes detected")
    rationale = "; ".join(rationale_parts) if rationale_parts else "default format"

    return {
        "primary_format": primary,
        "primary_detail": detail,
        "solidifying_agent": solid_agent,
        "solidifying_detail": solid_detail,
        "alternative": alternative,
        "warnings": warnings,
        "confidence": confidence.ConfidenceScore(
            value=conf_val, source="media_format",
            rationale=rationale,
        ),
        "rationale": rationale,
    }
