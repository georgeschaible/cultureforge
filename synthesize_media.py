"""Media Composition Synthesizer — compose a tailored recipe from a genome.

Per CLAUDE.md §"Media Composition Synthesizer (Core Innovation)" and the
confidence/tier addendum 2 output spec. Unlike `predict_media.py`, which
RECOMMENDS existing media, this module SYNTHESIZES a new recipe by layering
constraints onto a phylogenetic template:

  1. Template medium   — top-ranked medium from `predict_media.py` ranking
  2. Auxotrophy supplements — missing-biosynthesis compounds not already
                              covered (directly or via a complex source)
  3. Trace-metal supplements — high-confidence metal predictions from
                              `genome_metal_profile` not already in template
  4. Environmental adjustments — pH / temperature / atmosphere from the
                              multi-source thermal inference + GenomeSPOT
  5. Energy-metabolism overlay — electron donor/acceptor components per the
                              reference table in CLAUDE.md (via
                              --energy-metabolism)

Every component carries a ConfidenceScore. Overall recipe confidence is
`combine("min", critical_components, agreement_bonus=True)`. The report
mirrors the example in addendum 2.

Usage:
    python synthesize_media.py <genome.fasta> --accession ACC [options]

Options:
    --temperature T / --ph P / --salinity S   user overrides
    --energy-metabolism NAME                  e.g. 'methanogenesis'
    --template-id ID                          override auto-picked template
    --simulate-knockout COMPOUND              (test hook, rolled back)
    --no-persist                              don't write to DB (dry run)
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

import carbon_and_gas
import compatibility
import media_format
import confidence
import thermodynamics as td
from phylo_match import (
    DB, BLAST_DB,
    run_blast, get_organism_info, get_media_recipe,
    get_media_with_fallback, classify_temp, thermal_distance,
    infer_thermal_multisource,
    DIRECT_COMPOUND_PATTERNS,
    COMPLEX_AMINO_ACID_SOURCES, COMPLEX_VITAMIN_SOURCES,
    coverage_for_medium,
    THERMAL_WEIGHTS, UNKNOWN_THERMAL_W, FALLBACK_WEIGHTS,
    ph_weight, coverage_weight,
    rank_candidate_media,
)
from predict_media import (
    extract_16s, get_genome_id_for_accession,
    get_auxotrophies, get_transporter_summary, get_metal_profile,
)


# ---------------------------------------------------------------- schema

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER,
    input_accession TEXT,
    template_media_id INTEGER,
    template_media_name TEXT,
    template_media_source_id TEXT,
    overall_confidence REAL NOT NULL,
    overall_category TEXT NOT NULL,
    user_temp REAL,
    user_ph REAL,
    user_salinity REAL,
    energy_metabolism TEXT,
    n_components INTEGER,
    n_uncertain INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    FOREIGN KEY (template_media_id) REFERENCES media(id)
);

CREATE TABLE IF NOT EXISTS recipe_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    compound_name TEXT,
    concentration REAL,
    concentration_units TEXT,
    role TEXT NOT NULL,
    is_critical INTEGER NOT NULL DEFAULT 0,
    component_confidence REAL NOT NULL,
    confidence_source TEXT,
    uncertainty_flag INTEGER NOT NULL DEFAULT 0,
    uncertainty_note TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

CREATE INDEX IF NOT EXISTS idx_rc_pred ON recipe_components(prediction_id);
"""


# ---------------------------------------------------------------- role classifier

_NITROGEN_RE = re.compile(
    r"\b(NH4|ammon|nitrate|NO3|NO2|urea|KNO3|NaNO3|NH4Cl)", re.IGNORECASE)
_PHOSPHATE_RE = re.compile(r"phosph|KH2PO4|K2HPO4|Na2HPO4|Na2HPO3", re.IGNORECASE)
_SULFATE_RE = re.compile(r"sulfate|SO4|Na2SO4|Na2S2O3|thiosulfate", re.IGNORECASE)
_BUFFER_RE = re.compile(
    r"\b(HEPES|MOPS|MES|Tris|PIPES|TES|bicine|tricine|borate|"
    r"carbonate|bicarbonate|NaHCO3)", re.IGNORECASE)
_AGAR_RE = re.compile(r"\b(agar|gelatin|gellan|water|distilled)", re.IGNORECASE)
_SUGAR_RE = re.compile(
    r"\b(glucose|sucrose|fructose|galactose|lactose|maltose|trehalose|"
    r"mannose|xylose|arabinose|ribose|rhamnose|cellobiose|starch|"
    r"glycerol|glycogen|sorbitol|mannitol|xylitol|arabitol|ribitol|"
    r"acetate|lactate|pyruvate|succinate|fumarate|malate|citrate|"
    r"formate|propionate|butyrate|methanol|ethanol)", re.IGNORECASE)


def classify_role(name):
    """Map a compound name from MediaDive to one of:
       base_salt / carbon_source / nitrogen_source / phosphate /
       sulfur_source / trace_metal / buffer / complex_source /
       vitamin / amino_acid / gelling_agent / water / other."""
    if not name:
        return "other"
    lo = name.lower()
    if _AGAR_RE.search(name):
        return "water" if "water" in lo or "distilled" in lo else "gelling_agent"
    # Complex sources (peptones, extracts) — covers both amino acids + vitamins
    for src in COMPLEX_AMINO_ACID_SOURCES:
        if src in lo:
            return "complex_source"
    for src in COMPLEX_VITAMIN_SOURCES:
        if src in lo:
            return "complex_source"
    # Nitrogen / phosphate / sulfur headline compounds
    if _NITROGEN_RE.search(name):
        return "nitrogen_source"
    if _PHOSPHATE_RE.search(name):
        return "phosphate"
    if _SULFATE_RE.search(name) and "MgSO4" not in name and "MnSO4" not in name \
            and "ZnSO4" not in name and "FeSO4" not in name and "CuSO4" not in name \
            and "CoSO4" not in name and "NiSO4" not in name and "CaSO4" not in name:
        return "sulfur_source"
    # Trace metals and major salts
    if re.search(r"(MgSO4|MgCl2|Mg\()", name):
        return "base_salt"  # Mg is a major ion, always a base salt
    if re.search(r"(CaCl2|CaSO4|Ca\()", name):
        return "base_salt"
    if re.search(r"(NaCl|KCl|K2SO4|Na2SO4|NaNO3)", name, re.IGNORECASE):
        return "base_salt"
    if re.search(
        r"(FeSO4|FeCl|Fe\(|ZnSO4|ZnCl|MnSO4|MnCl|CuSO4|CuCl|CoCl|CoSO4|"
        r"NiCl|NiSO4|Na2MoO4|Na2WO4|Na2SeO3|Na3VO4|H3BO3|boric)",
        name, re.IGNORECASE,
    ):
        return "trace_metal"
    # Buffers
    if _BUFFER_RE.search(name):
        return "buffer"
    # Carbon sources
    if _SUGAR_RE.search(name):
        return "carbon_source"
    # Amino acids / vitamins — check direct patterns
    for aa, patterns in DIRECT_COMPOUND_PATTERNS.items():
        if any(p in lo for p in patterns):
            # amino_acid if L-<aa> or just the aa, vitamin if Bx
            if "(B" in aa or any(v in aa.lower() for v in
                                 ("biotin", "folate", "thiamin", "riboflavin",
                                  "pantothen", "pyridoxal", "cobalamin", "niacin")):
                return "vitamin"
            return "amino_acid"
    return "other"


