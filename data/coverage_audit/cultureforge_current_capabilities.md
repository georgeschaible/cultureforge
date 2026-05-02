# CultureForge Current Capability Inventory

**Source:** `data/pathway_definitions.json`, `data/diagnostic_markers/*_refs.fasta`, `genome_diagnostic_markers` table.

**Date:** 2026-04-30 (post-Phase-3.2).

## 17 capabilities defined

| Capability key | Diagnostic markers | Negative markers | Override | Essential AND | Phylogenetic-distribution scope |
|---|---|---|---|---|---|
| `methanogenesis` | mcrA | — | no | no | Methanobacteriales, Methanococcales, Methanopyrales, some Methanosarcinales, partial Methanomassiliicoccales |
| `acetogenesis_wood_ljungdahl` | acsB_cdhC, cooS_cdhA | mcrA, dsrAB, aprAB, mtrC_omcB | no | no (composite) | Acetobacterium, Moorella, Clostridium, Sporomusa |
| `ammonia_oxidation` | amoA, hao | — | no | no | β-/γ-AOB; partial AOA + comammox (LIMITATIONS A.2) |
| `anoxygenic_phototrophy_purple` | pufLM | — | YES (Phase 1.5n) | no | Rhodobacterales, Rhodospirillales, Allochromatium, Chloroflexus (FAP) |
| `anoxygenic_phototrophy_green_sulfur` | pscA_fmoA | — | no | no | Chlorobiaceae |
| `oxygenic_phototrophy` | psaA_psbA | — | no | no | Cyanobacteria |
| `dissimilatory_sulfate_reduction` | aprAB, dsrAB, qmoA | — | no | YES (dsrAB AND qmoA) | Desulfovibrionales, Desulfobacterales, Desulfobulbales, Archaeoglobales |
| `sulfur_oxidation` | soxB, **tqoDoxD, tqoDoxA, tetH, sor** | — | no | no | Bacterial soxB lineages + Sulfolobales (Phase 3.2 archaeal markers) |
| `denitrification` | nosZ | — | no | YES (nosZ Clade I) | Many Pseudomonadota; LIMITATIONS E.4 Clade II gap |
| `iron_ii_oxidation` | cyc2 | — | no | no | Acidithiobacillus, Leptospirillum, Mariprofundus (acidophilic only); LIMITATIONS A.4 neutrophilic gap |
| `iron_iii_reduction` | mtrC_omcB | — | no | no | Geobacteraceae, Shewanellaceae; LIMITATIONS D.2 non-Geobacter/Shewanella gap |
| `bacteriorhodopsin` | rhodopsin | — | YES (Phase 1.5n) | no | Halobacteriales (BR), some marine SAR11 (PR) |
| `nitrogen_fixation` | nifH | — | no | no | nifH Mo-dependent only; LIMITATIONS B.1 vnfH/anfH gap |
| `aerobic_respiration` | (none — pathway scoring + terminal_oxidases marker file) | — | no | no | Universal aerobic |
| `fermentation_mixed` | (none — broad pathway-based) | — | no | no | All glycolysis-bearing organisms (12 of 26 test set per LIMITATIONS B.2) |
| `anammox` | hzsA, hdh | — | no | no | Brocadiaceae; LIMITATIONS E.1 Scalindua MAG-completeness |
| `organohalide_respiration` | rdhA | — | YES (Phase 1.5n) | no | Dehalococcoides, Dehalobacter; LIMITATIONS A.1/D.1 substrate-class ambiguity |

## Reference marker files

27 marker reference FASTA files in `data/diagnostic_markers/`:

```
acsB_cdhC, amoA, aprAB, autotrophy, cooS_cdhA, cyc2, dsrAB, hao,
hdh, hzsA, mcrA, mcrBG, mtrC_omcB, nifH, nosZ, psaA_psbA, pscA_fmoA,
pufLM, qmoA, rdhA, rhodopsin, sor, soxB, terminal_oxidases, tetH,
tqoDoxA, tqoDoxD
```

## Per-test-organism primary cultivation mode (current detection)

