"""De Novo Media Synthesizer — build recipes from genomic evidence, not templates.

Per DENOVO_DESIGN.md: instead of copying a phylogenetic relative's medium,
this module constructs a recipe from first principles:

  1. Gather all genomic evidence (gapseq, GenomeSPOT, MeBiPred)
  2. Determine energy metabolism (decision tree)
  3. Select carbon, nitrogen, sulfur, phosphate/buffer sources
  4. Add vitamins, trace metals, base salts, reducing agent, atmosphere
  5. Calibrate concentrations from MediaDive (metabolism-specific medians)
  6. Compatibility check + thermodynamic viability
  7. Physical format prediction

Template comparison (--compare-template) runs rank_candidate_media() and
shows the top-1 result side-by-side.

Usage:
    python synthesize_denovo.py <genome.fasta> --accession ACC [options]

Options:
    --accession ACC          genome accession for DB lookup (required)
    --temperature T          override growth temperature (°C)
    --ph P                   override pH
    --energy-metabolism NAME e.g. sulfate-reduction, methanogenesis
    --compare-template       add side-by-side template comparison
    --no-persist             dry run, do not write to DB
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import confidence
import thermodynamics as td
from carbon_and_gas import get_carbon_profile, get_gas_phase_recommendation
from compatibility import (
    check_compatibility, generate_prep_instructions,
    confidence_penalty, format_warnings,
)
from media_constants import (
    METAL_SUPPLEMENT, COFACTOR_CONCENTRATION, AA_SUPPLEMENT_CONC,
    AUTOTROPHY_PATTERNS, METABOLISM_TAXONOMY_PROXIES, REDUCING_AGENTS,
    BUFFER_BY_PH, PREFERRED_CARBON_BY_METABOLISM,
)
from media_format import predict_format
from phylo_match import (
    DB, BLAST_DB, run_blast, infer_thermal_multisource, rank_candidate_media,
    classify_temp, COMPLEX_AMINO_ACID_SOURCES, COMPLEX_VITAMIN_SOURCES,
)
from predict_media import (
    extract_16s, get_genome_id_for_accession,
    get_auxotrophies, get_transporter_summary, get_metal_profile,
)
from synthesize_media import (
    Component, classify_role, compose_overall_confidence,
    build_variation_matrix, check_thermodynamic_viability, THERMO_VIABILITY_MAP,
    SCHEMA_SQL as SM_SCHEMA_SQL,
)


# ---------------------------------------------------------------- constants

YEAST_EXTRACT_AUXO_THRESHOLD = 5   # Approved addition #2: if >5 auxotrophies, add YE
COMPLEX_NITROGEN_AA_THRESHOLD = 10  # if >10 amino acid auxotrophies, offer peptone option

# Autotrophy score thresholds (Concern 1 — session 18b).
# Replaces the hard AUTOTROPHY_COMPATIBLE_TYPES gate with a multi-evidence
# scoring system that does not depend on energy metabolism classification.
AUTOTROPHY_SCORE_HIGH = 0.50     # → assign NaHCO3 (converging evidence)
AUTOTROPHY_SCORE_LOW  = 0.20     # → assign organic carbon (clear heterotroph)
# Between LOW and HIGH → present both options with evidence

# Na+ cycling transporter TC families for marine salinity detection (Fix 4).
# These are specific Na+/H+ antiporter and Na+-coupled energy families —
# NOT generic Na+-coupled symporters (which are universal).
NA_CYCLING_TC_FAMILIES = [
    "2.A.36",   # monovalent cation/proton antiporter (CPA1): nhaA, nhaB, nhaN
    "2.A.63",   # multisubunit Na+/H+ antiporter (Mrp/Mnh)
    "3.D.5",    # Na+-translocating NADH:quinone oxidoreductase (Nqr)
]

# Halophile marker pathways for base-salt calibration.
# Only ectoine is used — glycine betaine biosynthesis is a general-purpose
# osmolyte present in many non-halophilic organisms (e.g. Lactobacillus
# plantarum has 100% complete betaine II pathway but grows at 0-1% NaCl).
HALOPHILE_MARKERS = [
    (r"ectoine biosynthesis", "moderate halophile"),
]

# Outer-membrane cytochrome / iron-reducer marker pathways
IRON_REDUCER_MARKERS = [
    r"outer.membrane cytochrome",
    r"mtr[ABC]|omcA|omcB|omcS|omcZ",
    r"iron.reduc",
    r"dissimilatory iron reduction",
]

# Autotroph carbon source result
CO2_FIXATION_SOURCES = {"CO2", "co2"}


# ---------------------------------------------------------------- evidence container

@dataclass
class Evidence:
    """All genomic evidence gathered for one genome."""
    genome_id: int
    accession: str
    # GenomeSPOT predictions
    temperature_opt: Optional[float] = None
    ph_opt: Optional[float] = None
    salinity_pct: Optional[float] = None
    oxygen_prediction: Optional[str] = None
    # Pathway-level data
    pathways: List[dict] = field(default_factory=list)       # {name, completeness, predicted}
    carbon_profile: Dict = field(default_factory=dict)       # {substrate: info}
    # Hydrogenases
    hydrogenases: List[dict] = field(default_factory=list)   # {type, group, gene, ...}
    # Transporters
    transporters: List[Tuple] = field(default_factory=list)  # (substrate, count)
    # Auxotrophies
    auxotrophies: List[dict] = field(default_factory=list)   # {name, class, best_completeness}
    # Metal profile
    metal_profile: List[dict] = field(default_factory=list)  # from genome_metal_profile
    # Reaction markers (terminal oxidases, catalase, hao, amo)
    reaction_markers: Dict[str, dict] = field(default_factory=dict)
    # User overrides (applied after evidence gathering)
    user_temperature: Optional[float] = None
    user_ph: Optional[float] = None
    user_energy_metabolism: Optional[str] = None

    @property
    def effective_temperature(self) -> Optional[float]:
        return self.user_temperature or self.temperature_opt

    @property
    def effective_ph(self) -> Optional[float]:
        return self.user_ph or self.ph_opt or 7.0

    @property
    def is_anaerobe(self) -> bool:
        return bool(self.oxygen_prediction and
                    "not tolerant" in self.oxygen_prediction.lower())


# ---------------------------------------------------------------- evidence gathering

def gather_evidence(conn: sqlite3.Connection, genome_id: int,
                    accession: str = "") -> Evidence:
    """Collect all genomic data for genome_id into a single Evidence object."""
    ev = Evidence(genome_id=genome_id, accession=accession)

    # GenomeSPOT growth predictions
    rows = conn.execute("""
        SELECT target, value, numeric_value
          FROM genome_growth_predictions
         WHERE genome_id = ?
    """, (genome_id,)).fetchall()
    for target, value, num in rows:
        t = target.lower()
        if "temperature" in t and "optimum" in t and num:
            ev.temperature_opt = num
        elif "ph" in t and "optimum" in t and num:
            ev.ph_opt = num
        elif "salinity" in t and num:
            ev.salinity_pct = num
        elif "oxygen" in t and value:
            ev.oxygen_prediction = value

    # gapseq pathways (all complete enough to be relevant)
    ev.pathways = [
        {"name": r[0], "completeness": r[1], "predicted": bool(r[2])}
        for r in conn.execute("""
            SELECT pathway_name, completeness, predicted
              FROM genome_pathways
             WHERE genome_id = ?
        """, (genome_id,)).fetchall()
    ]

    # Carbon profile (reuse carbon_and_gas)
    try:
        ev.carbon_profile = get_carbon_profile(conn, genome_id)
    except Exception:
        ev.carbon_profile = {}

    # BLAST-confirmed hydrogenases
    try:
        ev.hydrogenases = [
            {"type": r[0], "group": r[1], "gene": r[2],
             "pident": r[3], "bitscore": r[4], "confidence": r[5]}
            for r in conn.execute("""
                SELECT hydrogenase_type, group_id, gene_id, pident, bitscore, confidence
                  FROM genome_hydrogenases
                 WHERE genome_id = ? AND bitscore >= 100
              ORDER BY bitscore DESC
            """, (genome_id,)).fetchall()
        ]
    except sqlite3.OperationalError:
        ev.hydrogenases = []

    # Transporters
    ev.transporters = get_transporter_summary(conn, genome_id, top_n=20)

    # Auxotrophies
    ev.auxotrophies = get_auxotrophies(conn, genome_id)

    # Metal profile
    ev.metal_profile = get_metal_profile(conn, genome_id)

    # Reaction markers (terminal oxidases, catalase, hao, amo)
    try:
        for row in conn.execute("""
            SELECT marker, n_good_blast, best_bitscore, complex_complete
              FROM genome_reaction_markers
             WHERE genome_id = ?
        """, (genome_id,)).fetchall():
            ev.reaction_markers[row[0]] = {
                "n_good_blast": row[1],
                "best_bitscore": row[2],
                "complex_complete": bool(row[3]),
            }
    except sqlite3.OperationalError:
        ev.reaction_markers = {}

    return ev


# ---------------------------------------------------------------- helpers

def _pathway_matches(pathways: List[dict], pattern: str,
                     min_completeness: float = 50.0) -> List[dict]:
    """Return pathways matching the regex pattern at >= min_completeness or predicted."""
    rx = re.compile(pattern, re.IGNORECASE)
    return [p for p in pathways if rx.search(p["name"])
            and (p["predicted"] or p["completeness"] >= min_completeness)]


def _best_completeness(pathways: List[dict], pattern: str) -> float:
    """Max completeness across matching pathways; 0 if none."""
    matches = _pathway_matches(pathways, pattern, min_completeness=0)
    return max((p["completeness"] for p in matches), default=0.0)


def _marker_good_blast(evidence: 'Evidence', marker: str) -> int:
    """Return the number of good_blast hits for a reaction marker, or 0."""
    m = evidence.reaction_markers.get(marker)
    return m["n_good_blast"] if m else 0


def _marker_complex_complete(evidence: 'Evidence', marker: str) -> bool:
    """Return whether a reaction marker's complex is complete."""
    m = evidence.reaction_markers.get(marker)
    return m["complex_complete"] if m else False


def _has_autotrophy(pathways: List[dict]) -> Tuple[bool, str, float]:
    """Return (is_autotroph, cycle_name, completeness).

    Threshold at 80% — partial Calvin cycle genes (69-76%) are common in
    heterotrophs from pentose phosphate pathway overlap.
    """
    for rx, name in AUTOTROPHY_PATTERNS:
        matches = _pathway_matches(pathways, rx, min_completeness=80)
        if matches:
            comp = max(p["completeness"] for p in matches)
            return True, name, comp
    return False, "", 0.0


