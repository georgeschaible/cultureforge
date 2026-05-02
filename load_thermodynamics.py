"""Load Amend & Shock 2001 thermodynamic data from TSV digitizations.

Two TSV formats, one per file:

  compounds.tsv — one row per compound (Tables 4.1, 5.1, 6.1, 7.1, ...)
    Columns (tab-separated):
      compound_name   formula   phase   chemical_system   source_table
      dG_2C   dG_18C   dG_25C   dG_37C   dG_45C   dG_55C
      dG_70C  dG_85C   dG_100C  dG_115C  dG_150C  dG_200C   notes

  reactions.tsv — one row per reaction (Tables 4.2, 5.2, 6.2, 7.2, ...)
    Columns (tab-separated):
      reaction_name   equation   stoichiometry_json   chemical_system
      reaction_type   organisms_known   source_table
      dGr_2C  dGr_18C  dGr_25C  dGr_37C  dGr_45C  dGr_55C
      dGr_70C dGr_85C  dGr_100C dGr_115C dGr_150C dGr_200C   notes

Missing values: empty cell OR literal 'NA' → NULL in the DB.

Usage:
    python load_thermodynamics.py compounds path/to/compounds.tsv
    python load_thermodynamics.py reactions path/to/reactions.tsv
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

import thermodynamics as td

_ROOT = Path(__file__).parent

DB = str(_ROOT / "data" / "cultureforge.db")


def _parse_cell(s: str) -> Optional[float]:
    s = (s or "").strip()
    if s == "" or s.upper() in {"NA", "N/A", "-", "--", "NULL"}:
        return None
    return float(s)


def _parse_12(row, start: int):
    return tuple(_parse_cell(row[start + i]) for i in range(12))


_DG_COLS = [
    "dG_2C", "dG_18C", "dG_25C", "dG_37C", "dG_45C", "dG_55C",
    "dG_70C", "dG_85C", "dG_100C", "dG_115C", "dG_150C", "dG_200C",
]
_DGR_COLS = [c.replace("dG_", "dGr_") for c in _DG_COLS]


def load_compounds(conn: sqlite3.Connection, tsv_path: str) -> int:
    td.init_schema(conn)
    n = 0
    with open(tsv_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = (row.get("compound_name") or "").strip()
            if not name or name.startswith("#"):
                continue
            formula = (row.get("formula") or "").strip() or None
            phase = (row.get("phase") or "").strip()
            chem_sys = (row.get("chemical_system") or "").strip() or None
            src_table = (row.get("source_table") or "").strip() or None
            dg_values = tuple(
                _parse_cell(row.get(c, "")) for c in _DG_COLS
            )
            notes = (row.get("notes") or "").strip() or None
            conn.execute(
                "DELETE FROM thermodynamic_compounds "
                "WHERE compound_name=? AND phase=?", (name, phase))
            td.insert_compound(
                conn, name=name, formula=formula, phase=phase,
                chemical_system=chem_sys, source_table=src_table,
                dg_values=dg_values, notes=notes,
            )
            n += 1
    conn.commit()
    return n


def load_reactions(conn: sqlite3.Connection, tsv_path: str) -> int:
    td.init_schema(conn)
    n = 0
    with open(tsv_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            # Accept either "reaction_name" or "reaction_id" as the name field
            name = (row.get("reaction_name") or row.get("reaction_id") or "").strip()
            if not name or name.startswith("#"):
                continue
            equation = (row.get("equation") or "").strip()
            stoichiometry = json.loads(row.get("stoichiometry_json", "{}"))
            chem_sys = (row.get("chemical_system") or "").strip() or None
            rxn_type = (row.get("reaction_type") or "").strip() or None
            organisms = (row.get("organisms_known") or "").strip() or None
            src_table = (row.get("source_table") or "").strip() or None
            dgr_values = tuple(
                _parse_cell(row.get(c, "")) for c in _DGR_COLS
            )
            notes = (row.get("notes") or "").strip() or None
            conn.execute("DELETE FROM metabolic_reactions WHERE reaction_name=?",
                         (name,))
            td.insert_reaction(
                conn, name=name, equation=equation,
                stoichiometry=stoichiometry,
                chemical_system=chem_sys, reaction_type=rxn_type,
                source_table=src_table, dgr_values=dgr_values,
                organisms_known=organisms, notes=notes,
            )
            n += 1
    conn.commit()
    return n


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"compounds", "reactions"}:
        sys.exit(__doc__)
    kind, tsv = sys.argv[1], sys.argv[2]
    conn = sqlite3.connect(DB)
    try:
        if kind == "compounds":
            n = load_compounds(conn, tsv)
            print(f"loaded {n} compound rows from {tsv}")
        else:
            n = load_reactions(conn, tsv)
            print(f"loaded {n} reaction rows from {tsv}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
