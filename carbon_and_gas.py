"""Carbon source verification + gas phase recommendation from gapseq pathways.

Per CLAUDE.md Addendum 4, these two features enhance the synthesizer:

  1. **Carbon source verification** — checks whether the template medium's
     carbon source is metabolically compatible with the organism's predicted
     degradation pathways. Flags mismatches (e.g., glucose in a medium for
     an organism with no glycolysis pathway).

  2. **Gas phase recommendation** — infers headspace gas composition from
     hydrogen-related gapseq pathways. Detects uptake hydrogenases (→ add H₂),
     fermentative H₂ production (→ may need H₂ removal), and anaerobic/aerobic
     terminal oxidases (→ N₂/CO₂ vs air).

Both use existing `genome_pathways` data — no new tools or databases needed.
This is the "gapseq pathway → substrate/gas" bridge that the addendum describes
as complementing CAZy.

Public API:
    get_carbon_profile(conn, genome_id) → dict of {substrate: confidence_info}
    verify_carbon_source(conn, genome_id, compound_name) → (compatible, explanation)
    get_gas_phase_recommendation(conn, genome_id) → dict with headspace, rationale
"""

from __future__ import annotations

import re
import sqlite3
from typing import Dict, List, Optional, Tuple

import confidence


# ---------------------------------------------------------------- schema

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS genome_carbon_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    carbon_source TEXT NOT NULL,
    evidence_type TEXT NOT NULL,    -- 'gapseq_pathway' or 'cazyme' (future)
    evidence_pathway TEXT,
    max_completeness REAL,
    confidence REAL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, carbon_source)
);
CREATE INDEX IF NOT EXISTS idx_gcs_genome ON genome_carbon_sources(genome_id);

CREATE TABLE IF NOT EXISTS genome_hydrogenases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    gene_id TEXT NOT NULL,
    hydrogenase_type TEXT NOT NULL,     -- [NiFe] or [FeFe]
    group_id TEXT NOT NULL,            -- 1/2/3/4 for [NiFe]; A-F for [FeFe]
    reference_id TEXT,
    reference_acc TEXT,
    pident REAL,
    evalue REAL,
    bitscore REAL,
    confidence REAL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, gene_id, reference_id)
);
CREATE INDEX IF NOT EXISTS idx_gh_genome ON genome_hydrogenases(genome_id);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create carbon_sources and hydrogenases tables if they don't exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


# ---------------------------------------------------------------- carbon source mapping

