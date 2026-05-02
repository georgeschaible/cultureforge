#!/bin/bash
# Run gapseq on all 10 validation genomes, 2 at a time.
# Then run fast analyses (GenomeSPOT + MeBiPred + prodigal).
set -e

source "$(conda info --base)/etc/profile.d/conda.sh"
PROJ="$(cd "$(dirname "$0")" && pwd)"
GENOMES=$PROJ/data/genomes

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

# For archaea, gapseq needs -m Archaea
declare -A DOMAIN
DOMAIN[Methanococcus_jannaschii]="Archaea"
DOMAIN[Sulfolobus_acidocaldarius]="Archaea"

run_gapseq_one() {
  local name=$1
  local genome=$GENOMES/${name}.fasta
  local work=$PROJ/data/gapseq/${name}
  local domain=${DOMAIN[$name]:-Bacteria}

  if [ -f "$work/${name}.RDS" ] || [ -f "$work/${name}.xml" ]; then
    echo "[SKIP] $name — already complete"
    return 0
  fi

  mkdir -p "$work"
  cd "$work"

  echo "[START] $name (domain=$domain) at $(date)"

  conda activate gapseq

  gapseq find -p all -b 200 -m "$domain" "$genome" 2>&1 | tail -3

  PREFIX=$(ls *-all-Pathways.tbl 2>/dev/null | sed 's/-all-Pathways.tbl//' | head -1)
  if [ -z "$PREFIX" ]; then echo "[ERROR] $name: no Pathways.tbl"; return 1; fi

  gapseq find-transport -b 200 "$genome" 2>&1 | tail -3

  gapseq draft -r "${PREFIX}-all-Reactions.tbl" \
               -t "${PREFIX}-Transporter.tbl" \
               -c "$genome" \
               -p "${PREFIX}-all-Pathways.tbl" \
               -b auto 2>&1 | tail -3

  GAPSEQ_DAT=$(dirname $(which gapseq))/../share/gapseq/dat
  ALLMED="$GAPSEQ_DAT/media/ALLmed.csv"

  gapseq fill -m "${PREFIX}-draft.RDS" \
              -n "$ALLMED" \
              -c "${PREFIX}-rxnWeights.RDS" \
              -g "${PREFIX}-rxnXgenes.RDS" 2>&1 | tail -10

  echo "[DONE] $name at $(date)"
}

# Run in pairs to limit RAM usage
for ((i=0; i<${#ORGS[@]}; i+=2)); do
  org1=${ORGS[$i]}
  org2=${ORGS[$i+1]:-}

  echo "=== BATCH: $org1 + $org2 ==="

  run_gapseq_one "$org1" &
  PID1=$!

  if [ -n "$org2" ]; then
    run_gapseq_one "$org2" &
    PID2=$!
    wait $PID1 $PID2
  else
    wait $PID1
  fi
done

echo "=== ALL GAPSEQ COMPLETE ==="
echo "Now run fast analyses (GenomeSPOT + MeBiPred)"

# Fast analyses
conda activate genomespot

for name in "${ORGS[@]}"; do
  genome=$GENOMES/${name}.fasta
  gsdir=$PROJ/data/genomespot/${name}
  mbdir=$PROJ/data/mebipred/${name}

  mkdir -p "$gsdir" "$mbdir"

  # Prodigal
  if [ ! -f "$gsdir/${name}_proteins.faa" ]; then
    echo "[PRODIGAL] $name"
    prodigal -i "$genome" -a "$gsdir/${name}_proteins.faa" -o /dev/null -f gff -p single 2>/dev/null
  fi

  # Clean proteins for MeBiPred
  if [ ! -f "$mbdir/${name}_proteins_clean.faa" ]; then
    python3 -c "
from Bio import SeqIO
with open('$mbdir/${name}_proteins_clean.faa','w') as out:
    for r in SeqIO.parse('$gsdir/${name}_proteins.faa','fasta'):
        out.write(f'>{r.id}\n{str(r.seq).replace(\"*\",\"\")}\n')
"
  fi

  # GenomeSPOT
  if [ ! -f "$gsdir/${name}.predictions.tsv" ]; then
    echo "[GENOMESPOT] $name"
    python -m genome_spot.genome_spot \
      --contigs "$genome" \
      --proteins "$gsdir/${name}_proteins.faa" \
      --output-prefix "$gsdir/${name}" \
      --models "$PROJ/vendor/GenomeSPOT/models" 2>&1 | tail -3
  fi

  # MeBiPred
  if [ ! -f "$mbdir/${name}_predictions.tsv" ]; then
    echo "[MEBIPRED] $name"
    cd "$PROJ"
    python run_mebipred.py "$mbdir/${name}_proteins_clean.faa" "$mbdir/${name}_predictions.tsv" 2>&1 | tail -3
  fi

  # Hydrogenase BLAST
  hdir=$PROJ/data/hydrogenase
  if [ ! -f "$hdir/${name}_hits.tsv" ]; then
    echo "[HYDROGENASE] $name"
    blastp -query "$mbdir/${name}_proteins_clean.faa" \
           -db "$hdir/hydrogenase_ref" \
           -outfmt "6 qseqid sseqid pident length evalue bitscore" \
           -evalue 1e-20 -max_target_seqs 3 -num_threads 4 \
           -out "$hdir/${name}_hits.tsv" 2>/dev/null
  fi
done

echo "=== ALL FAST ANALYSES COMPLETE ==="
