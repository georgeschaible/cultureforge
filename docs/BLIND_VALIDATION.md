# CultureForge Blind Validation — 5 Novel Organisms

**Date:** 2026-04-23
**Protocol:** All 5 organisms processed with NO user overrides — no `--energy-metabolism`, no `--temperature`, no `--ph`. The system received only a genome FASTA. Real media were NOT consulted until all 5 predictions were complete.
**gapseq flags:** `-b 200 -t Bacteria` (or `-t Archaea` for Halobacterium)
**Total gapseq compute:** ~48 hours (sequential, 5 organisms)

---

## Summary: 0/5 energy metabolism classifications correct

| # | Organism | Real metabolism | Predicted metabolism | Carbon correct? | Atmosphere correct? | Would grow? |
|---|---|---|---|---|---|---|
| 1 | Nitrosomonas europaea | Ammonia oxidizer | **Methanogen** | No | No | **No** |
| 2 | Rhodopseudomonas palustris | Versatile phototroph | **Methanogen** | No | ~ (microaerobic) | Unlikely |
| 3 | Halobacterium salinarum | Aerobic halophile | **Microaerophile** | No | No | **No** (no salt) |
| 4 | Syntrophomonas wolfei | Syntrophic anaerobe | **Methanogen** | ~ (pyruvate) | No (aerobic!) | **No** |
| 5 | Acetobacterium woodii | Acetogen (WL pathway) | **Methanogen** | Yes (fructose) | Yes (H2:CO2) | **Maybe** |

**Energy metabolism accuracy: 0/5 (0%)**
**Would-grow rate: ~1/5 (20%) at best**

This is a categorical failure. The system that scored 10/10 on the tuning set scores 0/5 on novel metabolic types.

---

## Detailed Results

### 1. Nitrosomonas europaea — Obligate ammonia oxidizer

**De novo prediction:**
- Energy: Methanogen [0.75] — methanogenesis-from-acetate pathway at 50%
- Carbon: none (methanogen → autotrophic CO2)
- Atmosphere: Aerobic (from GenomeSPOT, no unambiguous oxidase detected)
- NaCl: 9.9 g/L
- Reducing: Na2S 0.5 g/L (methanogen default)
- Overall: 0.55 (LOW)

**Real medium (DSMZ 756a):**
- Energy: Aerobic ammonia oxidation (NH4+ → NO2-)
- Carbon: NaHCO3 0.5 g/L (obligate autotroph)
- Electron donor: (NH4)2SO4 2.5 g/L
- Base salts: KH2PO4 0.2 g/L, MgSO4 0.04 g/L, CaCl2 0.02 g/L
- NaCl: 0.6 g/L
- Trace metals: standard
- Atmosphere: Aerobic
- pH: 8.0
- Temperature: 28°C

**What was present in the genome data but not used:**
- Ammonia oxidation I (aerobic): **100% complete, predicted=true**
- amoABC reaction: **10 good_blast hits, complex_complete**
- hao reaction: **3 good_blast hits, complex_complete**
- The ammonia oxidizer check at step 6 would have correctly classified this organism, but the methanogen check at step 2 fired first on a false-positive 50% methanogenesis-from-acetate pathway.

**Root cause:** Decision tree ordering. The methanogen check (step 2) fires at ≥50% completeness for ANY methanogenesis variant. Methanogenesis-from-acetate shares enzymes with general acetyl-CoA metabolism (phosphotransacetylase, acetate kinase), so any organism with active acetate metabolism triggers this check.

---

### 2. Rhodopseudomonas palustris — Versatile phototroph

**De novo prediction:**
- Energy: Methanogen [0.75] — methanogenesis-from-acetate at 50%
- Carbon: none (methanogen → autotrophic CO2)
- Atmosphere: Microaerobic (cbb3 complex detected — actually reasonable)
- NaCl: 9.9 g/L
- Overall: 0.55 (LOW)

**Real medium (DSMZ 27, modified):**
- Energy: Photoheterotroph (anaerobic light) or chemoautotroph
- Carbon: Succinate 1 g/L or malate (photoheterotrophic); NaHCO3 (photoautotrophic)
- Yeast extract: 0.3 g/L
- NH4Cl, MgSO4, CaCl2, K2HPO4
- Trace metals: SL-6
- NaCl: minimal
- Atmosphere: Anaerobic (for photoheterotrophic growth); or aerobic (for chemoheterotrophic)
- pH: 6.8
- Temperature: 25-30°C

