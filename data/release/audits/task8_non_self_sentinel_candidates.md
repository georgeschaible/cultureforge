# Task 8 (deferred): non-self sentinel candidates for affected markers

**Status:** Draft / research-only. Task 8 starts AFTER the first hard checkpoint (V12 review). This document captures the verify-at-creation candidate research done while T2 batch processing was running.

**Note on Phase 5.0 overlap:** several candidates here are also in the Phase 5.0 expanded test set (`data/release/phase5_0_genome_list_final.tsv`). This is fine — sentinels and Phase 5.0 evaluation candidates serve different purposes, but the underlying genome only needs to be processed once. Adding such an organism as gid=904+ sentinel "uses up" its Phase 5.0 candidate slot; the eventual Phase 5.0 batch run will skip it via the wrapper's already-registered logic. The biological coverage in the Phase 5.0 evaluation pass is preserved.

## Reference-set composition per affected marker

What's currently in each marker reference (organisms whose proteins ARE in the FASTA):

| Marker | Organisms in reference set |
|---|---|
| mcrA | *Methanothermobacter marburgensis* Marburg; *Methanosarcina barkeri* Fusaro; *Methanosarcina acetivorans* C2A; *Methanopyrus kandleri* AV19; *Methanococcus vannielii* |
| mmoX | *Methylococcus capsulatus* Bath; *Methylosinus trichosporium*; *Methylomonas* sp. GYJ3; *Methylocella silvestris* |
| nrfA | *Wolinella succinogenes* DSM 1740; *Sulfurospirillum deleyianum*; *Shewanella oneidensis* MR-1; *Mannheimia haemolytica*; *Salmonella enteritidis* PT4; *Desulfovibrio desulfuricans* |
| nxrA | *Ca. Nitrospira inopinata*; *Nitrospira japonica*; *Nitrospira defluvii*; *Nitrobacter winogradskyi* Nb-255; *Nitrobacter alkalicus*; *Ca. Nitrotoga fabula*; *Ca. Nitrotoga arctica*; *Nitrolancea hollandica* |
| pmoA | *Methylococcus capsulatus* Bath; *Methylocystis parvus*; *Methylosinus trichosporium*; *Methylocaldum szegediense* (Note: in pmoA refs); *Methylacidiphilum fumariolicum* SolV; *Methylacidiphilum infernorum* V4 |

## Candidate non-self sentinels per affected marker

The candidate organism's protein must NOT appear in the marker reference set, but the organism MUST credibly express the metabolism the marker detects.

### mcrA — candidate: *Methanobrevibacter smithii* ATCC 35061

| Field | Value |
|---|---|
| Verified accession | GCF_000016525.1 |
| Verification | NCBI Datasets: returns "Methanobrevibacter smithii ATCC 35061", strain "ATCC 35061; PS; DSMZ 861", Complete Genome, 1,853,160 bp |
| Reference-set check | `grep -i "Methanobrevibacter" mcrA_refs.fasta` → no match. Genus NOT in reference set. |
| Phase 5.0 overlap | YES (in `phase5_0_genome_list_final.tsv` under category=methane_metabolism). Sentinel addition would consume that Phase 5.0 slot but provide non-self mcrA validation. |
| Cultivation | DSMZ Medium 119; 37°C, pH 7, anaerobic, H2/CO2 substrate. Gut methanogen — different niche from existing reference organisms. |
| Validation expected | mcrA should fire above the 50% override threshold (Methanobrevibacter mcrA is sequence-similar to but distinct from the genera in the reference set). NOT a self-hit. |

### mmoX — candidate: *Methylocystis* sp. SC2 (or *Methylocystis parvus* OBBP if available)

| Field | Value |
|---|---|
| Verified accession | TBD — search needed (Methylocystis parvus OBBP is sometimes deposited; *Methylocystis* sp. SC2 has GCF_000756075.1) |
| Verification | Pending |
| Reference-set check | mmoX refs include *Methylosinus trichosporium* (Type II), *Methylococcus capsulatus* (Type I), *Methylomonas* (Type I), *Methylocella* (Type II Beijerinckiaceae). Methylocystis is also Type II — close phylogenetic match but distinct species. Need to verify exact protein not in refs. |
| Phase 5.0 overlap | Phase 5.0 list has *Methylobacter tundripaludum*, *Methylocaldum szegediense*, *Methylacidiphilum infernorum* in methane_metabolism. *Methylocaldum szegediense* IS in pmoA refs but not in mmoX refs — could work as mmoX-only sentinel. |
| Cultivation | DSMZ Medium varies; 25°C, pH 6, aerobic, CH4 + air |