def _score_autotrophy(evidence: 'Evidence') -> Tuple[float, str, List[str]]:
    """Multi-evidence autotrophy scoring (Concern 1 — session 18b).

    Scores from 0.0 (definitely heterotrophic) to 1.0 (definitely autotrophic)
    using MULTIPLE independent lines of evidence.  Does NOT reference the energy
    metabolism classification — this is an independent assessment so that a
    misclassified metabolism cannot drag the carbon source down with it.

    Lines of evidence scored:
      (+) CO₂ fixation pathway completeness (Calvin, rTCA, WL, 3-HP, DC/4-HB)
      (+) Very few organic carbon utilization pathways (≤5 at ≥80%)
      (−) Many organic carbon utilization pathways (≥15 at ≥80%)
      (−) Many sugar transport systems

    Returns (score, best_cycle_name, evidence_list).
    """
    pwys = evidence.pathways
    score = 0.0
    reasons: List[str] = []

    # --- Positive signals: CO₂ fixation pathways ---
    best_cycle = ""
    best_comp = 0.0
    for rx, name in AUTOTROPHY_PATTERNS:
        comp = _best_completeness(pwys, rx)
        if comp > best_comp:
            best_comp = comp
            best_cycle = name

    if best_comp >= 90:
        # Near-complete CO₂ fixation cycle — strong autotroph signal.
        # At ≥90% the pathway is almost certainly real, not just shared
        # enzymes from pentose phosphate / gluconeogenesis overlap.
        score += 0.65
        reasons.append(f"{best_cycle} {best_comp:.0f}% complete — strong autotrophy signal")
    elif best_comp >= 80:
        # Moderate — could be real autotrophy OR enzyme overlap.
        # Needs corroboration from low organic carbon breadth.
        score += 0.30
        reasons.append(f"{best_cycle} {best_comp:.0f}% complete — moderate (check organic C breadth)")
    elif best_comp >= 60:
        # Weak — likely pentose phosphate / gluconeogenesis overlap.
        score += 0.05
        reasons.append(f"{best_cycle} {best_comp:.0f}% — partial genes, likely PP pathway overlap")

    # --- Negative signals: organic carbon utilization breadth ---
    # Count substrates with ≥80% pathway completeness in the carbon profile.
    # True autotrophs have few (Methanococcus: 3); heterotrophs have many
    # (Lactobacillus: 25).  Acidithiobacillus has 12 due to shared enzymes,
    # so the penalty must not be too aggressive below 15.
    n_organic_high = sum(1 for v in evidence.carbon_profile.values()
                         if v["max_completeness"] >= 80)

    if n_organic_high >= 15:
        score -= 0.25
        reasons.append(f"{n_organic_high} organic substrates at ≥80% — strong heterotroph signal")
    elif n_organic_high >= 10:
        score -= 0.10
        reasons.append(f"{n_organic_high} organic substrates at ≥80% — moderate heterotroph signal")
    elif n_organic_high <= 5:
        score += 0.10
        reasons.append(f"{n_organic_high} organic substrates at ≥80% — few, consistent with autotrophy")

    # --- Sugar transporter density as a heterotrophy marker ---
    # Many sugar-specific transporters suggest active sugar catabolism.
    # We count only transporters whose substrate explicitly names a sugar.
    sugar_keywords = {"glucose", "fructose", "sucrose", "maltose", "mannose",
                      "galactose", "xylose", "lactose", "cellobiose", "trehalose"}
    sugar_trans = sum(
        cnt for sub, cnt in evidence.transporters
        if sub and any(kw in sub.lower() for kw in sugar_keywords)
        and isinstance(cnt, int)
    )
    if sugar_trans >= 30:
        score -= 0.15
        reasons.append(f"{sugar_trans} sugar-specific transporters — active sugar catabolism")
    elif sugar_trans <= 5:
        score += 0.05
        reasons.append(f"{sugar_trans} sugar-specific transporters — few, consistent with autotrophy")

    score = max(0.0, min(1.0, score))
    return score, best_cycle, reasons


# ---------------------------------------------------------------- energy metabolism

@dataclass
class EnergyMetabolism:
    type: str               # e.g. "sulfate_reducer"
    electron_donor: str
    electron_acceptor: str
    is_autotrophic: bool
    genomic_evidence: List[str]
    confidence: confidence.ConfidenceScore


def determine_energy_metabolism(conn, evidence, user_override=None):
    """DEPRECATED Phase 2c: replaced by compose_recipe.compose_recipe().

    The original sequential-decision-tree implementation (~320 lines) was
    deleted as of Phase 2c. The new pipeline reads a RecipeContext
    (Phase 2b) and produces a Recipe object via compose_recipe.py with
    biology-aware mode routing, sub-mode classification, thermodynamic
    gating, and LIMITATIONS.md flagging.

    Callers should migrate to:
        from compose_recipe import compose_recipe
        recipe = compose_recipe(genome_id, conn)

    This stub raises NotImplementedError to surface the migration.
    """
    raise NotImplementedError(
        "determine_energy_metabolism() was deleted in Phase 2c. "
        "Use compose_recipe.compose_recipe(genome_id, conn) instead."
    )


def _donor_for_type(met_type: str) -> str:
    return {
        "methanogen":       "H2(aq)",
        "sulfate_reducer":  "organic acids (lactate/pyruvate/acetate) or H2",
        "iron_reducer":     "acetate or organic acids",
        "sulfur_oxidizer":  "H2S / S⁰ / thiosulfate",
        "ammonia_oxidizer": "NH4⁺",
        "denitrifier":      "organic compounds",
        "aerobic_heterotroph": "organic carbon",
        "fermenter":        "organic carbon",
        "hydrogen_oxidizer": "H2(aq)",
    }.get(met_type, "unknown")


def _acceptor_for_type(met_type: str) -> str:
    return {
        "methanogen":       "CO2",
        "sulfate_reducer":  "SO4²⁻",
        "iron_reducer":     "Fe(III)",
        "sulfur_oxidizer":  "O2 or NO3⁻",
        "ammonia_oxidizer": "O2",
        "denitrifier":      "NO3⁻",
        "aerobic_heterotroph": "O2",
        "fermenter":        "organic (internal)",
        "hydrogen_oxidizer": "O2",
    }.get(met_type, "unknown")


# ---------------------------------------------------------------- calibration engine

# Functional media composition signatures (Concern 2 — session 18b).
# Instead of searching by taxonomy (organism name LIKE "%desulfo%"), identify
# media by their composition pattern.  This works for novel organisms whose
# names don't match any known genus.
FUNCTIONAL_MEDIA_SIGNATURES = {
    "sulfate_reducer": {
        "must_contain":  ["%sulfate%", "%so4%"],
        "should_contain": ["%lactate%", "%pyruvate%", "%acetate%"],
        "description":  "media containing sulfate + organic acid (SRB signature)",
    },
    "methanogen": {
        "must_contain":  ["%nahco3%", "%bicarbonate%"],
        "exclude":       ["%glucose%", "%peptone%", "%tryptone%"],
        "description":  "media with NaHCO3 as sole carbon, no organics (methanogen)",
    },
    "iron_reducer": {
        "must_contain":  ["%ferric%", "%fe(iii)%", "%iron%citrate%"],
        "description":  "media containing Fe(III) as electron acceptor",
    },
    "fermenter": {
        "must_contain":  ["%glucose%"],
        "min_conc":      5.0,  # fermenters need high sugar (≥5 g/L)
        "description":  "media with high glucose (≥5 g/L, fermenter signature)",
    },
    "sulfur_oxidizer": {
        "must_contain":  ["%thiosulfate%", "%nahco3%"],
        "description":  "media with thiosulfate + NaHCO3 (autotrophic S-oxidizer)",
    },
}


