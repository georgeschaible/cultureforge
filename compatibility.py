"""Media Compatibility Engine — Tier A (rule-based precipitation check).

Per CLAUDE.md Addendum 6, scans a recipe's components pairwise against a
curated table of known chemical incompatibilities. When two compounds are
present whose ions would precipitate under the recipe's pH / temperature,
the engine:

  1. Flags the incompatibility with severity (HIGH / MEDIUM / LOW)
  2. Suggests specific remediation (separate autoclaving, chelators, etc.)
  3. Generates preparation instructions (which solutions to combine when)
  4. Adjusts recipe confidence per the severity rules in the addendum

Public API:
    populate_rules(conn)         — seed the precipitation_rules table
    check_compatibility(conn, components, pH, temperature, is_sulfidogenic)
                                 → list of Warning dicts
    generate_prep_instructions(warnings, components) → str
    confidence_penalty(warnings) → float  (to subtract from overall)
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------- schema

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS precipitation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_a TEXT NOT NULL,        -- ion/species pattern (regex-friendly)
    component_b TEXT NOT NULL,
    condition_ph_min REAL,           -- NULL = any pH
    condition_ph_max REAL,
    condition_notes TEXT,            -- human-readable condition
    precipitate_formula TEXT,
    precipitate_name TEXT,
    severity TEXT NOT NULL,          -- HIGH / MEDIUM / LOW
    remediation TEXT NOT NULL,       -- suggested fix
    UNIQUE (component_a, component_b, precipitate_formula)
);
"""


# ---------------------------------------------------------------- rules data

# Each tuple: (component_a, component_b, ph_min, ph_max, condition_notes,
#               precipitate_formula, precipitate_name, severity, remediation)
RULES = [
    # Iron-phosphate
    ("Fe", "PO4|HPO4|K2HPO4|KH2PO4|phosphat",
     5.5, None, "pH > 5.5",
     "FePO4 / Fe3(PO4)2", "vivianite / iron phosphate", "HIGH",
     "Prepare iron and phosphate solutions SEPARATELY; autoclave separately; "
     "combine post-cooling. OR add chelator (NTA 0.1-1 mg/L or Na-EDTA 0.5-5 mg/L) "
     "to iron solution before combining. OR use ferric citrate (pre-chelated iron)."),

    # Iron-sulfide
    ("Fe", "Na2S\\b|sulfide|H2S|HS-|thioglycolat|cysteine",
     None, None, "any pH",
     "FeS / FeS2", "iron sulfide / pyrite", "HIGH",
     "Prepare iron and reducing-agent/sulfide solutions SEPARATELY; "
     "combine under anaerobic conditions post-autoclaving. "
     "Consider titanium(III) citrate as alternative reductant if FeS "
     "precipitation is problematic."),

    # Calcium-carbonate
    ("Ca", "CO3|HCO3|NaHCO3|bicarbonat|carbonat",
     7.5, None, "pH > 7.5",
     "CaCO3", "calcite", "MEDIUM",
     "Autoclave CaCl2 and NaHCO3 solutions separately. "
     "OR use CO2 sparging to maintain dissolved CO2 rather than bicarbonate salts."),

    # Calcium-phosphate
    ("Ca", "PO4|HPO4|K2HPO4|KH2PO4|phosphat",
     6.5, None, "pH > 6.5",
     "Ca3(PO4)2", "apatite / calcium phosphate", "MEDIUM",
     "Autoclave calcium and phosphate solutions separately; combine post-cooling."),

    # Calcium-sulfate (only at high concentrations)
    ("Ca", "SO4|MgSO4|Na2SO4|sulfat",
     None, None, "high concentrations (>20 mM each)",
     "CaSO4", "gypsum", "LOW",
     "Usually not problematic at typical medium concentrations. "
     "If both Ca and SO4 are at high levels, reduce one or prepare separately."),

    # Magnesium-phosphate-ammonia (struvite)
    ("Mg.*NH4|NH4.*Mg", "PO4|HPO4|K2HPO4|phosphat",
     8.0, None, "pH > 8.0 + NH4 present",
     "MgNH4PO4", "struvite", "MEDIUM",
     "Maintain pH below 8 during preparation; autoclave phosphate separately."),

    # Manganese-carbonate
    ("Mn", "CO3|HCO3|carbonat",
     7.5, None, "pH > 7.5",
     "MnCO3", "rhodochrosite", "MEDIUM",
     "Autoclave manganese and carbonate solutions separately."),

    # Metal-sulfide pairs (Ni, Cu, Zn, Co with sulfide)
    ("Cu", "Na2S\\b|sulfide|H2S|HS-|thioglycolat",
     None, None, "any pH",
     "CuS", "covellite", "HIGH",
     "Prepare trace metals and sulfide/reducing agent SEPARATELY; "
     "combine post-autoclaving under anaerobic conditions."),

    ("Zn", "Na2S\\b|sulfide|H2S|HS-|thioglycolat",
     None, None, "any pH",
     "ZnS", "sphalerite", "HIGH",
     "Prepare trace metals and sulfide/reducing agent SEPARATELY; "
     "combine post-autoclaving under anaerobic conditions."),

    ("Ni", "Na2S\\b|sulfide|H2S|HS-|thioglycolat",
     6.0, None, "neutral-alkaline pH",
     "NiS", "millerite", "HIGH",
     "Prepare trace metals and sulfide/reducing agent SEPARATELY; "
     "combine post-autoclaving under anaerobic conditions."),

    ("Co", "Na2S\\b|sulfide|H2S|HS-|thioglycolat",
     6.0, None, "neutral-alkaline pH",
     "CoS", "cobalt sulfide", "HIGH",
     "Prepare trace metals and sulfide/reducing agent SEPARATELY; "
     "combine post-autoclaving under anaerobic conditions."),

    # Ferric hydroxide
    ("Fe.*Cl3|FeCl3|Fe\\(III\\)|ferric|Fe3",
     "OH|NaOH",
     3.0, None, "pH > 3 (ferric only)",
     "Fe(OH)3", "ferrihydrite", "HIGH",
     "Use ferrous (Fe2+) salts instead of ferric (Fe3+) at neutral pH. "
     "Add chelator (citrate or NTA) to keep iron in solution."),
]


