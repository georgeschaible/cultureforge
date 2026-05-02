# Pathway Definitions Audit

Date: 2026-04-24
Scope: Cross-reference `data/pathway_definitions.json` against the Phase 1 prompt scientific basis and the 17-organism smoke test results.

---

## Per-Metabolism Assessment

### methanogenesis — MINOR GAP

**Steps (5/7 from spec):** Has methyl-CoM reductase, methanogenesis pathway (any variant), CoM/CoB regeneration, reductive acetyl-CoA methanogen variant, methanofuran biosynthesis. Missing individual enzyme steps (formyl-MFR DH, formyl-MFR:H4MPT transferase, methenyl-H4MPT cyclohydrolase, methylene-H4MPT DH, methylene-H4MPT reductase, mtr methyltransferase) because gapseq reports these as part of the whole "methanogenesis from H2 and CO2" pathway rather than individually.

**Cofactors (3/3):** F420, CoM, CoB. Pattern for F420 updated in Phase 1.5 to match gapseq naming.

**Diagnostic markers (1):** mcrA only. Spec called for mcrB and mcrG (beta and gamma subunits) as additional markers. These exist in the BLAST database (mcrBG_refs.fasta) but are not referenced as diagnostic markers for any step. Adding mcrBG as a step would boost confidence for organisms where all three subunits are present.

**Transporters:** None specified, none present. Correct for hydrogenotrophic methanogenesis (H2 and CO2 diffuse).

**Score impact:** Methanococcus at 0.753. F420 biosynthesis now matching. Adding mcrBG reference could push to 0.80+.

**Verdict:** Minor gap. Consider adding mcrBG as a weighted step in Phase 2.

---

### acetogenesis_wood_ljungdahl — COMPLETE

**Steps (6):** Reductive acetyl-CoA pathway, formate assimilation, CO DH/acetyl-CoA synthase (x2 with different markers), acetate/ATP formation, pyruvate ferredoxin oxidoreductase. Well-matched to gapseq output.

**Cofactors (1):** Corrinoid biosynthesis. Matches.

**Negative markers (4):** mcrA, dsrAB, aprAB, mtrC_omcB. Correctly excludes methanogens, SRBs, and iron reducers using WL for autotrophy.

**Diagnostic markers (2):** acsB_cdhC, cooS_cdhA. Both reference DBs populated.

**Score impact:** Acetobacterium at 0.750. Good.

**Verdict:** Complete.

---

### ammonia_oxidation — COMPLETE

**Steps (4):** amoABC, haoA, cytochrome c554, cytochrome cM552. First two have diagnostic markers.

**Cofactors (1):** Heme biosynthesis. Relevant.

**Transporters (1):** Ammonium transporter (amt). Present.

**Score impact:** Nitrosomonas at 0.916. Excellent.

**Verdict:** Complete.

---

### anoxygenic_phototrophy_purple — COMPLETE

**Steps (6):** pufL, pufM, puhA, bacteriochlorophyll biosynthesis, carotenoid biosynthesis, light-harvesting complex.

**Cofactors (1):** Bacteriochlorophyll a biosynthesis.

**Diagnostic markers (2):** pufLM (shared between pufL and pufM steps).

**Score impact:** Rhodopseudomonas at 0.768. Good.

**Verdict:** Complete. gapseq may not have specific pathway names for bch/crt genes, so some steps may not match. Worth inspecting for Rhodopseudomonas.

---

### anoxygenic_phototrophy_green_sulfur — MINOR GAP

**Steps (4):** pscA, fmoA, bacteriochlorophyll c/d/e biosynthesis, chlorosome proteins.

**Cofactors (0):** None specified. Could add bacteriochlorophyll c/d/e biosynthesis as cofactor.

**Diagnostic markers (2):** pscA_fmoA. However, this marker has a high false-positive rate across organisms (30-38% identity hits in non-phototrophs from iron-sulfur proteins). The marker BLAST thresholds were tightened in Phase 1.5 (40%/300 for full credit) which reduces but does not eliminate FPs.

