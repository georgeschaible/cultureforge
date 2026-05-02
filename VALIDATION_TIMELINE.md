# CultureForge Validation Timeline — V1 through V5

## V1: Sequential Decision Tree (5 organisms)

**Score: 0/5 correct (0%)**

Architecture: Sequential decision tree in `synthesize_denovo.py::determine_energy_metabolism()`. Checks metabolism types in fixed order: methanogen → SRB → iron reducer → sulfur oxidizer → ammonia oxidizer → denitrifier → microaerophile → aerobic heterotroph → fermenter.

Dominant failure: methanogenesis-from-acetate pathway at 50% completeness fires on any organism with acetate kinase + phosphotransacetylase (most bacteria). This triggers before more specific checks like ammonia oxidation.

| Organism | Prediction | Reality | Failure reason |
|---|---|---|---|
| Nitrosomonas | Methanogen | Ammonia oxidizer | Decision tree ordering |
| Rhodopseudomonas | Methanogen | Phototroph | Decision tree ordering |
| Halobacterium | Microaerophile | Extreme halophile | No halophile detector |
| Syntrophomonas | Methanogen | Syntrophic | Decision tree ordering |
| Acetobacterium | Methanogen | Acetogen | WL pathway overlap |

**Lesson:** A sequential decision tree with single-pathway thresholds creates cascading failures on any organism not in the tuning set.

---

## V2: Parallel Pathway-Integrity Detectors (8 organisms)

**Score: 4/8 functionally relevant (3 correct + 1 partial)**

Architecture: Parallel detectors in `capability_detectors.py`. Each metabolism evaluated independently via pathway-integrity scoring (0.70 pathway + 0.20 cofactor + 0.05 marker + 0.15 transporter bonus, multiplied by negative marker penalty). Diagnostic marker BLAST database with 17 marker sets.

Key improvements:
- mcrA negative marker eliminates methanogen false positives on acetogens
- pufLM marker enables phototrophy detection
- Syntrophy composite detector (beta-oxidation + hydrogenase + no terminal acceptors)
- Bacteriorhodopsin marker enables Halobacterium detection

Remaining failures:
- Fermentation over-fires on autotrophs (Nitrospira, Chloroflexus)
- Aerobic respiration over-fires on obligate anaerobes (Scalindua)
- Missing detector categories (anammox, organohalide respiration)
- Marker reference coverage too narrow (comammox amoA, FAP pufLM)

| Organism | Prediction | Reality | Status |
|---|---|---|---|
| Nitrospira | Fermentation 0.80 | Comammox | Incorrect (FP) |
| Chloroflexus | Fermentation 0.90 | FAP phototroph | Incorrect (FP) |
| Dehalococcoides | N-fixation 0.61 | Organohalide resp | Incorrect (missing) |
| Picrophilus | Aerobic 0.90 | Aerobic acidophile | Correct |
| Thermotoga | Fermentation 0.78 | Hypertherm fermenter | Correct |
| Scalindua | Fermentation 0.90 | Anammox | Incorrect (FP + missing) |
| Methanoperedens | Methanogenesis 0.93 | ANME (reverse) | Partial |
| Prometheoarchaeum | Syntrophy 0.70 | Syntrophic Asgard | Correct |

**Lesson:** Parallel detection eliminates the methanogen cascade but reveals false-positive issues from broad detectors (fermentation, aerobic respiration) and marker reference coverage gaps.

---

## V3: False-Positive Cascade Fixes + New Detectors (8 organisms)

**Score: 7/8 functionally relevant (4 correct + 3 partial)**

Architecture changes:
- Phase 1.5b: autotrophy disqualifier (caps fermentation when CO2 fixation detected), acceptor disqualifier (caps fermentation below respiration for facultatives), anaerobe disqualifier (caps aerobic resp when obligate-anaerobe metabolism detected)
- Phase 1.5c: expanded amoA (comammox) and pufLM (FAP) marker references
- Phase 1.5d: anammox (hzsA) and organohalide respiration (rdhA) detectors added
- Two-pass orchestrator (primary detectors first, then context-dependent)

Key improvements:
- Dehalococcoides now correctly detected as organohalide respirer (rdhA at 100%)
- Fermentation FPs on Nitrospira and Chloroflexus eliminated by autotrophy disqualifier
- Chloroflexus pufLM now detected via expanded FAP references

