#!/bin/bash
# fetch_oxidase_markers.sh — download terminal oxidase reference sequences
# Run on a machine with internet access: bash fetch_oxidase_markers.sh
set -euo pipefail

OUTDIR="data/diagnostic_markers"
mkdir -p "$OUTDIR"

fetch_one() {
    local accession=$1
    local output=$2
    echo "  Fetching $accession ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${accession}.fasta" >> "$output" || \
        echo "  FAILED: $accession" >&2
    sleep 0.5
}

# terminal_oxidases — caa3, qoxABCD, soxM (archaeal), aox
OUTFILE="$OUTDIR/terminal_oxidases_refs.fasta"
: > "$OUTFILE"

echo "Building terminal_oxidases ..."

# caa3-type cytochrome c oxidase (Thermus, Actinobacteria)
# Thermus thermophilus CtaD (subunit I of caa3)
fetch_one Q56431 "$OUTFILE"
# Thermus thermophilus CtaC (subunit II)
fetch_one P82543 "$OUTFILE"

# qoxABCD quinol oxidase (Bacillus subtilis)
fetch_one P34957 "$OUTFILE"  # QoxB (subunit I)
fetch_one P34956 "$OUTFILE"  # QoxA (subunit II)

# SoxM/SoxB — Sulfolobus archaeal terminal oxidase
# (note: these are the respiratory SoxM/SoxB, NOT the sulfur Sox pathway)
fetch_one P39484 "$OUTFILE"  # SoxM (Sulfolobus acidocaldarius)
fetch_one Q4J781 "$OUTFILE"  # SoxB (Sulfolobus)

# coxA/coxB generic cytochrome c oxidase subunits (Paracoccus denitrificans)
fetch_one P08305 "$OUTFILE"  # CoxI (subunit I)
fetch_one P08306 "$OUTFILE"  # CoxII (subunit II)

n=$(grep -c '^>' "$OUTFILE" 2>/dev/null || echo 0)
echo "  terminal_oxidases: $n sequences"
echo "Done. Run build_marker_blast_db.py --rebuild to update BLAST databases."
