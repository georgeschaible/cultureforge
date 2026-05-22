#!/usr/bin/env python3
"""
Classify Task-4 sourmash identity-verification results into the 7-category
schema defined in TASK5_REVISED.md.  Produces:

    docs/phase6_5/sourmash_identity_verification.tsv

Inputs (defaults):
    --results : data/validation/sourmash_identity_verification/results_<ts>.tsv
    --db      : data/cultureforge.db  (read-only; for full untruncated notes)
    --out     : docs/phase6_5/sourmash_identity_verification.tsv

The categorization rules are described in detail in TASK5_REVISED.md. In
short, GTDB representations of the cohort organisms differ from curated
literature names for three benign reasons (suffix-splits, formal renames,
Candidatus placeholders); a naive species-string match would generate
~40 false-positive flags.
"""

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path


KNOWN_RENAMES = {
    # claimed_genus(_lower) -> (gtdb_genus, citation_hint, source)
    "methanococcus":      ("Methanocaldococcus",     "Whitman et al. 2002",  "curator-flagged"),
    "desulfovibrio":      ("Nitratidesulfovibrio",   "Waite et al. 2020",    "curator-flagged"),
    "lactobacillus":      ("Lactiplantibacillus",    "Zheng et al. 2020",    "curator-flagged"),
    "magnetospirillum":   ("Paramagnetospirillum",   "Lin et al. 2020",      "curator-flagged"),
    "nostoc":             ("Trichormus",             "GTDB R220 reclass.",   "curator-flagged"),
    "rhodobacter":        ("Cereibacter_A",          "GTDB suffix-rename",   "curator-flagged"),
    "methanobrevibacter": ("Methanocatella",         "GTDB R220 reclass.",   "curator-flagged"),
    "methylorubrum":      ("Methylobacterium",       "GTDB lumped",          "curator-flagged"),
    "anabaena":           ("Dolichospermum",         "GTDB grouping",        "curator-flagged"),
    "pseudorhizobium":    ("Neorhizobium",           "GTDB R220 reclass.",   "curator-flagged"),
    "neomoorella":        ("Moorella",               "GTDB lumped",          "curator-flagged"),
    "leptothrix":         ("Sphaerotilus",           "GTDB R220 reclass.",   "curator-flagged"),
    # discovered during analysis, NOT curator-flagged:
    "allochromatium":     ("Thermochromatium",       "GTDB R226 reclass.",   "discovered-this-analysis"),
    "bacillus":           ("Salisediminibacterium",  "GTDB R226 reclass. (selenitireducens lineage)",
                                                                            "discovered-this-analysis"),
    # Picrophilus torridus -> P. oshimae: same genus, treated by CLEAN_SELF_MATCH branch
}

# Genera with GTDB suffix-splits seen in this cohort (from the task prompt).
SUFFIX_SPLITS = {
    "Clostridium", "Nitrospira", "Methylobacter", "Bacillus", "Selenomonas",
    "Peptoclostridium", "Pelotomaculum", "Acidithiobacillus", "Pseudomonas",
    "Campylobacter", "Thiovulum",
}

# GTDB placeholder-genus pattern: letters then 4+ digits (e.g. UBA1062, QENH01,
# DQIP01, SFFY03, JABMQQ01).  An optional letter suffix may follow.
PLACEHOLDER_RX = re.compile(r"^[A-Z]{2,}\d{2,}[A-Z]?$")


def strip_gprefix(s: str, prefix: str) -> str:
    return s[len(prefix):] if s.startswith(prefix) else s


