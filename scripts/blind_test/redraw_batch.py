#!/usr/bin/env python3
"""
Replacement-slot redraw for the CultureForge blind-test cohort, applied
after a §16 first-draw batch has been verified and one or more picks
have failed §17 (held-out ANI) and/or §18 (CheckM2) gates.

This is the executable form of the §16-style reject-and-redraw mechanic
applied to verification-failed candidates. Same semantic as a §16
BioProject conflict (the acc is removed from the working pool and the
slot gets the next random.choice), but the trigger is "failed Task 3
verification" rather than "BioProject conflict with earlier-drawn pick".

Authoritative methodology: §13 (discovery), §14 (scope filter), §15
(Bacteria + Archaea domain), §16 (sampling constraint), §17 (held-out
ANI alignment-fraction floor), and §18 (pool pre-filter + CheckM2
binding gate) of `docs/phase6/blind_test_cohort_design.md`. The doc
text controls; this script is the executable form for §16-style
redraw after verification, not an alternative authority.

Algorithm — per-slot independent RNG replay:

  1. Run the original §16 first-draw at the same seed (delegating to
     draw_batch.draw_batch) to identify which slot(s) each --exclude
     accession originated from.
  2. For each failed slot, in original draw order:
     a. Replay the seed up to (but not including) the failed slot's
        first random.choice — one random.choice per non-empty prior
        slot, no §16/exclusion check during the replay. This matches
        the original draw's RNG-consumption pattern exactly when the
        original draw produced 0 §16 rejections (the typical case).
     b. At the failed slot, draw with reject-and-redraw:
        - random.choice from the sorted pool.
        - If pick is in --exclude, reject (record, remove from pool,
          retry) — same mechanic as §16, different trigger.
        - Else if pick's BioProject is in `keeper_bps`, reject (§16).
        - Else commit as the replacement.
  3. `keeper_bps` composition (the key difference from draw_batch):
     - {BPs of --keep accessions} ∪ {BPs of replacements committed
       earlier in the failed-slot iteration order}.
     - Static at the start of each slot, NOT a running set that
       accumulates as the script picks slots. This is what makes the
       redraw "consistent with the verified keepers" rather than
       "consistent with the draw order it happens to take".

Why per-slot independent replay rather than `draw_batch --exclude`:

  A naïve --exclude flag inside draw_batch's cumulative loop (treat
  excluded picks as §16-rejects) would do an extra random.choice at
  the first failed slot to skip the excluded accession. That extra
  random.choice shifts the RNG state for every later slot — including
  slots whose original picks PASSED verification. The kept picks
  would not reproduce. Per-slot independent replay restarts from the
  seed for each failed slot, advances by exactly the original draw's
  RNG-consumption pattern, and so the kept slots are untouched.

Reproducibility contract: [committed-script SHA] + [seed] + [tier
quotas] + [pool TSV content hash] + [BioProject JSONL content hashes]
+ [exclusion set] + [keep set] fully determine the replacement-slot
TSV. Re-running with the same arguments reproduces the replacements
byte-identically.

Recorded use — batch 1 (manuscript provenance):

  After §16 first-draw at seed 20260603 from survivors_v4.tsv produced
  7 candidates + 1 §13.2 shortfall (comammox), Task 3 verification
  failed two picks: GCA_055108635.1 (halophile, CheckM2 completeness
  55.96% < §3 threshold) and GCA_054608515.1 (lithoautotrophic iron,
  held-out ANI 98.21% / 78.34% AFq / 68.26% AFr to dev cohort gid 11
  — §17 trigger). This script was run with:

    --seed 20260603 --strong 2 --mid 4 --weak 2
    --exclude GCA_055108635.1,GCA_054608515.1
    --keep    GCA_964732075.1,GCA_982640665.1,GCA_982592295.1,
              GCA_977678135.1,GCA_057266155.1
    --survivors data/validation/blind_test_batch1/survivors_v4.tsv
    --bins      data/validation/blind_test_batch1/category_bins_v4.tsv
    --bact-jsonl data/validation/blind_test_batch1/broad_query_bacteria.jsonl
    --arch-jsonl data/validation/blind_test_batch1/broad_query_archaea.jsonl

  Produces the two replacements:
    halophile             -> GCA_054328135.1 (BP PRJNA1306690)
    lithoautotrophic iron -> GCA_054603255.1 (BP PRJNA1017420)

Usage:
  python3 scripts/blind_test/redraw_batch.py \\
    --seed 20260603 \\
    --strong 2 --mid 4 --weak 2 \\
    --survivors data/validation/blind_test_batch1/survivors_v4.tsv \\
    --bins data/validation/blind_test_batch1/category_bins_v4.tsv \\
    --bact-jsonl data/validation/blind_test_batch1/broad_query_bacteria.jsonl \\
    --arch-jsonl data/validation/blind_test_batch1/broad_query_archaea.jsonl \\
    --exclude GCA_055108635.1,GCA_054608515.1 \\
    --keep GCA_964732075.1,GCA_982640665.1,GCA_982592295.1,GCA_977678135.1,GCA_057266155.1 \\
    --output data/validation/blind_test_batch1/proposed_batch1_v4_repl.tsv

This script intentionally does NOT download genomes, run ANI/skani,
run CheckM2, run inspect, or produce any scoring output. It produces
a replacement-slot proposed TSV for human review only.
"""
import argparse
import csv
import random
import sys
from pathlib import Path

