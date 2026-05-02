"""Derive RecipeContext from a CapabilityProfile and supporting database tables.

Translates "what can this organism do" into "what does the recipe need to provide."
Read-only: queries existing data, runs no new analyses.

Usage:
    from derive_recipe_context import derive_recipe_context
    ctx = derive_recipe_context(genome_id, conn)
"""

from __future__ import annotations

import re
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from recipe_context import (
    Atmosphere, CarbonSource, CofactorRequirement, ElectronAcceptor,
    ElectronDonor, GrowthConditions, NitrogenSource, RecipeContext,
    SpecialRequirement, TraceMetal,
)

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from capability_detectors import (
    CapabilityProfile, profile_capabilities, _get_genomespot_oxygen,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_species(conn, genome_id):
    row = conn.execute("""
        SELECT COALESCE(o.species, g.notes, g.accession)
        FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
        WHERE g.id = ?
    """, (genome_id,)).fetchone()
    sp = row[0] if row else str(genome_id)
    for prefix in ("Validation organism: ", "Blind validation: ", "Blind v2: "):
        sp = sp.replace(prefix, "")
    return sp.replace("_", " ")


def _mode_names(profile):
    """Return set of active cultivation mode names."""
    return {m["mode"] for m in profile.cultivation_modes}


def _cap_detected(profile, keyword):
    """Check if a capability containing keyword is detected."""
    for c in profile.capabilities:
        if c.detected and keyword.lower() in c.name.lower():
            return c
    return None


def _gapseq_pathways(conn, genome_id, pattern):
    """Query gapseq pathways matching pattern, return list of (name, comp, pred)."""
    rows = conn.execute("""
        SELECT pathway_name, completeness, predicted FROM genome_pathways
        WHERE genome_id = ? AND lower(pathway_name) LIKE ?
    """, (genome_id, f"%{pattern.lower()}%")).fetchall()
    return [(r[0], r[1], bool(r[2])) for r in rows]


def _best_pathway(conn, genome_id, pattern):
    """Return (name, completeness, predicted) for best matching pathway, or None."""
    matches = _gapseq_pathways(conn, genome_id, pattern)
    if not matches:
        return None
    return max(matches, key=lambda x: (x[2], x[1]))


# ---------------------------------------------------------------------------
# 2.1 Atmosphere derivation
# ---------------------------------------------------------------------------

def _derive_atmosphere(profile: CapabilityProfile,
                       genomespot_oxygen: Optional[str],
                       ) -> Tuple[Optional[Atmosphere], List[Atmosphere], List[str]]:
    """Derive primary atmosphere and alternatives from cultivation modes."""
    modes = _mode_names(profile)
    primary = None
    alternatives = []
    gases = []

    # Priority order for primary atmosphere.
    # Methanogenic and phototrophic have unique atmospheres (check first).
    # For organisms with both aerobic and anaerobic modes, aerobic wins as
    # primary because aerobic cultivation is simpler and the anaerobic mode
    # is offered as an alternative.
    if "methanogenic" in modes:
        primary = Atmosphere.SPECIAL_GAS
        gases = ["H2", "CO2"]
    elif "methanotrophic" in modes:
        # Phase 3.5: methanotroph atmosphere — air + methane
        primary = Atmosphere.SPECIAL_GAS
        gases = ["air", "CH4"]
    elif "phototrophic" in modes:
        primary = Atmosphere.PHOTOTROPHIC
        if "aerobic_chemotrophic" in modes:
            alternatives.append(Atmosphere.AEROBIC)
    elif "lithotrophic_aerobic" in modes and "anaerobic_respiratory" in modes:
        # Lithotrophic + anaerobic respiratory co-primary = microaerophile
        # (e.g., Sulfurimonas: sulfur oxidation + denitrification)
        primary = Atmosphere.MICROAEROBIC
        alternatives = [Atmosphere.AEROBIC, Atmosphere.ANAEROBIC]
    elif "aerobic_chemotrophic" in modes or "lithotrophic_aerobic" in modes:
        # Aerobic is preferred when available (even for facultatives)
        primary = Atmosphere.AEROBIC
        if any(m in modes for m in ("fermentative", "anaerobic_respiratory", "acetogenic")):
            alternatives.append(Atmosphere.ANAEROBIC)
    elif "halophilic_with_rhodopsin" in modes:
        primary = Atmosphere.AEROBIC
    elif "syntrophic" in modes or "acetogenic" in modes:
        primary = Atmosphere.ANAEROBIC
        gases = ["N2", "CO2"]
    elif "anaerobic_respiratory" in modes:
        primary = Atmosphere.ANAEROBIC
        gases = ["N2", "CO2"]
    elif "fermentative" in modes:
        primary = Atmosphere.ANAEROBIC
        gases = ["N2", "CO2"]

    # Microaerobic from GenomeSPOT
    if genomespot_oxygen == "microaerophile" or (
            primary == Atmosphere.AEROBIC and _cap_detected(profile, "cbb3")):
        # Check if cbb3 is the ONLY oxidase (microaerophile signal)
        bo3 = _cap_detected(profile, "bo3")
        if not bo3 and primary == Atmosphere.AEROBIC:
            primary = Atmosphere.MICROAEROBIC

    # Fallback
    if primary is None:
        if genomespot_oxygen == "tolerant":
            primary = Atmosphere.AEROBIC
        elif genomespot_oxygen == "not_tolerant":
            primary = Atmosphere.ANAEROBIC
            gases = ["N2"]
        else:
            primary = Atmosphere.AEROBIC  # safest default

    return primary, alternatives, gases


# ---------------------------------------------------------------------------
# 2.2 Carbon source derivation
# ---------------------------------------------------------------------------

def _derive_carbon_sources(profile: CapabilityProfile,
                           conn: sqlite3.Connection,
                           genome_id: int) -> List[CarbonSource]:
    modes = _mode_names(profile)
    sources = []

    # Autotrophic modes: CO2 as carbon
    if any(m in modes for m in ("methanogenic", "lithotrophic_aerobic", "acetogenic")):
        sources.append(CarbonSource(
            name="CO2", type="CO2", confidence=0.85,
            evidence=["autotrophic cultivation mode detected"],
            derived_from_capability=next(iter(modes & {"methanogenic", "lithotrophic_aerobic", "acetogenic"}), None),
        ))

    # Phototrophic: organic acids typical for purple bacteria
    if "phototrophic" in modes:
        for substrate in ["malate", "succinate", "lactate", "acetate"]:
            pwy = _best_pathway(conn, genome_id, substrate)
            if pwy and (pwy[2] or pwy[1] >= 70):
                sources.append(CarbonSource(
                    name=substrate, type="organic_acid", confidence=min(0.85, pwy[1] / 100),
                    evidence=[f"gapseq: {pwy[0]} ({pwy[1]:.0f}%)"],
                    derived_from_capability="phototrophic",
                ))
                break  # one primary organic acid is enough
        if not any(s.derived_from_capability == "phototrophic" for s in sources):
            sources.append(CarbonSource(
                name="CO2", type="CO2", confidence=0.70,
                evidence=["photoautotrophic growth possible"],
                derived_from_capability="phototrophic",
            ))

    # Syntrophy: fatty acids (check before general heterotrophic to avoid sugar FP)
    # Also check for syntrophy evidence even if mode threshold wasn't reached,
    # since syntrophy detection can be suppressed by marginal denitrification FPs.
    syntrophy_cap = next((c for c in profile.capabilities
                          if "syntrophy" in c.name.lower()), None)
    syntrophy_signal = ("syntrophic" in modes or
                        (syntrophy_cap and syntrophy_cap.confidence >= 0.50))
    if syntrophy_signal:
        for substrate in ["butyrate", "propionate", "crotonate", "fatty acid", "beta-oxidation"]:
            pwy = _best_pathway(conn, genome_id, substrate)
            if pwy and pwy[1] >= 50:
                sources.append(CarbonSource(
                    name=substrate, type="fatty_acid", confidence=min(0.75, pwy[1] / 100),
                    evidence=[f"gapseq: {pwy[0]} ({pwy[1]:.0f}%)"],
                    derived_from_capability="syntrophic",
                ))
                break
        if not any(s.derived_from_capability == "syntrophic" for s in sources):
            sources.append(CarbonSource(
                name="butyrate (or other short-chain fatty acid)", type="fatty_acid",
                confidence=0.60,
                evidence=["syntrophic mode: fatty acid oxidation is typical substrate"],
                derived_from_capability="syntrophic",
            ))

    # Heterotrophic modes: sugars and organic acids (skip if syntrophic already provided carbon)
    if any(m in modes for m in ("aerobic_chemotrophic", "fermentative")) and not syntrophy_signal:
        # Query gapseq for best sugar utilization
        for substrate, stype in [("glucose", "sugar"), ("fructose", "sugar"),
                                  ("lactose", "sugar"), ("sucrose", "sugar"),
                                  ("lactate", "organic_acid"), ("acetate", "organic_acid"),
                                  ("pyruvate", "organic_acid"), ("succinate", "organic_acid")]:
            pwy = _best_pathway(conn, genome_id, substrate)
            if pwy and (pwy[2] or pwy[1] >= 70):
                sources.append(CarbonSource(
                    name=substrate, type=stype, confidence=min(0.85, pwy[1] / 100),
                    evidence=[f"gapseq: {pwy[0]} ({pwy[1]:.0f}%)"],
                    derived_from_capability="heterotrophic",
                ))
                if len([s for s in sources if s.derived_from_capability == "heterotrophic"]) >= 3:
                    break

    # Iron reduction: acetate
    if _cap_detected(profile, "Fe(III) reduction"):
        sources.append(CarbonSource(
            name="acetate", type="organic_acid", confidence=0.75,
            evidence=["iron reducer: acetate is typical electron donor"],
            derived_from_capability="iron_reduction",
        ))

    # Sulfate reduction: lactate/pyruvate/acetate
    if _cap_detected(profile, "sulfate reduction"):
        for substrate in ["lactate", "pyruvate", "acetate"]:
            pwy = _best_pathway(conn, genome_id, substrate)
            if pwy and (pwy[2] or pwy[1] >= 60):
                sources.append(CarbonSource(
                    name=substrate, type="organic_acid", confidence=0.75,
                    evidence=[f"sulfate reducer: {pwy[0]} ({pwy[1]:.0f}%)"],
                    derived_from_capability="sulfate_reduction",
                ))
                break

    # Deduplicate by name
    seen = set()
    unique = []
    for s in sources:
        if s.name not in seen:
            seen.add(s.name)
            unique.append(s)
    return unique


# ---------------------------------------------------------------------------
# 2.3 Electron donor derivation
# ---------------------------------------------------------------------------

def _derive_electron_donors(profile: CapabilityProfile,
                            conn: sqlite3.Connection) -> List[ElectronDonor]:
    modes = _mode_names(profile)
    donors = []

    if "methanogenic" in modes or "acetogenic" in modes:
        donors.append(ElectronDonor("H2", 0.85, ["hydrogenotrophic pathway"], "methanogenic"))

    # Phase 3.5: methanotrophy — methane is both donor and carbon source
    if "methanotrophic" in modes:
        donors.append(ElectronDonor("CH4", 0.95,
                                    ["methane monooxygenase (pmoA / mmoX) detected"],
                                    "methanotrophic"))

    if _cap_detected(profile, "ammonia oxidation"):
        donors.append(ElectronDonor("NH4+", 0.90, ["ammonia monooxygenase (amoA) detected"], "ammonia_oxidation"))

    # Phase 3.3: nitrite oxidation as electron donor
    if _cap_detected(profile, "nitrite oxidation"):
        donors.append(ElectronDonor("NO2-", 0.90,
                                    ["nitrite oxidoreductase (nxrA) detected"],
                                    "nitrite_oxidation"))

    if _cap_detected(profile, "Sulfur oxidation") or _cap_detected(profile, "sulfide"):
        donors.append(ElectronDonor("H2S / thiosulfate", 0.80,
                                    ["sulfur oxidation pathway detected"], "sulfur_oxidation"))

    if _cap_detected(profile, "Fe(II) oxidation"):
        donors.append(ElectronDonor("Fe(II)", 0.75, ["iron oxidation detected"], "iron_oxidation"))

    if any(m in modes for m in ("aerobic_chemotrophic", "fermentative", "anaerobic_respiratory")):
        donors.append(ElectronDonor("organic carbon", 0.75,
                                    ["heterotrophic metabolism: carbon source is electron donor"],
                                    "heterotrophic"))

    if "syntrophic" in modes:
        donors.append(ElectronDonor("fatty acids", 0.70,
                                    ["syntrophic fatty acid oxidation"], "syntrophic"))

    return donors


# ---------------------------------------------------------------------------
# 2.4 Electron acceptor derivation
# ---------------------------------------------------------------------------

def _derive_electron_acceptors(profile: CapabilityProfile,
                               conn: sqlite3.Connection) -> List[ElectronAcceptor]:
    modes = _mode_names(profile)
    acceptors = []

    if any(m in modes for m in ("aerobic_chemotrophic", "lithotrophic_aerobic")):
        acceptors.append(ElectronAcceptor("O2", 0.90, ["aerobic respiration"], "aerobic"))

    if _cap_detected(profile, "sulfate reduction"):
        acceptors.append(ElectronAcceptor("SO4^2-", 0.80,
                                          ["dissimilatory sulfate reduction (dsrAB)"], "sulfate_reduction"))

    if _cap_detected(profile, "Denitrification"):
        acceptors.append(ElectronAcceptor("NO3-", 0.75,
                                          ["denitrification pathway detected"], "denitrification"))

    # Phase 3.4: DNRA — same acceptor (NO3-) as denitrification but reduced
    # to NH4+ via NrfA terminal step instead of N2O reductase + nosZ.
    if _cap_detected(profile, "Dissimilatory nitrate reduction to ammonium"):
        acceptors.append(ElectronAcceptor("NO3-", 0.85,
                                          ["DNRA via NrfA (nrfA detected)"], "dnra"))

    if _cap_detected(profile, "Fe(III) reduction"):
        acceptors.append(ElectronAcceptor("Fe(III)", 0.75,
                                          ["dissimilatory Fe(III) reduction (mtrC/omcB)"], "iron_reduction"))

    if _cap_detected(profile, "Organohalide") or _cap_detected(profile, "dehalogenation"):
        acceptors.append(ElectronAcceptor("chlorinated organics", 0.70,
                                          ["reductive dehalogenase (rdhA)"], "organohalide"))

    if "methanogenic" in modes:
        acceptors.append(ElectronAcceptor("CO2", 0.85,
                                          ["methanogenesis: CO2 reduced to CH4"], "methanogenic"))

    if "acetogenic" in modes:
        acceptors.append(ElectronAcceptor("CO2", 0.80,
                                          ["acetogenesis: CO2 reduced to acetate via WL"], "acetogenic"))

    if _cap_detected(profile, "Anammox"):
        acceptors.append(ElectronAcceptor("NO2-", 0.80,
                                          ["anammox: nitrite as electron acceptor"], "anammox"))

    # Fermentative and syntrophic: no external acceptor
    if "fermentative" in modes and not acceptors:
        acceptors.append(ElectronAcceptor("none (substrate-level phosphorylation)", 0.75,
                                          ["fermentation: internal electron balance"], "fermentative"))

    if "syntrophic" in modes:
        acceptors.append(ElectronAcceptor("partner organism (H2 sink)", 0.70,
                                          ["syntrophic: electrons transferred as H2 to partner"], "syntrophic"))

    return acceptors


# ---------------------------------------------------------------------------
# 2.5 Nitrogen source derivation
# ---------------------------------------------------------------------------

def _derive_nitrogen_sources(profile: CapabilityProfile,
                             conn: sqlite3.Connection,
                             genome_id: int) -> List[NitrogenSource]:
    sources = []

    # Default: NH4+ (universal prokaryotic nitrogen source)
    sources.append(NitrogenSource("NH4+", 0.80, ["standard inorganic nitrogen source"]))

    # N2 fixation
    if _cap_detected(profile, "Nitrogen fixation"):
        sources.append(NitrogenSource("N2 (if NH4+ unavailable)", 0.60,
                                      ["nifH detected: organism can fix atmospheric N2"]))

    # Amino acid auxotrophy check
    try:
        auxotrophies = conn.execute("""
            SELECT compound_name, compound_class, best_completeness
            FROM genome_auxotrophies WHERE genome_id = ?
            AND compound_class = 'amino_acid'
        """, (genome_id,)).fetchall()

        n_aa_aux = len(auxotrophies)
        if n_aa_aux >= 10:
            missing = [a[0] for a in auxotrophies[:5]]
            sources.append(NitrogenSource(
                "amino acid supplement (peptone/casamino acids)", 0.80,
                [f"{n_aa_aux} amino acid auxotrophies detected: {', '.join(missing)}...",
                 "organism cannot synthesize many amino acids; complex nitrogen needed"],
            ))
        elif n_aa_aux >= 3:
            missing = [a[0] for a in auxotrophies]
            sources.append(NitrogenSource(
                f"individual amino acid supplements ({n_aa_aux})", 0.70,
                [f"auxotrophic for: {', '.join(missing)}"],
            ))
    except Exception:
        pass

    return sources


# ---------------------------------------------------------------------------
# 2.6 Trace metals derivation
# ---------------------------------------------------------------------------

def _derive_trace_metals(profile: CapabilityProfile,
                         conn: sqlite3.Connection,
                         genome_id: int) -> List[TraceMetal]:
    metals = []

    # MeBiPred data
    try:
        rows = conn.execute("""
            SELECT metal_ion, n_binding_proteins, fraction_of_proteome, confidence, is_anomaly
            FROM genome_metal_profile WHERE genome_id = ?
            ORDER BY n_binding_proteins DESC
        """, (genome_id,)).fetchall()
        for metal, n_bind, frac, conf, anomaly in rows:
            if n_bind >= 10 and conf >= 0.70:
                importance = "essential" if frac >= 0.10 else "supporting" if frac >= 0.05 else "trace"
                ev = [f"MeBiPred: {n_bind} binding proteins ({frac:.1%} of proteome)"]
                if anomaly:
                    ev.append("flagged as anomalous (elevated relative to typical)")
                metals.append(TraceMetal(metal, importance, ev))
    except Exception:
        pass

    # Capability-derived requirements
    modes = _mode_names(profile)
    if "methanogenic" in modes:
        _ensure_metal(metals, "Ni", "essential", ["methanogenesis: mcrA contains Ni"])
        _ensure_metal(metals, "Co", "essential", ["methanogenesis: corrinoid cofactors"])
    if _cap_detected(profile, "Nitrogen fixation"):
        _ensure_metal(metals, "Mo", "essential", ["nitrogenase: Mo-Fe cofactor"])
    if _cap_detected(profile, "sulfate reduction"):
        _ensure_metal(metals, "Mo", "supporting", ["sulfate reduction: molybdopterin enzymes"])

    # Standard metals if none from MeBiPred
    if not metals:
        for m in ["Fe", "Zn", "Mn", "Co", "Ni", "Cu"]:
            metals.append(TraceMetal(m, "trace", ["standard trace element addition (no MeBiPred data)"]))

    return metals


def _ensure_metal(metals, element, importance, evidence):
    """Add metal if not already present, or upgrade importance."""
    for m in metals:
        if m.element == element:
            if importance == "essential" and m.importance != "essential":
                m.importance = importance
                m.evidence.extend(evidence)
            return
    metals.append(TraceMetal(element, importance, evidence))


# ---------------------------------------------------------------------------
# 2.7 Cofactor derivation
# ---------------------------------------------------------------------------

def _derive_cofactors(profile: CapabilityProfile,
                      conn: sqlite3.Connection,
                      genome_id: int) -> List[CofactorRequirement]:
    cofactors = []

    # Check auxotrophy view for vitamins/cofactors
    try:
        rows = conn.execute("""
            SELECT compound_name, compound_class, best_completeness
            FROM genome_auxotrophies WHERE genome_id = ?
            AND compound_class IN ('vitamin', 'cofactor')
        """, (genome_id,)).fetchall()
        for name, cls, comp in rows:
            cofactors.append(CofactorRequirement(
                name=name,
                can_synthesize=False,
                completeness=comp,
                confidence=0.80,
                evidence=[f"gapseq: biosynthesis pathway {comp:.0f}% complete (auxotrophic)"],
            ))
    except Exception:
        pass

    # Capability-specific cofactors
    modes = _mode_names(profile)
    if "methanogenic" in modes:
        for cof in ["F420", "coenzyme M", "coenzyme B"]:
            if not any(c.name == cof for c in cofactors):
                # Check if detected in capability profile
                cap = _cap_detected(profile, "Methanogenesis")
                if cap:
                    cov = cap.cofactor_coverage
                    cofactors.append(CofactorRequirement(
                        name=cof, can_synthesize=cov > 0.5, completeness=cov * 100,
                        confidence=0.75,
                        evidence=[f"methanogenesis cofactor: coverage {cov:.0%}"],
                    ))

    return cofactors


# ---------------------------------------------------------------------------
# 2.8 Growth conditions derivation
# ---------------------------------------------------------------------------

# Genus reclassifications: keys are the older (or CultureForge-internal) name,
# values are the newer name now used in TEMPURA / current taxonomy. Mirrors the
# table in data/build_phase2d_caches.py — keep in sync if either expands.
_TEMPURA_GENUS_SYNONYMS = {
    "Methanococcus jannaschii": "Methanocaldococcus jannaschii",
    "Lactobacillus plantarum": "Lactiplantibacillus plantarum",
    "Desulfovibrio vulgaris": "Nitratidesulfovibrio vulgaris",
}


def _lookup_tempura(conn: sqlite3.Connection, genome_id: int, species: str) -> Optional[dict]:
    """Find the TEMPURA-derived organisms-table row for this genome.

    Two-step lookup, in priority order:
      1. genomes.organism_id → organisms row (if linkage exists AND has values)
      2. species name match against organisms (handles unlinked genomes; tries
         exact match, genus-reclassification synonym, and stripped subsp/str).

    Returns a dict with keys optimal_temp, optimal_ph, min_temp, max_temp,
    match_method (one of "organism_id", "species_exact", "species_synonym",
    "species_stripped"), or None if no record carries any TEMPURA data.
    """
    # Step 1: organism_id linkage
    try:
        org_id_row = conn.execute(
            "SELECT organism_id FROM genomes WHERE id = ?", (genome_id,)
        ).fetchone()
        if org_id_row and org_id_row[0]:
            row = conn.execute(
                "SELECT optimal_temp, optimal_ph, min_temp, max_temp "
                "FROM organisms WHERE id = ?",
                (org_id_row[0],),
            ).fetchone()
            if row and (row[0] is not None or row[1] is not None):
                return {
                    "optimal_temp": row[0], "optimal_ph": row[1],
                    "min_temp": row[2], "max_temp": row[3],
                    "match_method": "organism_id",
                }
    except Exception:
        pass

    # Step 2: species name lookup (for unlinked genomes — most validation set)
    if not species:
        return None
    sp_clean = species.split(" subsp.")[0].split(" str.")[0].strip()
    candidates = [(sp_clean, "species_exact")]
    if sp_clean in _TEMPURA_GENUS_SYNONYMS:
        candidates.append((_TEMPURA_GENUS_SYNONYMS[sp_clean], "species_synonym"))
    if sp_clean.startswith("Candidatus "):
        candidates.append((sp_clean[len("Candidatus "):], "species_stripped"))

    for query_name, method in candidates:
        try:
            row = conn.execute(
                "SELECT optimal_temp, optimal_ph, min_temp, max_temp "
                "FROM organisms "
                "WHERE species = ? "
                "  AND (optimal_temp IS NOT NULL OR optimal_ph IS NOT NULL) "
                "ORDER BY optimal_temp IS NULL, optimal_ph IS NULL "
                "LIMIT 1",
                (query_name,),
            ).fetchone()
            if row:
                return {
                    "optimal_temp": row[0], "optimal_ph": row[1],
                    "min_temp": row[2], "max_temp": row[3],
                    "match_method": method,
                }
        except Exception:
            continue

    return None


def _derive_conditions(profile: CapabilityProfile,
                       conn: sqlite3.Connection,
                       genome_id: int,
                       overrides: Optional[dict] = None) -> GrowthConditions:
    """Derive growth conditions with TEMPURA-first priority (G.1 fix).

    Priority order for each field:
      Temperature: user_override → TEMPURA optimum → GenomeSPOT temperature_optimum → None
      pH:          user_override → TEMPURA optimum → GenomeSPOT ph_optimum → None
      Salinity:    user_override (g/L) sits alongside the category (Phase 3.1)

    Per-field provenance is encoded in cond.source as a comma-separated string
    like "temp:user_override, ph:tempura, salinity:not_set". Consumers that just
    check for "tempura" or "genomespot" substrings continue to work; the
    inspector surfaces full provenance to the user.
    """
    overrides = overrides or {}
    cond = GrowthConditions()
    species = _get_species(conn, genome_id)
    tempura = _lookup_tempura(conn, genome_id, species)

    temp_source = "none"
    ph_source = "none"
    salinity_source = "not_set"

    # Temperature: user override > TEMPURA > GenomeSPOT
    if overrides.get("temperature") is not None:
        cond.temperature_optimum_c = float(overrides["temperature"])
        cond.temperature_range_c = (cond.temperature_optimum_c - 5,
                                     cond.temperature_optimum_c + 5)
        temp_source = "user_override"
    elif tempura and tempura.get("optimal_temp") is not None:
        cond.temperature_optimum_c = tempura["optimal_temp"]
        temp_source = "tempura"
        if tempura.get("min_temp") is not None and tempura.get("max_temp") is not None:
            cond.temperature_range_c = (tempura["min_temp"], tempura["max_temp"])

    # pH: user override > TEMPURA > GenomeSPOT
    if overrides.get("ph") is not None:
        cond.ph_optimum = float(overrides["ph"])
        ph_source = "user_override"
    elif tempura and tempura.get("optimal_ph") is not None:
        cond.ph_optimum = tempura["optimal_ph"]
        ph_source = "tempura"

    # GenomeSPOT fallback for whichever fields are still unset (and not user-overridden)
    if temp_source != "user_override" or ph_source != "user_override":
        try:
            rows = conn.execute("""
                SELECT target, value, numeric_value, error
                FROM genome_growth_predictions WHERE genome_id = ?
            """, (genome_id,)).fetchall()
            for target, value, num, error in rows:
                t = target.lower()
                if (temp_source == "none"
                        and "temperature" in t and "optimum" in t and num):
                    cond.temperature_optimum_c = num
                    temp_source = "genomespot"
                    if error:
                        cond.temperature_range_c = (max(0, num - error), num + error)
                elif (ph_source == "none"
                        and "ph" in t and "optimum" in t and num):
                    cond.ph_optimum = num
                    ph_source = "genomespot"
                    if error:
                        cond.ph_range = (max(0, num - error), min(14, num + error))
        except Exception:
            pass

    # Salinity: user override is numeric (g/L); category is detector-derived
    if overrides.get("salinity") is not None:
        cond.salinity_g_per_l = float(overrides["salinity"])
        salinity_source = "user_override"
        cond.salinity_evidence = [f"user-supplied override: {cond.salinity_g_per_l:g} g/L NaCl"]

    # Salt-in halophily detection (separate from numeric override — sets category)
    if any("halophilic" in m for m in _mode_names(profile)):
        cond.salinity_category = "extreme_halophile"
        if salinity_source == "not_set":
            cond.salinity_evidence = ["salt-in halophily detected by capability detector"]
            salinity_source = "capability_detector"
    elif cond.temperature_optimum_c is None:
        cond.salinity_category = "non_halophile"
        if salinity_source == "not_set":
            cond.salinity_evidence = ["no halophile markers detected"]

    # Per-field source string. "unknown" is preserved when nothing was found
    # to keep the existing condition-confidence floor logic intact.
    if temp_source == "none" and ph_source == "none" and salinity_source == "not_set":
        cond.source = "unknown"
    else:
        cond.source = f"temp:{temp_source}, ph:{ph_source}, salinity:{salinity_source}"

    return cond


# ---------------------------------------------------------------------------
# 2.9 Special requirements derivation
# ---------------------------------------------------------------------------

def _derive_special_requirements(profile: CapabilityProfile,
                                 conn: sqlite3.Connection,
                                 genome_id: int,
                                 conditions: GrowthConditions) -> List[SpecialRequirement]:
    reqs = []
    modes = _mode_names(profile)

    if "syntrophic" in modes:
        reqs.append(SpecialRequirement(
            "syntrophic_partner",
            "Requires a syntrophic partner organism (typically a hydrogenotrophic methanogen) "
            "to consume H2 and maintain thermodynamically favorable conditions",
            ["syntrophy composite detector triggered"],
        ))

    if "phototrophic" in modes:
        reqs.append(SpecialRequirement(
            "light",
            "Requires a light source for phototrophic growth (tungsten lamp or LED, "
            "wavelength depends on pigment type)",
            ["phototrophic cultivation mode detected"],
        ))

    if "halophilic_with_rhodopsin" in modes:
        reqs.append(SpecialRequirement(
            "high_salt",
            "Extreme halophile requiring high NaCl concentration (typically 15-25% w/v)",
            ["bacteriorhodopsin / salt-in halophily detected"],
        ))

    # Temperature-based
    if conditions and conditions.temperature_optimum_c:
        t = conditions.temperature_optimum_c
        if t >= 80:
            reqs.append(SpecialRequirement(
                "hyperthermophilic_incubation",
                f"Requires high-temperature incubation ({t:.0f} C); "
                "use sealed vessels rated for high pressure if aqueous",
                [f"predicted temperature optimum {t:.0f} C"],
            ))
        elif t >= 55:
            reqs.append(SpecialRequirement(
                "thermophilic_incubation",
                f"Requires thermophilic incubation ({t:.0f} C)",
                [f"predicted temperature optimum {t:.0f} C"],
            ))

    # Strict anaerobe handling (skip if microaerophile — they're mutually exclusive)
    genomespot_ox = _get_genomespot_oxygen(conn, genome_id)
    is_microaerophile = ("lithotrophic_aerobic" in modes and "anaerobic_respiratory" in modes)
    if not is_microaerophile and (
            genomespot_ox == "not_tolerant" or any(
                m in modes for m in ("methanogenic", "syntrophic", "acetogenic"))):
        reqs.append(SpecialRequirement(
            "strict_anaerobe",
            "Strict anaerobic conditions required. Use Hungate technique or anaerobic "
            "chamber with N2/CO2 atmosphere. All solutions must be boiled and cooled "
            "under O2-free gas before use.",
            ["anaerobic cultivation mode or GenomeSPOT anaerobe prediction"],
        ))
    elif is_microaerophile:
        reqs.append(SpecialRequirement(
            "microaerophile",
            "Microaerophilic conditions recommended. Use reduced O2 (2-5%) with "
            "N2/CO2 balance, or CampyGen sachets for small-scale cultivation.",
            ["lithotrophic + anaerobic respiratory co-primary modes"],
        ))

    return reqs


# ---------------------------------------------------------------------------
# 2.10 Orchestrator
# ---------------------------------------------------------------------------

def derive_recipe_context(genome_id: int,
                          conn: sqlite3.Connection,
                          overrides: Optional[dict] = None) -> RecipeContext:
    """Top-level: derive RecipeContext from existing detection data.

    Args:
        genome_id: numeric genome ID in the genomes table.
        conn: open SQLite connection to data/cultureforge.db.
        overrides: optional dict with keys 'temperature', 'ph', 'salinity'.
            When a key is present and not None, the corresponding cultivation
            condition is set to that user-supplied value instead of being
            derived from TEMPURA/GenomeSPOT (Phase 3.1 manual override flags).
    """
    species = _get_species(conn, genome_id)
    profile = profile_capabilities(genome_id, conn)

    # QC gate
    if profile.quality_verdict.verdict == "REJECT":
        return RecipeContext(
            genome_id=genome_id, species=species,
            incompleteness_flags=["Genome failed quality control: " + profile.quality_verdict.rationale],
        )

    # Derive each field
    genomespot_ox = _get_genomespot_oxygen(conn, genome_id)
    primary_atm, alt_atm, gases = _derive_atmosphere(profile, genomespot_ox)
    carbon = _derive_carbon_sources(profile, conn, genome_id)
    donors = _derive_electron_donors(profile, conn)
    acceptors = _derive_electron_acceptors(profile, conn)
    nitrogen = _derive_nitrogen_sources(profile, conn, genome_id)
    metals = _derive_trace_metals(profile, conn, genome_id)
    cofactors = _derive_cofactors(profile, conn, genome_id)
    conditions = _derive_conditions(profile, conn, genome_id, overrides=overrides)
    special = _derive_special_requirements(profile, conn, genome_id, conditions)

    # Cultivation mode info
    mode_names = [m["mode"] for m in profile.cultivation_modes]
    mode_notes = []
    if len(mode_names) > 1:
        mode_notes.append(f"Multi-mode organism: {', '.join(mode_names)}. "
                          "Consider generating alternative recipes for each mode.")

    # Incompleteness flags
    flags = []
    if not carbon:
        flags.append("No carbon source could be determined")
    if conditions and conditions.temperature_optimum_c is None:
        flags.append("Growth temperature unknown (no GenomeSPOT/TEMPURA data)")
    if conditions and conditions.ph_optimum is None:
        flags.append("pH optimum unknown")
    if not profile.cultivation_modes:
        flags.append("No metabolic capabilities detected; substantial uncertainty in all recipe fields")

    # Overall confidence: average of top-mode confidence and condition source quality
    mode_conf = profile.cultivation_modes[0]["max_confidence"] if profile.cultivation_modes else 0.3
    cond_conf = 0.7 if conditions and (
        "tempura" in conditions.source or "genomespot" in conditions.source
    ) else 0.4
    overall = round(0.6 * mode_conf + 0.4 * cond_conf, 2)

    return RecipeContext(
        genome_id=genome_id,
        species=species,
        primary_atmosphere=primary_atm,
        alternative_atmospheres=alt_atm,
        gas_requirements=gases,
        carbon_sources=carbon,
        electron_donors=donors,
        electron_acceptors=acceptors,
        nitrogen_sources=nitrogen,
        conditions=conditions,
        trace_metals=metals,
        cofactors=cofactors,
        special_requirements=special,
        primary_cultivation_modes=mode_names,
        cultivation_mode_notes=mode_notes,
        overall_confidence=overall,
        incompleteness_flags=flags,
    )