| gid | Species | Primary mode | n_detected_caps | Notes |
|---|---|---|---|---|
| 7 | Nitratidesulfovibrio vulgaris | anaerobic_respiratory | 2 | Correct (sulfate reducer) |
| 8 | Methanocaldococcus jannaschii | methanogenic | 1 | Correct |
| 9 | Thermus aquaticus | aerobic_chemotrophic | 1 | Correct |
| 10 | Lactobacillus plantarum | fermentative | 1 | Correct (lactic acid fermentation) |
| 11 | Acidithiobacillus ferrooxidans | aerobic_chemotrophic | 4 | Sulfur ox + Fe ox detected as secondary |
| 12 | Clostridium acetobutylicum | fermentative | 2 | Correct |
| 13 | Geobacter sulfurreducens | anaerobic_respiratory | 2 | Iron(III) reduction detected |
| 14 | Sulfolobus acidocaldarius | aerobic_chemotrophic | 1 | Correct (per Phase 3.2 honest finding — DSM 639 lacks canonical Sulfolobales sulfur oxidation enzymes) |
| 15 | Campylobacter jejuni | aerobic_chemotrophic | 3 | Microaerobic via composite signal |
| 16 | Magnetospirillum magneticum | aerobic_chemotrophic | 3 | Heterotrophy + denitrification |
| 17 | Sulfurimonas denitrificans | lithotrophic_aerobic | 2 | Sulfur ox + denitrification (sulfide-driven autotrophic denitrifier) |
| 18 | Nitrosomonas europaea | lithotrophic_aerobic | 3 | AOB amoA detected |
| 19 | Rhodopseudomonas palustris | anaerobic_respiratory | 5 | Phototroph + denitrifier — multimodal |
| 20 | Halobacterium salinarum | aerobic_chemotrophic | 2 | Halophilic + bacteriorhodopsin |
| 21 | Syntrophomonas wolfei | syntrophic | 1 | Correct |
| 22 | Acetobacterium woodii | acetogenic | 3 | Correct |
| 23 | **Nitrospira moscoviensis** | **acetogenic** | **1** | **WRONG. Should be lithotrophic_aerobic_nitrite. Acetogenesis fires spuriously via gapseq partial WL pathway (F.3 pattern). 5 nxrA paralogs at 94-96% pident invisible to current capability set.** |
| 24 | Chloroflexus aurantiacus | aerobic_chemotrophic | 5 | Phototroph (FAP) detected via Phase 1.5n override |
| 25 | Dehalococcoides mccartyi | anaerobic_respiratory | 2 | Organohalide via Phase 1.5n override |
| 26 | Picrophilus torridus | aerobic_chemotrophic | 2 | Correct (acidophilic heterotroph) |
| 27 | Thermotoga maritima | fermentative | 1 | Correct |
| 28 | **Ca. Methanoperedens nitroreducens** | **methanogenic** | **3** | **WRONG. ANME-2d, runs methanogenesis in reverse with NO₃⁻ acceptor. LIMITATIONS C.1 + F.2.** |
| 29 | Ca. Prometheoarchaeum syntrophicum | methanogenic | 3 | Detection layer raw; recipe composer's F.3 mitigation correctly demotes to syntrophic primary at recipe time |
| 30 | **Ca. Scalindua profunda** | **fermentative** | **2** | **WRONG. Anammox. MAG completeness limits gene detection (LIMITATIONS E.1).** |
| 31 | Allochromatium vinosum | phototrophic | 4 | Phototroph + sulfur oxidation correctly detected |
| 32 | Escherichia coli | fermentative | 2 | Detection raw; recipe composer's facultative-anaerobe rule correctly flips to aerobic_chemotrophic at recipe time |

## Misclassified test-set organisms (V12 score reflects this)

Five organisms produce wrong primary cultivation modes at the detection layer:

| gid | Organism | Wrong | Should be | Documented in |
|---|---|---|---|---|
| 23 | Nitrospira moscoviensis | acetogenic (spurious WL pathway) | lithotrophic_aerobic_nitrite | Pre-Phase-3.3 verification (`nitrospira_verification.md`) |
| 28 | Methanoperedens nitroreducens | methanogenic (forward) | ANME-2d (reverse methanogenesis with NO₃⁻) | LIMITATIONS C.1 + F.2 |
| 30 | Scalindua profunda | fermentative | anammox | LIMITATIONS E.1 (MAG completeness) |
| 18 | Nitrosomonas europaea | lithotrophic_aerobic (correct mode) | (correct) | — |
| Notes: Prometheoarchaeum (gid 29) and E. coli (gid 32) raw detection differs from recipe-time primary mode; recipe composer's F.3 mitigation + facultative-anaerobe rule fix the user-facing output. |

## Capability framework features

- Pathway integrity scoring with weighted steps
- Diagnostic-marker boost (1.5x weight when high-confidence BLAST hit)
- Negative-marker rules (multiplicative penalty)
- Essential-marker AND rules (confidence cap when missing)
- diagnostic_marker_override (Phase 1.5n) for marker-required metabolisms with sparse gapseq pathway annotation
- Recipe-time mode picker (compose_recipe._pick_primary_mode_for_recipe) with: specificity preference (specific over generic), F.3 mitigation (require diagnostic-marker corroboration for marker-required modes), facultative-anaerobe rule
- Multi-source thermal inference with TEMPURA-first priority (Phase 2e G.1 fix)

## Capabilities NOT defined

The following metabolisms have no capability or diagnostic marker:

- Aerobic nitrite oxidation (canonical NOB / nxrAB) — **the largest active gap**
- Comammox (full-length amoA + nxrAB joint detection)
- DNRA (dissimilatory nitrate-to-ammonium / nrfA)
- Aerobic methanotrophy (pmoA / mmoX)
- Aerobic CO oxidation (Mo-CODH / coxL)
- Knallgas autotrophy (aerobic H₂ oxidation as standalone capability — currently inferred from hydrogenase + Calvin)
- Manganese(IV) reduction
- Selenate, arsenate, chlorate/perchlorate respiration
- N-DAMO (Ca. Methylomirabilis)
- ANME reverse methanogenesis (capability category absent — F.2)
- Heliobacterial phototrophy (pshA)
- Photoferrotrophy (PioABC / FoxEYZ)
- Aerobic anoxygenic phototrophy (AAP — pufLM detects but routed wrongly to anaerobic atmosphere)
- Sulfur disproportionation (indistinguishable from sulfate reduction at marker level; capability absent)
- Cable bacteria EET