# Single source of truth for I/O + record formatting — do NOT duplicate
# these helpers here, so the reproduction guarantee can't silently rot
# from drift between draw_batch and redraw_batch.
import draw_batch as db
from draw_batch import (
    read_bins, read_survivors, load_bioproject_map, load_chosen_records,
    extract_bioproject, biosample_attrs, fmt_env, fmt_strain,
    OUTPUT_COLUMNS,
)


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--seed", type=int, required=True,
                   help="Random seed of the ORIGINAL §16 first-draw (recorded in output).")
    p.add_argument("--strong", type=int, default=2,
                   help="Strong-tier quota used in the original draw.")
    p.add_argument("--mid", type=int, default=4,
                   help="Mid-tier quota used in the original draw.")
    p.add_argument("--weak", type=int, default=2,
                   help="Weak-tier quota used in the original draw.")
    p.add_argument("--survivors", type=Path, required=True,
                   help="Cleaned-survivor pool TSV used in the original draw.")
    p.add_argument("--bins", type=Path, required=True,
                   help="Category-bin counts TSV used in the original draw.")
    p.add_argument("--bact-jsonl", type=Path, required=True,
                   help="Bacteria broad-query JSONL.")
    p.add_argument("--arch-jsonl", type=Path, required=True,
                   help="Archaea broad-query JSONL.")
    p.add_argument("--exclude", required=True,
                   help="Comma-separated accessions to exclude "
                        "(verification-failed picks from the original draw).")
    p.add_argument("--keep", required=True,
                   help="Comma-separated accessions kept from the original draw "
                        "(verification-passed picks). Their BioProjects seed "
                        "the keeper_bps set used for §16 enforcement.")
    p.add_argument("--output", type=Path, required=True,
                   help="Replacement-slot TSV output path.")
    return p.parse_args()


def parse_acc_list(s):
    return [a.strip() for a in s.split(",") if a.strip()]


def advance_rng_to_slot(target_tier, target_cat, tier_cats,
                        survivors_by_cat, quotas, seed):
    """Replay the seed up to (but not including) the target slot's first
    random.choice.

    Validity contract: this uses one random.choice per non-empty prior
    slot with no §16/exclusion check during the replay. That matches
    the original draw's RNG-consumption pattern IFF the original draw
    produced 0 §16 rejections at this seed (one random.choice per
    non-shortfall slot). If the original draw had rejections at this
    seed, this replay would land at the wrong RNG state and the
    replacements would not reproduce — the caller (main) must verify
    the original draw is rejection-free before calling this.
    """
    random.seed(seed)
    for tier in ("strong", "mid", "weak"):
        chosen = sorted(random.sample(tier_cats[tier], quotas[tier]))
        for cat in chosen:
            if tier == target_tier and cat == target_cat:
                return
            pool = list(survivors_by_cat[cat])
            if not pool:
                continue
            _ = random.choice(pool)
    raise RuntimeError(
        f"replay did not reach slot ({target_tier}, {target_cat}) — "
        "category not in tier_cats? quotas mismatched between draw and redraw?"
    )


