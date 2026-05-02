# DNRA / nrfA Markers — Phase 3.4 Literature Review

**Date:** 2026-05-01
**Purpose:** Confirm enzyme set + reference candidates + cross-reactivity assessment for Phase 3.4 dissimilatory nitrate reduction to ammonium (DNRA) detection via NrfA.

**Result:** Empirical scan + heme-motif analysis classifies the 26-genome test-set hits into 3 categories: 4 real canonical NrfA, 1 MAG-contamination case, 1 non-NrfA multi-heme cytochrome (Campylobacter — likely Otr-family). The protein family is more sequence-divergent than nxrA was. Threshold recommendation: **65% pident** (conservative); divergent-NrfA detection in some Bacillota / Geobacteraceae lineages deferred to a future sub-phase if needed.

---

## 1. Biology background

### 1.1 NrfA — cytochrome c nitrite reductase

NrfA is the terminal enzyme of dissimilatory nitrate reduction to ammonium (DNRA), catalyzing the 6-electron reduction NO₂⁻ + 6H⁺ + 6e⁻ → NH₄⁺ + 2H₂O. It's a periplasmic pentaheme c-type cytochrome with a characteristic Lys-axial active-site heme.

**Diagnostic protein-sequence signatures:**
- ~478-525 aa mature protein
- **5 c-type heme-binding motifs total**: 4 canonical CXXCH + 1 distinctive CXXCK (the active-site Lys-coordinated heme that distinguishes NrfA from related multi-heme cytochromes)
- The CXXCK motif is the **key diagnostic feature** — Otr (octaheme nitrite reductase), HAO, and many other multi-heme cytochromes c lack this motif

### 1.2 Distinguishing NrfA from related enzymes

| Enzyme | Heme architecture | CXXCK | Notes |
|---|---|---|---|
| **NrfA** | 5 hemes (4 CXXCH + 1 CXXCK) | ✅ YES | Canonical DNRA terminal |
| Otr (octaheme nitrite reductase) | 8 hemes (8 CXXCH) | ❌ NO | DNRA in some Epsilonproteobacteria; alternative architecture |
| HAO (hydroxylamine oxidoreductase) | 8 hemes | ❌ NO | AOB ammonia oxidation (different reaction) |
| NirB (assimilatory sulfite reductase) | flavin + Fe-S, no c-type | ❌ NO | Sulfite assimilation; different domain architecture |
| NrfH (small subunit) | 4 hemes, ~150 aa | ❌ NO | NrfA's quinol-dehydrogenase membrane partner |

The CXXCK motif is the unambiguous diagnostic feature. Sequences with 4 CXXCH + 1 CXXCK ≈ NrfA; sequences with 5+ CXXCH and no CXXCK ≈ Otr/HAO family (different enzyme).

### 1.3 Distribution

DNRA via NrfA is documented in:
- **Epsilonproteobacteria**: Wolinella, Sulfurospirillum (canonical, well-conserved)
- **Gammaproteobacteria**: Enterobacteriaceae (E. coli, Salmonella, Citrobacter), Pasteurellaceae (Mannheimia), Shewanella
- **Deltaproteobacteria**: Desulfovibrio (alongside sulfate-reducing capability)
- **Bacillota**: Some Clostridium, Bacillus species, Syntrophomonas (divergent NrfA)
- **Geobacteraceae**: Geobacter has documented DNRA capability via NrfA-related enzyme

### 1.4 Cultivation conditions for obligate DNRA model organisms

- Anaerobic atmosphere (N₂/CO₂)
- Organic donor (formate is canonical for Wolinella; lactate, acetate alternatives)
- NaNO₃ or NaNO₂ as terminal acceptor (~10-20 mM)
- Bicarbonate or phosphate buffer near pH 7
- Reducing agent (cysteine or Na₂S)
- ~37°C for mesophiles
- DSMZ Medium 720 family (Wolinella succinogenes medium)

### 1.5 Literature

- Simon J. 2002. Enzymology and bioenergetics of respiratory nitrite ammonification. *FEMS Microbiol Rev* 26:285-309.
- Einsle O et al. 2002. Mechanism of the six-electron reduction of nitrite to ammonia by cytochrome c nitrite reductase. *JACS* 124:11737-11745.
- Welsh A et al. 2014. Refined NrfA phylogeny improves PCR-based nrfA gene detection. *Appl Environ Microbiol* 80:2110-2119.
- Kraft B et al. 2014. The environmental controls that govern the end product of bacterial nitrate respiration. *Science* 345:676-679.
- Klotz MG et al. 2008. Evolution of an octaheme nitrite reductase (Otr) in Epsilonproteobacteria.

