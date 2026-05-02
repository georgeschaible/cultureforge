"""16S phylogenetic matcher — CultureForge Tier 1, Step 1.

Given a 16S rRNA query sequence (FASTA file or raw sequence), find the
closest cultivated relatives in the CultureForge database and retrieve
their known cultivation media with full recipes.

Usage:
    python phylo_match.py <query.fasta> [--top N] [--min-identity 90]

Example:
    python phylo_match.py test_ecoli_16s.fasta --top 10
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import confidence

_ROOT = Path(__file__).parent

BLAST_DB = str(_ROOT / "data" / "blastdb" / "16s_ref")
DB = str(_ROOT / "data" / "cultureforge.db")

# Thermal class boundaries (°C)
THERMAL_CLASSES = [
    ("psychrophile",      None, 20),
    ("mesophile",         20,   45),
    ("thermophile",       45,   80),
    ("hyperthermophile",  80,   None),
]


def classify_temp(temp):
    """Return thermal class name for a given temperature, or None."""
    if temp is None:
        return None
    for name, lo, hi in THERMAL_CLASSES:
        if (lo is None or temp >= lo) and (hi is None or temp < hi):
            return name
    return None


def thermal_distance(class_a, class_b):
    """Return 0-3 integer distance between two thermal classes.
    0 = same class, 1 = adjacent, 2 = two apart, 3 = opposite ends."""
    if class_a is None or class_b is None:
        return 0  # unknown → no penalty
    names = [c[0] for c in THERMAL_CLASSES]
    try:
        return abs(names.index(class_a) - names.index(class_b))
    except ValueError:
        return 0


def _org_thermal_sources(conn, organism_id):
    """For a given organism_id, return a dict of {source_name: (class, temp)}
    from BacDive / TEMPURA records stored on the organisms table.

    BacDive and TEMPURA are distinguished via the `temp_source` column.
    If the direct organism record has no T data, falls back to a
    species-level lookup (common when the linked BacDive strain record hasn't
    been downloaded yet but a sister strain has).
    Returns empty dict if no T_opt is available at any level.
    """
    row = conn.execute("""
        SELECT species, optimal_temp, min_temp, max_temp, temp_source
          FROM organisms
         WHERE id=?
    """, (organism_id,)).fetchone()
    if not row:
        return {}
    species, t_opt, t_min, t_max, t_src = row

    # If this exact organism lacks T data, try species-level fallback
    if t_opt is None and species:
        sister = conn.execute("""
            SELECT optimal_temp, min_temp, max_temp, temp_source
              FROM organisms
             WHERE species = ?
               AND optimal_temp IS NOT NULL
               AND id != ?
             ORDER BY (temp_source IS NOT NULL) DESC
             LIMIT 1
        """, (species, organism_id)).fetchone()
        if sister:
            t_opt, t_min, t_max, t_src = sister

    sources = {}
    if t_opt is not None:
        tc = classify_temp(t_opt)
        if t_src and "TEMPURA" in t_src:
            sources["TEMPURA"] = (tc, t_opt)
        elif t_src is None or t_src == "":
            sources["BacDive"] = (tc, t_opt)
        else:
            sources[t_src] = (tc, t_opt)
    return sources


def _genomespot_thermal(conn, genome_id):
    """Return (class, temp) from GenomeSPOT's temperature_optimum row, or None."""
    if not genome_id:
        return None
    row = conn.execute("""
        SELECT numeric_value FROM genome_growth_predictions
         WHERE genome_id=? AND source='GenomeSPOT' AND target='temperature_optimum'
    """, (genome_id,)).fetchone()
    if not row or row[0] is None:
        return None
    temp = float(row[0])
    return (classify_temp(temp), temp)


