# CultureForge Coverage Map

**Purpose:** Tabular gap analysis. For each metabolism in the master list, classify CultureForge's current detection status and the test-set evidence.

**Date:** 2026-04-30 (post-Phase-3.2).

## Status definitions

- **COVERED** — capability + verified diagnostic markers + at least one organism in test set is correctly classified (or no test-set organism but markers ready)
- **PARTIAL** — capability exists but lineage/architecture coverage incomplete (sub-clade gaps, sparse references, or distinguishing-substrate ambiguity)
- **GAP** — no capability and no diagnostic markers

## Master coverage table

| # | Metabolism | Status | Test-set organism (if any) | Currently classified as | Should be classified as |
|---|---|---|---|---|---|
| **A1** | Aerobic chemoorganotrophy | COVERED | E. coli, Lactobacillus, Thermus, Clostridium, Picrophilus, Acidithiobacillus, etc. (~16/26) | aerobic_chemotrophic / fermentative | matches |
| **A2** | Aerobic ammonia oxidation (AOB) | COVERED | Nitrosomonas europaea | lithotrophic_aerobic | matches |
| **A2'** | Aerobic ammonia oxidation (AOA) | PARTIAL | none in test set | n/a | (Thaumarchaeota AOA divergent amoA may miss) |
| **A3** | **Aerobic nitrite oxidation (NOB)** | **GAP** | **Nitrospira moscoviensis** | **acetogenic (WRONG)** | **lithotrophic_aerobic_nitrite** |
| **A4** | Comammox | GAP | none (test-set Nitrospira is canonical NOB, not comammox) | n/a | comammox |
| **A5** | Aerobic sulfur oxidation (bacterial soxB) | COVERED | Acidithiobacillus, Allochromatium, Sulfurimonas | matches | matches |
| **A6** | Aerobic sulfur oxidation (archaeal Sulfolobales) | COVERED (Phase 3.2) | Sulfolobus acidocaldarius DSM 639 (true negative — genome lacks the enzymes) | aerobic_chemotrophic (correct given gene content) | matches |
| **A7** | Acidophilic Fe(II) oxidation | COVERED | Acidithiobacillus ferrooxidans | matches | matches |
| **A8** | Neutrophilic Fe(II) oxidation | GAP | none | n/a | (would be missed entirely) |
| **A9** | Microaerophilic chemolithotrophy | PARTIAL | Campylobacter jejuni, Sulfurimonas denitrificans | aerobic_chemotrophic / lithotrophic_aerobic with composite atmosphere signal | matches (atmosphere correctly downshifted) |
| **A10** | Aerobic methanotrophy (pmoA, mmoX) | GAP | none | n/a | aerobic_methanotroph |
| **A11** | Aerobic CO oxidation (Mo-CODH) | GAP | none | n/a | (would be missed) |
| **A12** | Aerobic H₂ oxidation (knallgas) | PARTIAL | none in test set as primary mode | n/a | (would detect via hydrogenase + autotrophy markers but no unified capability) |
| **B1** | Denitrification (NO₃⁻ → N₂) | COVERED (Clade I nosZ) | Sulfurimonas, Magnetospirillum (secondary) | matches | matches |
| **B1'** | Denitrification with Clade II nosZ | PARTIAL | none | n/a | LIMITATIONS E.4 |
| **B2** | **DNRA (NO₃⁻ → NH₄⁺)** | **GAP** | none | n/a | DNRA |
| **B3** | Sulfate reduction (canonical) | COVERED | Nitratidesulfovibrio vulgaris | anaerobic_respiratory | matches |
| **B4** | Sulfite-only respiration | PARTIAL | none | (capped at 0.40 by qmoA-essential rule) | matches (correctly excluded from sulfate reduction) |
| **B5** | Sulfur disproportionation | GAP | none | n/a | (indistinguishable from sulfate reduction at marker level) |
| **B6** | Iron(III) reduction (mtrC/omcB) | COVERED | Geobacter sulfurreducens | anaerobic_respiratory | matches |
| **B6'** | Iron(III) reduction non-Geobacter/Shewanella | GAP | none | n/a | LIMITATIONS D.2 |
| **B7** | Manganese(IV) reduction | GAP | none | n/a | Mn reduction (would be silent or detect as iron reduction via shared mtr) |
| **B8** | Selenate respiration | GAP | none | n/a | selenate_respiration |
| **B9** | Arsenate respiration | GAP | none | n/a | arsenate_respiration |
| **B10** | Chlorate/perchlorate respiration | GAP | none | n/a | (per)chlorate_respiration |
| **B11** | Organohalide respiration | COVERED | Dehalococcoides mccartyi | anaerobic_respiratory (via Phase 1.5n override) | matches |
| **B12** | Methanogenesis, hydrogenotrophic | COVERED | Methanocaldococcus jannaschii | methanogenic | matches |
| **B13** | Methanogenesis, aceticlastic | PARTIAL | none in test set | (would detect via mcrA but recipe assumes hydrogenotrophic gas phase) | matches with substrate caveat |
| **B14** | Methanogenesis, methylotrophic / H₂-dependent methylotrophic | PARTIAL | none in test set | (mcrA detection works, substrate variant not distinguished) | matches with substrate caveat |
| **B15** | **ANME (reverse methanogenesis)** | **GAP** | **Methanoperedens nitroreducens (NO₃⁻ acceptor)** | **methanogenic (WRONG direction)** | **ANME-2d** |
| **B16** | Anammox | COVERED (MAG-completeness limited) | Scalindua profunda | fermentative (WRONG — MAG missing hzsA + hdh per LIMITATIONS E.1) | anammox |
| **B17** | N-DAMO (NC10 Methylomirabilis) | GAP | none | n/a | N-DAMO |
| **B18** | Acetogenesis (Wood-Ljungdahl) | COVERED | Acetobacterium woodii | acetogenic | matches |
| **B19** | Hydrogenotrophic denitrification | PARTIAL | (Sulfurimonas overlap) | denitrification + lithotrophic_aerobic | matches partially |
| **B20** | Sulfide-driven autotrophic denitrification | PARTIAL | Sulfurimonas denitrificans | lithotrophic_aerobic | matches |
| **C1** | Anoxygenic phototrophy purple Type II | COVERED | Allochromatium vinosum, Rhodopseudomonas palustris | phototrophic + anaerobic_respiratory | matches |
| **C2** | Anoxygenic phototrophy green sulfur | COVERED | none in test set | n/a (markers ready) | matches |
| **C3** | Anoxygenic phototrophy filamentous (FAP) | COVERED (override) | Chloroflexus aurantiacus | aerobic_chemotrophic primary; phototrophic secondary via Phase 1.5n override at recipe time | matches |
| **C4** | Anoxygenic phototrophy aerobic (AAP) | PARTIAL | none in test set | (would route to anoxygenic_phototrophy_purple → wrong atmosphere) | aerobic anoxygenic phototroph |
| **C5** | Oxygenic phototrophy (cyanobacteria) | COVERED | none in test set | n/a (markers ready) | matches |
| **C6** | Heliobacterial phototrophy (pshA) | GAP | none | n/a | LIMITATIONS B.5 |
| **C7** | Photoferrotrophy | GAP | none | n/a | (would route to anoxygenic_phototrophy without Fe²⁺ as donor) |
| **C8** | Bacteriorhodopsin / proteorhodopsin | COVERED (override) | Halobacterium salinarum | aerobic_chemotrophic primary; halophilic_with_rhodopsin via Phase 1.5n override at recipe time | matches |
| **D1-5** | Fermentation variants | COVERED (broad detector) | E. coli, Lactobacillus, Clostridium, Thermotoga, etc. | fermentative | matches (substrate-specific variants not distinguished, accepted per LIMITATIONS B.2) |
| **E1** | Syntrophy | COVERED | Syntrophomonas wolfei (also Prometheoarchaeum at recipe-time mode pick) | syntrophic | matches |
| **E2** | Cable bacteria EET | GAP | none | n/a | (would be silent) |