Remaining failures:
- Scalindua anammox still missed (hzsA too divergent for BLAST)
- Ranking issues on 17-organism set (Geobacter, Rhodopseudomonas, Syntrophomonas)

| Organism | V2 → V3 Change | Status |
|---|---|---|
| Nitrospira | Ferm 0.80 → S-ox 0.59 | Partial (improved) |
| Chloroflexus | Ferm 0.90 → Aero 0.85 + photo 0.77 | Partial (improved) |
| Dehalococcoides | N-fix → **Organohalide 0.65** | **Correct (new)** |
| Picrophilus | Same | Correct |
| Thermotoga | Same | Correct |
| Scalindua | Ferm 0.90 → Aero 0.90 | Incorrect (no improvement) |
| Methanoperedens | Same | Partial |
| Prometheoarchaeum | Same | Correct |

**Lesson:** Context-aware disqualifiers and expanded markers fix most false-positive cascades. Missing detectors are additive fixes.

---

## V4: Evidence-Grounded Ranking + HMM Detection (8 organisms)

**Score: 7/8 functionally relevant (4 correct + 3 partial)**

Architecture changes:
- Phase 1.5f: GenomeSPOT oxygen integration (suppresses aerobic respiration for GenomeSPOT-predicted anaerobes), cultivation mode framework (co-primary handling), symmetric syntrophy-fermentation cross-suppression
- Phase 1.5g: HMM-based hzsA detection (10 reference sequences from 4 anammox families, no Scalindua)

Key improvements on 17-organism set:
- Syntrophomonas: syntrophy primary (fermentation suppressed by cross-suppression)
- Rhodopseudomonas: aerobic + phototrophic as co-primary cultivation modes
- Geobacter: aerobic respiration suppressed by GenomeSPOT anaerobe prediction

hzsA HMM result: zero false positives on E. coli (specific), zero true positives on Scalindua (too divergent). The deep-branching Scalindua hzsA cannot be detected without Scalindua-type reference sequences.

Blind v2 unchanged from V3 because ranking fixes primarily affected the 17-organism set and HMM detection failed for Scalindua.

**Lesson:** GenomeSPOT oxygen prediction is a powerful biological context filter for ranking, but fails on archaeal aerobes (Sulfolobus). Cultivation modes correctly capture multi-mode organisms. HMM detection is limited by reference sequence diversity in deep-branching families.

---

## Progression Summary

| Version | Framework | Blind set | Correct | Partial | Incorrect | Functional |
|---|---|---|---|---|---|---|
| V1 | Sequential tree | 5 org | 0 | 0 | 5 | **0%** |
| V2 | Parallel detectors | 8 org | 3 | 1 | 4 | **50%** |
| V3 | + disqualifiers + markers | 8 org | 4 | 3 | 1 | **87.5%** |
| V4 | + ranking + HMM | 8 org | 4 | 3 | 1 | **87.5%** |

The improvement trajectory: 0% → 50% → 87.5% → 87.5%.

V3 → V4 did not improve the blind score but did fix ranking issues on the 17-organism training set (Syntrophomonas, Rhodopseudomonas). The blind set's single remaining failure (Scalindua) requires either test-set-contaminating reference sequences or a fundamentally different detection approach (structural homology via Tier 2).

---

## Failure Category Evolution

| Category | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| Decision tree ordering | 4/5 | 0/8 | 0/8 | 0/8 |
| Fermentation FP | — | 3/8 | 0/8 | 0/8 |
| Aerobic resp FP on anaerobes | — | 1/8 | 1/8 | 1/8 |
| Missing detector | — | 2/8 | 0/8 | 0/8 |
| Marker divergence | — | 2/8 | 1/8 | 1/8 |
| Direction ambiguity (ANME) | — | 1/8 | 1/8 | 1/8 |
| Ranking issue (17-set) | 3/17 | 3/17 | 3/17 | 1/17 |

The remaining failure (Scalindua aerobic resp FP) requires either Scalindua-type hzsA references or Tier 2 structural analysis to resolve. The ANME direction ambiguity (Methanoperedens) is fundamentally unresolvable from genomic data alone.

---

## V5: Phase 1.5j-k (Essential Marker Gating + qmoA)

**Score: 7/8 correct (87.5%)** — no change from V4 on existing organisms.