def infer_thermal_multisource(conn, hits, genome_id=None, user_temp=None):
    """Multi-source thermal inference per CLAUDE.md addendum 3.

    Combines up to three direct-data sources: GenomeSPOT (from THIS genome's
    predictions), TEMPURA, and BacDive (from the linked organism record).
    Falls back to phylogenetic inference from `hits` when no direct data.

    Agreement rules (per addendum):
      - All three sources agree on same thermal class → 0.95
      - Two of three agree                          → 0.85
      - Only one source available                   → 0.70
      - Sources disagree                            → 0.50  (flag)
      - user_temp supplied                          → 0.95  (override)

    Returns: (thermal_class, ConfidenceScore, effective_temp, details)
        details is {source_name: temperature_c, ...} for provenance display.
    """
    # User override wins — addendum: "User-supplied override → 0.95"
    if user_temp is not None:
        return (
            classify_temp(user_temp),
            confidence.ConfidenceScore(
                value=0.95, source="user_supplied",
                rationale=f"user-supplied {user_temp:.1f}°C",
                context={"user_temp": user_temp},
            ),
            user_temp,
            {"user_supplied": user_temp},
        )

    sources = {}  # {name: (class, temp)}

    # GenomeSPOT — direct prediction on this genome
    gs = _genomespot_thermal(conn, genome_id) if genome_id else None
    if gs:
        sources["GenomeSPOT"] = gs

    # TEMPURA / BacDive — from the linked organism record (if genome_id set)
    if genome_id:
        org_row = conn.execute(
            "SELECT organism_id FROM genomes WHERE id=?", (genome_id,)
        ).fetchone()
        if org_row and org_row[0]:
            sources.update(_org_thermal_sources(conn, org_row[0]))

    # No direct data? Fall back to phylogenetic inference from relatives.
    if not sources:
        inferred_tc, _, inferred_temp = infer_query_thermal_class(hits, conn)
        if inferred_tc:
            return (
                inferred_tc,
                confidence.ConfidenceScore(
                    value=0.70, source="phylo_inference",
                    rationale=(f"inferred from {len(hits)} relatives "
                               f"(weighted T_opt ~{inferred_temp:.0f}°C)"),
                    context={"n_hits": len(hits), "inferred_temp": inferred_temp},
                ),
                inferred_temp,
                {"phylo_inference": inferred_temp},
            )
        return (
            None,
            confidence.ConfidenceScore(
                value=0.50, source="none",
                rationale="no thermal data available for query",
                context={},
            ),
            None,
            {},
        )

    # Apply agreement rules
    classes = [c for c, _ in sources.values()]
    temps   = [t for _, t in sources.values()]
    from collections import Counter
    cls_count = Counter(classes)
    dominant_cls, n_dom = cls_count.most_common(1)[0]
    n_sources = len(classes)
    mean_temp = sum(temps) / len(temps)

    if n_sources >= 3 and n_dom == n_sources:
        v = 0.95
        rat = (f"3 sources agree on {dominant_cls} (~{mean_temp:.0f}°C): "
               + ", ".join(f"{k}={t:.0f}°C" for k, (_, t) in sources.items()))
    elif n_sources >= 2 and n_dom >= 2:
        v = 0.85
        rat = (f"{n_dom}/{n_sources} sources agree on {dominant_cls} "
               f"(~{mean_temp:.0f}°C): "
               + ", ".join(f"{k}={t:.0f}°C" for k, (_, t) in sources.items()))
    elif n_sources == 1:
        v = 0.70
        only_src = next(iter(sources))
        _, only_t = sources[only_src]
        rat = (f"single source ({only_src}) says {dominant_cls} "
               f"(~{only_t:.0f}°C)")
    else:
        v = 0.50
        disagreement = ", ".join(f"{k}={c}@{t:.0f}°C"
                                 for k, (c, t) in sources.items())
        rat = f"sources DISAGREE: {disagreement} — flag for review"

    return (
        dominant_cls,
        confidence.ConfidenceScore(
            value=v, source="thermal_multi",
            rationale=rat,
            context={"sources": {k: t for k, (_, t) in sources.items()},
                     "n_sources": n_sources, "n_agreeing": n_dom},
        ),
        mean_temp,
        {k: t for k, (_, t) in sources.items()},
    )


def infer_query_thermal_class(hits, conn):
    """Infer the query organism's likely thermal class from its top relatives.

    Uses identity-weighted voting across hits that have T_opt data.
    Returns (class_name, confidence_str, weighted_temp).
    """
    weighted_sum = 0.0
    weight_total = 0.0
    votes = defaultdict(float)

    for hit in hits:
        org = get_organism_info(conn, hit["bacdive_id"])
        if not org or not org.get("optimal_temp"):
            continue
        t_opt = org["optimal_temp"]
        tc = classify_temp(t_opt)
        if tc is None:
            continue
        # Weight by identity — closer relatives count more
        w = hit["identity"] / 100.0
        votes[tc] += w
        weighted_sum += t_opt * w
        weight_total += w

    if weight_total == 0:
        return None, "unknown (no T_opt data in relatives)", None

    best_class = max(votes, key=votes.get)
    weighted_temp = weighted_sum / weight_total
    total_vote = sum(votes.values())
    confidence = votes[best_class] / total_vote

    if confidence > 0.8:
        conf_str = "high"
    elif confidence > 0.5:
        conf_str = "moderate"
    else:
        conf_str = "low"

    return best_class, conf_str, weighted_temp