**Assessment:** Same methanogen false positive. The atmosphere call (microaerobic via cbb3) is defensible — R. palustris CAN grow microaerobically. But the photosynthetic reaction center and bacteriochlorophyll genes (puf, bch operons) are the key diagnostic features, and CultureForge has no phototrophy detection at all.

**Missing capability:** No pathway pattern for photosynthesis (reaction center, bacteriochlorophyll biosynthesis). This is a metabolic type the decision tree simply cannot recognize.

---

### 3. Halobacterium salinarum — Extreme halophile

**De novo prediction:**
- Energy: Microaerophile [0.72] — cbb3 complex (likely false positive from archaeal cytochrome)
- Carbon: Sucrose 10 g/L (from carbon profile)
- Atmosphere: Microaerobic
- NaCl: 9.9 g/L
- Overall: 0.55 (LOW)

**Real medium (DSMZ 97):**
- Energy: Aerobic heterotroph (+ bacteriorhodopsin for light-driven ATP)
- Carbon: Yeast extract 5 g/L + casamino acids 5 g/L (amino acid based)
- NaCl: **250 g/L** (4.3 M!)
- MgSO4·7H2O: 20 g/L
- KCl: 2 g/L
- Trisodium citrate: 3 g/L
- Atmosphere: Aerobic
- pH: 7.0
- Temperature: 37°C

**Assessment:** Triple failure.
1. **Salinity catastrophe:** NaCl 9.9 g/L vs required 250 g/L — off by 25x. The organism would lyse instantly. GenomeSPOT's salinity prediction completely fails for extreme halophiles. The ectoine pathway (our halophile marker) is NOT how Halobacterium handles osmotic stress — it uses KCl flooding ("salt-in" strategy), which requires no compatible solute genes at all.
2. **Metabolism wrong:** Microaerophile from a cbb3 false positive. Real organism is an obligate aerobe that uses bacteriorhodopsin.
3. **Carbon wrong:** Sucrose instead of amino acids. Halobacterium is a peptide/amino acid fermenter that cannot catabolize sugars efficiently.

**Missing capability:** No "salt-in" halophile detection (high intracellular K+, no compatible solute genes = extreme halophile). No bacteriorhodopsin detection.

---

### 4. Syntrophomonas wolfei — Obligate syntrophic fatty acid oxidizer

**De novo prediction:**
- Energy: Methanogen [0.75] — methanogenesis at 50%
- Carbon: Sodium pyruvate 2.2 g/L
- Atmosphere: **Aerobic** (GenomeSPOT fallback — no unambiguous oxidase)
- NaCl: 9.9 g/L
- Reducing agent: none (classified as aerobe → no reducer)
- Hydrogenases: **8 hits** (correct!)
- Overall: 0.56 (LOW)

**Real medium (DSMZ 722):**
- Energy: Syntrophic beta-oxidation of fatty acids (butyrate → acetate + H2, coupled to a methanogenic partner)
- Carbon: Crotonate 2 g/L (or butyrate with partner)
- NaHCO3: 4 g/L (buffer)
- NH4Cl: 1 g/L
- K2HPO4, MgSO4, CaCl2
- Reducing agent: Na2S 0.36 g/L + L-cysteine 0.5 g/L
- Trace metals: SL-10
- Vitamins: standard
- Atmosphere: **N2:CO2 or H2:CO2** (strict anaerobe)
- pH: 7.2
- Temperature: 37°C
- **Requires co-culture with Methanospirillum hungatei** for growth on butyrate

**Assessment:** The methanogen false positive fired again. Critically, the atmosphere is wrong (aerobic) — this organism is a strict anaerobe that would die in air. The pyruvate carbon source is not unreasonable (S. wolfei can use some organic acids) but the real substrate is crotonate/butyrate. The 8 hydrogenase hits are biologically meaningful — S. wolfei produces H2 during syntrophic fatty acid oxidation. But the system has no concept of syntrophy.

**Missing capability:** No syntrophic metabolism detection. No beta-oxidation pathway detection. No co-culture requirement prediction.

---

### 5. Acetobacterium woodii — Acetogen (Wood-Ljungdahl pathway)

**De novo prediction:**
- Energy: Methanogen [0.75] — methanogenesis at **83%** (strongest false positive)
- Carbon: **D-Fructose 5 g/L**
- Atmosphere: **H2:CO2 (80:20)** at 1-2 bar
- Reducing agent: **Na2S 0.5 g/L**
- NaCl: 9.9 g/L
- Hydrogenases: 6 hits
- Overall: 0.56 (LOW)

