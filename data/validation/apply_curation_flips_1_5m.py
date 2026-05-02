"""Apply user-confirmed curation flips to phase1_5m_hit_patterns.tsv.

User decisions (Checkpoint 2 acknowledgment):
  Sulfolobus_acidocaldarius x autotrophy: NEGATIVE -> POSITIVE  (3HP/4HB cycle)
  Methanoperedens_nitroreducens x acsB_cdhC: NEGATIVE -> POSITIVE  (reverse Wood-Ljungdahl)
  Methanoperedens_nitroreducens x cooS_cdhA: NEGATIVE -> POSITIVE  (reverse Wood-Ljungdahl)
  Methanoperedens_nitroreducens x nifH: NEGATIVE -> POSITIVE       (some ANME encode nitrogenase)

Recomputes the verdict column for those rows and re-tallies the totals.
Also patches EXPECTATIONS in run_phase1_5m_hit_patterns.py for future runs.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TSV = ROOT / "data/validation/phase1_5m_hit_patterns.tsv"
SCRIPT = ROOT / "data/validation/run_phase1_5m_hit_patterns.py"

FLIPS = {
    ("Sulfolobus_acidocaldarius",     "autotrophy"): "POSITIVE",
    ("Methanoperedens_nitroreducens", "acsB_cdhC"):  "POSITIVE",
    ("Methanoperedens_nitroreducens", "cooS_cdhA"):  "POSITIVE",
    ("Methanoperedens_nitroreducens", "nifH"):       "POSITIVE",
}


def verdict(positive: bool, exp: str) -> str:
    if exp == "POSITIVE":
        return "OK_TP" if positive else "MISS_FN"
    if exp == "NEGATIVE":
        return "OK_TN" if not positive else "FALSE_POS"
    if exp == "OPTIONAL":
        return "OK_OPT_HIT" if positive else "OK_OPT_NOHIT"
    return "UNKNOWN"


def main():
    rows = list(csv.DictReader(TSV.open(), delimiter="\t"))

    flipped = 0
    for r in rows:
        key = (r["organism"], r["marker"])
        if key in FLIPS:
            new_exp = FLIPS[key]
            old_v = r["verdict"]
            r["expectation"] = new_exp
            r["verdict"] = verdict(r["positive_call"] == "Y", new_exp)
            flipped += 1
            print(f"  {r['organism']:35s} x {r['marker']:18s}: {old_v:10s} -> {r['verdict']}")

    cols = list(rows[0].keys())
    with TSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"\nFlipped {flipped} rows in {TSV.name}")

    # Tally
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("\n=== Updated verdict tally ===")
    for k, v in sorted(counts.items()):
        print(f"  {k:18s} {v}")


if __name__ == "__main__":
    main()
