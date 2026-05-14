"""End-to-end pipeline for processing a new genome through CultureForge (Phase 4.1).

The user-facing entry point is `cultureforge.py process --input <genome.fna>`,
which calls into `process_genome()` here. This module orchestrates:

    1. Genome registration (gid >= 1000)
    2. prodigal — protein prediction from assembly
    3. gapseq — pathway / transporter annotation
    4. GenomeSPOT — environmental envelope prediction
    5. marker BLAST — diagnostic enzyme detection
    6. CheckM2 (optional) — genome completeness/contamination QC
    7. MeBiPred (optional) — per-protein metal binding prediction

Each stage's output goes to a per-accession output directory. Any failure
mid-pipeline triggers cleanup via `deregister_genome()`.

External tools that MUST be available:
    - prodigal       (apt: prodigal)
    - gapseq         (conda env named "gapseq" by convention)
    - GenomeSPOT     (vendored; runs via project Python)
    - blastp         (apt: ncbi-blast+)

External tools that are OPTIONAL:
    - checkm2        (conda env named "checkm2")
    - mymetal        (MeBiPred python package)

The wrapper finds conda environments via `conda env list` and locates the
relevant binaries inside them. If a required tool is missing, the wrapper
fails early with a clear error message naming what's missing and how to
install it. If an optional tool is missing, the wrapper logs a notice and
continues — the resulting recipe will use SL-10-baseline trace metals
instead of organism-specific predictions, etc.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from register_genome import (
    register_genome,
    deregister_genome,
    update_genome_metadata,
    USER_GID_MIN,
)
from loaders.gapseq_generic import load_gapseq_outputs
from loaders.genomespot_generic import load_genomespot_outputs
from loaders.marker_blast_generic import load_marker_blast_results
from loaders.mebipred_generic import load_mebipred_outputs

_ROOT = Path(__file__).resolve().parent
_DEFAULT_DB = str(_ROOT / "data" / "cultureforge.db")


# ---------------------------------------------------------------------------
# Conda environment discovery
# ---------------------------------------------------------------------------

def find_conda_env_bin(env_name: str) -> Optional[Path]:
    """Locate the bin/ directory of a named conda environment.

    Returns None if the environment isn't found or `conda` itself isn't
    on PATH. The caller decides whether absence is fatal or recoverable.
    """
    if shutil.which("conda") is None:
        return None
    try:
        result = subprocess.run(
            ["conda", "env", "list", "--json"],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    import json
    try:
        envs = json.loads(result.stdout).get("envs", [])
    except json.JSONDecodeError:
        return None

    for env_path in envs:
        env_p = Path(env_path)
        if env_p.name == env_name:
            bin_p = env_p / "bin"
            if bin_p.is_dir():
                return bin_p
    return None


def find_tool(tool_name: str, conda_env: Optional[str] = None) -> Optional[Path]:
    """Locate a tool binary, preferring a conda env if given.

    Search order:
      1. CULTUREFORGE_<TOOL>_BIN env var (e.g. CULTUREFORGE_GAPSEQ_BIN)
      2. The named conda environment's bin/ (if conda_env supplied)
      3. Ambient PATH via shutil.which

    Returns None if not found.
    """
    env_override = os.environ.get(f"CULTUREFORGE_{tool_name.upper()}_BIN")
    if env_override:
        candidate = Path(env_override) / tool_name
        if candidate.exists():
            return candidate

    if conda_env:
        env_bin = find_conda_env_bin(conda_env)
        if env_bin:
            candidate = env_bin / tool_name
            if candidate.exists():
                return candidate

    which = shutil.which(tool_name)
    if which:
        return Path(which)

    return None


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

def run_prodigal(
    genome_path: Path, output_dir: Path, verbose: bool = False
) -> Tuple[Path, int]:
    """Predict proteins from genome assembly using prodigal (single mode).

    Returns: (proteome_faa_path, n_proteins).
    """
    print("[1/6] Predicting proteins with prodigal...", flush=True)
    prodigal = find_tool("prodigal")
    if prodigal is None:
        raise RuntimeError(
            "prodigal not found. Install with `sudo apt install prodigal` "
            "or set CULTUREFORGE_PRODIGAL_BIN to the directory containing "
            "the prodigal binary."
        )

    proteome_path = output_dir / "proteome.faa"
    genes_gff = output_dir / "genes.gff"
    cmd = [
        str(prodigal),
        "-i", str(genome_path),
        "-a", str(proteome_path),
        "-o", str(genes_gff),
        "-f", "gff",
        "-p", "single",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"prodigal failed (exit {result.returncode}):\n{result.stderr}"
        )
    if verbose:
        print(result.stderr, file=sys.stderr)

    n_proteins = sum(1 for line in proteome_path.open() if line.startswith(">"))
    print(f"      Predicted {n_proteins} proteins → {proteome_path.name}", flush=True)
    return proteome_path, n_proteins


def run_gapseq(
    genome_path: Path,
    output_dir: Path,
    biomass_template: str = "Bacteria",
    verbose: bool = False,
) -> Path:
    """Run the 4-step gapseq pipeline (find, find-transport, draft, fill).

    Returns: directory containing gapseq output files.
    """
    print("[2/6] Running gapseq (this takes 30-60 minutes)...", flush=True)
    gapseq = find_tool("gapseq", conda_env="gapseq")
    if gapseq is None:
        raise RuntimeError(
            "gapseq not found. Install via "
            "`conda create -n gapseq -c bioconda gapseq`, or set "
            "CULTUREFORGE_GAPSEQ_BIN to the directory containing the "
            "gapseq binary."
        )

    gapseq_dir = output_dir / "gapseq"
    gapseq_dir.mkdir(exist_ok=True)
    accession = genome_path.stem

    # gapseq needs PATH that includes its env's bin/ for subtools (R, blast, etc.)
    env = dict(os.environ)
    if gapseq.parent.is_dir():
        env["PATH"] = str(gapseq.parent) + os.pathsep + env.get("PATH", "")

    steps = [
        ("find -p all", [
            str(gapseq), "find", "-p", "all", "-b", "200",
            "-m", biomass_template, str(genome_path),
        ]),
        ("find-transport", [
            str(gapseq), "find-transport", "-b", "200", str(genome_path),
        ]),
        ("draft", [
            str(gapseq), "draft",
            "-r", f"{accession}-all-Reactions.tbl",
            "-t", f"{accession}-Transporter.tbl",
            "-c", str(genome_path),
            "-p", f"{accession}-all-Pathways.tbl",
            "-b", "auto",
        ]),
        # gapseq fill is also part of the standard pipeline but not required
        # for downstream loading — we use the pathways/transporter/reactions
        # tables directly, not the gap-filled SBML model.
    ]

    for label, cmd in steps:
        print(f"      gapseq {label} ...", flush=True)
        result = subprocess.run(
            cmd, cwd=str(gapseq_dir), env=env,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"gapseq {label} failed (exit {result.returncode}):\n"
                f"{result.stderr[-2000:]}"
            )
        if verbose:
            print(result.stdout[-500:], file=sys.stderr)

    print(f"      gapseq output → {gapseq_dir}", flush=True)
    return gapseq_dir


def run_genomespot(
    genome_path: Path,
    proteome_path: Path,
    output_dir: Path,
    verbose: bool = False,
) -> Path:
    """Run GenomeSPOT for environmental envelope prediction.

    Returns: path to the predictions.tsv output.
    """
    print("[3/6] Running GenomeSPOT...", flush=True)
    gs_dir = output_dir / "genomespot"
    gs_dir.mkdir(exist_ok=True)
    output_prefix = gs_dir / "genomespot"

    # Try the genomespot conda env first; fall back to ambient python only
    # if the ambient python has joblib (GenomeSPOT's required dep).
    gs_python = None
    env_bin = find_conda_env_bin("genomespot")
    if env_bin and (env_bin / "python").exists():
        gs_python = env_bin / "python"

    if gs_python is None:
        # Verify the project Python can import joblib before falling back.
        # Without joblib GenomeSPOT crashes with ModuleNotFoundError.
        joblib_check = subprocess.run(
            [sys.executable, "-c", "import joblib"],
            capture_output=True,
        )
        if joblib_check.returncode == 0:
            gs_python = Path(sys.executable)
        else:
            raise RuntimeError(
                "GenomeSPOT requires joblib but neither a `genomespot` conda "
                "env nor the project Python has it. Install via "
                "`conda create -n genomespot python=3.10 && conda activate genomespot && "
                "pip install joblib scikit-learn numpy biopython` (and ensure "
                "the env contains the vendored GenomeSPOT package), or "
                "`pip install joblib` into the active python environment."
            )

    cmd = [
        str(gs_python), "-m", "genome_spot.genome_spot",
        "--contigs", str(genome_path),
        "--proteins", str(proteome_path),
        "--models", str(_ROOT / "vendor" / "GenomeSPOT" / "models"),
        "--output-prefix", str(output_prefix),
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_ROOT / "vendor" / "GenomeSPOT") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            f"GenomeSPOT failed (exit {result.returncode}):\n{result.stderr}"
        )
    if verbose:
        print(result.stdout[-500:], file=sys.stderr)

    predictions_tsv = output_dir / "genomespot" / "genomespot.predictions.tsv"
    if not predictions_tsv.exists():
        raise RuntimeError(
            f"GenomeSPOT did not produce expected output: {predictions_tsv}"
        )

    print(f"      GenomeSPOT predictions → {predictions_tsv.name}", flush=True)
    return predictions_tsv


def run_checkm2_if_available(
    genome_path: Path, output_dir: Path, verbose: bool = False
) -> Optional[Path]:
    """Run CheckM2 if installed; return None and log notice if not.

    Returns: path to the quality_report.tsv output, or None if skipped.
    """
    checkm2 = find_tool("checkm2", conda_env="checkm2")
    if checkm2 is None:
        print("[5/6] CheckM2 not installed — skipping (genome quality unknown)",
              flush=True)
        return None

    print("[5/6] Running CheckM2...", flush=True)
    cm_dir = output_dir / "checkm2"
    cm_dir.mkdir(exist_ok=True)
    cmd = [
        str(checkm2), "predict",
        "--threads", "4",
        "--input", str(genome_path),
        "--output-directory", str(cm_dir),
    ]
    env = dict(os.environ)
    if checkm2.parent.is_dir():
        env["PATH"] = str(checkm2.parent) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"      CheckM2 failed: {result.stderr[-500:]}", file=sys.stderr)
        return None

    report = cm_dir / "quality_report.tsv"
    if report.exists():
        print(f"      CheckM2 report → {report}", flush=True)
        return report
    return None


def run_mebipred_if_available(
    proteome_path: Path, output_dir: Path, verbose: bool = False
) -> Optional[Path]:
    """Run MeBiPred (mymetal) if installed; return None and log notice if not.

    Returns: path to predictions TSV, or None if skipped.
    """
    try:
        import mymetal  # noqa: F401
    except ImportError:
        print("[6/6] MeBiPred (mymetal) not installed — skipping "
              "(metal profile defaults to SL-10 baseline)", flush=True)
        return None

    print("[6/6] Running MeBiPred...", flush=True)
    # The actual invocation depends on user's MeBiPred installation;
    # the existing run_mebipred.py wraps mymetal with project conventions.
    # Defer to that script for now.
    runner = _ROOT / "run_mebipred.py"
    if not runner.exists():
        print("      run_mebipred.py missing — skipping", file=sys.stderr)
        return None

    mb_dir = output_dir / "mebipred"
    mb_dir.mkdir(exist_ok=True)
    predictions_tsv = mb_dir / "predictions.tsv"

    cmd = [
        sys.executable, str(runner),
        "--proteome", str(proteome_path),
        "--output", str(predictions_tsv),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not predictions_tsv.exists():
        print(f"      MeBiPred failed: {result.stderr[-500:]}", file=sys.stderr)
        return None

    print(f"      MeBiPred predictions → {predictions_tsv}", flush=True)
    return predictions_tsv


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------

def process_genome(
    input_path: str,
    accession: Optional[str] = None,
    notes: str = "",
    output_dir: Optional[str] = None,
    biomass_template: str = "Gram_neg",
    skip_checkm2: bool = False,
    skip_mebipred: bool = False,
    gapseq_output_dir: Optional[str] = None,
    skip_gapseq: bool = False,
    db_path: str = _DEFAULT_DB,
    verbose: bool = False,
) -> int:
    """Full end-to-end pipeline. Returns the assigned gid.

    On any failure mid-pipeline, the partially-loaded genome is deregistered
    so the database stays consistent and the user can retry cleanly.
    """
    input_path_p = Path(input_path).resolve()
    if not input_path_p.exists():
        raise FileNotFoundError(f"Genome FASTA not found: {input_path_p}")

    if accession is None:
        accession = input_path_p.stem
    if output_dir is None:
        output_dir_p = _ROOT / "data" / "user_genomes" / accession
    else:
        output_dir_p = Path(output_dir).resolve()
    output_dir_p.mkdir(parents=True, exist_ok=True)

    print("=== CultureForge process pipeline ===", flush=True)
    print(f"  Input genome: {input_path_p}", flush=True)
    print(f"  Accession:    {accession}", flush=True)
    print(f"  Output dir:   {output_dir_p}", flush=True)
    print(f"  Biomass:      {biomass_template}", flush=True)
    print(f"  Database:     {db_path}", flush=True)
    print("", flush=True)

    # Stage genome into output dir under a clean name
    staged_genome = output_dir_p / "genome.fna"
    if not staged_genome.exists():
        shutil.copy(input_path_p, staged_genome)

    # Map biomass shorthand to gapseq's domain argument (Bacteria/Archaea)
    gapseq_domain = "Archaea" if biomass_template.lower().startswith("arch") else "Bacteria"

    # Register
    gid = register_genome(
        db_path=db_path,
        accession=accession,
        file_path=str(staged_genome),
        notes=notes or f"User-loaded genome: {accession} (Phase 4.1 wrapper)",
        biomass_template=biomass_template,
    )
    print(f"Registered gid={gid}", flush=True)
    print("", flush=True)

    try:
        # Stage 1: prodigal
        proteome_path, n_proteins = run_prodigal(
            staged_genome, output_dir_p, verbose=verbose,
        )
        update_genome_metadata(db_path=db_path, gid=gid, n_unique_genes=n_proteins)

        # Stage 2: gapseq (slow) — or load pre-computed outputs from cluster run
        if skip_gapseq:
            if not gapseq_output_dir:
                raise ValueError(
                    "--skip-gapseq requires --gapseq-output-dir pointing to "
                    "pre-computed gapseq outputs."
                )
            gapseq_dir = Path(gapseq_output_dir).resolve()
            if not gapseq_dir.is_dir():
                raise FileNotFoundError(
                    f"--gapseq-output-dir does not exist or is not a directory: "
                    f"{gapseq_dir}"
                )
            print(f"[2/6] Skipping local gapseq run — loading pre-computed "
                  f"outputs from {gapseq_dir} (accession prefix: {accession})",
                  flush=True)
            gapseq_summary = load_gapseq_outputs(
                gid=gid,
                gapseq_dir=str(gapseq_dir),
                db_path=db_path,
                accession=accession,
            )
            print(f"      gapseq loaded — {gapseq_summary}", flush=True)
        else:
            gapseq_dir = run_gapseq(
                staged_genome, output_dir_p,
                biomass_template=gapseq_domain, verbose=verbose,
            )
            # gapseq names outputs from the staged FASTA stem (e.g. "genome-*.tbl"),
            # not the user's --accession. Pass accession=None to let
            # _resolve_gapseq_files glob the directory and pick up whatever stem
            # gapseq used.
            gapseq_summary = load_gapseq_outputs(
                gid=gid,
                gapseq_dir=str(gapseq_dir),
                db_path=db_path,
                accession=None,
            )
            print(f"      gapseq loaded — {gapseq_summary}", flush=True)

        # Stage 3: GenomeSPOT
        gs_predictions = run_genomespot(
            staged_genome, proteome_path, output_dir_p, verbose=verbose,
        )
        n_gs = load_genomespot_outputs(
            gid=gid, predictions_tsv=str(gs_predictions), db_path=db_path,
        )
        print(f"      GenomeSPOT loaded — {n_gs} predictions", flush=True)

        # Stage 4: marker BLAST
        print("[4/6] Running marker BLAST...", flush=True)
        marker_results = load_marker_blast_results(
            gid=gid, proteome_path=str(proteome_path), db_path=db_path,
        )
        n_markers_fired = sum(1 for v in marker_results.values() if v)
        n_hits = sum(len(v) for v in marker_results.values())
        print(f"      Marker BLAST loaded — "
              f"{n_markers_fired} markers fired, {n_hits} total hits",
              flush=True)

        # Stage 5: optional CheckM2
        if not skip_checkm2:
            run_checkm2_if_available(staged_genome, output_dir_p, verbose=verbose)

        # Stage 6: optional MeBiPred
        if not skip_mebipred:
            mb_tsv = run_mebipred_if_available(
                proteome_path, output_dir_p, verbose=verbose,
            )
            if mb_tsv:
                mb_summary = load_mebipred_outputs(
                    gid=gid, predictions_tsv=str(mb_tsv), db_path=db_path,
                )
                print(f"      MeBiPred loaded — {mb_summary}", flush=True)

    except Exception as exc:
        print("", file=sys.stderr)
        print(f"ERROR during pipeline: {exc}", file=sys.stderr)
        print(f"Cleaning up partial database entries for gid={gid}...",
              file=sys.stderr)
        try:
            deleted = deregister_genome(db_path, gid)
            print(f"Cleaned: {deleted}", file=sys.stderr)
        except Exception as cleanup_exc:
            print(f"Cleanup also failed: {cleanup_exc}", file=sys.stderr)
        raise

    print("", flush=True)
    print("=== Processing complete ===", flush=True)
    print(f"Genome registered as gid={gid}", flush=True)
    print(f"Run `python3 cultureforge.py inspect {gid}` to view the recipe.",
          flush=True)
    print("", flush=True)
    return gid


if __name__ == "__main__":
    # Direct invocation (cultureforge.py dispatches here too)
    import argparse
    parser = argparse.ArgumentParser(
        description="End-to-end CultureForge pipeline for a new genome",
    )
    parser.add_argument("--input", required=True, help="Path to genome FASTA")
    parser.add_argument("--accession", help="Accession identifier (default: filename stem)")
    parser.add_argument("--notes", default="", help="Notes for the database row")
    parser.add_argument("--output-dir", help="Output directory (default: data/user_genomes/<accession>/)")
    parser.add_argument(
        "--biomass-template", default="Gram_neg",
        choices=["Gram_neg", "Gram_pos", "Archaea"],
        help="Biomass template for gapseq (default: Gram_neg)",
    )
    parser.add_argument(
        "--gapseq-output-dir",
        help="Path to pre-computed gapseq output directory containing "
             "<accession>-all-Pathways.tbl, -all-Reactions.tbl, -Transporter.tbl. "
             "Used with --skip-gapseq for the cluster-then-load hybrid workflow.",
    )
    parser.add_argument(
        "--skip-gapseq", action="store_true",
        help="Skip the local gapseq run and load pre-computed outputs instead. "
             "Requires --gapseq-output-dir.",
    )
    parser.add_argument("--skip-checkm2", action="store_true")
    parser.add_argument("--skip-mebipred", action="store_true")
    parser.add_argument("--db", default=_DEFAULT_DB)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    gid = process_genome(
        input_path=args.input,
        accession=args.accession,
        notes=args.notes,
        output_dir=args.output_dir,
        biomass_template=args.biomass_template,
        skip_checkm2=args.skip_checkm2,
        skip_mebipred=args.skip_mebipred,
        gapseq_output_dir=args.gapseq_output_dir,
        skip_gapseq=args.skip_gapseq,
        db_path=args.db,
        verbose=args.verbose,
    )
    sys.exit(0)
