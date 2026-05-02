"""CultureForge Capability Report — human-readable one-page genome summary.

Produces a scannable report of a genome's metabolic capability profile,
designed for bench microbiologists to read in under a minute.

Usage:
    python capability_report.py --genome-id 8
    python capability_report.py --accession NC_000909.1
    python capability_report.py --species "Methanococcus jannaschii"
    python capability_report.py --genome-id 8 --json
    python capability_report.py --genome-id 8 --output report.txt
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent
DB_DEFAULT = str(_ROOT / "data" / "cultureforge.db")


def _find_genome_id(conn, args):
    """Resolve genome_id from various input types."""
    if args.genome_id:
        return args.genome_id
    if args.accession:
        row = conn.execute("SELECT id FROM genomes WHERE accession = ?",
                           (args.accession,)).fetchone()
        if row:
            return row[0]
        print(f"No genome found for accession '{args.accession}'", file=sys.stderr)
        sys.exit(1)
    if args.species:
        row = conn.execute("""
            SELECT g.id FROM genomes g
            LEFT JOIN organisms o ON o.id = g.organism_id
            WHERE lower(o.species) LIKE ?
            LIMIT 1
        """, (f"%{args.species.lower()}%",)).fetchone()
        if row:
            return row[0]
        # Try matching the notes field
        row = conn.execute("SELECT id FROM genomes WHERE lower(notes) LIKE ? LIMIT 1",
                           (f"%{args.species.lower()}%",)).fetchone()
        if row:
            return row[0]
        print(f"No genome found for species '{args.species}'", file=sys.stderr)
        sys.exit(1)
    print("Specify --genome-id, --accession, or --species", file=sys.stderr)
    sys.exit(1)


def _get_genomespot(conn, genome_id):
    """Get GenomeSPOT predictions if available."""
    try:
        rows = conn.execute("""
            SELECT target, value, numeric_value
            FROM genome_growth_predictions WHERE genome_id = ?
        """, (genome_id,)).fetchall()
        preds = {}
        for target, value, num in rows:
            t = target.lower()
            if "temperature" in t and "optimum" in t:
                preds["temperature"] = f"{num:.1f} C" if num else value
            elif "ph" in t and "optimum" in t:
                preds["pH"] = f"{num:.1f}" if num else value
            elif "salinity" in t:
                preds["salinity"] = f"{num:.1f}%" if num else value
            elif "oxygen" in t:
                preds["oxygen"] = value
        return preds
    except Exception:
        return {}


def generate_report(genome_id, conn):
    """Generate the full capability report for a genome."""
    # Import here to avoid circular imports at module level
    sys.path.insert(0, str(_ROOT))
    from capability_detectors import profile_capabilities

    # Basic genome info
    row = conn.execute("""
        SELECT g.accession, g.length_bp, g.biomass_template, g.notes,
               o.species
        FROM genomes g
        LEFT JOIN organisms o ON o.id = g.organism_id
        WHERE g.id = ?
    """, (genome_id,)).fetchone()

    if not row:
        return f"ERROR: genome_id {genome_id} not found in database"

    accession, length_bp, biomass, notes, species = row
    organism_name = species or (notes or "").replace("Blind validation: ", "").replace("Validation organism: ", "")

    # Quality data
    qc_row = conn.execute("""
        SELECT completeness, contamination, genome_size, gc_content, n50,
               acidic_residue_fraction, checkm_version
        FROM genome_quality WHERE genome_id = ?
    """, (genome_id,)).fetchone()

    # GenomeSPOT
    gs_preds = _get_genomespot(conn, genome_id)

    # Run capability detection
    profile = profile_capabilities(genome_id, conn)

    # Build report
    lines = []
    bar = "=" * 65
    thin = "-" * 65

    lines.append(bar)
    lines.append("CultureForge Capability Report")
    lines.append(f"Organism: {organism_name}")
    lines.append(f"Genome: {accession}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Genome quality
    lines.append("GENOME QUALITY")
    lines.append(thin)
    if qc_row:
        comp, contam, gsize, gc, n50, acidic, checkm_v = qc_row
        if comp is not None:
            lines.append(f"CheckM completeness: {comp:.1f}%")
            lines.append(f"CheckM contamination: {contam:.1f}%")
        else:
            lines.append("CheckM: not available (genome stats only)")
        if gsize:
            lines.append(f"Genome size: {gsize:,} bp")
        if gc:
            lines.append(f"GC content: {gc:.1%}")
        if n50:
            lines.append(f"N50: {n50:,}")
        if acidic is not None:
            lines.append(f"Acidic residue fraction (D+E): {acidic:.4f}")
    lines.append(f"Quality verdict: {profile.quality_verdict.verdict}")
    if gs_preds:
        gs_str = ", ".join(f"{k} {v}" for k, v in gs_preds.items())
        lines.append(f"GenomeSPOT predictions: {gs_str}")
    lines.append("")

    # Primary capabilities
    primary = [c for c in profile.capabilities if c.detected and c.confidence >= 0.50]
    primary.sort(key=lambda c: c.confidence, reverse=True)

    if primary:
        lines.append(f"PRIMARY CAPABILITIES (detected, confidence >= 0.50)")
        lines.append(thin)
        for i, cap in enumerate(primary, 1):
            lines.append(f"{i}. {cap.name}")
            lines.append(f"   Confidence: {cap.confidence:.2f}")
            # Show key evidence
            for ev in cap.evidence_summary[:3]:
                lines.append(f"   - {ev}")
            if cap.diagnostic_markers_hit:
                lines.append(f"   Diagnostic markers: {', '.join(cap.diagnostic_markers_hit)}")
            if cap.uncertainty_flags:
                for uf in cap.uncertainty_flags[:2]:
                    lines.append(f"   ! {uf}")
            lines.append("")
    else:
        lines.append("PRIMARY CAPABILITIES: NONE DETECTED")
        lines.append(thin)
        lines.append(f"Action: {profile.recommended_action}")
        if profile.escalation_rationale:
            lines.append(f"Rationale: {profile.escalation_rationale}")
        lines.append("")

    # Secondary capabilities
    secondary = [c for c in profile.capabilities
                 if c.detected and 0.30 <= c.confidence < 0.50]
    secondary.sort(key=lambda c: c.confidence, reverse=True)

    if secondary:
        lines.append("SECONDARY CAPABILITIES (detected, confidence 0.30-0.50)")
        lines.append(thin)
        for cap in secondary:
            lines.append(f"- {cap.name}: {cap.confidence:.2f}")
            if cap.evidence_summary:
                lines.append(f"  {cap.evidence_summary[0]}")
        lines.append("")

    # Rejected capabilities (those considered but scored low)
    rejected = [c for c in profile.capabilities
                if not c.detected and c.confidence > 0.0]
    rejected.sort(key=lambda c: c.confidence, reverse=True)

    if rejected:
        lines.append("CONSIDERED AND REJECTED")
        lines.append(thin)
        for cap in rejected[:8]:
            reason = ""
            if cap.negative_markers_present:
                reason = f" (negative marker: {', '.join(cap.negative_markers_present)})"
            elif cap.confidence < 0.20:
                reason = " (pathway not detected)"
            else:
                reason = f" (below threshold, pathway score {cap.pathway_completeness:.2f})"
            lines.append(f"- {cap.name[:50]:50s} {cap.confidence:.3f}{reason}")
        lines.append("")

    # Uncertainty flags (aggregated)
    all_flags = []
    for cap in primary:
        for uf in cap.uncertainty_flags:
            all_flags.append(f"[{cap.name[:30]}] {uf}")
    if all_flags:
        lines.append("UNCERTAINTY FLAGS")
        lines.append(thin)
        for flag in all_flags[:5]:
            lines.append(f"- {flag}")
        lines.append("")

    # Recommended action
    lines.append("RECOMMENDED ACTION")
    lines.append(thin)
    if profile.recommended_action == "synthesize":
        primary_names = [c.name for c in primary[:3]]
        lines.append(f"Proceed to recipe synthesis with primary capabilities:")
        for pn in primary_names:
            lines.append(f"  - {pn}")
    elif profile.recommended_action == "escalate_tier2":
        lines.append("Escalate to Tier 2 structural analysis (ESMFold + Foldseek)")
        lines.append("No confident metabolic capabilities detected from genome alone")
    elif profile.recommended_action == "reject":
        lines.append("Genome quality too low for reliable analysis")
    else:
        lines.append(f"Action: {profile.recommended_action}")
    lines.append("")
    lines.append(bar)

    return "\n".join(lines)


def generate_json(genome_id, conn):
    """Generate machine-readable JSON output."""
    sys.path.insert(0, str(_ROOT))
    from capability_detectors import profile_capabilities

    profile = profile_capabilities(genome_id, conn)

    result = {
        "genome_id": genome_id,
        "quality": {
            "verdict": profile.quality_verdict.verdict,
            "completeness": profile.quality_verdict.completeness,
            "contamination": profile.quality_verdict.contamination,
        },
        "primary_metabolisms": profile.primary_metabolisms,
        "recommended_action": profile.recommended_action,
        "capabilities": [
            {
                "name": c.name,
                "detected": c.detected,
                "confidence": c.confidence,
                "pathway_completeness": c.pathway_completeness,
                "diagnostic_markers": c.diagnostic_markers_hit,
                "negative_markers_present": c.negative_markers_present,
                "uncertainty_flags": c.uncertainty_flags,
            }
            for c in sorted(profile.capabilities,
                            key=lambda x: x.confidence, reverse=True)
        ],
    }
    return json.dumps(result, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="CultureForge Capability Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--genome-id", type=int, help="Genome ID in database")
    group.add_argument("--accession", help="Genome accession (e.g., NC_000909.1)")
    group.add_argument("--species", help="Species name (partial match)")
    parser.add_argument("--db", default=DB_DEFAULT, help="Database path")
    parser.add_argument("--output", help="Write report to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    genome_id = _find_genome_id(conn, args)

    if args.json:
        report = generate_json(genome_id, conn)
    else:
        report = generate_report(genome_id, conn)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    conn.close()


if __name__ == "__main__":
    main()