---

## 2. Reference candidates — 6 verified accessions across 5 genera

All accessions hand-fetched from UniProt; protein names + organisms + lengths verified.

| # | Accession | Source organism | Length | Status | Class | Notes |
|---|---|---|---|---|---|---|
| 1 | Q9S1E5 | *Wolinella succinogenes* DSM 1740 | 507 | **Swiss-Prot** | Epsilonproteobacteria | Canonical reference (Einsle et al. 2002 structural reference) |
| 2 | Q9Z4P4 | *Sulfurospirillum deleyianum* | 514 | **Swiss-Prot** | Epsilonproteobacteria | Sister-Epsilon DNRA |
| 3 | Q8EAC7 | *Shewanella oneidensis* MR-1 | 467 | **Swiss-Prot** | Gammaproteobacteria | Shewanella DNRA |
| 4 | Q06PW6 | *Mannheimia haemolytica* | 500 | **Swiss-Prot** | Gammaproteobacteria | Pasteurellaceae |
| 5 | B5QZA1 | *Salmonella enteritidis* PT4 | 478 | **Swiss-Prot** | Gammaproteobacteria | Enterobacteriaceae (close to E. coli) |
| 6 | Q8VNU2 | *Desulfovibrio desulfuricans* | 514 | TrEMBL | Deltaproteobacteria | Sister-genus to test-set Nitratidesulfovibrio (sister-species rule applies) |

**Test-set exclusions enforced** (none of these are from):
- Escherichia coli (P0ABK9 excluded — test set, gid 32)
- Campylobacter jejuni (excluded — gid 15)
- Nitratidesulfovibrio vulgaris Hildenborough (Q72EF3 excluded — gid 7)

**Wrong-protein traps caught (excluded):**
- O33732 — flagged in the Phase 3.4 prompt as "Sulfurospirillum deleyianum nrfA" but UniProt confirms it is actually a *Shewanella frigidimarina* nitrate reductase (938 aa, NOT nrfA). Replaced with the correctly identified Q9Z4P4 (genuine S. deleyianum nrfA, 514 aa, Swiss-Prot reviewed).
- V5Z1T4, Q6ZXS7 — short fragmentary D. desulfuricans nrfA entries (290 aa, 167 aa). Only the full-length Q8VNU2 (514 aa) used.

**Note on Swiss-Prot status:** Unlike Phase 3.3's nxrA (no Swiss-Prot reviewed entries exist), 5 of the 6 NrfA references ARE Swiss-Prot reviewed. This is a higher-quality reference set than typical for new diagnostic markers.

---

## 3. Pairwise reference identity — protein family is more divergent than nxrA

| Pair | pident | qcov | bitscore |
|---|---|---|---|
| Wolinella × Sulfurospirillum (intra-Epsilon) | 75.6% | 97% | 812 |
| Shewanella × Salmonella (intra-Gamma) | 62.8% | 91% | 610 |
| Shewanella × Mannheimia (intra-Gamma) | 58.9% | 87% | 550 |
| Salmonella × Mannheimia (intra-Gamma) | 59.6% | 92% | 574 |
| Wolinella × Shewanella (cross-class) | 51.3% | 90% | 454 |
| Mannheimia × Wolinella (cross-class) | 46.7% | 97% | 432 |
| Salmonella × Wolinella (cross-class) | 47.6% | 92% | 424 |
| Wolinella × Desulfovibrio (Epsilon × Delta) | 32.7% | 77% | 198 |
| Shewanella × Desulfovibrio | 34.3% | 78% | 200 |
| Mannheimia × Desulfovibrio | 31.3% | 74% | 192 |

**Two divergence tiers:**
- **Within-class** (Gamma-Gamma, Epsilon-Epsilon): 58-76% pident
- **Cross-class** (Gamma vs Epsilon): 46-51% pident
- **Most divergent**: Delta (Desulfovibrio) vs others: 31-34% pident