def calibrate_concentration(conn: sqlite3.Connection,
                             compound_pattern: str,
                             metabolism_type: Optional[str] = None,
                             fallback_conc: Optional[float] = None,
                             ) -> Tuple[float, float, float, int, str]:
    """Query MediaDive for median concentration of a compound.

    Concern 2 (session 18b): three-level lookup.
      Level 1: functional composition query — find media by what they CONTAIN,
               not by who they were designed for.  E.g. SRB media = media that
               contain both sulfate and an organic acid electron donor.
      Level 2: taxonomy proxy (fallback if functional query returns <10 results).
      Level 3: global median across all media.

    Returns (median, p10, p90, n_data_points, source_level).
    """
    def _basic_query(extra_where: str = "", params=()):
        sql = """
            SELECT mc.g_per_L
              FROM media_compounds mc
              JOIN compounds c ON c.id = mc.compound_id
             WHERE lower(c.name) LIKE ?
               AND mc.g_per_L > 0
        """ + extra_where
        all_params = [f"%{compound_pattern.lower()}%"] + list(params)
        rows = conn.execute(sql, all_params).fetchall()
        return [r[0] for r in rows if r[0] is not None]

    def _stats(values):
        if not values:
            return None
        values.sort()
        n = len(values)
        median = statistics.median(values)
        p10 = values[max(0, int(0.10 * n) - 1)]
        p90 = values[min(n - 1, int(0.90 * n))]
        return median, p10, p90, n

    # Level 1: functional composition signature
    sig = FUNCTIONAL_MEDIA_SIGNATURES.get(metabolism_type)
    values = []
    source_level = ""
    if sig:
        # Find media IDs that contain ALL must_contain compounds
        must = sig.get("must_contain", [])
        if must:
            # Build a query: media that contain ALL required signature compounds
            media_id_sql = """
                SELECT mc.media_id
                  FROM media_compounds mc
                  JOIN compounds c ON c.id = mc.compound_id
                 WHERE ({like_clauses})
                   AND mc.g_per_L > 0
                 GROUP BY mc.media_id
                HAVING COUNT(DISTINCT CASE WHEN {case_clauses} END) >= ?
            """
            like_parts = " OR ".join(f"lower(c.name) LIKE ?" for _ in must)
            case_parts = " ".join(
                f"WHEN lower(c.name) LIKE ? THEN {i}" for i, _ in enumerate(must)
            )
            media_id_sql = media_id_sql.format(like_clauses=like_parts,
                                                case_clauses=case_parts)
            try:
                mid_params = list(must) + list(must) + [len(must)]
                media_ids = [r[0] for r in conn.execute(media_id_sql, mid_params).fetchall()]
                if media_ids:
                    placeholders = ",".join("?" * len(media_ids))
                    min_conc = sig.get("min_conc", 0)
                    conc_sql = f"""
                        SELECT mc.g_per_L
                          FROM media_compounds mc
                          JOIN compounds c ON c.id = mc.compound_id
                         WHERE mc.media_id IN ({placeholders})
                           AND lower(c.name) LIKE ?
                           AND mc.g_per_L > {min_conc}
                    """
                    rows = conn.execute(
                        conc_sql,
                        media_ids + [f"%{compound_pattern.lower()}%"]
                    ).fetchall()
                    values = [r[0] for r in rows if r[0] is not None]
                    source_level = f"functional:{metabolism_type}"
            except (sqlite3.OperationalError, Exception):
                values = []

    # Level 2: taxonomy proxy (fallback)
    if len(values) < 10:
        proxies = METABOLISM_TAXONOMY_PROXIES.get(metabolism_type) if metabolism_type else None
        if proxies:
            join_sql = """
                  JOIN organism_media om ON om.media_id = mc.media_id
                  JOIN organisms o ON o.id = om.organism_id
                 WHERE lower(c.name) LIKE ?
                   AND mc.g_per_L > 0
                   AND om.growth = 1
                   AND ("""
            like_clauses = " OR ".join(f"lower(o.species) LIKE ?" for _ in proxies)
            full_sql = f"""
                SELECT mc.g_per_L
                  FROM media_compounds mc
                  JOIN compounds c ON c.id = mc.compound_id
                {join_sql}{like_clauses})
            """
            try:
                rows = conn.execute(full_sql,
                                    [f"%{compound_pattern.lower()}%"] + list(proxies)).fetchall()
                tax_values = [r[0] for r in rows if r[0] is not None]
                if len(tax_values) > len(values):
                    values = tax_values
                    source_level = f"taxonomy_proxy:{metabolism_type}"
            except sqlite3.OperationalError:
                pass

    # Level 3: global median
    if len(values) < 5:
        values = _basic_query()
        source_level = "global_median"

    if len(values) < 5 and fallback_conc is not None:
        return fallback_conc, fallback_conc, fallback_conc, 0, "fallback_constant"

    s = _stats(values)
    if s is None:
        if fallback_conc is not None:
            return fallback_conc, fallback_conc, fallback_conc, 0, "fallback_constant"
        return 1.0, 0.1, 5.0, 0, "default_guess"

    return s[0], s[1], s[2], s[3], source_level


# ---------------------------------------------------------------- determine_* functions

def _select_organic_carbon(conn: sqlite3.Connection,
                           evidence: 'Evidence',
                           energy: EnergyMetabolism,
                           ) -> List[Component]:
    """Select the best organic carbon source for a heterotrophic recipe.

    Ranking: metabolism-preferred substrate → gapseq carbon profile
    by (completeness × simplicity) → glucose default.
    """
    pref = PREFERRED_CARBON_BY_METABOLISM.get(energy.type, [])
    profile = evidence.carbon_profile

    selected = []
    # First: use preferred substrates if genome supports them
    for preferred in pref:
        if preferred.upper() == "CO2":
            continue
        if preferred in profile:
            selected.append((preferred, profile[preferred]["max_completeness"]))
            break

    # If none from preferences, fall back to best-scoring substrate
    if not selected and profile:
        _simplicity = {"glucose": 10, "fructose": 9, "sucrose": 8,
                       "lactate": 7, "pyruvate": 7, "acetate": 6,
                       "succinate": 6, "maltose": 5, "glycerol": 5}
        candidates = sorted(
            profile.items(),
            key=lambda kv: (kv[1]["max_completeness"],
                            _simplicity.get(kv[0], 0)),
            reverse=True,
        )
        selected.append((candidates[0][0], candidates[0][1]["max_completeness"]))

    if not selected:
        selected = [("glucose", 75.0)]

    components = []
    for substrate, comp_pct in selected:
        compound_name = _canonical_compound(substrate)
        med, p10, p90, n, src = calibrate_concentration(
            conn, substrate, energy.type, fallback_conc=2.0)
        conf = confidence.score("gapseq", "pathway_completeness",
                                comp_pct, {"predicted": comp_pct >= 75,
                                           "carbon_source": substrate})
        components.append(Component(
            name=compound_name,
            compound_name=compound_name,
            concentration=round(med, 2),
            units="g/L",
            role="carbon_source",
            confidence_obj=confidence.ConfidenceScore(
                value=conf.value, source="gapseq",
                rationale=(f"genome encodes {substrate} utilization "
                           f"({comp_pct:.0f}% pathway completeness); "
                           f"calibrated: median={med:.2f} g/L (n={n}, {src}); "
                           f"preferred for {energy.type}"),
            ),
            source_tag="gapseq",
        ))
    return components


def determine_carbon_source(conn: sqlite3.Connection,
                            evidence: Evidence,
                            energy: EnergyMetabolism,
                            ) -> List[Component]:
    """Select carbon source(s) using multi-evidence autotrophy scoring.

    Concern 1 (session 18b): replaces the hard metabolism-type gate with
    an independent scoring system.  The autotrophy score is computed from
    CO₂ fixation pathway completeness, organic carbon utilization breadth,
    and sugar transporter density — WITHOUT referencing the energy metabolism
    classification.  A user override (energy.is_autotrophic from --energy-
    metabolism) is treated as one strong positive signal, not a hard gate.

    Score ≥ AUTOTROPHY_SCORE_HIGH → NaHCO₃ (converging evidence)
    Score < AUTOTROPHY_SCORE_LOW  → organic carbon (clear heterotroph)
    Between → present BOTH options with evidence for user decision
    """
    auto_score, cycle_name, auto_reasons = _score_autotrophy(evidence)

    # User-specified autotrophic metabolism is a strong positive signal.
    # The bonus is large enough (+0.45) to push even a low genomic score
    # above the HIGH threshold when the user explicitly asserts autotrophy
    # (e.g. --energy-metabolism methanogenesis).  However, it cannot force
    # NaHCO₃ when genomic evidence STRONGLY contradicts (score capped at 1.0,
    # and a heterotroph with 25 substrates + 200 sugar transporters would
    # have a base score of -0.35, resulting in 0.10 after the bonus — still
    # below the threshold).
    if energy.is_autotrophic:
        auto_score = min(1.0, auto_score + 0.45)
        auto_reasons.append(f"energy metabolism ({energy.type}) is autotrophic (+0.45)")

    # --- Decision ---
    if auto_score >= AUTOTROPHY_SCORE_HIGH:
        # Strong autotrophy signal → NaHCO3 as sole carbon source
        med, p10, p90, n, src = calibrate_concentration(
            conn, "nahco3", energy.type, fallback_conc=2.5)
        conf_val = min(0.90, 0.60 + auto_score * 0.30)
        return [Component(
            name="NaHCO3 (CO2 source / buffer)",
            compound_name="NaHCO3",
            concentration=round(med, 2),
            units="g/L",
            role="carbon_source",
            confidence_obj=confidence.ConfidenceScore(
                value=round(conf_val, 2), source="gapseq",
                rationale=(f"autotrophy score {auto_score:.2f} ≥ {AUTOTROPHY_SCORE_HIGH} — "
                           f"{'; '.join(auto_reasons)}; "
                           f"calibrated: median={med:.2f} g/L (n={n}, {src})"),
            ),
            source_tag="autotrophy",
        )]

    if auto_score < AUTOTROPHY_SCORE_LOW:
        # Clear heterotroph → organic carbon only
        return _select_organic_carbon(conn, evidence, energy)

    # --- Ambiguous: present both options ---
    components = []

    # Option A: organic carbon (primary recommendation)
    organic = _select_organic_carbon(conn, evidence, energy)
    for c in organic:
        c.uncertainty_note = (
            f"Autotrophy score {auto_score:.2f} is ambiguous — "
            f"recommend testing both organic carbon and NaHCO₃ (CO₂)")
    components.extend(organic)

    # Option B: NaHCO3 (alternative)
    med, p10, p90, n, src = calibrate_concentration(
        conn, "nahco3", energy.type, fallback_conc=2.5)
    components.append(Component(
        name="NaHCO3 (CO2 source — OPTION B)",
        compound_name="NaHCO3",
        concentration=round(med, 2),
        units="g/L",
        role="carbon_source",
        confidence_obj=confidence.ConfidenceScore(
            value=round(0.40 + auto_score * 0.30, 2), source="gapseq",
            rationale=(f"OPTION B (autotrophic CO₂): {cycle_name} detected; "
                       f"autotrophy score {auto_score:.2f} is ambiguous — "
                       f"{'; '.join(auto_reasons)}; "
                       f"test with NaHCO₃ as sole carbon to confirm"),
        ),
        uncertainty_note=(f"Autotrophy score {auto_score:.2f} is ambiguous "
                          f"({AUTOTROPHY_SCORE_LOW}–{AUTOTROPHY_SCORE_HIGH}). "
                          f"Test OPTION A (organic) and OPTION B (NaHCO₃ only) in parallel."),
        source_tag="autotrophy_ambiguous",
    ))

    return components


