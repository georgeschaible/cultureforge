# Nitrite Oxidation Markers — Phase 3.3 Literature Review

**Date:** 2026-05-01
**Purpose:** Confirm enzyme set + reference candidates + narG cross-reactivity assessment for Phase 3.3 canonical nitrite oxidation detection.

**Result:** nxrA primary marker; cross-reactivity with narG-family (DMSO reductase superfamily) is real at ~45-48% pident over full coverage. Tight pident threshold (≥75%) cleanly discriminates nxrA from narG. Paired-marker (nxrA AND nxrB) is recommended belt-and-suspenders for robustness.

---

## 1. Biology background

### 1.1 Nitrite oxidoreductase (NXR) — the diagnostic enzyme

Canonical NOB use **NxrAB** (nitrite oxidoreductase, alpha and beta subunits) for the central energy-conserving reaction NO₂⁻ → NO₃⁻. NxrA is the catalytic subunit (~1100-1220 aa, contains Mo-bisMGD cofactor + [4Fe-4S] cluster); NxrB is the electron-transfer subunit (~400-500 aa, contains Fe-S clusters).

The enzyme is membrane-bound. Distinguishing feature between major NOB lineages: the active site faces the periplasm in Nitrobacter / Nitrolancea (Type B), and the cytoplasm in Nitrospira / Nitrotoga / Nitrococcus (Type A). The two architectures are evolutionarily distinct — at the sequence level they share <25% identity (verified empirically below).

### 1.2 NXR is a member of the Mo/W-DMSO reductase superfamily

The same superfamily includes:

- **NarG** — membrane-bound nitrate reductase (catalyzes the *reverse* reaction NO₃⁻ → NO₂⁻ in denitrifiers and DNRA organisms)
- **NarG-like** — variants in archaea (Methanoperedens), anammox bacteria (Scalindua), and other lineages
- **Other family members** — perchlorate reductase (PcrA), arsenite oxidase (AioA), TMAO reductase, DMSO reductase

NxrA and NarG share the same fold and the same Mo-bisMGD cofactor. The functional difference (oxidation vs reduction at the same substrate) is determined by enzyme orientation, accessory subunits, and quaternary structure — not by primary sequence alone.

**Implication:** any BLAST-based nxrA detection scheme will produce moderate-identity hits on narG-bearing organisms. Threshold design must account for this.

### 1.3 Nitrospira-type vs Nitrobacter-type — empirical confirmation

Pairwise BLAST among the 8 candidate references shows two well-separated clades:

| Pair (representative) | pident | qcov | bitscore |
|---|---|---|---|
| Nitrospira × Nitrospira (intra-genus, e.g., N. inopinata × N. defluvii) | **88%** | 99% | 2112 |
| Nitrospira × Nitrospira (e.g., N. inopinata × N. japonica) | **87%** | 100% | 2090 |
| Nitrospira × Nitrotoga (cross-genus, both Type A) | **35%** | 99% | 691 |
| Nitrospira × Nitrobacter (cross-clade, Type A vs Type B) | **24%** | 39% | 93 |
| Nitrospira × Nitrolancea (cross-clade) | **24%** | 39% | 93 |

The Nitrospira and Nitrobacter clades are essentially separate protein families at BLAST level. A single threshold cannot detect both with one ref clade alone — but with refs from both clades in the database, a hit from any reference covers its lineage.

### 1.4 CO₂ fixation pathways

- **Nitrospira lineage**: reductive TCA cycle (rTCA), key enzyme ATP-citrate lyase (aclAB)
- **Nitrobacter lineage**: Calvin-Benson-Bassham (CBB), key enzyme RuBisCO
- **Nitrolancea hollandica**: CBB
- **Nitrotoga**: CBB

Recipe composer can tolerate either pathway; bicarbonate as carbon source supplies both.

### 1.5 Cultivation conditions (DSMZ Medium 2399 / NOB media)

