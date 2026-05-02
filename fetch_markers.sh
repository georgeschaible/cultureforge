#!/bin/bash
# fetch_markers_v2.sh — download VERIFIED diagnostic marker reference sequences from UniProt
#
# Phase 1.5l: Every accession has been verified against UniProt's actual content.
# Previous version (fetch_markers.sh) had ~50% wrong-protein contamination.
#
# Run this on a machine with internet access:
#   bash fetch_markers_v2.sh
#
# Populates data/diagnostic_markers/ with protein FASTAs for each marker set.

set -euo pipefail

OUTDIR="data/diagnostic_markers"
mkdir -p "$OUTDIR"

fetch_one() {
    local accession=$1
    local output=$2
    echo "  Fetching $accession ..."
    curl -sS "https://rest.uniprot.org/uniprotkb/${accession}.fasta" >> "$output" || \
        echo "  FAILED: $accession for $output" >&2
    sleep 0.5  # rate limit
}

build_ref() {
    local name=$1
    shift
    local outfile="$OUTDIR/${name}_refs.fasta"
    : > "$outfile"
    echo "Building $name ..."
    for acc in "$@"; do
        fetch_one "$acc" "$outfile"
    done
    local n=$(grep -c '^>' "$outfile" 2>/dev/null || echo 0)
    echo "  $name: $n sequences"
}

# ============================================================
# Methanogenesis markers (VERIFIED Phase 1.5l)
# ============================================================

# mcrA — methyl-coenzyme M reductase alpha subunit
# Phase 1.5m: Q58256 (Methanocaldococcus jannaschii) EXCLUDED — dev-set organism.
# Replaced with Q49605 (Methanopyrus kandleri). 5 entries from 4 orders.
# WARNING: Do NOT use P24200 (E. coli McrA restriction enzyme — different protein!)
build_ref mcrA \
    P11558 \
    P07962 \
    Q8THH1 \
    Q49605 \
    P07961

# mcrB + mcrG — beta and gamma subunits
# Phase 1.5m: Q58252/Q58255 (Methanocaldococcus jannaschii) EXCLUDED — dev-set organism.
# Replaced with P12972 (mcrB) + P12973 (mcrG) from Methanothermus fervidus.
# WARNING: Do NOT use P15005 (E. coli McrB restriction enzyme)
build_ref mcrBG \
    P11560 \
    P07955 \
    P12972 \
    P11562 \
    P07964 \
    P12973

# ============================================================
# Acetogenesis (Wood-Ljungdahl) markers (VERIFIED Phase 1.5l)
# ============================================================

# acsB — acetyl-CoA synthase / CODH-ACS alpha subunit (EC 2.3.1.169)
# NOTE: UniProt gene name "acsB" maps to acetyl-CoA synthetase (ligase), NOT synthase.
# Use EC 2.3.1.169 entries instead.
build_ref acsB_cdhC \
    P27988 \
    P27989 \
    P72021 \
    O29868 \
    O27745

# cooS — CO dehydrogenase (EC 1.2.7.4)
# Phase 1.5m: Q58138 (Methanocaldococcus jannaschii) EXCLUDED — dev-set organism.
# Replaced with A0A4P8R3D7 (Methanosarcina mazei).
build_ref cooS_cdhA \
    P31896 \
    O28429 \
    A0A4P8R3D7 \
    Q8TXX3

# ============================================================
# Ammonia oxidation markers (VERIFIED Phase 1.5l)
# ============================================================

# amoA — ammonia monooxygenase subunit A
# Phase 1.5m: Q04507 (Nitrosomonas europaea) EXCLUDED — dev-set organism.
# Replaced with O85076 (Nitrosospira multiformis) + P95336 (Nitrosospira briensis).
# Comammox Nitrospira amoA kept as TrEMBL (N. inopinata + uncultured Nitrospira).
# NOTE: only Q04507 was Swiss-Prot; rest of amoA universe is TrEMBL.
build_ref amoA \
    O85076 \
    P95336 \
    A0A7D4WXT9 \
    A0A8D4WF74

