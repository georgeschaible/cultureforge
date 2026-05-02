#!/bin/bash
set -e

GAPSEQ="conda run -n gapseq --no-banner gapseq"
ROOT="$(cd "$(dirname "$0")" && pwd)"

ORGANISMS=(
  "Nitrosomonas_europaea:NC_004757.1:Gram_neg"
  "Rhodopseudomonas_palustris:NC_005296.1:Gram_neg"
  "Halobacterium_salinarum:NC_002607.1:Archaea"
  "Syntrophomonas_wolfei:NC_008346.1:Gram_neg"
  "Acetobacterium_woodii:NC_016894.1:Gram_pos"
)

for entry in "${ORGANISMS[@]}"; do
  IFS=: read -r NAME ACC BIOMASS <<< "$entry"
  GENOME="$ROOT/data/genomes/${NAME}.fasta"
  OUTDIR="$ROOT/data/gapseq/${NAME}"
  
  if [ -f "$OUTDIR/${NAME}-all-Pathways.tbl" ]; then
    echo "[SKIP] $NAME already has gapseq output"
    continue
  fi
  
  echo "=== $(date): Starting gapseq for $NAME ==="
  mkdir -p "$OUTDIR"
  cd "$OUTDIR"
  
  echo "  find -p all..."
  $GAPSEQ find -p all -b $BIOMASS "$GENOME" > /dev/null 2>&1
  
  echo "  find-transport..."
  $GAPSEQ find-transport -b 200 "$GENOME" > /dev/null 2>&1
  
  echo "  draft..."
  PATHWAYS=$(ls ${NAME}-all-Pathways.tbl 2>/dev/null || ls *-all-Pathways.tbl 2>/dev/null | head -1)
  TRANSPORT=$(ls ${NAME}-Transporter.tbl 2>/dev/null || ls *-Transporter.tbl 2>/dev/null | head -1)
  if [ -n "$PATHWAYS" ] && [ -n "$TRANSPORT" ]; then
    $GAPSEQ draft -r "$PATHWAYS" -t "$TRANSPORT" -c "$GENOME" -b "$BIOMASS" -u 200 -l 100 > /dev/null 2>&1
  fi
  
  echo "  $(date): Done with $NAME"
  cd "$ROOT"
done

echo "=== ALL DONE ==="
