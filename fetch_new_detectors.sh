#!/bin/bash
set -euo pipefail
OUTDIR="data/diagnostic_markers"

fetch_one() {
    local acc=$1; local out=$2
    echo "  Fetching $acc ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${acc}.fasta" >> "$out" || echo "  FAILED: $acc" >&2
    sleep 0.5
}

# === hzsA — hydrazine synthase (anammox diagnostic) ===
OUT="$OUTDIR/hzsA_refs.fasta"
: > "$OUT"
echo "Building hzsA..."
# Ca. Kuenenia stuttgartiensis HzsA
fetch_one Q1Q5W1 "$OUT"
# Search for other anammox hzsA
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=hydrazine+synthase+Brocadia&format=fasta&size=2" >> "$OUT"
sleep 0.5
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=hydrazine+synthase+Jettenia&format=fasta&size=1" >> "$OUT"
sleep 0.5
n=$(grep -c '^>' "$OUT" 2>/dev/null || echo 0)
echo "  hzsA: $n sequences"

# === hdh — hydrazine dehydrogenase (anammox confirmatory) ===
OUT="$OUTDIR/hdh_refs.fasta"
: > "$OUT"
echo "Building hdh..."
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=hydrazine+oxidoreductase+Kuenenia&format=fasta&size=2" >> "$OUT"
sleep 0.5
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=hydrazine+dehydrogenase+Brocadia&format=fasta&size=2" >> "$OUT"
sleep 0.5
n=$(grep -c '^>' "$OUT" 2>/dev/null || echo 0)
echo "  hdh: $n sequences"

# === rdhA — reductive dehalogenase (organohalide respiration) ===
OUT="$OUTDIR/rdhA_refs.fasta"
: > "$OUT"
echo "Building rdhA..."
# Search for diverse reductive dehalogenases
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=reductive+dehalogenase+Dehalococcoides&format=fasta&size=5" >> "$OUT"
sleep 0.5
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=reductive+dehalogenase+Dehalobacter&format=fasta&size=2" >> "$OUT"
sleep 0.5
curl -sS "https://rest.uniprot.org/uniprotkb/search?query=reductive+dehalogenase+Desulfitobacterium&format=fasta&size=2" >> "$OUT"
sleep 0.5
n=$(grep -c '^>' "$OUT" 2>/dev/null || echo 0)
echo "  rdhA: $n sequences"

echo "Done."
