# Sentinel Organisms for Phase 3 Gaps

**Purpose:** For each top-priority gap, identify a well-characterized type-strain "sentinel" organism that performs the metabolism. The list informs future test-set expansion (NOT in this audit; documentation only).

**Date:** 2026-04-30. NCBI assembly availability verified by direct esummary lookup.

## Sentinel table

| # | Metabolism (priority) | Sentinel organism | Strain | NCBI assembly | Status |
|---|---|---|---|---|---|
| 1 | Canonical nitrite oxidation (P1) | *Nitrobacter winogradskyi* | Nb-255 | GCF_000012725.1 | Complete Genome |
| 2 | Canonical nitrite oxidation (P1) | *Nitrobacter hamburgensis* | X14 | GCF_000013805.1 | Complete Genome |
| 3 | Comammox (P8 / bundle with P1) | *Ca.* Nitrospira inopinata | (type strain) | GCF_001458695.1 | Complete Genome |
| 4 | Aerobic methanotrophy (P2) | *Methylococcus capsulatus* | Bath | GCF_000008325.1 | Complete Genome |
| 5 | Aerobic methanotrophy (P2) | *Methylosinus trichosporium* | OB3b | GCF_001644205.1 | Complete Genome |
| 6 | DNRA (P3) | *Wolinella succinogenes* | DSM 1740 | GCF_000196135.1 | Complete Genome |
| 7 | DNRA (P3) | *Sulfurospirillum deleyianum* | DSM 6946 | GCF_000168475.1 | Complete Genome |
| 8 | ANME (P4) | *Ca.* Methanoperedens nitroreducens | (already in test set, gid 28) | GCA_000315995.1 | already loaded |
| 9 | Photoferrotrophy (P6) | *Rhodopseudomonas palustris* | TIE-1 | GCF_000020445.1 | Complete Genome |
| 10 | Photoferrotrophy (P6) | *Chlorobium ferrooxidans* | KoFox | GCF_000020525.1 | Complete Genome |
| 11 | Heliobacterial phototrophy (P7) | *Heliomicrobium modesticaldum* (formerly *Heliobacterium*) | Ice1 | GCF_000019165.1 | Complete Genome |
| 12 | Sulfide-driven autotrophic denitrification (B20) | *Thiobacillus denitrificans* | ATCC 25259 | GCF_000012745.1 | Complete Genome |
| 13 | Manganese / iron reduction (B6'/B7) | *Shewanella oneidensis* | MR-1 | GCF_000146165.1 | Chromosome |
| 14 | Neutrophilic Fe(II) oxidation (P10 / A8) | *Mariprofundus ferrooxydans* | PV-1 | GCF_000153765.1 | Scaffold |
| 15 | Neutrophilic Fe(II) oxidation | *Sideroxydans lithotrophicus* | ES-1 | GCF_000025705.1 | Complete Genome |
| 16 | Chlorate / perchlorate respiration (B10) | *Dechloromonas aromatica* | RCB | GCA_004555545.1 | Contig |
| 17 | N-DAMO (B17) | *Ca.* Methylomirabilis oxygeniifera | (type) | GCA_979680375.1 | Complete Genome |
| 18 | Cable bacteria (E2) | *Ca.* Electrothrix communis | (uncultured, environmental) | not in NCBI assembly DB as a single organism | n/a (specialty MAGs only) |

## Notes per sentinel

### Canonical NOB sentinels

- *Nitrobacter winogradskyi* Nb-255 (GCF_000012725.1) — type-strain α-proteobacterial NOB. Encodes nxrAB. Established cultivation in DSMZ Medium 756.
- *Nitrobacter hamburgensis* X14 — second sentinel for genus diversity. Includes facultative mixotrophic growth on pyruvate.
- *Ca.* Nitrospira inopinata (GCF_001458695.1) — type-strain comammox. Encodes both amoCAB and nxrAB; would validate the comammox+canonical detection logic.

### Methanotroph sentinels

- *Methylococcus capsulatus* Bath (GCF_000008325.1) — Type I methanotroph (γ-proteobacteria). Encodes both pmoA (particulate MMO) and mmoX (soluble MMO). Most commonly cited methanotroph type strain.
- *Methylosinus trichosporium* OB3b (GCF_001644205.1) — Type II methanotroph (α-proteobacteria, Methylocystaceae). Adds genus diversity.

### DNRA sentinels

- *Wolinella succinogenes* DSM 1740 (GCF_000196135.1) — Epsilonproteobacterium, classical DNRA model organism. Encodes nrfA (cytochrome c nitrite reductase, the diagnostic terminal-step marker).
- *Sulfurospirillum deleyianum* DSM 6946 — second sentinel; Epsilonproteobacterium, also DNRA + sulfur-respiration capable.

### Photoferrotroph sentinels

- *Rhodopseudomonas palustris* TIE-1 (GCF_000020445.1) — purple-bacterial photoferrotroph; encodes PioABC (Calvin + Fe²⁺-oxidizing system).
- *Chlorobium ferrooxidans* KoFox (GCF_000020525.1) — green-sulfur-bacterial photoferrotroph; FoxEYZ system (distinct architecture).

### Cable bacteria

- *Ca.* Electrothrix and *Ca.* Electronema are environmental MAGs; no single high-quality reference assembly currently. NCBI hosts MAG-derived sequences but not a clean reference genome. Phase 3 work on cable bacteria deferred until a reference genome quality threshold improves.

## Recommended near-term test-set additions (if user wants empirical Phase 3 validation)

If the user wants to validate Phase 3 fixes against real organisms (not just gene-content theory), the highest-value additions would be:

1. *Nitrobacter winogradskyi* Nb-255 — validates Phase 3.3 NOB fix on a non-Nitrospira lineage
2. *Methylococcus capsulatus* Bath — validates Phase 3.4 methanotroph addition
3. *Wolinella succinogenes* DSM 1740 — validates Phase 3.5 DNRA addition

All three are GCF Complete Genome assemblies with well-characterized phenotypes and standard cultivation media. Adding to test set would cost ~3 hours per organism (download genome → run gapseq → run GenomeSPOT/MeBiPred → load into DB). All can wait — current 26-organism set is sufficient for Phase 3.3-3.5 development; sentinels are useful only as post-hoc validation.

**This document is reference material. No organisms are being added to the test set.**