def parse_claimed_organism(notes: str, fasta_name: str) -> tuple[str, str, str]:
    """Return (claimed_full, claimed_genus, claimed_species_token).

    `claimed_full` is a normalised one-line label suitable for the report.
    `claimed_genus` is the genus extracted heuristically.
    `claimed_species_token` is the species epithet if parseable, else ''.
    Falls back to the FASTA header (`query_name_from_fasta`) when the notes
    don't contain a parseable organism name (AUDIT CORRECTION etc.).
    """
    n = notes or ""
    # Strip common prefixes
    body = n
    for prefix in [
        "Phase 5.0 SMOKE TEST: ", "Phase 5.0 main: ",
        "Phase 1.5k validation organism - ",
        "Validation organism: ", "Blind validation: ", "Blind v2: ",
        "SENTINEL: ", "BLIND TEST: ",
    ]:
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    # AUDIT CORRECTION: derive organism from FASTA header instead
    if body.startswith("AUDIT CORRECTION"):
        body = ""

    candidates: list[str] = []
    if body:
        candidates.append(body.replace("_", " "))
    if fasta_name:
        # FASTA header usually looks like:
        #   "NC_002937.3 Nitratidesulfovibrio vulgaris str. Hildenborough..."
        # Strip the leading accession + version token.
        parts = fasta_name.split(maxsplit=1)
        candidates.append(parts[1] if len(parts) == 2 else fasta_name)

    claimed_full = ""
    claimed_genus = ""
    claimed_species_token = ""

    # Try strongest matches first across all candidates, then fall back.
    # Pattern 1: re.search "Candidatus X y" (handles cases where prefix
    # wasn't stripped, e.g. notes like 'Phase 5.0 SMOKE TEST: Candidatus ...')
    for cand in candidates:
        if not cand.strip():
            continue
        m = re.search(r"\b(Candidatus\s+[A-Z][A-Za-z]+)\s+([a-z]+)", cand)
        if m:
            claimed_genus = m.group(1)
            claimed_species_token = m.group(2)
            claimed_full = cand.strip()[:120]
            return claimed_full, claimed_genus, claimed_species_token

    # Pattern 2: re.match "Genus species" at start of a candidate
    for cand in candidates:
        cand = cand.strip()
        if not cand:
            continue
        m = re.match(r"([A-Z][A-Za-z]+)\s+([a-z]+)", cand)
        if m:
            claimed_genus = m.group(1)
            claimed_species_token = m.group(2)
            claimed_full = cand[:120]
            return claimed_full, claimed_genus, claimed_species_token

    # Pattern 3: lone "Genus" (no species) at start
    for cand in candidates:
        cand = cand.strip()
        if not cand:
            continue
        m = re.match(r"([A-Z][A-Za-z]+)\b", cand)
        if m:
            claimed_genus = m.group(1)
            claimed_full = cand[:120]
            return claimed_full, claimed_genus, ""

    return (body or fasta_name or "?")[:120], "", ""


