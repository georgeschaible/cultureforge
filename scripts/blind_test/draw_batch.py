#!/usr/bin/env python3
"""
Per-batch sampling script for the CultureForge blind-test cohort.

This is the executable form of §16 (one MAG per BioProject per batch)
and the §7 tier-quota draw, operating on the cleaned survivor pool
produced by `scripts/blind_test/filter_option1.py` (the §14 scope-filter
authority).

Authoritative methodology: §13 (discovery), §14 (scope filter), §15
(Bacteria + Archaea domain), and §16 (sampling constraint) of
`docs/phase6/blind_test_cohort_design.md`. The doc text controls;
this script is the executable form, not an alternative authority.

What it does:
  1. Reads the cleaned survivor pool (`survivors_v3.tsv` produced by
     `filter_option1.py`) and the category-bin counts.
  2. Builds a BioProject-by-accession map by scanning the broad-query
     JSONLs once (the `assembly_info.biosample.bioproject_accession`
     field, with the BioSample's `bioprojects[]` list as fallback).
  3. Runs a seeded draw under tier quotas (strong/mid/weak as CLI
     parameters): per tier, `random.sample` picks N distinct
     categories (alphabetical order recorded), then per chosen
     category `random.choice` picks one survivor.
  4. Enforces §16.2: if the chosen survivor's BioProject is already
     in the running set of drawn BioProjects, the survivor is
     rejected and re-drawn from the same pool (with the conflicting
     accession excluded). On pool exhaustion, the slot is left
     short, recorded as a §16-induced shortfall (no backfill, no
     filter relaxation — same as §13.2 shortfalls).
  5. Records the seed + tier quotas + draw order + the list of
     §16-rejected accessions in the output TSV header, so the
     rule's application is auditable from the artifact alone.

Reproducibility contract: [committed-script SHA] + [seed] + [tier
quotas] + [input artifacts at known content hashes] fully determine
the batch — including the list of §16-rejected accessions.
Re-running with the same arguments reproduces the batch exactly.

Usage:
  python3 scripts/blind_test/draw_batch.py \\
    --seed 20260601 \\
    --strong 2 --mid 4 --weak 2 \\
    --survivors data/validation/blind_test_batch1/survivors_v3.tsv \\
    --bins data/validation/blind_test_batch1/category_bins_v3.tsv \\
    --bact-jsonl data/validation/blind_test_batch1/broad_query_bacteria.jsonl \\
    --arch-jsonl data/validation/blind_test_batch1/broad_query_archaea.jsonl \\
    --output data/validation/blind_test_batch1/proposed_batch1.tsv

This script intentionally does NOT download genomes, run ANI/skani,
run CheckM2, run inspect, or produce any scoring output. It produces
a proposed-batch TSV for human review only.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path


# BioSample fields surfaced in the per-candidate provenance string
ENV_FIELDS = (
    "isolation_source", "env_broad_scale", "env_local_scale",
    "env_medium", "env_package", "env_feature",
    "host", "host_description", "host_taxid", "host_scientific_name",
    "geo_loc_name", "package",
)

MISSING_VALUES = (
    None, "", "missing", "Missing",
    "not applicable", "Not applicable", "not collected", "Not collected",
    "not provided", "Not provided",
)


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--seed", type=int, required=True,
                   help="Random seed (recorded in output TSV).")
    p.add_argument("--strong", type=int, default=2,
                   help="Number of strong-tier categories to sample.")
    p.add_argument("--mid", type=int, default=4,
                   help="Number of mid-tier categories to sample.")
    p.add_argument("--weak", type=int, default=2,
                   help="Number of weak-tier categories to sample.")
    p.add_argument("--survivors", type=Path, required=True,
                   help="Cleaned-survivor TSV from filter_option1.py.")
    p.add_argument("--bins", type=Path, required=True,
                   help="Category-bin counts TSV from filter_option1.py.")
    p.add_argument("--bact-jsonl", type=Path, required=True,
                   help="Bacteria broad-query JSONL.")
    p.add_argument("--arch-jsonl", type=Path, required=True,
                   help="Archaea broad-query JSONL.")
    p.add_argument("--output", type=Path, required=True,
                   help="Proposed-batch TSV output path.")
    return p.parse_args()


def read_bins(path):
    tier_cats = {"strong": [], "mid": [], "weak": []}
    bin_counts = {}
    with path.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["category"] == "UNBINNED":
                continue
            tier = row["strength_tier"]
            if tier not in tier_cats:
                continue
            tier_cats[tier].append(row["category"])
            bin_counts[row["category"]] = int(row["n_survivors"])
    for tier in tier_cats:
        tier_cats[tier].sort()
    return tier_cats, bin_counts


def read_survivors(path, bin_counts):
    """Partition survivors by category. Categories field is ';'-delimited."""
    survivors_by_cat = {cat: [] for cat in bin_counts}
    unbinned_count = 0
    binned_count = 0
    total_count = 0
    with path.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            total_count += 1
            cats_field = row["categories"]
            if cats_field == "UNBINNED":
                unbinned_count += 1
                continue
            binned_count += 1
            seen = set()
            for c in [s.strip() for s in cats_field.split(";")]:
                if c in survivors_by_cat and c not in seen:
                    survivors_by_cat[c].append(row["accession"])
                    seen.add(c)
    for cat in survivors_by_cat:
        survivors_by_cat[cat].sort()
    return survivors_by_cat, total_count, binned_count, unbinned_count


def extract_bioproject(rec):
    """Per §16.2: bioproject_accession field, with bioprojects[] list fallback."""
    bs = rec.get("assembly_info", {}).get("biosample", {})
    bp = bs.get("bioproject_accession", "") or ""
    if not bp:
        bps = bs.get("bioprojects") or []
        if isinstance(bps, list) and bps:
            bp = bps[0].get("accession", "") or ""
    return bp


def load_bioproject_map(*jsonl_paths):
    """Pass 1: build accession -> bioproject_accession map (str, '' if absent)."""
    bp_map = {}
    for path in jsonl_paths:
        with path.open() as f:
            for line in f:
                rec = json.loads(line)
                acc = rec.get("accession")
                if not acc:
                    continue
                bp_map[acc] = extract_bioproject(rec)
    return bp_map


def load_chosen_records(jsonl_paths, accessions):
    """Pass 2: full JSON records for the chosen accessions only."""
    records = {}
    remaining = set(accessions)
    for path in jsonl_paths:
        if not remaining:
            break
        with path.open() as f:
            for line in f:
                if not remaining:
                    break
                rec = json.loads(line)
                acc = rec.get("accession")
                if acc in remaining:
                    records[acc] = rec
                    remaining.remove(acc)
    return records


def biosample_attrs(rec):
    out = {}
    bs = rec.get("assembly_info", {}).get("biosample", {})
    for a in bs.get("attributes", []) or []:
        if "name" in a and "value" in a:
            out[a["name"]] = a["value"]
    for k in ENV_FIELDS:
        if k in bs and k not in out:
            out[k] = bs[k]
    return out


def fmt_env(rec):
    attrs = biosample_attrs(rec)
    parts = []
    for k in ENV_FIELDS:
        v = attrs.get(k, "")
        if isinstance(v, str):
            v = v.strip()
        if v in MISSING_VALUES:
            continue
        parts.append(f"{k}={v}")
    return " | ".join(parts) if parts else "(no env fields populated)"


def fmt_strain(rec):
    org = rec.get("organism", {})
    name = org.get("organism_name", "")
    infra = org.get("infraspecific_names") or {}
    strain = infra.get("strain") or infra.get("isolate") or ""
    if strain:
        return f"{name} (isolate {strain})"
    bs = rec.get("assembly_info", {}).get("biosample", {})
    iso = bs.get("isolate") or ""
    if iso:
        return f"{name} (isolate {iso})"
    return name


def draw_batch(tier_cats, survivors_by_cat, quotas, bioproject_by_acc, seed):
    """
    Implements §16.2 inside a §7 tier-quota draw.

    Draw order: strong → mid → weak; within each tier, alphabetical
    order of the categories that random.sample returned. Per chosen
    category, random.choice picks from a working copy of the sorted
    survivor pool; if the chosen survivor's BioProject is already in
    drawn_bioprojects, the survivor is rejected (recorded in
    rejections), removed from the working pool, and another
    random.choice is taken. Repeats until a non-conflict is found or
    the working pool is exhausted (§16-induced shortfall).

    Records with empty BioProject are treated as distinct (never
    conflict) per §16.2.
    """
    random.seed(seed)
    draws = []
    rejections = []
    drawn_bioprojects = set()

    for tier in ("strong", "mid", "weak"):
        n = quotas[tier]
        cats = tier_cats[tier]
        if n > len(cats):
            sys.stderr.write(
                f"ERROR: requested {n} {tier} cats but tier only has {len(cats)}\n"
            )
            sys.exit(2)
        chosen_cats = random.sample(cats, n)
        chosen_cats.sort()
        for cat in chosen_cats:
            pool = list(survivors_by_cat[cat])
            picked = None
            if not pool:
                draws.append({
                    "tier": tier, "category": cat, "accession": None,
                    "shortfall": True,
                    "shortfall_reason": "§13.2 — category empty in survivor pool",
                })
                continue
            while pool:
                pick = random.choice(pool)
                bp = bioproject_by_acc.get(pick, "")
                if bp and bp in drawn_bioprojects:
                    rejections.append({
                        "tier": tier, "category": cat,
                        "rejected_accession": pick,
                        "rejected_bioproject": bp,
                        "reason": f"§16 — BioProject {bp} already drawn earlier in this batch",
                    })
                    pool = [a for a in pool if a != pick]
                    continue
                picked = pick
                if bp:
                    drawn_bioprojects.add(bp)
                break
            if picked is None:
                draws.append({
                    "tier": tier, "category": cat, "accession": None,
                    "shortfall": True,
                    "shortfall_reason": (
                        "§16 — pool exhausted by BioProject conflicts "
                        "(no eligible non-conflicting BioProject in category pool)"
                    ),
                })
            else:
                draws.append({
                    "tier": tier, "category": cat, "accession": picked,
                    "shortfall": False,
                })
    return draws, rejections


OUTPUT_COLUMNS = [
    "tier", "category", "tier_position", "shortfall", "shortfall_reason",
    "accession", "organism_with_strain", "biosample_accession",
    "release_date", "bioproject_accession", "biosample_provenance",
    "geo_loc_name", "package", "source_option", "draw_seed",
]


def write_output(out_path, draws, rejections, records, bioproject_by_acc,
                 seed, quotas, tier_cats, bin_counts,
                 total_count, binned_count, unbinned_count,
                 survivors_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        f.write(f"# Blind-test cohort proposed-batch draw — Option 1 (A3 broad query + post-hoc binning)\n")
        f.write(f"# Sampling-step methodology: §13 + §14 + §15 + §16 of "
                f"docs/phase6/blind_test_cohort_design.md\n")
        f.write(f"# Executable form of §16.2: scripts/blind_test/draw_batch.py\n")
        f.write(f"# Pool: {survivors_path} ({total_count} survivors, "
                f"{binned_count} binned, {unbinned_count} UNBINNED)\n")
        f.write(f"# UNBINNED not eligible for category-targeted sampling "
                f"(not a problem — just not category-addressable per §13.2 binner)\n")
        f.write(f"# Seed: {seed}\n")
        f.write(f"# Tier quotas: strong={quotas['strong']}, mid={quotas['mid']}, "
                f"weak={quotas['weak']} (target={sum(quotas.values())})\n")
        f.write(f"# Draw order: strong → mid → weak; "
                f"within tier, alphabetical order of chosen categories\n")
        f.write(f"# Constraint: §16 one-per-BioProject within batch "
                f"(later-drawn rejected on conflict, re-drawn from same pool)\n")
        f.write(f"#\n")
        f.write(f"# §16-rejected accessions ({len(rejections)} total — "
                f"reproduces the rule's application):\n")
        if rejections:
            for r in rejections:
                f.write(f"#   [{r['tier']}] {r['category']}: rejected {r['rejected_accession']} "
                        f"(BioProject {r['rejected_bioproject']}) — {r['reason']}\n")
        else:
            f.write(f"#   (none — no §16 conflict surfaced at this seed)\n")
        f.write(f"#\n")
        f.write(f"# Bin eligibility (n_survivors per category):\n")
        for tier in ("strong", "mid", "weak"):
            for cat in tier_cats[tier]:
                f.write(f"#   [{tier}] {cat}: {bin_counts[cat]}\n")
        f.write("#\n")

        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, delimiter="\t")
        w.writeheader()

        tier_seen = {"strong": 0, "mid": 0, "weak": 0}
        for d in draws:
            tier_seen[d["tier"]] += 1
            pos = f"{d['tier']}_{tier_seen[d['tier']]}"
            if d["shortfall"]:
                w.writerow({
                    "tier": d["tier"], "category": d["category"],
                    "tier_position": pos,
                    "shortfall": "YES",
                    "shortfall_reason": d["shortfall_reason"],
                    "accession": "(slot left short — see shortfall_reason)",
                    "organism_with_strain": "",
                    "biosample_accession": "", "release_date": "",
                    "bioproject_accession": "",
                    "biosample_provenance": "",
                    "geo_loc_name": "", "package": "",
                    "source_option": "Option 1 (A3 broad query + post-hoc binning)",
                    "draw_seed": str(seed),
                })
                continue
            rec = records[d["accession"]]
            bs = rec.get("assembly_info", {}).get("biosample", {})
            attrs = biosample_attrs(rec)
            w.writerow({
                "tier": d["tier"], "category": d["category"],
                "tier_position": pos,
                "shortfall": "NO",
                "shortfall_reason": "",
                "accession": d["accession"],
                "organism_with_strain": fmt_strain(rec),
                "biosample_accession": bs.get("accession", "") or "",
                "release_date": rec.get("assembly_info", {}).get("release_date", "") or "",
                "bioproject_accession": bioproject_by_acc.get(d["accession"], "") or "",
                "biosample_provenance": fmt_env(rec),
                "geo_loc_name": attrs.get("geo_loc_name", "") or bs.get("geo_loc_name", "") or "",
                "package": attrs.get("package", "") or bs.get("package", "") or "",
                "source_option": "Option 1 (A3 broad query + post-hoc binning)",
                "draw_seed": str(seed),
            })


def main():
    args = parse_args()
    quotas = {"strong": args.strong, "mid": args.mid, "weak": args.weak}

    tier_cats, bin_counts = read_bins(args.bins)
    survivors_by_cat, total, binned, unbinned = read_survivors(
        args.survivors, bin_counts
    )

    # Sanity-check parser against bins file (catches delimiter/parsing drift)
    for cat, n in bin_counts.items():
        got = len(survivors_by_cat[cat])
        if got != n:
            sys.stderr.write(
                f"WARN: bin '{cat}' expected {n}, got {got} "
                f"(check ';' delimiter and category-name spelling)\n"
            )

    # Pass 1: BioProject map for the full record set
    bp_map = load_bioproject_map(args.bact_jsonl, args.arch_jsonl)

    # Run the §16-constrained draw
    draws, rejections = draw_batch(tier_cats, survivors_by_cat, quotas,
                                   bp_map, args.seed)

    # Pass 2: fetch full records for the (non-shortfall) chosen accessions
    chosen = [d["accession"] for d in draws if d["accession"]]
    records = load_chosen_records((args.bact_jsonl, args.arch_jsonl), chosen)
    missing = set(chosen) - set(records.keys())
    if missing:
        sys.stderr.write(f"ERROR: missing JSONL records for {missing}\n")
        sys.exit(2)

    write_output(args.output, draws, rejections, records, bp_map,
                 args.seed, quotas, tier_cats, bin_counts,
                 total, binned, unbinned, args.survivors)

    # Stdout summary
    print(f"SEED: {args.seed}")
    print(f"Pool: {total} survivors total | {binned} binned | "
          f"{unbinned} UNBINNED (not eligible)")
    print()
    print("Tier-category random selection:")
    for tier in ("strong", "mid", "weak"):
        sel = [d["category"] for d in draws if d["tier"] == tier]
        print(f"  [{tier}] picked {len(sel)} of {len(tier_cats[tier])}: "
              f"{', '.join(sel)}")
    print()
    if rejections:
        print(f"§16-rejected accessions ({len(rejections)}):")
        for r in rejections:
            print(f"  [{r['tier']}] {r['category']}: rejected {r['rejected_accession']} "
                  f"(BP {r['rejected_bioproject']})")
        print()
    print("Drawn organisms:")
    print("=" * 92)
    for d in draws:
        if d["shortfall"]:
            print(f"  [{d['tier']:6s}] {d['category']:22s}  SHORTFALL ({d['shortfall_reason']})")
            continue
        rec = records[d["accession"]]
        name = fmt_strain(rec)
        date = rec.get("assembly_info", {}).get("release_date", "") or ""
        bp = bp_map.get(d["accession"], "") or "(no BP)"
        print(f"  [{d['tier']:6s}] {d['category']:22s}  {d['accession']:18s}  "
              f"{date}  {bp:15s}  {name[:40]}")
    print("=" * 92)
    n_filled = sum(1 for d in draws if not d["shortfall"])
    n_short = sum(1 for d in draws if d["shortfall"])
    print(f"\nTotal drawn: {n_filled} / {sum(quotas.values())} target  |  "
          f"Shortfalls: {n_short}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
