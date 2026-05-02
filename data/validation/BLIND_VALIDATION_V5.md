# CultureForge Blind Validation V5 — Post Phase 1.5i Fixes

Date: 2026-04-26
Fixes applied: archaeal GenomeSPOT handling (Option B — skip archaea), iron reduction cross-suppression of fermentation

## V4 to V5 Changes

### Sulfolobus (the archaeal aerobe regression)
- V4: aerobic respiration 0.30 (suppressed by GenomeSPOT "not tolerant")
- V5: aerobic respiration **0.50** (GenomeSPOT skipped for archaea, restored by terminal oxidase BLAST)
- Cultivation mode: aerobic_chemotrophic(0.50) ✓

### Geobacter (the iron reducer ranking issue)
- V4: fermentative(0.65) primary, anaerobic_respiratory(0.60) secondary
- V5: **anaerobic_respiratory(0.60)** only (fermentation suppressed by iron reduction cross-suppression)
- Cultivation mode: anaerobic_respiratory(0.60) ✓

## 17-Organism Set V5 Results

| Organism | V5 Cultivation modes | Correct? |
|---|---|---|
| E. coli | aerobic(0.90) + fermentative(0.65) | ✓ |
| D. vulgaris | anaerobic_resp(0.73) + fermentative(0.65) | ✓ |
| Methanococcus | methanogenic(0.75) | ✓ |
| Thermus | aerobic(0.75) | ✓ |
| Lactobacillus | fermentative(0.71) | ✓ |
| Acidithiobacillus | aerobic(0.85) + lithotrophic(0.68) | ✓ |
| Clostridium | fermentative(0.90) | ✓ |
| Geobacter | anaerobic_resp(0.60) | ✓ **FIXED** |
| Sulfolobus | aerobic(0.50) | ✓ **FIXED** |
| Campylobacter | aerobic(0.90) + fermentative(0.64) | ✓ |
| Magnetospirillum | fermentative(0.65) + anaerobic_resp(0.58) | ~ (aero suppressed by dsrAB FP) |
| Sulfurimonas | lithotrophic(0.59) | ✓ |
| Nitrosomonas | lithotrophic(0.92) + aerobic(0.90) | ✓ |
| Rhodopseudomonas | aerobic(0.90) + phototrophic(0.77) + anaerobic_resp(0.55) | ✓ |
| Halobacterium | halophilic(0.66) + aerobic(0.60) | ✓ |
| Syntrophomonas | syntrophic(0.70) | ✓ |
| Acetobacterium | acetogenic(0.75) + fermentative(0.73) | ✓ |

**Score: 16/17 correct** (Magnetospirillum is the one remaining issue due to reverse-dsrAB being misinterpreted as sulfate reduction).

## 8-Organism Blind Set V5 Results

| # | Organism | V5 Modes | Assessment |
|---|---|---|---|
| 1 | Nitrospira | lithotrophic(0.59) | Partial (comammox missed) |
| 2 | Chloroflexus | aerobic(0.85) + ferm(0.65) + acetogenic(0.64) | Partial (photo in secondary) |
| 3 | Dehalococcoides | anaerobic_resp(0.65) | **Correct** |
| 4 | Picrophilus | aerobic(0.90) + ferm(0.65) | **Correct** |
| 5 | Thermotoga | fermentative(0.78) | **Correct** |
| 6 | Scalindua | aerobic(0.90) + ferm(0.65) | Incorrect (anammox missed) |
| 7 | Methanoperedens | methanogenic(0.93) + syntrophic(0.70) | Partial (right enzymes, wrong direction) |
| 8 | Prometheoarchaeum | syntrophic(0.70) | **Correct** |

**Score: 7/8 functionally relevant (4 correct + 3 partial).** Unchanged from V4.

## Phase 2 Readiness Verdict

**17-organism set: 16/17 correct cultivation modes.**
The one remaining issue (Magnetospirillum) is a dsrAB direction-ambiguity problem analogous to the ANME methanogenesis direction problem. Magnetospirillum has reverse dsrAB for sulfide oxidation, which the detector reads as sulfate reduction. This triggers the anaerobe disqualifier and suppresses aerobic respiration. The fix would require dsrAB direction inference (forward vs reverse operon context), which is Phase 3 scope.

**8-organism blind set: 7/8 functionally relevant.** V4 baseline maintained.

**Sulfolobus: FIXED.** Aerobic respiration restored to 0.50.
**Geobacter: FIXED.** Iron reduction is primary cultivation mode.
**No regressions on any previously-correct organism.**

**VERDICT: GO FOR PHASE 2.**

Phase 2 scope:
1. Wire cultivation_modes into recipe synthesis (replace old determine_energy_metabolism)
2. Generate alternative recipes for multi-mode organisms (e.g., Rhodopseudomonas gets both phototrophic and aerobic recipes)
3. Thermodynamic viability layer using Amend & Shock data
4. BacDive pattern retrieval as consistency check
5. The cultivation_modes list (not top-1 ranking) drives carbon source, electron donor/acceptor, and atmosphere selection