**Real medium (DSMZ 135):**
- Energy: Acetogenesis (H2 + CO2 → acetate via Wood-Ljungdahl) or fructose fermentation
- Carbon: **Fructose 5 g/L** (or H2+CO2)
- NaHCO3: 5 g/L
- NH4Cl: 1 g/L
- Yeast extract: 2 g/L
- K2HPO4, MgSO4, CaCl2
- Reducing agent: **Na2S 0.5 g/L + L-cysteine 0.5 g/L**
- Trace metals: SL-10
- Vitamins: standard
- Atmosphere: **N2:CO2 80:20** (or H2:CO2 for autotrophic)
- pH: 7.0
- Temperature: 30°C

**Assessment: The best result of the five, despite wrong energy classification.**
- **Fructose 5 g/L: CORRECT** — matches reality exactly. gapseq found fructose utilization pathways and the calibration hit the right concentration.
- **H2:CO2 atmosphere: PARTIALLY CORRECT** — A. woodii CAN grow on H2:CO2 (autotrophic acetogenesis). N2:CO2 with fructose is more standard, but H2:CO2 would also work.
- **Na2S 0.5 g/L: CORRECT** — matches reality.
- **Hydrogenases: 6 hits: CORRECT** — A. woodii has [FeFe] hydrogenases for H2 metabolism.

The methanogen classification is biochemically understandable: the Wood-Ljungdahl pathway (acetogenesis) shares most of its enzymes with the reverse direction of methanogenesis. gapseq reports 83% methanogenesis completeness because the WL enzymes (formyltetrahydrofolate synthetase, CO dehydrogenase/acetyl-CoA synthase) match methanogenesis reference sequences. The distinction between acetogenesis and methanogenesis lies in the final enzymatic step (methyl-CoM reductase for methane vs phosphotransacetylase/acetate kinase for acetate) — a nuance the 50% pathway-completeness threshold cannot capture.

---

## Component-Level Precision and Recall

Using 2x tolerance for C/e-donor/e-acceptor, 5x for trace metals/vitamins.

| Organism | Components | True pos | False pos | False neg | Precision | Recall |
|---|---|---|---|---|---|---|
| Nitrosomonas | 20 | 5 | 12 | 5 | 0.29 | 0.50 |
| Rhodopseudomonas | 17 | 5 | 9 | 5 | 0.36 | 0.50 |
| Halobacterium | 16 | 2 | 11 | 8 | 0.15 | 0.20 |
| Syntrophomonas | 20 | 7 | 9 | 6 | 0.44 | 0.54 |
| Acetobacterium | 20 | 11 | 5 | 4 | 0.69 | 0.73 |
| **Mean** | **18.6** | **6.0** | **9.2** | **5.6** | **0.39** | **0.49** |

**Comparison to tuning set: precision dropped from 0.74 to 0.39, recall from 0.78 to 0.49.**

### What the system got right (true positives across all 5)

- **NH4Cl** as nitrogen source: correct in 4/5 (all except Halobacterium which needs casamino acids)
- **K2HPO4/KH2PO4** phosphate buffer: correct in all 5
- **MgSO4, CaCl2** base salts: correct in 4/5 (wrong concentration for Halobacterium)
- **Standard trace metals** (Fe, Zn, Mn, Co, Ni, Cu): present in all 5 real media
- **Na2S reducing agent** for anaerobes: correct in 2/2 where predicted (Acetobacterium, Nitrosomonas-as-methanogen)
- **Fructose 5 g/L** for Acetobacterium: exact match
- **Hydrogenase detection**: biologically meaningful in 3/3 organisms that use H2

### What the system got wrong (systematic failures)

1. **Methanogenesis-from-acetate false positive (4/5 organisms):** The #1 failure. Any organism with acetyl-CoA metabolism triggers the methanogen check at ≥50% completeness. This is because phosphotransacetylase and acetate kinase — found in MOST bacteria — are also part of the aceticlastic methanogenesis pathway.

2. **No phototrophy detection (1/5):** The decision tree has no patterns for bacteriochlorophyll biosynthesis, reaction center proteins, or photosystem genes. Phototrophs are invisible.

3. **No extreme halophile detection (1/5):** The "salt-in" strategy (high intracellular KCl, no compatible solute genes) is the opposite of what the ectoine/betaine markers detect. Extreme halophiles that use salt-in are completely missed.

4. **No syntrophic metabolism detection (1/5):** Obligate syntrophs that require a partner organism for thermodynamic viability cannot be recognized from genome alone.