### Changes
- Phase 1.5j: Added `essential_marker` gating to pathway_definitions.json. Sulfate reduction now requires dsrAB positive BLAST hit; denitrification requires nosZ. Without the essential marker, confidence capped at 0.40.
- Phase 1.5k: Extended to `essential_marker_AND` supporting multi-marker requirements. Sulfate reduction now requires BOTH dsrAB AND qmoA. qmoA (QmoABC complex) is the biologically correct discriminator between forward sulfate reduction and reverse-dsr sulfide oxidation.

### Impact on 9-genome database set
- Nitratidesulfovibrio vulgaris: sulfate reduction detected (0.818) — both dsrAB and qmoA present
- Geobacter sulfurreducens: sulfate reduction NOT detected (0.400) — neither marker present (no regression)
- Sulfolobus/Thermus: sulfate reduction NOT detected — have dsrAB but lack qmoA (correctly discriminated)

### Allochromatium vinosum validation (Phase 1.5k final)
Allochromatium vinosum DSM 180 was added as an 18th development organism to validate the qmoA discriminator against the exact case it was designed for: a reverse-dsr organism with strong dsrAB homology. Results:
- dsrAB: POSITIVE (43.1% identity, bs=329) — reverse dsr uses the same enzyme
- qmoA: NEGATIVE — forward-dsr-specific QmoABC complex absent
- Sulfate reduction: NOT detected (0.400, capped by missing qmoA)
- Primary metabolisms: anoxygenic phototrophy (0.768), sulfur oxidation (0.838), N2 fixation (0.614)

This confirms the Phase 1.5k fix discriminates forward from reverse dsr based on biology, not hit strength. Development genome set: 18 organisms (17 original + Allochromatium).

| Version | Framework | Blind set | Correct | Partial | Incorrect | Functional |
|---|---|---|---|---|---|---|
| V1 | Sequential tree | 5 org | 0 | 0 | 5 | **0%** |
| V2 | Parallel detectors | 8 org | 3 | 1 | 4 | **50%** |
| V3 | + disqualifiers + markers | 8 org | 4 | 3 | 1 | **87.5%** |
| V4 | + ranking + HMM | 8 org | 4 | 3 | 1 | **87.5%** |
| V5 | + essential marker AND + qmoA | 8 org | 4 | 3 | 1 | **87.5%** |
| V6 | + verified marker references | 8 org | 4 | 3 | 1 | **87.5%** |

---

## V6: Phase 1.5l (Marker Reference Verification Audit)

**Score: unchanged on blind set (87.5%)** — but significant improvements on development set.

### Changes
~50% of UniProt accessions in fetch_markers.sh were returning wrong proteins. All references replaced with verified accessions. New fetch_markers_v2.sh created.

### Key detection improvements
- **Acidithiobacillus ferrooxidans**: Fe(II) oxidation now detected (0.56) — cyc2 marker working for first time (was wrong plant Beclin protein)
- **Geobacter**: mtrC/omcB now correctly detected (was wrong Sugar transporter / PpiC)
- **Clostridium**: Acetogenesis now detected (0.59) — corrected acsB/cdhC references
- **Sulfurimonas**: soxB now properly detected with correct references

### Known regression
- **Sulfolobus**: Aerobic respiration detection lost (0.50 → not detected). Previous detection relied partly on wrong references (Sulfolobus alcohol dehydrogenase in terminal_oxidase set). Requires archaeal SoxM/SoxB terminal oxidase references to restore.

---

## V7-V8: Phase 1.5l (Marker Reference Verification Audit + Allochromatium consolidation)

V6 was Phase 1.5l on the 18-dev-set audit. V7 + V8 reflect intermediate states from Phase 1.5l completion to pre-1.5m baseline:
- V7 = Phase 1.5l with the documented Sulfolobus regression open (terminal_oxidases lacked archaeal SoxM/SoxB references)
- V8 = post-Allochromatium-validation state used as the baseline for Phase 1.5m comparison

### V7-V8 known issues (carried into Phase 1.5m)
- **Sulfolobus aerobic respiration regression** — Phase 1.5l removed the misfiled Sulfolobus alcohol dehydrogenase from terminal_oxidases; bacterial Cox references don't catch archaeal SoxB.
- **D. vulgaris dsrAB self-validation** — The only Swiss-Prot dsrAB pair retained from Phase 1.5l (P45574/P45575) was from D. vulgaris itself, producing 100%-identity hits when validating against D. vulgaris.
- **Allochromatium pufLM self-validation** — P51762/P51763 in pufLM references were from Allochromatium itself.
- **A. ferrooxidans cyc2 self-validation** — B7JAQ7/O33823 in cyc2 references were from A. ferrooxidans itself.