def determine_nitrogen_source(conn: sqlite3.Connection,
                              evidence: Evidence,
                              energy: EnergyMetabolism,
                              ) -> List[Component]:
    """Select nitrogen source from genome evidence.

    Fix 2 (session 17): when amino acid auxotrophy count > 10, present
    two options — defined (NH4Cl + individual AAs) for enrichment, and
    complex (peptone + yeast extract) for pure-culture maintenance.
    """
    components = []
    pwys = evidence.pathways

    # Count amino acid auxotrophies specifically
    aa_auxotrophies = [a for a in evidence.auxotrophies
                       if a.get("class") == "amino_acid"]
    n_aa_aux = len(aa_auxotrophies)
    n_aux = len(evidence.auxotrophies)

    # Check N2 fixation
    nif_comp = _best_completeness(pwys, r"nifHDK|nitrogen fixation|nitrogen.*fix")
    has_nitrate_red = _best_completeness(pwys, r"assimilatory nitrate reductase|nasA|narB") >= 50
    has_amtB = any("ammoni" in (sub or "").lower()
                   for sub, _ in evidence.transporters)

    # Primary N source: NH4Cl (always present as inorganic nitrogen base)
    med, p10, p90, n, src = calibrate_concentration(
        conn, "nh4cl", evidence.user_energy_metabolism or energy.type,
        fallback_conc=1.0)
    rationale_parts = []
    if nif_comp >= 50:
        rationale_parts.append(f"N2 fixation genes detected ({nif_comp:.0f}%); NH4Cl still preferred for cultivation")
    if has_amtB:
        rationale_parts.append("ammonium transporter (amtB) detected")
    if has_nitrate_red:
        rationale_parts.append("assimilatory nitrate reductase present (can also use NO3⁻)")
    if not rationale_parts:
        rationale_parts.append("NH4Cl default (universal prokaryotic N source)")

    n_conf = confidence.ConfidenceScore(
        value=0.85 if has_amtB else 0.75,
        source="gapseq",
        rationale="; ".join(rationale_parts) + f"; calibrated median={med:.2f} g/L (n={n})",
    )
    components.append(Component(
        name="NH4Cl",
        compound_name="NH4Cl",
        concentration=round(med, 2),
        units="g/L",
        role="nitrogen_source",
        confidence_obj=n_conf,
        source_tag="gapseq",
    ))

    # Two-option nitrogen strategy for auxotroph-rich organisms
    if n_aa_aux > COMPLEX_NITROGEN_AA_THRESHOLD:
        # Option B: complex nitrogen (peptone + yeast extract)
        # Recommended for pure culture maintenance
        pep_med, _, _, pep_n, pep_src = calibrate_concentration(
            conn, "peptone", energy.type, fallback_conc=5.0)
        ye_med, _, _, ye_n, ye_src = calibrate_concentration(
            conn, "yeast extract", None, fallback_conc=2.0)
        aa_names = ", ".join(a["name"] for a in aa_auxotrophies[:5])
        if n_aa_aux > 5:
            aa_names += f" + {n_aa_aux - 5} more"
        components.append(Component(
            name="Peptone (complex nitrogen — Option B)",
            compound_name="Peptone",
            concentration=round(pep_med, 1),
            units="g/L",
            role="complex_source",
            confidence_obj=confidence.ConfidenceScore(
                value=0.82, source="gapseq",
                rationale=(f"{n_aa_aux} amino acid auxotrophies ({aa_names}); "
                           f"peptone covers all 20 AAs; "
                           f"calibrated: median={pep_med:.1f} g/L (n={pep_n}); "
                           f"OPTION B: for pure culture maintenance — "
                           f"complex nitrogen supports faster growth but also contaminants"),
            ),
            source_tag="auxotrophy",
        ))
        components.append(Component(
            name="Yeast extract",
            compound_name="Yeast extract",
            concentration=round(ye_med, 1),
            units="g/L",
            role="complex_source",
            confidence_obj=confidence.ConfidenceScore(
                value=0.82, source="gapseq",
                rationale=(f"{n_aux} total auxotrophies; "
                           f"yeast extract covers vitamins + amino acids; "
                           f"calibrated: median={ye_med:.1f} g/L (n={ye_n})"),
            ),
            uncertainty_note=(f"OPTION A (defined/selective): use NH4Cl + individual "
                              f"amino acid supplements for {n_aa_aux} auxotrophies — "
                              f"recommended for enrichment and first isolation. "
                              f"OPTION B (complex/practical): use peptone {pep_med:.0f} g/L "
                              f"+ yeast extract {ye_med:.0f} g/L — recommended for "
                              f"pure culture maintenance. WARNING: complex nitrogen "
                              f"supports contaminant growth."),
            source_tag="auxotrophy",
        ))
    elif n_aux > YEAST_EXTRACT_AUXO_THRESHOLD:
        # Moderate auxotrophy: yeast extract covers vitamins + some AAs
        ye_med, _, _, ye_n, ye_src = calibrate_concentration(
            conn, "yeast extract", None, fallback_conc=1.0)
        ye_conf = confidence.ConfidenceScore(
            value=0.80, source="gapseq",
            rationale=(f"{n_aux} auxotrophies detected (>{YEAST_EXTRACT_AUXO_THRESHOLD} threshold); "
                       f"yeast extract covers vitamins + amino acids; "
                       f"calibrated: median={ye_med:.2f} g/L (n={ye_n})"),
        )
        components.append(Component(
            name="Yeast extract",
            compound_name="Yeast extract",
            concentration=round(ye_med, 2),
            units="g/L",
            role="complex_source",
            confidence_obj=ye_conf,
            uncertainty_note=f"{n_aux} auxotrophies; yeast extract covers most; test without if pure culture needed",
            source_tag="auxotrophy",
        ))

    return components


def determine_sulfur_source(conn: sqlite3.Connection,
                            evidence: Evidence,
                            energy: EnergyMetabolism,
                            ) -> List[Component]:
    """Select sulfur source. For SRBs, sulfate is already in the energy components."""
    components = []
    pwys = evidence.pathways

    # If SRB or sulfur oxidizer: sulfate is handled by energy overlay
    if energy.type in ("sulfate_reducer", "sulfur_oxidizer"):
        # MgSO4 still provides Mg + SO4 as base salt; flag it covers sulfur too
        return []  # MgSO4 added in determine_base_salts; no extra sulfur needed

    # Check for cysteine auxotrophy (organic sulfur needed)
    cys_aux = any("cysteine" in a["name"].lower() for a in evidence.auxotrophies)
    if cys_aux:
        components.append(Component(
            name="L-Cysteine (sulfur source)",
            compound_name="L-Cysteine",
            concentration=0.050,
            units="g/L",
            role="sulfur_source",
            confidence_obj=confidence.ConfidenceScore(
                value=0.80, source="gapseq",
                rationale="cysteine auxotrophy detected — needs organic sulfur supplement",
            ),
            source_tag="auxotrophy",
        ))
        return components

    # Check sulfate assimilation pathway (cysNDC, sat, aprAB)
    sulfate_assim = _best_completeness(pwys, r"sulfate assimilation|cysNDC|cysNC")
    # Default: MgSO4 provides both Mg and sulfur — handled in base_salts.
    # Only add dedicated Na2SO4 if MgSO4 won't be enough (unusual).
    # For simplicity, return empty — MgSO4 in base_salts covers this.
    return components


def determine_phosphate_buffer(conn: sqlite3.Connection,
                               evidence: Evidence,
                               ) -> List[Component]:
    """Select phosphate source and pH buffer."""
    components = []
    ph = evidence.effective_ph or 7.0
    pwys = evidence.pathways

    # Check for high-affinity pst phosphate transporter
    has_pst = any("phosphat" in (sub or "").lower() and cnt >= 2
                  for sub, cnt in evidence.transporters)
    pst_comp = _best_completeness(pwys, r"pst.system|high.affinity phosphate")

    # Phosphate concentration based on transporter type
    if has_pst or pst_comp >= 50:
        # P-limited environment → lower phosphate
        p_conc_fallback = 0.2
        p_rationale = "high-affinity pst phosphate transporter detected → P-limited environment"
    else:
        p_conc_fallback = 0.5
        p_rationale = "standard phosphate concentration (no P-limitation signal)"

    # Buffer selection by pH
    buffer_compound = None
    for ph_min, ph_max, compound, pka, conc in BUFFER_BY_PH:
        if ph_min <= ph <= ph_max:
            buffer_compound = (compound, conc)
            break
    if buffer_compound is None:
        buffer_compound = ("KH2PO4 / K2HPO4", 0.5)

    # Decide: if phosphate buffer covers the pH range, use K2HPO4 for both
    use_phosphate_buffer = 6.0 <= ph <= 7.5

    if use_phosphate_buffer:
        med, p10, p90, n, src = calibrate_concentration(
            conn, "k2hpo4", None, fallback_conc=p_conc_fallback)
        components.append(Component(
            name="K2HPO4",
            compound_name="K2HPO4",
            concentration=round(med, 2),
            units="g/L",
            role="phosphate",
            confidence_obj=confidence.ConfidenceScore(
                value=0.85, source="gapseq",
                rationale=(f"{p_rationale}; pH {ph:.1f} ≈ phosphate pKa 7.2; "
                           f"calibrated: median={med:.2f} g/L (n={n})"),
            ),
            source_tag="genomespot",
        ))
        if p_conc_fallback == 0.2:   # P-limited: also add small KH2PO4 for ratio
            components.append(Component(
                name="KH2PO4",
                compound_name="KH2PO4",
                concentration=round(med * 0.3, 3),
                units="g/L",
                role="buffer",
                confidence_obj=confidence.ConfidenceScore(
                    value=0.80, source="gapseq",
                    rationale="KH2PO4/K2HPO4 ratio maintains pH 7.0-7.4",
                ),
                source_tag="genomespot",
            ))
    else:
        # Phosphate separate from buffer
        med_p, _, _, n_p, src_p = calibrate_concentration(
            conn, "k2hpo4", None, fallback_conc=p_conc_fallback)
        components.append(Component(
            name="K2HPO4",
            compound_name="K2HPO4",
            concentration=round(med_p, 2),
            units="g/L",
            role="phosphate",
            confidence_obj=confidence.ConfidenceScore(
                value=0.80, source="gapseq",
                rationale=f"{p_rationale}; calibrated median={med_p:.2f} g/L (n={n_p})",
            ),
            source_tag="genomespot",
        ))
        # Non-phosphate buffer
        buf_name, buf_conc_default = buffer_compound
        med_b, _, _, n_b, src_b = calibrate_concentration(
            conn, buf_name.split()[0].lower(), None, fallback_conc=buf_conc_default)
        components.append(Component(
            name=buf_name,
            compound_name=buf_name,
            concentration=round(med_b, 2),
            units="g/L",
            role="buffer",
            confidence_obj=confidence.ConfidenceScore(
                value=0.75, source="genomespot",
                rationale=(f"pH {ph:.1f} → non-phosphate buffer needed; "
                           f"calibrated median={med_b:.2f} g/L (n={n_b})"),
            ),
            source_tag="genomespot",
        ))

    return components