def run_blast(query_fasta, top_n=20, min_identity=80.0):
    """BLAST query 16S against the reference database.

    Returns list of dicts with keys:
        accession, bacdive_id, species, identity, alignment_length,
        mismatches, gap_opens, q_start, q_end, s_start, s_end, evalue, bitscore
    """
    result = subprocess.run(
        [
            "blastn",
            "-query", query_fasta,
            "-db", BLAST_DB,
            "-outfmt", "6 sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore",
            "-max_target_seqs", str(top_n * 3),  # fetch extra, deduplicate later
            "-evalue", "1e-10",
            "-num_threads", "4",
            "-perc_identity", str(min_identity),
        ],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"BLAST error:\n{result.stderr}", file=sys.stderr)
        return []

    hits = []
    seen_species = set()
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) < 11:
            continue

        # Parse our custom header format: accession|bacdive_id|species
        sseqid = fields[0]
        parts = sseqid.split("|")
        accession = parts[0] if parts else sseqid
        bacdive_id = int(parts[1]) if len(parts) > 1 else 0
        species = parts[2].replace("_", " ") if len(parts) > 2 else "unknown"

        identity = float(fields[1])
        aln_len = int(fields[2])

        # Skip very short alignments (< 500 bp for 16S)
        if aln_len < 500:
            continue

        hit = {
            "accession": accession,
            "bacdive_id": bacdive_id,
            "species": species,
            "identity": identity,
            "alignment_length": aln_len,
            "mismatches": int(fields[3]),
            "gap_opens": int(fields[4]),
            "q_start": int(fields[5]),
            "q_end": int(fields[6]),
            "s_start": int(fields[7]),
            "s_end": int(fields[8]),
            "evalue": float(fields[9]),
            "bitscore": float(fields[10]),
        }
        # Attach per-hit phylogenetic confidence (continuous score from
        # confidence module — replaces the old LOW/GOOD/HIGH boolean flag).
        hit["phylo_conf"] = confidence.score(
            "phylo_16s", "identity_pct", identity,
            context={"raw_value": identity, "species": species,
                     "alignment_length": aln_len},
        )

        # Deduplicate by species — keep best hit per species
        if species not in seen_species:
            hits.append(hit)
            seen_species.add(species)

        if len(hits) >= top_n:
            break

    return hits


def get_organism_info(conn, bacdive_id):
    """Fetch organism details from database."""
    row = conn.execute(
        "SELECT * FROM organisms WHERE id = ?", (bacdive_id,)
    ).fetchone()
    if not row:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM organisms LIMIT 0").description]
    return dict(zip(cols, row))


def get_media_for_organism(conn, bacdive_id):
    """Get all media recipes that support growth of this organism."""
    rows = conn.execute("""
        SELECT m.id, m.source_id, m.name, m.source, m.complex_medium,
               m.min_ph, m.max_ph, m.link, om.growth
        FROM organism_media om
        JOIN media m ON m.id = om.media_id
        WHERE om.organism_id = ?
        ORDER BY om.growth DESC, m.name
    """, (bacdive_id,)).fetchall()

    media = []
    for row in rows:
        media.append({
            "id": row[0],
            "source_id": row[1],
            "name": row[2],
            "source": row[3],
            "complex_medium": row[4],
            "min_ph": row[5],
            "max_ph": row[6],
            "link": row[7],
            "growth": row[8],
        })
    return media


def derive_genus(org):
    """Return the genus for an organism, falling back to first word of species
    name when the genus column is NULL (common for organisms without a fully
    downloaded BacDive record)."""
    if not org:
        return None
    if org.get("genus"):
        return org["genus"]
    species = org.get("species") or ""
    parts = species.strip().split()
    if not parts:
        return None
    first = parts[0]
    # Skip obvious non-genus prefixes
    if first.lower() in {"candidatus", "uncultured", "unidentified"}:
        return parts[1] if len(parts) > 1 else None
    if first[0].isupper():
        return first
    return None


