"""Build a BLAST nucleotide database from the 16S reference FASTA.

Reads:  data/16s_reference.fasta
Creates: data/blastdb/16s_ref.n* (BLAST database files)

Run after fetch_16s_sequences.py completes.
"""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent

FASTA = str(_ROOT / "data" / "16s_reference.fasta")
DB_DIR = str(_ROOT / "data" / "blastdb")
DB_NAME = str(_ROOT / "data" / "blastdb" / "16s_ref")


def main():
    if not os.path.exists(FASTA):
        print(f"Error: {FASTA} not found. Run fetch_16s_sequences.py first.")
        sys.exit(1)

    # Count sequences
    n = sum(1 for line in open(FASTA) if line.startswith(">"))
    print(f"Building BLAST database from {n} sequences...")

    os.makedirs(DB_DIR, exist_ok=True)

    result = subprocess.run(
        [
            "makeblastdb",
            "-in", FASTA,
            "-dbtype", "nucl",
            "-out", DB_NAME,
            "-title", "CultureForge 16S Reference",
        ],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"makeblastdb failed:\n{result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print(f"BLAST database: {DB_NAME}")


if __name__ == "__main__":
    main()