### nrfA — candidate: *Klebsiella oxytoca* (canonical DNRA-capable enterobacterium)

| Field | Value |
|---|---|
| Verified accession | TBD — search needed |
| Verification | Pending |
| Reference-set check | nrfA refs include *Salmonella enteritidis*, but NOT *Klebsiella*. Pick a Klebsiella whose nrfA isn't in refs. |
| Phase 5.0 overlap | Klebsiella oxytoca is in `phase5_0_genome_list_final.tsv` under nitrogen_metabolism category. |
| Cultivation | DSMZ Medium 1; 37°C, pH 7, facultative anaerobic |

### nxrA — candidate: *Nitrospina gracilis* 3/211 (Nitrospinota phylum, distinct from Nitrospira/Nitrobacter)

| Field | Value |
|---|---|
| Verified accession | GCF_000341545.2 |
| Verification | Confirmed via earlier Phase 5.0 curation lookup |
| Reference-set check | nxrA refs include Nitrospira × 3 + Nitrobacter × 2 + Nitrotoga × 2 + Nitrolancea. *Nitrospina* (different phylum) is NOT in refs. |
| Phase 5.0 overlap | YES — in nitrogen_metabolism category as added during Phase 5.0 curation. |
| Cultivation | Lücker 2013 paper / DSMZ 5928; 28°C, pH 7.5, marine ~2.5% NaCl, aerobic |
| Validation expected | nxrA should fire — but at lower pident than the within-clade refs (different phylum). True generalization test for the dual-clade marker architecture. |

### pmoA — candidate: *Methylobacter tundripaludum*

| Field | Value |
|---|---|
| Verified accession | GCF_002934365.1 |
| Verification | Confirmed via earlier Phase 5.0 curation lookup |
| Reference-set check | pmoA refs include Methylococcus capsulatus, Methylocystis parvus, Methylosinus trichosporium, Methylocaldum szegediense, Methylacidiphilum × 2. *Methylobacter* genus NOT in refs (also Type I Methylococcaceae but different genus). |
| Phase 5.0 overlap | YES — in methane_metabolism category. |
| Cultivation | BacDive 11283 / Wartiainen 2006; 23°C, pH 7, freshwater, aerobic CH4 |
| Validation expected | pmoA should fire (Type I methanotroph) but at sub-100% identity since organism is not the reference. Tundra-cold-adapted strain. |

## Operational plan for Task 8 (when V12 hard checkpoint clears)

When Task 8 is unblocked:

1. **Verify each candidate accession** via `datasets summary genome accession` (re-do the verify step — Rule 1 of VERIFICATION_DISCIPLINE.md).
2. **Confirm reference-set absence** for each candidate's genus + species via `grep -i "OS=<Genus species>" data/diagnostic_markers/<marker>_refs.fasta` returning empty.
3. **Process each candidate through the wrapper** (`cultureforge.py process --input <fna> --accession <acc> --notes "AUDIT RESOLUTION sentinel for <marker> non-self validation"`).
4. **Assign at gid=904+** (next free slot after existing 900-903 sentinels). Document in `data/release/audits/new_sentinel_selections.md`.
5. **Verify each new sentinel produces the expected primary cultivation mode** AND that the marker fires at sub-100% pident (the genuine generalization signal).
6. **Update test-set exclusion list** in `data/diagnostic_markers/REFERENCE_CURATION.md` to include new sentinel gids.
7. **Update Phase 3 sentinel reports** with non-self addendum: existing 900-903 gids reframed as self-recognition; new 904+ gids as non-self generalization.

Estimated time once unblocked: ~3-4 days for 4-5 new sentinels (most of it is gapseq wall time).

## Decisions deferred to V12 hard checkpoint

After V12 review, the user may decide:

- Whether to add all 5 marker non-self sentinels at once, or pick a subset (e.g., just mcrA + pmoA which were the highest-claim Phase 3.5/3.6/3.8 sentinels)
- Whether to use Phase 5.0-overlapping candidates (saves work) or pick organisms outside the Phase 5.0 list (cleaner separation)
- Whether the sentinel pattern should evolve to include both self-recognition (gid 900-903) AND non-self generalization (gid 904+) as standard going forward

These decisions don't block T3/T7 work — Task 8 is downstream of the first hard checkpoint.