# Map gapseq pathway name patterns → utilizable carbon substrates.
# Each entry: (pathway_pattern, [carbon_sources_it_enables])
PATHWAY_TO_CARBON = [
    # Sugars
    (r"glycolysis.*(glucose|from glucose)", ["glucose"]),
    (r"galactose degradation", ["galactose"]),
    (r"lactose degradation", ["lactose"]),
    (r"maltose degradation", ["maltose"]),
    (r"sucrose degradation", ["sucrose"]),
    (r"trehalose degradation", ["trehalose"]),
    (r"fructose degradation|fructose.*utiliz", ["fructose"]),
    (r"mannose degradation", ["mannose"]),
    (r"xylose degradation|xylose.*utiliz", ["xylose"]),
    (r"L-arabinose degradation", ["arabinose"]),
    (r"D-arabinose degradation", ["arabinose"]),
    (r"L-rhamnose degradation", ["rhamnose"]),
    (r"L-fucose degradation", ["fucose"]),
    (r"ribose degradation|ribose.*utiliz", ["ribose"]),
    (r"cellobiose degradation", ["cellobiose"]),
    # Polyols
    (r"glycerol degradation", ["glycerol"]),
    (r"D-arabinitol degradation|arabitol", ["arabitol"]),
    (r"ribitol degradation", ["ribitol"]),
    (r"sorbitol|glucitol degradation", ["sorbitol"]),
    (r"mannitol degradation", ["mannitol"]),
    (r"xylitol degradation", ["xylitol"]),
    (r"ethylene glycol degradation", ["ethylene glycol"]),
    # Organic acids (critical for SRBs and anaerobes)
    (r"pyruvate fermentation|pyruvate.*oxidat", ["pyruvate"]),
    (r"lactate.*fermentation|lactate.*oxidat|L-lactaldehyde degradation",
     ["lactate"]),
    (r"acetate.*utiliz|acetate.*oxidat|acetyl-CoA.*from.*acetate", ["acetate"]),
    (r"formate.*oxidat|formate.*dehydrogenase", ["formate"]),
    (r"citrate.*degradation|citrate.*utiliz|TCA cycle", ["citrate"]),
    (r"succinate.*degradation|succinate.*oxidat", ["succinate"]),
    (r"fumarate.*degradation|fumarate.*reduct", ["fumarate"]),
    (r"L-malate degradation", ["malate"]),
    (r"propionate.*degradation|propionate.*oxidat", ["propionate"]),
    (r"butyrate.*degradation|butyrate.*oxidat", ["butyrate"]),
    (r"benzoate degradation", ["benzoate"]),
    (r"oxalate degradation", ["oxalate"]),
    # Alcohols
    (r"ethanol degradation|ethanol.*oxidat", ["ethanol"]),
    (r"methanol.*degradation|methanol.*oxidat", ["methanol"]),
    # Complex polymers (CAZy-level — from gapseq pathway names)
    (r"starch degradation|amylase|starch.*utiliz", ["starch"]),
    (r"cellulose degradation|cellulase", ["cellulose"]),
    (r"chitin degradation|chitinase", ["chitin"]),
    (r"xylan degradation|xylanase", ["xylan"]),
    (r"pectin degradation|pectinase", ["pectin"]),
    # Amino acids as carbon sources
    (r"L-alanine degradation", ["alanine"]),
    (r"L-aspartate degradation", ["aspartate"]),
    (r"L-glutamate degradation", ["glutamate"]),
    (r"L-glutamine degradation", ["glutamine"]),
    (r"L-serine degradation", ["serine"]),
    (r"L-cysteine degradation", ["cysteine"]),
    # Inorganic carbon
    (r"methanogenesis|autotrophic.*CO2.*fixation|Calvin", ["CO2"]),
    (r"acetogenesis|Wood-Ljungdahl", ["CO2"]),
]

# Map compound names from media recipes → canonical carbon-source names
MEDIUM_COMPOUND_TO_CARBON = {
    "glucose":     ["glucose"],
    "d(+)-glucose": ["glucose"],
    "dextrose":    ["glucose"],
    "fructose":    ["fructose"],
    "galactose":   ["galactose"],
    "lactose":     ["lactose"],
    "maltose":     ["maltose"],
    "sucrose":     ["sucrose"],
    "trehalose":   ["trehalose"],
    "mannose":     ["mannose"],
    "xylose":      ["xylose"],
    "arabinose":   ["arabinose"],
    "rhamnose":    ["rhamnose"],
    "ribose":      ["ribose"],
    "glycerol":    ["glycerol"],
    "starch":      ["starch"],
    "cellobiose":  ["cellobiose"],
    "acetate":     ["acetate"],
    "na-acetate":  ["acetate"],
    "sodium acetate": ["acetate"],
    "lactate":     ["lactate"],
    "na-dl-lactate": ["lactate"],
    "na-lactate":  ["lactate"],
    "sodium lactate": ["lactate"],
    "dl-lactate":  ["lactate"],
    "pyruvate":    ["pyruvate"],
    "sodium pyruvate": ["pyruvate"],
    "na-pyruvate": ["pyruvate"],
    "formate":     ["formate"],
    "sodium formate": ["formate"],
    "citrate":     ["citrate"],
    "na-citrate":  ["citrate"],
    "succinate":   ["succinate"],
    "fumarate":    ["fumarate"],
    "malate":      ["malate"],
    "ethanol":     ["ethanol"],
    "methanol":    ["methanol"],
    "benzoate":    ["benzoate"],
    "propionate":  ["propionate"],
    "butyrate":    ["butyrate"],
}