def determine_vitamins(conn: sqlite3.Connection,
                       evidence: Evidence,
                       ) -> List[Component]:
    """Add vitamin/cofactor supplements from genome_auxotrophies."""
    components = []
    n_aux = len(evidence.auxotrophies)

    # If yeast extract was already added (>5 auxotrophies), only add cofactors
    # that yeast extract doesn't cover (heme, molybdopterin, etc.)
    ye_added = n_aux > YEAST_EXTRACT_AUXO_THRESHOLD
    ye_covered = {"cobalamin", "b12", "thiamin", "b1", "riboflavin", "b2",
                  "niacin", "b3", "pantothenate", "b5", "pyridoxal", "b6",
                  "folate", "b9", "biotin", "b7"}

    for aux in evidence.auxotrophies:
        name = aux["name"]
        cls = aux.get("class", "")
        comp = aux.get("best_completeness", 0)

        # Skip amino acids if yeast extract is added (it covers them)
        if ye_added and cls == "amino_acid":
            continue

        # Skip vitamins covered by YE
        if ye_added and any(v in name.lower() for v in ye_covered):
            continue

        # Determine concentration
        conc = COFACTOR_CONCENTRATION.get(name)
        if conc is None:
            conc = 0.001 if cls in ("vitamin", "cofactor") else AA_SUPPLEMENT_CONC

        # Confidence: gap probability → supplement confidence
        gap_prob = max(0, 1 - (comp or 0) / 100.0)
        supp_conf_val = min(0.95, 0.50 + 0.45 * gap_prob)

        role = "vitamin" if cls in ("vitamin", "cofactor") else "amino_acid"
        flag = None
        if comp and 50 <= comp < 90:
            flag = (f"partial biosynthesis ({comp:.0f}%); "
                    "test with/without to confirm requirement")

        components.append(Component(
            name=f"{name} supplement",
            compound_name=name,
            concentration=conc,
            units="g/L",
            role=role,
            confidence_obj=confidence.ConfidenceScore(
                value=supp_conf_val, source="gapseq",
                rationale=(f"gapseq auxotrophy: biosynthesis pathway "
                           f"{comp:.0f}% complete (gap probability {gap_prob:.0%})"),
            ),
            uncertainty_note=flag,
            source_tag="auxotrophy",
        ))

    return components


def determine_trace_metals(conn: sqlite3.Connection,
                           evidence: Evidence,
                           ) -> List[Component]:
    """Add trace metal supplements from genome_metal_profile (MeBiPred)."""
    components = []
    for m in evidence.metal_profile:
        metal = m["metal"]
        if m["n_binding"] < 3 or m["max_probability"] < 0.65:
            continue

        supp = METAL_SUPPLEMENT.get(metal)
        if not supp:
            continue
        compound, conc, units = supp

        # Use profile's typical_concentration if available
        if m.get("typical_concentration"):
            try:
                conc = float(m["typical_concentration"])
            except (TypeError, ValueError):
                pass

        note = None
        if m.get("is_anomaly"):
            note = m.get("anomaly_note", "")

        components.append(Component(
            name=f"{metal} trace metal ({compound})",
            compound_name=compound,
            concentration=conc,
            units=units,
            role="trace_metal",
            confidence_obj=confidence.ConfidenceScore(
                value=m["confidence"], source="mebipred",
                rationale=(f"MeBiPred: {m['n_binding']} {metal}-binding proteins "
                           f"(max_p={m['max_probability']:.2f}, "
                           f"fraction={m['fraction_of_proteome']:.1%})"),
            ),
            uncertainty_note=note,
            source_tag="mebipred",
        ))

    # Always include standard SL-10-like trace elements at baseline concentrations
    # if no metal profile data is available
    if not components:
        baseline_metals = ["Fe", "Zn", "Mn", "Co", "Ni", "Cu"]
        for metal in baseline_metals:
            supp = METAL_SUPPLEMENT.get(metal)
            if supp:
                compound, conc, units = supp
                components.append(Component(
                    name=f"{metal} trace metal ({compound})",
                    compound_name=compound,
                    concentration=conc,
                    units=units,
                    role="trace_metal",
                    confidence_obj=confidence.ConfidenceScore(
                        value=0.65, source="gapseq",
                        rationale="baseline trace element addition (no MeBiPred data)",
                    ),
                    source_tag="default",
                ))

    return components


def _detect_marine_salinity(conn: sqlite3.Connection,
                            evidence: Evidence) -> Tuple[bool, int, str]:
    """Fix 4: detect marine organisms via Na+ cycling genes in transporter data.

    Counts transporters belonging to specific TC families that are diagnostic
    for Na+-dependent energy metabolism (nha, mrp, nqr).  Generic Na+-coupled
    symporters (present in all prokaryotes) are NOT counted.
    Returns (is_marine, n_specific_na_genes, rationale).
    """
    n_specific = 0
    n_families = 0
    evidence_parts = []

    # Query the database for specific TC family hits
    try:
        for tc_prefix in NA_CYCLING_TC_FAMILIES:
            count = conn.execute("""
                SELECT COUNT(*) FROM genome_transporters
                 WHERE genome_id = ? AND tc_id LIKE ?
            """, (evidence.genome_id, f"{tc_prefix}%")).fetchone()[0]
            if count > 0:
                n_specific += count
                n_families += 1
                evidence_parts.append(f"TC {tc_prefix}: {count} hits")
    except Exception:
        pass

    # Require ≥8 specific Na+ cycling genes from ≥2 different TC families.
    # Lower thresholds produce false positives: Lactobacillus has 5 (CPA1
    # for acid tolerance).  The gene count alone does not distinguish marine
    # from non-marine; it must be combined with GenomeSPOT salinity > 2%
    # in the caller.
    is_marine = n_specific >= 8 and n_families >= 2
    rationale = "; ".join(evidence_parts) if evidence_parts else "no specific Na+ cycling TC families detected"
    return is_marine, n_specific, rationale


def determine_base_salts(conn: sqlite3.Connection,
                         evidence: Evidence,
                         ) -> List[Component]:
    """Determine NaCl and base salt mixture from GenomeSPOT + compatible solute genes.

    Fix 4 (session 17): marine salinity detection via Na+ cycling genes
    (nhaA/B, mrp, nqr) in transporter data. When detected alongside
    GenomeSPOT salinity > 1%, increase NaCl to marine range (20-30 g/L).
    """
    components = []
    pwys = evidence.pathways

    # Detect halophile markers (compatible solute genes).
    # Require predicted=true OR ≥80% completeness — many non-halophiles
    # have partial ectoine/betaine genes at 50-60% that are not functional.
    halophile_level = None
    for pat, level in HALOPHILE_MARKERS:
        matches = _pathway_matches(pwys, pat, min_completeness=80)
        if matches:
            halophile_level = level
            break

    # Fix 4: marine salinity detection.
    # Na+/H+ antiporter gene counts (nha, mrp, nqr) do NOT reliably distinguish
    # marine from non-marine organisms — they serve pH homeostasis, membrane
    # energetics, and acid tolerance as well.  GenomeSPOT salinity is the primary
    # signal, with halophile markers (ectoine) as the strongest override.
    nacl_conc = None
    nacl_rationale = ""
    nacl_conf = 0.70

    if halophile_level:
        nacl_conc = 30.0
        nacl_rationale = f"halophile marker detected: {halophile_level}"
        nacl_conf = 0.85
    elif evidence.salinity_pct is not None and evidence.salinity_pct > 2.5:
        # High GenomeSPOT salinity (>2.5%) — likely marine or moderately halophilic
        nacl_conc = evidence.salinity_pct * 10
        nacl_rationale = (f"GenomeSPOT salinity {evidence.salinity_pct:.2f}% "
                          f"(>2.5% threshold → marine/halophilic range)")
        nacl_conf = 0.80
    elif evidence.salinity_pct is not None:
        # Low–moderate GenomeSPOT salinity (≤2.5%): cap conservatively.
        # GenomeSPOT over-predicts salinity for many mesophiles; without a
        # confirmatory signal we limit to 5 g/L.
        nacl_conc = min(evidence.salinity_pct * 10, 5.0)
        nacl_rationale = (f"GenomeSPOT salinity {evidence.salinity_pct:.2f}%; "
                          f"capped at 5 g/L (below marine threshold)")
        nacl_conf = 0.70
    else:
        med, p10, p90, n, src = calibrate_concentration(
            conn, "nacl", None, fallback_conc=1.0)
        nacl_conc = round(med, 1)
        nacl_rationale = f"global median NaCl = {med:.1f} g/L (n={n})"
        nacl_conf = 0.70

    if nacl_conc is not None and nacl_conc > 0.1:
        components.append(Component(
            name="NaCl",
            compound_name="NaCl",
            concentration=round(nacl_conc, 1),
            units="g/L",
            role="base_salt",
            confidence_obj=confidence.ConfidenceScore(
                value=nacl_conf,
                source="genomespot",
                rationale=nacl_rationale,
            ),
            source_tag="genomespot",
        ))

    # MgSO4 — scale up for marine/halophilic organisms
    mg_fallback = 3.5 if (nacl_conc and nacl_conc >= 20) else 0.5
    med_mg, _, _, n_mg, _ = calibrate_concentration(
        conn, "mgso4", None, fallback_conc=mg_fallback)
    mg_conc = mg_fallback if (nacl_conc and nacl_conc >= 20) else round(med_mg, 2)
    mg_rationale = (f"MgSO4 — marine/halophilic concentration (NaCl ≥ 20 g/L → elevated Mg); "
                    f"fallback={mg_fallback} g/L") if mg_conc >= 3.0 else (
                    f"MgSO4 — standard major cation + sulfur source; "
                    f"median={med_mg:.2f} g/L (n={n_mg})")
    components.append(Component(
        name="MgSO4·7H2O",
        compound_name="MgSO4·7H2O",
        concentration=mg_conc,
        units="g/L",
        role="base_salt",
        confidence_obj=confidence.ConfidenceScore(
            value=0.90 if mg_conc < 3.0 else 0.78,
            source="mediadive",
            rationale=mg_rationale,
        ),
        source_tag="default",
    ))

    # CaCl2 (calcium)
    med_ca, _, _, n_ca, _ = calibrate_concentration(
        conn, "cacl2", None, fallback_conc=0.05)
    components.append(Component(
        name="CaCl2·2H2O",
        compound_name="CaCl2·2H2O",
        concentration=round(med_ca, 3),
        units="g/L",
        role="base_salt",
        confidence_obj=confidence.ConfidenceScore(
            value=0.88, source="mediadive",
            rationale=f"CaCl2 — standard calcium source; median={med_ca:.3f} g/L (n={n_ca})",
        ),
        source_tag="default",
    ))

    return components