def get_media_for_taxon(conn, level, value, exclude_org_id, limit=10):
    """Get most common positive-growth media for organisms at a given taxonomic level.

    level: 'genus' or 'family'
    value: the genus or family name to search for
    exclude_org_id: skip this organism (the focal hit)

    For 'genus', also matches organisms whose genus column is NULL but whose
    species name starts with the genus (handles incomplete BacDive data).
    """
    if level == "genus":
        # Match by genus column OR by species starting with the genus name + space
        like_pat = f"{value} %"
        rows = conn.execute("""
            SELECT m.id, m.source_id, m.name, m.source, m.complex_medium,
                   m.min_ph, m.max_ph, m.link,
                   COUNT(DISTINCT o.id) AS n_strains
              FROM organisms o
              JOIN organism_media om ON om.organism_id = o.id
              JOIN media m ON m.id = om.media_id
             WHERE (o.genus = ? OR (o.genus IS NULL AND o.species LIKE ?))
               AND om.growth = 1
               AND o.id != ?
             GROUP BY m.id
             ORDER BY n_strains DESC, m.name
             LIMIT ?
        """, (value, like_pat, exclude_org_id, limit)).fetchall()
    elif level == "family":
        rows = conn.execute("""
            SELECT m.id, m.source_id, m.name, m.source, m.complex_medium,
                   m.min_ph, m.max_ph, m.link,
                   COUNT(DISTINCT o.id) AS n_strains
              FROM organisms o
              JOIN organism_media om ON om.organism_id = o.id
              JOIN media m ON m.id = om.media_id
             WHERE o.family = ?
               AND om.growth = 1
               AND o.id != ?
             GROUP BY m.id
             ORDER BY n_strains DESC, m.name
             LIMIT ?
        """, (value, exclude_org_id, limit)).fetchall()
    else:
        return []

    return [
        {
            "id": r[0], "source_id": r[1], "name": r[2], "source": r[3],
            "complex_medium": r[4], "min_ph": r[5], "max_ph": r[6], "link": r[7],
            "growth": 1, "n_strains": r[8],
        }
        for r in rows
    ]


def get_media_with_fallback(conn, organism_id, organism_info):
    """Find media for an organism, falling back through taxonomic levels.

    Returns (media_list, source_tag) where source_tag is one of:
        'direct'                     — at least one positive-growth medium found
        'genus-fallback:Xxx'         — fell back to genus level
        'family-fallback:Yyy'        — fell back to family level
        None                         — no media at any level
    """
    direct = get_media_for_organism(conn, organism_id)
    positive = [m for m in direct if m["growth"] == 1]
    if positive:
        return positive, "direct"

    genus = derive_genus(organism_info)
    if genus:
        genus_media = get_media_for_taxon(conn, "genus", genus, organism_id)
        if genus_media:
            return genus_media, f"genus-fallback:{genus}"

    family = organism_info.get("family") if organism_info else None
    if family:
        family_media = get_media_for_taxon(conn, "family", family, organism_id)
        if family_media:
            return family_media, f"family-fallback:{family}"

    return [], None


def get_media_recipe(conn, media_id):
    """Get the full compound list for a medium."""
    rows = conn.execute("""
        SELECT c.name, mc.solution_name, mc.amount, mc.unit,
               mc.g_per_L, mc.optional
        FROM media_compounds mc
        JOIN compounds c ON c.id = mc.compound_id
        WHERE mc.media_id = ?
        ORDER BY mc.solution_name, mc.amount DESC
    """, (media_id,)).fetchall()

    return [
        {
            "compound": r[0],
            "solution": r[1],
            "amount": r[2],
            "unit": r[3],
            "g_per_L": r[4],
            "optional": bool(r[5]),
        }
        for r in rows
    ]


# ---------------------------------------------------------------- coverage logic

# Substring patterns by which a medium-compound name "directly" provides an
# auxotrophy compound. Lower-case, matched as substring.
DIRECT_COMPOUND_PATTERNS = {
    "L-alanine":         ["alanine"],
    "L-arginine":        ["arginine"],
    "L-asparagine":      ["asparagine"],
    "L-aspartate":       ["aspartate", "aspartic acid"],
    "L-cysteine":        ["cysteine", "cystine"],
    "L-glutamate":       ["glutamate", "glutamic acid"],
    "L-glutamine":       ["glutamine"],
    "glycine":           ["glycine"],
    "L-histidine":       ["histidine"],
    "L-isoleucine":      ["isoleucine"],
    "L-leucine":         ["leucine"],
    "L-lysine":          ["lysine"],
    "L-methionine":      ["methionine"],
    "L-phenylalanine":   ["phenylalanine"],
    "L-proline":         ["proline"],
    "L-serine":          ["serine"],
    "L-threonine":       ["threonine"],
    "L-tryptophan":      ["tryptophan"],
    "L-tyrosine":        ["tyrosine"],
    "L-valine":          ["valine"],
    # vitamins
    "biotin (B7)":       ["biotin"],
    "folate (B9)":       ["folate", "folic acid", "folinic"],
    "thiamin (B1)":      ["thiamin", "thiamine"],
    "riboflavin (B2)":   ["riboflavin", "riboflavine"],
    "pantothenate (B5)": ["pantothen"],
    "pyridoxal-5P (B6)": ["pyridox"],
    "cobalamin (B12)":   ["cobalamin", "vitamin b12", "cyanocobal"],
    "niacin (B3)":       ["nicotin", "niacin"],
    # cofactors
    "heme":              ["heme", "hemin", "haem"],
    "siroheme":          ["siroheme"],
    "molybdopterin":     ["molybdopterin"],
    "NAD":               ["nad+", "nad ", "nadh", "nicotinamide adenine"],
}