def get_carbon_profile(conn: sqlite3.Connection, genome_id: int
                       ) -> Dict[str, dict]:
    """Extract the set of usable carbon sources from gapseq pathway predictions.

    Returns {carbon_source: {"pathways": [...], "max_completeness": float,
                              "confidence": ConfidenceScore}}.
    """
    rows = conn.execute("""
        SELECT pathway_name, completeness, predicted
          FROM genome_pathways
         WHERE genome_id = ?
           AND (predicted = 1 OR completeness >= 75)
    """, (genome_id,)).fetchall()

    profile: Dict[str, dict] = {}
    for pwy_name, comp, pred in rows:
        for pattern, carbons in PATHWAY_TO_CARBON:
            if re.search(pattern, pwy_name, re.IGNORECASE):
                for c in carbons:
                    if c not in profile:
                        profile[c] = {"pathways": [], "max_completeness": 0}
                    profile[c]["pathways"].append(pwy_name)
                    profile[c]["max_completeness"] = max(
                        profile[c]["max_completeness"], comp)
                break

    # Add confidence scores
    for c, info in profile.items():
        comp = info["max_completeness"]
        info["confidence"] = confidence.score(
            "gapseq", "pathway_completeness", comp,
            context={"predicted": True, "carbon_source": c},
        )
    return profile


def verify_carbon_source(conn: sqlite3.Connection, genome_id: int,
                         compound_name: str
                         ) -> Tuple[bool, str]:
    """Check if a medium compound is a carbon source the organism can use.

    Returns (compatible, explanation).
    """
    profile = get_carbon_profile(conn, genome_id)
    lo = compound_name.lower()

    # Map compound name to canonical carbon source(s)
    matches = None
    for pat, carbons in MEDIUM_COMPOUND_TO_CARBON.items():
        if pat in lo:
            matches = carbons
            break

    if matches is None:
        return True, f"'{compound_name}' not recognized as a carbon source"

    for carbon in matches:
        if carbon in profile:
            pwy = profile[carbon]["pathways"][0]
            return True, (f"organism can use {carbon} — predicted via "
                          f"'{pwy}' ({profile[carbon]['max_completeness']:.0f}%)")

    return False, (f"organism has NO predicted pathway for {matches[0]} "
                   f"degradation/utilization — this carbon source may not "
                   f"support growth")


# ---------------------------------------------------------------- gas phase

# Map gapseq pathway patterns → hydrogenase capabilities
H2_PATHWAY_PATTERNS = [
    (r"hydrogen oxidation", "uptake",
     "[NiFe] uptake hydrogenase — organism can oxidize H₂ as electron donor"),
    (r"hydrogen to fumarate", "uptake",
     "periplasmic hydrogenase — couples H₂ to fumarate reduction"),
    (r"hydrogen production", "production",
     "[FeFe] fermentative hydrogenase — organism produces H₂"),
    (r"dissimilatory sulfate reduction", "sulfate_reducer",
     "sulfate reducer — classic H₂-consuming metabolism"),
    (r"methanogenesis", "methanogen",
     "methanogen — likely requires H₂:CO₂ headspace for autotrophic growth"),
]


