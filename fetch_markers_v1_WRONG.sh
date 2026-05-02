#!/bin/bash
# fetch_markers.sh — download diagnostic marker reference sequences from UniProt
#
# Run this on a machine with internet access:
#   bash fetch_markers.sh
#
# Populates data/diagnostic_markers/ with protein FASTAs for each marker set.
# Each file contains 3-5 canonical sequences from Swiss-Prot for BLASTP reference.

set -euo pipefail

OUTDIR="data/diagnostic_markers"
mkdir -p "$OUTDIR"

fetch_one() {
    local accession=$1
    local output=$2
    echo "  Fetching $accession ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${accession}.fasta" >> "$output" || \
        echo "  FAILED: $accession for $output" >&2
    sleep 0.5  # rate limit
}

build_ref() {
    local name=$1
    shift
    local outfile="$OUTDIR/${name}_refs.fasta"
    : > "$outfile"
    echo "Building $name ..."
    for acc in "$@"; do
        fetch_one "$acc" "$outfile"
    done
    local n=$(grep -c '^>' "$outfile" 2>/dev/null || echo 0)
    echo "  $name: $n sequences"
}

# ============================================================
# Methanogenesis markers
# ============================================================

# mcrA — methyl-coenzyme M reductase alpha subunit
# THE definitive marker for methanogenesis
build_ref mcrA \
    P11558 \
    Q8TIY1 \
    Q6LYP5 \
    A5UL61 \
    Q58256

# mcrB + mcrG — beta and gamma subunits
build_ref mcrBG \
    P11559 \
    Q8TIY0 \
    Q58257 \
    Q58258

# ============================================================
# Acetogenesis (Wood-Ljungdahl) markers
# ============================================================

# acsB / cdhC — acetyl-CoA synthase / carbon monoxide dehydrogenase complex
build_ref acsB_cdhC \
    P27988 \
    Q8TMC6 \
    Q3AEH4 \
    P31896

# cooS / cdhA — CO dehydrogenase
build_ref cooS_cdhA \
    P31896 \
    Q2RJY1 \
    P29342 \
    Q8TMC8

# ============================================================
# Ammonia oxidation markers
# ============================================================

# amoA — ammonia monooxygenase subunit A
build_ref amoA \
    Q04507 \
    Q82WK9 \
    A0A1H8YHT3

# haoA — hydroxylamine oxidoreductase
build_ref hao \
    P24022 \
    Q82SR3

# ============================================================
# Phototrophy markers
# ============================================================

# pufLM — reaction center L and M subunits (purple bacteria)
build_ref pufLM \
    Q07006 \
    Q07007 \
    P02948 \
    P02953 \
    P06008 \
    P06009

# pscA + fmoA — green sulfur bacteria reaction center + FMO protein
build_ref pscA_fmoA \
    Q8KEI5 \
    P0C0Y4 \
    Q3AUE1

# psaA + psbA — photosystem I + II (oxygenic, cyanobacteria)
build_ref psaA_psbA \
    P29254 \
    P16033 \
    P10898 \
    Q8DHP3

# ============================================================
# Sulfur metabolism markers
# ============================================================

# soxB — anchor enzyme of thiosulfate oxidation SOX pathway
build_ref soxB \
    Q93UV4 \
    Q3SLP0 \
    O66037

# dsrAB — dissimilatory sulfite reductase (sulfate reduction AND reverse for S oxidation)
build_ref dsrAB \
    P45574 \
    P45575 \
    O28606 \
    O28607

# aprAB — adenylyl-sulfate reductase
build_ref aprAB \
    Q725B7 \
    Q725B6 \
    Q72AU3

# qmoA — QmoABC complex subunit A (forward sulfate reduction discriminator)
# Phase 1.5k: distinguishes forward sulfate reducers from reverse-dsr sulfide oxidizers.
# D. vulgaris Hildenborough QmoA (Q72CJ9) excluded — test set contamination.
# Current refs were manually curated from UniProt TrEMBL (no Swiss-Prot qmoA available).
build_ref qmoA \
    Q7X167 \
    A0A8G2C1P1 \
    A0A0U9HMV6 \
    A0A1M4Z6K0 \
    A0A0T6BPM1 \
    A0A2T4KNK8

# ============================================================
# Denitrification markers
# ============================================================

# nosZ — nitrous oxide reductase (terminal step, diagnostic)
build_ref nosZ \
    P19573 \
    P24474 \
    Q53198

# ============================================================
# Iron metabolism markers
# ============================================================

# cyc2 — outer membrane cytochrome for Fe(II) oxidation (acidophilic)
build_ref cyc2 \
    Q4A194

# mtrC + omcB — outer membrane cytochromes for Fe(III) reduction
build_ref mtrC_omcB \
    Q8EG35 \
    Q74D43 \
    Q74AE7

# ============================================================
# Rhodopsin markers
# ============================================================

# bacteriorhodopsin / proteorhodopsin
build_ref rhodopsin \
    P02945 \
    Q3INN5 \
    Q9F7P4

# ============================================================
# Nitrogen fixation markers
# ============================================================

# nifH — nitrogenase iron protein
build_ref nifH \
    P00459 \
    P07328 \
    P00458

# ============================================================
echo ""
echo "=== SUMMARY ==="
for f in "$OUTDIR"/*_refs.fasta; do
    n=$(grep -c '^>' "$f" 2>/dev/null || echo 0)
    echo "  $(basename $f): $n sequences"
done
echo ""
echo "Done. Run build_marker_blast_db.py to build BLAST databases."

# ============================================================
# Autotrophy diagnostic markers (Phase 1.5b)
# ============================================================

# rbcL — RuBisCO large subunit (CBB cycle diagnostic)
build_ref autotrophy \
    P54205 \
    Q3IXP8 \
    Q1JU64 \
    Q8KFR1 \
    Q9F721 \
    A4YHK3

