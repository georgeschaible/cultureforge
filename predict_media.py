"""CultureForge Tier 1 — full pipeline from genome FASTA to media recommendations.

Workflow:
  1. Extract 16S rRNA from the genome (barrnap)
  2. Phylogenetic match against the BLAST DB → closest cultivated relatives
  3. Pull gapseq-derived auxotrophies and transporters from the database
     (genome must already be loaded; run gapseq + load_gapseq.py first)
  4. For each candidate medium from the relatives, compute:
        - which auxotrophies the medium covers (direct or via complex sources)
        - which still need supplementation
  5. Score: identity × thermal × pH × auxotrophy_coverage
  6. Print a structured report

Usage:
    python predict_media.py <genome.fasta> [--accession ACC]
                             [--temperature T] [--ph PH] [--top N]
                             [--simulate-knockout COMPOUND]

Examples:
    python predict_media.py data/genomes/ecoli_k12_mg1655.fasta \\
        --accession NC_000913.3
    python predict_media.py data/genomes/ecoli_k12_mg1655.fasta \\
        --accession NC_000913.3 --simulate-knockout L-lysine
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import tempfile
from collections import defaultdict

import confidence

# Reuse machinery from the 16S-only matcher
from phylo_match import (
    BLAST_DB, DB,
    run_blast,
    get_organism_info,
    get_media_recipe,
    get_media_with_fallback,
    classify_temp,
    thermal_distance,
    infer_query_thermal_class,
    infer_thermal_multisource,
    DIRECT_COMPOUND_PATTERNS,
    COMPLEX_AMINO_ACID_SOURCES,
    COMPLEX_VITAMIN_SOURCES,
    coverage_for_medium,
    THERMAL_WEIGHTS,
    UNKNOWN_THERMAL_W,
    FALLBACK_WEIGHTS,
    ph_weight,
    coverage_weight,
    rank_candidate_media,
)


# ---------------------------------------------------------------- 16S extraction

def extract_16s(genome_fasta, kingdom="bac", min_length=900):
    """Extract 16S rRNA sequence(s) from a genome FASTA using barrnap.

    Returns path to a temp FASTA with one record per detected 16S, or None
    if no 16S found. Filters to records >= min_length to avoid partial fragments.
    """
    # barrnap writes GFF to stdout; pair with bedtools/awk to slice the FASTA
    # Simpler: have barrnap output the actual sequences via --outseq
    out_fasta = tempfile.NamedTemporaryFile(
        mode="w", suffix=".16s.fasta", delete=False
    ).name

    try:
        subprocess.run(
            ["barrnap", "--kingdom", kingdom, "--quiet",
             "--outseq", out_fasta, genome_fasta],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"barrnap failed: {e.stderr}\n")
        return None
    except FileNotFoundError:
        sys.stderr.write("barrnap not found — activate the gapseq conda env "
                         "or install barrnap separately.\n")
        return None

    # Filter: keep only 16S records of sufficient length
    keep = []
    cur_header = None
    cur_seq_lines = []
    with open(out_fasta) as f:
        for line in f:
            if line.startswith(">"):
                if cur_header and "16S_rRNA" in cur_header:
                    seq = "".join(cur_seq_lines)
                    if len(seq) >= min_length:
                        keep.append((cur_header.strip(), seq))
                cur_header = line
                cur_seq_lines = []
            else:
                cur_seq_lines.append(line.strip())
        if cur_header and "16S_rRNA" in cur_header:
            seq = "".join(cur_seq_lines)
            if len(seq) >= min_length:
                keep.append((cur_header.strip(), seq))

    if not keep:
        sys.stderr.write(f"No 16S rRNA sequences ≥{min_length} bp found.\n")
        return None

    # Write a clean FASTA — keep just the longest if multiple copies (rRNA operons
    # are nearly identical; the longest covers the most variable regions)
    keep.sort(key=lambda kv: -len(kv[1]))
    final = tempfile.NamedTemporaryFile(
        mode="w", suffix=".16s.fasta", delete=False
    )
    final.write(f">query_16S\n{keep[0][1]}\n")
    final.close()
    return final.name


# ---------------------------------------------------------------- DB queries

def get_genome_id_for_accession(conn, accession):
    row = conn.execute(
        "SELECT id, organism_id, biomass_template, n_unique_genes, gapseq_version "
        "FROM genomes WHERE accession=?", (accession,)
    ).fetchone()
    return row


def get_auxotrophies(conn, genome_id):
    """Return list of {compound_name, compound_class, best_completeness}."""
    rows = conn.execute("""
        SELECT compound_name, compound_class, best_completeness,
               n_pathway_variants_found
          FROM genome_auxotrophies
         WHERE genome_id=?
      ORDER BY compound_class, compound_name
    """, (genome_id,)).fetchall()
    return [
        {"name": r[0], "class": r[1], "best_completeness": r[2],
         "n_variants_seen": r[3]}
        for r in rows
    ]


def get_transporter_summary(conn, genome_id, top_n=15):
    """Group transporters by substrate; return list of (substrate, count) tuples."""
    rows = conn.execute("""
        SELECT substrate, COUNT(*) AS n
          FROM genome_transporters
         WHERE genome_id=?
      GROUP BY substrate
      ORDER BY n DESC
      LIMIT ?
    """, (genome_id, top_n)).fetchall()
    return rows


def get_metal_profile(conn, genome_id):
    """Return list of dicts for genome_metal_profile rows, ordered by fraction."""
    rows = conn.execute("""
        SELECT metal_ion, n_binding_proteins, n_high_confidence,
               max_probability, fraction_of_proteome, confidence,
               is_anomaly, anomaly_note, media_component, typical_concentration
          FROM genome_metal_profile
         WHERE genome_id=?
      ORDER BY fraction_of_proteome DESC
    """, (genome_id,)).fetchall()
    if not rows:
        return []
    return [
        {
            "metal": r[0], "n_binding": r[1], "n_high_confidence": r[2],
            "max_probability": r[3], "fraction_of_proteome": r[4],
            "confidence": r[5],
            "is_anomaly": bool(r[6]), "anomaly_note": r[7],
            "media_component": r[8], "typical_concentration": r[9],
        }
        for r in rows
    ]


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(
        description="CultureForge Tier 1: predict cultivation media from a genome."
    )
    parser.add_argument("genome", help="Path to genome FASTA")
    parser.add_argument("--accession", default=None,
                        help="Genome accession to look up gapseq results in DB. "
                             "If omitted, uses the FASTA basename.")
    parser.add_argument("--temperature", type=float, default=None,
                        help="User-supplied growth temperature (°C)")
    parser.add_argument("--ph", type=float, default=None,
                        help="User-supplied environmental pH")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of phylogenetic relatives to consider")
    parser.add_argument("--min-identity", type=float, default=80.0,
                        help="BLAST minimum %% identity (default 80)")
    parser.add_argument("--simulate-knockout", default=None,
                        help="Compound name to knock out (e.g., 'L-lysine'). "
                             "Sets all matching biosynthesis pathways to "
                             "predicted=0, completeness=20 within a "
                             "transaction that is rolled back at exit.")
    args = parser.parse_args()

    if not os.path.exists(args.genome):
        sys.exit(f"Genome not found: {args.genome}")

    # ---------------- step 1: 16S extraction
    print(f"\n[1/5] Extracting 16S rRNA from {args.genome} (barrnap)...")
    s16_path = extract_16s(args.genome)
    if not s16_path:
        sys.exit("Aborting: could not extract a 16S sequence.")
    with open(s16_path) as f:
        seq_len = sum(len(line.strip()) for line in f if not line.startswith(">"))
    print(f"      Extracted {seq_len} bp 16S to {s16_path}")

    # ---------------- step 2: phylogenetic match
    print(f"\n[2/5] BLASTing against {BLAST_DB}...")
    hits = run_blast(s16_path, top_n=args.top, min_identity=args.min_identity)
    if not hits:
        sys.exit("No BLAST hits.")
    print(f"      {len(hits)} top hits, best identity {hits[0]['identity']:.1f}% "
          f"({hits[0]['species']})")

    conn = sqlite3.connect(DB)
    try:
        # ---------------- step 3: gapseq predictions
        accession = args.accession or os.path.splitext(os.path.basename(args.genome))[0]
        genome_row = get_genome_id_for_accession(conn, accession)

        if genome_row is None:
            print(f"\n[3/5] No gapseq data found in DB for accession '{accession}'.")
            print("      Run the gapseq pipeline + load_gapseq.py first, or provide "
                  "the correct --accession.\n      Continuing with phylo-only "
                  "analysis (no auxotrophy / transporter info).")
            genome_id = None
            biomass_template = "?"
            n_genes = "?"
            gapseq_v = "?"
        else:
            genome_id, organism_id, biomass_template, n_genes, gapseq_v = genome_row
            print(f"\n[3/5] Loaded gapseq predictions for genome_id={genome_id} "
                  f"(accession={accession}, biomass={biomass_template}, "
                  f"genes={n_genes}, gapseq={gapseq_v})")

        # ---------------- (optional) simulate knockout in a transaction
        in_txn = False
        if args.simulate_knockout and genome_id is not None:
            in_txn = True
            conn.execute("BEGIN")
            # Look up the canonical essential_compound pattern so the knockout
            # matches the same pathways the auxotrophy view considers (avoids
            # drift between e.g. "cobalamin biosynthesis%" vs
            # "%cobalamin biosynthesis%" — actual pathway is "adenosylcobalamin
            # biosynthesis...").
            compound = args.simulate_knockout
            row = conn.execute("""
                SELECT name, pathway_name_pattern FROM essential_compounds
                 WHERE lower(name) = lower(?)
                    OR lower(name) LIKE lower(?) || ' (%'
                    OR lower(name) LIKE lower(?) || '%'
                LIMIT 1
            """, (compound, compound, compound)).fetchone()
            if row is None:
                sys.exit(f"--simulate-knockout: '{compound}' not found in "
                         "essential_compounds. Choose one of: " +
                         ", ".join(r[0] for r in conn.execute(
                            "SELECT name FROM essential_compounds")))
            canonical_name, pattern = row
            n = conn.execute("""
                UPDATE genome_pathways
                   SET predicted=0, completeness=20
                 WHERE genome_id=?
                   AND lower(pathway_name) LIKE lower(?)
                   AND lower(pathway_name) LIKE '%biosynthesis%'
            """, (genome_id, pattern)).rowcount
            print(f"      [SIMULATION] '{canonical_name}': knocked out {n} "
                  f"biosynthesis pathways matching '{pattern}'")

        auxotrophies = get_auxotrophies(conn, genome_id) if genome_id else []
        transporters = get_transporter_summary(conn, genome_id) if genome_id else []
        metal_profile = get_metal_profile(conn, genome_id) if genome_id else []

        # ---------------- step 4: candidate media + coverage analysis
        print(f"\n[4/5] Building candidate media list from {len(hits)} relatives...")

        # Per-hit organism / media (with genus/family fallback)
        hit_data = []
        for hit in hits:
            org = get_organism_info(conn, hit["bacdive_id"])
            media_list, source_tag = get_media_with_fallback(
                conn, hit["bacdive_id"], org
            )
            t_opt = org.get("optimal_temp") if org else None
            tc = classify_temp(t_opt)
            hit_data.append((hit, org, media_list, source_tag, tc))

        # Multi-source thermal inference (GenomeSPOT + TEMPURA + BacDive + phylo)
        # per CLAUDE.md addendum 3. Returns a ConfidenceScore we can pass straight
        # into the recipe composition below.
        query_tc, thermal_multi_conf, effective_temp, thermal_details = \
            infer_thermal_multisource(conn, hits, genome_id=genome_id,
                                       user_temp=args.temperature)
        inferred_tc = query_tc
        inferred_temp = effective_temp
        # Stash for print_report to surface provenance
        args._thermal_conf = thermal_multi_conf
        args._thermal_details = thermal_details

        # Aggregate scoring per medium via shared ranking function
        ranked = rank_candidate_media(conn, hits, auxotrophies, query_tc, args.ph)

        # ---------------- step 4b: per-medium confidence composition
        #
        # The recipe-level confidence for each candidate medium combines:
        #   phylo_conf  — 16S identity score of the best contributing relative
        #   thermal_conf — how well the medium's typical users match query thermal class
        #   medium_conf — intrinsic MediaDive curation confidence (0.95 baseline)
        #   coverage_conf — fraction of auxotrophies covered (direct/complex sources)
        #
        # Per CLAUDE.md addendum 3: "overall = min(critical) + agreement_bonus"
        best_phylo_conf = max(hits, key=lambda h: h["phylo_conf"].value)["phylo_conf"]
        mediadive_conf = confidence.score("mediadive", "curated", None)

        # Thermal matching confidence comes directly from the multi-source helper
        # computed above — no need to recompute here.
        thermal_class_conf = thermal_multi_conf

        for mid, info in media_records.items():
            # coverage fraction → confidence (linear map to [0.50, 0.95])
            cov = info["coverage"]
            if not cov:
                cov_val = 0.95  # no auxotrophies = trivially covered
                cov_note = "no auxotrophies (prototroph)"
            else:
                n_cov = sum(1 for v in cov.values() if v[0] != "missing")
                frac = n_cov / len(cov)
                cov_val = 0.50 + 0.45 * frac
                cov_note = f"{n_cov}/{len(cov)} auxotrophies covered"
            coverage_conf = confidence.ConfidenceScore(
                value=cov_val, source="coverage_analysis",
                rationale=cov_note,
                context={"coverage_fraction": 1.0 if not cov else n_cov / len(cov)},
            )
            info["phylo_conf"] = best_phylo_conf
            info["thermal_conf"] = thermal_class_conf
            info["medium_conf"] = mediadive_conf
            info["coverage_conf"] = coverage_conf
            # Composite: min of critical components, with agreement bonus
            info["overall_conf"] = confidence.combine(
                "min",
                [best_phylo_conf, thermal_class_conf, mediadive_conf, coverage_conf],
                agreement_bonus=True,
            )

        # ---------------- step 5: report
        print(f"\n[5/5] Generating report\n")
        print_report(args, hits, hit_data, query_tc, inferred_tc, inferred_temp,
                     biomass_template, n_genes, gapseq_v, auxotrophies,
                     transporters, metal_profile, ranked)

        if in_txn:
            conn.execute("ROLLBACK")
            print("\n[Note] Simulated knockout rolled back. Database is unchanged.")
    finally:
        conn.close()


# ---------------------------------------------------------------- report

def _classify_substrate(substrate):
    """Group transporter substrates into rough functional classes for the report."""
    s = substrate.lower()
    metals = {"iron", "zinc", "copper", "manganese", "cobalt", "molybdate",
              "molybdenum", "nickel", "cadmium", "magnesium", "calcium",
              "potassium", "sodium", "chloride"}
    if any(m in s for m in metals):
        return "metals/ions"
    sugars = {"glucose", "ribose", "arabinose", "xylose", "fructose", "lactose",
              "galactose", "maltose", "sucrose", "trehalose", "mannose",
              "rhamnose", "fucose", "glycerol", "arabitol", "ribitol", "xylitol"}
    if any(g in s for g in sugars):
        return "sugars/polyols"
    aas = {"alanine", "valine", "leucine", "isoleucine", "lysine", "arginine",
           "serine", "threonine", "glutamine", "asparagine", "histidine",
           "methionine", "cysteine", "phenylalanine", "tyrosine", "tryptophan",
           "proline", "glycine", "glutamate", "aspartate"}
    if any(a in s for a in aas):
        return "amino acids/peptides"
    nitrogens = {"ammoni", "nitrate", "nitrite", "urea"}
    if any(n in s for n in nitrogens):
        return "nitrogen sources"
    sulfs = {"sulfate", "sulfite", "thiosulfate", "taurine"}
    if any(p in s for p in sulfs):
        return "sulfur sources"
    if "phosph" in s:
        return "phosphate"
    return "other"


def print_report(args, hits, hit_data, query_tc, inferred_tc, inferred_temp,
                 biomass_template, n_genes, gapseq_v,
                 auxotrophies, transporters, metal_profile, ranked_media):
    bar = "=" * 80
    print(bar)
    print(f"  CULTUREFORGE TIER 1 PREDICTION — {os.path.basename(args.genome)}")
    print(bar)

    # 1. confidence
    best_id = max(h["identity"] for h in hits) if hits else 0
    if best_id < 90:
        conf = "LOW"
    elif best_id < 95:
        conf = "MODERATE"
    elif best_id < 97:
        conf = "GOOD"
    else:
        conf = "HIGH"
    print(f"\n  Phylogenetic confidence: {conf} (best 16S identity {best_id:.1f}%)")

    # 2. user inputs / inferred params (with multi-source provenance)
    thermal_conf = getattr(args, "_thermal_conf", None)
    thermal_details = getattr(args, "_thermal_details", {}) or {}
    if query_tc:
        src_str = ", ".join(f"{k}={t:.0f}°C" for k, t in thermal_details.items())
        extra = f" [sources: {src_str}]" if src_str else ""
        label = f"{int(thermal_conf.value*100)}%" if thermal_conf else ""
        print(f"  Thermal class: {query_tc.upper()} (~{inferred_temp:.0f}°C, "
              f"confidence {label}){extra}")
        if thermal_conf:
            print(f"      → {thermal_conf.rationale}")
    if args.ph is not None:
        print(f"  Environmental pH: {args.ph}")

    # 3. genome / gapseq summary
    print(f"  Genome metadata: biomass={biomass_template}, "
          f"genes={n_genes}, gapseq={gapseq_v}")

    # 4. relatives
    print(f"\n{bar}")
    print("  PHYLOGENETIC RELATIVES (top 5)")
    print(bar)
    for i, (hit, org, media_list, source_tag, tc) in enumerate(hit_data[:5], 1):
        tag = ""
        if query_tc and tc:
            d = thermal_distance(query_tc, tc)
            tag = " [thermal MATCH]" if d == 0 else f" [thermal Δ={d}]"
        print(f"  #{i}  {hit['species']}  ({hit['identity']:.1f}% id, "
              f"{hit['alignment_length']} bp){tag}")
        if org and org.get("optimal_temp"):
            print(f"        T_opt={org['optimal_temp']}°C  "
                  f"phylum={org.get('phylum') or '?'}")

    # 5. auxotrophies
    print(f"\n{bar}")
    print("  PREDICTED AUXOTROPHIES "
          f"({len(auxotrophies)} compounds needed from medium)")
    print(bar)
    if not auxotrophies:
        print("  [PROTOTROPH] organism synthesises every essential compound "
              "in our list.")
        print("  Medium needs: carbon, N, P, S, salts only — no organic "
              "supplements.")
    else:
        by_class = defaultdict(list)
        for a in auxotrophies:
            by_class[a["class"]].append(a)
        for cls, items in by_class.items():
            print(f"\n  {cls.upper()} ({len(items)}):")
            for a in items:
                comp_pct = a["best_completeness"] or 0
                vars_seen = a["n_variants_seen"] or 0
                print(f"    - {a['name']:25s} (best biosynthesis pathway "
                      f"{comp_pct:5.1f}% across {vars_seen} variants)")

    # 6. transporters
    print(f"\n{bar}")
    print("  PREDICTED TRANSPORTERS (grouped by substrate class)")
    print(bar)
    if not transporters:
        print("  No transporter data available.")
    else:
        groups = defaultdict(list)
        for sub, n in transporters:
            groups[_classify_substrate(sub)].append((sub, n))
        for cls in ["sugars/polyols", "amino acids/peptides", "metals/ions",
                    "nitrogen sources", "sulfur sources", "phosphate", "other"]:
            items = groups.get(cls, [])
            if not items:
                continue
            tot = sum(n for _, n in items)
            uniq = len(items)
            top = ", ".join(f"{s}({n})" for s, n in items[:6])
            print(f"  {cls:22s} {uniq:>3} substrates / {tot:>4} entries: {top}")

    # 6b. predicted metal-binding profile (MeBiPred)
    print(f"\n{bar}")
    print("  PREDICTED METAL REQUIREMENTS (MeBiPred)")
    print(bar)
    if not metal_profile:
        print("  No MeBiPred data loaded for this genome.")
        print("  Run: python run_mebipred.py <proteins.faa> <out.tsv> && "
              "python load_mebipred.py <accession> <out.tsv>")
    else:
        print(f"  {'Metal':6s} {'n_bind':>7s} {'n_high':>7s} "
              f"{'max_p':>6s} {'frac%':>6s} {'conf':>5s}  media_component")
        strong = [m for m in metal_profile if m["n_binding"] >= 5
                  and m["max_probability"] >= 0.75]
        weak   = [m for m in metal_profile if m not in strong]
        for m in metal_profile:
            flag = ""
            if m["is_anomaly"]:
                flag = f"  ⚠ {m['anomaly_note']}"
            mc = m.get("media_component") or "-"
            print(f"  {m['metal']:6s} {m['n_binding']:>7d} "
                  f"{m['n_high_confidence']:>7d} {m['max_probability']:>6.2f} "
                  f"{100*m['fraction_of_proteome']:>5.1f}% "
                  f"{m['confidence']:>5.2f}  {mc}{flag}")
        # Summary line
        n_strong = len(strong)
        total_prots = sum(m["n_binding"] for m in metal_profile)
        print(f"\n  Strong metal requirements (≥5 binding proteins, max_p≥0.75): "
              f"{n_strong} metals "
              f"({', '.join(m['metal'] for m in strong) if strong else 'none'})")
        anomalies = [m for m in metal_profile if m["is_anomaly"]]
        if anomalies:
            print(f"  Anomaly flags: "
                  + ", ".join(f"{m['metal']} ({m['anomaly_note']})"
                              for m in anomalies))
        else:
            print(f"  Anomaly flags: none (all metals within typical proteome "
                  f"fractions for the 10 metals MeBiPred predicts)")
        print(f"  Note: MeBiPred does not predict W/V/Se — for unusual "
              f"metabolisms requiring tungsten (hyperthermophilic "
              f"methanogens), vanadium, or selenium, supplement via "
              f"BRENDA cross-reference (not yet integrated).")

    # 7. media recommendations with coverage
    print(f"\n{bar}")
    print("  RECOMMENDED MEDIA (with auxotrophy coverage analysis)")
    print(bar)
    if not ranked_media:
        print("  No candidate media surfaced.")
        return
    n_show = min(8, len(ranked_media))
    for i, (mid, info) in enumerate(ranked_media[:n_show], 1):
        # Coverage status
        cov = info["coverage"]
        if not cov:
            cov_status = "(no auxotrophies — fully covered)"
        else:
            n_dir = sum(1 for v in cov.values() if v[0] == "direct")
            n_cmp = sum(1 for v in cov.values() if v[0] == "complex")
            n_mis = sum(1 for v in cov.values() if v[0] == "missing")
            tot = len(cov)
            cov_status = f"covers {n_dir + n_cmp}/{tot} (direct={n_dir}, complex={n_cmp}, MISSING={n_mis})"

        # Source breakdown
        srcs = ", ".join(
            f"{n} {s.split(':',1)[0].replace('genus-fallback','genus').replace('family-fallback','family')}"
            + (f"({s.split(':',1)[1]})" if ':' in s else "")
            for s, n in sorted(info["sources"].items(), key=lambda x: -x[1])
        )

        # Thermal flag
        flag = ""
        if info["thermal_matches"] > 0 and info["thermal_mismatches"] == 0:
            flag = " ✱thermal"
        elif info["thermal_mismatches"] > 0 and info["thermal_matches"] == 0:
            flag = " !thermal-mismatch"

        overall_conf = info.get("overall_conf")
        conf_label = (
            confidence.explain(overall_conf, brief=True) if overall_conf else "?"
        )
        print(f"\n  #{i}  {info['name']}  "
              f"— overall {conf_label}  (score {info['score']:.2f}{flag})")
        print(f"        pH {info['min_ph']}-{info['max_ph']}  |  "
              f"sources: {srcs}")
        print(f"        Coverage: {cov_status}")

        # Per-component confidence breakdown per CLAUDE.md addendum 3 example
        if overall_conf:
            comps = [
                ("Phylogenetic match",   info["phylo_conf"]),
                ("Thermal match",        info["thermal_conf"]),
                ("Medium curation",      info["medium_conf"]),
                ("Auxotrophy coverage",  info["coverage_conf"]),
            ]
            for label, c in comps:
                flag_marker = " ⚠" if c.value < 0.75 else ""
                print(f"          [{int(c.value*100):>3}%]{flag_marker} "
                      f"{label:22s} → {c.rationale}")

        # If there are auxotrophies, break them down
        if cov:
            for auxo, (status, src) in cov.items():
                if status == "direct":
                    print(f"          ✓ {auxo:25s} via {src}")
                elif status == "complex":
                    print(f"          ✓ {auxo:25s} via complex source: {src}")
                else:
                    print(f"          ✗ {auxo:25s} → SUPPLEMENT REQUIRED")

    # 8. global supplement summary across the top medium
    print(f"\n{bar}")
    print("  SUPPLEMENT SUMMARY")
    print(bar)
    if not auxotrophies:
        print("  None — organism predicted to be a prototroph.")
    else:
        top_id, top_info = ranked_media[0]
        missing = [name for name, (st, _) in top_info["coverage"].items()
                   if st == "missing"]
        if not missing:
            print(f"  Using top recommendation '{top_info['name']}': all "
                  f"{len(auxotrophies)} auxotrophies covered. No supplements "
                  f"needed.")
        else:
            print(f"  If using top recommendation '{top_info['name']}', supply:")
            for m in missing:
                print(f"    - {m}")
            print("  These compounds are not present (directly or via a complex "
                  "source) in the recommended medium.")

    # 9. Provenance block — which tools/databases contributed
    print(f"\n{bar}")
    print("  PROVENANCE")
    print(bar)
    print(f"  Phylogenetic match:  MediaDive + BacDive (16S BLAST against "
          f"12,318 reference sequences)")
    if auxotrophies is not None:
        print(f"  Metabolic analysis:  gapseq {gapseq_v} "
              f"(pathway completeness, transporters, auxotrophy inference)")
    env_src = "BacDive + TEMPURA (T_opt coverage) + GenomeSPOT"
    if args.temperature is not None or args.ph is not None:
        env_src += " + user override"
    print(f"  Environmental:       {env_src}")
    if metal_profile:
        print(f"  Metal profile:       MeBiPred (10 metals: Ca, Co, Cu, Fe, "
              f"K, Mg, Mn, Na, Ni, Zn)")
    # Flag missing components that CLAUDE.md mentions but we haven't wired yet
    missing_components = []
    if not metal_profile:
        missing_components.append("MeBiPred metal binding")
    missing_components.append("Amend & Shock thermodynamics check")
    missing_components.append("BRENDA enzyme/cofactor cross-reference")
    if missing_components:
        print(f"  Not yet integrated:  {', '.join(missing_components)}")
    # Uncertainty summary — flag any component <0.75 across top candidate
    if ranked_media:
        top_info = ranked_media[0][1]
        comps_with_conf = [
            ("Phylogenetic",  top_info.get("phylo_conf")),
            ("Thermal",       top_info.get("thermal_conf")),
            ("Medium",        top_info.get("medium_conf")),
            ("Coverage",      top_info.get("coverage_conf")),
        ]
        uncertain = [(l, c) for l, c in comps_with_conf
                     if c is not None and c.value < 0.75]
        if uncertain:
            print(f"\n  UNCERTAINTY FLAGS (components <0.75):")
            for label, c in uncertain:
                print(f"    ⚠ {label}: {confidence.explain(c, brief=True)}")
                print(f"      → {c.rationale}")
            print(f"  → RECOMMENDATION: vary uncertain components "
                  f"experimentally; consider promoting to Tier 2 "
                  f"(structure-based) or Tier 3 (deep) analysis.")


if __name__ == "__main__":
    main()