def get_gas_phase_recommendation(conn: sqlite3.Connection, genome_id: int,
                                 genomespot_oxygen: Optional[str] = None
                                 ) -> dict:
    """Recommend headspace gas composition based on BLAST-confirmed hydrogenases
    (genome_hydrogenases table) + gapseq H₂ pathways + GenomeSPOT oxygen.

    Returns {"headspace": str, "rationale": str, "confidence": ConfidenceScore,
             "h2_capabilities": list, "hydrogenase_blast": list, "is_anaerobe": bool}.
    """
    # BLAST-confirmed hydrogenases (preferred, higher confidence).
    # Graceful fallback: table may not exist if hydrogenase BLAST hasn't run.
    hydrogenase_blast = []
    try:
        blast_hits = conn.execute("""
            SELECT hydrogenase_type, group_id, gene_id, pident, bitscore, confidence
              FROM genome_hydrogenases
             WHERE genome_id = ? AND bitscore >= 100
          ORDER BY bitscore DESC
        """, (genome_id,)).fetchall()
        hydrogenase_blast = [
            {"type": r[0], "group": r[1], "gene": r[2],
             "pident": r[3], "bitscore": r[4], "confidence": r[5]}
            for r in blast_hits
        ]
    except sqlite3.OperationalError:
        pass  # table doesn't exist yet — fall back to gapseq-only

    # gapseq pathway-based (fallback / supplementary)
    rows = conn.execute("""
        SELECT pathway_name, completeness, predicted FROM genome_pathways
        WHERE genome_id = ?
          AND (predicted = 1 OR completeness >= 75)
          AND (lower(pathway_name) LIKE '%hydrogen%'
            OR lower(pathway_name) LIKE '%sulfate reduction%'
            OR lower(pathway_name) LIKE '%methanogen%')
    """, (genome_id,)).fetchall()

    capabilities = []
    for pwy_name, comp, pred in rows:
        for pattern, cap_type, desc in H2_PATHWAY_PATTERNS:
            if re.search(pattern, pwy_name, re.IGNORECASE):
                capabilities.append({
                    "type": cap_type, "pathway": pwy_name,
                    "completeness": comp, "description": desc,
                })
                break

    # Check GenomeSPOT oxygen prediction from DB
    if genomespot_oxygen is None:
        row = conn.execute("""
            SELECT value FROM genome_growth_predictions
            WHERE genome_id = ? AND target = 'oxygen'
        """, (genome_id,)).fetchone()
        if row:
            genomespot_oxygen = row[0]

    is_anaerobe = (genomespot_oxygen and
                   "not tolerant" in str(genomespot_oxygen).lower())

    # Use BLAST hits for classification when available
    blast_types = {h["type"] + "_G" + h["group"] for h in hydrogenase_blast}

    # Merge evidence: BLAST-confirmed types take precedence
    has_nife_g1 = any("[NiFe]_G1" in t for t in blast_types)
    has_nife_g3 = any("[NiFe]_G3" in t for t in blast_types)
    has_nife_g4 = any("[NiFe]_G4" in t for t in blast_types)
    has_fefe_ga = any("[FeFe]_GA" in t for t in blast_types)

    has_uptake = (has_nife_g1 or
                  any(c["type"] == "uptake" for c in capabilities))
    has_production = (has_fefe_ga or
                      any(c["type"] == "production" for c in capabilities))
    is_srb = any(c["type"] == "sulfate_reducer" for c in capabilities)
    # [NiFe] Group 3 (F420-reducing) is diagnostic for methanogens even
    # without gapseq pathway confirmation — gapseq often underestimates
    # methanogenesis pathway completeness for archaea.
    is_methanogen = (has_nife_g3 or
                     any(c["type"] == "methanogen" for c in capabilities))

    # Decision logic per CLAUDE.md addendum 4
    if is_methanogen:
        headspace = "H₂:CO₂ (80:20) at 1-2 bar overpressure"
        rationale = "hydrogenotrophic methanogen — requires H₂ as electron donor"
        conf_val = 0.90
    elif is_srb and has_uptake:
        headspace = "N₂:CO₂ (80:20) — OR H₂:CO₂ (80:20) if testing lithoautotrophic growth"
        rationale = ("sulfate reducer with uptake hydrogenase — can use H₂ or "
                     "organic donors; N₂:CO₂ is standard for heterotrophic growth "
                     "with lactate/pyruvate; H₂:CO₂ enables autotrophic growth")
        conf_val = 0.85
    elif has_uptake and is_anaerobe:
        headspace = "H₂:CO₂ (80:20)"
        rationale = "anaerobe with uptake hydrogenase — can use H₂ as electron donor"
        conf_val = 0.85
    elif has_production and not has_uptake and is_anaerobe:
        headspace = "N₂:CO₂ (80:20) — do NOT add H₂ (inhibits H₂-producing fermentation)"
        rationale = ("fermentative H₂ producer — adding H₂ would make "
                     "fermentation thermodynamically unfavorable")
        conf_val = 0.80
    elif is_anaerobe:
        headspace = "N₂:CO₂ (80:20) or 100% N₂"
        rationale = "strict anaerobe — no H₂-specific metabolism detected"
        conf_val = 0.75
    else:
        headspace = "Aerobic (air) — no special headspace needed"
        rationale = "no anaerobic or H₂-dependent metabolism detected"
        conf_val = 0.85

    return {
        "headspace": headspace,
        "rationale": rationale,
        "confidence": confidence.ConfidenceScore(
            value=conf_val, source="gapseq",
            rationale=rationale,
        ),
        "h2_capabilities": capabilities,
        "hydrogenase_blast": hydrogenase_blast,
        "is_anaerobe": is_anaerobe,
    }