# ---------------------------------------------------------------- role → critical

CRITICAL_ROLES = {
    "base_salt", "carbon_source", "nitrogen_source", "complex_source",
    "amino_acid", "vitamin", "trace_metal", "phosphate", "sulfur_source",
    "auxotrophy_supplement", "electron_donor", "electron_acceptor",
}

# Supplement concentrations per the addendum 1 metal-media table
METAL_SUPPLEMENT = {
    "Fe": ("FeSO4·7H2O", 0.005, "g/L"),
    "Zn": ("ZnSO4·7H2O", 0.0005, "g/L"),
    "Mn": ("MnCl2·4H2O", 0.0005, "g/L"),
    "Cu": ("CuSO4·5H2O", 0.00005, "g/L"),
    "Co": ("CoCl2·6H2O", 0.00005, "g/L"),
    "Ni": ("NiCl2·6H2O", 0.00005, "g/L"),
    "Mg": ("MgSO4·7H2O", 0.5, "g/L"),
    "Ca": ("CaCl2·2H2O", 0.05, "g/L"),
    "K":  ("K2HPO4", 0.5, "g/L"),
    "Na": ("NaCl", 1.0, "g/L"),
}

# Auxotrophy supplement defaults — biologically appropriate concentrations.
# Amino acids: 20-100 mg/L typical for supplementation (not bulk C/N source)
AA_SUPPLEMENT_CONC = 0.050   # g/L = 50 mg/L — mid-range for amino acid supplements
VITAMIN_SUPPLEMENT_CONC = 0.001  # g/L = 1 mg/L — trace vitamins

# Cofactor-specific overrides where generic defaults would be wrong.
# These compounds are active at very different concentrations than amino acids.
COFACTOR_CONCENTRATION_OVERRIDES = {
    "heme":         0.005,   # g/L = 5 mg/L (hemin typically 1-10 mg/L)
    "siroheme":     0.001,   # g/L = 1 mg/L
    "molybdopterin": 0.001,  # g/L = 1 mg/L (usually supplied as Na2MoO4 0.01-0.1 mM)
    "NAD":          0.005,   # g/L = 5 mg/L
    "biotin (B7)":  0.00002, # g/L = 20 µg/L (biotin is active at µg/L)
    "folate (B9)":  0.001,   # g/L = 1 mg/L
    "cobalamin (B12)": 0.0001, # g/L = 0.1 mg/L = 100 µg/L
    "thiamin (B1)":  0.001,  # g/L = 1 mg/L
    "riboflavin (B2)": 0.001, # g/L = 1 mg/L
    "pantothenate (B5)": 0.001, # g/L = 1 mg/L
    "pyridoxal-5P (B6)": 0.001, # g/L = 1 mg/L
    "niacin (B3)":  0.001,   # g/L = 1 mg/L
}

# Electron donor/acceptor reference from main doc §Media Composition Synthesizer
ENERGY_METABOLISM = {
    "iron-reduction":     [("Ferric citrate", 5.0, "g/L", "electron_acceptor")],
    "sulfate-reduction":  [("Na2SO4", 2.0, "g/L", "electron_acceptor"),
                            ("Sodium lactate", 2.0, "g/L", "electron_donor")],
    "sulfur-oxidation":   [("Na2S2O3·5H2O", 5.0, "g/L", "electron_donor")],
    "methanogenesis":     [("NaHCO3", 2.5, "g/L", "electron_acceptor"),
                            ("Gas phase: H2:CO2 (80:20)", None, None,
                             "electron_donor")],
    "iron-oxidation":     [("FeSO4·7H2O", 10.0, "g/L", "electron_donor")],
    "ammonia-oxidation":  [("NH4Cl", 0.5, "g/L", "electron_donor")],
    "denitrification":    [("KNO3", 1.0, "g/L", "electron_acceptor")],
    "anammox":            [("NH4Cl", 0.5, "g/L", "electron_donor"),
                            ("NaNO2", 0.3, "g/L", "electron_acceptor")],
    "hydrogen-oxidation": [("Gas phase: H2:CO2 (80:20)", None, None,
                             "electron_donor")],
    "phototrophic":       [("NaHCO3", 2.0, "g/L", "carbon_source"),
                            ("(Light conditions: specify)", None, None,
                             "electron_donor")],
}

