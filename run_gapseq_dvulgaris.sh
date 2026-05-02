#!/bin/bash
set -e
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate gapseq

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$HERE/data/gapseq/dvulgaris"
GENOME="$HERE/data/genomes/dvulgaris_hildenborough.fasta"
mkdir -p "$WORK"
cd "$WORK"

echo "STEP 1/4 — gapseq find -p all (pathway prediction)"
echo "Started: $(date)"
gapseq find -p all -b 200 -m Bacteria "$GENOME" 2>&1 | tail -5
echo "Done step 1: $(date)"

echo "STEP 2/4 — gapseq find-transport"
echo "Started: $(date)"
gapseq find-transport -b 200 "$GENOME" 2>&1 | tail -5
echo "Done step 2: $(date)"

echo "STEP 3/4 — gapseq draft"
echo "Started: $(date)"
# Detect the actual output prefix gapseq used
PREFIX=$(ls *-all-Pathways.tbl 2>/dev/null | sed 's/-all-Pathways.tbl//' | head -1)
if [ -z "$PREFIX" ]; then echo "ERROR: no Pathways.tbl found"; exit 1; fi
echo "Detected prefix: $PREFIX"
gapseq draft -r "${PREFIX}-all-Reactions.tbl" \
             -t "${PREFIX}-Transporter.tbl" \
             -c "$GENOME" \
             -p "${PREFIX}-all-Pathways.tbl" \
             -b auto 2>&1 | tail -5
echo "Done step 3: $(date)"

echo "STEP 4/4 — gapseq fill"
echo "Started: $(date)"
GAPSEQ_DAT=$(dirname $(which gapseq))/../share/gapseq/dat
ALLMED="$GAPSEQ_DAT/media/ALLmed.csv"
gapseq fill -m "${PREFIX}-draft.RDS" \
            -n "$ALLMED" \
            -c "${PREFIX}-rxnWeights.RDS" \
            -g "${PREFIX}-rxnXgenes.RDS" 2>&1 | tail -20
echo "Done step 4: $(date)"

echo "PIPELINE COMPLETE"
ls -la "$WORK"