## Aggregate counts

| Status | Count | Notes |
|---|---|---|
| COVERED | 17 | (counting variant capabilities as separate where the master list distinguishes them) |
| PARTIAL | 11 | mostly variant-distinguishing or context-routing limitations |
| GAP | 13 | true absence of capability + markers |
| **Total** | **~41** | (some metabolisms in master list collapsed for table) |

## Test-set classification correctness summary

| Outcome | Count | Organisms |
|---|---|---|
| Correct primary mode + correct recipe class | ~21 | E. coli, Lactobacillus, Thermus, Acidithiobacillus, Clostridium, Geobacter, Sulfolobus (true negative for sulfur ox), Campylobacter, Magnetospirillum, Sulfurimonas, Nitrosomonas, Rhodopseudomonas, Halobacterium, Syntrophomonas, Acetobacterium, Chloroflexus, Dehalococcoides, Picrophilus, Thermotoga, Allochromatium, Nitratidesulfovibrio, Methanococcus |
| Wrong primary at detection but correct at recipe-time mode pick | 2 | Prometheoarchaeum (F.3 mitigation), E. coli (facultative-anaerobe rule) |
| Wrong primary, wrong recipe — directly attributable to a GAP | 3 | **Nitrospira moscoviensis** (no nitrite-oxidation capability), **Methanoperedens** (no ANME capability), **Scalindua profunda** (anammox markers can detect but MAG missing them) |

The 3 wrong-recipe organisms map directly to: GAP (NOB), GAP (ANME directional), and a partial-MAG case (Scalindua) where detection logic is sound but proteome is incomplete.

## What this analysis implies for Phase 3 priorities

1. **Canonical nitrite oxidation (A3)** is the single largest gap by both biological frequency and direct test-set impact — Nitrospira moscoviensis is currently misclassified as acetogen with H₂/CO₂ recipe. Adding `lithotrophic_aerobic_nitrite` capability + nxrA marker would be the highest-impact Phase 3 sub-phase.

2. **Aerobic methanotrophy (A10)** is a HIGH-frequency gap with no test-set organism to validate against — but adding pmoA + mmoX markers is straightforward. Since pmoA is sequence-related to amoA, cross-reactivity check is required.

3. **DNRA (B2)** is MEDIUM-HIGH frequency but no test-set organism. Recipe consequence is significant (anaerobic respirer would currently look like aerobic chemoheterotroph).

4. **ANME (B15)** is a directional ambiguity issue rather than a marker-presence issue. mcrA fires correctly; what's missing is a way to distinguish forward vs reverse operation. This is LIMITATIONS F.2 and requires more capability-framework work than marker addition.

5. **Photoferrotrophy (C7)** is LOW-MEDIUM frequency. Specialized but biologically interesting; would need PioABC / FoxEYZ marker curation.

6. **AAP (C4)** is an atmosphere-routing issue rather than a detection gap. Existing pufLM detects AAP organisms but routes them to anaerobic atmosphere. Fix is in recipe composer logic, not marker addition.

7. **Heliobacterial phototrophy (C6)** is LOW frequency. LIMITATIONS B.5 documented; pshA marker addition is straightforward.