# Map each --energy-metabolism name to:
#   (reaction_name_in_DB, default_activities, adjustment_advice)
# The reaction_name must match metabolic_reactions.reaction_name exactly.
# Default activities are "typical environmental" — override via --activity.
THERMO_VIABILITY_MAP = {
    "methanogenesis": (
        "Methanogenesis (hydrogenotrophic)",
        {"CO2(aq)": 1e-2, "H2(aq)": 1e-4, "CH4(aq)": 1e-5, "H2O(l)": 1.0},
        "Increase H2 partial pressure (raise headspace H2:CO2 ratio); "
        "lower CO2 activity may help.",
    ),
    "sulfate-reduction": (
        "Sulfate reduction to H2S (H2 donor)",
        {"SO4(2-)": 2.8e-2, "H2(aq)": 1e-4, "H+": 1e-7,
         "H2S(aq)": 1e-4, "H2O(l)": 1.0},
        "Increase H2 or electron donor concentration; "
        "remove H2S (e.g., use FeS precipitation) to shift equilibrium.",
    ),
    "hydrogen-oxidation": (
        "Knallgas reaction (dissolved)",
        {"H2(aq)": 1e-4, "O2(aq)": 2e-4, "H2O(l)": 1.0},
        "Increase headspace H2 partial pressure.",
    ),
    "denitrification": (
        "Denitrification to N2 (nitrate)",
        {"NO3-": 1e-3, "H2(aq)": 1e-4, "H+": 1e-7,
         "N2(aq)": 1e-3, "H2O(l)": 1.0},
        "Increase nitrate or electron donor; flush N2.",
    ),
    "ammonia-oxidation": (
        "Ammonia oxidation (nitrification step 1)",
        {"NH3(aq)": 1e-3, "O2(aq)": 2e-4, "H+": 1e-7,
         "NO2-": 1e-5, "H2O(l)": 1.0},
        "Ensure adequate O2; increase ammonia if rate-limited.",
    ),
    "anammox": (
        "Anaerobic ammonia oxidation (anammox)",
        {"NH3(aq)": 1e-3, "NO2-": 1e-3, "H+": 1e-7,
         "N2(aq)": 1e-3, "H2O(l)": 1.0},
        "Increase NH4+ and NO2- concentrations; maintain strict anoxia.",
    ),
    "sulfur-oxidation": (
        "Sulfur oxidation to sulfate",
        {"S(s)": 1.0, "O2(aq)": 2e-4, "SO4(2-)": 1e-3,
         "H+": 1e-7, "H2O(l)": 1.0},
        "Ensure O2 availability; provide excess elemental sulfur.",
    ),
    # iron-reduction, iron-oxidation, phototrophic have no A&S reaction in
    # current database (require Table 9 digitisation). Mark as unavailable.
}


# ---------------------------------------------------------------- thermodynamic viability

def check_thermodynamic_viability(conn, energy_metabolism, temp_c,
                                  user_activities=None):
    """Look up the A&S reaction for this energy metabolism and compute ΔGr.

    Returns a dict with keys: reaction_name, equation, temp_c, dg_standard,
    dg_actual, viability, activities_used, adjustment_advice, available.
    If the metabolism has no A&S reaction in the DB, returns available=False.
    """
    key = energy_metabolism.lower().replace("_", "-")
    mapping = THERMO_VIABILITY_MAP.get(key)
    if mapping is None:
        return {
            "available": False,
            "reason": (f"no Amend & Shock reaction digitized for "
                       f"'{energy_metabolism}' (requires Table 9 metals "
                       f"or phototrophic reactions)"),
        }

    rxn_name, default_activities, advice = mapping
    try:
        rxn = td.get_reaction(conn, rxn_name)
    except KeyError:
        return {"available": False,
                "reason": f"reaction '{rxn_name}' not found in database"}

    # Merge user overrides onto defaults
    activities = dict(default_activities)
    if user_activities:
        activities.update(user_activities)

    dg_std = td.dg_standard_reaction(conn, rxn_name, temp_c)
    dg_actual = td.delta_gr(conn, rxn_name, temp_c, activities)
    v = td.viability(dg_actual)

    return {
        "available": True,
        "reaction_name": rxn_name,
        "equation": rxn.equation,
        "stoichiometry": rxn.stoichiometry,
        "temp_c": temp_c,
        "dg_standard": dg_std,
        "dg_actual": dg_actual,
        "viability": v,
        "activities_used": activities,
        "adjustment_advice": advice,
    }


# ---------------------------------------------------------------- component dataclass

class Component:
    __slots__ = ("name", "compound_name", "concentration", "units", "role",
                 "confidence", "confidence_source", "uncertainty_note",
                 "source_tag")

    def __init__(self, name, compound_name, concentration, units, role,
                 confidence_obj, uncertainty_note=None, source_tag=None):
        self.name = name
        self.compound_name = compound_name
        self.concentration = concentration
        self.units = units
        self.role = role
        self.confidence = confidence_obj
        self.confidence_source = confidence_obj.source
        self.uncertainty_note = uncertainty_note
        self.source_tag = source_tag or ""

    @property
    def is_critical(self):
        return self.role in CRITICAL_ROLES

    @property
    def uncertainty_flag(self):
        return self.confidence.value < 0.75

    def conc_display(self):
        if self.concentration is None:
            return self.units or ""
        if self.units == "g/L":
            if self.concentration < 0.001:
                return f"{self.concentration * 1e6:.0f} μg/L"
            if self.concentration < 1:
                return f"{self.concentration * 1000:.1f} mg/L"
        return f"{self.concentration} {self.units or ''}".strip()


# ---------------------------------------------------------------- synthesizer

def pick_template(conn, hits, auxotrophies, user_ph, query_tc, user_temp=None):
    """Rank candidate media and return the top one as template.

    Uses the shared rank_candidate_media() function for scoring so that
    identical weights are applied here as in predict_media and phylo_match.

    Returns (template_dict, ranked_list_of_all_candidates) where each entry
    in the list is an info_dict (not a (media_id, info) tuple) to preserve
    backward compatibility with the callers that iterate ranked as dicts.
    """
    ranked_pairs = rank_candidate_media(conn, hits, auxotrophies, query_tc, user_ph)

    # rank_candidate_media returns (media_id, info_dict) pairs; convert to
    # plain dicts with "id" key so existing synthesize_media callers work.
    ranked = []
    for media_id, info in ranked_pairs:
        entry = dict(info)
        entry["id"] = media_id
        ranked.append(entry)

    return (ranked[0] if ranked else None), ranked