# Complex/rich sources that conventionally cover all 20 amino acids.
# These are biological extracts; presence in the medium = AA coverage.
COMPLEX_AMINO_ACID_SOURCES = [
    "yeast extract", "peptone", "tryptone", "trypticase",
    "casein peptone", "casein hydrolysate", "casamino acids",
    "beef extract", "meat extract", "brain heart infusion",
    "soy peptone", "soytone", "proteose peptone", "polypeptone",
    "bacto peptone", "casein digest", "neopeptone",
    "trypticase soy", "tryptic soy",
    "lab-lemco", "liver extract", "tryptose",
]
# Sources that conventionally cover most B-vitamins
COMPLEX_VITAMIN_SOURCES = [
    "yeast extract", "beef extract", "meat extract",
    "brain heart infusion", "malt extract", "liver extract",
]


def coverage_for_medium(recipe, auxotrophies):
    """For each auxotrophy, decide whether the medium covers it.

    Returns dict:
        {auxo_name: ("direct"|"complex"|"missing", source_compound_name)}
    """
    # Lowercase compound names for fast substring matching
    cmpd_names = [(c["compound"], c["compound"].lower()) for c in recipe
                  if c["compound"]]

    has_complex_aa = next(
        ((orig, lo) for orig, lo in cmpd_names
         if any(src in lo for src in COMPLEX_AMINO_ACID_SOURCES)),
        None,
    )
    has_complex_vit = next(
        ((orig, lo) for orig, lo in cmpd_names
         if any(src in lo for src in COMPLEX_VITAMIN_SOURCES)),
        None,
    )

    result = {}
    for a in auxotrophies:
        name = a["name"]
        cls = a["class"]
        patterns = DIRECT_COMPOUND_PATTERNS.get(name, [])

        # Try direct match first (most specific)
        hit = None
        for orig, lo in cmpd_names:
            if any(p in lo for p in patterns):
                hit = ("direct", orig)
                break
        if hit:
            result[name] = hit
            continue

        # Fall back to complex source coverage by class
        if cls == "amino_acid" and has_complex_aa:
            result[name] = ("complex", has_complex_aa[0])
        elif cls == "vitamin" and has_complex_vit:
            result[name] = ("complex", has_complex_vit[0])
        else:
            result[name] = ("missing", None)
    return result


# ---------------------------------------------------------------- ranking

THERMAL_WEIGHTS = {0: 1.0, 1: 0.5, 2: 0.2, 3: 0.1}
UNKNOWN_THERMAL_W = 0.7
FALLBACK_WEIGHTS = {"direct": 1.0, "genus-fallback": 0.6, "family-fallback": 0.3}


def ph_weight(media, user_ph):
    if user_ph is None:
        return 1.0
    lo, hi = media.get("min_ph"), media.get("max_ph")
    if lo is None and hi is None:
        return 1.0
    lo = lo if lo is not None else hi
    hi = hi if hi is not None else lo
    if lo - 1.0 <= user_ph <= hi + 1.0:
        return 1.0
    return 0.3


def coverage_weight(coverage):
    """Soft penalty for missing auxotrophies. 1.0 if all covered, 0.4 floor."""
    if not coverage:
        return 1.0  # no auxotrophies = trivially covered
    n_missing = sum(1 for v in coverage.values() if v[0] == "missing")
    n_total = len(coverage)
    frac_covered = (n_total - n_missing) / n_total
    return 0.4 + 0.6 * frac_covered


