# GenomeSPOT Archaeal Oxygen Prediction Audit

Date: 2026-04-26

## Data

Only 2 archaea have GenomeSPOT predictions in the database:

| Genome ID | Organism | Real O2 tolerance | GenomeSPOT prediction | Confidence | Correct? |
|---|---|---|---|---|---|
| 8 | Methanococcus jannaschii | Strict anaerobe | not tolerant | 0.850 | Yes |
| 14 | Sulfolobus acidocaldarius | Obligate aerobe | not tolerant | 0.944 | **No** |

Blind v2 archaea (no GenomeSPOT run):
- Picrophilus torridus: aerobe (no prediction, not affected)
- Methanoperedens nitroreducens: strict anaerobe (no prediction)
- Prometheoarchaeum syntrophicum: strict anaerobe (no prediction)

## Assessment

GenomeSPOT confidence does not discriminate — the incorrect Sulfolobus prediction (0.944) is MORE confident than the correct Methanococcus prediction (0.850). Confidence-based filtering (Option A) is therefore not viable.

## Decision: Option B

Do not apply GenomeSPOT oxygen predictions as an aerobic respiration disqualifier on archaea. For archaeal genomes, only the obligate-anaerobe-metabolism disqualifier (methanogenesis, sulfate reduction, etc.) is used to suppress aerobic respiration.

Rationale: GenomeSPOT was trained on bacterial data and cannot reliably distinguish archaeal aerobes (Sulfolobus, Halobacterium) from archaeal anaerobes (Methanococcus). With n=2 archaeal samples and a 50% error rate, the prediction is no better than random for archaea.
