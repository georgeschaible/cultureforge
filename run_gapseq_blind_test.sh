#!/bin/bash
# Full gapseq pipeline for blind test organism.
# Steps: find -> find-transport -> draft -> fill
# Output goes to data/gapseq/blind_test_organism_001/

set -e
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate gapseq

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$HERE/data/gapseq/blind_test_organism_001"
GENOME="$HERE/data/sentinel/blind_test_organism_001/genome.fna"
PREFIX=blind_test_organism_001

mkdir -p "$WORK"
cd "$WORK"

echo "============================================================"
echo "STEP 1/4 — gapseq find -p all (pathway prediction)"
echo "Started: $(date)"
echo "============================================================"
gapseq find -p all -b 200 -m Bacteria "$GENOME" 2>&1 | tail -20
echo "Done step 1: $(date)"
echo ""

echo "============================================================"
echo "STEP 2/4 — gapseq find-transport (transporter prediction)"
echo "Started: $(date)"
echo "============================================================"
gapseq find-transport -b 200 "$GENOME" 2>&1 | tail -20
echo "Done step 2: $(date)"
echo ""

echo "============================================================"
echo "STEP 3/4 — gapseq draft (draft metabolic model)"
echo "Started: $(date)"
echo "============================================================"
gapseq draft -r "${PREFIX}-all-Reactions.tbl" \
             -t "${PREFIX}-Transporter.tbl" \
             -c "$GENOME" \
             -p "${PREFIX}-all-Pathways.tbl" \
             -b auto 2>&1 | tail -20
echo "Done step 3: $(date)"
echo ""

echo "============================================================"
echo "STEP 4/4 — gapseq fill (gap filling)"
echo "Started: $(date)"
echo "============================================================"
GAPSEQ_DAT=$(dirname $(which gapseq))/../share/gapseq/dat
ALLMED="$GAPSEQ_DAT/media/ALLmed.csv"
if [ ! -f "$ALLMED" ]; then
    ALLMED=$(find $(dirname $(which gapseq))/.. -name "ALLmed.csv" 2>/dev/null | head -1)
fi
echo "Using medium: $ALLMED"

gapseq fill -m "${PREFIX}-draft.RDS" \
            -n "$ALLMED" \
            -c "${PREFIX}-rxnWeights.RDS" \
            -g "${PREFIX}-rxnXgenes.RDS" 2>&1 | tail -20
echo "Done step 4: $(date)"
echo ""

echo "============================================================"
echo "PIPELINE COMPLETE"
echo "============================================================"
ls -la "$WORK"