The Delta-vs-others divergence is striking — Desulfovibrio NrfA shares only ~32% identity with canonical Gamma/Epsilon NrfA despite catalyzing the same reaction with the same mechanism. This is much more divergent than nxrA (where intra-clade NOB stayed at 87%+ pident).

---

## 4. Empirical cross-reactivity assessment — 26-genome test-set scan

Build BLAST DB from the 6 nrfA references and run blastp against each test-set proteome at evalue ≤ 1e-30.

### 4.1 Hits sorted by pident

| Test genome | Best pident | Best qcov | Bitscore | n_hits | Hit gene |
|---|---|---|---|---|---|
| Scalindua profunda | **99.8%** | 100% | 1004 | 6 | AMSN01000031.1_15 |
| E. coli K-12 MG1655 | **90.0%** | 100% | 915 | 6 | NC_000913.3_3986 |
| Nitratidesulfovibrio vulgaris (D. vulgaris) | **68.8%** | 96% | 721 | 6 | NC_002937.3_592 |
| Syntrophomonas wolfei | **34.0%** | 89% | 248 | 6 | NC_008346.1_1564 |
| Geobacter sulfurreducens | **32.9%** | 78% | 176 | 6 | NC_002939.5_3111 |
| Campylobacter jejuni | **29.7%** | 83% | 198 | 1 | NC_002163.1_1302 |
| 20 other organisms | 0 hits | — | — | 0 | — |

### 4.2 Heme-motif analysis — definitive enzyme identification

For each hit, count CXXCH (canonical c-type heme-binding) and CXXCK (NrfA active-site Lys-coordinated heme) motifs:

| Hit | Length | CXXCH | CXXCK | Motif | Verdict |
|---|---|---|---|---|---|
| Scalindua AMSN01000031.1_15 | 478 aa | 4 | **1** | CWSCK | Canonical NrfA architecture — but 99.8% pident to Salmonella nrfA on a Brocadiaceae MAG is biologically implausible. **MAG contamination case** (Salmonella DNA contaminating Scalindua MAG). |
| E. coli NC_000913.3_3986 | 478 aa | 4 | **1** | CWSCK | Real canonical NrfA. (Test-set excluded from references.) |
| D. vulgaris NC_002937.3_592 | 524 aa | 4 | **1** | CWNCK | Real canonical NrfA — Deltaproteobacteria divergent, with W→N substitution but Lys-axial preserved. |
| Syntrophomonas NC_008346.1_1564 | 416 aa | 4 | **1** | CFTCK | **Real divergent NrfA** — Bacillota DNRA. CXXCK motif preserved despite low overall pident. |
| Geobacter NC_002939.5_3111 | 490 aa | 4 | **1** | CLTCK | **Real divergent NrfA** — Geobacter DNRA-capable. CXXCK motif preserved. |
| Campylobacter NC_002163.1_1302 | 540 aa | **5** | **0** | (NONE) | **NOT canonical NrfA.** 5 CXXCH heme motifs but no CXXCK active-site Lys-coordinated heme. Different multi-heme cytochrome c — likely Otr-family or related enzyme. C. jejuni's reported DNRA capability evidently uses a non-NrfA enzyme architecture. |

### 4.3 Three categories of hits

**A. Real canonical NrfA (high-identity, expected):**
- E. coli (90%) — test-set facultative, DNRA capability flagged but not primary mode
- D. vulgaris (68.8%) — test-set sulfate reducer, primary mode unaffected

**B. Real divergent NrfA (low-identity, biologically genuine):**
- Syntrophomonas (34%, CXXCK preserved) — Bacillota DNRA
- Geobacter (32.9%, CXXCK preserved) — Geobacter DNRA-capable
- Both already classify correctly into non-DNRA primary modes (syntrophic / iron-reduction); adding DNRA detection wouldn't change their classification.

**C. Non-NrfA cross-reactivity (must be excluded):**
- Campylobacter (29.7%, CXXCK absent) — different enzyme architecture, likely Otr-family (5 CXXCH only). C. jejuni's reported DNRA capability uses a different enzyme; this is the user's prompt-anticipated "Otr / octaheme cytochrome" case. Phase 3.4 nrfA-only scope correctly excludes it. Otr-based DNRA is a separate marker territory deferred to a future sub-phase.