def redraw_slot(target_tier, target_cat, tier_cats, survivors_by_cat,
                bp_map, seed, quotas, exclusion_set, keeper_bps):
    """Per-slot independent redraw: advance to target, then reject-and-
    redraw on exclusion or §16 conflict until a non-conflict pick is
    found (or pool is exhausted)."""
    advance_rng_to_slot(target_tier, target_cat, tier_cats,
                        survivors_by_cat, quotas, seed)
    pool = list(survivors_by_cat[target_cat])
    rejections = []
    while pool:
        pick = random.choice(pool)
        bp = bp_map.get(pick, "")
        if pick in exclusion_set:
            rejections.append({
                "tier": target_tier, "category": target_cat,
                "rejected_accession": pick, "rejected_bioproject": bp,
                "reason": "exclusion — accession in --exclude (verification-failed)",
            })
            pool = [a for a in pool if a != pick]
            continue
        if bp and bp in keeper_bps:
            rejections.append({
                "tier": target_tier, "category": target_cat,
                "rejected_accession": pick, "rejected_bioproject": bp,
                "reason": f"§16 — BioProject {bp} held by a keeper or earlier replacement",
            })
            pool = [a for a in pool if a != pick]
            continue
        return pick, bp, rejections
    return None, "", rejections


def identify_failed_slots(draws, exclusion_set):
    """Walk the original draw in order, return [(tier, category,
    original_acc)] for each slot whose pick is in --exclude."""
    failed = []
    for d in draws:
        if d.get("accession") in exclusion_set:
            failed.append((d["tier"], d["category"], d["accession"]))
    return failed


def validate_partition(draws, keep_set, exclude_set):
    """The --keep ∪ --exclude must cover all non-shortfall original picks,
    must be disjoint, and every --keep/--exclude acc must appear in the
    original draw. Catches incomplete or contradictory verification states
    before the redraw runs."""
    drawn_accs = {d["accession"] for d in draws if d.get("accession")}
    overlap = keep_set & exclude_set
    if overlap:
        sys.exit(f"ERROR: --keep and --exclude overlap on {sorted(overlap)} "
                 "(an accession cannot be both verified and failed).")
    extra_keep = keep_set - drawn_accs
    if extra_keep:
        sys.exit(f"ERROR: --keep contains accessions not in original draw at "
                 f"this seed/quotas: {sorted(extra_keep)}")
    extra_excl = exclude_set - drawn_accs
    if extra_excl:
        sys.exit(f"ERROR: --exclude contains accessions not in original draw at "
                 f"this seed/quotas: {sorted(extra_excl)}")
    uncovered = drawn_accs - keep_set - exclude_set
    if uncovered:
        sys.exit(f"ERROR: original draw has non-shortfall picks not classified "
                 f"in --keep or --exclude: {sorted(uncovered)} — verification "
                 "state is incomplete.")


