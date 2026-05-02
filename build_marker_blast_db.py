"""Build BLAST protein databases from diagnostic marker reference FASTAs.

Scans data/diagnostic_markers/ for *_refs.fasta files and runs makeblastdb
on each.  Honors --rebuild to force re-creation.

Usage:
    python build_marker_blast_db.py [--rebuild]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
MARKER_DIR = _ROOT / "data" / "diagnostic_markers"


def build_all(rebuild: bool = False) -> dict:
    """Build BLAST databases for all marker reference FASTAs.

    Returns dict mapping marker_name -> db_path.
    """
    if not MARKER_DIR.exists():
        print(f"Marker directory not found: {MARKER_DIR}", file=sys.stderr)
        return {}

    fastas = sorted(MARKER_DIR.glob("*_refs.fasta"))
    if not fastas:
        print("No reference FASTAs found in", MARKER_DIR, file=sys.stderr)
        return {}

    databases = {}
    for fasta in fastas:
        # Skip empty files
        n_seqs = sum(1 for line in open(fasta) if line.startswith(">"))
        if n_seqs == 0:
            print(f"  SKIP {fasta.name}: empty")
            continue

        marker_name = fasta.stem.replace("_refs", "")
        db_path = MARKER_DIR / f"blastdb_{marker_name}"

        # Check if already built
        if not rebuild and (db_path.parent / f"{db_path.name}.pdb").exists():
            print(f"  EXISTS {marker_name}: {n_seqs} seqs")
            databases[marker_name] = str(db_path)
            continue

        # Build
        cmd = [
            "makeblastdb",
            "-in", str(fasta),
            "-dbtype", "prot",
            "-out", str(db_path),
            "-title", marker_name,
        ]

        # Optional: prepend a conda env's bin/ to PATH (set CULTUREFORGE_BLAST_BIN
        # to the directory containing makeblastdb); otherwise rely on ambient PATH.
        build_env = dict(os.environ)
        extra_bin = os.environ.get("CULTUREFORGE_BLAST_BIN")
        if extra_bin and os.path.isdir(extra_bin):
            build_env["PATH"] = extra_bin + os.pathsep + build_env.get("PATH", "")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                env=build_env,
            )
            if result.returncode == 0:
                print(f"  BUILT {marker_name}: {n_seqs} seqs")
                databases[marker_name] = str(db_path)
            else:
                print(f"  FAIL {marker_name}: {result.stderr[:200]}",
                      file=sys.stderr)
        except Exception as e:
            print(f"  FAIL {marker_name}: {e}", file=sys.stderr)

    return databases


def get_marker_databases() -> dict:
    """Return dict of marker_name -> db_path for all built databases."""
    databases = {}
    if not MARKER_DIR.exists():
        return databases
    for pdb_file in MARKER_DIR.glob("blastdb_*.pdb"):
        marker_name = pdb_file.stem.replace("blastdb_", "")
        db_path = str(pdb_file).replace(".pdb", "")
        databases[marker_name] = db_path
    return databases


def main():
    parser = argparse.ArgumentParser(
        description="Build BLAST databases from diagnostic marker FASTAs")
    parser.add_argument("--rebuild", action="store_true",
                        help="Force rebuild all databases")
    args = parser.parse_args()

    databases = build_all(rebuild=args.rebuild)
    print(f"\n{len(databases)} marker databases ready.")


if __name__ == "__main__":
    main()