**D. MAG contamination (anomaly):**
- Scalindua (99.8%) — a Brocadiaceae MAG cannot biologically have a 99.8%-identical Salmonella NrfA. This is contamination from Enterobacteriaceae DNA in the metagenomic assembly. Same MAG-completeness pattern as LIMITATIONS E.1. Documented but not treated as real Scalindua biology. The capability detection will fire on this (confidence-wise correctly representing what's in the proteome) but the recipe interpretation should respect E.1's MAG-completeness caveat.

---

## 5. Threshold recommendation

The Phase 3.3 nxrA decision was easy because there was a 39-point pident gap between cross-reactivity and true positives. **For nrfA, the gap is much smaller**: real divergent NrfA goes down to 32.9% pident; non-NrfA cross-reactivity reaches 29.7%. A 3-point gap is too narrow to set thresholds reliably from one test-set scan.

The user's pre-approved decision tree for this case:

> "If borderline hits are genuine divergent NrfA: we have a harder choice. Either set threshold at 28-30% and accept sulfite reductase false positives [...] or set threshold at 65% and accept that we'll miss divergent NrfA in lineages we don't have references for. The right call depends on how often divergent NrfA matters in real submissions."

### Recommendation: **threshold at 65% pident, 80% qcov, 1500 bitscore, 1e-30 evalue**

Rationale:

1. **Cleanly catches canonical NrfA** in Enterobacteriaceae, Pasteurellaceae, Shewanellaceae, Epsilonproteobacteria-Wolinella-class, and Desulfovibrionaceae lineages (the major characterized DNRA lineages).

2. **Cleanly excludes the borderline band** including Campylobacter's non-NrfA multi-heme cytochrome c (29.7% pident) and any sulfite-reductase-family or Otr-family false positives that might appear in real submissions but weren't represented in this 26-organism test set.

3. **Safe vs the "harder choice" branch** — setting threshold at 28-30% would require sulfite-reductase negative-marker curation (extra Phase scope) and would still produce false positives like Campylobacter's non-NrfA enzyme. The 65% threshold defers that complexity.

4. **Test-set classification stable** — the test-set DNRA-capable organisms that fall above 65% (E. coli, D. vulgaris) are facultative organisms with strong primary modes (aerobic_chemotrophic / sulfate reduction); flagging DNRA as alternative cultivation mode is the appropriate behavior. Syntrophomonas / Geobacter at 32-34% would be missed but they already classify correctly without DNRA detection.

5. **Documented gap** — this leaves divergent NrfA detection in some Bacillota / Geobacteraceae lineages as a future-sub-phase enhancement. The gap is biologically real but doesn't affect any current test-set primary mode, so deferring is honest and tractable.

6. **Forward path** if divergent NrfA detection becomes important: add a paired-marker requirement (nrfA + nrfH operon partner; nrfH is co-encoded in the canonical DNRA operon) to allow lower pident threshold safely. nrfH is short (~150 aa) but distinctive (4-heme cytochrome c). Reserved for future expansion.

### Rejected alternatives

- **30% pident**: catches divergent NrfA but the discrimination from Campylobacter Otr-family (29.7%) is fragile (3-point gap, within typical BLAST noise). Risk of NirB / sulfite reductase false positives in real submissions not represented in test set.
- **40% pident**: same problem — sits in the cross-class divergence range. No clean discrimination.
- **50% pident**: would miss D. vulgaris cross-class divergence (Delta vs others = 32%; cross-class minimum from this scan = 32-34%). Better than 30% but doesn't catch D. vulgaris reliably.
- **65% pident with paired nrfH marker**: belt-and-suspenders. Worth considering but adds curation work; defer.

---

## 6. Expected detection behavior on test-set organisms

| gid | Organism | Best nrfA hit | At 65% threshold | Primary mode (predicted) |
|---|---|---|---|---|
| 7 | Nitratidesulfovibrio vulgaris | 68.8% | ✅ FIRES | anaerobic_respiratory (sulfate reduction primary; DNRA flagged as alternative via existing facultative-anaerobe rule pattern) |
| 15 | Campylobacter jejuni | 29.7% | ❌ does not fire | aerobic_chemotrophic (microaerobic — unchanged; Otr-family enzyme not in scope) |
| 17 | Sulfurimonas denitrificans | 0 hits | ❌ | unchanged |
| 23 | Nitrospira moscoviensis | 0 hits | ❌ | unchanged (Phase 3.3 lithotrophic_aerobic_nitrite primary preserved) |
| 30 | Scalindua profunda | 99.8% (MAG contamination) | ✅ FIRES | Currently fermentative primary; would gain anaerobic_respiratory_dnra capability — biologically wrong (real Scalindua is anammox) but reflects MAG contamination that's documented as E.1. Fix is upstream MAG quality, not Phase 3.4 scope. |
| 32 | E. coli | 90.0% | ✅ FIRES | aerobic_chemotrophic (Phase 3.1 facultative-anaerobe rule keeps aerobic primary; DNRA flagged as alternative) |
| (20 others) | various | 0 hits | ❌ | unchanged |

**Critical for Task 5 verification:** E. coli's primary mode must remain `aerobic_chemotrophic` despite nrfA hit at 90%. This is handled by the existing Phase 3.1 facultative-anaerobe rule extended to also demote `anaerobic_respiratory_dnra` when aerobic_chemotrophic confidence ≥ 0.60. Same pattern as Phase 3.3 except for the new capability key.

For Scalindua: the MAG-contamination case will produce a DNRA detection that's wrong biologically but reflects the proteome content. Documented under LIMITATIONS E.1 (MAG completeness limitations) — it's the same fundamental issue as the original Scalindua misclassification, not Phase 3.4's responsibility to resolve.

---

## 7. Recommendation summary for Checkpoint A

**Markers to add (1):** nrfA (single-marker; nrfH paired-marker deferred).

**Reference set:** 6 verified accessions across 5 genera. 5 of 6 are Swiss-Prot reviewed (better quality reference set than Phase 3.3's all-TrEMBL nxrA refs). Test-set exclusion enforced (no E. coli, Campylobacter, or Nitratidesulfovibrio proteins). Wrong-protein traps caught (O33732, V5Z1T4, Q6ZXS7 excluded).

**Threshold:** **65% pident, 80% qcov, 1500 bitscore, 1e-30 evalue**.

**Empirical cross-reactivity finding:** The protein family is more divergent than nxrA. Using heme-motif analysis (CXXCK active-site signature), the borderline pident=30-34% hits classify as 2 real divergent NrfA (Syntrophomonas, Geobacter) + 1 non-NrfA multi-heme cytochrome c (Campylobacter — likely Otr family). The conservative 65% threshold cleanly catches all canonical NrfA while excluding the Otr-family Campylobacter case. Divergent NrfA in some Bacillota / Geobacteraceae lineages is documented as a known gap; deferred to a future sub-phase if needed.

**Expected behavior on test-set organisms:**
- E. coli: nrfA hit at 90% pident → DNRA flagged as alternative; primary stays aerobic_chemotrophic via Phase 3.1 facultative-anaerobe rule extended to DNRA.
- D. vulgaris: nrfA hit at 68.8% → DNRA flagged as alternative; primary stays anaerobic_respiratory (sulfate reduction).
- Campylobacter: nrfA hit at 29.7% → below threshold, not detected. C. jejuni's DNRA uses a non-NrfA enzyme (Otr family) which is out of Phase 3.4 scope.
- Scalindua: 99.8% pident hit is MAG contamination (Enterobacteriaceae DNA in Brocadiaceae MAG); will fire DNRA but documented as E.1 MAG-completeness anomaly, not real Scalindua biology.

**Risk assessment:** Low. The conservative 65% threshold matches the established Phase 1.5m / 3.3 pattern of "tight-thresholds-first, expand-later-if-needed." 5/6 references are Swiss-Prot reviewed. The known gap (divergent NrfA in some lineages) is documented and tractable as future enhancement.

**Predicted V12 impact:** Minimal. No test-set organism is an obligate DNRA primary; E. coli and D. vulgaris already classify correctly at their existing primary modes. Adding DNRA as flagged secondary capability shouldn't move primary-mode-driven recipe scores. Scalindua's MAG-contamination case might shift it from fermentative-primary (currently wrong) to anaerobic_respiratory_dnra-primary (also wrong but in a different direction) — net biological correctness unchanged.

---

## 8. Stop here for Checkpoint A

Per the Phase 3.4 prompt, stopping for user acknowledgment before proceeding to Task 2 (reference curation, BLAST DB build, capability definition, recipe composer routing). The 65% threshold and single-marker nrfA logic are the recommended choices; the heme-motif analysis backs up the threshold call empirically.