# ---------------------------------------------------------------- DB helpers

def populate_rules(conn: sqlite3.Connection) -> int:
    """Seed (or refresh) the precipitation_rules table from the RULES constant.
    Replaces all existing rules to pick up pattern fixes."""
    conn.executescript(SCHEMA_SQL)
    conn.execute("DELETE FROM precipitation_rules")
    n = 0
    for (a, b, ph_min, ph_max, cond, formula, name, sev, remed) in RULES:
        conn.execute("""
            INSERT INTO precipitation_rules
              (component_a, component_b, condition_ph_min, condition_ph_max,
               condition_notes, precipitate_formula, precipitate_name,
               severity, remediation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (a, b, ph_min, ph_max, cond, formula, name, sev, remed))
        n += 1
    conn.commit()
    return n


# ---------------------------------------------------------------- checker

@dataclass
class CompatWarning:
    severity: str          # HIGH / MEDIUM / LOW
    component_a: str       # actual compound name from recipe
    component_b: str       # actual compound name from recipe
    precipitate: str       # e.g. "FeS (iron sulfide)"
    condition: str         # e.g. "any pH" or "pH > 5.5"
    remediation: str       # human-readable fix
    rule_id: int           # DB row id for provenance


def _compound_matches_pattern(compound_name: str, pattern: str) -> bool:
    """Check if a compound name matches a rule pattern. The pattern is a
    pipe-separated set of substrings or simple regexes, matched case-insensitively
    against the compound name."""
    for term in pattern.split("|"):
        term = term.strip()
        if not term:
            continue
        try:
            if re.search(term, compound_name, re.IGNORECASE):
                return True
        except re.error:
            # Fall back to simple substring
            if term.lower() in compound_name.lower():
                return True
    return False


def check_compatibility(conn: sqlite3.Connection,
                        compound_names: List[str],
                        ph: Optional[float] = 7.0,
                        temperature: Optional[float] = None,
                        is_sulfidogenic: bool = False,
                        ) -> List[CompatWarning]:
    """Scan all compound pairs against precipitation_rules.

    compound_names: list of compound name strings from the recipe.
    ph: recipe pH (default 7.0).
    is_sulfidogenic: if True, add implicit "H2S(aq)" to the compound list
        because the organism produces sulfide as a metabolic product. This
        is critical for sulfate reducers where FeS / metal-sulfide precipitation
        is the #1 practical problem even though sulfide isn't explicitly
        in the recipe.

    Returns list of CompatWarning sorted by severity (HIGH first).
    """
    populate_rules(conn)

    # Add implicit sulfide if the organism produces it
    names = list(compound_names)
    if is_sulfidogenic and not any("sulfide" in n.lower() or "H2S" in n
                                   or "Na2S" in n for n in names):
        names.append("H2S(aq) [metabolic product]")

    rules = conn.execute("""
        SELECT id, component_a, component_b, condition_ph_min,
               condition_ph_max, condition_notes, precipitate_formula,
               precipitate_name, severity, remediation
          FROM precipitation_rules
    """).fetchall()

    warnings = []
    seen_precipitates = set()  # avoid duplicate warnings for same precipitate

    for rule in rules:
        (rid, pat_a, pat_b, ph_min, ph_max, cond, formula, pname,
         severity, remediation) = rule

        # Check pH conditions
        if ph_min is not None and ph is not None and ph < ph_min:
            continue
        if ph_max is not None and ph is not None and ph > ph_max:
            continue

        # Find matching compounds in the recipe
        matches_a = [n for n in names if _compound_matches_pattern(n, pat_a)]
        matches_b = [n for n in names if _compound_matches_pattern(n, pat_b)]

        if matches_a and matches_b:
            # Avoid self-match (same compound matching both patterns)
            real_pairs = [(a, b) for a in matches_a for b in matches_b
                          if a != b]
            if not real_pairs:
                continue

            precipitate_key = formula
            if precipitate_key in seen_precipitates:
                continue
            seen_precipitates.add(precipitate_key)

            a_name, b_name = real_pairs[0]
            warnings.append(CompatWarning(
                severity=severity,
                component_a=a_name,
                component_b=b_name,
                precipitate=f"{formula} ({pname})",
                condition=cond or "any conditions",
                remediation=remediation,
                rule_id=rid,
            ))

    # Sort by severity: HIGH > MEDIUM > LOW
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    warnings.sort(key=lambda w: severity_order.get(w.severity, 9))
    return warnings


# ---------------------------------------------------------------- prep instructions

def generate_prep_instructions(warnings: List[CompatWarning],
                               compound_names: List[str],
                               ) -> Optional[str]:
    """Generate preparation instructions from compatibility warnings.

    Groups compounds into solutions that must be autoclaved separately,
    and specifies order of combination.
    """
    if not warnings:
        return None

    high = [w for w in warnings if w.severity == "HIGH"]
    medium = [w for w in warnings if w.severity == "MEDIUM"]

    if not high and not medium:
        return None

    # Collect compounds that need separate preparation
    # Group A: metals/iron compounds (prepare together, separate from phosphate/sulfide)
    # Group B: phosphate/carbonate compounds (separate from metals)
    # Group C: sulfide/reducing agents (add last, post-autoclaving, under anaerobic conditions)
    # Group D: vitamins (filter-sterilize, add post-autoclaving)

    metal_compounds = set()
    phosphate_compounds = set()
    sulfide_compounds = set()
    other_compounds = set()

    metal_patterns = re.compile(
        r"Fe|Mn|Zn|Cu|Co|Ni|NiCl|CoCl|CuSO|ZnSO|MnCl|FeSO|FeCl|trace",
        re.IGNORECASE)
    phosphate_patterns = re.compile(
        r"PO4|HPO4|K2HPO4|KH2PO4|phosphat", re.IGNORECASE)
    sulfide_patterns = re.compile(
        r"Na2S|sulfide|H2S|thioglycolat|cysteine|ascorb|reduc",
        re.IGNORECASE)

    for name in compound_names:
        if sulfide_patterns.search(name):
            sulfide_compounds.add(name)
        elif metal_patterns.search(name):
            metal_compounds.add(name)
        elif phosphate_patterns.search(name):
            phosphate_compounds.add(name)

    lines = []
    lines.append("  PREPARATION INSTRUCTIONS (auto-generated from compatibility check)")
    lines.append("")

    sol_num = ord("A")

    if phosphate_compounds:
        lines.append(f"  SOLUTION {chr(sol_num)} — Phosphate/buffer (autoclave separately):")
        for c in sorted(phosphate_compounds):
            lines.append(f"    - {c}")
        lines.append(f"    → Dissolve in partial volume H₂O, autoclave 121°C 15 min")
        lines.append("")
        sol_num += 1

    if metal_compounds:
        lines.append(f"  SOLUTION {chr(sol_num)} — Metals/iron (autoclave separately):")
        for c in sorted(metal_compounds):
            lines.append(f"    - {c}")
        # Check if chelator needed
        if any(w.severity == "HIGH" and "chelator" in w.remediation.lower()
               for w in warnings):
            lines.append(f"    - Na-EDTA or NTA (chelator, 0.5-5 mg/L)")
        lines.append(f"    → Dissolve in partial volume H₂O, autoclave 121°C 15 min")
        lines.append("")
        sol_num += 1

    if sulfide_compounds:
        lines.append(f"  SOLUTION {chr(sol_num)} — Reducing agents/sulfide "
                     f"(prepare under N₂, add LAST):")
        for c in sorted(sulfide_compounds):
            lines.append(f"    - {c}")
        lines.append(f"    → Prepare under N₂ atmosphere; autoclave separately or")
        lines.append(f"      prepare from sterile anaerobic stock; add to cooled")
        lines.append(f"      combined medium under anaerobic conditions")
        lines.append("")
        sol_num += 1

    lines.append(f"  COMBINE: Cool all solutions to ~50°C under sterile conditions.")
    lines.append(f"           Add solutions in order: base salts → phosphate →")
    lines.append(f"           metals (with chelator) → reducing agents/sulfide (last).")
    lines.append(f"           Adjust pH to target with sterile NaOH/HCl.")

    return "\n".join(lines)


# ---------------------------------------------------------------- confidence penalty

def confidence_penalty(warnings: List[CompatWarning]) -> float:
    """Compute the confidence penalty from compatibility warnings.

    Per CLAUDE.md addendum 6:
      - No warnings → 0
      - MEDIUM severity → -0.05
      - HIGH severity → -0.10
      - Multiple HIGH → -0.15
    """
    if not warnings:
        return 0.0
    high_count = sum(1 for w in warnings if w.severity == "HIGH")
    medium_count = sum(1 for w in warnings if w.severity == "MEDIUM")

    if high_count >= 2:
        return 0.15
    if high_count == 1:
        return 0.10
    if medium_count >= 1:
        return 0.05
    return 0.0


# ---------------------------------------------------------------- format for report

def format_warnings(warnings: List[CompatWarning]) -> str:
    """Format compatibility warnings for inclusion in the synthesizer report."""
    if not warnings:
        return ""
    lines = []
    for w in warnings:
        marker = {"HIGH": "✗", "MEDIUM": "⚠", "LOW": "○"}[w.severity]
        lines.append(f"    {marker} [{w.severity}] {w.precipitate}")
        lines.append(f"        {w.component_a}  +  {w.component_b}  "
                     f"(condition: {w.condition})")
        lines.append(f"        → {w.remediation}")
        lines.append("")
    return "\n".join(lines)
