"""Run CheckM2 (or CheckM1 fallback) on a genome FASTA and return quality metrics.

Usage:
    python run_checkm.py <genome.fasta> [--output-dir <dir>]

Returns a dict with: completeness, contamination, strain_heterogeneity,
genome_size, gc_content, n50, checkm_version.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _fasta_stats(fasta_path: str) -> dict:
    """Compute genome size, GC content, and N50 from a FASTA file."""
    lengths = []
    gc = 0
    total = 0
    current_len = 0

    with open(fasta_path) as f:
        for line in f:
            if line.startswith(">"):
                if current_len > 0:
                    lengths.append(current_len)
                current_len = 0
            else:
                seq = line.strip().upper()
                current_len += len(seq)
                total += len(seq)
                gc += seq.count("G") + seq.count("C")
    if current_len > 0:
        lengths.append(current_len)

    # N50
    lengths.sort(reverse=True)
    cumsum = 0
    n50 = 0
    for ln in lengths:
        cumsum += ln
        if cumsum >= total / 2:
            n50 = ln
            break

    return {
        "genome_size": total,
        "gc_content": round(gc / total, 4) if total > 0 else 0.0,
        "n50": n50,
        "n_contigs": len(lengths),
    }


def run_checkm2(fasta_path: str, output_dir: str = None) -> dict:
    """Run CheckM2 and parse results.  Falls back to CheckM1 if unavailable."""
    fasta_path = os.path.abspath(fasta_path)
    stats = _fasta_stats(fasta_path)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="checkm_")
        cleanup = True
    else:
        os.makedirs(output_dir, exist_ok=True)
        cleanup = False

    result = {
        "completeness": None,
        "contamination": None,
        "strain_heterogeneity": None,
        "checkm_version": None,
        **stats,
    }

    # Try CheckM2 first
    checkm2_bin = shutil.which("checkm2")
    if checkm2_bin is None:
        # Try via conda
        try:
            proc = subprocess.run(
                ["conda", "run", "-n", "checkm2", "which", "checkm2"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                checkm2_bin = "conda run -n checkm2 checkm2"
        except Exception:
            pass

    if checkm2_bin:
        try:
            # Create a tmp input dir with symlink (CheckM2 expects a directory)
            input_dir = os.path.join(output_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            link_path = os.path.join(input_dir, os.path.basename(fasta_path))
            if not os.path.exists(link_path):
                os.symlink(fasta_path, link_path)

            cmd = f"{checkm2_bin} predict --input {input_dir} --output_directory {output_dir} --force"
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=3600,
            )

            # Parse quality_report.tsv
            report = os.path.join(output_dir, "quality_report.tsv")
            if os.path.exists(report):
                with open(report) as f:
                    header = f.readline().strip().split("\t")
                    values = f.readline().strip().split("\t")
                    row = dict(zip(header, values))
                    result["completeness"] = float(row.get("Completeness", 0))
                    result["contamination"] = float(row.get("Contamination", 0))
                    result["checkm_version"] = "CheckM2"
                    return result
        except Exception as e:
            print(f"CheckM2 failed: {e}", file=sys.stderr)

    # Fallback: CheckM1
    checkm1_bin = shutil.which("checkm")
    if checkm1_bin is None:
        try:
            proc = subprocess.run(
                ["conda", "run", "-n", "checkm", "which", "checkm"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                checkm1_bin = "conda run -n checkm checkm"
        except Exception:
            pass

    if checkm1_bin:
        try:
            input_dir = os.path.join(output_dir, "input")
            os.makedirs(input_dir, exist_ok=True)
            link_path = os.path.join(input_dir, os.path.basename(fasta_path))
            if not os.path.exists(link_path):
                os.symlink(fasta_path, link_path)

            results_dir = os.path.join(output_dir, "checkm1_out")
            cmd = (f"{checkm1_bin} lineage_wf {input_dir} {results_dir} "
                   f"-x fasta --tab_table -f {output_dir}/checkm1_results.tsv")
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=7200,
            )

            tsv_path = os.path.join(output_dir, "checkm1_results.tsv")
            if os.path.exists(tsv_path):
                with open(tsv_path) as f:
                    header = f.readline().strip().split("\t")
                    values = f.readline().strip().split("\t")
                    row = dict(zip(header, values))
                    result["completeness"] = float(row.get("Completeness", 0))
                    result["contamination"] = float(row.get("Contamination", 0))
                    result["strain_heterogeneity"] = float(
                        row.get("Strain heterogeneity", 0))
                    result["checkm_version"] = "CheckM1"
                    return result
        except Exception as e:
            print(f"CheckM1 failed: {e}", file=sys.stderr)

    # Neither CheckM available — return stats only with None for quality
    print("WARNING: Neither CheckM2 nor CheckM1 available. "
          "Genome quality assessment skipped. "
          "Install CheckM2: conda create -n checkm2 -c bioconda checkm2",
          file=sys.stderr)
    result["checkm_version"] = None
    return result

    if cleanup and os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Run CheckM on a genome FASTA")
    parser.add_argument("genome", help="Path to genome FASTA")
    parser.add_argument("--output-dir", default=None,
                        help="Directory for CheckM output (default: temp)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    result = run_checkm2(args.genome, args.output_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