def write_output(out_path, replacements, all_rejections, records, bp_map,
                 seed, quotas, tier_cats, bin_counts,
                 total_count, binned_count, unbinned_count,
                 survivors_path, exclude_set, keep_set, keep_bps_initial,
                 failed_slots):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        f.write("# Blind-test cohort REPLACEMENT-SLOT draw — §16-style reject-and-redraw\n")
        f.write("# Sampling-step methodology: §13 + §14 + §15 + §16 + §17 + §18 of "
                "docs/phase6/blind_test_cohort_design.md\n")
        f.write("# Executable form of §16-style redraw: scripts/blind_test/redraw_batch.py\n")
        f.write(f"# Pool: {survivors_path} ({total_count} survivors, "
                f"{binned_count} binned, {unbinned_count} UNBINNED)\n")
        f.write(f"# Seed (original draw): {seed}\n")
        f.write(f"# Tier quotas (original draw): strong={quotas['strong']}, "
                f"mid={quotas['mid']}, weak={quotas['weak']}\n")
        f.write(f"# Exclusion set ({len(exclude_set)}): {','.join(sorted(exclude_set))}\n")
        f.write(f"# Keep set ({len(keep_set)}): {','.join(sorted(keep_set))}\n")
        f.write(f"# Initial keeper_bps from --keep: "
                f"{','.join(sorted(keep_bps_initial)) if keep_bps_initial else '(none)'}\n")
        f.write("# Mechanic: per-slot independent RNG replay (see module docstring).\n")
        f.write("#\n")
        f.write(f"# Failed slots identified from original draw ({len(failed_slots)}):\n")
        for tier, cat, orig in failed_slots:
            f.write(f"#   [{tier}] {cat}: original pick {orig} (in --exclude)\n")
        f.write("#\n")
        f.write(f"# Rejections during redraw ({len(all_rejections)}):\n")
        if all_rejections:
            for r in all_rejections:
                f.write(f"#   [{r['tier']}] {r['category']}: rejected "
                        f"{r['rejected_accession']} "
                        f"(BP {r['rejected_bioproject'] or '(none)'}) — {r['reason']}\n")
        else:
            f.write("#   (none)\n")
        f.write("#\n")

        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, delimiter="\t")
        w.writeheader()
        for r in replacements:
            if r["accession"] is None:
                w.writerow({
                    "tier": r["tier"], "category": r["category"],
                    "tier_position": r["tier_position"],
                    "shortfall": "YES",
                    "shortfall_reason": r["shortfall_reason"],
                    "accession": "(replacement slot left short — pool exhausted)",
                    "organism_with_strain": "",
                    "biosample_accession": "", "release_date": "",
                    "bioproject_accession": "",
                    "biosample_provenance": "",
                    "geo_loc_name": "", "package": "",
                    "source_option": "Option 1 (A3 broad query + post-hoc binning) — redraw",
                    "draw_seed": str(seed),
                })
                continue
            rec = records[r["accession"]]
            bs = rec.get("assembly_info", {}).get("biosample", {})
            attrs = biosample_attrs(rec)
            w.writerow({
                "tier": r["tier"], "category": r["category"],
                "tier_position": r["tier_position"],
                "shortfall": "NO",
                "shortfall_reason": "",
                "accession": r["accession"],
                "organism_with_strain": fmt_strain(rec),
                "biosample_accession": bs.get("accession", "") or "",
                "release_date": rec.get("assembly_info", {}).get("release_date", "") or "",
                "bioproject_accession": bp_map.get(r["accession"], "") or "",
                "biosample_provenance": fmt_env(rec),
                "geo_loc_name": attrs.get("geo_loc_name", "") or bs.get("geo_loc_name", "") or "",
                "package": attrs.get("package", "") or bs.get("package", "") or "",
                "source_option": "Option 1 (A3 broad query + post-hoc binning) — redraw",
                "draw_seed": str(seed),
            })