def determine_atmosphere(conn: sqlite3.Connection,
                         evidence: Evidence,
                         energy: EnergyMetabolism,
                         ) -> List[Component]:
    """Determine atmosphere from terminal oxidase profile (primary) and GenomeSPOT (secondary).

    Concern 3 (session 18b): atmosphere is determined by the terminal oxidase
    profile directly, independent of energy metabolism classification.  This
    prevents wrong metabolism → wrong atmosphere cascade.

      aa3/bo3 complex_complete → aerobic (these are low-affinity, high-O₂ oxidases)
      cbb3/bd complex_complete only → microaerophilic (high-affinity, low-O₂)
      no terminal oxidases → anaerobic
      both high and low affinity → facultative (recommend aerobic + note)

    GenomeSPOT is consulted as a SECONDARY signal.  When it disagrees with the
    oxidase profile, the disagreement is flagged but the oxidase profile wins.
    """
    # Get the base gas recommendation (handles H₂:CO₂ for methanogens etc.)
    gas_rec = get_gas_phase_recommendation(
        conn, evidence.genome_id,
        genomespot_oxygen=evidence.oxygen_prediction,
    )
    headspace = gas_rec["headspace"]
    base_is_anaerobe = gas_rec.get("is_anaerobe", False)

    # --- Terminal oxidase profile ---
    # Only bo3 and cbb3 complex_complete are unambiguous respiratory signals:
    #   bo3 = quinol oxidase, ONLY functions in aerobic respiration (low-affinity)
    #   cbb3 = high-affinity cytochrome c oxidase, ONLY aerobic (microaerophilic)
    # bd oxidase is AMBIGUOUS: respiratory in microaerophiles, but protective
    #   (O₂ detox) in strict anaerobes and aerotolerant fermenters.
    # cytc_hits are TOO NOISY: Geobacter has 12 hits from iron-reduction
    #   cytochromes, not terminal oxidases.  Cannot be used for atmosphere.
    bo3_cc  = _marker_complex_complete(evidence, "bo3_oxidase")
    cbb3_cc = _marker_complex_complete(evidence, "cbb3_oxidase")
    bd_cc   = _marker_complex_complete(evidence, "bd_oxidase")

    ox_evidence = []
    if bo3_cc:  ox_evidence.append("bo3 complex complete (unambiguous low-affinity aerobic)")
    if cbb3_cc: ox_evidence.append("cbb3 complex complete (unambiguous high-affinity microaerophilic)")
    if bd_cc:   ox_evidence.append("bd complex complete (ambiguous: respiratory or protective)")

    # --- Primary decision from unambiguous oxidase markers ---
    oxidase_atmosphere = None
    oxidase_is_anaerobe = None

    if bo3_cc:
        # bo3 is definitively an aerobic terminal oxidase
        oxidase_atmosphere = "Aerobic (air) — bo3 terminal oxidase complex detected"
        oxidase_is_anaerobe = False
        ox_evidence.append("→ aerobic (bo3 is unambiguously respiratory)")
    elif cbb3_cc:
        # cbb3 is definitively a microaerophilic terminal oxidase
        oxidase_atmosphere = ("Microaerobic: 5-10% O₂, 10% CO₂, balance N₂ "
                              "(use CampyGen sachets or gas mixer)")
        oxidase_is_anaerobe = False
        ox_evidence.append("→ microaerophilic (cbb3 is unambiguously respiratory, high-affinity)")
    else:
        # No unambiguous respiratory oxidase detected.
        # bd alone is not diagnostic (present in both anaerobes for O₂ protection
        # and in aerotolerant fermenters).  Fall back to GenomeSPOT.
        if bd_cc:
            ox_evidence.append("→ bd only — ambiguous; deferring to GenomeSPOT")
        else:
            ox_evidence.append("→ no terminal oxidase detected; deferring to GenomeSPOT")

    # --- Merge oxidase decision with base gas_rec ---
    gs_says_anaerobe = ("not tolerant" in (evidence.oxygen_prediction or "").lower())
    gs_says_aerobe = not gs_says_anaerobe and evidence.oxygen_prediction is not None

    if oxidase_atmosphere is not None:
        # Unambiguous oxidase signal (bo3 or cbb3) overrides GenomeSPOT
        headspace = oxidase_atmosphere
        gas_rec["is_anaerobe"] = False

        if gs_says_anaerobe:
            ox_evidence.append(
                "NOTE: GenomeSPOT predicts anaerobe, but unambiguous terminal "
                "oxidase disagrees — oxidase profile takes precedence")

        gas_rec["confidence"] = confidence.ConfidenceScore(
            value=0.82,
            source="genomic",
            rationale=f"oxidase profile: {'; '.join(ox_evidence)}",
        )
    else:
        # No unambiguous oxidase → GenomeSPOT is the primary signal.
        # The base gas_rec from carbon_and_gas already uses GenomeSPOT.
        # Just annotate with the oxidase evidence.
        ox_rationale = "; ".join(ox_evidence)
        old_rationale = gas_rec["confidence"].rationale if gas_rec.get("confidence") else ""
        gas_rec["confidence"] = confidence.ConfidenceScore(
            value=gas_rec["confidence"].value if gas_rec.get("confidence") else 0.65,
            source="genomic",
            rationale=f"{old_rationale}; oxidase check: {ox_rationale}",
        )

    components = [Component(
        name=f"Headspace: {headspace}",
        compound_name=headspace,
        concentration=None,
        units=None,
        role="other",
        confidence_obj=gas_rec["confidence"],
        source_tag="gapseq",
    )]

    # Resazurin for anaerobes
    if gas_rec.get("is_anaerobe"):
        components.append(Component(
            name="Resazurin (redox indicator)",
            compound_name="Resazurin",
            concentration=0.0005,
            units="g/L",
            role="other",
            confidence_obj=confidence.ConfidenceScore(
                value=0.95, source="mediadive",
                rationale="standard redox indicator for strict anaerobes",
            ),
            source_tag="default",
        ))

    return components, gas_rec


def determine_reducing_agent(conn: sqlite3.Connection,
                             evidence: Evidence,
                             energy: EnergyMetabolism,
                             ) -> List[Component]:
    """Approved addition #1: Select reducing agent by metabolism type.

    Na2S for SRBs, cysteine-HCl for Clostridia/fermenters,
    Ti(III) citrate for iron reducers, DTT for methanogens.
    """
    if not evidence.is_anaerobe and energy.type in ("aerobic_heterotroph", "microaerophile"):
        return []

    # Select by metabolism type
    reducer_spec = REDUCING_AGENTS.get(energy.type)
    if reducer_spec is None:
        if evidence.is_anaerobe:
            reducer_spec = REDUCING_AGENTS["default_anaerobe"]
        else:
            return []

    compound, conc, units, rationale = reducer_spec

    conf_val = 0.90 if energy.confidence.value >= 0.80 else 0.75
    c = Component(
        name=compound,
        compound_name=compound,
        concentration=conc,
        units=units,
        role="other",  # reducing agents don't fit standard roles cleanly
        confidence_obj=confidence.ConfidenceScore(
            value=conf_val, source="gapseq",
            rationale=(f"reducing agent for {energy.type}: {rationale}"),
        ),
        source_tag=f"reducing_agent:{energy.type}",
    )
    return [c]


# ---------------------------------------------------------------- energy overlay

def _energy_overlay_components(energy: EnergyMetabolism,
                               conn: sqlite3.Connection,
                               ) -> List[Component]:
    """Add electron donor/acceptor compounds for the specific metabolism type."""
    components = []

    specs = {
        "sulfate_reducer": [
            ("Na2SO4", "electron_acceptor", "so4", 2.0),
            ("Sodium DL-lactate", "electron_donor", "lactate", 2.0),
        ],
        "methanogen": [
            ("NaHCO3", "electron_acceptor", "nahco3", 2.5),
        ],
        "iron_reducer": [
            ("Ferric citrate", "electron_acceptor", "ferric citrate", 5.0),
            ("Sodium acetate", "electron_donor", "acetate", 2.0),
        ],
        "sulfur_oxidizer": [
            ("Na2S2O3·5H2O", "electron_donor", "thiosulfate", 5.0),
        ],
        "ammonia_oxidizer": [
            ("NH4Cl", "electron_donor", "nh4cl", 0.5),
        ],
        "denitrifier": [
            ("KNO3", "electron_acceptor", "kno3", 1.0),
        ],
        "hydrogen_oxidizer": [],  # gas phase handles H2
    }.get(energy.type, [])

    for compound, role, calibrate_key, fallback in specs:
        med, p10, p90, n, src = calibrate_concentration(
            conn, calibrate_key, energy.type, fallback_conc=fallback)
        c = Component(
            name=compound,
            compound_name=compound,
            concentration=round(med, 2),
            units="g/L",
            role=role,
            confidence_obj=confidence.ConfidenceScore(
                value=energy.confidence.value,
                source=energy.confidence.source,
                rationale=(f"{role} for {energy.type}; "
                           f"calibrated: median={med:.2f} g/L "
                           f"[P10={p10:.2f}, P90={p90:.2f}] (n={n}, {src})"),
            ),
            source_tag=f"energy:{energy.type}",
        )
        components.append(c)

    return components


# ---------------------------------------------------------------- canonical compound names

def _canonical_compound(substrate: str) -> str:
    """Map a carbon substrate name to a canonical MediaDive-style compound name."""
    _MAP = {
        "lactate":   "Sodium DL-lactate",
        "pyruvate":  "Sodium pyruvate",
        "acetate":   "Sodium acetate",
        "formate":   "Sodium formate",
        "succinate": "Disodium succinate",
        "glucose":   "D(+)-Glucose",
        "fructose":  "D-Fructose",
        "maltose":   "Maltose",
        "sucrose":   "Sucrose",
        "malate":    "DL-Malic acid",
        "citrate":   "Trisodium citrate",
        "butyrate":  "Sodium butyrate",
        "propionate": "Sodium propionate",
        "ethanol":   "Ethanol",
        "methanol":  "Methanol",
        "glycerol":  "Glycerol",
    }
    return _MAP.get(substrate.lower(), substrate.capitalize())


# ---------------------------------------------------------------- main synthesizer

@dataclass
class DeNovoRecipe:
    """Complete de novo recipe output."""
    genome_id: int
    accession: str
    energy: EnergyMetabolism
    components: List[Component]
    overall_confidence: Optional[confidence.ConfidenceScore] = None
    compatibility_warnings: list = field(default_factory=list)
    prep_instructions: Optional[str] = None
    format_rec: Optional[dict] = None
    gas_recommendation: Optional[dict] = None
    thermo_result: Optional[dict] = None
    is_autotrophic: bool = False
    n_auxotrophies: int = 0