def synthesize_template_as_components(template, hits):
    """Turn the template's raw recipe rows into Component objects.

    The template baseline gets one confidence score derived from:
      - phylo identity of the best contributing relative (via hits)
      - MediaDive source baseline (0.95)
    """
    if template is None:
        return []
    best_phylo = confidence.score(
        "phylo_16s", "identity_pct", template["phylo_identity_best"])
    mediadive_conf = confidence.score("mediadive", "curated", None)
    # Template-as-a-whole confidence: min of phylo + mediadive with agreement
    template_conf = confidence.combine(
        "min", [best_phylo, mediadive_conf], agreement_bonus=True,
    )

    components = []
    for r in template["recipe"]:
        name = r["compound"]
        if name == "Distilled water" or name.lower() == "water":
            continue
        role = classify_role(name)
        if role == "water":
            continue
        # Components within the template share the template-level confidence
        # (conservatively — we don't have per-compound provenance in MediaDive).
        # pH buffers and gelling agents are down-weighted slightly.
        conf_val = template_conf.value
        if role == "gelling_agent":
            conf_val = min(conf_val, 0.70)   # agar is replaceable; non-critical

        # Compute final concentration: MediaDive's g_per_L is the per-sub-
        # solution concentration (e.g., 50 g/L for a 10-mL stock), NOT the
        # final medium concentration. Since all MediaDive media are formulated
        # per 1000 mL total, the raw `amount` field (grams) IS the final g/L.
        # Use amount when the unit is grams; fall back to g_per_L for ml/other.
        raw_gpl = r.get("g_per_L")
        raw_amount = r.get("amount")
        raw_unit = r.get("unit") or ""
        if raw_unit.lower() in ("g",) and raw_amount is not None:
            final_conc = raw_amount  # grams in 1L total medium
            final_unit = "g/L"
        elif raw_gpl is not None:
            final_conc = raw_gpl
            final_unit = "g/L"
        else:
            final_conc = raw_amount
            final_unit = raw_unit

        c = Component(
            name=name,
            compound_name=name,
            concentration=final_conc,
            units=final_unit,
            role=role,
            confidence_obj=confidence.ConfidenceScore(
                value=conf_val, source="template",
                rationale=(f"from template '{template['name']}' — "
                           f"{template_conf.rationale}"),
            ),
            source_tag="template",
        )
        components.append(c)
    return components, template_conf


def add_auxotrophy_supplements(components, auxotrophies, template):
    """For each auxotrophy NOT already covered by the template (direct or
    complex), add a Component."""
    # Recompute coverage against the template's recipe
    coverage = coverage_for_medium(template["recipe"], auxotrophies)
    added = []
    for a in auxotrophies:
        name = a["name"]
        status, via = coverage.get(name, ("missing", None))
        if status != "missing":
            continue  # already covered by template
        best_pwy_completeness = a.get("best_completeness") or 0
        # Confidence for supplementing = confidence we need to supplement
        # = confidence that the auxotrophy prediction is correct.
        # gapseq scoring: low completeness → high confidence in the gap.
        gap_prob = max(0, 1 - best_pwy_completeness / 100.0)
        # Higher gap → higher confidence the supplement is needed (invert)
        supp_conf_val = 0.50 + 0.45 * gap_prob
        supp_conf = confidence.ConfidenceScore(
            value=min(0.95, supp_conf_val), source="gapseq",
            rationale=(f"gapseq reports auxotrophy (best biosynthesis pathway "
                       f"{best_pwy_completeness:.0f}%); template '"
                       f"{template['name']}' lacks a direct source for {name}"),
        )
        units = "g/L"
        # Use cofactor-specific concentration if available; fall back to
        # class-level defaults.
        conc = COFACTOR_CONCENTRATION_OVERRIDES.get(name)
        if conc is None:
            conc = VITAMIN_SUPPLEMENT_CONC if a["class"] in ("vitamin", "cofactor") \
                else AA_SUPPLEMENT_CONC
        c = Component(
            name=f"{name} supplement",
            compound_name=name,
            concentration=conc,
            units=units,
            role="auxotrophy_supplement",
            confidence_obj=supp_conf,
            uncertainty_note=(f"partial biosynthesis ({best_pwy_completeness:.0f}%); "
                              f"test 0, 0.5×, 1×, 2× to verify requirement")
            if best_pwy_completeness >= 50 else None,
            source_tag="auxotrophy",
        )
        added.append(c)
        components.append(c)
    return added


def _template_has_metal_salt(template, metal):
    """True if the template's recipe already provides this metal as a salt."""
    patterns = {
        "Fe": [r"FeSO4", r"FeCl", r"Fe\("],
        "Zn": [r"ZnSO4", r"ZnCl"],
        "Mn": [r"MnSO4", r"MnCl"],
        "Cu": [r"CuSO4", r"CuCl"],
        "Co": [r"CoCl", r"CoSO4"],
        "Ni": [r"NiCl", r"NiSO4"],
        "Mg": [r"MgSO4", r"MgCl"],
        "Ca": [r"CaCl", r"CaSO4", r"CaCO3"],
        "K":  [r"K2HPO4", r"KH2PO4", r"KCl", r"KNO3"],
        "Na": [r"NaCl", r"NaSO4", r"Na2SO4"],
    }.get(metal, [])
    pats = [re.compile(p, re.IGNORECASE) for p in patterns]
    # Complex sources also provide metals implicitly at some level
    complex_hint = any(
        src in (r["compound"] or "").lower()
        for r in template["recipe"]
        for src in ("yeast extract", "beef extract", "meat extract",
                    "brain heart infusion", "peptone"))
    for r in template["recipe"]:
        name = r["compound"] or ""
        if any(p.search(name) for p in pats):
            return True, "direct_salt"
    if complex_hint and metal in ("Fe", "Mg", "Ca", "K", "Na"):
        # Complex sources always contribute these ions
        return True, "complex_source"
    return False, None


def add_metal_supplements(components, metal_profile, template):
    """For each high-confidence metal NOT already in the template, add a salt."""
    added = []
    if not metal_profile:
        return added
    for m in metal_profile:
        metal = m["metal"]
        if m["n_binding"] < 5 or m["max_probability"] < 0.75:
            continue  # only high-signal metals
        has, via = _template_has_metal_salt(template, metal)
        if has:
            continue
        supp = METAL_SUPPLEMENT.get(metal)
        if not supp:
            continue
        compound, conc, units = supp
        # Confidence: reuse metal_profile's aggregated confidence
        supp_conf = confidence.ConfidenceScore(
            value=m["confidence"], source="mebipred",
            rationale=(f"MeBiPred: {m['n_binding']} {metal}-binding proteins "
                       f"(max_p={m['max_probability']:.2f}); template "
                       f"'{template['name']}' lacks a direct {metal} salt"),
        )
        note = None
        if m["is_anomaly"]:
            note = m["anomaly_note"]
        c = Component(
            name=f"{metal} trace supplement",
            compound_name=compound,
            concentration=conc,
            units=units,
            role="trace_metal",
            confidence_obj=supp_conf,
            uncertainty_note=note,
            source_tag="mebipred",
        )
        added.append(c)
        components.append(c)
    return added


