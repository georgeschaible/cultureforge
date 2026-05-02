#!/bin/bash
set -e
# Optional: set CULTUREFORGE_GAPSEQ_BIN to a conda env bin/ to prepend to PATH
[ -n "$CULTUREFORGE_GAPSEQ_BIN" ] && export PATH="$CULTUREFORGE_GAPSEQ_BIN:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT/data/validation/blind_gapseq_v2.log"

ORGANISMS=(
  "Nitrosomonas_europaea:NC_004757.1:Bacteria"
  "Rhodopseudomonas_palustris:NC_005296.1:Bacteria"
  "Halobacterium_salinarum:NC_002607.1:Archaea"
  "Syntrophomonas_wolfei:NC_008346.1:Bacteria"
  "Acetobacterium_woodii:NC_016894.1:Bacteria"
)

echo "$(date): Starting all blind gapseq runs (correct flags)" | tee "$LOG"

for entry in "${ORGANISMS[@]}"; do
  IFS=: read -r NAME ACC TAXON <<< "$entry"
  GENOME="$ROOT/data/genomes/${NAME}.fasta"
  OUTDIR="$ROOT/data/gapseq/${NAME}"
  
  if [ -f "$OUTDIR/${NAME}-all-Pathways.tbl" ]; then
    good=$(grep -c "good_blast" "$OUTDIR/${NAME}-all-Reactions.tbl" 2>/dev/null || echo 0)
    if [ "$good" -gt "0" ]; then
      echo "$(date): [SKIP] $NAME already done with good_blast=$good" | tee -a "$LOG"
      continue
    fi
  fi
  
  echo "$(date): === Starting $NAME (taxonomy=$TAXON) ===" | tee -a "$LOG"
  rm -rf "$OUTDIR"/*
  mkdir -p "$OUTDIR"
  cd "$OUTDIR"
  
  # CORRECT FLAGS: -b 200 (bitscore), -t taxonomy, NO -a (too slow, not needed)
  echo "$(date):   find -p all -b 200 -t $TAXON" | tee -a "$LOG"
  gapseq find -p all -b 200 -t "$TAXON" "$GENOME" >> "$LOG" 2>&1
  
  echo "$(date):   find-transport -b 200" | tee -a "$LOG"
  gapseq find-transport -b 200 "$GENOME" >> "$LOG" 2>&1
  
  PATHWAYS=$(ls *-all-Pathways.tbl 2>/dev/null | head -1)
  TRANSPORT=$(ls *-Transporter.tbl 2>/dev/null | head -1)
  if [ -n "$PATHWAYS" ] && [ -n "$TRANSPORT" ]; then
    echo "$(date):   draft" | tee -a "$LOG"
    gapseq draft -r "$PATHWAYS" -t "$TRANSPORT" -c "$GENOME" -b auto -u 200 -l 100 >> "$LOG" 2>&1 || true
  fi
  
  good=$(grep -c "good_blast" *-all-Reactions.tbl 2>/dev/null || echo 0)
  pred=$(awk -F'\t' '$3=="true"' *-all-Pathways.tbl 2>/dev/null | wc -l)
  echo "$(date):   DONE: $NAME (good_blast=$good, predicted=$pred)" | tee -a "$LOG"
  
  cd "$ROOT"
done

echo "$(date): === ALL DONE ===" | tee -a "$LOG"
