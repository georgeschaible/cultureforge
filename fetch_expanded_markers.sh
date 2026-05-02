#!/bin/bash
set -euo pipefail
OUTDIR="data/diagnostic_markers"

fetch_one() {
    local acc=$1; local out=$2
    echo "  Fetching $acc ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${acc}.fasta" >> "$out" || echo "  FAILED: $acc" >&2
    sleep 0.5
}

# === Expand amoA with comammox + AOA ===
echo "Adding comammox + AOA amoA sequences..."
# Ca. Nitrospira inopinata AmoA
fetch_one A0A0E2YHM7 "$OUTDIR/amoA_refs.fasta"
# Nitrosopumilus maritimus AmoA (AOA)
fetch_one B6ZBA7 "$OUTDIR/amoA_refs.fasta"
# Try additional comammox by searching for Nitrospira amoA
fetch_one A0A1I4DSW4 "$OUTDIR/amoA_refs.fasta"  # N. inopinata variant

n=$(grep -c '^>' "$OUTDIR/amoA_refs.fasta" 2>/dev/null || echo 0)
echo "  amoA total: $n sequences"

# === Expand pufLM with FAP-type ===
echo "Adding FAP-type pufLM sequences..."
# Chloroflexus aurantiacus PufL
fetch_one P26362 "$OUTDIR/pufLM_refs.fasta"
# Chloroflexus aurantiacus PufM  
fetch_one P26363 "$OUTDIR/pufLM_refs.fasta"
# Roseiflexus castenholzii PufL and PufM
fetch_one A7NQ45 "$OUTDIR/pufLM_refs.fasta"
fetch_one A7NQ46 "$OUTDIR/pufLM_refs.fasta"

n=$(grep -c '^>' "$OUTDIR/pufLM_refs.fasta" 2>/dev/null || echo 0)
echo "  pufLM total: $n sequences"

echo "Done. Rebuild BLAST DBs with: python3 build_marker_blast_db.py --rebuild"