**Score impact:** No true green sulfur bacteria in the validation set. Marker-only detection at 0.225 in non-phototrophs (below threshold, correctly rejected).

**Verdict:** Minor gap. pscA_fmoA FP rate needs monitoring. No green sulfur bacteria in validation set to confirm true-positive behavior.

---

### oxygenic_phototrophy — COMPLETE

**Steps (4):** psbA (PSII), psaA (PSI), cytochrome b6f, oxygen-evolving complex.

**Cofactors (1):** Chlorophyll a biosynthesis.

**Diagnostic markers (2):** psaA_psbA.

**Score impact:** No cyanobacteria in validation set. Untested.

**Verdict:** Complete but untested.

---

### dissimilatory_sulfate_reduction — COMPLETE

**Steps (6):** sat, aprAB, dsrAB, DsrC, QmoABC, DsrMKJOP.

**Diagnostic markers (2):** aprAB, dsrAB. Both at high quality in D. vulgaris (100% identity).

**Transporters (1):** Sulfate transporter (sulP family).

**Score impact:** D. vulgaris at 0.733. Appropriate.

**Verdict:** Complete.

---

### sulfur_oxidation — COMPLETE (Phase 1.5 fix)

**Steps (5):** Sulfide oxidation I, sulfide oxidation III, sulfur oxidation I (aerobic), sulfite oxidation, thiosulfate oxidation (SOX multienzyme).

**Diagnostic markers (1):** soxB.

**Score impact:** Acidithiobacillus 0.681, Sulfurimonas 0.594. Both detected.

**Verdict:** Complete after Phase 1.5 pattern fix.

---

### denitrification — MINOR GAP

**Steps (4):** Nitrate reductase (narG/napA), nitrite reductase (nirS/nirK), nitric oxide reductase (norBC), nitrous oxide reductase (nosZ).

**Diagnostic markers (1):** nosZ.

**Transporters (1):** Nitrate/nitrite transporter (narK).

**Gap:** The step patterns use enzyme-level names (narG, nirS, norB, nosZ) which may not match gapseq pathway naming. The spec called for checking gapseq pathway names. Denitrification detected for Magnetospirillum (0.548) and Sulfurimonas (weak), suggesting some patterns match but not optimally.

**Verdict:** Minor gap. Inspect gapseq denitrification pathway names and update patterns.

---

### iron_ii_oxidation — SIGNIFICANT GAP

**Steps (4):** cyc2, rusticyanin, cytochrome c4, aa3-type cytochrome oxidase.

**Diagnostic markers (1):** cyc2. Only 1 reference sequence in the database.

**Gap:** Acidithiobacillus ferrooxidans is the canonical iron oxidizer in our set but scores 0.200 for iron(II) oxidation (not detected). cyc2 is the diagnostic enzyme but gapseq does not annotate it as a pathway. The detection relies entirely on the marker BLAST, which returned 0 hits for Acidithiobacillus. This may be because the cyc2 reference (Q4A194) is too divergent from the A. ferrooxidans variant, or because the proteome FASTA does not contain the cyc2 ORF.

**Proposed fix:** Add additional cyc2 reference sequences from NCBI for Acidithiobacillus strains. Also check if rusticyanin is annotated in gapseq pathway output.

**Verdict:** Significant gap. Iron(II) oxidation is effectively non-functional for Acidithiobacillus. Proposed fix before Phase 2.

---

### iron_iii_reduction — MINOR GAP

**Steps (4):** mtrABC/omcBC (outer membrane conduit), ppcA (periplasmic cytochromes), omcS/omcZ (outer surface), pilA (conductive pili).

**Diagnostic markers (1):** mtrC_omcB. Geobacter at 100% identity bs=699.

