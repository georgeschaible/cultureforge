#!/usr/bin/env python3
"""CultureForge — AI-driven cultivation media prediction from genome sequences.

Subcommands:
    inspect     Examine what CultureForge knows about a genome
    (synthesize, consistency-check — planned for Phase 2b+)

Usage:
    cultureforge inspect <identifier>
    cultureforge inspect <identifier> --section capabilities
    cultureforge inspect <identifier> --json
    cultureforge inspect --list
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent
DB_DEFAULT = str(_ROOT / "data" / "cultureforge.db")

# ---------------------------------------------------------------------------
# Genome identifier resolution
# ---------------------------------------------------------------------------

def _resolve_genome(conn, identifier):
    """Resolve identifier to (genome_id, accession, species_name).

    Accepts numeric ID, accession string, or species name (fuzzy).
    Returns None if not found, or raises SystemExit for ambiguous names.
    """
    # Try numeric ID
    try:
        gid = int(identifier)
        row = conn.execute("""
            SELECT g.id, g.accession, COALESCE(o.species, g.notes)
            FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
            WHERE g.id = ?
        """, (gid,)).fetchone()
        if row:
            return row
    except (ValueError, TypeError):
        pass

    # Try accession
    row = conn.execute("""
        SELECT g.id, g.accession, COALESCE(o.species, g.notes)
        FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
        WHERE g.accession = ?
    """, (identifier,)).fetchone()
    if row:
        return row

    # Try species name (fuzzy)
    pattern = f"%{identifier}%"
    rows = conn.execute("""
        SELECT g.id, g.accession, COALESCE(o.species, g.notes)
        FROM genomes g LEFT JOIN organisms o ON o.id = g.organism_id
        WHERE lower(COALESCE(o.species, g.notes, '')) LIKE lower(?)
    """, (pattern,)).fetchall()

    if len(rows) == 1:
        return rows[0]
    elif len(rows) > 1:
        print(f"Multiple genomes match '{identifier}':")
        for r in rows:
            print(f"  ID {r[0]:3d}: {r[1]}  {r[2] or ''}")
        print("Please specify by accession or genome ID.")
        sys.exit(1)

    return None


# ---------------------------------------------------------------------------
# Section renderers (text)
# ---------------------------------------------------------------------------

def _section_header(conn, gid, accession, species):
    """Section 1: Header."""
    domain = conn.execute(
        "SELECT biomass_template FROM genomes WHERE id = ?", (gid,)
    ).fetchone()
    domain_str = domain[0] if domain else "Unknown"

    # Try git hash
    version = datetime.now().strftime("%Y-%m-%d")
    try:
        git = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(_ROOT), timeout=5)
        if git.returncode == 0:
            version = f"git:{git.stdout.strip()}"
    except Exception:
        pass

    lines = []
    bar = "\u2550" * 70
    lines.append(bar)
    lines.append("CultureForge Inspection Report")
    # Clean up species display
    sp = (species or "Unknown")
    for prefix in ("Validation organism: ", "Blind validation: ", "Blind v2: "):
        sp = sp.replace(prefix, "")
    sp = sp.replace("_", " ")
    lines.append(f"Genome: {sp} ({accession})")
    lines.append(f"Genome ID: {gid}")
    lines.append(f"Domain: {domain_str}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"CultureForge version: {version}")
    lines.append(bar)
    return "\n".join(lines)


def _section_quality(conn, gid):
    """Section 2: Genome Quality."""
    lines = ["\nGENOME QUALITY (Section 2)", "\u2500" * 70]
    row = conn.execute("""
        SELECT completeness, contamination, strain_heterogeneity,
               genome_size, gc_content, n50, acidic_residue_fraction, checkm_version
        FROM genome_quality WHERE genome_id = ?
    """, (gid,)).fetchone()

    if not row:
        lines.append("CheckM not run for this genome.")
        lines.append("\u2500" * 70)
        return "\n".join(lines)

    comp, contam, strain_het, gsize, gc, n50, acidic, checkm_v = row
    if comp is not None:
        lines.append(f"CheckM completeness:        {comp:.1f}%")
        lines.append(f"CheckM contamination:       {contam:.1f}%")
        if strain_het is not None:
            lines.append(f"Strain heterogeneity:       {strain_het:.1f}%")
    else:
        lines.append("CheckM not available (genome stats only)")
    if gsize:
        lines.append(f"Genome size:                {gsize:,} bp ({gsize/1e6:.2f} Mb)")
    if gc:
        lines.append(f"GC content:                 {gc:.1%}")
    if n50:
        lines.append(f"N50:                        {n50:,}")
    if acidic is not None:
        lines.append(f"Acidic residue fraction:    {acidic:.4f}")

    # QC verdict
    sys.path.insert(0, str(_ROOT))
    from qc_gate import evaluate_genome_quality
    verdict = evaluate_genome_quality(gid, conn)
    lines.append(f"QC verdict:                 {verdict.verdict}")
    lines.append(f"QC rationale:               {verdict.rationale}")
    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_predictions(conn, gid):
    """Section 3: GenomeSPOT Predictions."""
    lines = ["\nGROWTH CONDITIONS (Section 3) - GenomeSPOT predictions", "\u2500" * 70]

    rows = conn.execute("""
        SELECT target, value, numeric_value, error, confidence
        FROM genome_growth_predictions WHERE genome_id = ?
    """, (gid,)).fetchall()

    if not rows:
        lines.append("GenomeSPOT not run for this genome.")
        lines.append("\u2500" * 70)
        return "\n".join(lines)

    domain = conn.execute(
        "SELECT biomass_template FROM genomes WHERE id = ?", (gid,)
    ).fetchone()
    is_archaea = domain and domain[0] == "Archaea"

    for target, value, num, error, conf in rows:
        t = target.lower()
        conf_str = f"(conf {conf:.2f})" if conf else ""
        err_str = f" \u00b1{error:.1f}" if error else ""
        if "temperature" in t and "optimum" in t:
            lines.append(f"Predicted temperature optimum:  {num:.1f}\u00b0C{err_str} {conf_str}")
        elif "ph" in t and "optimum" in t:
            lines.append(f"Predicted pH optimum:           {num:.1f}{err_str} {conf_str}")
        elif "salinity" in t and "optimum" in t:
            lines.append(f"Predicted salinity optimum:     {num:.2f}% NaCl{err_str} {conf_str}")
        elif "oxygen" in t:
            lines.append(f"Predicted oxygen tolerance:     {value} {conf_str}")
            if is_archaea:
                lines.append("  Note: GenomeSPOT oxygen predictions are unreliable for "
                             "archaea; cross-check against capability results.")

    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_capabilities(conn, gid):
    """Section 4: Capability Profile."""
    sys.path.insert(0, str(_ROOT))
    from capability_detectors import profile_capabilities

    profile = profile_capabilities(gid, conn)
    lines = ["\nCAPABILITY PROFILE (Section 4)", "\u2500" * 70]

    # Cultivation modes
    if profile.cultivation_modes:
        lines.append("\nPRIMARY CULTIVATION MODES")
        for mode in profile.cultivation_modes:
            lines.append(f"\n  Mode: {mode['mode']:<40s} conf {mode['max_confidence']:.2f}")
            for cap_name, cap_conf in mode["capabilities"]:
                short = _short_cap_name(cap_name)
                lines.append(f"    \u251c\u2500 {short:<50s} {cap_conf:.3f}")
                # Find the full capability object for evidence
                cap_obj = next((c for c in profile.capabilities if c.name == cap_name), None)
                if cap_obj:
                    for ev in cap_obj.evidence_summary[:4]:
                        lines.append(f"    \u2502   {ev}")
                    if cap_obj.diagnostic_markers_hit:
                        lines.append(f"    \u2502   Diagnostic markers: {', '.join(cap_obj.diagnostic_markers_hit)}")
    else:
        lines.append("\nNo cultivation modes detected above threshold.")

    # Detected capabilities
    detected = sorted([c for c in profile.capabilities if c.detected],
                      key=lambda c: c.confidence, reverse=True)
    if detected:
        lines.append("\n  DETECTED CAPABILITIES (confidence >= 0.50)")
        for cap in detected:
            tag = "primary" if cap.confidence >= 0.60 else "secondary"
            short_name = _short_cap_name(cap.name)
            lines.append(f"    {short_name:<50s} {cap.confidence:.3f}  {tag}")

    # Rejected capabilities
    rejected = sorted([c for c in profile.capabilities if not c.detected and c.confidence > 0],
                      key=lambda c: c.confidence, reverse=True)
    if rejected:
        lines.append("\n  REJECTED CAPABILITIES")
        for cap in rejected[:10]:
            short_name = _short_cap_name(cap.name)
            reason = _human_reject_reason(cap)
            lines.append(f"    {short_name[:40]:<42s} {cap.confidence:.3f}  {reason}")

    # Uncertainty flags
    all_flags = []
    for cap in detected:
        for uf in cap.uncertainty_flags:
            all_flags.append(f"[{cap.name[:25]}] {uf}")
    if all_flags:
        lines.append("\n  UNCERTAINTY FLAGS")
        for flag in all_flags[:5]:
            lines.append(f"    - {flag}")

    lines.append("\n" + "\u2500" * 70)
    return "\n".join(lines)


def _section_pathways(conn, gid):
    """Section 5: gapseq Pathways (top 20)."""
    total = conn.execute(
        "SELECT COUNT(*) FROM genome_pathways WHERE genome_id = ?", (gid,)
    ).fetchone()[0]

    n_predicted = conn.execute(
        "SELECT COUNT(*) FROM genome_pathways WHERE genome_id = ? AND predicted = 1", (gid,)
    ).fetchone()[0]

    lines = [f"\ngapseq PATHWAYS (Section 5) - {n_predicted} predicted of {total} total",
             "\u2500" * 70]

    # Show predicted pathways first (metabolically active), then top by completeness
    rows = conn.execute("""
        SELECT pathway_name, completeness, predicted
        FROM genome_pathways WHERE genome_id = ?
        ORDER BY predicted DESC, completeness DESC LIMIT 25
    """, (gid,)).fetchall()

    if not rows:
        lines.append("No gapseq pathways loaded for this genome.")
    else:
        # Filter out universal pathways (amino acid/nucleotide biosynthesis) from display
        # unless they're the only predicted ones
        metabolic_keywords = [
            "methanogenesis", "sulfate", "sulfur", "sulfide", "thiosulfate",
            "denitrification", "nitrogen fixation", "ammonia", "fermentation",
            "TCA cycle", "glycolysis", "respiration", "photosyn", "Calvin",
            "reductive", "Wood-Ljung", "acetogenesis", "acetyl coenzyme A",
            "hydrogenase", "iron", "methanol", "formate", "lactate", "ethanol",
            "butanol", "butyrate", "acetate", "beta-oxidation",
        ]
        metabolic = [(n, c, p) for n, c, p in rows
                     if any(kw.lower() in n.lower() for kw in metabolic_keywords)]
        other_predicted = [(n, c, p) for n, c, p in rows if p and (n, c, p) not in metabolic]

        if metabolic:
            lines.append("  Metabolically relevant:")
            for name, comp, pred in metabolic[:15]:
                mark = "\u2713" if pred else " "
                lines.append(f"    {name[:55]:<57s} {comp:5.0f}%  {mark}")
        if other_predicted:
            lines.append(f"  Other predicted pathways ({len(other_predicted)} more):")
            for name, comp, pred in other_predicted[:5]:
                lines.append(f"    {name[:55]:<57s} {comp:5.0f}%  \u2713")

    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_markers(conn, gid):
    """Section 6: Diagnostic Marker BLAST/HMM Hits."""
    lines = ["\nDIAGNOSTIC MARKER HITS (Section 6)", "\u2500" * 70]

    # Get all markers that exist in the database (any genome)
    all_markers = [r[0] for r in conn.execute(
        "SELECT DISTINCT marker_name FROM genome_diagnostic_markers ORDER BY marker_name"
    ).fetchall()]

    if not all_markers:
        lines.append("No diagnostic marker data in database.")
        lines.append("\u2500" * 70)
        return "\n".join(lines)

    lines.append(f"  {'Marker':<20s} {'Method':<8s} {'Best Hit':<25s} {'Identity':>8s} {'Bitscore':>8s} {'Status'}")
    lines.append("  " + "\u2500" * 65)

    for marker in all_markers:
        try:
            row = conn.execute("""
                SELECT hit_accession, pident, bitscore, positive_call, 'blastp'
                FROM genome_diagnostic_markers
                WHERE genome_id = ? AND marker_name = ?
                ORDER BY bitscore DESC LIMIT 1
            """, (gid, marker)).fetchone()
        except Exception:
            row = None

        if row:
            acc, pid, bs, pos, method = row
            acc_short = (acc or "")[:23]
            pid_str = f"{pid:.1f}%" if pid else "n/a"
            bs_str = f"{bs:.0f}" if bs else "n/a"
            status = "POSITIVE" if pos else "(weak)"
            lines.append(f"  {marker:<20s} {method:<8s} {acc_short:<25s} {pid_str:>8s} {bs_str:>8s} {status}")
        else:
            lines.append(f"  {marker:<20s} {'blastp':<8s} {'no hit':<25s} {'':>8s} {'':>8s} (negative)")

    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_hydrogenases(conn, gid):
    """Section 7: Hydrogenases."""
    lines = ["\nHYDROGENASES (Section 7)", "\u2500" * 70]

    rows = conn.execute("""
        SELECT hydrogenase_type, group_id, gene_id, pident, bitscore
        FROM genome_hydrogenases WHERE genome_id = ? AND bitscore >= 100
        ORDER BY bitscore DESC
    """, (gid,)).fetchall()

    if not rows:
        lines.append("No hydrogenases detected (bitscore >= 100).")
    else:
        lines.append(f"  {'Type':<10s} {'Group':<8s} {'Gene':<25s} {'Identity':>8s} {'Bitscore':>8s}")
        lines.append("  " + "\u2500" * 55)
        for h_type, group, gene, pid, bs in rows[:10]:
            lines.append(f"  {h_type or '?':<10s} {group or '?':<8s} {(gene or '')[:23]:<25s} "
                         f"{pid:.1f}%{bs:>10.0f}")

    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_action(conn, gid):
    """Section 8: Recommended Action."""
    sys.path.insert(0, str(_ROOT))
    from capability_detectors import profile_capabilities

    profile = profile_capabilities(gid, conn)
    lines = ["\nRECOMMENDED ACTION (Section 8)", "\u2500" * 70]

    # Override flag_uncertain when capabilities are clearly detected
    action = profile.recommended_action.upper()
    if action == "FLAG_UNCERTAIN" and profile.cultivation_modes:
        best_conf = max(m["max_confidence"] for m in profile.cultivation_modes)
        if best_conf >= 0.60:
            action = "SYNTHESIZE (CheckM not run but capabilities clearly detected)"
        elif best_conf >= 0.50:
            action = "SYNTHESIZE_WITH_CAUTION (capabilities detected, no CheckM verification)"

    lines.append(f"Action:    {action}")
    if profile.escalation_rationale:
        lines.append(f"Rationale: {profile.escalation_rationale}")
    else:
        modes = [m["mode"] for m in profile.cultivation_modes]
        if modes:
            lines.append(f"Rationale: Cultivation mode(s): {', '.join(modes)}")
        else:
            lines.append(f"Rationale: No clear cultivation mode detected.")

    # Growth condition notes from GenomeSPOT
    preds = conn.execute("""
        SELECT target, value, numeric_value
        FROM genome_growth_predictions WHERE genome_id = ?
    """, (gid,)).fetchall()
    notes = []
    for target, value, num in preds:
        t = target.lower()
        if "temperature" in t and "optimum" in t and num:
            notes.append(f"Predicted growth temperature: {num:.0f}\u00b0C")
        elif "ph" in t and "optimum" in t and num:
            notes.append(f"Predicted pH: {num:.1f}")
        elif "oxygen" in t:
            notes.append(f"Predicted oxygen: {value}")

    if notes:
        lines.append("\nNotes:")
        for n in notes:
            lines.append(f"  - {n}")

    lines.append("\u2500" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def _build_json(conn, gid, accession, species, overrides=None):
    """Build complete JSON output."""
    sys.path.insert(0, str(_ROOT))
    from capability_detectors import profile_capabilities

    profile = profile_capabilities(gid, conn)

    domain_row = conn.execute(
        "SELECT biomass_template FROM genomes WHERE id = ?", (gid,)
    ).fetchone()

    # Quality
    qc_row = conn.execute("""
        SELECT completeness, contamination, genome_size, gc_content, n50,
               acidic_residue_fraction
        FROM genome_quality WHERE genome_id = ?
    """, (gid,)).fetchone()

    # Predictions
    preds = {}
    for row in conn.execute("""
        SELECT target, value, numeric_value, confidence
        FROM genome_growth_predictions WHERE genome_id = ?
    """, (gid,)).fetchall():
        key = row[0].lower().replace(" ", "_")
        preds[key] = {"value": row[1], "numeric": row[2], "confidence": row[3]}

    # Pathways
    pathways = [{"name": r[0], "completeness": r[1], "predicted": bool(r[2])}
                for r in conn.execute("""
                    SELECT pathway_name, completeness, predicted
                    FROM genome_pathways WHERE genome_id = ?
                    ORDER BY completeness DESC LIMIT 20
                """, (gid,)).fetchall()]

    # Markers
    markers = {}
    for r in conn.execute("""
        SELECT marker_name, hit_accession, pident, bitscore, positive_call
        FROM genome_diagnostic_markers WHERE genome_id = ?
        ORDER BY marker_name, bitscore DESC
    """, (gid,)).fetchall():
        if r[0] not in markers:
            markers[r[0]] = {"accession": r[1], "pident": r[2], "bitscore": r[3],
                             "positive": bool(r[4]), "method": "blastp"}

    # Hydrogenases
    hydro = [{"type": r[0], "group": r[1], "gene": r[2], "pident": r[3], "bitscore": r[4]}
             for r in conn.execute("""
                 SELECT hydrogenase_type, group_id, gene_id, pident, bitscore
                 FROM genome_hydrogenases WHERE genome_id = ? AND bitscore >= 100
                 ORDER BY bitscore DESC LIMIT 10
             """, (gid,)).fetchall()]

    result = {
        "header": {
            "genome_id": gid,
            "accession": accession,
            "species": species,
            "domain": domain_row[0] if domain_row else None,
            "generated_at": datetime.now().isoformat(),
        },
        "quality": {
            "completeness": qc_row[0] if qc_row else None,
            "contamination": qc_row[1] if qc_row else None,
            "genome_size": qc_row[2] if qc_row else None,
            "gc_content": qc_row[3] if qc_row else None,
            "verdict": profile.quality_verdict.verdict,
            "rationale": profile.quality_verdict.rationale,
        },
        "predictions": preds,
        "capabilities": {
            "cultivation_modes": profile.cultivation_modes,
            "detected": [
                {"name": c.name, "confidence": c.confidence,
                 "markers": c.diagnostic_markers_hit,
                 "evidence": c.evidence_summary[:5]}
                for c in sorted(profile.capabilities, key=lambda x: x.confidence, reverse=True)
                if c.detected
            ],
            "rejected": [
                {"name": c.name, "confidence": c.confidence,
                 "negative_markers": c.negative_markers_present,
                 "flags": c.uncertainty_flags}
                for c in sorted(profile.capabilities, key=lambda x: x.confidence, reverse=True)
                if not c.detected and c.confidence > 0
            ][:10],
        },
        "pathways_top20": pathways,
        "diagnostic_markers": markers,
        "hydrogenases": hydro,
        "recommended_action": {
            "action": profile.recommended_action,
            "rationale": profile.escalation_rationale or "Proceed with recipe synthesis",
            "modes": [m["mode"] for m in profile.cultivation_modes],
        },
    }

    # Phase 2c: include composed recipe in JSON output
    recipe_obj = None
    try:
        from compose_recipe import compose_recipe
        from dataclasses import asdict
        recipe_obj = compose_recipe(gid, conn, overrides=overrides)
        recipe_dict = asdict(recipe_obj)
        # Convert IngredientCategory enums to their string values
        for ing in recipe_dict.get("ingredients", []):
            cat = ing.get("category")
            if hasattr(cat, "value"):
                ing["category"] = cat.value
            elif isinstance(cat, dict) and "_value_" in cat:
                ing["category"] = cat["_value_"]
        result["recipe"] = recipe_dict
    except Exception as e:
        result["recipe"] = {"error": str(e)}

    # Phase 2d: published media comparison as a top-level field (Phase 2e Task 2)
    try:
        if recipe_obj is not None:
            result["published_media_comparison"] = _build_comparison_json(
                conn, gid, recipe_obj, species
            )
        else:
            result["published_media_comparison"] = {"error": "recipe composition failed"}
    except Exception as e:
        result["published_media_comparison"] = {"error": str(e)}

    # Phase 3.1: surface user-supplied overrides at the top level for downstream tools
    if overrides:
        result["user_overrides"] = dict(overrides)

    return result


def _build_comparison_json(conn, gid: int, recipe, species: str) -> dict:
    """Phase 2d comparison data as a JSON-serializable dict.

    Mirrors the data-acquisition logic of `_section_published_media` but
    returns structured data instead of formatted text. Top-level shape:
      - relationship: "direct" | "functional_neighbor" | "no_match"
      - matched_organism / functional_neighbors: provenance
      - report: ComparisonReport asdict (or null when no_match)
    """
    from dataclasses import asdict
    from recipe_comparison import compare_recipes
    from capability_vector import find_functional_neighbors

    direct_media = [r[0] for r in conn.execute(
        "SELECT DISTINCT medium_id FROM organism_to_published_media "
        "WHERE cultureforge_genome_id = ? AND relationship = 'direct'",
        (gid,)
    ).fetchall()]

    if direct_media:
        bd_count = conn.execute(
            "SELECT COUNT(*) FROM organism_to_bacdive WHERE cultureforge_genome_id = ?",
            (gid,)
        ).fetchone()[0]
        report = compare_recipes(recipe, direct_media, conn,
                                  relationship="direct", genome_id=gid, species=species)
        return {
            "relationship": "direct",
            "matched_species": species,
            "n_bacdive_strains": bd_count,
            "n_reference_media": len(direct_media),
            "reference_medium_ids": sorted(direct_media),
            "functional_neighbors": [],
            "report": asdict(report),
        }

    nbrs = find_functional_neighbors(gid, conn, top_n=5, min_similarity=0.30)
    if not nbrs:
        return {
            "relationship": "no_match",
            "matched_species": species,
            "n_reference_media": 0,
            "reference_medium_ids": [],
            "functional_neighbors": [],
            "report": None,
        }

    all_neighbor_media: list = []
    nbr_payload = []
    for ngid, ns, sim, media in nbrs:
        nbr_payload.append({
            "neighbor_genome_id": ngid,
            "neighbor_species": ns,
            "similarity": sim,
            "neighbor_published_media": media,
        })
        all_neighbor_media.extend(media)
    seen: set = set()
    aggregated = [m for m in all_neighbor_media if not (m in seen or seen.add(m))]
    report = compare_recipes(recipe, aggregated, conn,
                              relationship="functional_neighbor",
                              genome_id=gid, species=species)
    report.matched_published_ids = aggregated
    return {
        "relationship": "functional_neighbor",
        "matched_species": species,
        "n_reference_media": len(aggregated),
        "reference_medium_ids": aggregated,
        "functional_neighbors": nbr_payload,
        "report": asdict(report),
    }


# ---------------------------------------------------------------------------
# List subcommand
# ---------------------------------------------------------------------------

def _cmd_list(conn, sort_by="id"):
    """List all genomes in the database.

    CheckM completeness is shown only for genomes that have it (a small
    minority \u2014 most validation/blind genomes never had CheckM run). The
    "QC%" column shows a value when present, blank otherwise. Run
    `inspect <id> --section quality` for the per-genome detail.
    """
    order = {"id": "g.id", "species": "species", "accession": "g.accession",
             "completeness": "gq.completeness DESC"}
    order_clause = order.get(sort_by, "g.id")

    rows = conn.execute(f"""
        SELECT g.id, g.accession, COALESCE(o.species, g.notes, '') as species,
               gq.completeness, gq.genome_size
        FROM genomes g
        LEFT JOIN organisms o ON o.id = g.organism_id
        LEFT JOIN genome_quality gq ON gq.genome_id = g.id
        ORDER BY {order_clause}
    """).fetchall()

    # Compute species column width to fit the longest cleaned name
    cleaned_species = []
    for gid, acc, species, comp, size in rows:
        sp = species or ""
        sp = sp.replace("Blind validation: ", "").replace("Blind v2: ", "").replace("Validation organism: ", "")
        sp = sp.replace("_", " ")
        cleaned_species.append(sp)
    sp_width = max([len(s) for s in cleaned_species] + [13])  # "Species/Notes" is 13

    n_with_qc = sum(1 for _, _, _, comp, _ in rows if comp is not None)
    qc_header = f"QC% (n={n_with_qc})" if n_with_qc < len(rows) else "QC%"

    line_len = 4 + 2 + 22 + 1 + sp_width + 1 + len(qc_header) + 1 + 10
    print(f"{'ID':>4s}  {'Accession':<22s} {'Species/Notes':<{sp_width}s} {qc_header:>{len(qc_header)}s} {'Size':>10s}")
    print("\u2500" * line_len)
    for (gid, acc, _, comp, size), sp in zip(rows, cleaned_species):
        comp_str = f"{comp:.0f}%" if comp else ""
        size_str = f"{size/1e6:.1f} Mb" if size else "n/a"
        print(f"{gid:4d}  {acc:<22s} {sp:<{sp_width}s} {comp_str:>{len(qc_header)}s} {size_str:>10s}")
    print("\u2500" * line_len)
    print(f"Total: {len(rows)} genomes  ({n_with_qc} with CheckM completeness)")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _short_cap_name(name):
    """Shorten a capability name for display."""
    # Strip the long description that follows the pathway name
    name = re.sub(r"\. Negative markers?:.*", "", name)
    name = re.sub(r" \(mixed products\)", "", name)
    name = re.sub(r" \(composite signature\)", "", name)
    name = re.sub(r" via extracellular electron transfer", "", name)
    name = re.sub(r" \(nitrification step 1\)", "", name)
    name = re.sub(r" via electron transport chain", " (ETC pathway)", name)
    name = re.sub(r" \(hydrogenotrophic, aceticlastic, or methylotrophic\)", "", name)
    name = re.sub(r"Substrate-level phosphorylation fermentation", "Fermentation", name)
    name = re.sub(r"Sulfur/sulfide/thiosulfate oxidation", "Sulfur oxidation", name)
    name = re.sub(r"Bacteriorhodopsin/proteorhodopsin light-driven proton pump",
                  "Bacteriorhodopsin", name)
    name = re.sub(r"Anaerobic ammonium oxidation.*", "Anammox", name)
    name = re.sub(r"Reductive dehalogenation of organohalide compounds.*",
                  "Organohalide respiration", name)
    name = re.sub(r"Extreme salt-in halophily", "Salt-in halophily", name)
    name = re.sub(r"Biological nitrogen fixation \(N2 to NH3\)", "Nitrogen fixation", name)
    name = re.sub(r"Anoxygenic phototrophy \(purple bacteria, Type II.*\)",
                  "Purple phototrophy", name)
    name = re.sub(r"Anoxygenic phototrophy \(green sulfur.*\)", "Green sulfur phototrophy", name)
    name = re.sub(r"Oxygenic phototrophy \(cyanobacteria.*\)", "Oxygenic phototrophy", name)
    name = re.sub(r"Dissimilatory Fe\(III\) reduction", "Iron(III) reduction", name)
    name = re.sub(r"Acidophilic Fe\(II\) oxidation", "Iron(II) oxidation (acidophilic)", name)
    name = re.sub(r"Acetogenesis via Wood-Ljungdahl pathway", "Acetogenesis (Wood-Ljungdahl)", name)
    return name[:50]


def _human_reject_reason(cap):
    """Produce a human-readable rejection reason for a capability."""
    if cap.negative_markers_present:
        return f"Negative marker: {', '.join(cap.negative_markers_present)}"
    for flag in cap.uncertainty_flags:
        if "autotrophy_disqualifier" in flag:
            return "Autotrophy detected; glycolytic genes are anabolic, not catabolic"
        if "acceptor_disqualifier" in flag:
            return "Strong respiratory metabolism detected; fermentation is secondary"
        if "syntrophy_disqualifier" in flag:
            return "Syntrophy detected; beta-oxidation is syntrophic, not fermentative"
        if "iron_reduction_disqualifier" in flag:
            return "Iron reduction detected; acetate oxidation is respiratory, not fermentative"
        if "anaerobe_disqualifier" in flag:
            return "Obligate anaerobe signals; cytochrome hits are non-respiratory"
    for ev in cap.evidence_summary:
        if "capped" in ev.lower() or "suppressed" in ev.lower():
            return ev[:75]
    if cap.pathway_completeness < 0.30:
        return f"Pathway score too low ({cap.pathway_completeness:.2f})"
    return f"Below threshold (pathway {cap.pathway_completeness:.2f})"


def _section_recipe_context(conn, gid, overrides=None):
    """Section 9: Recipe Context."""
    sys.path.insert(0, str(_ROOT))
    from derive_recipe_context import derive_recipe_context

    ctx = derive_recipe_context(gid, conn, overrides=overrides)
    lines = ["\nRECIPE CONTEXT (Section 9)", "\u2500" * 70]

    # Atmosphere
    lines.append("\nATMOSPHERE")
    atm = ctx.primary_atmosphere.value if ctx.primary_atmosphere else "unknown"
    lines.append(f"  Primary:        {atm}")
    if ctx.alternative_atmospheres:
        lines.append(f"  Alternatives:   {', '.join(a.value for a in ctx.alternative_atmospheres)}")
    if ctx.gas_requirements:
        lines.append(f"  Gas needs:      {', '.join(ctx.gas_requirements)}")

    # Carbon sources
    if ctx.carbon_sources:
        lines.append("\nCARBON SOURCES")
        for cs in ctx.carbon_sources:
            lines.append(f"  {cs.name:<25s} type={cs.type:<15s} conf {cs.confidence:.2f}")
            for ev in cs.evidence[:2]:
                lines.append(f"    {ev}")

    # Electron donors
    if ctx.electron_donors:
        lines.append("\nELECTRON DONORS")
        for ed in ctx.electron_donors:
            lines.append(f"  {ed.name:<25s} conf {ed.confidence:.2f}  ({ed.derived_from_capability or ''})")

    # Electron acceptors
    if ctx.electron_acceptors:
        lines.append("\nELECTRON ACCEPTORS")
        for ea in ctx.electron_acceptors:
            lines.append(f"  {ea.name:<30s} conf {ea.confidence:.2f}  ({ea.derived_from_capability or ''})")

    # Nitrogen sources
    if ctx.nitrogen_sources:
        lines.append("\nNITROGEN SOURCES")
        for ns in ctx.nitrogen_sources:
            lines.append(f"  {ns.name:<45s} conf {ns.confidence:.2f}")
            for ev in ns.evidence[:1]:
                lines.append(f"    {ev}")

    # Trace metals
    if ctx.trace_metals:
        lines.append("\nTRACE METALS")
        for tm in ctx.trace_metals[:8]:
            lines.append(f"  {tm.element:<5s} {tm.importance:<12s} {tm.evidence[0] if tm.evidence else ''}")

    # Cofactors
    if ctx.cofactors:
        lines.append("\nCOFACTORS")
        for cf in ctx.cofactors:
            status = "synthesizes" if cf.can_synthesize else "needs supplementation"
            lines.append(f"  {cf.name:<25s} {status:<25s} ({cf.completeness:.0f}% pathway)")

    # Growth conditions
    if ctx.conditions:
        lines.append("\nGROWTH CONDITIONS")
        c = ctx.conditions
        if c.temperature_optimum_c:
            rng = f" (range {c.temperature_range_c[0]:.0f}-{c.temperature_range_c[1]:.0f}\u00b0C)" if c.temperature_range_c else ""
            lines.append(f"  Temperature:    {c.temperature_optimum_c:.0f}\u00b0C optimum{rng}  (source: {c.source})")
        if c.ph_optimum:
            rng = f" (range {c.ph_range[0]:.1f}-{c.ph_range[1]:.1f})" if c.ph_range else ""
            lines.append(f"  pH:             {c.ph_optimum:.1f} optimum{rng}")
        if c.salinity_category:
            lines.append(f"  Salinity:       {c.salinity_category}")

    # Special requirements
    if ctx.special_requirements:
        lines.append("\nSPECIAL REQUIREMENTS")
        for sr in ctx.special_requirements:
            lines.append(f"  - {sr.requirement}: {sr.description[:75]}")

    # Incompleteness flags
    if ctx.incompleteness_flags:
        lines.append("\nINCOMPLETENESS FLAGS")
        for flag in ctx.incompleteness_flags:
            lines.append(f"  ! {flag}")

    lines.append(f"\nOVERALL CONFIDENCE: {ctx.overall_confidence:.2f}")
    lines.append("\u2500" * 70)
    return "\n".join(lines)


def _section_recipe(conn, gid, overrides=None):
    """Section 10: Recipe (Phase 2c — composed cultivation medium)."""
    sys.path.insert(0, str(_ROOT))
    from compose_recipe import compose_recipe

    r = compose_recipe(gid, conn, overrides=overrides)
    lines = ["\nRECIPE (Section 10)", "─" * 70]

    if r.escalated:
        lines.append("")
        lines.append("ESCALATED — no recipe composed")
        lines.append(f"  Reason: {r.escalation_reason}")
        lines.append(f"  Overall confidence: {r.overall_confidence:.2f}")
        lines.append("─" * 70)
        return "\n".join(lines)

    # Header
    conf_label = "high" if r.overall_confidence >= 0.75 else (
        "medium" if r.overall_confidence >= 0.55 else "low")
    lines.append("")
    lines.append(f"PRIMARY CULTIVATION MODE: {r.primary_cultivation_mode}")
    if r.alternative_cultivation_modes:
        lines.append(f"ALTERNATIVE MODES (also detected): {', '.join(r.alternative_cultivation_modes)}")
    else:
        lines.append("ALTERNATIVE MODES (also detected): none")
    # Phase 3.1: surface any user-supplied overrides prominently
    if overrides:
        ov_parts = []
        if "temperature" in overrides:
            ov_parts.append(f"temperature={overrides['temperature']:g}°C")
        if "ph" in overrides:
            ov_parts.append(f"pH={overrides['ph']:g}")
        if "salinity" in overrides:
            ov_parts.append(f"salinity={overrides['salinity']:g} g/L")
        lines.append(f"USER OVERRIDES APPLIED: {', '.join(ov_parts)}")

    # Gas phase
    if r.gas_phase:
        lines.append("")
        lines.append("GAS PHASE")
        for sp, frac in r.gas_phase.composition.items():
            lines.append(f"  {sp+':':<6s} {frac*100:.0f}%")
        lines.append(f"  Pressure: {r.gas_phase.pressure_atm:.1f} atm")
        if r.gas_phase.rationale:
            for line in _wrap(r.gas_phase.rationale, 65, indent="    "):
                lines.append(line)

    # Conditions
    if r.conditions:
        lines.append("")
        lines.append("INCUBATION CONDITIONS")
        lines.append(f"  Temperature: {r.conditions.temperature_c:.1f}°C")
        lines.append(f"  pH:          {r.conditions.ph:.1f}")
        lines.append(f"  Light:       {'required' if r.conditions.light_required else 'not required'}"
                     + (f"  ({r.conditions.light_intensity_umol_per_m2_per_s:.0f} µmol/m²/s)"
                        if r.conditions.light_intensity_umol_per_m2_per_s else ""))
        lines.append(f"  Shaking:     {f'{r.conditions.shaking_rpm} rpm' if r.conditions.shaking_rpm else 'static'}")
        if r.conditions.rationale:
            for line in _wrap(r.conditions.rationale, 65, indent="    "):
                lines.append(line)

    # Ingredients grouped by category
    lines.append("")
    lines.append("INGREDIENTS")
    by_cat: dict = {}
    for ing in r.ingredients:
        by_cat.setdefault(ing.category.value, []).append(ing)
    cat_order = ["buffer", "salt", "carbon_source", "nitrogen_source",
                 "electron_donor", "electron_acceptor", "reducing_agent",
                 "supplement", "trace_metal", "vitamin", "gas_phase",
                 "sulfur_source", "phosphorus_source"]
    seen_cats = set()
    for cat in cat_order:
        if cat not in by_cat:
            continue
        seen_cats.add(cat)
        lines.append(f"  {cat.replace('_', ' ').title()}:")
        for ing in by_cat[cat]:
            unit = ing.concentration_unit
            if isinstance(ing.concentration, float) and ing.concentration > 0:
                conc_str = f"{ing.concentration:>8.3g} {unit}"
            else:
                conc_str = f"{unit}"
            lines.append(f"    {ing.name[:42]:<42s} {conc_str}")
            for w in _wrap(ing.rationale, 60, indent="      "):
                lines.append(w)
            if ing.confidence < 0.95:
                lines.append(f"      (confidence {ing.confidence:.2f})")
    # Any categories not in cat_order
    for cat, items in by_cat.items():
        if cat in seen_cats:
            continue
        lines.append(f"  {cat.replace('_', ' ').title()}:")
        for ing in items:
            lines.append(f"    {ing.name[:42]:<42s} {ing.concentration} {ing.concentration_unit}")

    # Thermodynamic check
    if r.thermodynamic_checks:
        lines.append("")
        lines.append("THERMODYNAMIC CHECK")
        for tc in r.thermodynamic_checks:
            lines.append(f"  Reaction: {tc.primary_reaction}")
            lines.append(f"  ΔG (standard, default activities): {tc.delta_g_kj_per_mol:+.1f} kJ/mol")
            lines.append(f"  Feasibility: {tc.feasibility_class} ({'feasible' if tc.feasible else 'INFEASIBLE'})")
            if tc.notes:
                for w in _wrap(tc.notes, 65, indent="    "):
                    lines.append(w)

    # Uncertainty flags
    lines.append("")
    if r.uncertainty_flags:
        lines.append("UNCERTAINTY FLAGS")
        for f in r.uncertainty_flags:
            for w in _wrap(f"- {f}", 67, indent="    "):
                lines.append(w if w.lstrip().startswith('-') else "  " + w)
    else:
        lines.append("UNCERTAINTY FLAGS")
        lines.append("  None significant for this recipe.")

    # Limitations
    if r.limitations_referenced:
        lines.append("")
        lines.append(f"LIMITATIONS REFERENCED: {', '.join(r.limitations_referenced)}")
        lines.append("  See LIMITATIONS.md for details on each category.")

    # Confidence
    lines.append("")
    lines.append(f"OVERALL CONFIDENCE: {r.overall_confidence:.2f} ({conf_label})")
    if r.confidence_rationale:
        for w in _wrap(f"RATIONALE: {r.confidence_rationale}", 65, indent="    "):
            lines.append(w if w.lstrip().startswith('R') else "  " + w)

    lines.append("─" * 70)
    return "\n".join(lines)


def _wrap(text: str, width: int, indent: str = "  ") -> list:
    """Word-wrap helper for inspector output."""
    if not text:
        return []
    words = text.split()
    lines, cur = [], indent
    for w in words:
        if len(cur) + len(w) + 1 > width and cur != indent:
            lines.append(cur)
            cur = indent + w
        else:
            cur = cur + (" " if cur != indent else "") + w
    if cur != indent:
        lines.append(cur)
    return lines


def _section_published_media(conn, gid, overrides=None):
    """Section 11: Published Media Comparison (Phase 2d)."""
    sys.path.insert(0, str(_ROOT))
    from compose_recipe import compose_recipe
    from recipe_comparison import compare_recipes
    from capability_vector import find_functional_neighbors

    recipe = compose_recipe(gid, conn, overrides=overrides)
    sp_row = conn.execute(
        "SELECT COALESCE(o.species, g.notes, g.accession) FROM genomes g "
        "LEFT JOIN organisms o ON o.id = g.organism_id WHERE g.id = ?",
        (gid,)
    ).fetchone()
    species = (sp_row[0] or "?").replace("Validation organism: ", "") \
        .replace("Blind validation: ", "").replace("Blind v2: ", "").replace("_", " ")

    lines = ["\nPUBLISHED MEDIA COMPARISON (Section 11)", "─" * 70]

    # Direct matches via BacDive
    direct_media = [r[0] for r in conn.execute(
        "SELECT DISTINCT medium_id FROM organism_to_published_media "
        "WHERE cultureforge_genome_id = ? AND relationship = 'direct'",
        (gid,)
    ).fetchall()]

    if direct_media:
        bd_count = conn.execute(
            "SELECT COUNT(*) FROM organism_to_bacdive WHERE cultureforge_genome_id = ?",
            (gid,)
        ).fetchone()[0]
        lines.append("")
        lines.append(f"DIRECT MATCH: {species} ({bd_count} BacDive strain(s))")
        lines.append(f"  Reference media: {len(direct_media)} ({', '.join(sorted(direct_media)[:6])}{'...' if len(direct_media) > 6 else ''})")
        report = compare_recipes(recipe, direct_media, conn,
                                  relationship="direct",
                                  genome_id=gid, species=species)
        lines.extend(_format_comparison_report(report))
        lines.append("")
        lines.append("─" * 70)
        return "\n".join(lines)

    # No direct match — look up functional neighbors
    lines.append("")
    lines.append(f"NO DIRECT MATCH in BacDive for {species}.")
    lines.append("")
    lines.append("FUNCTIONAL NEIGHBORS (top 5 by CultureForge capability similarity):")
    nbrs = find_functional_neighbors(gid, conn, top_n=5, min_similarity=0.30)
    if not nbrs:
        lines.append("  (no functional neighbors found above similarity threshold)")
        lines.append("")
        lines.append("─" * 70)
        return "\n".join(lines)
    all_neighbor_media: list = []
    for ngid, ns, sim, media in nbrs:
        lines.append(f"  - {ns:42s} (gid={ngid:2d}, sim={sim:.3f})")
        lines.append(f"      → published media: {', '.join(media[:6])}")
        all_neighbor_media.extend(media)
    # Deduplicate while preserving order
    seen: set = set()
    aggregated = [m for m in all_neighbor_media if not (m in seen or seen.add(m))]
    if aggregated:
        report = compare_recipes(recipe, aggregated, conn,
                                  relationship="functional_neighbor",
                                  genome_id=gid, species=species)
        report.matched_published_ids = aggregated
        lines.extend(_format_comparison_report(report))

    lines.append("")
    lines.append("NOTE: This organism doesn't have a direct BacDive entry. "
                 "Comparison is against media from functionally similar organisms.")
    lines.append("─" * 70)
    return "\n".join(lines)


def _format_comparison_report(report) -> list:
    lines = []
    lines.append("")
    lines.append("INGREDIENT-LEVEL COMPARISON")
    by_severity = {"critical": [], "important": [], "minor": []}
    shared_n = sum(1 for d in report.diffs if d.kind == "shared")
    for d in report.diffs:
        by_severity[d.severity].append(d)
    # The compare function doesn't add "shared" to diffs — so derive from agreement counts
    n_total_diffs = sum(len(v) for v in by_severity.values())
    lines.append(f"  Diffs: {len(by_severity['critical'])} critical / "
                 f"{len(by_severity['important'])} important / "
                 f"{len(by_severity['minor'])} minor "
                 f"(across {report.n_published_media} reference media)")
    if by_severity["critical"]:
        lines.append("")
        lines.append("  CRITICAL DIFFERENCES (different acceptor/donor/atmosphere):")
        for d in by_severity["critical"]:
            lines.append(f"    ! {d.kind:18s} {d.ingredient[:30]:30s}  {d.note[:75]}")
    if by_severity["important"]:
        lines.append("")
        lines.append("  IMPORTANT DIFFERENCES (carbon/nitrogen/buffer/reducing):")
        for d in by_severity["important"]:
            lines.append(f"    ⚠ {d.kind:18s} {d.ingredient[:30]:30s}  {d.note[:75]}")
    if by_severity["minor"]:
        lines.append("")
        lines.append(f"  MINOR DIFFERENCES (concentrations / trace components, "
                     f"showing top 8 of {len(by_severity['minor'])}):")
        for d in by_severity["minor"][:8]:
            lines.append(f"    · {d.kind:18s} {d.ingredient[:30]:30s}  {d.note[:75]}")
    lines.append("")
    pct = report.overall_agreement * 100
    label = ("high" if pct >= 75 else "medium-high" if pct >= 60 else
             "moderate" if pct >= 40 else "low")
    lines.append(f"OVERALL AGREEMENT: {pct:.0f}% ({label})")
    if report.rationale:
        lines.append(f"  RATIONALE: {report.rationale}")
    return lines


SECTION_RENDERERS = {
    "quality": _section_quality,
    "predictions": _section_predictions,
    "capabilities": _section_capabilities,
    "pathways": _section_pathways,
    "markers": _section_markers,
    "hydrogenases": _section_hydrogenases,
    "action": _section_action,
    "recipe-context": _section_recipe_context,
    "recipe": _section_recipe,
    "published-media": _section_published_media,
}


def main():
    parser = argparse.ArgumentParser(
        prog="cultureforge",
        description="CultureForge genome inspection and analysis tool",
    )
    sub = parser.add_subparsers(dest="command")

    # inspect subcommand
    inspect_p = sub.add_parser("inspect", help="Inspect a genome's data and capability profile")
    inspect_p.add_argument("identifier", nargs="?", help="Genome ID, accession, or species name")
    inspect_p.add_argument("--list", action="store_true", help="List all genomes in database")
    inspect_p.add_argument("--section", action="append",
                           choices=["quality", "predictions", "capabilities", "pathways",
                                    "markers", "hydrogenases", "action", "recipe-context",
                                    "recipe", "published-media"],
                           help="Limit output to specific section(s)")
    inspect_p.add_argument("--json", action="store_true", help="Output as JSON")
    inspect_p.add_argument("--output", help="Write output to file")
    inspect_p.add_argument("--sort-by", default="id",
                           choices=["id", "species", "accession", "completeness"],
                           help="Sort order for --list")
    inspect_p.add_argument("--db", default=DB_DEFAULT, help="Database path")
    # Phase 3.1: manual cultivation-condition overrides
    inspect_p.add_argument("--temperature", type=float, default=None,
                           help="Override cultivation temperature in °C (range 0-130)")
    inspect_p.add_argument("--ph", type=float, default=None,
                           help="Override cultivation pH (range 0-14)")
    inspect_p.add_argument("--salinity", type=float, default=None,
                           help="Override cultivation salinity in g/L NaCl (range 0-400)")

    args = parser.parse_args()

    # Validate Phase 3.1 overrides at parse time, before any DB queries
    if args.command == "inspect":
        if args.temperature is not None and not 0 <= args.temperature <= 130:
            print(f"Error: --temperature value {args.temperature} is outside "
                  f"acceptable range (0-130°C). Hyperthermophiles cap around "
                  f"122°C (Methanopyrus kandleri).", file=sys.stderr)
            sys.exit(1)
        if args.ph is not None and not 0 <= args.ph <= 14:
            print(f"Error: --ph value {args.ph} is outside acceptable range "
                  f"(0-14).", file=sys.stderr)
            sys.exit(1)
        if args.salinity is not None and not 0 <= args.salinity <= 400:
            if args.salinity < 0:
                print(f"Error: --salinity value {args.salinity} cannot be "
                      f"negative.", file=sys.stderr)
            else:
                print(f"Error: --salinity value {args.salinity} is outside "
                      f"acceptable range (0-400 g/L NaCl).", file=sys.stderr)
            sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = sqlite3.connect(args.db)

    if args.command == "inspect":
        if args.list:
            _cmd_list(conn, sort_by=args.sort_by)
            conn.close()
            return

        if not args.identifier:
            print("Error: specify a genome identifier or use --list")
            sys.exit(1)

        resolved = _resolve_genome(conn, args.identifier)
        if not resolved:
            print(f"No genome found matching '{args.identifier}'.")
            print("Use `cultureforge inspect --list` to see available genomes.")
            sys.exit(1)

        gid, accession, species = resolved

        # Phase 3.1: collect overrides into a dict; only non-None entries kept
        overrides = {}
        if args.temperature is not None:
            overrides["temperature"] = args.temperature
        if args.ph is not None:
            overrides["ph"] = args.ph
        if args.salinity is not None:
            overrides["salinity"] = args.salinity

        if args.json:
            result = _build_json(conn, gid, accession, species, overrides=overrides or None)
            output = json.dumps(result, indent=2, default=str)
        else:
            sections_to_render = args.section or list(SECTION_RENDERERS.keys())
            parts = [_section_header(conn, gid, accession, species)]
            for sec_name in sections_to_render:
                renderer = SECTION_RENDERERS.get(sec_name)
                if renderer:
                    if sec_name in ("recipe-context", "recipe", "published-media"):
                        parts.append(renderer(conn, gid, overrides=overrides or None))
                    else:
                        parts.append(renderer(conn, gid))
            output = "\n".join(parts)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Report written to {args.output}")
        else:
            print(output)

    conn.close()


if __name__ == "__main__":
    main()