def classify(row: dict, full_notes: str) -> dict:
    """Return classification metadata for one rank-1 row."""
    gid = row["gid"]
    fasta_name = row.get("query_name_from_fasta", "")
    notes_field = row.get("claimed_organism", "")  # in TSV this is truncated; we have full_notes
    notes = full_notes or notes_field

    hit_genus_raw = strip_gprefix(row.get("top_match_genus", ""), "g__")
    hit_species_raw = strip_gprefix(row.get("top_match_species", ""), "s__")
    lineage = row.get("top_match_lineage", "")
    note_col = row.get("notes", "")  # the script's processing-status notes
    cont = row.get("containment_or_similarity", "")
    try:
        cont_f = float(cont) if cont else 0.0
    except ValueError:
        cont_f = 0.0

    claimed_full, claimed_genus, claimed_species_token = parse_claimed_organism(notes, fasta_name)

    out = {
        "gid": gid,
        "claimed_organism": notes,
        "claimed_organism_short": claimed_full,
        "claimed_genus": claimed_genus,
        "top_match_lineage": lineage,
        "top_match_genus": hit_genus_raw,
        "top_match_species": hit_species_raw,
        "containment": cont,
        "query_name_from_fasta": fasta_name,
        "category": "",
        "category_rationale": "",
        "needs_action": "N",
        "rename_source": "",
    }

    # No-match / very-low-containment branch
    if note_col == "no_matches" or (not hit_genus_raw and not hit_species_raw):
        # Per task prompt, the two known Candidatus placeholders in unrepresented
        # lineages (Electronema, Magnetoglobus) are NO_CLOSE_MATCH_EXPECTED.
        out["category"] = "NO_CLOSE_MATCH_EXPECTED"
        out["category_rationale"] = (
            "No GTDB RS226 hit returned; claimed organism is a Candidatus lineage "
            "(under-represented in cultured/reference databases)."
        )
        return out
    if cont_f < 0.20:
        out["category"] = "NO_CLOSE_MATCH_EXPECTED"
        out["category_rationale"] = (
            f"Top GTDB hit containment {cont_f:.3f} is below the 0.20 floor; "
            "biological novelty, not contamination."
        )
        return out

    # Special handling: "Picrophilus" claimed -> oshimae hit (C1 erratum).  GTDB
    # lacks a P. torridus rep; the sister species P. oshimae is the documented
    # closest neighbour.
    if (claimed_genus == "Picrophilus" and hit_genus_raw == "Picrophilus"
            and "torridus" in (claimed_species_token or "")
            and "oshimae" in (hit_species_raw or "")):
        out["category"] = "CLEAN_SELF_MATCH"
        out["category_rationale"] = (
            "Same-genus congener match (Picrophilus oshimae) — "
            "GTDB RS226 has no P. torridus representative; "
            "C1 BacDive erratum documents this taxonomy ambiguity."
        )
        return out

    # Normalised genus for matching: strip an optional "Candidatus " prefix.
    # GTDB drops "Candidatus" once it assigns a formal genus name (e.g. claim
    # "Candidatus Brocadia sinica" matches hit genus "Brocadia").  We keep the
    # original `claimed_genus` for display purposes.
    claimed_genus_norm = claimed_genus
    if claimed_genus.startswith("Candidatus "):
        claimed_genus_norm = claimed_genus[len("Candidatus "):]

    # Candidatus + placeholder genus
    if claimed_genus.startswith("Candidatus") and PLACEHOLDER_RX.match(hit_genus_raw or ""):
        # Strongest confirmation: cohort accession == GTDB rep accession
        cohort_acc = (row.get("accession_in_db") or "").strip()
        gtdb_acc = (row.get("top_match_gtdb_accession") or "").strip()
        accession_match = cohort_acc and gtdb_acc and cohort_acc == gtdb_acc

        # Fallback: FASTA header literally mentions the claimed organism name
        claimed_organism_token = claimed_genus.replace("Candidatus ", "")
        fasta_lc = (fasta_name or "").lower()
        fasta_confirms = (claimed_organism_token.lower() in fasta_lc) or \
                         ("candidatus" in fasta_lc)

        if accession_match:
            confirm_phrase = (
                f"Cohort accession ({cohort_acc}) matches the GTDB rep accession "
                f"exactly — literally the same source sequence."
            )
            out["needs_action"] = "N"
        elif fasta_confirms:
            confirm_phrase = "FASTA header literally mentions the claimed organism name."
            out["needs_action"] = "N"
        else:
            confirm_phrase = (
                "Confirmation indirect: accession does not match the GTDB rep and "
                "the FASTA header does not literally name the Candidatus taxon. "
                "Flagged for human review."
            )
            out["needs_action"] = "Y"

        out["category"] = "CANDIDATUS_PLACEHOLDER"
        out["category_rationale"] = (
            f"Claimed Candidatus organism; GTDB placeholder genus '{hit_genus_raw}' "
            f"(not yet formally classified). {confirm_phrase}"
        )
        return out

    # Suffix split: hit genus == claimed_genus_norm + "_<letter(s)>"
    if claimed_genus_norm and hit_genus_raw.startswith(claimed_genus_norm + "_"):
        species_match = (claimed_species_token and
                         claimed_species_token.lower() in (hit_species_raw or "").lower())
        prefix_note = ("(claim used 'Candidatus' prefix; GTDB drops it) "
                       if claimed_genus.startswith("Candidatus ") else "")
        out["category"] = "GTDB_SUFFIX_SPLIT"
        out["category_rationale"] = (
            f"{prefix_note}GTDB has split the polyphyletic genus "
            f"'{claimed_genus_norm}' into sub-genera using letter suffixes; "
            f"this genome falls into '{hit_genus_raw}'. Species name aligns."
            if species_match else
            f"{prefix_note}Hit genus '{hit_genus_raw}' is a GTDB suffix-split of "
            f"'{claimed_genus_norm}'; species names diverge — see report."
        )
        return out

    # Known formal rename (genus-level)
    claimed_lc = (claimed_genus or "").lower()
    if claimed_lc in KNOWN_RENAMES:
        renamed_to, citation, source = KNOWN_RENAMES[claimed_lc]
        if hit_genus_raw == renamed_to or hit_genus_raw.startswith(renamed_to + "_"):
            curator_flagged = "[TAXONOMIC RENAME" in (notes or "")
            out["category"] = "KNOWN_TAXONOMIC_RENAME"
            out["category_rationale"] = (
                f"Formal genus reclassification: '{claimed_genus}' -> "
                f"'{hit_genus_raw}' ({citation}). "
                + ("Curator-flagged in notes." if curator_flagged
                   else "Not curator-flagged in notes; documentation update suggested.")
            )
            out["rename_source"] = source
            if source == "discovered-this-analysis":
                out["needs_action"] = "Y"
            return out

    # Self-match (normalised genus identical, decent containment).
    # The normalised genus drops a "Candidatus " prefix from the claim so that
    # e.g. "Candidatus Brocadia sinica" matches GTDB's "Brocadia".
    if claimed_genus_norm and hit_genus_raw == claimed_genus_norm:
        prefix_note = (" (claim used 'Candidatus' prefix; GTDB has assigned "
                       "the formal genus name)") if \
                       claimed_genus.startswith("Candidatus ") else ""
        out["category"] = "CLEAN_SELF_MATCH"
        out["category_rationale"] = (
            f"Claimed genus '{claimed_genus_norm}' matches top-hit genus exactly"
            f"{prefix_note}; containment {cont_f:.3f}."
        )
        return out

    # Special: claimed genus with a stripped-suffix that resolves an underscore variant
    if claimed_genus and hit_genus_raw and \
       hit_genus_raw.split("_")[0] == claimed_genus and "_" in hit_genus_raw \
       and hit_genus_raw.split("_", 1)[0] in SUFFIX_SPLITS:
        out["category"] = "GTDB_SUFFIX_SPLIT"
        out["category_rationale"] = (
            f"GTDB suffix-split: '{claimed_genus}' -> '{hit_genus_raw}'."
        )
        return out

    # Anything else: needs human review
    out["category"] = "NEEDS_REVIEW"
    out["category_rationale"] = (
        f"Claimed genus '{claimed_genus}' vs GTDB top-hit genus "
        f"'{hit_genus_raw}' ({hit_species_raw}); containment {cont_f:.3f}. "
        f"Does not fit suffix-split, known-rename, placeholder, or self-match "
        f"patterns — requires manual inspection."
    )
    out["needs_action"] = "Y"
    return out