def rank_candidate_media(conn, hits, auxotrophies, query_tc, user_ph):
    """Score and rank candidate media across all phylogenetic hits.

    For each hit: fetches organism info and media (with genus/family fallback),
    then scores each candidate medium using identity × thermal × pH × fallback
    × coverage weights.

    Args:
        conn:         open SQLite connection
        hits:         list of BLAST hit dicts (from run_blast)
        auxotrophies: list of auxotrophy dicts (from get_auxotrophies), or []
        query_tc:     thermal class string for the query organism, or None
        user_ph:      user-supplied pH float, or None

    Returns:
        sorted list of (media_id, info_dict) pairs (highest score first).
        Each info_dict has: score, raw_count, sources, name, source_id,
        min_ph, max_ph, recipe, coverage, phylo_identity_best,
        thermal_matches, thermal_mismatches.
    """
    media_records = {}  # media_id -> dict

    for hit in hits:
        org = get_organism_info(conn, hit["bacdive_id"])
        media_list, source_tag = get_media_with_fallback(
            conn, hit["bacdive_id"], org)
        if not source_tag:
            continue

        t_opt = org.get("optimal_temp") if org else None
        tc = classify_temp(t_opt)

        identity_w = hit["identity"] / 100.0
        if query_tc and tc:
            dist = thermal_distance(query_tc, tc)
            therm_w = THERMAL_WEIGHTS.get(dist, 0.1)
        elif query_tc and not tc:
            therm_w = UNKNOWN_THERMAL_W
            dist = None
        else:
            therm_w = 1.0
            dist = None

        fb_w = FALLBACK_WEIGHTS.get(source_tag.split(":", 1)[0], 0.5)

        for m in media_list:
            mid = m["id"]
            if mid not in media_records:
                recipe = get_media_recipe(conn, mid)
                cov = coverage_for_medium(recipe, auxotrophies)
                media_records[mid] = {
                    "name": m["name"],
                    "source_id": m["source_id"],
                    "min_ph": m["min_ph"],
                    "max_ph": m["max_ph"],
                    "recipe": recipe,
                    "coverage": cov,
                    "score": 0.0,
                    "raw_count": 0,
                    "sources": defaultdict(int),
                    "phylo_identity_best": 0.0,
                    "thermal_matches": 0,
                    "thermal_mismatches": 0,
                }
            entry = media_records[mid]
            ph_w = ph_weight(m, user_ph)
            cov_w = coverage_weight(entry["coverage"])
            entry["score"] += identity_w * therm_w * ph_w * fb_w * cov_w
            entry["raw_count"] += 1
            entry["sources"][source_tag] += 1
            entry["phylo_identity_best"] = max(
                entry["phylo_identity_best"], hit["identity"])
            if query_tc and tc:
                if dist == 0:
                    entry["thermal_matches"] += 1
                else:
                    entry["thermal_mismatches"] += 1

    return sorted(media_records.items(), key=lambda kv: -kv[1]["score"])


