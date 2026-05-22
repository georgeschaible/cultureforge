#!/usr/bin/env python3
"""
Curation fix for the 13 gids surfaced by the Phase 6.5 sourmash identity
verification — appends formal `[TAXONOMIC RENAME]`,
`[AUDIT CORRECTION 2026-05-21]`, and `[RESOLVED IDENTITY 2026-05-21]`
markers to `genomes.notes`, and appends an erratum section to the
verification report.

Default mode is DRY RUN: prints a per-gid before/after diff and the
report-erratum insertion site, makes no writes.  Use `--commit` to
actually apply the changes.

Idempotency / safety: each update specifies the exact `expected_old`
notes string.  If the current notes don't match `expected_old`, the
script refuses to apply (this catches double-runs and any out-of-band
changes).  Already-applied updates are skipped, not duplicated.

Usage:
    # Dry run (default)
    python3 data/validation/curation_fix_phase6_5.py

    # Apply
    python3 data/validation/curation_fix_phase6_5.py --commit

DB backup is the caller's responsibility — taken before running this
script as `data/cultureforge.db.pre_curation_fix_20260521`.
"""

import argparse
import difflib
import sqlite3
import sys
from pathlib import Path


# ----------------------------------------------------------------------------
# UPDATES — exactly the 13 gids approved on 2026-05-21.
# Each entry: (gid, expected_old_notes, proposed_new_notes)
# ----------------------------------------------------------------------------

