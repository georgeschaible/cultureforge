#!/bin/bash
# Phase 1.5n — re-run capability_report.py on all 26 genomes (18 dev + 8 blind).
# BLAST data unchanged from V9; only the detector logic has the new override rule.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DEV="$ROOT/data/validation/phase1_5n_capability"
OUT_BLIND="$ROOT/data/validation/phase1_5n_blind_capability"
PY="${CULTUREFORGE_PYTHON:-python3}"
mkdir -p "$OUT_DEV" "$OUT_BLIND"

cd "$ROOT"

declare -a DEV=(
  "7|Nitratidesulfovibrio_vulgaris" "8|Methanococcus_jannaschii"
  "9|Thermus_aquaticus" "10|Lactobacillus_plantarum"
  "11|Acidithiobacillus_ferrooxidans" "12|Clostridium_acetobutylicum"
  "13|Geobacter_sulfurreducens" "14|Sulfolobus_acidocaldarius"
  "15|Campylobacter_jejuni" "16|Magnetospirillum_magneticum"
  "17|Sulfurimonas_denitrificans" "18|Nitrosomonas_europaea"
  "19|Rhodopseudomonas_palustris" "20|Halobacterium_salinarum"
  "21|Syntrophomonas_wolfei" "22|Acetobacterium_woodii"
  "31|Allochromatium_vinosum" "32|Escherichia_coli"
)

declare -a BLIND=(
  "23|Nitrospira_moscoviensis" "24|Chloroflexus_aurantiacus"
  "25|Dehalococcoides_mccartyi" "26|Picrophilus_torridus"
  "27|Thermotoga_maritima" "28|Methanoperedens_nitroreducens"
  "29|Prometheoarchaeum_syntrophicum" "30|Scalindua_profunda"
)

echo "=== Dev set (18 organisms) ==="
for entry in "${DEV[@]}"; do
  IFS='|' read -r gid label <<< "$entry"
  $PY capability_report.py --genome-id "$gid" --json --output "$OUT_DEV/$label.json" 2>&1
done

echo ""
echo "=== Blind set (8 organisms) ==="
for entry in "${BLIND[@]}"; do
  IFS='|' read -r gid label <<< "$entry"
  $PY capability_report.py --genome-id "$gid" --json --output "$OUT_BLIND/$label.json" 2>&1
done

echo ""
echo "=== DONE ==="
echo "  Dev:   $(ls $OUT_DEV | wc -l) files"
echo "  Blind: $(ls $OUT_BLIND | wc -l) files"