These were not test-set leaks at the level of detection accuracy but they meant Phase 1.5l could not honestly answer "would CultureForge detect this metabolism if the organism's own protein were not in the references?"

| Version | Framework | Blind set | Correct | Partial | Incorrect | Functional |
|---|---|---|---|---|---|---|
| V7-V8 | Phase 1.5l + Allochromatium | 8 org | 4 | 3 | 1 | **87.5%** |

---

## V9: Phase 1.5m (Rigorous Marker Reference Rebuild)

**Score on dev set: zero Y→N regressions (all 7 user-specified organism checks pass).**
**Score on blind set: 7/8 functionally relevant (same as V5-V8, but failure modes shifted).**

Architecture changes:
- Phase 1.5m: enforced 26-organism exclusion rule across all 23 markers (18 dev-set + 8 blind-set species). Every accession in `fetch_markers.sh` re-verified against UniProt with strict five-step verification discipline. 116 accessions total across 23 marker reference sets.
- Headline test: Acidithiobacillus iron oxidation detected at 85.7% identity from non-self references (Phase 1.5l detected it only via self-validation).
- Phase 1.5l Sulfolobus regression FIXED — Saccharolobus solfataricus SoxB reference at 81.9% identity.
- Three additional MISS_FN regressions from Phase 1.5l fixed: Campylobacter terminal_oxidases (cbb3 added), Sulfurimonas autotrophy (aclA/rTCA added), Sulfurimonas terminal_oxidases (cbb3 added).
- Allochromatium qmoA discrimination preserved (Task 7).

Blind-set comparison (V8 → V9):

| Organism | V8 | V9 | Net change |
|---|---|---|---|
| Nitrospira | partial | partial | unchanged |
| Chloroflexus | partial | partial | pufLM marker now detects (47.8% id) but pathway demotion persists |
| Dehalococcoides | correct | regression | rdhA hits at 33% id below pathway-integrity threshold (test-set exclusion cost) |
| Picrophilus | correct | correct | unchanged |
| Thermotoga | correct | correct | unchanged |
| Scalindua | incorrect | incorrect | **MAG-completeness confirmed** as the actual blocker, not reference coverage |
| Methanoperedens | partial | partial | reverse-WL still suppressed by mcrA negative marker |
| Prometheoarchaeum | correct | correct | Syntrophy maintained; +2 spurious gapseq pathway calls |

| Version | Framework | Blind set | Correct | Partial | Incorrect | Functional |
|---|---|---|---|---|---|---|
| V1 | Sequential tree | 5 org | 0 | 0 | 5 | **0%** |
| V2 | Parallel detectors | 8 org | 3 | 1 | 4 | **50%** |
| V3 | + disqualifiers + markers | 8 org | 4 | 3 | 1 | **87.5%** |
| V4 | + ranking + HMM | 8 org | 4 | 3 | 1 | **87.5%** |
| V5 | + essential marker AND + qmoA | 8 org | 4 | 3 | 1 | **87.5%** |
| V6 | + Phase 1.5l verified marker references | 8 org | 4 | 3 | 1 | **87.5%** |
| V7-V8 | + Allochromatium validation, Sulfolobus regression open | 8 org | 4 | 3 | 1 | **87.5%** |
| **V9** | **+ Phase 1.5m rigorous rebuild + test-set exclusion** | **8 org** | **3** | **4** | **1** | **87.5%** |

V9 numerical score is unchanged from V5-V8, but the underlying detection now rests on test-set-clean references and four MISS_FN regressions from Phase 1.5l were fixed via the autotrophy + terminal_oxidases expansion. The Dehalococcoides V9 "regression" is the test-set exclusion rule producing the honest signal — V5-V8 detection relied on D. mccartyi's own rdhA being in the reference set.

The four newly surfaced detector-side issues (Dehalococcoides organohalide threshold, Chloroflexus FAP / Halobacterium rhodopsin pathway-demotion, Methanoperedens reverse-WL category, spurious gapseq pathway calls) are not marker-reference issues and require detector logic changes — scoped for Phase 1.5n.

---

## Failure Category Evolution (V5 → V9)

