# CultureForge Blind Validation V2 — 8 Novel Organisms

Date: 2026-04-26
Framework: Phase 1.5 parallel pathway-integrity detectors
Protocol: All 8 organisms processed with NO user overrides and NO biology lookup until all profiles were generated. Real biology compared only after all 8 were complete.
gapseq flags: -b 200 -t Bacteria or -t Archaea as appropriate
Total gapseq compute: ~65 hours (sequential, 8 organisms)

---

## Summary

| # | Organism | Top-1 capability | Conf | Real metabolism | Assessment |
|---|---|---|---|---|---|
| 1 | Nitrospira moscoviensis | Fermentation | 0.80 | Comammox (complete ammonia oxidation) | **Incorrect** |
| 2 | Chloroflexus aurantiacus | Fermentation | 0.90 | FAP anoxygenic phototrophy + 3HP bicycle | **Incorrect** |
| 3 | Dehalococcoides mccartyi | N fixation | 0.61 | Organohalide respiration | **Incorrect** |
| 4 | Picrophilus torridus | Aerobic respiration | 0.90 | Aerobic heterotroph (extreme acidophile) | **Correct** |
| 5 | Thermotoga maritima | Fermentation | 0.78 | Hyperthermophilic fermenter | **Correct** |
| 6 | Ca. Scalindua profunda | Fermentation | 0.90 | Anammox | **Incorrect** |
| 7 | Ca. Methanoperedens nitroreducens | Methanogenesis | 0.93 | ANME (reverse methanogenesis) | **Partially correct** |
| 8 | Ca. Prometheoarchaeum syntrophicum | Syntrophy | 0.70 | Syntrophic amino acid oxidizer | **Correct** |

**Primary capability correct: 3/8 (37.5%)**
**Partially correct (right enzymes, wrong direction): 1/8 (12.5%)**
**Incorrect: 4/8 (50%)**

---

## Detailed Assessment

### 1. Nitrospira moscoviensis — Comammox

**CultureForge prediction:** Fermentation (0.80), sulfur oxidation (0.59)
**Reality:** Complete ammonia oxidation (comammox) — performs both ammonia oxidation (amoABC, hao) and nitrite oxidation (nxrAB) in a single organism. Obligate autotroph.
**Ammonia oxidation detector score:** 0.325 (not detected)

**Why it failed:** The amoA reference sequences in the marker database are from beta-proteobacterial ammonia oxidizers (Nitrosomonas, Nitrosospira). Nitrospira is in a different phylum (Nitrospirota). Its amoA is too divergent (<30% identity to the references) to pass the BLAST threshold. Additionally, CultureForge has no nitrite oxidation (nxrAB) detector at all.

**Category:** Failed due to marker database coverage gap. The detector logic is sound but the reference sequences are too narrow. Fix: add comammox-type amoA sequences from Nitrospira inopinata and Ca. Nitrospira nitrosa.

---

### 2. Chloroflexus aurantiacus — FAP Phototroph

**CultureForge prediction:** Fermentation (0.90), aerobic respiration (0.85), acetogenesis (0.64)
**Reality:** Filamentous anoxygenic phototroph (FAP) with Type II reaction center. Also uses 3-hydroxypropionate (3HP) bicycle for carbon fixation. Grows photoheterotrophically under anoxic conditions or chemoheterotrophically in the dark.
**Purple phototrophy detector score:** Not in primary capabilities (likely <0.50)

**Why it failed:** Chloroflexus has Type II reaction centers homologous to purple bacteria (pufLM), but its sequences are sufficiently divergent that the pufLM BLAST marker did not reach the 40%/300 bitscore threshold. The 3HP bicycle is not represented in any pathway definition.

**What was partially correct:** Aerobic respiration (0.85) is correct. Chloroflexus can grow aerobically as a chemoheterotroph. The acetogenesis call (0.64) is a false positive from CODH/ACS genes used for the 3HP carbon fixation.

**Category:** Failed due to marker sequence divergence (pufLM) and missing pathway definition (3HP bicycle).

---

### 3. Dehalococcoides mccartyi — Organohalide Respirer

**CultureForge prediction:** Nitrogen fixation (0.61)
**Reality:** Obligate organohalide-respiring bacterium. Uses reductive dehalogenases (rdhA) to respire chlorinated ethenes (PCE, TCE, DCE, vinyl chloride) as terminal electron acceptors. Minimal genome (1.47 Mb), highly specialized.
**No organohalide detector exists.**