# hao — hydroxylamine oxidoreductase (EC 1.7.2.6 / 1.7.2.9)
# Phase 1.5m: Q50925 (Nitrosomonas europaea) EXCLUDED — dev-set organism.
# Replaced with M5DCM0 (Nitrosococcus oceani) + A0A1I0GQH4 (Nitrosospira multiformis).
build_ref hao \
    M5DCM0 \
    A0A1I0GQH4 \
    Q1PX48

# ============================================================
# Phototrophy markers (VERIFIED Phase 1.5l)
# ============================================================

# pufLM — reaction center L and M subunits (purple bacteria)
# Phase 1.5m: P51762 / P51763 (Allochromatium vinosum) EXCLUDED — dev-set organism.
# Final set: 4α + 4β from Cereibacter, Rhodobacter, Blastochloris, Rhodospirillum.
build_ref pufLM \
    P0C0Y8 \
    P19057 \
    P06009 \
    P10717 \
    P0C0Y9 \
    P11847 \
    P06010 \
    P10718

# pscA + fmoA — green sulfur bacteria reaction center + FMO protein
# NOTE: pscA has no Swiss-Prot or TrEMBL entries found. Using fmoA (FMO protein) only.
# pscC and pscD Swiss-Prot entries exist but are different subunits.
build_ref pscA_fmoA \
    Q46393 \
    Q46135 \
    O07091 \
    Q8KEP5

# psaA + psbA — photosystem I + II (oxygenic, cyanobacteria)
build_ref psaA_psbA \
    P29254 \
    P0A406 \
    P16033 \
    P14660 \
    P51765

# ============================================================
# Sulfur metabolism markers (VERIFIED Phase 1.5l)
# ============================================================

# soxB — thiosulfohydrolase (sulfur oxidation SOX pathway)
# NOTE: Swiss-Prot "soxB" = sarcosine oxidase (WRONG enzyme). All sulfur SoxB are TrEMBL.
build_ref soxB \
    P72177 \
    A0A5C4S040 \
    A0A3D8P969

# dsrAB — dissimilatory sulfite reductase
# Phase 1.5m: D. vulgaris Hildenborough P45574/P45575 EXCLUDED — test set.
# 4 alpha + 4 beta from 4 distinct organisms (3 families) across bacteria + archaea.
build_ref dsrAB \
    Q59109 \
    Q59110 \
    P94693 \
    P94694 \
    A0A7T5VCS7 \
    A0A7T5VCY6 \
    A0A328FC82 \
    A0A328FAA8

# aprAB — adenylyl-sulfate reductase (DISSIMILATORY — gene aprA/aprB).
# Phase 1.5m: expanded for phylogenetic diversity.
# NOTE: Do NOT confuse with assimilatory APS reductase (gene cysH) — different enzyme.
# 3 alpha + 3 beta from 3 distinct organisms across bacteria + archaea.
build_ref aprAB \
    T2G6Z9 \
    T2G899 \
    A0A7J2TKV3 \
    A0A7C3MF07 \
    A0A2G6MT98 \
    A0A2G6MTF3

# qmoA — QmoABC complex subunit A (forward sulfate reduction discriminator)
# Phase 1.5k: D. vulgaris Hildenborough QmoA (Q72CJ9) excluded — test set contamination.
build_ref qmoA \
    Q7X167 \
    A0A8G2C1P1 \
    A0A0U9HMV6 \
    S5VWR0 \
    Q3IBM0 \
    A0A212JYQ4

# ============================================================
# Denitrification markers (VERIFIED Phase 1.5l)
# ============================================================

# nosZ — nitrous oxide reductase (EC 1.7.2.4)
build_ref nosZ \
    P19573 \
    Q51705 \
    Q59105 \
    P94127 \
    Q9HYL2

