#!/usr/bin/env python3
"""
Survivor-pool pre-filter for the CultureForge blind-test cohort.

This is the executable form of §18.2.A (the published-completeness
pool pre-filter) and produces the v4 pool described in §18.7.1, the
implementation step that takes the §14/§15/§16/§17-locked v3 pool
and applies the §18.2.A rule to produce `survivors_v4.tsv`.

Authoritative methodology: §13 (discovery), §14 (scope filter), §15
(Bacteria + Archaea domain), §16 (sampling constraint), §17 (held-out
ANI alignment-fraction floor), and §18 (pool pre-filter + CheckM2
binding gate) of `docs/phase6/blind_test_cohort_design.md`. The doc
text controls; this script is the executable form of §18.2.A, not an
alternative authority.

§18.2.A rule:
  Exclude any MAG with published completeness < 70% OR published
  contamination > 5%. KEEP published-passing MAGs AND MAGs with no
  published completeness/contamination data. The no-data fallback
  is the deliberate §18 design point: it protects data-sparse hard
  categories (ANME, cable bacteria, lithoautotrophic iron, extreme
  archaea — see the §18.7 ablation) from over-filtering.

Operative pool — important:
  The input is `survivors_v3.tsv` (the 89,665-record pool produced
  by `scripts/blind_test/filter_option1.py`), NOT the 89,687-record
  `scope_filter_kept_v3.jsonl` superset. The 22-record gap is the
  §14 mechanical filter's dev-cohort marker contamination guard
  (records whose taxid is in `marker_taxids.txt`, rejected with
  reason `taxid_in_marker_refs` in `mechanical_filter_rejected_v3.tsv`).
  Those 22 records are NOT in the operative pool and play no role
  in §18.2.A's decisions. The JSONL is read only to look up each
  v3-TSV record's published completeness/contamination attributes.

Field detection (mirrors `completeness_ablation.tsv`):
  Any BioSample attribute under `assembly_info.biosample.attributes[]`
  whose `name` (case-insensitive) contains 'completeness' or
  'contamination', EXCLUDING any attribute whose name contains
  'software' (which catches '*_software' tool-name fields). Values
  are parsed as floats with a trailing '%' tolerated. If either
  attribute is missing, the record is classified `no-published-data`.

What it does:
  1. Loads v3-TSV accessions into a set (the operative pool).
  2. Streams `scope_filter_kept_v3.jsonl` once, building a
     decision map `{accession -> (status, completeness, contamination)}`
     restricted to v3-pool accessions. `status` is one of:
       - "pass"    — has data, passes both thresholds  (KEEP)
       - "no_data" — missing one or both attributes    (KEEP per §18.2.A)
       - "fail"    — has data, fails at least one      (DROP)
  3. Streams `survivors_v3.tsv` row-by-row, writing v4 records to
     `survivors_v4.tsv` (same 9-column schema, byte-identical row
     content) for any row classified pass-or-no_data.
  4. Recomputes per-category bin counts from the v4 records and
     writes `category_bins_v4.tsv` (same schema and category order
     as `category_bins_v3.tsv`).
  5. Reports the binding v4 pool size, per-category v3→v4 deltas,
     v3-restricted dispositions, and a sanity check on the three
     already-CheckM2-verified candidates (GCA_054919905.1,
     GCA_055897235.1, GCA_057266155.1) — all three must survive
     into v4 because they classify as no-data.

Reproducibility contract: [committed-script SHA] + [thresholds
70% completeness / 5% contamination, both written in source]
+ [input artifacts at known content hashes] fully determine the
v4 pool. Re-running reproduces v4 exactly.

Usage:
  python3 scripts/blind_test/refilter_v4.py

  All paths are hardcoded to the §18.7.1 v3→v4 transition. If a
  future amendment requires another transition (e.g. v5), it will
  be implemented as its own committed script under
  `scripts/blind_test/`, not by retro-fitting this one — matching
  the v3-vs-v2 separation already established in filter_option1.py.

This script intentionally does NOT download genomes, run ANI/skani,
run CheckM2, or produce any scoring output. It produces the
pre-filtered pool TSV and bin counts for the §18.7.2 draw.
"""
import json
import os
import sys
from collections import defaultdict

ROOT = "/home/george/cultureforge"
BT = os.path.join(ROOT, "data/validation/blind_test_batch1")
KEPT_JSONL = os.path.join(BT, "scope_filter_kept_v3.jsonl")
SURV_V3 = os.path.join(BT, "survivors_v3.tsv")
BINS_V3 = os.path.join(BT, "category_bins_v3.tsv")
SURV_V4 = os.path.join(BT, "survivors_v4.tsv")
BINS_V4 = os.path.join(BT, "category_bins_v4.tsv")

COMPL_THRESHOLD = 70.0   # §3, §18.2.A
CONTAM_THRESHOLD = 5.0   # §3, §18.2.A