def main():
    args = parse_args()
    quotas = {"strong": args.strong, "mid": args.mid, "weak": args.weak}
    exclude_set = set(parse_acc_list(args.exclude))
    keep_set = set(parse_acc_list(args.keep))

    tier_cats, bin_counts = read_bins(args.bins)
    survivors_by_cat, total, binned, unbinned = read_survivors(args.survivors, bin_counts)
    bp_map = load_bioproject_map(args.bact_jsonl, args.arch_jsonl)

    # Step 1: replay the original §16 first-draw to identify failed slots
    # and to verify the rejection-free precondition required by the replay.
    orig_draws, orig_rejections = db.draw_batch(tier_cats, survivors_by_cat,
                                                quotas, bp_map, args.seed)
    if orig_rejections:
        sys.exit(
            f"ERROR: original draw at seed {args.seed} produced "
            f"{len(orig_rejections)} §16 rejection(s); per-slot replay's "
            "advance assumes zero rejections (one random.choice per "
            "non-shortfall slot). Replacement reproduction is not guaranteed "
            "in this case — extend the replay mechanic before proceeding."
        )

    validate_partition(orig_draws, keep_set, exclude_set)
    failed_slots = identify_failed_slots(orig_draws, exclude_set)
    if len(failed_slots) != len(exclude_set):
        # Defensive: any --exclude entry must hit exactly one slot.
        sys.exit(
            f"ERROR: {len(exclude_set)} --exclude accessions but "
            f"{len(failed_slots)} matched failed slots in original draw"
        )

    # Step 2: per-slot independent redraw, in original draw order.
    # keeper_bps starts from --keep's BPs and grows with prior replacements'
    # BPs as we walk through failed_slots in order.
    keeper_bps = {bp for bp in (bp_map.get(a, "") for a in keep_set) if bp}
    keeper_bps_initial = set(keeper_bps)

    # Position counter mirrors draw_batch's tier_position labeling — within
    # each tier, count among ORIGINAL non-shortfall draws so replacement
    # positions match the original-batch layout.
    tier_positions = {}
    for d in orig_draws:
        tier_positions.setdefault(d["tier"], 0)
        tier_positions[d["tier"]] += 1
        d["_position_label"] = f"{d['tier']}_{tier_positions[d['tier']]}"
    pos_by_slot = {(d["tier"], d["category"]): d["_position_label"]
                   for d in orig_draws}

    replacements = []
    all_rejections = []
    for tier, cat, orig_acc in failed_slots:
        pick, bp, rejs = redraw_slot(
            tier, cat, tier_cats, survivors_by_cat,
            bp_map, args.seed, quotas, exclude_set, keeper_bps,
        )
        all_rejections.extend(rejs)
        if pick is None:
            replacements.append({
                "tier": tier, "category": cat,
                "tier_position": pos_by_slot[(tier, cat)],
                "accession": None,
                "shortfall_reason": (
                    "§16 + exclusion — replacement pool exhausted "
                    "(no eligible non-conflicting non-excluded acc in category)"
                ),
            })
            continue
        replacements.append({
            "tier": tier, "category": cat,
            "tier_position": pos_by_slot[(tier, cat)],
            "accession": pick,
        })
        if bp:
            keeper_bps.add(bp)

    # Step 3: fetch full records for replacement accs to format provenance.
    chosen = [r["accession"] for r in replacements if r["accession"]]
    records = load_chosen_records((args.bact_jsonl, args.arch_jsonl), chosen)
    missing = set(chosen) - set(records.keys())
    if missing:
        sys.exit(f"ERROR: missing JSONL records for replacements {missing}")

    write_output(args.output, replacements, all_rejections, records, bp_map,
                 args.seed, quotas, tier_cats, bin_counts,
                 total, binned, unbinned, args.survivors,
                 exclude_set, keep_set, keeper_bps_initial, failed_slots)

    # Stdout summary
    print(f"SEED: {args.seed}")
    print(f"Pool: {total} survivors total | {binned} binned | "
          f"{unbinned} UNBINNED")
    print(f"Exclusion ({len(exclude_set)}): {sorted(exclude_set)}")
    print(f"Keep ({len(keep_set)}): {sorted(keep_set)}")
    print(f"Initial keeper_bps from --keep: {sorted(keeper_bps_initial) or '(none)'}")
    print()
    print(f"Failed slots in original draw ({len(failed_slots)}):")
    for tier, cat, orig in failed_slots:
        print(f"  [{tier}] {cat}: original pick {orig}")
    print()
    if all_rejections:
        print(f"Rejections during redraw ({len(all_rejections)}):")
        for r in all_rejections:
            print(f"  [{r['tier']}] {r['category']}: rejected "
                  f"{r['rejected_accession']} "
                  f"(BP {r['rejected_bioproject'] or '(none)'}) — {r['reason']}")
        print()
    print("Replacements:")
    print("=" * 92)
    for r in replacements:
        if r["accession"] is None:
            print(f"  [{r['tier']:6s}] {r['category']:24s}  SHORTFALL ({r['shortfall_reason']})")
            continue
        rec = records[r["accession"]]
        name = fmt_strain(rec)
        date = rec.get("assembly_info", {}).get("release_date", "") or ""
        bp = bp_map.get(r["accession"], "") or "(no BP)"
        print(f"  [{r['tier']:6s}] {r['category']:24s}  {r['accession']:18s}  "
              f"{date}  {bp:15s}  {name[:40]}")
    print("=" * 92)
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