# ============================================================
# Iron metabolism markers (VERIFIED Phase 1.5l)
# ============================================================

# cyc2 — cytochrome c iron oxidase (acidophilic + neutrophilic Fe(II) oxidizers)
# Phase 1.5m: B7JAQ7 / O33823 (Acidithiobacillus ferrooxidans) EXCLUDED — dev-set organism.
# All cyc2 entries are TrEMBL (no Swiss-Prot for this protein family).
# Replaced with: A. ferrivorans (sister species, monoheme),
# Leptospirillum ferriphilum (acidophile, monoheme),
# Acidihalobacter prosperus (acidophile, multiheme),
# Mariprofundus ferrooxydans PV-1 (neutrophile, multiheme).
build_ref cyc2 \
    A0A060UV08 \
    K4EQ75 \
    B2ZFM8 \
    A0A0H3ZGZ2

# mtrC + omcB — outer membrane cytochromes for Fe(III) reduction
# Phase 1.5m: Q749K5 (Geobacter sulfurreducens omcB) EXCLUDED — dev-set organism.
# Replaced with: E6XFS0 (Shewanella putrefaciens MtrC, full-length 654 aa),
#                A0ABR9NUT4 (Geobacter anodireducens OmcB, full-length 747 aa).
build_ref mtrC_omcB \
    P0DSN4 \
    E6XFS0 \
    A0ABR9NUT4

# ============================================================
# Rhodopsin markers (VERIFIED Phase 1.5l — both correct)
# ============================================================

# Phase 1.5m: P02945 (Halobacterium salinarum bacteriorhodopsin) EXCLUDED — dev-set organism.
# Replaced with Q5UXY6 + Q5V0R5 (Haloarcula marismortui BR-I and BR-II).
build_ref rhodopsin \
    Q5UXY6 \
    Q5V0R5 \
    Q9F7P4

# ============================================================
# Nitrogen fixation markers (VERIFIED Phase 1.5l)
# ============================================================

# nifH — nitrogenase iron protein
build_ref nifH \
    P00459 \
    P00458 \
    P06117 \
    P17303 \
    P22921

# ============================================================
# Autotrophy diagnostic markers (VERIFIED Phase 1.5l)
# ============================================================

# autotrophy — multi-pathway CO2 fixation diagnostic
# Phase 1.5m: expanded to cover four CO2 fixation pathways:
#   rbcL (CBB), aclA (rTCA), mcr (3-hydroxypropionate), 4hbd (3HP/4HB archaeal).
# 6 entries from 6 distinct organisms.
build_ref autotrophy \
    P54205 \
    P00880 \
    P04718 \
    A0A0S4XNU1 \
    A4YEN2 \
    A0A2U9IIH9

# ============================================================
# Anammox markers (PARTIALLY VERIFIED Phase 1.5l)
# ============================================================

# hzsA — hydrazine synthase subunit A
# Only 1 Swiss-Prot entry (Q1Q0T2 from Kuenenia). Rest are TrEMBL Brocadia/Jettenia.
# Phase 1.5m expansion: added Brocadia sinica + Brocadia carolinensis + Jettenia ecosi
# to broaden Brocadiaceae coverage. Anammoxoglobus / Anammoximicrobium have NO UniProt
# entries (documented in REFERENCE_CURATION.md). Scalindua entries excluded by rule.
build_ref hzsA \
    Q1Q0T2 \
    A0A2Z6A915 \
    G9ITI6 \
    G9ITI8 \
    A0A533QHC9 \
    A0A1V4ATP2 \
    A0ABQ0K0A8

# hdh — hydrazine dehydrogenase
# Phase 1.5m: added A0A6G7GWX3 (Kuenenia, longer 642 aa form) for additional diversity.
# Scalindua hdh entries excluded by rule. Anammoxoglobus / Anammoximicrobium lack UniProt entries.
build_ref hdh \
    Q1PW30 \
    Q1PX48 \
    A0A6G7GWX3

