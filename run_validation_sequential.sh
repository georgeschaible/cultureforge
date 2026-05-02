#!/bin/bash
# Run remaining gapseq organisms ONE AT A TIME (no CPU contention).
# Picks up from wherever the parallel batch left off (skips completed).
set -e

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate gapseq

PROJ="$(cd "$(dirname "$0")" && pwd)"
GENOMES=$PROJ/data/genomes

# All 10 organisms — script skips any that already have final .RDS
ORGS=(
  Thermus_aquaticus
  Methanococcus_jannaschii
  Lactobacillus_plantarum
  Acidithiobacillus_ferrooxidans
  Clostridium_acetobutylicum
  Geobacter_sulfurreducens
  Sulfolobus_acidocaldarius
  Campylobacter_jejuni
  Magnetospirillum_magneticum
  Sulfurimonas_denitrificans
)

declare -A DOMAIN
DOMAIN[Methanococcus_jannaschii]="Archaea"
DOMAIN[Sulfolobus_acidocaldarius]="Archaea"

for name in "${ORGS[@]}"; do
  genome=$GENOMES/${name}.fasta
  work=$PROJ/data/gapseq/${name}
  domain=${DOMAIN[$name]:-Bacteria}

  # Skip if already complete (has Pathways.tbl = at least step 1 done)
  if ls "$work"/*-all-Pathways.tbl 1>/dev/null 2>&1; then
    # Check if fill also completed
    if ls "$work"/${name}.RDS 1>/dev/null 2>&1 || ls "$work"/${name}-draft.RDS 1>/dev/null 2>&1; then
      echo "[SKIP] $name — already has gapseq output"
      continue
    fi
  fi

  mkdir -p "$work"
  cd "$work"

  echo "[SEQ-START] $name (domain=$domain) at $(date)"

  # Step 1: find
  if ! ls "$work"/*-all-Pathways.tbl 1>/dev/null 2>&1; then
    gapseq find -p all -b 200 -m "$domain" "$genome" 2>&1 | tail -3
  fi

  PREFIX=$(ls *-all-Pathways.tbl 2>/dev/null | sed 's/-all-Pathways.tbl//' | head -1)
  if [ -z "$PREFIX" ]; then echo "[ERROR] $name: no Pathways.tbl"; continue; fi

  # Step 2: transport
  if ! ls "$work"/*-Transporter.tbl 1>/dev/null 2>&1; then
    gapseq find-transport -b 200 "$genome" 2>&1 | tail -3
  fi

  # Step 3: draft
  if ! ls "$work"/*-draft.RDS 1>/dev/null 2>&1; then
    gapseq draft -r "${PREFIX}-all-Reactions.tbl" \
                 -t "${PREFIX}-Transporter.tbl" \
                 -c "$genome" \
                 -p "${PREFIX}-all-Pathways.tbl" \
                 -b auto 2>&1 | tail -3
  fi

  # Step 4: fill
  if ! ls "$work"/${name}.RDS 1>/dev/null 2>&1; then
    GAPSEQ_DAT=$(dirname $(which gapseq))/../share/gapseq/dat
    ALLMED="$GAPSEQ_DAT/media/ALLmed.csv"
    gapseq fill -m "${PREFIX}-draft.RDS" \
                -n "$ALLMED" \
                -c "${PREFIX}-rxnWeights.RDS" \
                -g "${PREFIX}-rxnXgenes.RDS" 2>&1 | tail -10
  fi

  echo "[SEQ-DONE] $name at $(date)"
done

echo "=== ALL SEQUENTIAL GAPSEQ COMPLETE ==="