def format_results(hits, conn, verbose=True, user_temp=None, user_ph=None,
                   user_salinity=None):
    """Pretty-print the phylogenetic match results with temperature-aware scoring.

    Optional environmental overrides (user_temp, user_ph, user_salinity) take
    precedence over inferred values from phylogenetic relatives.
    """
    if not hits:
        print("\nNo matches found.")
        return

    # --- Identity-based confidence (now via the central confidence module) ---
    best_identity = max(h["identity"] for h in hits) if hits else 0
    phylo_conf = confidence.score(
        "phylo_16s", "identity_pct", best_identity,
        context={"raw_value": best_identity, "n_hits": len(hits)},
    )
    confidence_level = phylo_conf.category
    # Append a recommendation when identity is too low for confident prediction
    if phylo_conf.category == "LOW":
        confidence_note = (
            phylo_conf.rationale + "\n"
            "      Media predictions are extrapolated from distant relatives.\n"
            "      RECOMMENDATION: run Tier 2 (structure-based function recovery)\n"
            "      and/or Tier 3 (deep structural analysis) before trusting recipes."
        )
    else:
        confidence_note = phylo_conf.rationale

    # --- Determine query thermal class: user override beats inference ---
    inferred_tc, tc_confidence, inferred_temp = infer_query_thermal_class(hits, conn)
    if user_temp is not None:
        query_tc = classify_temp(user_temp)
        tc_source = "user-supplied"
        effective_temp = user_temp
    else:
        query_tc = inferred_tc
        tc_source = "inferred from relatives"
        effective_temp = inferred_temp

    print(f"\n{'='*80}")
    print(f"  16S PHYLOGENETIC MATCH RESULTS — Top {len(hits)} hits")
    print(f"{'='*80}")

    # Print confidence box (now with continuous score from confidence module)
    print(f"\n  Prediction confidence: {confidence.explain(phylo_conf, brief=True)} "
          f"(best identity: {best_identity:.1f}%)")
    print(f"      {confidence_note}")

    # Print user-supplied environmental data
    env_lines = []
    if user_temp is not None:
        env_lines.append(f"temperature = {user_temp}°C")
    if user_ph is not None:
        env_lines.append(f"pH = {user_ph}")
    if user_salinity is not None:
        env_lines.append(f"salinity = {user_salinity}")
    if env_lines:
        print(f"\n  User-supplied environment: {', '.join(env_lines)}")
        print(f"      These values override any inferred values from phylogenetic relatives.")

    # Print thermal class
    if query_tc:
        if user_temp is not None:
            print(f"\n  Thermal class: {query_tc.upper()} ({tc_source}, T={effective_temp}°C)")
            if inferred_tc and inferred_tc != query_tc:
                print(f"      Note: phylogenetic relatives suggested {inferred_tc.upper()} "
                      f"(~{inferred_temp:.0f}°C) — overridden by user input")
        else:
            print(f"\n  Inferred thermal class: {query_tc.upper()} "
                  f"(weighted T_opt ~{effective_temp:.0f}°C, confidence: {tc_confidence})")
        print(f"      Media from {query_tc} relatives will be ranked higher.")
    else:
        print(f"\n  Thermal class: {tc_confidence}")
    print()

    # --- Per-hit display ---
    # Pre-compute organism info, fallback media, and thermal classes for scoring
    hit_data = []  # (hit, org, positive_media, source_tag, thermal_class)
    for hit in hits:
        org = get_organism_info(conn, hit["bacdive_id"])
        positive_media, source_tag = get_media_with_fallback(
            conn, hit["bacdive_id"], org
        )
        t_opt = org.get("optimal_temp") if org else None
        tc = classify_temp(t_opt)
        hit_data.append((hit, org, positive_media, source_tag, tc))

    for i, (hit, org, positive_media, source_tag, tc) in enumerate(hit_data, 1):
        # Thermal match indicator
        if query_tc and tc:
            dist = thermal_distance(query_tc, tc)
            if dist == 0:
                temp_tag = " [thermal MATCH]"
            elif dist == 1:
                temp_tag = " [thermal adjacent]"
            else:
                temp_tag = f" [thermal MISMATCH, {dist} classes away]"
        else:
            temp_tag = ""

        print(f"  #{i}  {hit['species']}{temp_tag}")
        print(f"      Identity: {hit['identity']:.1f}%  |  "
              f"Alignment: {hit['alignment_length']} bp  |  "
              f"E-value: {hit['evalue']:.2e}  |  "
              f"Accession: {hit['accession']}")

        if org:
            traits = []
            if org.get("optimal_temp"):
                temp_str = f"T_opt={org['optimal_temp']}°C [{classify_temp(org['optimal_temp']) or '?'}]"
                if org.get("min_temp") is not None and org.get("max_temp") is not None:
                    temp_str += f" (range {org['min_temp']:.0f}-{org['max_temp']:.0f}°C)"
                traits.append(temp_str)
            elif org.get("min_temp") is not None or org.get("max_temp") is not None:
                lo = f"{org['min_temp']:.0f}" if org.get("min_temp") is not None else "?"
                hi = f"{org['max_temp']:.0f}" if org.get("max_temp") is not None else "?"
                traits.append(f"T_range={lo}-{hi}°C")
            if org.get("optimal_ph"):
                traits.append(f"pH_opt={org['optimal_ph']}")
            if org.get("oxygen_requirement"):
                traits.append(f"O2={org['oxygen_requirement']}")
            if org.get("phylum"):
                traits.append(f"Phylum={org['phylum']}")
            if org.get("temp_source"):
                traits.append(f"src={org['temp_source']}")
            if traits:
                print(f"      Traits: {', '.join(traits)}")

        if positive_media:
            label = source_tag
            if source_tag and source_tag.startswith("genus-fallback"):
                tax = source_tag.split(":", 1)[1]
                label = f"genus-fallback: {tax}"
            elif source_tag and source_tag.startswith("family-fallback"):
                tax = source_tag.split(":", 1)[1]
                label = f"family-fallback: {tax}"
            print(f"      Media [{label}] ({len(positive_media)} candidates):")
            for m in positive_media[:5]:
                extra = ""
                if "n_strains" in m:
                    extra = f", {m['n_strains']} strains in {label.split(':')[-1].strip() if ':' in label else 'taxon'}"
                print(f"        - {m['name']} (#{m['source_id']}, "
                      f"pH {m['min_ph']}-{m['max_ph']}{extra})")
        else:
            print(f"      Media: none found at organism, genus, or family level")
        print()

    # --- Temperature-weighted media scoring ---
    # Score each medium via the shared rank_candidate_media() function.
    # No auxotrophies available in phylo_match context → pass [] so
    # coverage_weight() returns 1.0 for every medium (no penalty).
    ranked = rank_candidate_media(conn, hits, [], query_tc, user_ph)

    # Enrich ranked entries with ph_mismatch flag for display (not tracked by
    # rank_candidate_media, which only applies the weight during scoring).
    for media_id, info in ranked:
        lo = info.get("min_ph")
        hi = info.get("max_ph")
        if lo is None and hi is None:
            info["ph_mismatch"] = False
        else:
            lo = lo if lo is not None else hi
            hi = hi if hi is not None else lo
            info["ph_mismatch"] = (
                user_ph is not None and not (lo - 1.0 <= user_ph <= hi + 1.0)
            )

    print(f"{'='*80}")
    print(f"  RECOMMENDED MEDIA (temperature-weighted scoring)")
    print(f"{'='*80}\n")
    for media_id, info in ranked[:10]:
        recipe = info["recipe"]

        # Build thermal annotation
        thermal_note = ""
        if info["thermal_matches"] > 0 and info["thermal_mismatches"] == 0:
            thermal_note = " ** thermally consistent"
        elif info["thermal_matches"] > 0 and info["thermal_mismatches"] > 0:
            thermal_note = f" * mixed thermal ({info['thermal_matches']} match, {info['thermal_mismatches']} mismatch)"
        elif info["thermal_mismatches"] > 0 and info["thermal_matches"] == 0:
            thermal_note = " ! thermally inconsistent — use with caution"

        ph_note = " ! pH mismatch" if info["ph_mismatch"] else ""

        # Format source breakdown: "3 direct, 2 genus(Thermus)"
        source_parts = []
        for src, n in sorted(info["sources"].items(), key=lambda x: -x[1]):
            if src == "direct":
                source_parts.append(f"{n} direct")
            elif src.startswith("genus-fallback:"):
                tax = src.split(":", 1)[1]
                source_parts.append(f"{n} genus({tax})")
            elif src.startswith("family-fallback:"):
                tax = src.split(":", 1)[1]
                source_parts.append(f"{n} family({tax})")
            else:
                source_parts.append(f"{n} {src}")
        source_summary = ", ".join(source_parts)

        print(f"  {info['name']}  "
              f"(score: {info['score']:.2f}, "
              f"sources: {source_summary})"
              f"{thermal_note}{ph_note}")
        if verbose and recipe:
            print(f"    Recipe ({len(recipe)} components):")
            for comp in recipe:
                if comp["compound"] == "Distilled water" or comp["compound"] == "Agar":
                    continue
                conc = f"{comp['g_per_L']} g/L" if comp["g_per_L"] else f"{comp['amount']} {comp['unit']}"
                opt = " (optional)" if comp["optional"] else ""
                print(f"      {comp['compound']:40s} {conc}{opt}")
        print()

    return ranked