def synthesize_denovo(conn: sqlite3.Connection,
                      genome_id: int,
                      user_overrides: Optional[dict] = None,
                      ) -> DeNovoRecipe:
    """Top-level de novo pipeline. Returns a DeNovoRecipe."""
    user_overrides = user_overrides or {}
    accession = user_overrides.get("accession", str(genome_id))

    # Phase 1: Gather evidence
    ev = gather_evidence(conn, genome_id, accession)
    ev.user_temperature = user_overrides.get("temperature")
    ev.user_ph = user_overrides.get("ph")
    ev.user_energy_metabolism = user_overrides.get("energy_metabolism")

    # Phase 2: Energy metabolism
    energy = determine_energy_metabolism(
        conn, ev, user_override=ev.user_energy_metabolism)

    # Phase 3: Recipe dimensions
    carbon     = determine_carbon_source(conn, ev, energy)
    nitrogen   = determine_nitrogen_source(conn, ev, energy)
    sulfur     = determine_sulfur_source(conn, ev, energy)
    phosphate  = determine_phosphate_buffer(conn, ev)
    vitamins   = determine_vitamins(conn, ev)
    metals     = determine_trace_metals(conn, ev)
    salts      = determine_base_salts(conn, ev)
    reducing   = determine_reducing_agent(conn, ev, energy)
    atm_result = determine_atmosphere(conn, ev, energy)
    if isinstance(atm_result, tuple):
        atmosphere, gas_rec = atm_result
    else:
        atmosphere, gas_rec = atm_result, None

    # Energy overlay (electron donors/acceptors as explicit components)
    energy_comps = _energy_overlay_components(energy, conn)

    # Assemble all components
    all_components = (
        energy_comps + carbon + nitrogen + sulfur + phosphate +
        vitamins + metals + salts + reducing + atmosphere
    )

    # Deduplicate by compound name.  When the same compound appears in
    # multiple sources (e.g. NaCl from MeBiPred trace metals at 1 g/L AND
    # from base_salts at 20 g/L for marine organisms), keep the entry
    # with the higher concentration — the more specific source wins.
    seen: Dict[str, int] = {}          # key → index in unique_components
    unique_components: List[Component] = []
    for c in all_components:
        key = (c.compound_name or c.name).lower()
        if key not in seen:
            seen[key] = len(unique_components)
            unique_components.append(c)
        else:
            idx = seen[key]
            existing = unique_components[idx]
            e_conc = existing.concentration or 0
            n_conc = c.concentration or 0
            if n_conc > e_conc:
                unique_components[idx] = c

    # Phase 4: Compatibility check
    compound_names = [c.compound_name or c.name for c in unique_components
                      if c.compound_name]
    is_sulfidogenic = energy.type == "sulfate_reducer"
    compat_warnings = check_compatibility(
        conn, compound_names,
        ph=ev.effective_ph,
        temperature=ev.effective_temperature,
        is_sulfidogenic=is_sulfidogenic,
    )
    prep_instr = generate_prep_instructions(compat_warnings, compound_names)

    # Phase 5: Physical format
    format_rec = predict_format(
        conn, genome_id,
        temperature=ev.effective_temperature,
        ph=ev.effective_ph,
    )

    # Phase 6: Thermodynamic viability
    thermo_result = None
    if energy.type not in ("unknown",):
        thermo_result = check_thermodynamic_viability(
            conn, energy.type.replace("_", "-"),
            ev.effective_temperature or 37.0,
        )

    # Phase 7: Overall confidence — weighted approach for de novo.
    # Critical components (energy, carbon, nitrogen, base salts) carry more
    # weight than uncertain vitamin auxotrophies. This prevents a partial-
    # pathway auxotrophy at 0.55 from dragging the entire recipe to LOW
    # when the energy metabolism and base salts are at 0.90.
    critical_scores = []
    secondary_scores = []
    for c in unique_components:
        if c.role in ("electron_donor", "electron_acceptor", "carbon_source",
                       "nitrogen_source", "base_salt", "phosphate"):
            critical_scores.append(c.confidence)
        elif c.confidence.value < 1.0:  # skip trivial 1.0s
            secondary_scores.append(c.confidence)
    # Energy metabolism confidence is always critical
    critical_scores.append(energy.confidence)

    if critical_scores:
        critical_min = min(s.value for s in critical_scores)
    else:
        critical_min = 0.50
    if secondary_scores:
        secondary_mean = sum(s.value for s in secondary_scores) / len(secondary_scores)
    else:
        secondary_mean = critical_min

    # Weighted: 70% critical minimum, 30% secondary mean
    weighted_val = 0.70 * critical_min + 0.30 * secondary_mean
    # Agreement bonus if criticals are consistent
    if critical_scores and max(s.value for s in critical_scores) - critical_min < 0.10:
        weighted_val = min(0.95, weighted_val + 0.05)

    overall = confidence.ConfidenceScore(
        value=round(weighted_val, 2), source="combined",
        rationale=(f"weighted: 70% critical_min ({critical_min:.2f}) + "
                   f"30% secondary_mean ({secondary_mean:.2f}); "
                   f"{len(critical_scores)} critical, "
                   f"{len(secondary_scores)} secondary components"),
    )

    penalty = confidence_penalty(compat_warnings)
    if penalty > 0:
        new_val = max(0.20, overall.value - penalty)
        overall = confidence.ConfidenceScore(
            value=new_val, source="combined",
            rationale=(f"{overall.rationale}; "
                       f"−{penalty:.2f} compatibility penalty "
                       f"({len(compat_warnings)} warnings)"),
        )

    _, _, is_auto, _, _, _ = (False, "", False, "", 0.0, None)
    is_auto, _, _ = _has_autotrophy(ev.pathways)

    recipe = DeNovoRecipe(
        genome_id=genome_id,
        accession=accession,
        energy=energy,
        components=unique_components,
        overall_confidence=overall,
        compatibility_warnings=compat_warnings,
        prep_instructions=prep_instr,
        format_rec=format_rec,
        gas_recommendation=gas_rec,
        thermo_result=thermo_result,
        is_autotrophic=energy.is_autotrophic or is_auto,
        n_auxotrophies=len(ev.auxotrophies),
    )
    return recipe


# ---------------------------------------------------------------- template comparison

def _get_template_recipe(conn: sqlite3.Connection, hits: list,
                         evidence: Evidence) -> Optional[dict]:
    """Run rank_candidate_media and return top-1 template dict."""
    if not hits:
        return None
    query_tc = classify_temp(evidence.effective_temperature or 37.0)
    ranked_pairs = rank_candidate_media(
        conn, hits, evidence.auxotrophies,
        query_tc, evidence.effective_ph or 7.0)
    if not ranked_pairs:
        return None
    media_id, info = ranked_pairs[0]
    result = dict(info)
    result["id"] = media_id
    return result


def _side_by_side(recipe: DeNovoRecipe, template: dict) -> str:
    """Build a side-by-side comparison table."""
    lines = []

    # Index de novo by lower-case compound name
    denovo_by_compound: Dict[str, Component] = {}
    for c in recipe.components:
        key = (c.compound_name or c.name).lower()
        denovo_by_compound[key] = c

    # Index template recipe
    template_comps: Dict[str, dict] = {}
    for r in (template.get("recipe") or []):
        name = (r.get("compound") or "").lower()
        if name and name not in ("water", "distilled water"):
            template_comps[name] = r

    # Collect all compound keys
    all_keys = sorted(set(denovo_by_compound) | set(template_comps))

    lines.append(f"  {'Component':<30s} {'De novo':>12s}  {'Template':>12s}  {'Match':>6s}")
    lines.append("  " + "-" * 68)

    matches = 0
    total = 0
    for key in all_keys:
        dn = denovo_by_compound.get(key)
        tm = template_comps.get(key)

        dn_str = dn.conc_display() if dn and dn.concentration else "—"
        tm_conc = (tm.get("g_per_L") or tm.get("amount")) if tm else None
        tm_str = f"{tm_conc:.2f} g/L" if tm_conc else "—"

        # Match classification
        if dn and tm:
            if dn.concentration and tm_conc:
                ratio = dn.concentration / tm_conc if tm_conc else 999
                match = "✓" if 0.5 <= ratio <= 2.0 else "~"
            else:
                match = "~"
            matches += 1
        elif dn and not tm:
            match = "+"  # de novo adds
        else:
            match = "✗"  # template has, de novo omits
        total += 1

        display_key = key[:28]
        lines.append(f"  {display_key:<30s} {dn_str:>12s}  {tm_str:>12s}  {match:>6s}")

    lines.append("  " + "-" * 68)
    pct = int(100 * matches / total) if total else 0
    lines.append(f"  Agreement: {matches}/{total} components within 2x → {pct}%")
    return "\n".join(lines)


# ---------------------------------------------------------------- format report