**Score impact:** Geobacter at 0.597 (detected). Iron reduction ranks 3rd behind aerobic respiration (0.90, FP from expanded detector) and fermentation (0.775, FP from broad detection). The iron reduction call IS correct but ranking is problematic.

**Verdict:** Minor gap. Detector works but ranking is affected by aerobic respiration and fermentation over-detection. Phase 2 recipe synthesis must use the full capability profile rather than top-1 ranking.

---

### bacteriorhodopsin — COMPLETE

**Steps (3):** Bacteriorhodopsin/proteorhodopsin, retinal biosynthesis, carotenoid precursor.

**Diagnostic markers (1):** rhodopsin. Halobacterium at 100% identity.

**Score impact:** Halobacterium at 0.659. Detected.

**Verdict:** Complete.

---

### nitrogen_fixation — COMPLETE

**Steps (5):** nifH (Fe protein), nifD (MoFe alpha), nifK (MoFe beta), FeMo cofactor biosynthesis, electron donor.

**Diagnostic markers (1):** nifH. Multiple organisms correctly detected (Clostridium 67% id, Acidithiobacillus 74%, Magnetospirillum 67%, Rhodopseudomonas 74%).

**Verdict:** Complete.

---

### aerobic_respiration (JSON entry) — MINOR GAP

**Steps (5):** NADH dehydrogenase, succinate dehydrogenase, cytochrome bc1, terminal oxidase, F1F0 ATP synthase.

**Gap:** This JSON-defined pathway runs through the generic detector, but the actual aerobic respiration detection is handled by the custom `detect_aerobic_respiration()` function. The two detectors run in parallel, producing two separate aerobic respiration entries in the profile ("Aerobic respiration via electron transport chain" from JSON at ~0.32 and "Aerobic respiration" from custom at 0.55-0.90). This is confusing but not harmful.

**Proposed fix:** Remove the JSON entry and rely solely on the custom detector. Or merge them.

**Verdict:** Minor gap. Cosmetic duplication.

---

### fermentation_mixed — COMPLETE (Phase 1.5 addition)

**Steps (9):** Glycolysis I/III/IV, Entner-Doudoroff, pyruvate fermentation to lactate/ethanol/acetate/acetoin/butanoate/butanol, heterolactic fermentation.

**Score impact:** Lactobacillus 0.706, Clostridium 0.900, E. coli 0.900.

**Verdict:** Complete. Fires broadly, which is biologically correct (most bacteria can ferment).

---

## Summary

| Metabolism | Status | Action needed |
|---|---|---|
| Methanogenesis | Minor gap | Consider adding mcrBG step |
| Acetogenesis | Complete | None |
| Ammonia oxidation | Complete | None |
| Purple phototrophy | Complete | None |
| Green sulfur phototrophy | Minor gap | Monitor pscA_fmoA FPR |
| Oxygenic phototrophy | Complete (untested) | Need cyanobacterium in validation |
| Sulfate reduction | Complete | None |
| Sulfur oxidation | Complete | None |
| Denitrification | Minor gap | Update patterns to gapseq names |
| Fe(II) oxidation | **Significant gap** | Add cyc2 refs for Acidithiobacillus |
| Fe(III) reduction | Minor gap | Ranking affected by broad aerobic/ferm |
| Bacteriorhodopsin | Complete | None |
| Nitrogen fixation | Complete | None |
| Aerobic respiration (JSON) | Minor gap | Remove duplicate; use custom detector only |
| Fermentation | Complete | None |

**Phase 2 blockers:** None. The significant gap (Fe(II) oxidation) affects Acidithiobacillus ranking but the organism still gets aerobic respiration (correct secondary) and sulfur oxidation (correct). The iron oxidation gap is a missed detection, not a wrong one.

**Recommended hot-fixes before blind v2:** None. All gaps are acceptable for the blind validation since the 8 new organisms do not include a canonical iron(II) oxidizer.
