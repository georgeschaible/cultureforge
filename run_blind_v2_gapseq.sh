#!/bin/bash
set -e
# Optional: set CULTUREFORGE_GAPSEQ_BIN to a conda env bin/ to prepend to PATH
[ -n "$CULTUREFORGE_GAPSEQ_BIN" ] && export PATH="$CULTUREFORGE_GAPSEQ_BIN:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT/data/validation/blind_v2_gapseq.log"

ORGANISMS=(
  "Nitrospira_moscoviensis:Bacteria"
  "Chloroflexus_aurantiacus:Bacteria"
  "Dehalococcoides_mccartyi:Bacteria"
  "Picrophilus_torridus:Archaea"
  "Thermotoga_maritima:Bacteria"
  "Candidatus_Scalindua_profunda:Bacteria"
  "Candidatus_Methanoperedens_nitroreducens:Archaea"
  "Candidatus_Prometheoarchaeum_syntrophicum:Archaea"
)

echo "$(date): Starting blind v2 gapseq runs" | tee "$LOG"

for entry in "${ORGANISMS[@]}"; do
  IFS=: read -r NAME TAXON <<< "$entry"
  GENOME="$ROOT/data/genomes/blind_v2/${NAME}.fasta"
  OUTDIR="$ROOT/data/gapseq/${NAME}"
  
  if [ -f "$OUTDIR/${NAME}-all-Pathways.tbl" ]; then
    good=$(grep -c "good_blast" "$OUTDIR/${NAME}-all-Reactions.tbl" 2>/dev/null || echo 0)
    if [ "$good" -gt "0" ]; then
      echo "$(date): [SKIP] $NAME (good_blast=$good)" | tee -a "$LOG"
      continue
    fi
  fi
  
  echo "$(date): === $NAME (taxonomy=$TAXON) ===" | tee -a "$LOG"
  rm -rf "$OUTDIR"/*
  mkdir -p "$OUTDIR"
  cd "$OUTDIR"
  
  gapseq find -p all -b 200 -t "$TAXON" "$GENOME" >> "$LOG" 2>&1
  gapseq find-transport -b 200 "$GENOME" >> "$LOG" 2>&1
  
  PATHWAYS=$(ls *-all-Pathways.tbl 2>/dev/null | head -1)
  TRANSPORT=$(ls *-Transporter.tbl 2>/dev/null | head -1)
  if [ -n "$PATHWAYS" ] && [ -n "$TRANSPORT" ]; then
    gapseq draft -r "$PATHWAYS" -t "$TRANSPORT" -c "$GENOME" -b auto -u 200 -l 100 >> "$LOG" 2>&1 || true
  fi
  
  good=$(grep -c "good_blast" *-all-Reactions.tbl 2>/dev/null || echo 0)
  pred=$(awk -F'\t' '$3=="true"' *-all-Pathways.tbl 2>/dev/null | wc -l)
  echo "$(date): DONE $NAME (good=$good pred=$pred)" | tee -a "$LOG"
  cd "$ROOT"
done

echo "$(date): === ALL BLIND V2 DONE ===" | tee -a "$LOG"