def format_denovo_report(recipe: DeNovoRecipe,
                         template_comparison: Optional[dict] = None,
                         accession: str = "",
                         ) -> str:
    """Format the de novo recipe as the design-doc output."""
    out = []
    bar = "=" * 80
    acc = accession or recipe.accession

    out.append(bar)
    out.append(f"  DE NOVO RECIPE — composed from genomic evidence")
    out.append(f"  Query: {acc}")
    out.append(bar)
    out.append("")

    overall = recipe.overall_confidence
    if overall:
        out.append(f"  Overall Confidence: {overall.category} ({overall.value:.2f})")
        out.append(f"  → {overall.rationale}")
    out.append("")

    # Energy metabolism block
    e = recipe.energy
    out.append(f"  ENERGY METABOLISM: {e.type.replace('_', ' ').title()}")
    out.append(f"    Electron donor:    {e.electron_donor}")
    out.append(f"    Electron acceptor: {e.electron_acceptor}")
    out.append(f"    Autotrophic:       {'Yes' if e.is_autotrophic else 'No'}")
    if e.genomic_evidence:
        out.append(f"    Genomic evidence:  {'; '.join(e.genomic_evidence[:3])}")
    out.append(f"    Confidence:        [{e.confidence.value:.2f}] {e.confidence.category}")
    out.append(f"    → {e.confidence.rationale}")

    # Thermodynamic viability
    if recipe.thermo_result and recipe.thermo_result.get("available"):
        tr = recipe.thermo_result
        dga = tr.get("dg_actual")
        v = tr.get("viability", "?")
        marker = "✓ VIABLE" if v == "viable" else ("⚠ MARGINAL" if v == "marginal" else "✗ NOT VIABLE")
        if dga is not None:
            out.append(f"    Thermodynamics:    ΔGr = {dga:.1f} kJ/mol "
                       f"→ {marker}")
        if v != "viable" and tr.get("adjustment_advice"):
            out.append(f"    → {tr['adjustment_advice']}")
    out.append("")

    # Group components
    role_order = [
        ("electron_donor",        "ELECTRON DONOR"),
        ("electron_acceptor",     "ELECTRON ACCEPTOR"),
        ("carbon_source",         "CARBON SOURCE"),
        ("nitrogen_source",       "NITROGEN SOURCE"),
        ("complex_source",        "COMPLEX NUTRIENT SOURCE"),
        ("sulfur_source",         "SULFUR SOURCE"),
        ("phosphate",             "PHOSPHATE / BUFFER"),
        ("buffer",                "BUFFER"),
        ("vitamin",               "VITAMINS / COFACTORS"),
        ("amino_acid",            "AMINO ACID SUPPLEMENTS"),
        ("auxotrophy_supplement", "AUXOTROPHY SUPPLEMENTS"),
        ("trace_metal",           "TRACE METALS"),
        ("base_salt",             "BASE SALTS / OSMOLARITY"),
        ("other",                 "ATMOSPHERE / REDOX"),
        ("gelling_agent",         "GELLING AGENT"),
    ]
    by_role: Dict[str, List[Component]] = defaultdict(list)
    for c in recipe.components:
        by_role[c.role].append(c)

    for role, heading in role_order:
        items = by_role.get(role, [])
        if not items:
            continue
        out.append(f"  {heading}:")
        for c in items:
            conc_str = c.conc_display() if c.concentration is not None else ""
            flag = " ⚠" if c.uncertainty_flag else ""
            name_part = (c.compound_name or c.name)
            out.append(f"    {name_part:<40s} {conc_str:<15s} [{c.confidence.value:.2f}]{flag}")
            # Show rationale for all non-default components
            if c.source_tag not in ("default",):
                out.append(f"      → {c.confidence.rationale}")
            if c.uncertainty_note:
                out.append(f"      ⚠ {c.uncertainty_note}")
        out.append("")

    # Auxotrophy summary
    if recipe.n_auxotrophies > 0:
        out.append(f"  AUXOTROPHY SUMMARY: {recipe.n_auxotrophies} auxotrophies detected")
        if recipe.n_auxotrophies > YEAST_EXTRACT_AUXO_THRESHOLD:
            out.append(f"    → >{YEAST_EXTRACT_AUXO_THRESHOLD} auxotrophies: yeast extract added to cover vitamins + amino acids")
        out.append("")

    # Compatibility warnings
    if recipe.compatibility_warnings:
        out.append(bar)
        out.append("  COMPATIBILITY WARNINGS")
        out.append(bar)
        out.append(format_warnings(recipe.compatibility_warnings))

    # Prep instructions
    if recipe.prep_instructions:
        out.append(recipe.prep_instructions)
        out.append("")

    # Physical format
    if recipe.format_rec:
        fr = recipe.format_rec
        out.append(bar)
        out.append("  PHYSICAL FORMAT")
        out.append(bar)
        out.append(f"  Primary: {fr['primary_format']}")
        out.append(f"    → {fr['primary_detail']}")
        out.append(f"  Solidifying agent: {fr['solidifying_agent']}")
        if fr.get("alternative"):
            out.append(f"  Alternative: {fr['alternative']}")
        for w in fr.get("warnings", []):
            out.append(f"  ⚠ {w}")
        out.append("")

    # Variation matrix
    variations = build_variation_matrix(recipe.components)
    if variations:
        out.append(bar)
        out.append("  EXPERIMENTAL VARIATION MATRIX")
        out.append(bar)
        for name, reason, variant in variations:
            out.append(f"  • {name} ({reason})")
            out.append(f"      → {variant}")
        out.append("")

    # Template comparison
    if template_comparison:
        out.append(bar)
        out.append("  TEMPLATE COMPARISON (for reference)")
        out.append(bar)
        tmpl = template_comparison
        out.append(f"  Nearest template: {tmpl.get('name', '?')}")
        out.append(f"  Phylogenetic identity (best): {tmpl.get('phylo_identity_best', 0):.1f}%")
        out.append(f"  Template match score: {tmpl.get('score', 0):.2f}")
        out.append("")
        out.append(_side_by_side(recipe, tmpl))
        out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------- persist

def persist_denovo(conn: sqlite3.Connection, recipe: DeNovoRecipe,
                   args) -> int:
    """Persist the de novo recipe to predictions + recipe_components tables."""
    conn.executescript(SM_SCHEMA_SQL)
    confidence.populate_source_table(conn)
    now = datetime.utcnow().isoformat(timespec="seconds")
    overall = recipe.overall_confidence
    n_unc = sum(1 for c in recipe.components if c.uncertainty_flag)
    cur = conn.execute("""
        INSERT INTO predictions
          (genome_id, input_accession, template_media_id, template_media_name,
           template_media_source_id, overall_confidence, overall_category,
           user_temp, user_ph, user_salinity, energy_metabolism,
           n_components, n_uncertain, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recipe.genome_id, recipe.accession,
        None, None, None,
        overall.value if overall else 0.5,
        overall.category if overall else "LOW",
        getattr(args, "temperature", None),
        getattr(args, "ph", None),
        None,
        getattr(args, "energy_metabolism", None),
        len(recipe.components), n_unc, "de_novo", now,
    ))
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for c in recipe.components:
        conn.execute("""
            INSERT INTO recipe_components
              (prediction_id, component_name, compound_name,
               concentration, concentration_units, role, is_critical,
               component_confidence, confidence_source,
               uncertainty_flag, uncertainty_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid, c.name, c.compound_name,
            c.concentration, c.units, c.role, 1 if c.is_critical else 0,
            c.confidence.value, c.confidence_source,
            1 if c.uncertainty_flag else 0, c.uncertainty_note,
        ))
    conn.commit()
    return pid


# ---------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(
        description="CultureForge De Novo Media Synthesizer: build a recipe from genomic evidence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("genome", help="Path to genome FASTA")
    parser.add_argument("--accession", default=None,
                        help="Genome accession for DB lookup (required for gapseq data)")
    parser.add_argument("--temperature", type=float, default=None,
                        help="Override growth temperature (°C)")
    parser.add_argument("--ph", type=float, default=None,
                        help="Override pH")
    parser.add_argument("--energy-metabolism", default=None,
                        help="Override energy metabolism (e.g. sulfate-reduction, methanogenesis)")
    parser.add_argument("--compare-template", action="store_true",
                        help="Add side-by-side comparison with phylogenetically nearest template")
    parser.add_argument("--no-persist", action="store_true",
                        help="Dry run — do not write results to DB")
    parser.add_argument("--db", default=DB,
                        help=f"Path to SQLite database (default: {DB})")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of phylogenetic relatives to consider")
    parser.add_argument("--min-identity", type=float, default=80.0,
                        help="BLAST minimum %% identity")
    args = parser.parse_args()

    if not os.path.exists(args.genome):
        sys.exit(f"Genome not found: {args.genome}")

    accession = args.accession or os.path.splitext(os.path.basename(args.genome))[0]

    # ---- step 1: 16S extraction
    print(f"\n[1/5] Extracting 16S rRNA from {args.genome} ...")
    s16_path = extract_16s(args.genome)
    if not s16_path:
        print("      barrnap failed or not installed. Continuing without BLAST hits.")
        hits = []
    else:
        with open(s16_path) as f:
            seq_len = sum(len(ln.strip()) for ln in f if not ln.startswith(">"))
        print(f"      {seq_len} bp 16S extracted.")

        # ---- step 2: BLAST
        print(f"\n[2/5] BLASTing against {BLAST_DB} ...")
        hits = run_blast(s16_path, top_n=args.top, min_identity=args.min_identity)
        if hits:
            print(f"      {len(hits)} hits, best {hits[0]['identity']:.1f}% ({hits[0]['species']})")
        else:
            print("      No BLAST hits (BLAST DB may not exist — continuing).")

    conn = sqlite3.connect(args.db)
    try:
        # ---- step 3: genome DB lookup
        print(f"\n[3/5] Looking up genome in DB (accession={accession}) ...")
        genome_row = get_genome_id_for_accession(conn, accession)
        if genome_row is None:
            print(f"      No DB record for '{accession}'. ")
            print("      Synthesis will run with empty evidence (low confidence).")
            # Insert a placeholder genome row so the pipeline can run
            conn.execute(
                "INSERT OR IGNORE INTO genomes (accession, n_unique_genes) VALUES (?, 0)",
                (accession,),
            )
            conn.commit()
            genome_row = get_genome_id_for_accession(conn, accession)
            if genome_row is None:
                sys.exit("Cannot proceed without a genome record in the DB.")
        genome_id = genome_row[0]
        print(f"      genome_id={genome_id}")

        # ---- step 4: de novo synthesis
        print(f"\n[4/5] Synthesizing de novo recipe ...")
        user_overrides = {
            "accession": accession,
            "temperature": args.temperature,
            "ph": args.ph,
            "energy_metabolism": args.energy_metabolism,
        }
        recipe = synthesize_denovo(conn, genome_id, user_overrides)
        print(f"      Energy metabolism: {recipe.energy.type} "
              f"[{recipe.energy.confidence.value:.2f}]")
        print(f"      Components: {len(recipe.components)}, "
              f"auxotrophies: {recipe.n_auxotrophies}")

        # ---- step 5: template comparison (optional)
        template = None
        if args.compare_template:
            print(f"\n[5/5] Getting template comparison ...")
            ev = gather_evidence(conn, genome_id, accession)
            ev.user_temperature = args.temperature
            ev.user_ph = args.ph
            template = _get_template_recipe(conn, hits, ev)
            if template:
                print(f"      Template: {template.get('name', '?')}")
            else:
                print("      No template found.")
        else:
            print(f"\n[5/5] (Use --compare-template to see side-by-side comparison)")

        # Report
        report = format_denovo_report(
            recipe,
            template_comparison=template,
            accession=accession,
        )
        print()
        print(report)

        # Persist
        if not args.no_persist:
            pid = persist_denovo(conn, recipe, args)
            print(f"\nPersisted to DB as prediction_id={pid}")
        else:
            print("\n[dry run — not persisted]")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