def prepare_query(input_path):
    """Accept a FASTA file or raw sequence text; return path to a valid FASTA."""
    with open(input_path) as f:
        content = f.read().strip()

    # Already FASTA
    if content.startswith(">"):
        return input_path

    # Raw sequence — wrap in FASTA format
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False)
    tmp.write(">query_16S\n")
    # Clean: remove whitespace and numbers
    seq = "".join(c for c in content if c.isalpha())
    tmp.write(seq + "\n")
    tmp.close()
    return tmp.name


def main():
    parser = argparse.ArgumentParser(
        description="Find closest cultivated relatives by 16S rRNA sequence"
    )
    parser.add_argument("query", help="FASTA file or raw 16S sequence file")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of top hits to show (default: 10)")
    parser.add_argument("--min-identity", type=float, default=80.0,
                        help="Minimum %% identity threshold (default: 80)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON instead of text")
    parser.add_argument("--brief", action="store_true",
                        help="Hide full recipes in text output")
    parser.add_argument("--temperature", type=float, default=None,
                        help="User-supplied growth temperature (°C) — "
                             "overrides inferred thermal class")
    parser.add_argument("--ph", type=float, default=None,
                        help="User-supplied environmental pH")
    parser.add_argument("--salinity", type=float, default=None,
                        help="User-supplied salinity (e.g., %% NaCl)")
    args = parser.parse_args()

    if not os.path.exists(args.query):
        print(f"Error: {args.query} not found", file=sys.stderr)
        sys.exit(1)

    if not (os.path.exists(BLAST_DB + ".ndb") or os.path.exists(BLAST_DB + ".nin")):
        print(f"Error: BLAST database not found at {BLAST_DB}")
        print("Run build_blast_db.py first.")
        sys.exit(1)

    query_fasta = prepare_query(args.query)
    print(f"Searching 16S database with {query_fasta}...")

    hits = run_blast(query_fasta, top_n=args.top, min_identity=args.min_identity)

    conn = sqlite3.connect(DB)
    try:
        if args.json:
            results = []
            for hit in hits:
                org = get_organism_info(conn, hit["bacdive_id"])
                media_list, source_tag = get_media_with_fallback(
                    conn, hit["bacdive_id"], org
                )
                for m in media_list:
                    m["recipe"] = get_media_recipe(conn, m["id"])
                results.append({
                    "hit": hit,
                    "organism": org,
                    "media": media_list,
                    "media_source": source_tag,
                })
            print(json.dumps(results, indent=2))
        else:
            format_results(hits, conn, verbose=not args.brief,
                           user_temp=args.temperature,
                           user_ph=args.ph,
                           user_salinity=args.salinity)
    finally:
        conn.close()

    # Clean up temp file if we created one
    if query_fasta != args.query:
        os.unlink(query_fasta)


if __name__ == "__main__":
    main()