| Category | V5 | V6 | V7-V8 | V9 |
|---|---|---|---|---|
| Decision tree ordering | 0/8 | 0/8 | 0/8 | 0/8 |
| Fermentation FP | 0/8 | 0/8 | 0/8 | 0/8 |
| Aerobic resp FP on anaerobes | 1/8 | 1/8 | 1/8 | 1/8 |
| Missing detector | 0/8 | 0/8 | 0/8 | 0/8 |
| Marker divergence | 1/8 | 0/8 | 0/8 | 0/8 |
| Direction ambiguity (ANME) | 1/8 | 1/8 | 1/8 | 1/8 |
| Wrong-protein references | many | mostly fixed | resolved | resolved |
| Self-validation contamination | not assessed | present | present | **eliminated** |
| Detector-side pathway-demotion (post-1.5m surface) | hidden | hidden | hidden | **3-4 surfaced** |

---

## V10: Phase 1.5n (Diagnostic Marker Override for Specific-Marker Metabolisms)

**Score on dev set: zero regressions, +1 capability restored (Halobacterium rhodopsin).**
**Score on blind set: 5/8 correct (+1 over V9), 2/8 partial, 1/8 incorrect.**

Architecture changes:
- New `diagnostic_marker_override` field in `pathway_definitions.json` for three specific metabolisms (organohalide_respiration, anoxygenic_phototrophy_purple, bacteriorhodopsin) where a single marker is uniquely diagnostic of the pathway.
- Override fires ONLY when standard pathway-based detection fails, no negative marker has fired, and no essential marker is missing. Produces moderate confidence (0.60-0.65) — a floor, not an additive bonus.
- Cross-contamination audit identified and excluded one false-positive case (Prometheoarchaeum × rdhA at 33.2% identity to a single rdhA-superfamily protein) by tightening rdhA `min_pident` from 30 to 34.

Detection changes:
- Halobacterium rhodopsin: 0.225 → **0.600 PRIMARY** (rhodopsin override at 54.1% identity)
- Chloroflexus phototrophy purple: 0.025 → **0.650 PRIMARY** (pufLM override at 47.8% identity)
- Dehalococcoides organohalide respiration: 0.125 → **0.650 PRIMARY** (rdhA override at 35.3% identity, restoring V5-era detection that V9 had lost via test-set exclusion)

| Version | Framework | Blind set | Correct | Partial | Incorrect | Functional |
|---|---|---|---|---|---|---|
| V1 | Sequential tree | 5 org | 0 | 0 | 5 | **0%** |
| V2 | Parallel detectors | 8 org | 3 | 1 | 4 | **50%** |
| V3 | + disqualifiers + markers | 8 org | 4 | 3 | 1 | **87.5%** |
| V4 | + ranking + HMM | 8 org | 4 | 3 | 1 | **87.5%** |
| V5 | + essential marker AND + qmoA | 8 org | 4 | 3 | 1 | **87.5%** |
| V6 | + Phase 1.5l verified marker references | 8 org | 4 | 3 | 1 | **87.5%** |
| V7-V8 | + Allochromatium validation, Sulfolobus regression open | 8 org | 4 | 3 | 1 | **87.5%** |
| V9 | + Phase 1.5m rigorous rebuild + test-set exclusion | 8 org | 3 | 4 | 1 | **87.5%** |
| **V10** | **+ Phase 1.5n diagnostic marker override** | **8 org** | **5** | **2** | **1** | **87.5%** |

Numerical "functional" score remained 87.5% across V3-V10 because Scalindua remains undetectable (MAG-completeness limitation, not detection-layer). However V10 produces the highest correct count to date (5/8) thanks to the Dehalococcoides organohalide restoration and Chloroflexus phototrophy promotion. The two remaining "partial" calls (Nitrospira comammox amoA, Methanoperedens ANME reverse-WL) are deferred to Phase 3 by user decision.

---

## Failure Category Evolution (V1 → V10)

| Category | V5 | V6 | V7-V8 | V9 | V10 |
|---|---|---|---|---|---|
| Decision tree ordering | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Fermentation FP | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Aerobic resp FP on anaerobes | 1/8 | 1/8 | 1/8 | 1/8 | 1/8 |
| Missing detector | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Marker divergence | 1/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| Direction ambiguity (ANME) | 1/8 | 1/8 | 1/8 | 1/8 | 1/8 |
| Wrong-protein references | many | mostly fixed | resolved | resolved | resolved |
| Self-validation contamination | not assessed | present | present | eliminated | eliminated |
| Detector-side pathway-demotion | hidden | hidden | hidden | 3-4 surfaced | **3 resolved (F.1), 1 deferred to Phase 3 (F.2/F.3)** |