5. **Atmosphere wrong for 3/5:** Without unambiguous bo3/cbb3 oxidase complexes AND with misleading GenomeSPOT predictions, the atmosphere defaults are often wrong.

---

## Root Cause Analysis

### The methanogen threshold is the critical bug

The decision tree checks methanogen FIRST (step 2) at only 50% pathway completeness. This is fatally flawed because:

- Aceticlastic methanogenesis uses acetate kinase + phosphotransacetylase — enzymes present in virtually every bacterium
- gapseq reports methanogenesis-from-acetate at 50% for any organism with these common enzymes
- Step 2 fires before more specific checks (ammonia oxidizer at step 6, denitrifier at step 7)
- Result: 4 out of 5 novel organisms get misclassified as methanogens

**Fix required:** Either (a) raise the methanogen threshold to ≥75% AND require [NiFe] G3 hydrogenase confirmation, OR (b) move the methanogen check AFTER more specific checks, OR (c) require methanogen-specific markers (methyl-coenzyme M reductase / mcrA gene) as a confirmation.

### The tuning set was too narrow

The original 10 organisms included only metabolic types that happen to work with the current decision tree:
- Methanogens (Methanococcus — correctly classified because it also has [NiFe] G3)
- Sulfate reducers (D. vulgaris — dsrAB confirmation works)
- Iron reducers (Geobacter — outer membrane cytochrome markers work)
- Fermenters (Clostridium, Lactobacillus — TCA + fermentation pathway logic works)
- Aerobic heterotrophs (Thermus, E. coli — oxidase + TCA logic works)
- Microaerophiles (Campylobacter — cbb3 detection works)

None of the tuning organisms tested: ammonia oxidizers without [NiFe] G3, phototrophs, extreme halophiles, syntrophs, or acetogens. The 10/10 score on the tuning set gave false confidence.

### What works regardless of classification

Even when the energy metabolism is wrong, some components are correct because they come from independent pipelines:
- **MeBiPred** trace metals: always reasonable (MeBiPred predictions don't depend on metabolism type)
- **Phosphate/buffer**: K2HPO4/KH2PO4 is universal
- **NH4Cl**: correct for almost all prokaryotes
- **Hydrogenase detection**: correct wherever tested (genome-level BLAST)
- **gapseq carbon profile**: when consulted (heterotroph path), gives reasonable substrates

---

## Lessons Learned

1. **10/10 on a tuning set means nothing** if the tuning set doesn't cover the failure modes. Blind validation is essential.

2. **Decision tree ordering creates cascading failures.** The methanogen check at step 2 acts as a trap for any organism with common acetate metabolism enzymes. This is not a minor bug — it affects the majority of prokaryotes.

3. **Pathway completeness thresholds are fragile.** A 50% threshold that works perfectly for true methanogens (which also have [NiFe] G3 hydrogenase as confirmation) causes catastrophic false positives for non-methanogens.

4. **Missing metabolic types are invisible failures.** The system doesn't say "I don't know what this organism does" — it confidently assigns the wrong type. Adding a "none of the above" / "unrecognized metabolism" output when no pathway exceeds 75% would be more honest.

5. **Independent component pipelines are more robust than the classification.** MeBiPred metals, phosphate, NH4Cl, and hydrogenases all work correctly regardless of the metabolism classification. The classification-dependent components (carbon source, atmosphere, reducing agent) are the ones that fail.

---

## Recommended Fixes (Priority Order)

1. **Require mcrA (methyl-coenzyme M reductase) for methanogen classification.** This is THE diagnostic enzyme for methanogenesis — no non-methanogen has it. Add mcrA to the reaction marker scan. Without mcrA, never classify as methanogen regardless of pathway completeness.

2. **Add phototrophy detection.** Scan for pufLM (reaction center), bchA-Z (bacteriochlorophyll biosynthesis) in gapseq reaction tables. Present in Rhodopseudomonas, absent in everything else.

3. **Add extreme halophile detection.** Scan for trkA/trkH (K+ uptake), ktrAB (K+ transporter), absence of ectoine + presence of >5 K+ transport systems → "salt-in" halophile → NaCl 200+ g/L.

4. **Move methanogen check AFTER sulfur oxidizer and ammonia oxidizer.** Even without the mcrA fix, reordering so specific metabolisms are checked before the generic methanogenesis pathway would fix the Nitrosomonas case.

5. **Add "unrecognized metabolism" category.** When no pathway exceeds 75% completeness and no specific markers are confirmed, output "metabolism unclear — recommend user specification" instead of guessing.