def add_energy_metabolism_components(components, energy_metabolism):
    """Layer in the chosen electron donor/acceptor set. Skip compounds that
    the template already provides (deduplication)."""
    if not energy_metabolism:
        return []
    key = energy_metabolism.lower().replace("_", "-")
    specs = ENERGY_METABOLISM.get(key)
    if specs is None:
        raise ValueError(
            f"Unknown energy metabolism '{energy_metabolism}'. Options: "
            + ", ".join(sorted(ENERGY_METABOLISM)))

    # Collect existing compound names (lowercase) from the template components
    existing_names = {c.compound_name.lower() for c in components if c.compound_name}
    # Also extract significant words (>4 chars) for fuzzy matching — catches
    # "Na-DL-lactate" matching "Sodium lactate" via the shared word "lactate"
    existing_words = set()
    for n in existing_names:
        existing_words.update(w for w in re.split(r'[\s\-\(\)]+', n) if len(w) > 4)

    added = []
    user_conf = confidence.score("user_supplied", "energy_metabolism", None,
                                 context={"metabolism": key})
    for name, conc, units, role in specs:
        # Check if a similar compound is already in the template
        name_lo = name.lower()
        overlay_words = {w for w in re.split(r'[\s\-\(\)]+', name_lo) if len(w) > 4}
        already_present = (
            any(name_lo in ex or ex in name_lo
                for ex in existing_names if len(ex) > 3)
            or bool(overlay_words & existing_words)  # shared significant word
        )
        if already_present:
            continue  # template already provides this compound

        c = Component(
            name=f"{role} ({key})",
            compound_name=name,
            concentration=conc,
            units=units,
            role="carbon_source" if role == "carbon_source" else role,
            confidence_obj=confidence.ConfidenceScore(
                value=user_conf.value, source="user_supplied",
                rationale=(f"user-specified energy metabolism '{key}'; "
                           f"adding {role} per CLAUDE.md reference table"),
            ),
            source_tag=f"energy:{key}",
        )
        added.append(c)
        components.append(c)
    return added


def compose_overall_confidence(components, thermal_conf, gapseq_version):
    """Recipe-level composite via min+agreement_bonus on critical components only."""
    critical = [c.confidence for c in components if c.is_critical]
    if thermal_conf is not None:
        critical.append(thermal_conf)
    return confidence.combine("min", critical, agreement_bonus=True)


def build_variation_matrix(components):
    """Suggestions for experimentally-test variations of uncertain components."""
    out = []
    for c in components:
        if not c.uncertainty_flag and not c.uncertainty_note:
            continue
        role = c.role
        reason = c.uncertainty_note or f"{c.confidence.value:.0%} confidence"
        if role == "auxotrophy_supplement":
            variant = (f"Test 0×, 0.5×, 1×, 2× {c.compound_name} "
                       f"(0 / {c.concentration/2:.2f} / {c.concentration} / "
                       f"{c.concentration*2:.2f} {c.units})")
        elif role == "trace_metal":
            variant = f"Test with and without {c.compound_name}"
        elif role == "carbon_source":
            variant = f"Test alternative carbon sources alongside {c.compound_name}"
        else:
            variant = "Test variants experimentally"
        out.append((c.name, reason, variant))
    return out


# ---------------------------------------------------------------- persist