def parse_float(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if s.endswith("%"):
        s = s[:-1].strip()
    try:
        return float(s)
    except ValueError:
        return None


def extract_compl_contam(rec):
    """Returns (completeness, contamination); either may be None."""
    bs = rec.get("assembly_info", {}).get("biosample", {})
    attrs = bs.get("attributes", []) or []
    compl = None
    contam = None
    for a in attrs:
        name = (a.get("name") or "").strip()
        if not name:
            continue
        low = name.lower()
        if "software" in low:
            continue
        val = parse_float(a.get("value"))
        if val is None:
            continue
        if "completeness" in low and compl is None:
            compl = val
        elif "contamination" in low and contam is None:
            contam = val
    return compl, contam


def main():
    # 1. Load the v3-TSV operative pool (89,665 accessions).
    v3_accs = set()
    with open(SURV_V3) as f:
        f.readline()
        for line in f:
            parts = line.split("\t")
            if parts:
                v3_accs.add(parts[0])

    # 2. Stream the JSONL once, building decisions only for v3-pool accessions.
    decisions = {}
    n_pass = n_no_data = 0
    fail_compl_only = fail_contam_only = fail_both = 0
    with open(KEPT_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            acc = rec.get("accession")
            if acc not in v3_accs:
                continue
            compl, contam = extract_compl_contam(rec)
            has_compl = compl is not None
            has_contam = contam is not None
            if not has_compl and not has_contam:
                decisions[acc] = ("no_data", None, None)
                n_no_data += 1
                continue
            failed_compl = has_compl and compl < COMPL_THRESHOLD
            failed_contam = has_contam and contam > CONTAM_THRESHOLD
            if failed_compl or failed_contam:
                if failed_compl and failed_contam:
                    fail_both += 1
                elif failed_compl:
                    fail_compl_only += 1
                else:
                    fail_contam_only += 1
                decisions[acc] = ("fail", compl, contam)
            else:
                decisions[acc] = ("pass", compl, contam)
                n_pass += 1

    n_fail = fail_compl_only + fail_contam_only + fail_both

    # Safety: every v3 accession must have a decision (clean-subset invariant).
    if len(decisions) != len(v3_accs):
        missing = v3_accs - set(decisions.keys())
        sys.exit(
            f"FATAL: {len(missing)} v3 accessions had no JSONL decision. "
            f"This breaks the §14 mechanical-filter / scope-filter-kept "
            f"clean-subset invariant. First 5: {sorted(missing)[:5]}"
        )

    # 3. Load v3 category-bin order so v4 bins match the v3 row order.
    v3_cat_order = []
    with open(BINS_V3) as f:
        f.readline()
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            cat, tier, n = line.split("\t")
            v3_cat_order.append((cat, tier, int(n)))

    # 4. Stream v3 TSV → v4 TSV under §18.2.A.
    n_v3 = n_v4 = n_excluded = 0
    cat_v4 = defaultdict(int)
    excluded_examples = []
    with open(SURV_V3) as f, open(SURV_V4, "w") as out:
        out.write(f.readline())   # passthrough header
        for line in f:
            if not line.endswith("\n"):
                line += "\n"
            n_v3 += 1
            parts = line.rstrip("\n").split("\t")
            acc = parts[0]
            cats_field = parts[8] if len(parts) >= 9 else ""
            status, compl, contam = decisions[acc]
            if status == "fail":
                n_excluded += 1
                if len(excluded_examples) < 5:
                    excluded_examples.append((acc, compl, contam, cats_field))
                continue
            out.write(line)
            n_v4 += 1
            for c in cats_field.split(";"):
                c = c.strip()
                if c:
                    cat_v4[c] += 1

    # 5. Write category_bins_v4.tsv in v3 row order.
    with open(BINS_V4, "w") as f:
        f.write("category\tstrength_tier\tn_survivors\n")
        for cat, tier, _ in v3_cat_order:
            f.write(f"{cat}\t{tier}\t{cat_v4.get(cat, 0)}\n")

    # 6. Report.
    print("=" * 70)
    print("§18.7.1 RE-FILTER REPORT — v3→v4 under §18.2.A")
    print("=" * 70)
    print()
    print(f"v3 operative pool:   {n_v3:>7d}")
    print(f"v4 pool size:        {n_v4:>7d}  ← BINDING (was not pre-committed in §18)")
    print(f"Excluded (§18.2.A):  {n_excluded:>7d}")
    print()
    print("v3-restricted dispositions (tight — no JSONL-superset spillover):")
    total = n_pass + n_no_data + n_fail
    print(f"  published-pass:    {n_pass:>7d}  ({100.0 * n_pass / total:.2f}%)")
    print(f"  no-published-data: {n_no_data:>7d}  ({100.0 * n_no_data / total:.2f}%)")
    print(f"  published-fail:    {n_fail:>7d}  ({100.0 * n_fail / total:.2f}%)")
    print(f"    fail completeness only: {fail_compl_only}")
    print(f"    fail contamination only: {fail_contam_only}")
    print(f"    fail both:               {fail_both}")
    print()
    print("Per-category v3→v4:")
    print(f"  {'category':<22} {'tier':<7} {'v3':>7} {'v4':>7} {'Δ':>7} {'kept%':>7}")
    for cat, tier, nv3 in v3_cat_order:
        nv4 = cat_v4.get(cat, 0)
        delta = nv4 - nv3
        pct = (100.0 * nv4 / nv3) if nv3 else 0.0
        print(f"  {cat:<22} {tier:<7} {nv3:>7d} {nv4:>7d} {delta:>+7d} {pct:>6.1f}%")
    print()
    print("Already-CheckM2-verified candidates — must survive in v4:")
    for acc, label in [
        ("GCA_054919905.1", "halophile (#5)"),
        ("GCA_055897235.1", "hyperthermophile (#6)"),
        ("GCA_057266155.1", "ANME (#7)"),
    ]:
        d = decisions.get(acc)
        if d is None:
            print(f"  {acc}  {label}: NOT IN v3 ← FLAG")
        else:
            status, compl, contam = d
            kept = status in ("pass", "no_data")
            marker = "in v4 ✓" if kept else "EXCLUDED ← FLAG"
            print(f"  {acc}  {label}: status={status}  compl={compl}  contam={contam}  → {marker}")
    print()
    if excluded_examples:
        print("First 5 excluded examples (acc, compl, contam, categories):")
        for ex in excluded_examples:
            print(f"  {ex}")
    print()
    print(f"Wrote: {SURV_V4}")
    print(f"Wrote: {BINS_V4}")


if __name__ == "__main__":
    main()
