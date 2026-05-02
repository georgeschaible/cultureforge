"""Recipe comparison engine (Phase 2d Task 4).

Compares a CultureForge Recipe against MediaDive published media — both for
direct-match cases (when the organism has a BacDive entry) and for functional-
neighbor cases (when the organism's media must be inferred from similar
organisms).

Output: structured ComparisonReport with critical/important/minor differences.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from mediadive_client import get_medium_ingredients


# ---------------------------------------------------------------------------
# Compound name normalization
# ---------------------------------------------------------------------------
# MediaDive uses notation like "MgSO4 x 7 H2O" while CultureForge uses
# "MgSO4·7H2O". For comparison purposes we normalize to a canonical form.

_NORM_TABLE = {
    # Major salts
    "MgSO4·7H2O": ["mgso4", "magnesium sulfate"],
    "CaCl2·2H2O": ["cacl2", "calcium chloride"],
    "MgCl2·6H2O": ["mgcl2", "magnesium chloride"],
    "NaCl":       ["nacl", "sodium chloride"],
    "KCl":        ["kcl", "potassium chloride"],
    "K2HPO4":     ["k2hpo4", "potassium phosphate dibasic", "dipotassium phosphate"],
    "KH2PO4":     ["kh2po4", "potassium phosphate monobasic", "monopotassium phosphate"],
    "NaHCO3":     ["nahco3", "sodium bicarbonate", "sodium hydrogen carbonate"],
    "Na2SO4":     ["na2so4", "sodium sulfate"],
    "NH4Cl":      ["nh4cl", "ammonium chloride"],
    "(NH4)2SO4":  ["(nh4)2so4", "ammonium sulfate"],
    "KNO3":       ["kno3", "potassium nitrate"],
    # Iron — both ferric and ferrous forms
    "FeSO4·7H2O": ["feso4", "ferrous sulfate", "iron(ii) sulfate", "iron sulfate"],
    "FeCl2·4H2O": ["fecl2", "ferrous chloride", "iron(ii) chloride"],
    "FeCl3·6H2O": ["fecl3", "ferric chloride", "iron(iii) chloride"],
    "Ferric citrate": ["fe(iii) citrate", "ferric citrate", "iron citrate"],
    # Reducing agents and donors/acceptors
    "Na2S·9H2O":  ["na2s", "sodium sulfide"],
    "L-Cysteine·HCl": ["cysteine", "l-cysteine"],
    "Na2S2O3·5H2O": ["thiosulfate", "na2s2o3"],
    "Resazurin":  ["resazurin", "sodium resazurin"],
    # Carbon/N sources
    "Yeast extract": ["yeast extract"],
    "Peptone":    ["peptone", "tryptone", "soy peptone", "casein peptone", "casitone"],
    "Glucose":    ["glucose", "d-glucose", "dextrose"],
    "Fructose":   ["fructose"],
    "Sodium DL-lactate": ["lactate", "sodium lactate", "na-lactate"],
    "Sodium acetate": ["acetate", "sodium acetate"],
    # SL-10 trace metal components (full list per DSMZ 320)
    "FeCl2 (SL-10 component)": ["fecl2 x 4 h2o", "fecl2·4h2o"],
    "ZnCl2":      ["zncl2", "zinc chloride"],
    "ZnSO4·7H2O": ["znso4", "zinc sulfate"],
    "MnCl2·4H2O": ["mncl2", "manganese chloride"],
    "MnSO4·H2O":  ["mnso4", "manganese sulfate"],
    "H3BO3":      ["h3bo3", "boric acid"],
    "CoCl2·6H2O": ["cocl2", "cobalt chloride"],
    "CoSO4·7H2O": ["coso4", "cobalt sulfate"],
    "CuCl2·2H2O": ["cucl2", "copper chloride"],
    "CuSO4·5H2O": ["cuso4", "copper sulfate"],
    "NiCl2·6H2O": ["nicl2", "nickel chloride"],
    "Na2MoO4·2H2O": ["na2moo4", "sodium molybdate", "molybdate"],
    "Na2SeO3":    ["na2seo3", "sodium selenite", "selenite"],
    "Na2WO4·2H2O": ["na2wo4", "sodium tungstate", "tungstate"],
    "Nitrilotriacetic acid": ["nitrilotriacetic acid", "nta"],
    # Wolin's vitamin components (full list per DSMZ 141)
    "Cyanocobalamin": ["b12", "cobalamin", "vitamin b12", "cyanocobalamin"],
    "Biotin":     ["biotin"],
    "Thiamine HCl": ["thiamine"],
    "Riboflavin": ["riboflavin"],
    "Folic acid": ["folic acid", "folate"],
    "Pyridoxine HCl": ["pyridoxine"],
    "Ca-D-pantothenate": ["pantothenate", "pantothenic acid", "calcium d-(+)-pantothenate"],
    "Nicotinic acid": ["nicotinic acid", "niacinamide", "niacin", "nicotinamide"],
    "p-Aminobenzoic acid": ["p-aminobenzoic", "aminobenzoic acid", "paba"],
    "Lipoic acid": ["lipoic acid", "thioctic acid"],
}


# Trivial ingredients excluded from comparison (universal solvents, agar, etc.)
_SKIP_INGREDIENTS = {
    "distilled water", "water", "h2o", "double-distilled water", "dh2o",
    "deionized water", "tap water", "agar", "agarose", "gelrite", "gellan gum",
    "phytagel",
}


# Composite stock solutions that the CF composer uses as single-line ingredients.
# When comparing against MediaDive references (which list individual components),
# these solutions are conceptually "expanded" to their canonical components so
# the comparison credits CF for having e.g. iron + zinc + manganese.
# Full SL-10 trace element list per DSMZ Medium 320; Wolin's vitamin list per
# DSMZ Medium 141. Both stocks are widely used as composite ingredients in
# CultureForge recipes — expanding them lets the comparison engine credit CF
# for the individual trace metals / vitamins that DSMZ media list separately.
_SL10_COMPONENTS = [
    "FeCl2 (SL-10 component)",  # FeCl2·4H2O — primary iron in SL-10
    "FeSO4·7H2O",                # alternative iron form some media use
    "ZnCl2",                     # SL-10 lists ZnCl2; some media use ZnSO4·7H2O
    "ZnSO4·7H2O",
    "MnCl2·4H2O",
    "H3BO3",
    "CoCl2·6H2O",
    "CuCl2·2H2O",
    "NiCl2·6H2O",
    "Na2MoO4·2H2O",
]
_WOLIN_VITAMIN_COMPONENTS = [
    "Cyanocobalamin", "Biotin", "Thiamine HCl", "Riboflavin",
    "Folic acid", "Pyridoxine HCl", "Ca-D-pantothenate",
    "Nicotinic acid", "p-Aminobenzoic acid", "Lipoic acid",
]

_COMPOSITE_EXPANSIONS = {
    "sl-10 trace metal solution": _SL10_COMPONENTS,
    "trace element solution":     _SL10_COMPONENTS,
    "trace metal solution":       _SL10_COMPONENTS,
    "wolin's vitamin solution":   _WOLIN_VITAMIN_COMPONENTS,
    "vitamin solution":           _WOLIN_VITAMIN_COMPONENTS,
    "wolin vitamin":              _WOLIN_VITAMIN_COMPONENTS,
}


def _expand_composites(canon_set: set) -> set:
    """If `canon_set` contains composite stock solutions, replace them with
    their canonical component ingredients. The composite name itself is
    dropped — otherwise it would show up as a `cf_only` mismatch against
    references that list the components individually.
    """
    expanded = set()
    for name in canon_set:
        replaced = False
        for prefix, components in _COMPOSITE_EXPANSIONS.items():
            if prefix in name.lower():
                expanded.update(components)
                replaced = True
                break
        if not replaced:
            expanded.add(name)
    return expanded


def normalize_compound_name(raw: str) -> str:
    """Map a raw MediaDive or CF ingredient name to a canonical form.

    Returns the original (lowercased, hydrate-stripped) name when no canonical
    match is found — this keeps the comparison conservative (unknown ingredients
    are still compared by string equality). Returns empty string for trivial
    ingredients (water, agar) that shouldn't count in the comparison.
    """
    if not raw:
        return ""
    # Strip MediaDive's " x N H2O" hydrate notation and CultureForge's "·NH2O"
    cleaned = re.sub(r"\s*x\s*\d+\s*H2O", "", raw, flags=re.I)
    cleaned = re.sub(r"·\d+H2O", "", cleaned)
    cleaned = cleaned.strip().lower()
    if cleaned in _SKIP_INGREDIENTS:
        return ""
    for canonical, aliases in _NORM_TABLE.items():
        if any(a in cleaned for a in aliases):
            return canonical
    return cleaned


# ---------------------------------------------------------------------------
# Comparison data structures
# ---------------------------------------------------------------------------

@dataclass
class IngredientDiff:
    severity: str            # "critical" | "important" | "minor"
    kind: str                # "shared" | "cf_only" | "ref_only" | "concentration_disagree"
    ingredient: str
    cf_value: Optional[str] = None
    ref_value: Optional[str] = None
    note: str = ""


@dataclass
class ConditionMismatch:
    """Critical condition disagreement between CF recipe and reference media."""
    field: str          # "temperature" | "pH" | "atmosphere"
    cf_value: str
    ref_value: str
    severity: str = "critical"  # always critical per Phase 2d spec
    note: str = ""


@dataclass
class ComparisonReport:
    cf_recipe_genome_id: int
    cf_species: str
    relationship: str        # "direct" | "functional_neighbor"
    n_published_media: int
    matched_published_ids: List[str] = field(default_factory=list)
    diffs: List[IngredientDiff] = field(default_factory=list)
    condition_mismatches: List[ConditionMismatch] = field(default_factory=list)
    overall_agreement: float = 0.0
    rationale: str = ""
    scoring_method: str = ""  # "jaccard" | "frequency_weighted"


# ---------------------------------------------------------------------------
# Reference profile aggregation
# ---------------------------------------------------------------------------

def aggregate_published_recipes(medium_ids: List[str],
                                  conn: sqlite3.Connection) -> Dict[str, dict]:
    """Aggregate ingredients across multiple published media for a single
    reference profile. Returns: {canonical_name → {n, frequency, examples}}.

    'frequency' is the fraction of media that include the ingredient. The
    comparison logic treats high-frequency ingredients (in most references)
    as more important than low-frequency ones.
    """
    by_canon: Dict[str, dict] = {}
    n_media = 0
    for mid in medium_ids:
        ingredients = get_medium_ingredients(mid, conn)
        n_media += 1
        seen_in_this: set = set()
        for ing in ingredients:
            canon = normalize_compound_name(ing.get("compound", ""))
            if not canon or canon in seen_in_this:
                continue
            seen_in_this.add(canon)
            by_canon.setdefault(canon, {
                "n": 0, "raw_names": set(), "amounts": [], "media_with": []
            })
            by_canon[canon]["n"] += 1
            by_canon[canon]["raw_names"].add(ing.get("compound"))
            if ing.get("amount") is not None:
                by_canon[canon]["amounts"].append(float(ing["amount"]))
            by_canon[canon]["media_with"].append(mid)
    if n_media == 0:
        return {}
    for canon, info in by_canon.items():
        info["frequency"] = info["n"] / n_media
        info["raw_names"] = sorted(info["raw_names"])
        if info["amounts"]:
            info["min"] = min(info["amounts"])
            info["max"] = max(info["amounts"])
            info["median"] = sorted(info["amounts"])[len(info["amounts"]) // 2]
    return by_canon


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

# Severity classification helpers
_CRITICAL_CATEGORIES = {"electron_donor", "electron_acceptor", "gas_phase"}
_IMPORTANT_CATEGORIES = {"carbon_source", "nitrogen_source", "reducing_agent",
                          "buffer"}


def _severity_for_category(category: str, kind: str) -> str:
    """Critical for missing donors/acceptors/atmosphere. Important for missing
    carbon/N/buffer. Minor otherwise."""
    if category in _CRITICAL_CATEGORIES and kind in ("ref_only",):
        return "critical"
    if category in _IMPORTANT_CATEGORIES:
        return "important"
    return "minor"


# Genus reclassifications (mirrors data/build_phase2d_caches.py / derive_recipe_context.py)
_GENUS_SYNONYMS_FOR_BD = {
    "Methanococcus jannaschii": "Methanocaldococcus jannaschii",
    "Lactobacillus plantarum": "Lactiplantibacillus plantarum",
    "Desulfovibrio vulgaris": "Nitratidesulfovibrio vulgaris",
}


def _parse_ph_string(s) -> Optional[float]:
    """Parse pH from strings like '6.8-7.2', '6.5', '5.5 to 7.0'. Range → midpoint."""
    s = str(s).strip()
    rng = re.search(r"(\d+\.?\d*)\s*(?:-|–|to)\s*(\d+\.?\d*)", s)
    if rng:
        return (float(rng.group(1)) + float(rng.group(2))) / 2.0
    single = re.search(r"(\d+\.?\d*)", s)
    return float(single.group(1)) if single else None


def _bacdive_culture_ph(strain: dict) -> Optional[float]:
    """Extract a single representative culture pH from a BacDive strain record.

    BacDive's 'Culture and growth conditions / culture pH' is a list (or dict)
    of entries with 'type' (optimum / growth / minimum / maximum) and
    'ability' (positive / no / negative). Prefer optimum-positive over
    growth-positive over any positive entry. Range strings parsed to midpoint.
    """
    cgc = strain.get("Culture and growth conditions", {}) or {}
    field = cgc.get("culture pH") or cgc.get("pH")
    if field is None:
        return None
    entries = field if isinstance(field, list) else [field]

    def _positive(e):
        return isinstance(e, dict) and e.get("ability") != "no"

    for desired_type in ("optimum", "growth"):
        for e in entries:
            if not _positive(e):
                continue
            if e.get("type") == desired_type:
                v = _parse_ph_string(e.get("pH", ""))
                if v is not None:
                    return v
    # Last resort: any positive entry with a parseable pH
    for e in entries:
        if not _positive(e):
            continue
        v = _parse_ph_string(e.get("pH", ""))
        if v is not None:
            return v
    return None


def _lookup_bacdive_ph(conn: sqlite3.Connection, species: str) -> Optional[float]:
    """Median culture-pH for a species from bacdive_cache (G.3 fallback).

    Tries the species name directly, then a genus-reclassification synonym,
    then the Candidatus-stripped name. Returns None if nothing matches or
    no parseable pH found.
    """
    if not species:
        return None
    sp_clean = species.split(" subsp.")[0].split(" str.")[0].strip()
    candidates = [sp_clean]
    if sp_clean in _GENUS_SYNONYMS_FOR_BD:
        candidates.append(_GENUS_SYNONYMS_FOR_BD[sp_clean])
    if sp_clean.startswith("Candidatus "):
        candidates.append(sp_clean[len("Candidatus "):])

    for query_name in candidates:
        rows = conn.execute(
            "SELECT response_json FROM bacdive_cache WHERE species_name = ? LIMIT 20",
            (query_name,)
        ).fetchall()
        phs: list = []
        for (rj,) in rows:
            try:
                v = _bacdive_culture_ph(json.loads(rj))
                if v is not None:
                    phs.append(v)
            except Exception:
                continue
        if phs:
            phs.sort()
            return phs[len(phs) // 2]
    return None


def _bacdive_oxygen_category(strain: dict) -> Optional[str]:
    """Map a BacDive 'oxygen tolerance' record to one of:
    'aerobic', 'anaerobic', 'microaerobic', 'facultative'. Returns None when
    the field is missing or unparseable.
    """
    phys = strain.get("Physiology and metabolism", {}) or {}
    ox = phys.get("oxygen tolerance")
    if ox is None:
        return None
    entries = ox if isinstance(ox, list) else [ox]
    label = None
    for e in entries:
        if isinstance(e, dict):
            label = e.get("oxygen tolerance") or label
            if label:
                break
        elif isinstance(e, str):
            label = e
            break
    if not label:
        return None
    low = str(label).lower()
    # Order matters: "anaerobe" CONTAINS "aerobe" as substring, so check the
    # more specific anaerobic / microaerophile / facultative tokens first.
    if "facultative" in low:
        return "facultative"
    if "microaerophil" in low or "microaerobic" in low:
        return "microaerobic"
    if "anaerobe" in low or "anaerobic" in low:
        return "anaerobic"
    if "aerobe" in low or "aerobic" in low:
        return "aerobic"
    return None


def _lookup_bacdive_atmosphere(conn: sqlite3.Connection, species: str) -> Tuple[Optional[str], int, int]:
    """Find the majority oxygen-category for a species from bacdive_cache.

    Returns (majority_category, n_with_signal, n_strains_queried). Uses the
    same synonym fallback chain as `_lookup_bacdive_ph`.
    """
    if not species:
        return None, 0, 0
    sp_clean = species.split(" subsp.")[0].split(" str.")[0].strip()
    candidates = [sp_clean]
    if sp_clean in _GENUS_SYNONYMS_FOR_BD:
        candidates.append(_GENUS_SYNONYMS_FOR_BD[sp_clean])
    if sp_clean.startswith("Candidatus "):
        candidates.append(sp_clean[len("Candidatus "):])

    for query_name in candidates:
        rows = conn.execute(
            "SELECT response_json FROM bacdive_cache WHERE species_name = ? LIMIT 50",
            (query_name,)
        ).fetchall()
        cats: list = []
        for (rj,) in rows:
            try:
                cat = _bacdive_oxygen_category(json.loads(rj))
                if cat:
                    cats.append(cat)
            except Exception:
                continue
        if cats:
            from collections import Counter
            counter = Counter(cats)
            majority, _ = counter.most_common(1)[0]
            return majority, len(cats), len(rows)
    return None, 0, 0


def _cf_atmosphere_category(cf_gas: dict) -> str:
    """Map a CF gas-phase composition dict to a single category label."""
    if not cf_gas:
        return "anaerobic"  # closed bottle, no specific gas
    has_o2 = any(g in cf_gas for g in ("O2", "air"))
    has_h2 = "H2" in cf_gas
    has_ch4 = "CH4" in cf_gas
    # Phase 3.5: methanotroph atmosphere is its own category — air + methane
    # together indicates aerobic methanotrophy, distinct from plain aerobic
    # cultivation (no methane substrate) or anaerobic methanogen H2/CO2.
    if has_ch4 and has_o2:
        return "methanotroph"
    # Phase 3.6: ANME atmosphere — CH4 substrate WITHOUT O2 (anaerobic methane
    # oxidation coupled to alternative electron acceptor in liquid phase).
    if has_ch4 and not has_o2:
        return "anme"
    if has_o2:
        # Microaerobic when O2 partial pressure is sub-atmospheric (informative
        # heuristic: any explicit O2 < 10% indicates microaerobic intent).
        for k, v in cf_gas.items():
            if k in ("O2",) and isinstance(v, (int, float)) and 0 < v < 0.10:
                return "microaerobic"
        return "aerobic"
    if has_h2:
        return "anaerobic"  # H2/CO2 is anaerobic
    return "anaerobic"


def _check_cultivation_conditions(recipe, medium_ids: List[str],
                                   conn: sqlite3.Connection,
                                   relationship: str,
                                   genome_id: int) -> List[ConditionMismatch]:
    """Compare CF recipe cultivation conditions against expected conditions.

    Three checks per Phase 2d Fix #3:
      - Temperature: |CF - expected| > 15°C → mismatch
      - pH:          |CF - expected| > 2 units → mismatch
      - Atmosphere:  CF gas phase incompatible with reference signal → mismatch

    "Expected" conditions come from two sources, in priority:
      (1) the matched-species TEMPURA / organisms-table optimal_temp + optimal_ph
          (catches functional-neighbor cases where the recipe matches the
          neighbor media but is wrong for the actual target organism — the
          Picrophilus diagnostic case)
      (2) the reference media's pH range (mediadive_cache.min_pH / max_pH)
          + matched-strain BacDive culture-temp records (direct-match cases)

    Each mismatch deducts 0.20 from the agreement score (handled by caller).
    """
    mismatches: List[ConditionMismatch] = []
    if recipe.conditions is None:
        return mismatches
    cf_t = recipe.conditions.temperature_c
    cf_ph = recipe.conditions.ph
    cf_gas = recipe.gas_phase.composition if recipe.gas_phase else {}
    sp = ""  # cleaned species name; populated below, used by all checks

    # ----- (1) Target-organism expected conditions from TEMPURA / organisms -----
    # Look up the target species' optimal_temp / optimal_ph via species LIKE
    # match (genus-level fallback when species not in TEMPURA).
    target_sp_row = conn.execute(
        "SELECT COALESCE(o.species, g.notes, g.accession) FROM genomes g "
        "LEFT JOIN organisms o ON o.id = g.organism_id WHERE g.id = ?",
        (genome_id,)
    ).fetchone()
    if target_sp_row and target_sp_row[0]:
        sp = target_sp_row[0]
        for prefix in ("Validation organism: ", "Blind validation: ", "Blind v2: "):
            sp = sp.replace(prefix, "")
        sp = sp.replace("_", " ").split(" subsp.")[0].split(" str.")[0].strip()
        # Try species exact, then genus-reclassification synonym, then genus-only fallback.
        # Genus-only fallback can be misleading when a sister species has very
        # different conditions (e.g., Methanococcus aeolicus mesophile being
        # used as a proxy for Methanocaldococcus jannaschii hyperthermophile);
        # the synonym tier prevents that for the curated cases.
        rows = conn.execute(
            "SELECT optimal_temp, optimal_ph, min_temp, max_temp FROM organisms "
            "WHERE species = ? AND optimal_temp IS NOT NULL LIMIT 1",
            (sp,)
        ).fetchone()
        if not rows and sp in _GENUS_SYNONYMS_FOR_BD:
            rows = conn.execute(
                "SELECT optimal_temp, optimal_ph, min_temp, max_temp FROM organisms "
                "WHERE species = ? AND optimal_temp IS NOT NULL LIMIT 1",
                (_GENUS_SYNONYMS_FOR_BD[sp],)
            ).fetchone()
        if not rows:
            genus = sp.split()[0] if sp else ""
            if genus:
                rows = conn.execute(
                    "SELECT optimal_temp, optimal_ph, min_temp, max_temp FROM organisms "
                    "WHERE species LIKE ? AND optimal_temp IS NOT NULL LIMIT 1",
                    (f"{genus} %",)
                ).fetchone()
        if rows:
            exp_t, exp_ph, exp_mn, exp_mx = rows
            if exp_t is not None and abs(cf_t - exp_t) > 15.0:
                mismatches.append(ConditionMismatch(
                    field="temperature",
                    cf_value=f"{cf_t:.0f}°C",
                    ref_value=f"~{exp_t:.0f}°C (TEMPURA optimum)",
                    note=f"CF recipe T={cf_t:.0f}°C is {abs(cf_t - exp_t):.0f}°C "
                         f"off the TEMPURA-expected optimum for {sp.split()[0]} sp.",
                ))
        else:
            exp_t, exp_ph = None, None

        # G.3: When TEMPURA lacks optimal_ph for this species, fall back to
        # BacDive culture-pH records (extracted from bacdive_cache).
        ph_source = "TEMPURA optimum"
        if exp_ph is None:
            bd_ph = _lookup_bacdive_ph(conn, sp)
            if bd_ph is not None:
                exp_ph = bd_ph
                ph_source = "BacDive culture pH"

        if exp_ph is not None and abs(cf_ph - exp_ph) > 2.0:
            mismatches.append(ConditionMismatch(
                field="pH",
                cf_value=f"{cf_ph:.1f}",
                ref_value=f"~{exp_ph:.1f} ({ph_source})",
                note=f"CF recipe pH {cf_ph:.1f} is {abs(cf_ph - exp_ph):.1f} units "
                     f"off {ph_source} for {sp.split()[0]} sp.",
            ))

    # Aggregate reference pH range across media (from mediadive_cache.min_pH/max_pH)
    ref_phs: list = []
    ref_names_lower: list = []
    for mid in medium_ids:
        row = conn.execute(
            "SELECT min_pH, max_pH, medium_name FROM mediadive_cache WHERE medium_id = ?",
            (str(mid),)
        ).fetchone()
        if row:
            mn, mx, name = row
            if mn is not None:
                ref_phs.append(float(mn))
            if mx is not None:
                ref_phs.append(float(mx))
            if name:
                ref_names_lower.append(name.lower())
    # pH check
    if ref_phs:
        ref_lo, ref_hi = min(ref_phs), max(ref_phs)
        # Allow CF pH to fall within the reference range, expanded by ±1 unit tolerance
        if cf_ph < ref_lo - 1 or cf_ph > ref_hi + 1:
            diff = max(abs(cf_ph - ref_lo), abs(cf_ph - ref_hi))
            if diff > 2.0:
                mismatches.append(ConditionMismatch(
                    field="pH",
                    cf_value=f"{cf_ph:.1f}",
                    ref_value=f"{ref_lo:.1f}-{ref_hi:.1f}",
                    note=f"CF recipe pH {cf_ph:.1f} is {diff:.1f} units outside the reference range",
                ))

    # Temperature: extract from BacDive culture-temp records for matched strains
    # (medium JSONs don't carry temperature directly).
    ref_temps: list = []
    bds = conn.execute(
        "SELECT bacdive_id FROM organism_to_published_media "
        "WHERE cultureforge_genome_id = ? AND relationship = 'direct'",
        (genome_id,)
    ).fetchall()
    for (bid,) in bds:
        row = conn.execute(
            "SELECT response_json FROM bacdive_cache WHERE bacdive_id = ?", (bid,)
        ).fetchone()
        if not row:
            continue
        try:
            strain = json.loads(row[0])
        except Exception:
            continue
        cgc = strain.get("Culture and growth conditions", {}) or {}
        temp_field = cgc.get("culture temp")
        temps = temp_field if isinstance(temp_field, list) else (
            [temp_field] if isinstance(temp_field, dict) else [])
        for t in temps:
            if not isinstance(t, dict):
                continue
            v = t.get("temperature")
            try:
                if isinstance(v, str) and "-" in v:
                    parts = v.replace("°C", "").split("-")
                    ref_temps.append(float(parts[0]))
                    ref_temps.append(float(parts[1]))
                elif v is not None:
                    ref_temps.append(float(v))
            except (TypeError, ValueError):
                pass
    if ref_temps:
        ref_lo, ref_hi = min(ref_temps), max(ref_temps)
        if cf_t < ref_lo - 5 or cf_t > ref_hi + 5:
            diff = max(abs(cf_t - ref_lo), abs(cf_t - ref_hi))
            if diff > 15.0:
                mismatches.append(ConditionMismatch(
                    field="temperature",
                    cf_value=f"{cf_t:.0f}°C",
                    ref_value=f"{ref_lo:.0f}-{ref_hi:.0f}°C",
                    note=f"CF recipe T={cf_t:.0f}°C is {diff:.0f}°C outside reference range",
                ))

    # Atmosphere check — G.4 fix: prefer BacDive 'oxygen tolerance' for the
    # target species when present, fall back to the medium-name heuristic.
    cf_cat = _cf_atmosphere_category(cf_gas)
    bd_cat, bd_n_with, bd_n_total = _lookup_bacdive_atmosphere(conn, sp) if sp else (None, 0, 0)

    fired = False
    # Phase 3.6: ANME atmosphere is anaerobic for BacDive-comparison purposes.
    # CH4 is the substrate, not the gas tolerance — the cell still needs O2-free
    # conditions, so an "anaerobic" BacDive label is consistent.
    cf_cat_for_bd = "anaerobic" if cf_cat == "anme" else cf_cat
    if bd_cat is not None:
        # BacDive structured signal has priority. Facultative organisms match
        # any aerobic/anaerobic CF gas without firing.
        if bd_cat != "facultative" and cf_cat_for_bd != bd_cat:
            # Microaerobic ↔ aerobic mismatch is real (Campylobacter case);
            # microaerobic ↔ anaerobic mismatch is real (sulfide oxidizers);
            # but facultative on either side absorbs the discrepancy.
            mismatches.append(ConditionMismatch(
                field="atmosphere",
                cf_value=f"{cf_cat_for_bd} ({list(cf_gas.keys())})",
                ref_value=f"{bd_cat} (BacDive: {bd_n_with}/{bd_n_total} strains)",
                note=(f"BacDive reports {sp.split()[0]} sp. as {bd_cat}; "
                      f"CF recipe gas phase is {cf_cat_for_bd}"),
            ))
            fired = True

    # Fall back to medium-name heuristic only when BacDive has no signal
    if not fired and bd_cat is None and ref_names_lower:
        n_names = len(ref_names_lower)
        n_anaerobic = sum(1 for n in ref_names_lower if "anaerob" in n)
        n_h2co2 = sum(1 for n in ref_names_lower if "h2/co2" in n or "h2 / co2" in n)
        cf_h2co2 = "H2" in cf_gas and "CO2" in cf_gas
        cf_aerobic = "air" in cf_gas
        if n_h2co2 / n_names >= 0.5 and not cf_h2co2:
            mismatches.append(ConditionMismatch(
                field="atmosphere",
                cf_value=f"{list(cf_gas.keys())}",
                ref_value="H2/CO2",
                note=(f"{n_h2co2}/{n_names} reference media specify H2/CO2 atmosphere; "
                      "CF recipe uses different gas phase"),
            ))
        elif n_anaerobic / n_names >= 0.5 and cf_aerobic:
            mismatches.append(ConditionMismatch(
                field="atmosphere",
                cf_value="aerobic (air)",
                ref_value="anaerobic",
                note=f"{n_anaerobic}/{n_names} reference media are anaerobic; CF recipe uses air",
            ))

    return mismatches


def compare_recipes(recipe, medium_ids: List[str], conn: sqlite3.Connection,
                     relationship: str = "direct",
                     genome_id: int = 0,
                     species: str = "") -> ComparisonReport:
    """Compare a CultureForge Recipe against a list of published medium IDs.

    The comparison is symmetric:
      - shared ingredients (ref ↔ cf, normalized canonical match)
      - cf_only (in CF recipe, not in any reference)
      - ref_only (in references, not in CF recipe; severity ↑ if frequency >= 0.5)
      - concentration_disagree (>2x difference between CF and reference median)
      - cultivation-condition mismatches (T, pH, atmosphere) — Phase 2d Fix #3
    """
    report = ComparisonReport(
        cf_recipe_genome_id=genome_id, cf_species=species,
        relationship=relationship,
        n_published_media=len(medium_ids),
        matched_published_ids=list(medium_ids),
    )
    if not medium_ids:
        report.rationale = "No published media to compare against."
        return report

    # Cultivation condition checks — populates report.condition_mismatches
    report.condition_mismatches = _check_cultivation_conditions(
        recipe, medium_ids, conn, relationship, genome_id)

    ref_profile = aggregate_published_recipes(medium_ids, conn)

    # Build CF recipe's normalized ingredient set
    cf_canon: Dict[str, dict] = {}
    for ing in recipe.ingredients:
        canon = normalize_compound_name(ing.name)
        if not canon:
            continue
        cf_canon[canon] = {
            "name": ing.name,
            "amount": ing.concentration if ing.concentration_unit in ("g/L", "mM", "g/L NaHCO3") else None,
            "unit": ing.concentration_unit,
            "category": ing.category.value,
        }

    # Expand composite stock solutions (SL-10 trace metals, Wolin's vitamins)
    # so reference ingredients in those classes count as shared. The composite
    # name itself stays in cf_canon for display, but the comparison set is
    # treated as containing the expanded components.
    cf_canon_for_match = _expand_composites(set(cf_canon))
    cf_only_canons = cf_canon_for_match - set(ref_profile)
    ref_only_canons = set(ref_profile) - cf_canon_for_match
    common = cf_canon_for_match & set(ref_profile)

    # Shared ingredients — record concentration disagreements as diffs but the
    # ingredient itself still counts as shared.
    for canon in common:
        ref = ref_profile[canon]
        # cf may not have this canon directly (it can come from composite expansion)
        cf = cf_canon.get(canon)
        if cf is None:
            continue
        cf_amt = cf["amount"]
        ref_med = ref.get("median")
        if cf_amt is not None and ref_med is not None and ref_med > 0:
            ratio = max(cf_amt, ref_med) / max(min(cf_amt, ref_med), 1e-9)
            if ratio > 2.0 and abs(cf_amt - ref_med) > 0.01:
                report.diffs.append(IngredientDiff(
                    severity="minor",
                    kind="concentration_disagree",
                    ingredient=canon,
                    cf_value=f"{cf_amt} {cf['unit']}",
                    ref_value=(f"median {ref_med:.3f} g/L "
                               f"(range {ref['min']:.3f}-{ref['max']:.3f})"),
                    note=f"in {ref['n']}/{report.n_published_media} references",
                ))

    # CF-only ingredients (potentially over-specified). Severity is minor by
    # default — the recipe composer often adds basal salts or trace solutions
    # that aren't in every reference but are biologically reasonable.
    for canon in cf_only_canons:
        cf = cf_canon.get(canon)
        if cf is None:
            # Came from composite expansion — skip the cf_only diff entry
            continue
        report.diffs.append(IngredientDiff(
            severity="minor",
            kind="cf_only",
            ingredient=canon,
            cf_value=f"{cf['amount']} {cf['unit']}" if cf['amount'] else cf['unit'],
            note=f"category={cf['category']}; not in any of {report.n_published_media} references",
        ))

    # Reference-only ingredients (potentially missing from CF). Frequency-aware:
    # ingredients in most references are more important to flag.
    for canon in ref_only_canons:
        ref = ref_profile[canon]
        freq = ref["frequency"]
        if freq >= 0.7:
            severity = "important"
        else:
            severity = "minor"
        amounts = ""
        if "median" in ref:
            amounts = f"median {ref['median']:.3f} g/L"
        report.diffs.append(IngredientDiff(
            severity=severity,
            kind="ref_only",
            ingredient=canon,
            ref_value=amounts,
            note=f"in {ref['n']}/{report.n_published_media} references "
                 f"({freq:.0%}); {', '.join(ref['raw_names'][:2])}",
        ))

    # Frequency-weighted agreement.
    # For each ref-profile ingredient, score = freq if shared, 0 if missing.
    # For each CF ingredient, score = 1 if matched, smaller penalty if cf_only.
    # The agreement is the weighted-shared score / total possible score.
    n_shared = len(common)
    n_cf_only = len(cf_only_canons)
    n_ref_only_high = sum(1 for d in report.diffs
                            if d.kind == "ref_only" and d.severity == "important")
    n_critical = sum(1 for d in report.diffs if d.severity == "critical")

    if ref_profile:
        # Choose scoring method based on reference count:
        #   n=1 or n=2:  Jaccard-style (shared / union of all distinct ingredients)
        #   n>=3:        frequency-weighted high-frequency consensus
        if report.n_published_media <= 2:
            # Jaccard: |intersection| / |union|
            union = cf_canon_for_match | set(ref_profile)
            shared = cf_canon_for_match & set(ref_profile)
            coverage = len(shared) / max(len(union), 1)
            report.scoring_method = "jaccard"
        else:
            # Frequency-weighted high-frequency consensus
            hf_ref = [c for c, ref in ref_profile.items() if ref["frequency"] >= 0.5]
            n_hf_ref = len(hf_ref)
            n_hf_shared = sum(1 for c in hf_ref if c in cf_canon_for_match)
            if n_hf_ref == 0:
                hf_ref = list(ref_profile.keys())
                n_hf_ref = len(hf_ref)
                n_hf_shared = sum(1 for c in hf_ref if c in cf_canon_for_match)
            coverage = n_hf_shared / max(n_hf_ref, 1)
            report.scoring_method = "frequency_weighted"
        # Cultivation-condition penalties (Phase 2d Fix #3)
        condition_penalty = 0.20 * len(report.condition_mismatches)
        agreement = coverage - 0.10 * n_critical - condition_penalty
        report.overall_agreement = max(0.0, min(1.0, agreement))
    else:
        report.overall_agreement = 0.0

    report.rationale = (
        f"{n_shared} shared ingredients, "
        f"{n_critical} critical / {n_ref_only_high} high-frequency-missing / "
        f"{n_cf_only} cf-only diffs across {report.n_published_media} reference media."
    )
    return report