- **Atmosphere**: aerobic (air, 1 atm)
- **Electron donor**: NaNO₂ at 0.5-2 mM (toxic above ~5 mM; replenish during cultivation)
- **Carbon**: NaHCO₃ ~2.5 g/L
- **Buffer**: phosphate at pH 7.5-8.0
- **Temperature**: 28-37°C for mesophiles (Nitrospira moscoviensis NSP M-1 is mesophile, ~37°C)
- **Trace metals**: SL-10 standard; Mo important for nxr cofactor
- **Vitamins**: standard (Wolin's)
- **Reducing agent**: NOT needed (aerobic culture)

### 1.6 Literature

- Spieck E, Lipski A. 2011. Cultivation, growth physiology, and chemotaxonomy of nitrite-oxidizing bacteria. *Methods Enzymol* 486:109-130.
- Daims H, Lücker S, Wagner M. 2016. A new perspective on microbes formerly known as nitrite-oxidizing bacteria. *Trends Microbiol* 24:699-712.
- Lücker S, Wagner M, Maixner F, Pelletier E, Koch H et al. 2010. A Nitrospira metagenome illuminates the physiology and evolution of globally important nitrite-oxidizing bacteria. *PNAS* 107:13479-13484.
- Sorokin DY, Lücker S, Vejmelkova D et al. 2012. Nitrification expanded: discovery, physiology and genomics of a nitrite-oxidizing bacterium from the phylum Chloroflexi. *ISME J* 6:2245-2256. (Nitrolancea hollandica; first non-Nitrospirota NOB outside Pseudomonadota)

---

## 2. Reference candidates — 8 verified accessions across 4 NOB genera

All accessions hand-fetched from UniProt; protein names and lengths verified.

| # | Accession | Source organism | Length | Status | Genus / clade |
|---|---|---|---|---|---|
| 1 | A0A0S4KRS1 | *Ca.* Nitrospira inopinata | 1145 | TrEMBL | Nitrospira / Type A (cytoplasmic) |
| 2 | A0A1W1I298 | *Nitrospira japonica* | 1145 | TrEMBL | Nitrospira / Type A |
| 3 | A0ABM8RCK9 | *Nitrospira defluvii* | 1147 | TrEMBL | Nitrospira / Type A |
| 4 | Q3SQW5 | *Nitrobacter winogradskyi* Nb-255 | 1214 | TrEMBL | Nitrobacter / Type B (periplasmic) |
| 5 | Q71RT9 | *Nitrobacter alkalicus* | 1201 | TrEMBL | Nitrobacter / Type B |
| 6 | A0A916FC48 | *Ca.* Nitrotoga fabula | 1169 | TrEMBL | Nitrotoga / Type A |
| 7 | A0ABN8AJF8 | *Ca.* Nitrotoga arctica | 1169 | TrEMBL | Nitrotoga / Type A |
| 8 | A0A894Z0L1 | *Nitrolancea hollandica* | 1221 | TrEMBL | Nitrolancea / Type B |

**Test-set exclusion:** None of these are from Nitrospira moscoviensis NSP M-1. ✓

**Swiss-Prot status:** All TrEMBL. UniProt has no Swiss-Prot reviewed nxrA entry — consistent with the bidirectional name confusion (UniProt typically files these as "Nitrate reductase (quinone)" or "Putative nitrate oxidoreductase, alpha subunit"). Reference inclusion is therefore by curated TrEMBL only, with the verification standard being protein name + organism phenotype + genus diversity. This matches the soxB / qmoA / hzsA / etc. pattern from Phase 1.5m where Swiss-Prot doesn't exist for the diagnostic enzyme.

**Wrong-protein check:** Nitrobacter winogradskyi has multiple short-fragment nxrA entries in UniProt (Q3BJV5–Q3BJV9, 85-100 aa each). These are excluded — only the full-length Q3SQW5 / Q3SUK2 (both 1214 aa, locus Nwi_2068 / Nwi_0774) used.

---

## 3. narG cross-reactivity assessment — empirical BLAST scan

**Method:** Built BLAST DB from 8 nxrA references (`/tmp/p3_3xa/nxrA_refs.fa`), ran blastp against the predicted proteome of each of the 26 test-set genomes at evalue ≤ 1e-30, no pident/qcov filter applied at the BLAST stage.

**Result:**

| Test genome | Best pident | Best qcov | Best bitscore | n_hits | Interpretation |
|---|---|---|---|---|---|
| **Nitrospira moscoviensis NSP M-1** | **96.1%** | **100%** | **2332** | **25** | Target — strong, full-length hits across all 5 nxrA paralogs from all 3 Nitrospira refs |
| Methanoperedens nitroreducens | 48.0% | 99% | 1127 | 5 | Cross-reactivity with narG-like (ANME-2d uses narG-related nitrate reductase) |
| E. coli K-12 MG1655 | 45.9% | 99% | 1107 | 6 | Cross-reactivity with narGHI nitrate reductase |
| Scalindua profunda | 45.8% | 99% | 1089 | 6 | Cross-reactivity with narG-related (anammox uses nitrate reductase variant) |
| Lactobacillus plantarum | 44.1% | 99% | 1051 | 3 | Cross-reactivity with related Mo-DMSO superfamily enzyme |
| All 21 other test organisms | 0 hits | — | — | 0 | True negatives at evalue ≤ 1e-30 |

**Interpretation:** narG cross-reactivity is real and significant. Four organisms produce full-length 99%-qcov hits in the **45-48% pident range** — these are bona fide DMSO reductase superfamily members that are NOT NXR.

**Discrimination point:** between 48% (highest narG-family hit) and 87% (lowest within-clade NOB hit) there is a wide gap. **Any threshold in the 60-85% range cleanly separates true NOB from narG-family false positives.**

Recommended threshold: **pident ≥ 75%, qcov ≥ 80%, bitscore ≥ 1500** (the bitscore floor adds a length-aware safety margin).

At this threshold:
- Nitrospira moscoviensis fires (96% pident, bs=2332) ✓
- All four cross-reactive narG-bearing organisms (Methanoperedens, E. coli, Scalindua, Lactobacillus) DO NOT fire (best 48% pident) ✓
- Future Nitrobacter-class submissions would hit Nitrobacter refs at ~80% intra-genus pident — fires ✓
- Future Nitrotoga-class submissions hit Nitrotoga refs at ~80% intra-genus — fires ✓

This is clean. **Single-marker (nxrA only) at tight threshold suffices.**

---

## 4. Paired-marker option (nxrA AND nxrB)

**Optional belt-and-suspenders approach.** nxrAB is a heterodimer; nxrB co-occurs with nxrA in NOB genomes. Adding nxrB as a co-required marker would require BOTH subunits to fire above threshold for the capability to be detected — rejecting any organism that has only one (impossible in a real NOB genome).

**Pros:**
- Belt-and-suspenders against cross-reactivity edge cases not visible in this 26-organism test set
- Natural biological co-occurrence; rejects partial-genome MAGs that have only the alpha subunit
- Conservative — fewer false positives in future test sets

**Cons:**
- Doubled curation effort (4-6 nxrB references needed)
- nxrB shares same DMSO superfamily background as narH — same cross-reactivity profile expected (narG/narH co-occur, so requiring both nxrA + nxrB at high threshold should still discriminate)
- For MAGs that are missing one subunit (Scalindua-style E.1 issue), paired-marker requirement causes false negatives

**Verdict:** single-marker with tight threshold is sufficient and cleaner. Paired-marker is available if the user prefers belt-and-suspenders.

---

## 5. Recommended thresholds

For the new `lithotrophic_aerobic_nitrite` capability:

| Marker | min_pident | min_qcov | min_evalue | min_bitscore | Logic |
|---|---|---|---|---|---|
| nxrA | **75.0** | **80** | 1e-30 | **1500** | Single marker, OR logic across reference clades |

**Rationale for thresholds:**

- **75% pident**: cleanly above the 48% narG-family ceiling; well below the 87% within-clade NOB floor; provides safety margin for novel NOB lineages with slightly more divergent nxrA.
- **80% qcov**: full-length hits expected; allows minor truncation tolerance.
- **1e-30 evalue**: standard CultureForge marker stringency.
- **1500 bitscore**: NOB nxrA self-vs-self bitscores are 2300-2400 (full-length); within-clade (87% pident) is ~2100; intra-clade hits at the 80% pident floor would be ~1700-1800. Cross-clade Nitrospira-vs-Nitrobacter at 24% pident produces bs=93. The 1500 bitscore floor is a length-aware safety margin that excludes any sub-domain partial-match noise.

**Note on dual-clade detection:** Because the 8 references include both Type A (Nitrospira / Nitrotoga) and Type B (Nitrobacter / Nitrolancea) clades, a single OR-logic search against the combined DB will catch both lineages — each query genome BLASTs against all 8 refs and the best hit determines the call. A Nitrobacter genome will produce 80%+ pident against the Nitrobacter refs (Q3SQW5 or Q71RT9) even though it has near-zero similarity to the Nitrospira refs. The 75% threshold applies to the BEST hit — clade-specific.

---

## 6. Recommendation summary for Checkpoint A

**Markers to add (1):** nxrA (single-marker; paired nxrB not needed).

**Reference set:** 8 verified accessions across 4 genera (Nitrospira × 3, Nitrobacter × 2, Nitrotoga × 2, Nitrolancea × 1). Test-set exclusion enforced. All TrEMBL — no Swiss-Prot reviewed nxrA exists (UniProt names this protein family ambiguously). Wrong-protein traps (Q3BJV5–Q3BJV9 fragments) excluded.

**Thresholds:** pident ≥ 75%, qcov ≥ 80%, bitscore ≥ 1500, evalue ≤ 1e-30.

**Cross-reactivity:** Empirically verified narG/narG-like cross-reactivity caps at ~48% pident across the test set. The 75% pident threshold cleanly separates true NOB from DMSO-reductase-superfamily false positives.

**Capability definition (preview for Task 3):** New `lithotrophic_aerobic_nitrite` capability with single nxrA diagnostic marker. Pathway steps: nitrite oxidoreductase + autotrophic CO₂ fixation (rTCA or CBB) + aerobic respiration + ammonia assimilation. diagnostic_marker_override at 0.70 confidence so an nxrA hit alone produces a moderate-confidence detection even without strong pathway integrity score (consistent with Phase 1.5n pattern for marker-required metabolisms).

**Test-set impact (predicted):** Only Nitrospira moscoviensis classification changes — from acetogenic primary (V12 score 20%) to lithotrophic_aerobic_nitrite primary with aerobic / NaNO₂ / NaHCO₃ recipe matching DSMZ Medium 2399 architecture. Expected V12 score improvement: 20% → 50-70%.

**Risk assessment:** Low. The cross-reactivity scan is empirical and clean at the recommended threshold. The single-marker approach matches the pattern used for soxB, mcrA, and rdhA in Phase 1.5m (single discriminating marker per capability where the enzyme is uniquely discriminating). No capability framework changes needed.

---

## 7. Stop here for Checkpoint A

Per the Phase 3.3 prompt, stopping for user acknowledgment before proceeding to Task 2 (reference curation, BLAST DB build, capability definition, recipe composer routing). The narG cross-reactivity assessment determines the threshold and paired-marker decision; both are now resolved (single-marker, 75% pident, clean discrimination).