# ============================================================
# Organohalide respiration markers (VERIFIED Phase 1.5l — mostly correct)
# ============================================================

# rdhA — reductive dehalogenases
# Phase 1.5m: Q3ZAB8 / Q69GM4 (Dehalococcoides mccartyi) EXCLUDED — blind-set organism.
# Replaced with O68252 (Sulfurospirillum multivorans PceA, Swiss-Prot, distinct genus).
build_ref rdhA \
    Q8L172 \
    O68252 \
    Q8GJ27 \
    Q8GJ31 \
    Q848J2

# ============================================================
# Terminal oxidases (PARTIALLY VERIFIED Phase 1.5l)
# ============================================================

# terminal_oxidases — multi-architecture aerobic respiration diagnostic
# Phase 1.5m: expanded per Phase 1.5l hit_patterns audit.
# Pre-1.5m: only bacterial Cox + Qox + caa3 — missed Sulfolobus, Campylobacter, Sulfurimonas.
# Now spans: bacterial caa3 (Thermus thermophilus), qox (B. subtilis), aa3 (Paracoccus),
# cbb3 (S. meliloti FixN, R. capsulatus), archaeal SoxB (S. solfataricus),
# archaeal QoxA (Acidianus hospitalis). 9 entries.
build_ref terminal_oxidases \
    P82543 \
    P34957 \
    P34956 \
    P08305 \
    P08306 \
    Q05572 \
    P98059 \
    Q97VG9 \
    F4B7C5

# ============================================================
# Phase 3.2 — Archaeal sulfur oxidation markers
# ============================================================
# Sulfolobales archaea use a different toolkit than bacterial soxB:
# - SOR (sulfur oxygenase reductase) — cytoplasmic; lineage-restricted
# - TQO/DoxD + DoxA (thiosulfate:quinone oxidoreductase) — broadly conserved
# - TetH (tetrathionate hydrolase) — extracellular, acidophilic
# All references hand-verified against UniProt (Phase 3.2 Task 2).
# Test-set exclusion: no S. acidocaldarius proteins.
# See data/diagnostic_markers/archaeal_sulfur_oxidation_review.md for biology.

# tqoDoxD — thiosulfate:quinone oxidoreductase, large subunit
# Primary: P97207 = Acidianus ambivalens (Swiss-Prot, Müller et al. 2004)
# Plus Saccharolobus, Sulfurisphaera, Metallosphaera for genus diversity.
build_ref tqoDoxD \
    P97207 \
    Q97XJ3 \
    Q96ZH9 \
    A4YDN8

# tqoDoxA — thiosulfate:quinone oxidoreductase, small subunit (paired with DoxD)
# Primary: P97224 = Acidianus ambivalens (Swiss-Prot)
# Plus Saccharolobus, Sulfurisphaera, Metallosphaera for genus diversity.
build_ref tqoDoxA \
    P97224 \
    Q97XJ4 \
    F9VNN5 \
    A4YDN9

# tetH — tetrathionate hydrolase
# Primary: G8YXZ9 = Acidianus ambivalens tth1 (Swiss-Prot, Protze et al. 2011)
# UniProt coverage outside Acidianus is sparse — this reflects the literature.
build_ref tetH \
    G8YXZ9 \
    F4B6C8 \
    G8YY01

# sor — sulfur oxygenase reductase
# Primary: P29082 = Acidianus ambivalens (Swiss-Prot, Kletzin 1989/1992)
# Sulfolobales-specific to keep marker discriminating for archaeal sulfur oxidation.
# Excludes flanking-region ORFs P29086/P29087/P29088 (wrong proteins).
build_ref sor \
    P29082 \
    Q972K4 \
    Q977W3 \
    A4ZIS7

