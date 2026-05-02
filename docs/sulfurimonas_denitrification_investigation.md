# Sulfurimonas Denitrification Regression Investigation

Date: 2026-04-26

## Symptom

V5 validation showed Sulfurimonas with only lithotrophic(0.59) as primary mode. Denitrification scored 0.225 (not detected). Earlier versions showed denitrification as co-primary.

## Diagnosis

### Marker check (nosZ)
nosZ BLAST hit exists: sp|P19573|NOSZ_STUST, bitscore 294, pident 32.1%, qcov 71%, positive_call=1.

The hit is genuine but at the moderate credit tier (pident 32.1% < 40% threshold for full credit). It contributes a 1.2x weight boost but does not directly set the pathway step as "found."

### Pathway pattern check
The denitrification pathway definition used enzyme-level patterns (narG, nirS, norB, nosZ) that do not match gapseq's actual pathway names. gapseq names these:
- "nitrate reduction VII (denitrification)" at 60%
- "nitrate reduction IV (dissimilatory)" at 50%
- "nitrate reduction I (denitrification)" at 40%

The old patterns "nitrate reductase.*narG" and "nirS" never matched these names.

### Root cause
Same issue as methanogenesis and acetogenesis from Phase 1.5: enzyme-level gapseq_patterns do not match gapseq's pathway-level naming convention. This was fixed for methanogenesis and acetogenesis but not for denitrification.

## Fix applied

Updated denitrification steps in `pathway_definitions.json` to use gapseq pathway names:
- "nitrate reduction.*denitrification" → matches "nitrate reduction VII (denitrification)"
- "nitrate reduction.*dissimilatory" → matches "nitrate reduction IV (dissimilatory)"

## Result

Denitrification now scores 0.522 (detected) with 2/4 steps found. Sulfurimonas shows both lithotrophic_aerobic(0.59) and anaerobic_respiratory(0.52) as co-primary cultivation modes. This correctly reflects the organism's biology as a sulfur-oxidizing denitrifier.

## Non-regression check

Magnetospirillum magneticum (genome_id=16) also has denitrification pathway genes. The fix should improve its detection too (it had nosZ at 0.548 in earlier versions).