UPDATES: list[tuple[int, str, str]] = [
    # --- gid 7 — Desulfovibrio → Nitratidesulfovibrio ---
    (
        7,
        "Desulfovibrio (Nitratidesulfovibrio) vulgaris Hildenborough. Strict anaerobe, sulfate reducer. DSM 644.",
        "Desulfovibrio (Nitratidesulfovibrio) vulgaris Hildenborough. Strict anaerobe, sulfate reducer. DSM 644. [TAXONOMIC RENAME: Desulfovibrio vulgaris → Nitratidesulfovibrio vulgaris (GTDB R226); rename was already recorded inline in the parenthetical above — this bracket adds the formal marker for consistency; genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 8 — Methanococcus → Methanocaldococcus (verified Whitman 2002) ---
    (
        8,
        "Validation organism: Methanococcus_jannaschii",
        "Validation organism: Methanococcus_jannaschii [TAXONOMIC RENAME: Methanococcus jannaschii → Methanocaldococcus jannaschii (Whitman 2002, IJSEM 52:685; Validation List no. 85); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 26 — Picrophilus species clarification ---
    (
        26,
        "AUDIT CORRECTION: re-process for gid=26 (was Brevibacillus brevis NBRC 100599 from start). Cluster gapseq via SLURM array 227930. biomass=Archaea [AUDIT CORRECTION 2026-05-05: re-downloaded + re-processed; previously gid=26 had wrong-genome data loaded from project start. Pre-correction state preserved in data/cultureforge.db.pre_audit_correction_20260504]",
        "AUDIT CORRECTION: re-process for gid=26 (was Brevibacillus brevis NBRC 100599 from start). Cluster gapseq via SLURM array 227930. biomass=Archaea [AUDIT CORRECTION 2026-05-05: re-downloaded + re-processed; previously gid=26 had wrong-genome data loaded from project start. Pre-correction state preserved in data/cultureforge.db.pre_audit_correction_20260504] [AUDIT CORRECTION 2026-05-21: loaded FASTA (NC_005877.1) is Picrophilus oshimae DSM 9789, not P. torridus — sister species, both genus Picrophilus. Per C1 BacDive erratum. Phase 6.5 sourmash verification: containment 0.74 to GTDB R226 g__Picrophilus s__Picrophilus oshimae.]",
    ),
    # --- gid 31 — Allochromatium → Thermochromatium ---
    (
        31,
        "Phase 1.5k validation organism - reverse-dsr sulfide oxidizer",
        "Phase 1.5k validation organism - reverse-dsr sulfide oxidizer (Allochromatium vinosum DSM 180, NC_013851.1) [TAXONOMIC RENAME: Allochromatium vinosum → Thermochromatium vinosum (GTDB R226); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1000 — blind-test MAG resolved identity ---
    (
        1000,
        "BLIND TEST: bin.020 PacBio assembly via Phase 4.1 wrapper (load-step replay after filename-resolution fix; gapseq output reused from prior run)",
        "BLIND TEST: bin.020 PacBio assembly via Phase 4.1 wrapper (load-step replay after filename-resolution fix; gapseq output reused from prior run) [RESOLVED IDENTITY 2026-05-21: Thiovulum_A sp000276965 (GTDB R226) at sourmash containment 0.88; identity was not claimed at load time — this MAG was used solely to exercise the Phase 4.1 load step, not as a target organism. Phase 6.5 sourmash verification.]",
    ),
    # --- gid 1017 — Nostoc → Trichormus (GTDB R220) ---
    (
        1017,
        "Phase 5.0 main: Nostoc sp. PCC 7120 [nitrogen_metabolism]. biomass=Gram_neg",
        "Phase 5.0 main: Nostoc sp. PCC 7120 [nitrogen_metabolism]. biomass=Gram_neg [TAXONOMIC RENAME: Nostoc sp. PCC 7120 → Trichormus sp. (GTDB R220 placed this accession at g__Trichormus; GTDB R226 retains the placement with placeholder species id 's__Trichormus sp000009705' — genus-level rename, no named species assigned); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1030 — Rhodobacter → Cereibacter_A ---
    (
        1030,
        "Phase 5.0 main: Rhodobacter sphaeroides 2.4.1 [phototrophy]. biomass=Gram_neg",
        "Phase 5.0 main: Rhodobacter sphaeroides 2.4.1 [phototrophy]. biomass=Gram_neg [TAXONOMIC RENAME: Rhodobacter sphaeroides → Cereibacter sphaeroides (GTDB R226; GTDB uses the suffix-split variant Cereibacter_A for this lineage); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1043 — Methanobrevibacter → Methanocatella (GTDB R220) ---
    (
        1043,
        "Phase 5.0 main: Methanobrevibacter smithii ATCC 35061 [methane_metabolism]. biomass=Archaea",
        "Phase 5.0 main: Methanobrevibacter smithii ATCC 35061 [methane_metabolism]. biomass=Archaea [TAXONOMIC RENAME: Methanobrevibacter smithii → Methanocatella smithii (GTDB R220 reclassification); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1061 — Methylorubrum → Methylobacterium (GTDB lump) ---
    (
        1061,
        "Phase 5.0 main: Methylorubrum extorquens AM1 [methane_metabolism]. biomass=Gram_neg",
        "Phase 5.0 main: Methylorubrum extorquens AM1 [methane_metabolism]. biomass=Gram_neg [TAXONOMIC RENAME: Methylorubrum extorquens → Methylobacterium extorquens (GTDB R226 lumped Methylorubrum back into Methylobacterium); the current notes use the post-2018-split name Methylorubrum, GTDB reverts to the older Methylobacterium; genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1066 — Bacillus → Salisediminibacterium ---
    (
        1066,
        "Phase 5.0 main: Bacillus selenitireducens MLS10 [heavy_metal_respiration]. biomass=Gram_neg",
        'Phase 5.0 main: Bacillus selenitireducens MLS10 [heavy_metal_respiration]. biomass=Gram_neg [TAXONOMIC RENAME: Bacillus selenitireducens → Salisediminibacterium selenitireducens (GTDB R226); NCBI bracketed name "[Bacillus]" in source FASTA header was the prior signal; genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]',
    ),
    # --- gid 1092 — Anabaena → Dolichospermum (GTDB R220) ---
    (
        1092,
        "Phase 5.0 main: Anabaena sp. 90 [nitrogen_metabolism]. biomass=Gram_neg",
        "Phase 5.0 main: Anabaena sp. 90 [nitrogen_metabolism]. biomass=Gram_neg [TAXONOMIC RENAME: Anabaena sp. 90 → Dolichospermum lemmermannii (GTDB R220 reclassification); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1107 — Pseudorhizobium → Neorhizobium ---
    (
        1107,
        "Phase 5.0 main: Pseudorhizobium banfieldiae NT-26 [heavy_metal_respiration]. biomass=Gram_neg",
        "Phase 5.0 main: Pseudorhizobium banfieldiae NT-26 [heavy_metal_respiration]. biomass=Gram_neg [TAXONOMIC RENAME: Pseudorhizobium banfieldiae → Neorhizobium banfieldiae (GTDB R226); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1112 — Neomoorella → Moorella (GTDB lump) ---
    (
        1112,
        "Phase 5.0 main: Neomoorella thermoacetica DSM 521 [carbon_fixation]. biomass=Gram_neg",
        "Phase 5.0 main: Neomoorella thermoacetica DSM 521 [carbon_fixation]. biomass=Gram_neg [TAXONOMIC RENAME: Neomoorella thermoacetica → Moorella thermoacetica (GTDB R226 lump of Neomoorella back into Moorella); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
    # --- gid 1133 — Leptothrix → Sphaerotilus ---
    (
        1133,
        "Phase 5.0 main: Leptothrix discophora CCM 2812 [manganese_metabolism]. biomass=Gram_neg",
        "Phase 5.0 main: Leptothrix discophora CCM 2812 [manganese_metabolism]. biomass=Gram_neg [TAXONOMIC RENAME: Leptothrix discophora → Sphaerotilus discophorus (GTDB R226); genome unchanged; annotation added by Phase 6.5 audit 2026-05-21]",
    ),
]


# ----------------------------------------------------------------------------
# Erratum — appended to docs/phase6_5/sourmash_identity_verification_report.md
# ----------------------------------------------------------------------------

ERRATUM_MARKER = "## Erratum 2026-05-21"

ERRATUM_TEXT = """---

## Erratum 2026-05-21

This erratum is appended to the report — §3.3 and the supplementary TSV
are left as originally committed (methodology-record documents get
errata, not silent corrections).

### What §3.3 said vs. what was actually true

§3.3 reported that 11 of the 13 KNOWN_TAXONOMIC_RENAME entries were
"curator-flagged" in `genomes.notes`. **This overstated the existing
annotation.** At the time the report was committed (commit `a767b29`),
only **2** of the 13 had a formal
`[TAXONOMIC RENAME: ... → ...; genome unchanged; ...]` bracket marker
(gids 10 and 16). Of the remaining 11 that §3.3 counted as
"curator-flagged":

- **gid 7** (*Desulfovibrio* → *Nitratidesulfovibrio*): had an inline
  parenthetical (`Desulfovibrio (Nitratidesulfovibrio) vulgaris …`) but
  no formal bracket marker.
- **gid 1061** (*Methylorubrum* → *Methylobacterium*): notes used the
  post-2018-split name *Methylorubrum* with no annotation that GTDB
  lumps it back into *Methylobacterium*.
- **gids 8, 1017, 1030, 1043, 1092, 1107, 1112, 1133**: no rename
  annotation in notes at all — the curator's working name was the only
  identity recorded.

### Why §3.3 overstated

The classifier script `data/validation/classify_sourmash_results.py`
carries a `KNOWN_RENAMES` dict in which each entry's third tuple field
records whether the rename is `"curator-flagged"` or
`"discovered-this-analysis"`. **That field was hardcoded at script-
authoring time, not derived from re-reading `genomes.notes` to check
for the actual bracket marker.** The classifier populated the
`rename_source` column of the supplementary TSV (and the §3.3 table)
directly from that hardcoded field. Two of the eleven entries (gids 10
and 16) happened to be correct; the other nine were not.

### Action taken in the 2026-05-21 curation pass

This curation pass (recorded in this same commit) adds the missing
`[TAXONOMIC RENAME: ... → ...; genome unchanged; annotation added by
Phase 6.5 audit 2026-05-21]` markers to all 9 previously-bracket-free
gids (8, 1017, 1030, 1043, 1061, 1092, 1107, 1112, 1133), adds the
same marker to gid 7 (complementing its existing parenthetical), and
adds the 2 discovered-this-analysis markers (gids 31, 1066) plus the
gid 26 species clarification and gid 1000 resolved-identity
annotations.

**After this pass, 13 of 13 KNOWN_TAXONOMIC_RENAME entries carry a
formal `[TAXONOMIC RENAME]` marker in `genomes.notes`.** This brings
the cohort into consistency with the report's original (premature)
claim — not by rewriting the report (the report stands as the
historical record of what the classifier said), but by updating the
cohort to match what the classifier should have been checking.

### What this means for the supplementary TSV

`docs/phase6_5/sourmash_identity_verification.tsv` carries the same
`rename_source = curator-flagged` misattribution for the 9 under-
annotated rows. The TSV file is left as originally committed (it
remains the report-of-record for the 2026-05-21 sourmash run) and is
superseded for the `rename_source` column by this erratum and by the
2026-05-21 curation pass.

End of erratum.

"""

REPORT_PATH_DEFAULT = "docs/phase6_5/sourmash_identity_verification_report.md"
DB_PATH_DEFAULT = "data/cultureforge.db"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def print_unified_diff(label: str, old: str, new: str) -> None:
    """Render a wrapped unified diff for a single notes update."""
    print(f"\n----- {label} -----")
    old_lines = old.splitlines(keepends=False) or [""]
    new_lines = new.splitlines(keepends=False) or [""]
    diff_lines = list(difflib.unified_diff(
        old_lines, new_lines, fromfile="current", tofile="proposed",
        lineterm="", n=2,
    ))
    if not diff_lines:
        print("  (no change — already at target state)")
        return
    for line in diff_lines:
        print("  " + line)


def classify_state(current: str, expected_old: str, proposed_new: str) -> str:
    """Return one of: 'needs_update', 'already_applied', 'mismatch'."""
    if current == expected_old:
        return "needs_update"
    if current == proposed_new:
        return "already_applied"
    return "mismatch"


# ----------------------------------------------------------------------------
# DB pass
# ----------------------------------------------------------------------------

def run_db_pass(db_path: str, commit: bool) -> tuple[int, int, list[int]]:
    """Return (n_updated, n_already_applied, mismatch_gids)."""
    print(f"\n=== DB PASS ({'COMMIT' if commit else 'DRY RUN'}) — {db_path} ===")
    n_updated = 0
    n_already = 0
    mismatches: list[int] = []

    mode = "" if commit else "?mode=ro"
    conn = sqlite3.connect(f"file:{db_path}{mode}", uri=True, isolation_level=None)
    try:
        for gid, expected_old, proposed_new in UPDATES:
            row = conn.execute(
                "SELECT notes FROM genomes WHERE id = ?", (gid,)
            ).fetchone()
            if row is None:
                print(f"\n[gid {gid}] ERROR: not found in DB")
                mismatches.append(gid)
                continue
            current = row[0] or ""
            state = classify_state(current, expected_old, proposed_new)

            if state == "needs_update":
                print_unified_diff(f"gid {gid} (will update)", current, proposed_new)
                if commit:
                    conn.execute(
                        "UPDATE genomes SET notes = ? WHERE id = ?",
                        (proposed_new, gid),
                    )
                    # Verify
                    rb = conn.execute(
                        "SELECT notes FROM genomes WHERE id = ?", (gid,)
                    ).fetchone()
                    if rb is None or rb[0] != proposed_new:
                        print(f"  [gid {gid}] ERROR: read-back mismatch after UPDATE")
                        mismatches.append(gid)
                        continue
                    print(f"  [gid {gid}] UPDATE verified")
                n_updated += 1
            elif state == "already_applied":
                print(f"\n----- gid {gid} (already applied — skipping) -----")
                n_already += 1
            else:
                print(f"\n----- gid {gid} MISMATCH -----")
                print(f"  current notes do NOT match expected_old.")
                print(f"  Refusing to apply.")
                print(f"  current  : {current[:120]}{'…' if len(current) > 120 else ''}")
                print(f"  expected : {expected_old[:120]}{'…' if len(expected_old) > 120 else ''}")
                mismatches.append(gid)
    finally:
        conn.close()

    return n_updated, n_already, mismatches


# ----------------------------------------------------------------------------
# Erratum pass
# ----------------------------------------------------------------------------

REPORT_CLOSER = "End of report.\n"


def run_erratum_pass(report_path: str, commit: bool) -> str:
    """Append the erratum block to the report, immediately before its closing
    "End of report." line.  Idempotent: skipped if the erratum marker is
    already present.

    Returns one of: 'will_append', 'already_present', 'closer_missing'.
    """
    print(f"\n=== ERRATUM PASS ({'COMMIT' if commit else 'DRY RUN'}) — {report_path} ===")
    p = Path(report_path)
    if not p.is_file():
        print(f"  ERROR: report not found at {p}")
        return "missing"

    text = p.read_text(encoding="utf-8")
    if ERRATUM_MARKER in text:
        print(f"  Erratum marker '{ERRATUM_MARKER}' already present — skipping.")
        return "already_present"

    if REPORT_CLOSER not in text:
        print(f"  ERROR: closing line '{REPORT_CLOSER.strip()}' not found in report.")
        print(f"  Refusing to insert erratum at an unknown location.")
        return "closer_missing"

    new_text = text.replace(REPORT_CLOSER, ERRATUM_TEXT + REPORT_CLOSER, 1)
    insertion_index = text.index(REPORT_CLOSER)
    context_before = text[max(0, insertion_index - 80):insertion_index]
    print(f"  Will insert erratum immediately BEFORE this line:")
    print(f"    {REPORT_CLOSER.strip()!r}")
    print(f"  Context (last 80 chars before insertion point):")
    print(f"    {context_before!r}")
    print(f"  Erratum text length: {len(ERRATUM_TEXT)} chars")
    print(f"  New file length: {len(new_text)} (was {len(text)})")

    if commit:
        p.write_text(new_text, encoding="utf-8")
        print(f"  Erratum written.")
    return "will_append"


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DB_PATH_DEFAULT)
    ap.add_argument("--report", default=REPORT_PATH_DEFAULT)
    ap.add_argument("--commit", action="store_true",
                    help="Actually write the changes (default is dry run).")
    args = ap.parse_args()

    print(f"=== curation_fix_phase6_5.py ===")
    print(f"mode    : {'COMMIT (writes will happen)' if args.commit else 'DRY RUN (no writes)'}")
    print(f"db      : {args.db}")
    print(f"report  : {args.report}")
    print(f"updates : {len(UPDATES)} gids queued")

    n_updated, n_already, mismatches = run_db_pass(args.db, args.commit)
    erratum_state = run_erratum_pass(args.report, args.commit)

    print("\n=== SUMMARY ===")
    print(f"  gids that will be updated  : {n_updated}")
    print(f"  gids already applied (skip): {n_already}")
    print(f"  mismatches (refused)       : {len(mismatches)}"
          + (f"  -> {mismatches}" if mismatches else ""))
    print(f"  erratum                    : {erratum_state}")

    if mismatches:
        print("\n  Some gids did not match the expected current text — see diffs above.")
        print("  Investigate before re-running.")
        sys.exit(2)

    if not args.commit:
        print("\n  This was a DRY RUN — no writes made.  Re-run with --commit to apply.")


if __name__ == "__main__":
    main()