# ============================================================
# Phase 3.3 — Canonical nitrite oxidation marker
# ============================================================
# nxrA — nitrite oxidoreductase, alpha subunit. Diagnostic for canonical NOB
# (Nitrospira / Nitrobacter / Nitrotoga / Nitrolancea / Nitrococcus lineages).
# Two clades: Type A (cytoplasmic, Nitrospira/Nitrotoga) and Type B (periplasmic,
# Nitrobacter/Nitrolancea). All 8 references hand-verified against UniProt
# (Phase 3.3 Task 2). Test-set exclusion: no Nitrospira moscoviensis NSP M-1
# proteins. UniProt has no Swiss-Prot reviewed nxrA — TrEMBL is the only option.
# Wrong-protein traps excluded: Q3BJV5-Q3BJV9 are 85-100 aa Nitrobacter
# winogradskyi nxrA fragments. See nitrite_oxidation_review.md for biology.
build_ref nxrA \
    A0A0S4KRS1 \
    A0A1W1I298 \
    A0ABM8RCK9 \
    Q3SQW5 \
    Q71RT9 \
    A0A916FC48 \
    A0ABN8AJF8 \
    A0A894Z0L1

# ============================================================
# Phase 3.4 — Dissimilatory nitrate reduction to ammonium (DNRA)
# ============================================================
# nrfA — cytochrome c nitrite reductase, alpha subunit. Diagnostic for
# canonical DNRA via NrfA. Pentaheme architecture: 4 CXXCH + 1 CXXCK
# active-site Lys-coordinated heme. CXXCK motif distinguishes NrfA from
# Otr / HAO / sulfite reductases. 6 references hand-verified against UniProt
# (Phase 3.4 Task 2). Test-set exclusion: no E. coli (P0ABK9), no
# Nitratidesulfovibrio vulgaris Hildenborough (Q72EF3), no Campylobacter.
# Wrong-protein traps excluded: O33732 was suggested in original prompt as
# Sulfurospirillum nrfA but UniProt confirms it is Shewanella frigidimarina
# nitrate reductase (938 aa, NOT nrfA) — replaced with verified Q9Z4P4
# (514 aa, S. deleyianum, Swiss-Prot reviewed). V5Z1T4/Q6ZXS7 are
# fragmentary D. desulfuricans nrfA entries — only the full-length Q8VNU2
# used. See dnra_review.md for biology and threshold rationale.
build_ref nrfA \
    Q9S1E5 \
    Q9Z4P4 \
    Q8EAC7 \
    Q06PW6 \
    B5QZA1 \
    Q8VNU2

# ============================================================
# Phase 3.5 — Aerobic methanotrophy markers (pmoA + mmoX)
# ============================================================
# pmoA: particulate methane monooxygenase α subunit (~247 aa). Three-clade
# protein family: Type I (Gammaproteobacteria), Type II (Alphaproteobacteria),
# Type III (Verrucomicrobia, highly divergent). Dual-clade reference set with
# OR logic catches all three lineages. The pmoA/amoA paralogy is the primary
# cross-reactivity concern: empirical Phase 3.5 scan confirmed amoA caps at
# 50% pident; 60% threshold cleanly separates. See methanotrophy_review.md.
build_ref pmoA \
    Q607G3 \
    A4PDX7 \
    Q50541 \
    O06122 \
    I0JZS9 \
    A9QPD9

# mmoX: soluble methane monooxygenase α subunit (~526 aa). Single tight family,
# 82-99% intra-family conservation across genera. Zero cross-reactivity in the
# 26-organism test set. 50% pident threshold is generous because the family
# is so conserved.
build_ref mmoX \
    P22869 \
    P27353 \
    Q3YA75 \
    Q3T939

# ============================================================
echo ""
echo "=== SUMMARY ==="
for f in "$OUTDIR"/*_refs.fasta; do
    n=$(grep -c '^>' "$f" 2>/dev/null || echo 0)
    echo "  $(basename $f): $n sequences"
done
echo ""
echo "Done. Run build_marker_blast_db.py to build BLAST databases."
