#!/bin/bash
# Phase 1.5m Checkpoint 3 — re-run BLAST and capability detection on all 18 dev-set genomes.
# Output: data/validation/phase1_5m_capability_*.json

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/data/validation"
PY="${CULTUREFORGE_PYTHON:-python3}"
mkdir -p "$OUT/phase1_5m_capability"

# (genome_id, organism_label, proteome_path)
declare -a GENOMES=(
  "7|Nitratidesulfovibrio_vulgaris|data/genomespot/dvulgaris/dvulgaris_proteins.faa"
  "8|Methanococcus_jannaschii|data/genomespot/Methanococcus_jannaschii/Methanococcus_jannaschii_proteins.faa"
  "9|Thermus_aquaticus|data/genomespot/Thermus_aquaticus/Thermus_aquaticus_proteins.faa"
  "10|Lactobacillus_plantarum|data/genomespot/Lactobacillus_plantarum/Lactobacillus_plantarum_proteins.faa"
  "11|Acidithiobacillus_ferrooxidans|data/genomespot/Acidithiobacillus_ferrooxidans/Acidithiobacillus_ferrooxidans_proteins.faa"
  "12|Clostridium_acetobutylicum|data/genomespot/Clostridium_acetobutylicum/Clostridium_acetobutylicum_proteins.faa"
  "13|Geobacter_sulfurreducens|data/genomespot/Geobacter_sulfurreducens/Geobacter_sulfurreducens_proteins.faa"
  "14|Sulfolobus_acidocaldarius|data/gapseq/Sulfolobus_acidocaldarius/Sulfolobus_acidocaldarius_proteins.faa"
  "15|Campylobacter_jejuni|data/gapseq/Campylobacter_jejuni/Campylobacter_jejuni_proteins.faa"
  "16|Magnetospirillum_magneticum|data/genomespot/Magnetospirillum_magneticum/Magnetospirillum_magneticum_proteins.faa"
  "17|Sulfurimonas_denitrificans|data/genomespot/Sulfurimonas_denitrificans/Sulfurimonas_denitrificans_proteins.faa"
  "18|Nitrosomonas_europaea|data/gapseq/Nitrosomonas_europaea/Nitrosomonas_europaea_proteins.faa"
  "19|Rhodopseudomonas_palustris|data/gapseq/Rhodopseudomonas_palustris/Rhodopseudomonas_palustris_proteins.faa"
  "20|Halobacterium_salinarum|data/gapseq/Halobacterium_salinarum/Halobacterium_salinarum_proteins.faa"
  "21|Syntrophomonas_wolfei|data/gapseq/Syntrophomonas_wolfei/Syntrophomonas_wolfei_proteins.faa"
  "22|Acetobacterium_woodii|data/gapseq/Acetobacterium_woodii/Acetobacterium_woodii_proteins.faa"
  "31|Allochromatium_vinosum|data/gapseq/Allochromatium_vinosum/Allochromatium_vinosum.faa"
  "32|Escherichia_coli|data/genomespot/ecoli/ecoli_proteins.faa"
)

cd "$ROOT"

echo "=== Step 1: Re-run marker BLAST against post-1.5m references ==="
for entry in "${GENOMES[@]}"; do
  IFS='|' read -r gid label proteome <<< "$entry"
  echo "[$gid] $label"
  $PY run_marker_blast.py "$proteome" --genome-id "$gid" 2>&1 \
    | grep -E "^[0-9]+/|markers detected|^  [a-z]" \
    | head -30
  echo ""
done

echo ""
echo "=== Step 2: Generate capability JSON for each ==="
for entry in "${GENOMES[@]}"; do
  IFS='|' read -r gid label proteome <<< "$entry"
  $PY capability_report.py --genome-id "$gid" --json \
    --output "$OUT/phase1_5m_capability/${label}.json" 2>&1
done

echo ""
echo "=== DONE ==="
ls "$OUT/phase1_5m_capability/" | wc -l