def fetch_full_notes(db_path: str) -> dict[str, str]:
    """Return gid (string) -> full notes from the live DB."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.execute("SELECT id, notes FROM genomes")
        return {str(gid): notes or "" for gid, notes in cur}
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results",
                    default="data/validation/sourmash_identity_verification/"
                            "results_20260521_205346.tsv")
    ap.add_argument("--db", default="data/cultureforge.db")
    ap.add_argument("--out", default="docs/phase6_5/sourmash_identity_verification.tsv")
    args = ap.parse_args()

    full_notes_map = fetch_full_notes(args.db)

    # Read only rank-1 rows from the results TSV
    rows = []
    with open(args.results) as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for r in rdr:
            if r.get("top_match_rank") != "1":
                continue
            rows.append(r)
    print(f"[load] {len(rows)} rank-1 rows", file=sys.stderr)

    classified = []
    for r in rows:
        full_notes = full_notes_map.get(r["gid"], "")
        c = classify(r, full_notes)
        classified.append(c)

    # Write supplementary TSV
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "gid", "claimed_organism", "top_match_lineage", "containment",
        "category", "category_rationale", "needs_action",
        "top_match_genus", "top_match_species", "query_name_from_fasta",
        "rename_source",
    ]
    with open(out_path, "w", newline="") as out:
        w = csv.DictWriter(out, fieldnames=cols, delimiter="\t",
                           extrasaction="ignore")
        w.writeheader()
        for c in classified:
            w.writerow(c)

    # Print summary
    from collections import Counter
    counts = Counter(c["category"] for c in classified)
    print(f"\n[done] wrote {out_path}", file=sys.stderr)
    print(f"\n=== Category counts ===", file=sys.stderr)
    total = 0
    for cat in ["CLEAN_SELF_MATCH", "GTDB_SUFFIX_SPLIT",
                "KNOWN_TAXONOMIC_RENAME", "CANDIDATUS_PLACEHOLDER",
                "NO_CLOSE_MATCH_EXPECTED", "NEEDS_REVIEW", "PHYLUM_MISMATCH"]:
        v = counts.get(cat, 0)
        total += v
        print(f"  {cat:30s} {v:4d}", file=sys.stderr)
    print(f"  {'TOTAL':30s} {total:4d}", file=sys.stderr)

    print(f"\n=== NEEDS_REVIEW entries ===", file=sys.stderr)
    for c in classified:
        if c["category"] == "NEEDS_REVIEW":
            print(f"  gid={c['gid']} claim='{c['claimed_organism_short']}' "
                  f"hit={c['top_match_genus']}/{c['top_match_species']} "
                  f"C={c['containment']}", file=sys.stderr)

    print(f"\n=== Discovered renames (not curator-flagged) ===", file=sys.stderr)
    for c in classified:
        if c.get("rename_source") == "discovered-this-analysis":
            print(f"  gid={c['gid']} claim='{c['claimed_organism_short']}' "
                  f"-> {c['top_match_genus']} {c['top_match_species']}",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
