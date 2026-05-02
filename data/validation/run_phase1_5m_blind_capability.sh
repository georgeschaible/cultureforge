#!/bin/bash
# Phase 1.5m Task 6 — re-run BLAST + capability detection on the 8 blind organisms.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/data/validation"
PY="${CULTUREFORGE_PYTHON:-python3}"
mkdir -p "$OUT/phase1_5m_blind_capability"

# (genome_id, organism_label, proteome_path)
declare -a GENOMES=(
  "23|Nitrospira_moscoviensis|data/gapseq/Nitrospira_moscoviensis/Nitrospira_moscoviensis_proteins.faa"
  "24|Chloroflexus_aurantiacus|data/gapseq/Chloroflexus_aurantiacus/Chloroflexus_aurantiacus_proteins.faa"
  "25|Dehalococcoides_mccartyi|data/gapseq/Dehalococcoides_mccartyi/Dehalococcoides_mccartyi_proteins.faa"
  "26|Picrophilus_torridus|data/gapseq/Picrophilus_torridus/Picrophilus_torridus_proteins.faa"
  "27|Thermotoga_maritima|data/gapseq/Thermotoga_maritima/Thermotoga_maritima_proteins.faa"
  "28|Methanoperedens_nitroreducens|data/gapseq/Candidatus_Methanoperedens_nitroreducens/Candidatus_Methanoperedens_nitroreducens_proteins.faa"
  "29|Prometheoarchaeum_syntrophicum|data/gapseq/Candidatus_Prometheoarchaeum_syntrophicum/Candidatus_Prometheoarchaeum_syntrophicum_proteins.faa"
  "30|Scalindua_profunda|data/gapseq/Candidatus_Scalindua_profunda/Candidatus_Scalindua_profunda_proteins.faa"
)

cd "$ROOT"

echo "=== Step 1: marker BLAST against post-1.5m references ==="
for entry in "${GENOMES[@]}"; do
  IFS='|' read -r gid label proteome <<< "$entry"
  echo "[$gid] $label"
  $PY run_marker_blast.py "$proteome" --genome-id "$gid" 2>&1 \
    | grep -E "markers detected|^  [a-z]" \
    | head -25
  echo ""
done

echo ""
echo "=== Step 2: capability JSON for each ==="
for entry in "${GENOMES[@]}"; do
  IFS='|' read -r gid label proteome <<< "$entry"
  $PY capability_report.py --genome-id "$gid" --json \
    --output "$OUT/phase1_5m_blind_capability/${label}.json" 2>&1
done

echo ""
echo "=== DONE ==="
ls "$OUT/phase1_5m_blind_capability/" | wc -l