def persist_prediction(conn, genome_id, accession, template, components,
                      overall, args):
    conn.executescript(SCHEMA_SQL)
    confidence.populate_source_table(conn)
    now = datetime.utcnow().isoformat(timespec="seconds")
    n_unc = sum(1 for c in components if c.uncertainty_flag)
    cur = conn.execute("""
        INSERT INTO predictions
          (genome_id, input_accession, template_media_id, template_media_name,
           template_media_source_id, overall_confidence, overall_category,
           user_temp, user_ph, user_salinity, energy_metabolism,
           n_components, n_uncertain, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        genome_id, accession,
        template["id"] if template else None,
        template["name"] if template else None,
        template["source_id"] if template else None,
        overall.value, overall.category,
        args.temperature, args.ph, args.salinity,
        args.energy_metabolism,
        len(components), n_unc, None, now,
    ))
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for c in components:
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
        confidence.record(conn, "recipe_component", c.confidence,
                          related_table="recipe_components",
                          related_id=conn.execute(
                              "SELECT last_insert_rowid()").fetchone()[0])
    conn.commit()
    return pid


# ---------------------------------------------------------------- report

def format_report(template, components, overall, variations, thermal_conf,
                  thermal_details, accession, hits, args, biomass,
                  gapseq_version, metal_profile_summary, auxotrophy_count,
                  thermo_result=None, compat_warnings=None,
                  prep_instructions=None, carbon_profile=None,
                  carbon_warnings=None, gas_recommendation=None,
                  format_recommendation=None):
    out = []
    bar = "=" * 80
    tmpl_name = template["name"] if template else "(no template)"
    out.append(bar)
    out.append(f"  SYNTHESIZED RECIPE — derived from template '{tmpl_name}'")
    out.append(f"  Query: {accession}  ({len(hits)} relatives, "
               f"best identity {max(h['identity'] for h in hits):.1f}%)")
    out.append(bar)
    out.append("")
    out.append(f"  Overall Confidence: {overall.category} "
               f"({overall.value:.2f})")
    out.append(f"  → {overall.rationale}")
    out.append("")

    # Thermal provenance
    if thermal_details:
        src_line = ", ".join(f"{k}={v:.0f}°C" if isinstance(v, float)
                             else f"{k}={v}" for k, v in thermal_details.items())
        out.append(f"  Thermal sources: {src_line}")
        out.append(f"  → {thermal_conf.rationale}")
        out.append("")

    # Group components by role for readability
    role_order = [
        ("complex_source",        "Complex nutrient sources"),
        ("base_salt",             "Base salts"),
        ("carbon_source",         "Carbon sources"),
        ("nitrogen_source",       "Nitrogen sources"),
        ("phosphate",             "Phosphate"),
        ("sulfur_source",         "Sulfur"),
        ("trace_metal",           "Trace metals"),
        ("amino_acid",            "Amino acids"),
        ("vitamin",               "Vitamins"),
        ("auxotrophy_supplement", "Auxotrophy supplements"),
        ("electron_donor",        "Electron donor"),
        ("electron_acceptor",     "Electron acceptor"),
        ("buffer",                "Buffers"),
        ("gelling_agent",         "Gelling agent"),
        ("other",                 "Other"),
    ]
    by_role = defaultdict(list)
    for c in components:
        by_role[c.role].append(c)

    out.append("  COMPONENTS:")
    for role, heading in role_order:
        items = by_role.get(role, [])
        if not items:
            continue
        out.append(f"    [{heading}]")
        for c in items:
            conc = c.conc_display()
            flag = " ⚠" if c.uncertainty_flag else ""
            src_tag = f" ({c.source_tag})" if c.source_tag else ""
            out.append(f"      {c.compound_name:40s} {conc:15s}  "
                       f"[{c.confidence.value:.2f}]{flag}{src_tag}")
            if c.source_tag not in ("template", ""):
                # Show rationale for non-template (i.e. layered) components
                out.append(f"          → {c.confidence.rationale}")
            if c.uncertainty_note:
                out.append(f"          → {c.uncertainty_note}")
        out.append("")

    # Carbon source verification
    if carbon_profile or carbon_warnings:
        out.append(bar)
        out.append("  CARBON SOURCE ANALYSIS")
        out.append(bar)
        if carbon_profile:
            top_carbons = sorted(carbon_profile.items(),
                                 key=lambda kv: -kv[1]["max_completeness"])[:10]
            out.append(f"  Organism can utilize {len(carbon_profile)} predicted carbon sources:")
            for c_name, info in top_carbons:
                out.append(f"    ✓ {c_name:20s} ({info['max_completeness']:.0f}% "
                           f"pathway — {info['pathways'][0][:50]})")
        if carbon_warnings:
            out.append("")
            for compound, explanation in carbon_warnings:
                out.append(f"  ⚠ CARBON SOURCE MISMATCH: {compound}")
                out.append(f"    → {explanation}")
                out.append(f"    → Consider replacing with a compatible carbon source")
        out.append("")

    # Gas phase recommendation
    if gas_recommendation:
        out.append(bar)
        out.append("  GAS PHASE RECOMMENDATION")
        out.append(bar)
        gr = gas_recommendation
        out.append(f"  Headspace: {gr['headspace']}")
        out.append(f"    → {gr['rationale']}")
        if gr.get("hydrogenase_blast"):
            out.append(f"  BLAST-confirmed hydrogenases ({len(gr['hydrogenase_blast'])} hits):")
            for h in gr["hydrogenase_blast"][:6]:
                out.append(f"    • {h['type']:7s} Group {h['group']:1s}  "
                           f"{h['gene']:20s}  {h['pident']:>5.1f}%id  "
                           f"bs={h['bitscore']:.0f}")
        if gr["h2_capabilities"]:
            out.append(f"  gapseq H₂ pathways ({len(gr['h2_capabilities'])}):")
            for cap in gr["h2_capabilities"][:5]:
                out.append(f"    • {cap['type']:12s} {cap['completeness']:>5.0f}%  "
                           f"{cap['pathway'][:55]}")
        if gr["is_anaerobe"]:
            out.append(f"  ⚠ STRICT ANAEROBE — all manipulation must be under "
                       f"anoxic conditions (glove box or Hungate technique)")
        out.append("")

    # Physical media format
    if format_recommendation:
        fr = format_recommendation
        out.append(bar)
        out.append("  PHYSICAL FORMAT")
        out.append(bar)
        out.append(f"  Recommended: {fr['primary_format']}  "
                   f"[{fr['confidence'].value:.2f}]")
        out.append(f"    → {fr['primary_detail']}")
        if fr["alternative"]:
            out.append(f"  Alternative: {fr['alternative']}")
        out.append(f"  Solidifying agent: {fr['solidifying_agent']}")
        out.append(f"    → {fr['solidifying_detail']}")
        for w in fr["warnings"]:
            out.append(f"  ⚠ {w}")
        out.append("")

    # Thermodynamic viability section (only when --energy-metabolism given)
    if thermo_result and thermo_result.get("available"):
        tr = thermo_result
        out.append(bar)
        out.append("  THERMODYNAMIC VIABILITY CHECK (Amend & Shock 2001)")
        out.append(bar)
        out.append(f"    Reaction:  {tr['equation']}")
        out.append(f"    Temperature: {tr['temp_c']:.0f}°C")
        out.append(f"    ΔG°r (standard state): {tr['dg_standard']:.2f} kJ/mol")
        # Show activities
        act_parts = []
        for species, val in sorted(tr["activities_used"].items()):
            if species == "H2O(l)" or val == 1.0:
                continue
            act_parts.append(f"{species}={val:.1e}")
        if act_parts:
            out.append(f"    Activities:  {', '.join(act_parts)}")
        out.append(f"    ΔGr (actual):  {tr['dg_actual']:.2f} kJ/mol")
        v = tr["viability"]
        v_label = {"viable": "VIABLE (< -20 kJ/mol)",
                   "marginal": "MARGINAL (-20 to 0 kJ/mol)",
                   "not_viable": "NOT VIABLE (> 0 kJ/mol)"}[v]
        marker = {"viable": "✓", "marginal": "⚠", "not_viable": "✗"}[v]
        out.append(f"    Verdict:   {marker} {v_label}")
        if v in ("marginal", "not_viable"):
            out.append(f"    → {tr['adjustment_advice']}")
        out.append("")
    elif thermo_result and not thermo_result.get("available"):
        out.append(f"\n  Note: thermodynamic viability check not available — "
                   f"{thermo_result['reason']}")
        out.append("")

    # Compatibility warnings block
    if compat_warnings:
        out.append(bar)
        out.append(f"  COMPATIBILITY WARNINGS ({len(compat_warnings)} "
                   f"precipitation risks detected)")
        out.append(bar)
        out.append(compatibility.format_warnings(compat_warnings))
    if prep_instructions:
        out.append(prep_instructions)
        out.append("")

    # Uncertainty flags block
    uncertain = [c for c in components if c.uncertainty_flag]
    if uncertain:
        out.append(f"  ⚠ UNCERTAINTY FLAGS ({len(uncertain)} components <0.75):")
        for c in uncertain:
            out.append(f"    • {c.compound_name} ({c.confidence.value:.2f}) — "
                       f"{c.confidence.rationale}")
        out.append("")

    # Variation matrix
    if variations:
        out.append(f"  EXPERIMENTAL VARIATION MATRIX:")
        for name, reason, variant in variations:
            out.append(f"    • {name}")
            out.append(f"        reason:   {reason}")
            out.append(f"        variants: {variant}")
        out.append("")

    # Provenance
    out.append(bar)
    out.append("  PROVENANCE")
    out.append(bar)
    out.append(f"    Template medium:   {tmpl_name} "
               f"({template['source_id'] if template else '-'})")
    out.append(f"    Phylogenetic match: MediaDive + BacDive via 16S BLAST "
               f"(best {max(h['identity'] for h in hits):.1f}%)")
    out.append(f"    Metabolic analysis: gapseq {gapseq_version or '?'} "
               f"→ {auxotrophy_count} auxotrophy compound(s) required")
    out.append(f"    Environmental:     multi-source thermal inference "
               f"({len(thermal_details)} source(s))")
    if metal_profile_summary:
        out.append(f"    Metal profile:     MeBiPred "
                   f"({metal_profile_summary})")
    out.append(f"    Genome biomass:    {biomass or '?'}")
    if args.energy_metabolism:
        out.append(f"    Energy overlay:    user-specified "
                   f"'{args.energy_metabolism}'")
    if thermo_result and thermo_result.get("available"):
        out.append(f"    Thermo check:      Amend & Shock 2001 "
                   f"({thermo_result['reaction_name']}; "
                   f"ΔGr = {thermo_result['dg_actual']:.1f} kJ/mol "
                   f"→ {thermo_result['viability']})")
    out.append(bar)
    return "\n".join(out)


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(
        description="Synthesize a tailored cultivation recipe from a genome.")
    parser.add_argument("genome")
    parser.add_argument("--accession", required=True)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--ph", type=float, default=None)
    parser.add_argument("--salinity", type=float, default=None)
    parser.add_argument("--top", type=int, default=10,
                        help="relatives to consider for template ranking")
    parser.add_argument("--min-identity", type=float, default=80.0)
    parser.add_argument("--energy-metabolism", default=None,
                        choices=sorted(ENERGY_METABOLISM) + [None],
                        help="electron donor/acceptor overlay")
    parser.add_argument("--template-id", type=int, default=None,
                        help="override auto-picked template media_id")
    parser.add_argument("--activity", action="append", default=[],
                        metavar="SPECIES=VALUE",
                        help="override default activity for a species in the "
                             "thermodynamic viability check, e.g. "
                             "'--activity H2(aq)=1e-5'. May be repeated.")
    parser.add_argument("--simulate-knockout", default=None,
                        help="compound name; rolled back at end")
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args()

    # Parse --activity overrides
    user_activities = {}
    for spec in args.activity:
        if "=" not in spec:
            sys.exit(f"--activity must be 'SPECIES=VALUE', got '{spec}'")
        name, val = spec.split("=", 1)
        user_activities[name.strip()] = float(val.strip())

    if not os.path.exists(args.genome):
        sys.exit(f"genome not found: {args.genome}")

    # Step 1: 16S extraction
    s16 = extract_16s(args.genome)
    if not s16:
        sys.exit("no 16S extracted")

    # Step 2: phylo match
    hits = run_blast(s16, top_n=args.top, min_identity=args.min_identity)
    if not hits:
        sys.exit("no BLAST hits")

    conn = sqlite3.connect(DB)
    try:
        # Step 3: look up genome + its predictions
        genome_row = get_genome_id_for_accession(conn, args.accession)
        if genome_row is None:
            sys.exit(f"accession {args.accession} not found in genomes table — "
                     "run gapseq + load_gapseq.py first")
        genome_id, _, biomass, n_genes, gapseq_version = genome_row

        # Simulate knockout in a transaction
        in_txn = False
        if args.simulate_knockout:
            in_txn = True
            conn.execute("BEGIN")
            row = conn.execute("""
                SELECT name, pathway_name_pattern FROM essential_compounds
                 WHERE lower(name) = lower(?)
                    OR lower(name) LIKE lower(?) || ' (%'
                    OR lower(name) LIKE lower(?) || '%'
                LIMIT 1
            """, (args.simulate_knockout,) * 3).fetchone()
            if row is None:
                sys.exit(f"--simulate-knockout '{args.simulate_knockout}' not "
                         f"found in essential_compounds")
            canonical_name, pattern = row
            n = conn.execute("""
                UPDATE genome_pathways SET predicted=0, completeness=20
                 WHERE genome_id=? AND lower(pathway_name) LIKE lower(?)
                   AND lower(pathway_name) LIKE '%biosynthesis%'
            """, (genome_id, pattern)).rowcount
            print(f"  [simulation] knocked out {n} biosynthesis pathways for "
                  f"'{canonical_name}'", file=sys.stderr)

        auxotrophies = get_auxotrophies(conn, genome_id)
        transporters = get_transporter_summary(conn, genome_id)
        metal_profile = get_metal_profile(conn, genome_id)

        # Step 4: multi-source thermal
        query_tc, thermal_conf, effective_temp, thermal_details = \
            infer_thermal_multisource(conn, hits, genome_id=genome_id,
                                      user_temp=args.temperature)

        # Step 5: pick template
        if args.template_id:
            # User-supplied template override
            row = conn.execute("SELECT id, source_id, name, min_ph, max_ph "
                               "FROM media WHERE id=?",
                               (args.template_id,)).fetchone()
            if not row:
                sys.exit(f"template_id {args.template_id} not found")
            recipe = get_media_recipe(conn, row[0])
            template = {"id": row[0], "source_id": row[1], "name": row[2],
                        "min_ph": row[3], "max_ph": row[4], "recipe": recipe,
                        "phylo_identity_best": max(h["identity"] for h in hits),
                        "coverage": coverage_for_medium(recipe, auxotrophies),
                        "score": None, "sources": {}}
        else:
            template, _ranked = pick_template(
                conn, hits, auxotrophies, args.ph, query_tc, user_temp=args.temperature)
            if template is None:
                sys.exit("no template candidate — cannot synthesize")

        # Step 6: build components
        components, template_conf = synthesize_template_as_components(template, hits)
        added_aux = add_auxotrophy_supplements(components, auxotrophies, template)
        added_metal = add_metal_supplements(components, metal_profile, template)
        added_energy = add_energy_metabolism_components(
            components, args.energy_metabolism)

        # Step 6b: carbon source verification + gas phase recommendation
        carbon_profile = carbon_and_gas.get_carbon_profile(conn, genome_id) if genome_id else {}
        gas_recommendation = carbon_and_gas.get_gas_phase_recommendation(
            conn, genome_id) if genome_id else None

        # Check if template carbon sources are compatible with the organism
        carbon_warnings = []
        for c in components:
            if c.role == "carbon_source":
                compat, explanation = carbon_and_gas.verify_carbon_source(
                    conn, genome_id, c.compound_name)
                if not compat:
                    carbon_warnings.append((c.compound_name, explanation))

        # Step 6b2: physical media format prediction
        format_recommendation = media_format.predict_format(
            conn, genome_id,
            temperature=args.temperature or effective_temp,
            ph=args.ph,
        ) if genome_id else None

        # Step 6c: thermodynamic viability check (if --energy-metabolism set)
        thermo_result = None
        if args.energy_metabolism:
            growth_temp = effective_temp if effective_temp else 25.0
            thermo_result = check_thermodynamic_viability(
                conn, args.energy_metabolism, growth_temp,
                user_activities=user_activities if user_activities else None,
            )
            # If ΔGr > 0 (not viable), add a warning component that drags
            # down the overall confidence
            if thermo_result.get("available") and thermo_result["viability"] == "not_viable":
                components.append(Component(
                    name="thermodynamic viability WARNING",
                    compound_name="(reaction not viable at conditions)",
                    concentration=None, units=None,
                    role="electron_acceptor",  # critical role → drags min()
                    confidence_obj=confidence.ConfidenceScore(
                        value=0.25, source="amend_shock",
                        rationale=(f"ΔGr = {thermo_result['dg_actual']:.1f} kJ/mol "
                                   f"> 0 at {growth_temp:.0f}°C — reaction is "
                                   f"thermodynamically NOT VIABLE"),
                    ),
                    uncertainty_note=(f"CRITICAL: {thermo_result['adjustment_advice']}"),
                    source_tag="thermodynamics",
                ))
            elif thermo_result.get("available") and thermo_result["viability"] == "marginal":
                components.append(Component(
                    name="thermodynamic viability WARNING",
                    compound_name="(reaction marginally viable)",
                    concentration=None, units=None,
                    role="other",  # non-critical but flagged
                    confidence_obj=confidence.ConfidenceScore(
                        value=0.60, source="amend_shock",
                        rationale=(f"ΔGr = {thermo_result['dg_actual']:.1f} kJ/mol "
                                   f"(marginal: -20 to 0) at {growth_temp:.0f}°C"),
                    ),
                    uncertainty_note=(f"MARGINAL: {thermo_result['adjustment_advice']}"),
                    source_tag="thermodynamics",
                ))

        # Step 7: overall confidence
        overall = compose_overall_confidence(components, thermal_conf, gapseq_version)

        # If thermodynamically not viable, apply a further -0.15 penalty
        if (thermo_result and thermo_result.get("available")
                and thermo_result["viability"] == "not_viable"):
            overall = confidence.ConfidenceScore(
                value=max(0.10, overall.value - 0.15),
                source=overall.source,
                rationale=(overall.rationale +
                           f" MINUS 0.15 for NOT VIABLE thermodynamics"),
                context=overall.context,
            )

        # Step 8: variation matrix
        variations = build_variation_matrix(components)

        # Step 8b: compatibility check (Tier A — rule-based precipitation scan)
        recipe_ph = args.ph if args.ph is not None else 7.0
        is_sulfidogenic = (args.energy_metabolism and
                           "sulfat" in (args.energy_metabolism or "").lower())
        compound_names_for_compat = [c.compound_name for c in components
                                     if c.compound_name]
        compat_warnings = compatibility.check_compatibility(
            conn, compound_names_for_compat,
            ph=recipe_ph,
            is_sulfidogenic=is_sulfidogenic,
        )
        compat_penalty = compatibility.confidence_penalty(compat_warnings)
        if compat_penalty > 0:
            overall = confidence.ConfidenceScore(
                value=max(0.10, overall.value - compat_penalty),
                source=overall.source,
                rationale=(overall.rationale +
                           f" MINUS {compat_penalty:.2f} for precipitation risk "
                           f"({len(compat_warnings)} warnings)"),
                context=overall.context,
            )
        prep_instructions = compatibility.generate_prep_instructions(
            compat_warnings, compound_names_for_compat)

        # Step 9: persist
        pid = None
        if not args.no_persist:
            pid = persist_prediction(conn, genome_id, args.accession, template,
                                     components, overall, args)

        # Step 10: print report
        metal_summary = None
        if metal_profile:
            strong = [m["metal"] for m in metal_profile
                      if m["n_binding"] >= 5 and m["max_probability"] >= 0.75]
            metal_summary = f"{len(strong)} strong metals: " + ", ".join(strong)
        print(format_report(
            template, components, overall, variations, thermal_conf,
            thermal_details, args.accession, hits, args, biomass,
            gapseq_version, metal_summary, len(auxotrophies),
            thermo_result=thermo_result,
            compat_warnings=compat_warnings,
            prep_instructions=prep_instructions,
            carbon_profile=carbon_profile,
            carbon_warnings=carbon_warnings,
            gas_recommendation=gas_recommendation,
            format_recommendation=format_recommendation))

        if pid:
            print(f"\n  → persisted as prediction id={pid}")
        if added_aux or added_metal or added_energy:
            print(f"  → layered {len(added_aux)} auxotrophy + "
                  f"{len(added_metal)} metal + {len(added_energy)} "
                  f"energy-metabolism components onto template baseline")

        # Roll back simulation
        if in_txn:
            conn.execute("ROLLBACK")
            print("\n  [simulation] rolled back — database unchanged.",
                  file=sys.stderr)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