**Why it failed:** Reductive dehalogenation (rdhA) is not in the detector set. This was expected and documented as a known gap before blind validation. The nitrogen fixation call (0.61) is from nifH homologs that may be genuine (some Dehalococcoides strains fix nitrogen).

**Category:** Failed due to missing detector category. Expected outcome.

---

### 4. Picrophilus torridus — Extreme Acidophile (pH 0.7)

**CultureForge prediction:** Aerobic respiration (0.90), fermentation (0.73)
**Reality:** Aerobic heterotrophic archaeon that grows optimally at pH 0.7 and 60C. The most acidophilic organism known. Metabolizes sugars and yeast extract aerobically.

**Assessment:** Aerobic respiration is correct. The cbb3 oxidase complex was detected, TCA cycle at 88%, and cytochrome c oxidase hits confirmed the respiratory chain. Fermentation (0.73) as secondary is also plausible since Picrophilus can ferment sugars. The extreme acidophily (pH 0.7) is not captured by any detector since we have no pH-based capability classification, but GenomeSPOT would predict low pH if run.

**Category:** Correct for primary metabolism. Acidophily not captured (out of scope for capability detectors).

---

### 5. Thermotoga maritima — Hyperthermophilic Fermenter

**CultureForge prediction:** Fermentation (0.78)
**Reality:** Hyperthermophilic bacterium growing at 80C. Ferments sugars to H2, CO2, and acetate. One of the most efficient bacterial H2 producers known.

**Assessment:** Correct. The fermentation detector identified 7/9 pathway steps including glycolysis, pyruvate fermentation to ethanol/acetate/acetoin/butanoate. The organism's primary metabolism is fermentation. Hyperthermophily is not captured by the capability detectors (would require GenomeSPOT temperature prediction).

**Category:** Correct.

---

### 6. Ca. Scalindua profunda — Anammox

**CultureForge prediction:** Fermentation (0.90), aerobic respiration (0.90)
**Reality:** Anaerobic ammonium-oxidizing (anammox) planctomycete. Oxidizes ammonium with nitrite to produce N2 via the intermediate hydrazine. Key enzyme: hydrazine synthase (hzsA). Obligate anaerobe, obligate chemolithoautotroph.
**No anammox detector exists.**

