#!/bin/bash
set -euo pipefail
OUTDIR="data/diagnostic_markers"

fetch_one() {
    local acc=$1; local out=$2
    echo "  Fetching $acc ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${acc}.fasta" >> "$out" || echo "  FAILED: $acc" >&2
    sleep 0.5
}

# autotrophy_refs.fasta — mixed autotrophy diagnostic markers
OUT="$OUTDIR/autotrophy_refs.fasta"
: > "$OUT"
echo "Building autotrophy markers..."

# rbcL - RuBisCO large subunit (CBB cycle)
fetch_one P54205 "$OUT"   # Synechocystis PCC 6803
fetch_one Q3IXP8 "$OUT"   # Rhodobacter sphaeroides cbbL

# aclA - ATP-citrate lyase (rTCA cycle)
fetch_one Q1JU64 "$OUT"   # Hydrogenobacter thermophilus
fetch_one Q8KFR1 "$OUT"   # Chlorobaculum tepidum

# mcr - malonyl-CoA reductase (3HP bicycle)
fetch_one Q9F721 "$OUT"   # Chloroflexus aurantiacus

# 4hbd - 4-hydroxybutyryl-CoA dehydratase (3HP/4HB + DC/4HB cycles)
fetch_one A4YHK3 "$OUT"   # Metallosphaera sedula

n=$(grep -c '^>' "$OUT" 2>/dev/null || echo 0)
echo "  autotrophy: $n sequences"
