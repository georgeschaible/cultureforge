#!/bin/bash
set -e
# Optional: set CULTUREFORGE_GAPSEQ_BIN to a conda env bin/ to prepend to PATH
[ -n "$CULTUREFORGE_GAPSEQ_BIN" ] && export PATH="$CULTUREFORGE_GAPSEQ_BIN:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"

ORGANISMS=(
  "Nitrosomonas_europaea:NC_004757.1:Gram_neg"
  "Rhodopseudomonas_palustris:NC_005296.1:Gram_neg"
  "Halobacterium_salinarum:NC_002607.1:Archaea"
  "Syntrophomonas_wolfei:NC_008346.1:Gram_neg"
  "Acetobacterium_woodii:NC_016894.1:Gram_pos"
)

LOG="$ROOT/data/validation/blind_gapseq.log"
echo "=== $(date): Starting all blind gapseq runs ===" > "$LOG"

for entry in "${ORGANISMS[@]}"; do
  IFS=: read -r NAME ACC BIOMASS <<< "$entry"
  GENOME="$ROOT/data/genomes/${NAME}.fasta"
  OUTDIR="$ROOT/data/gapseq/${NAME}"
  
  if [ -f "$OUTDIR/${NAME}-all-Pathways.tbl" ]; then
    echo "$(date): [SKIP] $NAME already done" >> "$LOG"
    continue
  fi
  
  echo "$(date): Starting $NAME" >> "$LOG"
  mkdir -p "$OUTDIR"
  cd "$OUTDIR"
  
  echo "$(date):   find -p all..." >> "$LOG"
  gapseq find -p all -b "$BIOMASS" "$GENOME" >> "$LOG" 2>&1
  
  echo "$(date):   find-transport..." >> "$LOG"
  gapseq find-transport -b 200 "$GENOME" >> "$LOG" 2>&1
  
  PATHWAYS=$(ls *-all-Pathways.tbl 2>/dev/null | head -1)
  TRANSPORT=$(ls *-Transporter.tbl 2>/dev/null | head -1)
  if [ -n "$PATHWAYS" ] && [ -n "$TRANSPORT" ]; then
    echo "$(date):   draft..." >> "$LOG"
    gapseq draft -r "$PATHWAYS" -t "$TRANSPORT" -c "$GENOME" -b "$BIOMASS" -u 200 -l 100 >> "$LOG" 2>&1
  fi
  
  echo "$(date): DONE with $NAME" >> "$LOG"
  cd "$ROOT"
done

echo "$(date): === ALL BLIND ORGANISMS COMPLETE ===" >> "$LOG"