**Why it failed:** Hydrazine synthase (hzsA) is not in the marker database, and no anammox pathway definition exists. The fermentation and aerobic respiration calls are false positives from the broad detection patterns (Scalindua's genome encodes glycolysis genes and some cytochrome oxidase homologs for non-respiratory functions).

**Category:** Failed due to missing detector category (hzsA). Expected outcome, documented as known gap before blind validation.

---

### 7. Ca. Methanoperedens nitroreducens — ANME

**CultureForge prediction:** Methanogenesis (0.93), fermentation (0.73), syntrophy (0.70)
**Reality:** Anaerobic methane-oxidizing archaeon (ANME-2d). Runs the methanogenesis pathway in REVERSE to oxidize methane, coupled to nitrate reduction as terminal electron acceptor. Has mcrA, all methanogenesis cofactors (F420, CoM, CoB), and the complete reverse methanogenesis pathway.

**Assessment:** Enzymatically correct, directionally wrong. The system detected mcrA at 60.8% identity (bs=666), all 5 methanogenesis pathway steps, and all 3 cofactor biosyntheses (F420, CoM, CoB). The confidence of 0.93 is the highest in the entire blind set. This is because the genome genuinely has every gene needed for methanogenesis. The difference (running it backwards) cannot be determined from genomic data alone. Transcriptomic, proteomic, or isotope-tracer data would be needed to resolve the direction.

The syntrophy call (0.70) is interesting and partially correct. Methanoperedens does live in syntrophic consortia, though it is the methane-consuming partner rather than a classical fatty acid oxidizer.

**Category:** Partially correct. Correct enzymes, wrong direction. This is a genuine limit of genome-based metabolism prediction that was anticipated in the Phase 1.5 prompt.

---

### 8. Ca. Prometheoarchaeum syntrophicum MK-D1 — Asgard Archaeon

**CultureForge prediction:** Syntrophy (0.70), fermentation (0.59)
**Reality:** Asgard archaeon that grows extremely slowly in syntrophic association with bacterial and archaeal partners. Degrades amino acids, producing H2 and formate that are consumed by partner organisms. First cultured Asgard archaeon (Imachi et al. 2020).

**Assessment:** Correct. The syntrophy composite detector correctly identified: beta-oxidation pathway present, electron-bifurcating hydrogenase present, no terminal electron acceptor metabolism detected. This matches the biological reality of an obligate syntroph with no independent energy conservation pathway. The fermentation secondary call (0.59) is also reasonable since the amino acid degradation pathways share enzymes with classical fermentation.

**Category:** Correct. This is a notable success for the composite syntrophy detector on a genuinely novel organism type (Asgard archaea were first cultured in 2020).

---

## Summary Statistics

**Primary capability correct:** 3/8 (Picrophilus, Thermotoga, Prometheoarchaeum)
**Partially correct (right enzymes, wrong direction):** 1/8 (Methanoperedens)
**Incorrect due to marker database gap:** 2/8 (Nitrospira, Chloroflexus)
**Incorrect due to missing detector category:** 2/8 (Dehalococcoides, Scalindua)
**gapseq limited:** 0/8 (gapseq produced valid output for all organisms)

### By failure category

| Category | Count | Organisms | Fixable? |
|---|---|---|---|
| Correct | 3 | Picrophilus, Thermotoga, Prometheoarchaeum | N/A |
| Direction ambiguity | 1 | Methanoperedens | Not from genome alone |
| Marker coverage gap | 2 | Nitrospira (amoA), Chloroflexus (pufLM) | Yes, add phylum-diverse refs |
| Missing detector | 2 | Dehalococcoides (rdhA), Scalindua (hzsA) | Yes, add pathway definitions |

### Comparison to blind v1 (5 organisms, old sequential decision tree)

| Metric | Blind v1 (decision tree) | Blind v2 (parallel detectors) |
|---|---|---|
| Primary correct | 0/5 (0%) | 3/8 (37.5%) |
| Partially correct | 0/5 | 1/8 |
| Total usable | 0/5 (0%) | 4/8 (50%) |
| Dominant failure mode | Methanogen false positive (4/5) | Missing markers/detectors (4/8) |

The parallel detector framework eliminated the methanogen false-positive cascade that caused 0% accuracy in blind v1. The remaining failures are primarily from marker database coverage (fixable by adding diverse reference sequences) and missing detector categories (fixable by adding pathway definitions for anammox and organohalide respiration).

---

## What Phase 2 Needs Based on Blind V2

### Must-have before recipe synthesis

1. **Fermentation detector over-fires.** It detected 6/8 organisms including obligate autotrophs (Nitrospira, Scalindua). The detector needs a negative signal when strong autotrophic pathways are present, similar to how acetogenesis uses negative markers.

2. **Aerobic respiration over-fires on some anaerobes.** Scalindua (obligate anaerobe) scored 0.90 for aerobic respiration. The cytochrome c hits are from non-respiratory cytochromes. Phase 2 should implement a confidence reduction when GenomeSPOT predicts anaerobic lifestyle.

### Should-have for publication

3. **Add comammox amoA references.** Nitrospira-type amoA from Ca. Nitrospira inopinata, Ca. Nitrospira nitrosa, Nitrospira moscoviensis. Would fix the biggest correctability failure.

4. **Add anammox detector.** Hydrazine synthase (hzsA) from Ca. Kuenenia stuttgartiensis and Ca. Scalindua profunda. Would add a new metabolism category that affects a significant microbial group.

5. **Add organohalide respiration detector.** Reductive dehalogenase (rdhA) from Dehalococcoides mccartyi. Niche metabolism but highly relevant for bioremediation applications.

6. **Add 3-hydroxypropionate bicycle detector.** For Chloroflexus-type phototrophs. Or expand pufLM marker database with FAP-type sequences.

### Accepted limitations (not fixable from genome alone)

7. **ANME directional ambiguity.** The methanogenesis vs reverse-methanogenesis distinction requires transcriptomic or isotopic evidence. Genome-based detection correctly identifies the enzymatic machinery but cannot determine which direction it runs. Document this limitation.

8. **Acidophily / thermophily detection.** These are growth condition properties, not metabolic capabilities. GenomeSPOT predictions (when integrated in Phase 2) address these.
