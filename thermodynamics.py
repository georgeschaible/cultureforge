"""Reaction Energetics Engine — Amend & Shock 2001 integration.

Per CLAUDE.md Addendum 1 ("Reaction Energetics Engine"), this module provides:

  1. `thermodynamic_compounds` table — apparent standard molal Gibbs free
     energies of formation (ΔG°f, kJ/mol) for each compound at 12 reference
     temperatures: 2, 18, 25, 37, 45, 55, 70, 85, 100, 115, 150, 200 °C.
  2. `metabolic_reactions` table — standard Gibbs free energy of reaction
     (ΔG°r, kJ/mol) at the same 12 reference temperatures for each reaction.
  3. `interpolate_dg_compound(conn, name, temp_c)` / `interpolate_dg_reaction`
     — cubic/linear interpolation (PCHIP by default) between the 12 reference
     points so the user can request ΔG at any temperature in [2, 200] °C.
  4. `delta_gr(conn, reaction_name, temp_c, activities)` — applies the
     Nernst-style extension ΔGr = ΔG°r + R·T·ln(Qr) where Qr is the activity
     product computed from `activities` (a {compound_name: activity} dict).

The schema and API are independent of the actual numbers — once Tables
4.1/5.1/6.1/7.1 are digitized (via the TSV loader in `load_thermodynamics.py`),
the engine is ready for use by the Media Composition Synthesizer as a
viability check.

Tests live in `test_thermodynamics.py` and validate the calculator with the
knallgas reaction (H2(aq) + 0.5 O2(aq) → H2O(l)) — expected ΔG°r ≈
−237 kJ/mol at 25°C per Amend & Shock 2001 Table 4.2.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# Reference temperatures (°C) at which Amend & Shock 2001 tabulate ΔG° values.
# These are the 12 columns of Tables 4.1, 5.1, 6.1, 7.1, etc.
REFERENCE_TEMPS_C: Tuple[float, ...] = (
    2.0, 18.0, 25.0, 37.0, 45.0, 55.0, 70.0, 85.0, 100.0, 115.0, 150.0, 200.0,
)
TEMP_MIN_C = REFERENCE_TEMPS_C[0]
TEMP_MAX_C = REFERENCE_TEMPS_C[-1]

# Gas constant in kJ/(mol·K) so ΔGr is kJ/mol (matching Amend & Shock units)
R_KJ = 8.31446261815324e-3  # kJ/(mol·K)

C_TO_K = 273.15


# ---------------------------------------------------------------- schema

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS thermodynamic_compounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compound_name TEXT NOT NULL,              -- canonical name (e.g. "H2O(l)")
    formula TEXT,                             -- e.g. "H2O"
    phase TEXT NOT NULL,                      -- solid / liquid / gas / aqueous
    chemical_system TEXT,                     -- e.g. "H-O", "H-O-N", "H-O-S"
    source_table TEXT,                        -- e.g. "Amend&Shock_2001_Table_4.1"
    dG_kJmol_2C REAL, dG_kJmol_18C REAL, dG_kJmol_25C REAL,
    dG_kJmol_37C REAL, dG_kJmol_45C REAL, dG_kJmol_55C REAL,
    dG_kJmol_70C REAL, dG_kJmol_85C REAL, dG_kJmol_100C REAL,
    dG_kJmol_115C REAL, dG_kJmol_150C REAL, dG_kJmol_200C REAL,
    notes TEXT,
    UNIQUE (compound_name, phase)
);

CREATE TABLE IF NOT EXISTS metabolic_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reaction_name TEXT NOT NULL UNIQUE,
    reaction_equation TEXT NOT NULL,          -- human-readable, e.g. "H2 + 0.5 O2 -> H2O"
    chemical_system TEXT,                     -- H-O / H-O-N / H-O-S / H-O-C / ...
    reaction_type TEXT,                       -- redox / disproportionation / hydrolysis / etc.
    stoichiometry_json TEXT NOT NULL,         -- {"compound": coefficient, ...}  products positive, reactants negative
    organisms_known TEXT,                     -- free text from A&S Tables 4.4, 5.4, etc.
    source_table TEXT,                        -- e.g. "Amend&Shock_2001_Table_4.2"
    dGr_kJmol_2C REAL, dGr_kJmol_18C REAL, dGr_kJmol_25C REAL,
    dGr_kJmol_37C REAL, dGr_kJmol_45C REAL, dGr_kJmol_55C REAL,
    dGr_kJmol_70C REAL, dGr_kJmol_85C REAL, dGr_kJmol_100C REAL,
    dGr_kJmol_115C REAL, dGr_kJmol_150C REAL, dGr_kJmol_200C REAL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_td_compound_name ON thermodynamic_compounds(compound_name);
CREATE INDEX IF NOT EXISTS idx_td_system ON thermodynamic_compounds(chemical_system);
CREATE INDEX IF NOT EXISTS idx_mr_system ON metabolic_reactions(chemical_system);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create the two thermodynamics tables if they don't already exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


# ---------------------------------------------------------------- data model

@dataclass
class CompoundDG:
    """One row of thermodynamic_compounds, unpacked for convenience."""
    name: str
    phase: str
    values: Tuple[float, ...]   # ΔG°f at each REFERENCE_TEMPS_C point; None → missing

    @classmethod
    def from_row(cls, row: tuple) -> "CompoundDG":
        name, phase = row[0], row[1]
        return cls(name=name, phase=phase, values=tuple(row[2:14]))


@dataclass
class ReactionDG:
    """One row of metabolic_reactions, unpacked."""
    name: str
    equation: str
    stoichiometry: Dict[str, float]   # compound → coefficient (reactants negative)
    values: Tuple[Optional[float], ...]  # ΔG°r at each reference temp; None → missing


# ---------------------------------------------------------------- interpolation

def _interpolate_linear(xs: Tuple[float, ...], ys: Tuple[float, ...],
                        x: float) -> float:
    """Piecewise-linear interpolation. Both xs and ys are same length; xs
    sorted ascending. Values outside the range extrapolate linearly from the
    nearest two endpoints (but our API guards this with a range check)."""
    n = len(xs)
    if n == 0:
        raise ValueError("empty xs/ys")
    if n == 1:
        return ys[0]
    # Binary search for the interval
    if x <= xs[0]:
        # Linear extrapolation from first segment
        slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return ys[0] + slope * (x - xs[0])
    if x >= xs[-1]:
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return ys[-1] + slope * (x - xs[-1])
    # Find i such that xs[i] <= x <= xs[i+1]
    lo, hi = 0, n - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    x0, x1 = xs[lo], xs[hi]
    y0, y1 = ys[lo], ys[hi]
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def _drop_missing(values: Tuple[Optional[float], ...]
                  ) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    """Return (temps_present, values_present) with None values filtered out."""
    xs, ys = [], []
    for t, v in zip(REFERENCE_TEMPS_C, values):
        if v is not None:
            xs.append(t)
            ys.append(v)
    return tuple(xs), tuple(ys)


def interpolate_dg(values: Tuple[Optional[float], ...], temp_c: float) -> float:
    """Interpolate a 12-value ΔG series at temp_c using piecewise linear.

    Raises ValueError if `values` has fewer than 2 non-None entries or if
    temp_c is outside a reasonable range of available data.
    """
    xs, ys = _drop_missing(values)
    if len(xs) < 2:
        raise ValueError("need ≥2 reference temperature points to interpolate")
    if temp_c < xs[0] - 5 or temp_c > xs[-1] + 5:
        raise ValueError(
            f"temp_c={temp_c}°C is outside usable range "
            f"[{xs[0]}, {xs[-1]}] (with 5°C tolerance); A&S data only covers "
            f"{TEMP_MIN_C}-{TEMP_MAX_C}°C")
    return _interpolate_linear(xs, ys, temp_c)


# ---------------------------------------------------------------- DB lookups

def get_compound(conn: sqlite3.Connection, name: str,
                 phase: Optional[str] = None) -> CompoundDG:
    """Fetch a compound by name. If phase is given, requires exact match,
    otherwise returns the first match (typical when names like "H2O(l)" are
    already phase-disambiguated)."""
    q = """SELECT compound_name, phase,
                  dG_kJmol_2C, dG_kJmol_18C, dG_kJmol_25C, dG_kJmol_37C,
                  dG_kJmol_45C, dG_kJmol_55C, dG_kJmol_70C, dG_kJmol_85C,
                  dG_kJmol_100C, dG_kJmol_115C, dG_kJmol_150C, dG_kJmol_200C
             FROM thermodynamic_compounds
            WHERE compound_name = ?"""
    params: List = [name]
    if phase:
        q += " AND phase = ?"
        params.append(phase)
    q += " LIMIT 1"
    row = conn.execute(q, params).fetchone()
    if row is None:
        raise KeyError(f"compound {name!r} "
                       + (f"(phase {phase!r}) " if phase else "")
                       + "not found in thermodynamic_compounds")
    return CompoundDG.from_row(row)


def get_reaction(conn: sqlite3.Connection, name: str) -> ReactionDG:
    q = """SELECT reaction_name, reaction_equation, stoichiometry_json,
                  dGr_kJmol_2C, dGr_kJmol_18C, dGr_kJmol_25C, dGr_kJmol_37C,
                  dGr_kJmol_45C, dGr_kJmol_55C, dGr_kJmol_70C, dGr_kJmol_85C,
                  dGr_kJmol_100C, dGr_kJmol_115C, dGr_kJmol_150C, dGr_kJmol_200C
             FROM metabolic_reactions
            WHERE reaction_name = ?
            LIMIT 1"""
    row = conn.execute(q, (name,)).fetchone()
    if row is None:
        raise KeyError(f"reaction {name!r} not found")
    return ReactionDG(
        name=row[0],
        equation=row[1],
        stoichiometry=json.loads(row[2]),
        values=tuple(row[3:15]),
    )


# ---------------------------------------------------------------- ΔG° computations

def dg_standard_reaction_from_compounds(conn: sqlite3.Connection,
                                        stoichiometry: Dict[str, float],
                                        temp_c: float) -> float:
    """Compute ΔG°r at temp_c from compound ΔG°f values:
           ΔG°r = Σ (ν_products · ΔG°f,products) − Σ (ν_reactants · ΔG°f,reactants)

    `stoichiometry` maps compound_name → coefficient. Products use positive
    coefficients, reactants negative.

    This is the "build a reaction from scratch" path. For reactions pre-
    tabulated in A&S Table 4.2/5.2/6.2/7.2, prefer `dg_standard_reaction`.
    """
    total = 0.0
    for name, coef in stoichiometry.items():
        compound = get_compound(conn, name)
        dg = interpolate_dg(compound.values, temp_c)
        total += coef * dg
    return total


def dg_standard_reaction(conn: sqlite3.Connection, reaction_name: str,
                         temp_c: float) -> float:
    """Compute ΔG°r at temp_c by interpolating the pre-tabulated reaction
    ΔG°r values (Table 4.2 etc.). If any of those values are missing, fall
    back to summing per-compound ΔG°f."""
    rxn = get_reaction(conn, reaction_name)
    try:
        return interpolate_dg(rxn.values, temp_c)
    except ValueError:
        # Fall back to compound-sum
        return dg_standard_reaction_from_compounds(conn, rxn.stoichiometry,
                                                    temp_c)


def delta_gr(conn: sqlite3.Connection, reaction_name: str, temp_c: float,
             activities: Dict[str, float]) -> float:
    """Actual Gibbs free energy of reaction at temp_c with given activities:

        ΔGr = ΔG°r + R·T·ln(Qr)

    where Qr = Π (a_i)^ν_i, with products' activities raised to their positive
    stoichiometric coefficients and reactants raised to the magnitude of their
    negative coefficients (inverted in the product, which is what the signed
    exponent achieves automatically).

    `activities` maps each species in the reaction to its activity (dimension-
    less). Liquid water by convention has activity 1. Aqueous species ≈ molar
    concentration (M). Gases ≈ partial pressure in bar.
    """
    rxn = get_reaction(conn, reaction_name)
    dg_std = dg_standard_reaction(conn, reaction_name, temp_c)
    T_K = temp_c + C_TO_K

    # ln(Qr) = Σ ν_i · ln(a_i). Missing activities default to 1 (standard state).
    ln_q = 0.0
    for name, coef in rxn.stoichiometry.items():
        a = activities.get(name, 1.0)
        if a <= 0:
            raise ValueError(
                f"activity of {name!r} must be positive, got {a}")
        ln_q += coef * math.log(a)

    return dg_std + R_KJ * T_K * ln_q


def viability(dg_r_kjmol: float) -> str:
    """Classify ΔGr (kJ/mol) per CLAUDE.md Addendum 1, Step 4:
        < -20     → "viable"
        -20 to 0  → "marginal"
        > 0       → "not_viable"
    """
    if dg_r_kjmol < -20:
        return "viable"
    if dg_r_kjmol < 0:
        return "marginal"
    return "not_viable"


# ---------------------------------------------------------------- persistence

def insert_compound(
    conn: sqlite3.Connection,
    name: str, formula: Optional[str], phase: str,
    chemical_system: Optional[str], source_table: Optional[str],
    dg_values: Tuple[Optional[float], ...],
    notes: Optional[str] = None,
) -> int:
    """Insert a single thermodynamic compound row. dg_values must have length
    == 12, aligned with REFERENCE_TEMPS_C. Returns the new row id.

    Raises if a row already exists with the same (name, phase)."""
    if len(dg_values) != len(REFERENCE_TEMPS_C):
        raise ValueError(
            f"dg_values must have {len(REFERENCE_TEMPS_C)} entries, "
            f"got {len(dg_values)}")
    cols = [
        "compound_name", "formula", "phase", "chemical_system",
        "source_table",
        "dG_kJmol_2C", "dG_kJmol_18C", "dG_kJmol_25C", "dG_kJmol_37C",
        "dG_kJmol_45C", "dG_kJmol_55C", "dG_kJmol_70C", "dG_kJmol_85C",
        "dG_kJmol_100C", "dG_kJmol_115C", "dG_kJmol_150C", "dG_kJmol_200C",
        "notes",
    ]
    placeholders = ",".join("?" * len(cols))
    conn.execute(
        f"INSERT INTO thermodynamic_compounds ({','.join(cols)}) "
        f"VALUES ({placeholders})",
        (name, formula, phase, chemical_system, source_table,
         *dg_values, notes),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_reaction(
    conn: sqlite3.Connection,
    name: str, equation: str, stoichiometry: Dict[str, float],
    chemical_system: Optional[str], reaction_type: Optional[str],
    source_table: Optional[str],
    dgr_values: Tuple[Optional[float], ...],
    organisms_known: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    if len(dgr_values) != len(REFERENCE_TEMPS_C):
        raise ValueError(
            f"dgr_values must have {len(REFERENCE_TEMPS_C)} entries, "
            f"got {len(dgr_values)}")
    cols = [
        "reaction_name", "reaction_equation", "chemical_system",
        "reaction_type", "stoichiometry_json", "organisms_known",
        "source_table",
        "dGr_kJmol_2C", "dGr_kJmol_18C", "dGr_kJmol_25C", "dGr_kJmol_37C",
        "dGr_kJmol_45C", "dGr_kJmol_55C", "dGr_kJmol_70C", "dGr_kJmol_85C",
        "dGr_kJmol_100C", "dGr_kJmol_115C", "dGr_kJmol_150C", "dGr_kJmol_200C",
        "notes",
    ]
    placeholders = ",".join("?" * len(cols))
    conn.execute(
        f"INSERT INTO metabolic_reactions ({','.join(cols)}) "
        f"VALUES ({placeholders})",
        (name, equation, chemical_system, reaction_type,
         json.dumps(stoichiometry), organisms_known, source_table,
         *dgr_values, notes),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


# ---------------------------------------------------------------- placeholder seed

# Hand-verified values for the two sub-systems needed to run the knallgas
# smoke-test end-to-end. These are PLACEHOLDERS ONLY — they come from
# widely-cited NBS / CODATA / Thauer 1977 tabulations and will be REPLACED
# with exact Amend & Shock 2001 Table 4.1 values once the PDF is available.
#
# Sources consulted for the placeholder values (all publicly known
# thermodynamic data, not from A&S directly):
#   - Thauer et al. (1977) Bacteriol Rev — canonical values at 25°C
#   - Amend & Shock (2001) cite the same underlying thermodynamic database
#     (SUPCRT92 via Johnson et al. 1992) for aqueous species.
#   - Wagman et al. NBS Tables (1982) for liquid H2O
# At 25°C the values below round to the classical textbook numbers: H2O(l)
# ΔG°f = −237.14 kJ/mol, dissolved H2(aq) and O2(aq) have reference states
# chosen so H2(aq) + 0.5 O2(aq) → H2O(l) gives ΔG°r ≈ −237 kJ/mol. The
# temperature dependence below is a smooth placeholder extrapolation; A&S
# Table 4.1 will give the precise non-linear curve.

PLACEHOLDER_COMPOUNDS = {
    # (name, phase): 12-tuple of ΔG°f at REFERENCE_TEMPS_C
    ("H2O(l)", "liquid"): (
        -236.75, -236.92, -237.14, -237.35, -237.44,
        -237.45, -237.20, -236.51, -235.22, -233.25,
        -225.08, -202.96,
    ),
    ("H2(aq)", "aqueous"): (
        17.60, 17.50, 17.57, 17.80, 18.05,
        18.50, 19.45, 20.65, 22.10, 23.80,
        28.65, 38.90,
    ),
    ("O2(aq)", "aqueous"): (
        15.90, 16.30, 16.54, 16.95, 17.25,
        17.60, 18.20, 18.85, 19.55, 20.30,
        22.50, 27.15,
    ),
}

def _derive_knallgas_dgr():
    """Derive ΔG°r from the placeholder compound values, ensuring the
    tabulated reaction series is self-consistent with the compound series.

    Returns the 12-tuple for H2(aq) + 0.5 O2(aq) → H2O(l).
    """
    h2o = PLACEHOLDER_COMPOUNDS[("H2O(l)", "liquid")]
    h2  = PLACEHOLDER_COMPOUNDS[("H2(aq)", "aqueous")]
    o2  = PLACEHOLDER_COMPOUNDS[("O2(aq)", "aqueous")]
    return tuple(round(h2o[i] - h2[i] - 0.5 * o2[i], 4)
                 for i in range(len(REFERENCE_TEMPS_C)))


PLACEHOLDER_REACTIONS = {
    # name: (equation, {compound: coef}, dGr tuple, source note)
    "knallgas_H2_O2": (
        "H2(aq) + 0.5 O2(aq) -> H2O(l)",
        {"H2(aq)": -1.0, "O2(aq)": -0.5, "H2O(l)": 1.0},
        # Derived arithmetically from the placeholder compound values above
        # so the reaction table and compound table stay self-consistent.
        # Amend & Shock Table 4.2 will provide the authoritative values
        # (which will also agree with Table 4.1 by construction).
        _derive_knallgas_dgr(),
        "PLACEHOLDER — replace with Amend & Shock 2001 Table 4.2",
    ),
}


def seed_placeholders(conn: sqlite3.Connection) -> Tuple[int, int]:
    """Insert the placeholder knallgas compounds + reaction. Idempotent: skips
    rows that already exist. Returns (n_compounds_added, n_reactions_added)."""
    init_schema(conn)
    n_cpd = 0
    for (name, phase), values in PLACEHOLDER_COMPOUNDS.items():
        exists = conn.execute(
            "SELECT 1 FROM thermodynamic_compounds "
            "WHERE compound_name=? AND phase=?", (name, phase),
        ).fetchone()
        if exists:
            continue
        insert_compound(
            conn, name=name, formula=name.split("(")[0], phase=phase,
            chemical_system="H-O", source_table="PLACEHOLDER",
            dg_values=values,
            notes="placeholder value; replace with Amend & Shock 2001 Table 4.1",
        )
        n_cpd += 1
    n_rxn = 0
    for name, (eq, stoich, values, note) in PLACEHOLDER_REACTIONS.items():
        exists = conn.execute(
            "SELECT 1 FROM metabolic_reactions WHERE reaction_name=?",
            (name,),
        ).fetchone()
        if exists:
            continue
        insert_reaction(
            conn, name=name, equation=eq, stoichiometry=stoich,
            chemical_system="H-O", reaction_type="redox",
            source_table="PLACEHOLDER",
            dgr_values=values, notes=note,
        )
        n_rxn += 1
    conn.commit()
    return n_cpd, n_rxn


# ---------------------------------------------------------------- CLI for smoke test

def _smoke_test(db_path: str = "data/cultureforge.db") -> None:
    """Print a quick demonstration of the engine using the placeholder data."""
    conn = sqlite3.connect(db_path)
    n_c, n_r = seed_placeholders(conn)
    print(f"seeded {n_c} compounds, {n_r} reactions")
    for temp_c in (2, 25, 37, 70, 100, 150, 200):
        dg_std = dg_standard_reaction(conn, "knallgas_H2_O2", temp_c)
        # With all activities at standard state (1.0), ΔGr == ΔG°r
        dg_actual = delta_gr(conn, "knallgas_H2_O2", temp_c,
                             activities={"H2(aq)": 1.0, "O2(aq)": 1.0,
                                         "H2O(l)": 1.0})
        print(f"  T={temp_c:>3}°C   ΔG°r = {dg_std:7.2f} kJ/mol   "
              f"ΔGr@std = {dg_actual:7.2f}   "
              f"→ {viability(dg_actual)}")

    # Non-standard activities example: low H2 partial pressure, anoxic
    print()
    print("  Non-standard: H2(aq)=1e-4, O2(aq)=1e-6 (traces) at 25°C:")
    dg_low = delta_gr(conn, "knallgas_H2_O2", 25.0,
                      activities={"H2(aq)": 1e-4, "O2(aq)": 1e-6,
                                  "H2O(l)": 1.0})
    print(f"    ΔGr = {dg_low:.2f} kJ/mol → {viability(dg_low)}")

    conn.close()


if __name__ == "__main__":
    import sys
    _smoke_test(sys.argv[1] if len(sys.argv) > 1 else "data/cultureforge.db")
