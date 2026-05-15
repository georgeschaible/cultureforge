# Phase 5.0 — CultureForge predictions audit (n=168)

**Date of audit:** 2026-05-14  
**CultureForge revision:** git d4e9587 (post fermentation-primary-mode fix)  
**Scope:** All 168 genomes in `data/cultureforge.db` — 136 Phase 5.0 main load, 26 validation/blind organisms (gids 7-32), 4 sentinels (gids 900-903), 1 PacBio bin MAG (gid 1000), 1 Phase 5.0 smoke test (gid 1001).  
**Method:** Ran `cultureforge.py inspect <gid>` for each genome, parsed predictions, compared to known biology (BacDive, DSMZ, primary literature). **No code was modified.**  

**Headline:** 106 PASS / 31 PARTIAL / 30 FAIL / 1 INSUFFICIENT — pass rate **63%**, directional-or-better rate (PASS+PARTIAL) **82%**.

---

## 1. Executive summary

- **ANME-1/2a/3 archaea (gids 1005, 1006, 1007) are classified as forward methanogens.** All three encode mcrA and the C1 pathway with acsB+cooS, but they perform anaerobic oxidation of methane (reverse methanogenesis) in nature. Gid 28 (Methanoperedens nitratireducens) is correctly classified as `anme_reverse_methanogenic`; the same logic must extend to ANME-1/2a/3. **Three of 17 methane-category FAILs trace to this single missing classifier rule.**
- **Ammonia-oxidizing archaea (Nitrosopumilus 1049, Nitrososphaera 1102, Nitrosocosmicus 1106) always escalate** — only the `autotrophy` and `terminal_oxidases` markers hit; no capability detector recognizes archaeal-lineage `amoA` (it is too divergent from bacterial AMO). Bacterial AOB and the comammox Nitrospira inopinata (gid 1114) succeed cleanly, so this is an AOA-specific marker gap.
- **Wood-Ljungdahl is over-detected on non-acetogens and pulls primary mode to `acetogenic`.** Six diverse organisms — Geobacter metallireducens (1031), Rhodospirillum rubrum (1032), Azotobacter vinelandii (1056), Acetoanaerobium sticklandii (1079), Pelotomaculum schinkii (1126), Syntrophorhabdus aromaticivorans (1130) — share the pattern: acsB / cooS / CODH hits push WL ≈ 0.65–0.76, ranking above the organism's real primary mode (Fe(III) respiration, anoxygenic phototrophy, aerobic N-fixation, Stickland fermentation, syntrophy). This is structurally analogous to the fermentation primary-mode bug fixed 2026-05-13 (commit d4e9587), but in the *acetogenesis* lane.
- **Anammox bacteria detect Anammox capability at 0.95 but the recipe composer has no `anammox` cultivation mode**, so gids 30 (Scalindua japonica) and 1105 (Scalindua brodae) escalate, while gids 1001/1002/1090 fall back to `lithotrophic_aerobic` with a misleadingly aerobic recipe. The capability layer works; the composer-side mapping is the gap.
- **Hyperthermophilic / thermoacidophilic anaerobic archaea escalate as a class.** Thermococcus kodakarensis (1019), Ignicoccus hospitalis (1046), Caldivirga maquilingensis (1047), Stygiolobus azoricus (1129), Ferroplasma acidarmanus (1070), and Picrophilus torridus (26) all have `autotrophy` and assorted sulfur markers but no detector resolves to a primary mode. Cable bacteria (gids 1004, 1008) and vent ε-proteobacteria (Caminibacter 1127) fail for the same reason — the cultivation-mode library has no entry for their physiology.

## 2. Per-category pass rates

| Category | PASS | PARTIAL | FAIL | INSUFFICIENT | total | PASS% | (PASS+PARTIAL)% |
|---|---:|---:|---:|---:|---:|---:|---:|
| nitrogen_metabolism | 19 | 7 | 8 | 0 | 34 | 56% | 76% |
| methane_metabolism | 17 | 0 | 4 | 0 | 21 | 81% | 81% |
| sulfur_metabolism | 14 | 3 | 1 | 0 | 18 | 78% | 94% |
| phototrophy | 12 | 1 | 1 | 0 | 14 | 86% | 93% |
| fermentation | 10 | 2 | 1 | 0 | 13 | 77% | 92% |
| iron_metals | 3 | 4 | 2 | 0 | 9 | 33% | 78% |
| sulfate_reduction | 7 | 0 | 0 | 0 | 7 | 100% | 100% |
| carbon_fixation | 2 | 2 | 2 | 0 | 6 | 33% | 67% |
| syntrophy | 2 | 3 | 2 | 0 | 7 | 29% | 71% |
| extreme_archaea | 3 | 1 | 4 | 0 | 8 | 38% | 50% |
| marine_user_interest | 1 | 3 | 0 | 0 | 4 | 25% | 100% |
| manganese_metabolism | 3 | 0 | 1 | 0 | 4 | 75% | 75% |
| magnetotaxis | 3 | 2 | 0 | 0 | 5 | 60% | 100% |
| heavy_metal_respiration | 2 | 1 | 2 | 0 | 5 | 40% | 60% |
| halophile_alkaliphile | 3 | 1 | 0 | 0 | 4 | 75% | 100% |
| acetogenesis | 4 | 0 | 0 | 0 | 4 | 100% | 100% |
| phosphate_metabolism | 1 | 1 | 0 | 0 | 2 | 50% | 100% |
| cable_bacteria | 0 | 0 | 2 | 0 | 2 | 0% | 0% |
| unknown_MAG | 0 | 0 | 0 | 1 | 1 | 0% | 0% |
| **OVERALL** | **106** | **31** | **30** | **1** | **168** | **63%** | **82%** |

Read-out:
- Best-performing cohorts: **sulfate_reduction** (100% PASS) and **acetogenesis** (100% PASS) — gapseq+marker library is well-tuned for these textbook anaerobic respiratory & WL pathways.
- **methane_metabolism** is 81% but all four FAILs are concentrated in ANME archaea (one rule fix would lift it to 100%).
- Worst-performing cohorts: **cable_bacteria** (0%, 2/2 FAIL — no mode), **syntrophy** (29% PASS), **iron_metals** (33%), **carbon_fixation** (33%), **extreme_archaea** (38%), **heavy_metal_respiration** (40%). These share the property of relying on physiologies that gapseq doesn't model end-to-end and that lack a capability-detector entry.

## 3. Per-gid findings (grouped by category)

### nitrogen_metabolism  (34 genomes — PASS 19 / PARTIAL 7 / FAIL 8 / INSUFFICIENT 0)

- **gid 18 — Nitrosomonas europaea** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Aerobic ammonia oxidation=0.916, Aerobic respiration=0.9, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: amoA, autotrophy, cyc2, hao, terminal_oxidases
  - Rationale: AOB; lithotrophic_aerobic ✓; amoA-related detection works for bacterial pathway
  - Source: DSMZ 28437; Chain et al. 2003 J Bacteriol

- **gid 19 — Rhodopseudomonas palustris** — **PASS**
  - CultureForge: primary `phototrophic`; alt `anaerobic_respiratory, aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Denitrification (NO3- to N2)=0.925, Aerobic respiration=0.9, Purple phototrophy=0.768, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.557
  - Positive markers: autotrophy, nifH, nosZ, pufLM, soxB, terminal_oxidases
  - Rationale: purple non-sulfur metabolic chameleon; phototrophic primary + 3 alt modes ✓
  - Source: ATCC BAA-98; Larimer et al. 2004 Nat Biotechnol

- **gid 23 — Nitrospira moscoviensis** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `acetogenic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Aerobic nitrite oxidation (canonical NOB=0.769, Acetogenesis (Wood-Ljungdahl)=0.605
  - Positive markers: autotrophy, nxrA
  - Rationale: canonical NOB; lithotrophic_aerobic ✓; but acetogenesis (0.605) flagged as alt mode is a false positive — Nitrospira has rTCA carbon fixation, not WL
  - Source: DSMZ 10035; Ehrich et al. 1995 Arch Microbiol

- **gid 30 — Candidatus Scalindua japonica** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 7.0; T 31.1°C; salinity 2.94%
  - Detected caps (≥0.50): Anammox=0.95, Fermentation=0.65, Aerobic ammonia oxidation=0.621
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, hao, hdh, hzsA
  - Rationale: anammox bacterium; Anammox capability detected at 0.95 ✓ but recipe escalates because composer has no anammox cultivation-mode → mapping; should compose with NH4+/NO2- as electron donor/acceptor
  - Source: Oshiki et al. 2016 Environ Microbiol

- **gid 901 — Wolinella succinogenes DSM 1740** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Dissimilatory nitrate reduction to ammon=0.645, Nitrogen fixation=0.532, Aerobic respiration=0.5
  - Positive markers: nifH, nrfA, terminal_oxidases
  - Rationale: DNRA (nitrate→ammonium); anaerobic_respiratory ✓; nrfA hits expected
  - Source: DSMZ 1740; Baar et al. 2003 PNAS

- **gid 902 — Nitrobacter winogradskyi Nb-255** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Aerobic nitrite oxidation (canonical NOB=0.614, Aerobic respiration=0.5
  - Positive markers: autotrophy, cyc2, nxrA, terminal_oxidases
  - Rationale: type-B NOB; lithotrophic_aerobic ✓; nxrA + cyc2 + autotrophy markers ✓
  - Source: DSMZ 10237; Starkenburg et al. 2006 AEM

- **gid 1001 — Candidatus Brocadia sinica JPN1 (smoke test)** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory`; recipe `composed`; O2 n/a; pH 6.8; T 40.8°C; salinity 1.14%
  - Detected caps (≥0.50): Anammox=0.86, Aerobic ammonia oxidation=0.621
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, hao, hdh, hzsA
  - Rationale: anammox; primary mode lithotrophic_aerobic is misleading (anammox is anaerobic NH4+/NO2-); recipe composed but using aerobic profile
  - Source: Hira et al. 2012 Int J Syst Evol Microbiol

- **gid 1002 — Candidatus Brocadia fulgida** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory, fermentative`; recipe `composed`; O2 n/a; pH 6.7; T 40.8°C; salinity 2.35%
  - Detected caps (≥0.50): Anammox=0.86, Fermentation=0.65, Aerobic ammonia oxidation=0.621
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, hao, hdh, hzsA
  - Rationale: anammox; primary mode lithotrophic_aerobic — wrong oxygen handling (should be anaerobic); recipe composed
  - Source: Kartal et al. 2008 Environ Microbiol

- **gid 1017 — Nostoc sp. PCC 7120 (Anabaena PCC 7120)** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.1; T 36.3°C; salinity 0.79%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615, Nitrogen fixation=0.614
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: diazotrophic heterocyst-forming cyanobacterium; phototrophic ✓; T 36.3°C high (true 25-28°C); pH 8.1 ✓
  - Source: Pasteur PCC 7120; Kaneko et al. 2001 DNA Res

- **gid 1023 — Bradyrhizobium diazoefficiens USDA 110** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.9; T 30.5°C; salinity 0.58%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.778, Nitrogen fixation=0.614
  - Positive markers: autotrophy, nifH, nosZ, soxB, terminal_oxidases
  - Rationale: facultative chemolithoautotroph (H2-oxidizing) + symbiotic N-fixer; lithotrophic_aerobic ✓; nifH expected but heterotrophic growth in pure culture is primary
  - Source: USDA 110; Kaneko et al. 2002 DNA Res

- **gid 1026 — Methanococcus maripaludis S2** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.8; T 55.6°C; salinity 3.57%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, mcrA, mcrBG, nifH
  - Rationale: mesophilic hydrogenotrophic methanogen; methanogenic ✓; T 55.6°C ⚠ (true 35-40°C, over-predicted)
  - Source: DSMZ 14266; Hendrickson et al. 2004 J Bacteriol

- **gid 1032 — Rhodospirillum rubrum ATCC 11170** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `aerobic_chemotrophic, phototrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 7.1; T 25.7°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Acetogenesis (Wood-Ljungdahl)=0.763, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, nifH, pufLM, terminal_oxidases
  - Rationale: purple non-sulfur phototroph; classified primary=acetogenic — WRONG; purple phototrophy detected at 0.768 with pufLM ✓ but WL (0.763) ranks slightly higher pushing primary to acetogenic; should be phototrophic
  - Source: ATCC 11170; Munk et al. 2011 J Bacteriol

- **gid 1036 — Stutzerimonas stutzeri A1501 (Pseudomonas stutzeri)** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `anaerobic_respiratory, fermentative, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 7.5; T 31.8°C; salinity 3.85%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Fermentation=0.65, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: cyc2, nifH, nosZ, terminal_oxidases
  - Rationale: denitrifying N-fixer; aerobic_chemotrophic ✓; denitrification not in alt modes despite full nar/nir/nor/nos in P. stutzeri — possibly nosZ missed
  - Source: DSMZ 4166; Yan et al. 2008 PNAS

- **gid 1037 — Nitrobacter hamburgensis X14** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 6.6; T 28.2°C; salinity 1.56%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Aerobic nitrite oxidation (canonical NOB=0.718, Sulfur oxidation (bacterial SOX + archae=0.704
  - Positive markers: autotrophy, cyc2, nxrA, soxB, terminal_oxidases
  - Rationale: type-B NOB; lithotrophic_aerobic ✓; nxrA+cyc2 ✓; soxB cap (0.704) is unusual — Nitrobacter has no canonical sulfur oxidation in pure culture (possible false positive)
  - Source: DSMZ 10229; Starkenburg et al. 2008 Stand Genomic Sci

- **gid 1039 — Nitrosomonas eutropha C91** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.2; T 27.8°C; salinity 1.7%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Aerobic ammonia oxidation=0.816
  - Positive markers: amoA, autotrophy, cyc2, hao, terminal_oxidases
  - Rationale: AOB; lithotrophic_aerobic ✓
  - Source: DSMZ 101675; Stein et al. 2007 Environ Microbiol

- **gid 1045 — Crocosphaera subtropica ATCC 51142** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.5; T 37.5°C; salinity 3.04%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615, Nitrogen fixation=0.614
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: diazotrophic unicellular cyanobacterium; phototrophic ✓
  - Source: ATCC 51142; Welsh et al. 2008 PNAS

- **gid 1049 — Nitrosopumilus maritimus SCM1** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 7.1; T 38.2°C; salinity 6.13%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy, terminal_oxidases
  - Rationale: model ammonia-oxidizing archaeon; ESCALATED — only autotrophy + terminal_oxidases hit; archaeal amoA not in marker set or sequence too divergent from bacterial AMO
  - Source: DSMZ 28326; Walker et al. 2010 PNAS

- **gid 1056 — Azotobacter vinelandii DJ** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `aerobic_chemotrophic, fermentative`; recipe `composed`; O2 tolerant; pH 7.4; T 33.5°C; salinity 2.81%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Nitrogen fixation=0.614, Acetogenesis (Wood-Ljungdahl)=0.562
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH, terminal_oxidases
  - Rationale: obligate aerobic free-living N-fixer; classified primary=acetogenic — WRONG; high O2-tolerant respiration is its hallmark; WL false-positive driving primary mode (acsB+cooS hits from CODH not WL acetogenesis)
  - Source: ATCC BAA-1303; Setubal et al. 2009 J Bacteriol

- **gid 1065 — Frankia alni ACN14a** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 6.8; T 24.8°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: nifH, terminal_oxidases
  - Rationale: actinobacterial N-fixing symbiont (alder); aerobic_chemotrophic ✓; nitrogen fixation not in detected caps (vesicle-bound nitrogenase) — partial
  - Source: ATCC 51800; Normand et al. 2007 Genome Res

- **gid 1082 — Trichormus variabilis ATCC 29413 (Anabaena variabilis)** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.0; T 37.7°C; salinity 1.14%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615, Nitrogen fixation=0.614
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: heterocyst-forming diazotrophic cyanobacterium; phototrophic ✓
  - Source: ATCC 29413

- **gid 1090 — Candidatus Jettenia caeni** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory, fermentative`; recipe `composed`; O2 n/a; pH 6.9; T 44.5°C; salinity 2.7%
  - Detected caps (≥0.50): Anammox=0.86, Fermentation=0.637, Aerobic ammonia oxidation=0.621
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, hao, hdh, hzsA
  - Rationale: anammox bacterium; classified lithotrophic_aerobic — anammox is anaerobic NH4+/NO2- (should be its own anammox mode); recipe composed but aerobic profile wrong
  - Source: Ali et al. 2015 Environ Microbiol Rep

- **gid 1091 — Klebsiella michiganensis M5al (K. oxytoca canonical nif strain)** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.4; T 29.8°C; salinity 1.05%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: nifH, terminal_oxidases
  - Rationale: facultative anaerobe with nif operon; aerobic_chemotrophic ✓
  - Source: Saha et al. 2013 Curr Microbiol

- **gid 1092 — Anabaena sp. 90** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.7; T 36.1°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Nitrogen fixation=0.584
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: diazotrophic heterocyst-forming cyanobacterium; phototrophic ✓
  - Source: Wang et al. 2012 PLoS ONE

- **gid 1094 — Nitrospina gracilis 3/211** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 tolerant; pH 7.1; T 36.1°C; salinity 5.8%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: (none)
  - Rationale: marine NOB; ESCALATED — zero positive markers, no caps detected; nxrA likely too divergent from reference for BLAST hit (Nitrospina nxrA differs from Nitrospira/Nitrobacter)
  - Source: DSMZ 6680; Lücker et al. 2013 Front Microbiol

- **gid 1102 — Nitrososphaera viennensis EN76** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 6.7; T 36.9°C; salinity 2.21%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: terminal_oxidases
  - Rationale: soil AOA; ESCALATED — same systematic issue as gid 1049, archaeal amoA not detected
  - Source: DSMZ 26422; Kerou et al. 2016 PNAS

- **gid 1105 — Candidatus Scalindua brodae** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 7.5; T 34.4°C; salinity 3.05%
  - Detected caps (≥0.50): Anammox=0.95, Acetogenesis (Wood-Ljungdahl)=0.75, Fermentation=0.65, Aerobic ammonia oxidation=0.621
  - Positive markers: acsB_cdhC, cooS_cdhA, hao, hdh, hzsA
  - Rationale: anammox bacterium; Anammox cap detected at 0.95 with hzsA+hdh+hao ✓ but recipe ESCALATED — same composer→mode mapping gap as gid 30
  - Source: Speth et al. 2015 Standard Genomic Sci

- **gid 1106 — Candidatus Nitrosocosmicus oleophilus MY3** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 6.4; T 18.5°C; salinity 7.74%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: terminal_oxidases
  - Rationale: soil AOA; ESCALATED — archaeal amoA not detected; same systematic issue
  - Source: Jung et al. 2016 ISME J

- **gid 1114 — Candidatus Nitrospira inopinata** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `none`; recipe `composed`; O2 n/a; pH 7.5; T 38.4°C; salinity 1.93%
  - Detected caps (≥0.50): Aerobic ammonia oxidation=0.916, Aerobic nitrite oxidation (canonical NOB=0.614
  - Positive markers: amoA, autotrophy, hao, nxrA
  - Rationale: complete ammonia oxidizer (comammox); lithotrophic_aerobic ✓ with both AOB AND NOB caps detected ✓ (amoA 0.916, nxrA 0.614)
  - Source: Daims et al. 2015 Nature; van Kessel et al. 2015 Nature

- **gid 1116 — Rhizobium leguminosarum** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.4; T 28.6°C; salinity 0.99%
  - Detected caps (≥0.50): Aerobic respiration=0.9, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: nifH, terminal_oxidases
  - Rationale: α-proteobacterial N-fixing symbiont; aerobic_chemotrophic ✓
  - Source: Young et al. 2006 Genome Biol

- **gid 1118 — Clostridium pasteurianum ATCC 6013** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.3; T 38.1°C; salinity 1.43%
  - Detected caps (≥0.50): Fermentation=0.9, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, nifH
  - Rationale: saccharolytic Clostridium with N-fixation; fermentative ✓
  - Source: ATCC 6013; Poehlein et al. 2015 Genome Announc

- **gid 1120 — Paenibacillus polymyxa ATCC 15970** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.2; T 32.1°C; salinity 1.81%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Aerobic respiration=0.6, Fermentation=0.55
  - Positive markers: nifH, terminal_oxidases
  - Rationale: diazotrophic spore-forming Firmicute; aerobic_chemotrophic ✓
  - Source: Kim et al. 2010 J Bacteriol

- **gid 1124 — Paracoccus denitrificans ATCC 19367** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 7.8; T 33.6°C; salinity 2.36%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.63
  - Positive markers: autotrophy, nosZ, soxB, terminal_oxidases
  - Rationale: model denitrifier; lithotrophic_aerobic ✓ with denitrification alt ✓
  - Source: ATCC 19367; Baker et al. 1998 J Bacteriol

- **gid 1134 — Candidatus Nitrospira neomarina DK** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `none`; recipe `composed`; O2 tolerant; pH 7.3; T 30.9°C; salinity 0.65%
  - Detected caps (≥0.50): Aerobic nitrite oxidation (canonical NOB=0.614
  - Positive markers: autotrophy, nxrA, soxB
  - Rationale: marine NOB; lithotrophic_aerobic ✓
  - Source: Haaijer et al. 2013 Front Microbiol

- **gid 1136 — Shewanella loihica PV-4** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.4; T 26.4°C; salinity 2.67%
  - Detected caps (≥0.50): Denitrification (NO3- to N2)=0.817, Dissimilatory nitrate reduction to ammon=0.645, Iron(III) reduction=0.597, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: mtrC_omcB, nosZ, nrfA, terminal_oxidases
  - Rationale: marine metal/nitrate respirer; anaerobic_respiratory ✓; mtrC ✓; denitrification alt ✓
  - Source: ATCC BAA-1088; Gao et al. 2008 J Bacteriol

### methane_metabolism  (21 genomes — PASS 17 / PARTIAL 0 / FAIL 4 / INSUFFICIENT 0)

- **gid 8 — Methanococcus jannaschii** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 5.8; T 82.5°C; salinity 0.19%
  - Detected caps (≥0.50): Methanogenesis=0.753
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH, qmoA
  - Rationale: hydrogenotrophic methanogen; mcrA, cooS, acsB detected; pH 5.8/T 82.5°C reasonable (true T_opt 85°C, pH 6)
  - Source: DSMZ 2661; Jones et al. 1983 Arch Microbiol

- **gid 28 — Candidatus Methanoperedens nitratireducens** — **PASS**
  - CultureForge: primary `anme_reverse_methanogenic`; alt `methanogenic, fermentative`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Methanogenesis=0.675, Fermentation=0.625, Nitrogen fixation=0.614, Anaerobic methane oxidation (ANME archae=0.59
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: ANME-2d nitrate-coupled AOM; correctly classified anme_reverse_methanogenic ✓
  - Source: Haroon et al. 2013 Nature

- **gid 900 — Methylococcus capsulatus Bath** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Aerobic methanotrophy (CH4 → CO2 via pMM=0.803, Nitrogen fixation=0.532, Aerobic respiration=0.5
  - Positive markers: amoA, autotrophy, hao, mmoX, nifH, pmoA, terminal_oxidases
  - Rationale: Type X methanotroph; methanotrophic ✓; pmoA marker hits expected; recipe with CH4 headspace ✓
  - Source: DSMZ 11084; Ward et al. 2004 PLoS Biol

- **gid 903 — Methanosarcina acetivorans C2A** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Methanogenesis=0.65, Nitrogen fixation=0.532
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: acetoclastic + methylotrophic methanogen; methanogenic ✓
  - Source: DSMZ 2834; Galagan et al. 2002 Genome Res

- **gid 1005 — Candidatus Methanocomedens sp. (ANME-2a)** — **FAIL**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 7.1; T 43.2°C; salinity 4.95%
  - Detected caps (≥0.50): Methanogenesis=0.65, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: ANME-2a SHOULD be anme_reverse_methanogenic like gid 28; instead classified as forward methanogenic — systematic miss; mcrA + acsB + cooS markers present (consistent with ANME)
  - Source: Knittel & Boetius 2009 Annu Rev Microbiol

- **gid 1006 — Candidatus Methanophaga sp. (ANME-1)** — **FAIL**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 7.0; T 49.4°C; salinity 0.99%
  - Detected caps (≥0.50): Methanogenesis=0.65
  - Positive markers: acsB_cdhC, autotrophy, mcrA, mcrBG, nifH
  - Rationale: ANME-1 SHOULD be anme_reverse_methanogenic; classified as forward methanogenic — systematic miss
  - Source: Hinrichs et al. 1999 Nature; Meyerdierks et al. 2010 Environ Microbiol

- **gid 1007 — Candidatus Methanovorans sp. (ANME-3)** — **FAIL**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.8; T 39.5°C; salinity 3.7%
  - Detected caps (≥0.50): Methanogenesis=0.65
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: ANME-3 SHOULD be anme_reverse_methanogenic; classified as forward methanogenic — systematic miss
  - Source: Niemann et al. 2006 Nature

- **gid 1011 — Methanopyrus kandleri AV19** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 5.5; T 100.9°C; salinity 7.06%
  - Detected caps (≥0.50): Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: hyperthermophilic hydrogenotrophic methanogen; methanogenic ✓; T 100.9°C ✓ (Topt 98°C)
  - Source: DSMZ 6324; Kurr et al. 1991 Arch Microbiol

- **gid 1035 — Methanospirillum hungatei JF-1** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.7; T 42.9°C; salinity 1.79%
  - Detected caps (≥0.50): Methanogenesis=0.65
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: hydrogenotrophic methanogen; methanogenic ✓
  - Source: DSMZ 864; Gunsalus et al. 2016 Stand Genomic Sci

- **gid 1042 — Methanocorpusculum labreanum Z** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.9; T 43.0°C; salinity 0.79%
  - Detected caps (≥0.50): Methanogenesis=0.65
  - Positive markers: autotrophy, mcrA, mcrBG, nifH
  - Rationale: hydrogenotrophic methanogen; methanogenic ✓
  - Source: DSMZ 4855; Anderson et al. 2009 Stand Genomic Sci

- **gid 1043 — Methanobrevibacter smithii ATCC 35061** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 5.6; T 47.2°C; salinity 4.19%
  - Detected caps (≥0.50): Methanogenesis=0.608
  - Positive markers: autotrophy, mcrA, mcrBG, nifH
  - Rationale: gut hydrogenotrophic methanogen; methanogenic ✓; T 47.2°C high (true 37°C); pH 5.6 low (true 6.9-7.4)
  - Source: DSMZ 861; Samuel et al. 2007 PNAS

- **gid 1052 — Methylacidiphilum infernorum V4** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `none`; recipe `composed`; O2 n/a; pH 6.1; T 55.6°C; salinity 0.0%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Aerobic methanotrophy (CH4 → CO2 via pMM=0.586
  - Positive markers: amoA, autotrophy, nifH, pmoA, terminal_oxidases
  - Rationale: thermoacidophilic methanotroph (Verrucomicrobia); methanotrophic ✓; amoA + pmoA hits ✓; pH 6.1 too high (true pH 2.0-2.5)
  - Source: DSMZ 28253; Hou et al. 2008 Biol Direct

- **gid 1061 — Methylorubrum extorquens AM1 (Methylobacterium)** — **FAIL**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic, fermentative, acetogenic`; recipe `composed`; O2 tolerant; pH 7.0; T 29.7°C; salinity 1.72%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Sulfur oxidation (bacterial SOX + archae=0.679, Fermentation=0.65, Acetogenesis (Wood-Ljungdahl)=0.605
  - Positive markers: nifH, pufLM, soxB, terminal_oxidases
  - Rationale: aerobic methylotroph (methanol/methylamine, NOT methane); classified primary=phototrophic — WRONG; pufLM false-positive (some Methylorubrum strains carry vestigial pufLM but they are not phototrophs); should be aerobic_chemotrophic with C1 substrates
  - Source: ATCC 14718; Vuilleumier et al. 2009 PLoS ONE

- **gid 1086 — Methylocystis parvus OBBP** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `aerobic_chemotrophic, fermentative, acetogenic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 6.0; T 33.7°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Aerobic methanotrophy (CH4 → CO2 via pMM=0.628, Nitrogen fixation=0.614, Acetogenesis (Wood-Ljungdahl)=0.605, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: amoA, hao, nifH, pmoA, terminal_oxidases
  - Rationale: Type II methanotroph; methanotrophic ✓; pmoA ✓
  - Source: ATCC 35066; del Cerro et al. 2012 J Bacteriol

- **gid 1103 — Methanobacterium formicicum** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.2; T 52.9°C; salinity 3.42%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, mcrA, mcrBG, nifH
  - Rationale: hydrogenotrophic methanogen; methanogenic ✓
  - Source: DSMZ 1535; Müller et al. 2012 J Bacteriol

- **gid 1109 — Methylotuvimicrobium alcaliphilum 20Z** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic, fermentative`; recipe `composed`; O2 tolerant; pH 7.2; T 29.6°C; salinity 2.12%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.655, Fermentation=0.65, Aerobic methanotrophy (CH4 → CO2 via pMM=0.628
  - Positive markers: amoA, hao, pmoA, soxB, terminal_oxidases
  - Rationale: haloalkaliphilic Type I methanotroph; methanotrophic ✓
  - Source: Vuilleumier et al. 2012 J Bacteriol

- **gid 1110 — Methanosarcina barkeri 227** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.5; T 40.1°C; salinity 2.8%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: versatile methanogen (H2/CO2, acetate, methanol, methylamines); methanogenic ✓
  - Source: DSMZ 800

- **gid 1122 — Methylobacter tundripaludum OWC-G53F** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `aerobic_chemotrophic, fermentative, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 6.6; T 25.5°C; salinity 1.04%
  - Detected caps (≥0.50): Aerobic methanotrophy (CH4 → CO2 via pMM=0.876, Aerobic respiration=0.85, Fermentation=0.65, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.589
  - Positive markers: amoA, mmoX, nifH, pmoA, terminal_oxidases
  - Rationale: Type Ia methanotroph; methanotrophic ✓
  - Source: Wartiainen et al. 2006 IJSEM

- **gid 1132 — Methanothermobacter thermautotrophicus Delta H** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 5.5; T 59.9°C; salinity 3.86%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, mcrA, mcrBG, nifH, soxB
  - Rationale: thermophilic hydrogenotrophic methanogen; methanogenic ✓; T 59.9°C low (true 65°C); pH 5.5 low (true 7.0)
  - Source: DSMZ 1053; Smith et al. 1997 J Bacteriol

- **gid 1135 — Methylocaldum szegediense** — **PASS**
  - CultureForge: primary `methanotrophic`; alt `aerobic_chemotrophic, acetogenic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 7.0; T 41.7°C; salinity 2.75%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Aerobic methanotrophy (CH4 → CO2 via pMM=0.628, Nitrogen fixation=0.614, Acetogenesis (Wood-Ljungdahl)=0.605, Sulfur oxidation (bacterial SOX + archae=0.589, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: amoA, autotrophy, cyc2, hao, nifH, pmoA, terminal_oxidases
  - Rationale: thermophilic Type I methanotroph; methanotrophic ✓
  - Source: Bodrossy et al. 1999 IJSEM

- **gid 1137 — Methanofollis liminatans** — **PASS**
  - CultureForge: primary `methanogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.6; T 45.2°C; salinity 0.76%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Methanogenesis=0.608
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mcrA, mcrBG, nifH
  - Rationale: hydrogenotrophic methanogen; methanogenic ✓
  - Source: DSMZ 4140; Zellner et al. 1989 Arch Microbiol

### sulfur_metabolism  (18 genomes — PASS 14 / PARTIAL 3 / FAIL 1 / INSUFFICIENT 0)

- **gid 11 — Acidithiobacillus ferrooxidans** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 4.3; T 34.9°C; salinity 0.25%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Nitrogen fixation=0.614, Iron(II) oxidation (acidophilic)=0.564, Sulfur oxidation (bacterial SOX + archae=0.555
  - Positive markers: autotrophy, cyc2, nifH, qmoA, terminal_oxidases, tetH
  - Rationale: acidophilic Fe(II)/S oxidizer; primary lithotrophic_aerobic ✓; cyc2 marker ✓; pH 4.3 ✓ (true pH 1.4-3, slightly high); T 34.9°C ✓
  - Source: DSMZ 14882; Valdés et al. 2008 BMC Genomics

- **gid 17 — Sulfurimonas denitrificans** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.7; T 28.1°C; salinity 1.7%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.557, Denitrification (NO3- to N2)=0.522
  - Positive markers: autotrophy, nosZ, soxB, terminal_oxidases
  - Rationale: microaerophilic chemolithoautotrophic sulfur oxidizer + denitrifier; primary lithotrophic_aerobic OK but anaerobic denitrification alt missing; T 28.1°C, pH 6.7 OK (true 22°C optimum)
  - Source: DSMZ 1251; Sievert et al. 2008 AEM

- **gid 31 — Allochromatium vinosum (Phase 1.5k validation)** — **PASS**
  - CultureForge: primary `phototrophic`; alt `lithotrophic_aerobic, aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.3; T 37.3°C; salinity 4.16%
  - Detected caps (≥0.50): Purple phototrophy=0.768, Sulfur oxidation (bacterial SOX + archae=0.655, Aerobic respiration=0.65, Nitrogen fixation=0.614
  - Positive markers: aprAB, autotrophy, cyc2, dsrAB, nifH, pufLM, soxB, terminal_oxidases
  - Rationale: purple sulfur phototroph (Chromatiaceae); phototrophic + sulfur ox cap ✓
  - Source: DSMZ 180; Weissgerber et al. 2011 Stand Genomic Sci

- **gid 1015 — Archaeoglobus fulgidus VC-16** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a; pH 6.6; T 82.7°C; salinity 2.16%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.745
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, dsrAB, qmoA
  - Rationale: hyperthermophilic sulfate reducer; anaerobic_respiratory ✓; dsrAB+aprAB+qmoA ✓; T 82.7°C ✓
  - Source: DSMZ 4304; Klenk et al. 1997 Nature

- **gid 1022 — Hydrogenobacter thermophilus TK-6** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory`; recipe `composed`; O2 n/a; pH 6.0; T 76.3°C; salinity 0.36%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.606, Denitrification (NO3- to N2)=0.522
  - Positive markers: nifH, nosZ, soxB, terminal_oxidases
  - Rationale: thermophilic chemolithoautotrophic H2 oxidizer; lithotrophic_aerobic ✓; T 76.3°C ✓
  - Source: DSMZ 6534; Arai et al. 2010 J Bacteriol

- **gid 1055 — Acidithiobacillus ferrooxidans ATCC 53993** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 4.4; T 34.9°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Nitrogen fixation=0.614, Iron(II) oxidation (acidophilic)=0.564, Sulfur oxidation (bacterial SOX + archae=0.555
  - Positive markers: autotrophy, cyc2, nifH, qmoA, terminal_oxidases, tetH
  - Rationale: duplicate of gid 11; PASS
  - Source: ATCC 53993

- **gid 1057 — Sulfurihydrogenibium azorense Az-Fu1** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `none`; recipe `composed`; O2 n/a; pH 6.3; T 68.9°C; salinity 0.0%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.557
  - Positive markers: autotrophy, soxB
  - Rationale: microaerophilic thermophilic H2/S oxidizer; lithotrophic_aerobic ✓; T 68.9°C ✓
  - Source: DSMZ 15241; Reysenbach et al. 2009 Stand Genomic Sci

- **gid 1058 — Persephonella marina EX-H1** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory`; recipe `composed`; O2 n/a; pH 6.1; T 68.0°C; salinity 1.82%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.557, Denitrification (NO3- to N2)=0.522
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, nosZ, soxB
  - Rationale: microaerophilic thermophilic H2/S oxidizer; lithotrophic_aerobic ✓
  - Source: DSMZ 14350; Götz et al. 2002 IJSEM

- **gid 1062 — Halothiobacillus neapolitanus c2** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 5.8; T 31.5°C; salinity 1.5%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.758
  - Positive markers: autotrophy, cyc2, sor, soxB, terminal_oxidases
  - Rationale: obligate chemolithoautotroph (S2O3, S0); lithotrophic_aerobic ✓
  - Source: ATCC 23641; Kovaleva et al. 2011 Stand Genomic Sci

- **gid 1075 — Sulfuricurvum kujiense DSM 16994** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 6.4; T 25.6°C; salinity 1.31%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.606
  - Positive markers: autotrophy, nifH, soxB, terminal_oxidases
  - Rationale: facultatively anaerobic sulfur oxidizer (with nitrate); primary lithotrophic_aerobic ✓; anaerobic denitrification alt missing
  - Source: DSMZ 16994; Han et al. 2012 Stand Genomic Sci

- **gid 1083 — Beggiatoa alba B18LD** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.4; T 29.9°C; salinity 0.61%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.655, Nitrogen fixation=0.614
  - Positive markers: autotrophy, nifH, soxB, terminal_oxidases
  - Rationale: filamentous chemolithoautotrophic S oxidizer; lithotrophic_aerobic ✓; should flag microaerophile (Beggiatoa lives at O2/sulfide interfaces) — recipe uses standard aerobic
  - Source: ATCC 33555; Mußmann et al. 2007 PLoS ONE

- **gid 1093 — Thioalkalivibrio nitratireducens DSM 14787** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 7.9; T 42.6°C; salinity 6.45%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.719
  - Positive markers: aprAB, autotrophy, cyc2, dsrAB, nosZ, sor, soxB, terminal_oxidases
  - Rationale: haloalkaliphilic sulfur oxidizer + denitrifier; lithotrophic_aerobic ✓ with denitrification alt ✓
  - Source: DSMZ 14787; Mu et al. 2011 J Bacteriol

- **gid 1096 — Thiobacillus thioparus DSM 505** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 5.9; T 32.6°C; salinity 1.36%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.778
  - Positive markers: aprAB, autotrophy, dsrAB, nosZ, qmoA, soxB, terminal_oxidases
  - Rationale: obligate chemolithoautotroph (S oxidizer); lithotrophic_aerobic ✓
  - Source: DSMZ 505; Hutt et al. 2018 Stand Genomic Sci

- **gid 1115 — Thiobacillus denitrificans RG** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.6; T 30.2°C; salinity 1.22%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.778
  - Positive markers: aprAB, autotrophy, cyc2, dsrAB, nosZ, qmoA, soxB, terminal_oxidases
  - Rationale: facultatively anaerobic S oxidizer + denitrifier; lithotrophic_aerobic ✓
  - Source: ATCC 25259; Beller et al. 2006 J Bacteriol

- **gid 1117 — Chlorobaculum limnaeum DSM 1677** — **PASS**
  - CultureForge: primary `phototrophic`; alt `anaerobic_respiratory, lithotrophic_aerobic`; recipe `composed`; O2 n/a; pH 7.0; T 34.0°C; salinity 0.69%
  - Detected caps (≥0.50): Green sulfur phototrophy=0.75, Dissimilatory sulfate reduction=0.745, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.581
  - Positive markers: aprAB, autotrophy, dsrAB, nifH, pscA_fmoA, qmoA, soxB, terminal_oxidases
  - Rationale: green sulfur phototroph; phototrophic ✓
  - Source: DSMZ 1677

- **gid 1127 — Caminibacter mediatlanticus TB-2** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 6.2; T 58.2°C; salinity 0.0%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy
  - Rationale: vent ε-proteobacterial H2-oxidizing N/S reducer; ESCALATED — only autotrophy marker; no H2-oxidizing-anaerobic mode in capability library
  - Source: DSMZ 16013; Voordeckers et al. 2008 IJSEM

- **gid 1128 — Acidithiobacillus thiooxidans ATCC 19377** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 4.2; T 34.0°C; salinity 0.98%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.623, Aerobic respiration=0.6
  - Positive markers: autotrophy, soxB, terminal_oxidases, tetH
  - Rationale: acidophilic S oxidizer; lithotrophic_aerobic ✓; pH 4.2 (true 2.0-3.0 — a bit high)
  - Source: ATCC 19377

- **gid 1131 — Acidithiobacillus caldus strain MELC5** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 4.8; T 42.3°C; salinity 0.23%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.806, Aerobic respiration=0.6
  - Positive markers: autotrophy, qmoA, sor, soxB, terminal_oxidases
  - Rationale: thermoacidophilic S oxidizer; lithotrophic_aerobic ✓
  - Source: Valdés et al. 2009 BMC Genomics

### phototrophy  (14 genomes — PASS 12 / PARTIAL 1 / FAIL 1 / INSUFFICIENT 0)

- **gid 24 — Chloroflexus aurantiacus** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, fermentative, acetogenic, lithotrophic_aerobic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.65, Fermentation=0.65, Acetogenesis (Wood-Ljungdahl)=0.642, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: autotrophy, nifH, pufLM, terminal_oxidases
  - Rationale: filamentous anoxygenic phototroph; phototrophic ✓
  - Source: DSMZ 635; Tang et al. 2011 BMC Genomics

- **gid 1010 — Chlorobaculum tepidum TLS** — **PASS**
  - CultureForge: primary `phototrophic`; alt `anaerobic_respiratory, lithotrophic_aerobic`; recipe `composed`; O2 n/a; pH 6.6; T 34.4°C; salinity 0.7%
  - Detected caps (≥0.50): Green sulfur phototrophy=0.75, Dissimilatory sulfate reduction=0.745, Sulfur oxidation (bacterial SOX + archae=0.63, Nitrogen fixation=0.614
  - Positive markers: aprAB, autotrophy, dsrAB, nifH, pscA_fmoA, qmoA, soxB
  - Rationale: thermophilic green sulfur phototroph; phototrophic ✓; pscA, dsrAB, soxB markers ✓; T 34.4°C — true Topt is 47-48°C (under-prediction)
  - Source: ATCC 49652; Eisen et al. 2002 PNAS

- **gid 1018 — Synechocystis sp. PCC 6803** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.5; T 36.4°C; salinity 0.28%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: model cyanobacterium; phototrophic ✓; pH 8.5 ✓
  - Source: Pasteur PCC 6803; Kaneko et al. 1996 DNA Res

- **gid 1021 — Microcystis aeruginosa NIES-843** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.4; T 37.9°C; salinity 0.64%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: freshwater bloom-forming cyanobacterium; phototrophic ✓
  - Source: NIES-843; Kaneko et al. 2007 DNA Res

- **gid 1024 — Gloeobacter violaceus PCC 7421** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 8.5; T 33.9°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: ancestral cyanobacterium without thylakoids; phototrophic ✓
  - Source: Pasteur PCC 7421; Nakamura et al. 2003 DNA Res

- **gid 1025 — Prochlorococcus marinus MIT 9313** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 8.4; T 22.9°C; salinity 0.85%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: marine cyanobacterium; phototrophic ✓; T 22.9°C ✓; pH 8.4 ✓
  - Source: Rocap et al. 2003 Nature

- **gid 1028 — Synechococcus elongatus PCC 7942** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 8.8; T 44.6°C; salinity 1.36%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Oxygenic phototrophy=0.75, Sulfur oxidation (bacterial SOX + archae=0.615
  - Positive markers: autotrophy, nifH, psaA_psbA, terminal_oxidases
  - Rationale: freshwater cyanobacterium; phototrophic ✓; T 44.6°C high (true 26-30°C); pH 8.8 ✓
  - Source: Pasteur PCC 7942

- **gid 1030 — Rhodobacter sphaeroides 2.4.1** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 7.7; T 32.3°C; salinity 1.63%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: autotrophy, nifH, pufLM, terminal_oxidases
  - Rationale: purple non-sulfur phototroph; phototrophic ✓ with aerobic alt ✓
  - Source: ATCC 17023

- **gid 1044 — Roseiflexus castenholzii DSM 13941** — **PASS**
  - CultureForge: primary `phototrophic`; alt `fermentative, lithotrophic_aerobic`; recipe `composed`; O2 n/a; pH 8.0; T 49.5°C; salinity 0.0%
  - Detected caps (≥0.50): Fermentation=0.9, Purple phototrophy=0.65, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: autotrophy, nifH, pufLM, terminal_oxidases
  - Rationale: filamentous anoxygenic phototroph (thermophile); phototrophic ✓; pufLM ✓
  - Source: DSMZ 13941; van der Meer et al. 2010 Photosynth Res

- **gid 1051 — Heliomicrobium modesticaldum Ice1 (Heliobacterium)** — **FAIL**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.3; T 45.7°C; salinity 0.65%
  - Detected caps (≥0.50): Organohalide respiration=0.65, Nitrogen fixation=0.614, Fermentation=0.6
  - Positive markers: nifH, rdhA
  - Rationale: anoxygenic phototrophic Firmicute (heliobacteria); classified anaerobic_respiratory — WRONG; no purple/green phototrophy detected because heliobacteria use unique BChl g system (PufLM-like not in current marker set as heliobacterial reaction center)
  - Source: DSMZ 9504; Sattley et al. 2008 J Bacteriol

- **gid 1059 — Rhodobacter capsulatus SB 1003** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 7.6; T 30.4°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.563, Denitrification (NO3- to N2)=0.548
  - Positive markers: autotrophy, nifH, nosZ, pufLM, terminal_oxidases
  - Rationale: purple non-sulfur phototroph; phototrophic ✓ with extensive alts ✓
  - Source: DSMZ 1710; Strnad et al. 2010 J Bacteriol

- **gid 1077 — Rhodopseudomonas palustris CGA009** — **PASS**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, anaerobic_respiratory, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 6.6; T 29.9°C; salinity 0.62%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Purple phototrophy=0.768, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.557
  - Positive markers: autotrophy, nifH, nosZ, pufLM, soxB, terminal_oxidases
  - Rationale: metabolic chameleon; phototrophic ✓ with multiple alt modes ✓ (extensive)
  - Source: ATCC BAA-98

- **gid 1101 — Gemmatimonas phototrophica** — **PARTIAL**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, fermentative`; recipe `composed`; O2 tolerant; pH 7.7; T 28.1°C; salinity 0.14%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Fermentation=0.65
  - Positive markers: autotrophy, nifH, pufLM
  - Rationale: aerobic anoxygenic phototroph (AAP); phototrophic ✓ but primary lifestyle is heterotrophic with BChl supplementation — aerobic_chemotrophic might be a better primary
  - Source: Zeng et al. 2014 PNAS

- **gid 1121 — Halorhodospira halochloris DSM 1059** — **PASS**
  - CultureForge: primary `phototrophic`; alt `none`; recipe `composed`; O2 tolerant; pH 8.5; T 38.6°C; salinity 9.46%
  - Detected caps (≥0.50): Purple phototrophy=0.768, Nitrogen fixation=0.614
  - Positive markers: autotrophy, dsrAB, nifH, pufLM
  - Rationale: extremely halophilic purple sulfur phototroph; phototrophic ✓; pH 8.5 ✓
  - Source: DSMZ 1059

### fermentation  (13 genomes — PASS 10 / PARTIAL 2 / FAIL 1 / INSUFFICIENT 0)

- **gid 10 — Lactiplantibacillus plantarum (synonym Lactobacillus plantarum)** — **PARTIAL**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 tolerant; pH 5.8; T 18.8°C; salinity 2.06%
  - Detected caps (≥0.50): Fermentation=0.706
  - Positive markers: (none)
  - Rationale: aerotolerant LAB; primary mode fermentative ✓; pH 5.8 OK; T 18.8°C too low (true 30-37°C) — likely GenomeSPOT under-predicting mesophile
  - Source: DSMZ 20174; Zheng et al. 2020 IJSEM

- **gid 12 — Clostridium acetobutylicum** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.2; T 36.3°C; salinity 2.05%
  - Detected caps (≥0.50): Fermentation=0.9, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, nifH
  - Rationale: ABE-fermenting Clostridium; fermentative ✓; pH 6.2 ✓; T 36.3°C ✓
  - Source: DSMZ 792; Nölling et al. 2001 J Bacteriol

- **gid 15 — Campylobacter jejuni** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 6.6; T 24.5°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.9, Fermentation=0.637, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: terminal_oxidases
  - Rationale: microaerophilic host-associated; aerobic_chemotrophic close but should flag microaerophile (5% O2); no physical-format hint; T 24.5°C is low (true ~42°C avian host)
  - Source: DSMZ 4688; Parkhill et al. 2000 Nature

- **gid 32 — Escherichia coli K-12** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 7.4; T 30.3°C; salinity 2.28%
  - Detected caps (≥0.50): Aerobic respiration=0.9, Fermentation=0.65, Dissimilatory nitrate reduction to ammon=0.645
  - Positive markers: nrfA, terminal_oxidases
  - Rationale: facultative anaerobic prototroph; primary aerobic_chemotrophic + alt fermentative + DNRA ✓; pH 7.4 T 30°C ✓
  - Source: DSMZ 30083; Blattner et al. 1997 Science

- **gid 1009 — Lactococcus lactis subsp. lactis IL1403** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 tolerant; pH 5.8; T 26.3°C; salinity 0.51%
  - Detected caps (≥0.50): Fermentation=0.9
  - Positive markers: (none)
  - Rationale: homofermentative LAB; fermentative ✓; pH 5.8 ✓; T 26.3°C low (true 30°C) but acceptable
  - Source: DSMZ 20481; Bolotin et al. 2001 Genome Res

- **gid 1016 — Clostridium acetobutylicum ATCC 824** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.1; T 36.2°C; salinity 2.39%
  - Detected caps (≥0.50): Fermentation=0.9, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, nifH
  - Rationale: duplicate of gid 12; PASS
  - Source: ATCC 824

- **gid 1063 — Prevotella ruminicola 23** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.8; T 41.9°C; salinity 3.83%
  - Detected caps (≥0.50): Fermentation=0.706
  - Positive markers: (none)
  - Rationale: rumen anaerobic fermenter; fermentative ✓
  - Source: ATCC 19189; Purushe et al. 2010 Microb Ecol

- **gid 1064 — Bacteroides fragilis NCTC 9343** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.8; T 40.5°C; salinity 0.59%
  - Detected caps (≥0.50): Fermentation=0.775
  - Positive markers: (none)
  - Rationale: gut aerotolerant anaerobic fermenter; fermentative ✓
  - Source: ATCC 25285; Cerdeño-Tárraga et al. 2005 Science

- **gid 1079 — Acetoanaerobium sticklandii DSM 519 (Clostridium sticklandii)** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.6; T 35.5°C; salinity 2.26%
  - Detected caps (≥0.50): Acetogenesis (Wood-Ljungdahl)=0.75, Fermentation=0.727
  - Positive markers: acsB_cdhC, cooS_cdhA
  - Rationale: Stickland amino-acid fermenter (pairwise oxidation/reduction of amino acids); classified primary=acetogenic — WRONG; despite Wood-Ljungdahl pathway in some pyranose conditions, primary growth is Stickland fermentation; acsB+cooS markers detected drive WL false-positive
  - Source: DSMZ 519; Fonknechten et al. 2010 BMC Genomics

- **gid 1081 — Lactiplantibacillus plantarum WCFS1** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 tolerant; pH 5.8; T 18.9°C; salinity 2.07%
  - Detected caps (≥0.50): Fermentation=0.706
  - Positive markers: (none)
  - Rationale: homofermentative LAB; fermentative ✓; T 18.9°C low (under-predicted) — same as gid 10
  - Source: WCFS1; Kleerebezem et al. 2003 PNAS

- **gid 1087 — Megasphaera elsdenii DSM 20460** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.1; T 36.5°C; salinity 3.1%
  - Detected caps (≥0.50): Fermentation=0.761
  - Positive markers: aprAB, autotrophy, nifH
  - Rationale: rumen lactate/propionate fermenter; fermentative ✓
  - Source: DSMZ 20460; Marx et al. 2011 Stand Genomic Sci

- **gid 1088 — Selenomonas ruminantium subsp. lactilytica** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 7.0; T 35.6°C; salinity 4.61%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Fermentation=0.567
  - Positive markers: aprAB, nifH
  - Rationale: rumen anaerobic fermenter; fermentative ✓
  - Source: Kingsley & Hoeniger 1973 Can J Microbiol

- **gid 1100 — Peptoclostridium acidaminophilum DSM 3953** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 7.5; T 40.0°C; salinity 2.26%
  - Detected caps (≥0.50): Fermentation=0.796
  - Positive markers: (none)
  - Rationale: amino acid fermenter; fermentative ✓
  - Source: DSMZ 3953

### iron_metals  (9 genomes — PASS 3 / PARTIAL 4 / FAIL 2 / INSUFFICIENT 0)

- **gid 13 — Geobacter sulfurreducens** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a; pH 6.5; T 31.5°C; salinity 0.67%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Iron(III) reduction=0.597
  - Positive markers: acsB_cdhC, cooS_cdhA, mtrC_omcB, nifH, terminal_oxidases
  - Rationale: Fe(III) reducer; anaerobic_respiratory ✓; mtrC/omcB marker ✓; T 31.5°C, pH 6.5 ✓
  - Source: DSMZ 12127; Methé et al. 2003 Science

- **gid 1013 — Geobacter sulfurreducens PCA** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a; pH 6.5; T 31.5°C; salinity 0.67%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Iron(III) reduction=0.597
  - Positive markers: acsB_cdhC, cooS_cdhA, mtrC_omcB, nifH, terminal_oxidases
  - Rationale: duplicate of gid 13; same prediction; PASS
  - Source: DSMZ 12127

- **gid 1031 — Geobacter metallireducens GS-15** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `none`; recipe `composed`; O2 n/a; pH 6.3; T 30.9°C; salinity 0.0%
  - Detected caps (≥0.50): Acetogenesis (Wood-Ljungdahl)=0.662, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, mtrC_omcB, nifH, terminal_oxidases
  - Rationale: Fe(III)-reducing anaerobe; classified primary=acetogenic — WRONG; WL false-positive (0.662) from acsB+cooS hits (Geobacter has CODH/acetyl-CoA-synthase but not for autotrophic WL); should be anaerobic_respiratory like its sister G. sulfurreducens
  - Source: DSMZ 7210; Aklujkar et al. 2009 BMC Microbiol

- **gid 1033 — Anaeromyxobacter dehalogenans 2CP-C** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, fermentative, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.9; T 45.7°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Sulfur oxidation (bacterial SOX + archae=0.557, Denitrification (NO3- to N2)=0.522
  - Positive markers: autotrophy, nosZ, soxB, terminal_oxidases
  - Rationale: facultative microaerophile/anaerobe doing organohalide + Fe(III) + nitrate respiration; classified lithotrophic_aerobic — wrong primary; aerobic respiration is opportunistic at low O2, primary lifestyle is anaerobic respiration
  - Source: DSMZ 21875; Sanford et al. 2002 AEM

- **gid 1068 — Gallionella capsiferriformans ES-2** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `none`; recipe `composed`; O2 tolerant; pH 5.7; T 27.8°C; salinity 0.78%
  - Detected caps (≥0.50): Aerobic respiration=0.85
  - Positive markers: autotrophy, terminal_oxidases
  - Rationale: microaerophilic Fe(II) oxidizer; classified aerobic_chemotrophic — should be lithotrophic_aerobic (Fe-autotroph); microaerophile flag missing
  - Source: DSMZ 18553; Emerson et al. 2013 Front Microbiol

- **gid 1069 — Shewanella oneidensis MR-1** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.5; T 21.8°C; salinity 0.88%
  - Detected caps (≥0.50): Dissimilatory nitrate reduction to ammon=0.645, Iron(III) reduction=0.597, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: mtrC_omcB, nrfA, terminal_oxidases
  - Rationale: metal-respiring facultative anaerobe; anaerobic_respiratory ✓ with aerobic alt; mtrC ✓
  - Source: ATCC 700550; Heidelberg et al. 2002 Nat Biotechnol

- **gid 1070 — Ferroplasma acidarmanus Fer1** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 2.7; T 38.9°C; salinity 4.49%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy, sor
  - Rationale: acidophilic Fe(II)-oxidizing archaeon (Thermoplasmatales); ESCALATED — no acidophilic archaeal Fe oxidation mode in detector library; pH 2.7 ✓
  - Source: DSMZ 28986; Allen et al. 2007 ISME J

- **gid 1072 — Mariprofundus ferrooxydans PV-1** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 6.1; T 29.4°C; salinity 1.98%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.615
  - Positive markers: autotrophy, terminal_oxidases
  - Rationale: marine microaerophilic Fe(II) oxidizer (Zetaproteobacterium); classified aerobic_chemotrophic — should be lithotrophic_aerobic; microaerophile flag missing
  - Source: ATCC BAA-1545; Singer et al. 2011 PLoS ONE

- **gid 1089 — Leptospirillum ferrooxidans C2-3** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 5.2; T 24.2°C; salinity 0.0%
  - Detected caps (≥0.50): Nitrogen fixation=0.614, Aerobic respiration=0.6, Iron(II) oxidation (acidophilic)=0.564
  - Positive markers: aprAB, cyc2, nifH, tetH
  - Rationale: obligate acidophilic Fe(II) oxidizer; lithotrophic_aerobic ✓ but pH 5.2 predicted is way too high (true pH 1.5-2.5); cyc2 absent in detected caps
  - Source: DSMZ 2391; Levicán et al. 2008 BMC Genomics

### sulfate_reduction  (7 genomes — PASS 7 / PARTIAL 0 / FAIL 0 / INSUFFICIENT 0)

- **gid 7 — Desulfovibrio vulgaris Hildenborough** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.3; T 28.8°C; salinity 0.75%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65, Dissimilatory nitrate reduction to ammon=0.645
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, dsrAB, nrfA, qmoA, terminal_oxidases
  - Rationale: anaerobic sulfate reducer; predicted anaerobic_respiratory with dsrAB+aprAB+qmoA markers; pH 7.3, T 28.8°C consistent with DSM 644 (T 30-37°C, pH 6.6-7.5)
  - Source: DSMZ 644; Heidelberg et al. 2004 Nat Biotechnol

- **gid 1048 — Desulfosudis oleivorans Hxd3** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.9; T 33.0°C; salinity 0.58%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, dsrAB, qmoA
  - Rationale: alkane-oxidizing sulfate reducer; anaerobic_respiratory ✓
  - Source: DSMZ 6200; Cravo-Laureau et al. 2007 IJSEM

- **gid 1054 — Desulforapulum autotrophicum HRM2** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.2; T 31.9°C; salinity 0.04%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, dsrAB, nifH, qmoA, terminal_oxidases
  - Rationale: complete-oxidizing sulfate reducer; anaerobic_respiratory ✓
  - Source: DSMZ 3382; Strittmatter et al. 2009 Environ Microbiol

- **gid 1076 — Desulfobulbus propionicus 1pr3** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.8; T 33.3°C; salinity 1.34%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: aprAB, dsrAB, nifH, qmoA
  - Rationale: propionate-oxidizing sulfate reducer; anaerobic_respiratory ✓
  - Source: DSMZ 2032; Pagani et al. 2011 Stand Genomic Sci

- **gid 1119 — Desulfovibrio piger** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.9; T 36.2°C; salinity 0.0%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.745, Fermentation=0.65, Dissimilatory nitrate reduction to ammon=0.645
  - Positive markers: aprAB, dsrAB, nrfA, qmoA
  - Rationale: gut sulfate reducer; anaerobic_respiratory ✓
  - Source: ATCC 29098

- **gid 1123 — Thermodesulfobacterium commune** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.8; T 67.9°C; salinity 0.0%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.745, Fermentation=0.637
  - Positive markers: acsB_cdhC, aprAB, dsrAB, qmoA
  - Rationale: thermophilic sulfate reducer; anaerobic_respiratory ✓; T 67.9°C ✓
  - Source: DSMZ 2178

- **gid 1125 — Desulfobacter hydrogenophilus AcRS1** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.8; T 30.9°C; salinity 0.0%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: aprAB, dsrAB, nifH, qmoA, terminal_oxidases
  - Rationale: marine sulfate reducer; anaerobic_respiratory ✓
  - Source: DSMZ 3380

### carbon_fixation  (6 genomes — PASS 2 / PARTIAL 2 / FAIL 2 / INSUFFICIENT 0)

- **gid 1014 — Aquifex aeolicus VF5** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `none`; recipe `composed`; O2 n/a; pH 6.4; T 90.3°C; salinity 0.11%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.623
  - Positive markers: sor, soxB, terminal_oxidases
  - Rationale: microaerophilic H2/S oxidizer; lithotrophic_aerobic ✓; T 90.3°C ✓; pH 6.4 ✓
  - Source: DSMZ 7244; Deckert et al. 1998 Nature

- **gid 1029 — Carboxydothermus hydrogenoformans Z-2901** — **PARTIAL**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.8; T 58.8°C; salinity 0.0%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.579, Fermentation=0.529
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA, dsrAB, qmoA
  - Rationale: CO-oxidizing H2-producing thermophile (CO + H2O → CO2 + H2); anaerobic_respiratory close but CO trophy not labeled; T 58.8°C ✓
  - Source: DSMZ 6008; Wu et al. 2005 PLoS Genet

- **gid 1046 — Ignicoccus hospitalis KIN4/I** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 6.2; T 95.4°C; salinity 0.0%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy
  - Rationale: anaerobic hyperthermophilic H2/S0 autotroph (Crenarchaeota); ESCALATED with only autotrophy marker; no H2/S0 anaerobic chemolithoautotrophy mode in capability library
  - Source: DSMZ 18386; Podar et al. 2008 BMC Genomics

- **gid 1084 — Acetobacterium woodii DSM 1030 (duplicate of 22)** — **PASS**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.8; T 32.1°C; salinity 0.0%
  - Detected caps (≥0.50): Acetogenesis (Wood-Ljungdahl)=0.95, Fermentation=0.727, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH
  - Rationale: model acetogen; acetogenic ✓
  - Source: DSMZ 1030

- **gid 1111 — Metallosphaera sedula ARS120-2** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `none`; recipe `composed`; O2 n/a; pH 3.6; T 65.2°C; salinity 0.7%
  - Detected caps (≥0.50): Aerobic respiration=0.6
  - Positive markers: autotrophy, terminal_oxidases, tetH, tqoDoxA, tqoDoxD
  - Rationale: thermoacidophilic chemolithoautotrophic Fe/S oxidizer (Sulfolobales); classified aerobic_chemotrophic — should be lithotrophic_aerobic; pH 3.6 ✓
  - Source: DSMZ 5348; Auernik et al. 2008 AEM

- **gid 1112 — Neomoorella thermoacetica DSM 521 (Moorella thermoacetica)** — **FAIL**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.7; T 57.3°C; salinity 0.0%
  - Detected caps (≥0.50): Fermentation=0.831
  - Positive markers: acsB_cdhC, cooS_cdhA, dsrAB, qmoA
  - Rationale: model thermophilic acetogen (heterotrophic acetogenesis); classified fermentative — WRONG; WL detected but primary mode should be acetogenic like Clostridium ljungdahlii/Sporomusa ovata
  - Source: DSMZ 521; Pierce et al. 2008 Environ Microbiol

### syntrophy  (7 genomes — PASS 2 / PARTIAL 3 / FAIL 2 / INSUFFICIENT 0)

- **gid 21 — Syntrophomonas wolfei** — **PASS**
  - CultureForge: primary `syntrophic`; alt `none`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Syntrophy=0.7
  - Positive markers: nifH, qmoA
  - Rationale: obligate syntroph (fatty acid β-oxidizer); primary syntrophic ✓; nifH ✓
  - Source: DSMZ 2245; Sieber et al. 2010 Environ Microbiol

- **gid 29 — Candidatus Prometheoarchaeum syntrophicum** — **PASS**
  - CultureForge: primary `syntrophic`; alt `methanogenic, acetogenic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Methanogenesis=0.9, Syntrophy=0.7, Acetogenesis (Wood-Ljungdahl)=0.642
  - Positive markers: autotrophy, rdhA
  - Rationale: Asgard archaeon (MK-D1); syntrophic primary ✓; methanogenesis (0.9) alt is false-positive — MK-D1 has no mcrA and no published methanogenic potential
  - Source: Imachi et al. 2020 Nature

- **gid 1034 — Syntrophus aciditrophicus SB** — **PARTIAL**
  - CultureForge: primary `fermentative`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a; pH 6.9; T 39.9°C; salinity 0.04%
  - Detected caps (≥0.50): Fermentation=0.727, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: autotrophy
  - Rationale: obligate syntrophic benzoate degrader; classified fermentative — syntrophic should be primary
  - Source: DSMZ 26646; McInerney et al. 2007 PNAS

- **gid 1038 — Syntrophomonas wolfei subsp. wolfei Goettingen G311** — **PARTIAL**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 6.8; T 48.7°C; salinity 0.31%
  - Detected caps (≥0.50): Fermentation=0.727
  - Positive markers: nifH, qmoA
  - Rationale: duplicate of gid 21 (subsp. variant); classified fermentative — should be syntrophic like gid 21
  - Source: DSMZ 2245

- **gid 1041 — Syntrophobacter fumaroxidans MPOB** — **PARTIAL**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.1; T 40.8°C; salinity 0.59%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, dsrAB, nifH, qmoA
  - Rationale: syntrophic propionate oxidizer that can also reduce sulfate; classified anaerobic_respiratory ✓ in part; syntrophic lifestyle missed as primary
  - Source: DSMZ 10017; Plugge et al. 2012 Stand Genomic Sci

- **gid 1126 — Pelotomaculum schinkii HH** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `fermentative, lithotrophic_aerobic`; recipe `composed`; O2 n/a; pH 7.1; T 43.3°C; salinity 0.0%
  - Detected caps (≥0.50): Fermentation=0.831, Acetogenesis (Wood-Ljungdahl)=0.75, Nitrogen fixation=0.614, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH
  - Rationale: obligate syntrophic propionate-oxidizing Firmicute; classified primary=acetogenic — WRONG; syntrophic should be primary (it grows on propionate ONLY in co-culture with H2 scavenger)
  - Source: DSMZ 17574; Imachi et al. 2007 IJSEM

- **gid 1130 — Syntrophorhabdus aromaticivorans** — **FAIL**
  - CultureForge: primary `acetogenic`; alt `fermentative, aerobic_chemotrophic`; recipe `composed`; O2 n/a; pH 6.7; T 41.4°C; salinity 0.46%
  - Detected caps (≥0.50): Fermentation=0.831, Acetogenesis (Wood-Ljungdahl)=0.719, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: acsB_cdhC, autotrophy, cooS_cdhA
  - Rationale: obligate syntrophic aromatics degrader; classified acetogenic — WRONG; same systematic issue as 1126 (syntrophy mode lost to WL false-positive)
  - Source: DSMZ 17771; Nobu et al. 2015 Environ Microbiol

### extreme_archaea  (8 genomes — PASS 3 / PARTIAL 1 / FAIL 4 / INSUFFICIENT 0)

- **gid 9 — Thermus aquaticus YT-1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.6; T 67.7°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.55, Fermentation=0.5
  - Positive markers: autotrophy
  - Rationale: thermophilic aerobic heterotroph; T 67.7°C and pH 7.6 within Thermus range (T 50-80°C, pH 7-8.5)
  - Source: DSMZ 625; Brock & Freeze 1969 J Bacteriol

- **gid 14 — Sulfolobus acidocaldarius** — **PARTIAL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `none`; recipe `composed`; O2 n/a; pH 4.0; T 74.9°C; salinity 1.16%
  - Detected caps (≥0.50): Aerobic respiration=0.5
  - Positive markers: autotrophy, terminal_oxidases
  - Rationale: thermoacidophile; aerobic_chemotrophic ✓ but sulfur oxidation lithotrophy not flagged as primary — Sulfolobus is a chemolithotroph on S0/Fe2+; pH 4.0/T 74.9°C ✓
  - Source: DSMZ 639; Chen et al. 2005 J Bacteriol

- **gid 26 — Picrophilus torridus DSM 9790** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 2.6; T 45.6°C; salinity 4.05%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy, sor, tetH, tqoDoxD
  - Rationale: thermoacidophilic heterotroph (pH 0-3.5, T 60°C); ESCALATED — no aerobic_chemotrophic-acidophile profile; predicted pH 2.6 ✓ at least; markers sor+tetH+tqoDoxD detected but did not compose recipe
  - Source: DSMZ 9790; Fütterer et al. 2004 PNAS

- **gid 27 — Thermotoga maritima** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Fermentation=0.775
  - Positive markers: (none)
  - Rationale: hyperthermophilic fermenter; fermentative ✓ (true 80°C — predicted T blank in output)
  - Source: DSMZ 3109; Nelson et al. 1999 Nature

- **gid 1012 — Pyrococcus furiosus DSM 3638** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a; pH 7.0; T 90.8°C; salinity 0.0%
  - Detected caps (≥0.50): Organohalide respiration=0.65
  - Positive markers: autotrophy, rdhA
  - Rationale: hyperthermophilic peptide/sugar fermenter with S0 respiration; anaerobic_respiratory ✓; T 90.8°C ✓
  - Source: DSMZ 3638; Robb et al. 2001 Methods Enzymol

- **gid 1019 — Thermococcus kodakarensis KOD1** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 6.3; T 81.0°C; salinity 2.31%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy
  - Rationale: hyperthermophilic S0-respiring fermenter; ESCALATED — no primary mode detected; like Pyrococcus furiosus should map to anaerobic_respiratory
  - Source: JCM 12380; Fukui et al. 2005 Genome Res

- **gid 1047 — Caldivirga maquilingensis IC-167** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 3.8; T 75.3°C; salinity 0.0%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: aprAB, autotrophy, dsrAB, tetH
  - Rationale: thermoacidophilic facultatively anaerobic crenarchaeote (S0/thiosulfate reduction); ESCALATED with dsrAB+aprAB+autotrophy+tetH markers but no mode resolved
  - Source: DSMZ 13496; Itoh et al. 1999 IJSEM

- **gid 1129 — Stygiolobus azoricus DSM 6296** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 4.0; T 80.6°C; salinity 0.0%
  - Detected caps (≥0.50): none above 0.50
  - Positive markers: autotrophy, tetH, tqoDoxA, tqoDoxD
  - Rationale: thermoacidophilic anaerobic S0 reducer (Sulfolobales); ESCALATED — no anaerobic crenarchaeote sulfur reduction mode; pH 4.0 ✓
  - Source: DSMZ 6296; Segerer et al. 1991 IJSEM

### marine_user_interest  (4 genomes — PASS 1 / PARTIAL 3 / FAIL 0 / INSUFFICIENT 0)

- **gid 1027 — Pelagibacter ubique HTCC1062** — **PARTIAL**
  - CultureForge: primary `halophilic_with_rhodopsin`; alt `aerobic_chemotrophic, lithotrophic_aerobic, fermentative`; recipe `composed`; O2 tolerant; pH 7.1; T 27.3°C; salinity 3.36%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.667, Bacteriorhodopsin=0.6, Fermentation=0.567
  - Positive markers: aprAB, rhodopsin, terminal_oxidases
  - Rationale: marine heterotroph with proteorhodopsin (energy supplement, not primary); halophilic_with_rhodopsin overstates rhodopsin role; should be aerobic_chemotrophic with rhodopsin aux
  - Source: Giovannoni et al. 2005 Science

- **gid 1040 — Magnetococcus marinus MC-1** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 6.4; T 23.5°C; salinity 3.05%
  - Detected caps (≥0.50): Sulfur oxidation (bacterial SOX + archae=0.778, Nitrogen fixation=0.614, Aerobic respiration=0.6
  - Positive markers: dsrAB, nifH, soxB, terminal_oxidases
  - Rationale: microaerophilic chemolithoautotrophic magnetite producer; lithotrophic_aerobic OK direction; should flag microaerophile (recipe uses default aerobic)
  - Source: ATCC BAA-1437; Schübbe et al. 2009 AEM

- **gid 1073 — Roseobacter litoralis Och 149** — **PARTIAL**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, anaerobic_respiratory, lithotrophic_aerobic, fermentative`; recipe `composed`; O2 tolerant; pH 8.2; T 23.9°C; salinity 2.98%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Denitrification (NO3- to N2)=0.71, Sulfur oxidation (bacterial SOX + archae=0.679, Fermentation=0.65
  - Positive markers: nifH, nosZ, pufLM, soxB, terminal_oxidases
  - Rationale: aerobic anoxygenic phototroph (AAP); phototrophic ✓ — but Roseobacter primary lifestyle is heterotrophic with BChl as supplemental energy harvest; aerobic_chemotrophic might be more accurate primary
  - Source: DSMZ 6996; Kalhoefer et al. 2011 BMC Genomics

- **gid 1113 — Vibrio natriegens ATCC 14048** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.7; T 29.6°C; salinity 3.68%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Nitrogen fixation=0.614
  - Positive markers: nifH, terminal_oxidases
  - Rationale: fast-growing facultative anaerobic marine heterotroph; aerobic_chemotrophic ✓
  - Source: ATCC 14048; Wang et al. 2013 J Bacteriol

### manganese_metabolism  (4 genomes — PASS 3 / PARTIAL 0 / FAIL 1 / INSUFFICIENT 0)

- **gid 1050 — Pseudomonas putida GB-1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative, lithotrophic_aerobic`; recipe `composed`; O2 tolerant; pH 7.3; T 29.4°C; salinity 2.4%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Sulfur oxidation (bacterial SOX + archae=0.511
  - Positive markers: cyc2, terminal_oxidases
  - Rationale: Mn(II)-oxidizing heterotroph; aerobic_chemotrophic ✓; Mn oxidation is opportunistic not autotrophic
  - Source: ATCC BAA-1234; Banh et al. 2013 BMC Genomics

- **gid 1071 — Aurantimonas manganoxydans SI85-9A1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `acetogenic`; recipe `composed`; O2 tolerant; pH 7.2; T 25.5°C; salinity 2.97%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Acetogenesis (Wood-Ljungdahl)=0.605
  - Positive markers: autotrophy, soxB, terminal_oxidases
  - Rationale: marine Mn(II)-oxidizing heterotroph; aerobic_chemotrophic ✓
  - Source: Anderson et al. 2009 PLoS ONE

- **gid 1074 — Bacillus sp. SG-1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 8.4; T 33.2°C; salinity 5.25%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65
  - Positive markers: terminal_oxidases
  - Rationale: Mn(II)-oxidizing spore-forming Bacillus; aerobic_chemotrophic ✓
  - Source: Dick et al. 2008 AEM

- **gid 1133 — Leptothrix discophora CCM 2812** — **FAIL**
  - CultureForge: primary `phototrophic`; alt `aerobic_chemotrophic, lithotrophic_aerobic, acetogenic`; recipe `composed`; O2 tolerant; pH 7.3; T 29.7°C; salinity 0.59%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Purple phototrophy=0.768, Sulfur oxidation (bacterial SOX + archae=0.729, Acetogenesis (Wood-Ljungdahl)=0.605
  - Positive markers: autotrophy, nifH, pufLM, soxB, terminal_oxidases
  - Rationale: sheathed Fe(II)/Mn(II)-oxidizing β-proteobacterium; classified primary=phototrophic — WRONG; pufLM false-positive (Leptothrix has no anoxygenic photosynthesis); should be aerobic_chemotrophic (microaerophilic Fe/Mn oxidation)
  - Source: Spring 2006 Prokaryotes

### magnetotaxis  (5 genomes — PASS 3 / PARTIAL 2 / FAIL 0 / INSUFFICIENT 0)

- **gid 16 — Paramagnetospirillum magneticum AMB-1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.5; T 25.3°C; salinity 0.3%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Nitrogen fixation=0.614, Denitrification (NO3- to N2)=0.522
  - Positive markers: autotrophy, dsrAB, nifH, nosZ, terminal_oxidases
  - Rationale: microaerophilic magnetite-producing heterotroph; aerobic_chemotrophic acceptable but ideally flagged microaerophile; T 25.3°C, pH 6.5 ✓
  - Source: ATCC 700264; Matsunaga et al. 2005 DNA Res

- **gid 1020 — Paramagnetospirillum magneticum AMB-1** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.5; T 25.3°C; salinity 0.3%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Nitrogen fixation=0.614, Denitrification (NO3- to N2)=0.522
  - Positive markers: autotrophy, dsrAB, nifH, nosZ, terminal_oxidases
  - Rationale: duplicate of gid 16; microaerophile; aerobic_chemotrophic acceptable
  - Source: ATCC 700264

- **gid 1098 — Magnetospirillum gryphiswaldense MSR-1** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.6; T 25.1°C; salinity 1.31%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.679, Nitrogen fixation=0.614, Denitrification (NO3- to N2)=0.522
  - Positive markers: autotrophy, dsrAB, nifH, nosZ, soxB, terminal_oxidases
  - Rationale: microaerophilic magnetite-producer; classified lithotrophic_aerobic — primary mode should be aerobic_chemotrophic (microaerophile) like gid 16/1020 (sister taxa); aerobic respiration cap is OK but lithotrophic label is misleading
  - Source: DSMZ 6361; Wang et al. 2014 BMC Genomics

- **gid 1099 — Candidatus Magnetoglobus multicellularis** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 7.3; T 27.7°C; salinity 1.33%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.588
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, dsrAB, qmoA
  - Rationale: anaerobic multicellular magnetotactic bacterium; anaerobic_respiratory ✓
  - Source: Abreu et al. 2013 ISME J

- **gid 1108 — Magnetospira sp. QH-2** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.6; T 28.8°C; salinity 3.82%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.679, Denitrification (NO3- to N2)=0.522
  - Positive markers: aprAB, autotrophy, dsrAB, nosZ, soxB, terminal_oxidases
  - Rationale: microaerophilic magnetite-producer; classified lithotrophic_aerobic — should be aerobic_chemotrophic microaerophile
  - Source: Ji et al. 2014 ISME J

### heavy_metal_respiration  (5 genomes — PASS 2 / PARTIAL 1 / FAIL 2 / INSUFFICIENT 0)

- **gid 25 — Dehalococcoides mccartyi** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Organohalide respiration=0.65, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, nifH, rdhA
  - Rationale: obligate organohalide respirer; anaerobic_respiratory ✓
  - Source: DSMZ 11733; Seshadri et al. 2005 Science

- **gid 1066 — Bacillus selenitireducens MLS10** — **FAIL**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative`; recipe `composed`; O2 tolerant; pH 9.5; T 36.6°C; salinity 9.03%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65
  - Positive markers: terminal_oxidases
  - Rationale: alkaliphilic Se(IV)/As(V)-respiring anaerobe; classified aerobic_chemotrophic — WRONG; primary is anaerobic respiration of selenite/arsenate; aerobic respiration cap (0.85) is misleading (B. selenitireducens is anaerobic, not aerobic)
  - Source: DSMZ 15326; Switzer Blum et al. 1998 Arch Microbiol

- **gid 1078 — Cupriavidus metallidurans CH34** — **PARTIAL**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic, anaerobic_respiratory`; recipe `composed`; O2 tolerant; pH 6.2; T 30.6°C; salinity 0.0%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Denitrification (NO3- to N2)=0.817, Sulfur oxidation (bacterial SOX + archae=0.778
  - Positive markers: autotrophy, nosZ, soxB, terminal_oxidases
  - Rationale: heavy-metal-resistant β-proteobacterium with facultative H2 chemolithoautotrophy; lithotrophic_aerobic is one mode; primary lifestyle in lab is heterotrophic on rich media
  - Source: DSMZ 2839; Janssen et al. 2010 PLoS ONE

- **gid 1085 — Sulfurospirillum barnesii SES-3** — **FAIL**
  - CultureForge: primary `fermentative`; alt `anaerobic_respiratory, aerobic_chemotrophic`; recipe `composed`; O2 n/a; pH 6.4; T 25.7°C; salinity 1.17%
  - Detected caps (≥0.50): Fermentation=0.706, Dissimilatory nitrate reduction to ammon=0.645, Nitrogen fixation=0.614, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: nifH, nrfA, terminal_oxidases
  - Rationale: anaerobic As(V)/Se(VI)-respiring ε-proteobacterium; classified primary=fermentative — WRONG; primary lifestyle is anaerobic respiration on metalloid oxyanions or thiosulfate; nrfA marker ✓ (DNRA capable) but main mode is metalloid respiration
  - Source: DSMZ 10660; Stolz et al. 1999 IJSEM

- **gid 1107 — Pseudorhizobium banfieldiae NT-26 (Rhizobium-like)** — **PASS**
  - CultureForge: primary `lithotrophic_aerobic`; alt `aerobic_chemotrophic`; recipe `composed`; O2 tolerant; pH 7.7; T 30.6°C; salinity 2.65%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Sulfur oxidation (bacterial SOX + archae=0.63
  - Positive markers: autotrophy, soxB, terminal_oxidases
  - Rationale: chemolithoautotrophic arsenite oxidizer; lithotrophic_aerobic ✓
  - Source: Andres et al. 2013 BMC Genomics

### halophile_alkaliphile  (4 genomes — PASS 3 / PARTIAL 1 / FAIL 0 / INSUFFICIENT 0)

- **gid 20 — Halobacterium salinarum** — **PASS**
  - CultureForge: primary `halophilic_with_rhodopsin`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Bacteriorhodopsin=0.6, Aerobic respiration=0.6
  - Positive markers: autotrophy, rhodopsin, terminal_oxidases
  - Rationale: extreme halophilic archaeon with bacteriorhodopsin; mode correctly identified
  - Source: DSMZ 3754; Ng et al. 2000 PNAS

- **gid 1053 — Natranaerobius thermophilus JW/NM-WN-LF** — **PASS**
  - CultureForge: primary `fermentative`; alt `none`; recipe `composed`; O2 n/a; pH 10.0; T 38.3°C; salinity 10.83%
  - Detected caps (≥0.50): Fermentation=0.727
  - Positive markers: acsB_cdhC, cooS_cdhA
  - Rationale: alkali-thermo-halophilic anaerobic fermenter; fermentative ✓; pH 10.0 ✓; T 38.3°C low (true 50-55°C)
  - Source: DSMZ 18059; Mesbah et al. 2009 J Bacteriol

- **gid 1060 — Halorubrum lacusprofundi DSM 5036** — **PARTIAL**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 tolerant; pH 8.1; T 39.3°C; salinity 18.01%
  - Detected caps (≥0.50): Denitrification (NO3- to N2)=0.817
  - Positive markers: autotrophy, nosZ
  - Rationale: extreme halophilic archaeon (cold-adapted); classified anaerobic_respiratory — partly wrong (Halorubrum is aerobic heterotroph that can ferment); pH 8.1 ✓
  - Source: DSMZ 5036; Anderson et al. 2009 Genome Res

- **gid 1080 — Halomonas elongata DSM 2581** — **PASS**
  - CultureForge: primary `aerobic_chemotrophic`; alt `fermentative, acetogenic`; recipe `composed`; O2 tolerant; pH 7.8; T 33.3°C; salinity 7.99%
  - Detected caps (≥0.50): Aerobic respiration=0.85, Fermentation=0.65, Acetogenesis (Wood-Ljungdahl)=0.605
  - Positive markers: cyc2, terminal_oxidases
  - Rationale: moderately halophilic γ-proteobacterium; aerobic_chemotrophic ✓
  - Source: DSMZ 2581; Schwibbert et al. 2011 Environ Microbiol

### acetogenesis  (4 genomes — PASS 4 / PARTIAL 0 / FAIL 0 / INSUFFICIENT 0)

- **gid 22 — Acetobacterium woodii** — **PASS**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a
  - Detected caps (≥0.50): Acetogenesis (Wood-Ljungdahl)=0.75, Fermentation=0.727, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH
  - Rationale: model acetogen using Wood-Ljungdahl; acetogenic ✓
  - Source: DSMZ 1030; Poehlein et al. 2012 PLoS ONE

- **gid 1067 — Clostridium ljungdahlii DSM 13528** — **PASS**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a; pH 5.9; T 38.2°C; salinity 1.99%
  - Detected caps (≥0.50): Acetogenesis (Wood-Ljungdahl)=0.95, Fermentation=0.9, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH
  - Rationale: acetogen capable of CO/H2/CO2 + sugar fermentation; acetogenic ✓
  - Source: DSMZ 13528; Köpke et al. 2010 PNAS

- **gid 1097 — Sporomusa ovata DSM 2662** — **PASS**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.4; T 33.3°C; salinity 0.0%
  - Detected caps (≥0.50): Fermentation=0.775, Acetogenesis (Wood-Ljungdahl)=0.75, Nitrogen fixation=0.614
  - Positive markers: acsB_cdhC, cooS_cdhA, nifH
  - Rationale: acetogen; acetogenic ✓
  - Source: DSMZ 2662; Poehlein et al. 2013 Genome Announc

- **gid 1104 — Thermoanaerobacter kivui LKT-1** — **PASS**
  - CultureForge: primary `acetogenic`; alt `fermentative`; recipe `composed`; O2 n/a; pH 6.9; T 66.0°C; salinity 0.0%
  - Detected caps (≥0.50): Fermentation=0.775, Acetogenesis (Wood-Ljungdahl)=0.75
  - Positive markers: acsB_cdhC, cooS_cdhA
  - Rationale: thermophilic acetogen; acetogenic ✓; T 66°C ✓
  - Source: DSMZ 2030; Hess et al. 2014 J Biotechnol

### phosphate_metabolism  (2 genomes — PASS 1 / PARTIAL 1 / FAIL 0 / INSUFFICIENT 0)

- **gid 1003 — Candidatus Phosphitivorax anaerolimi** — **PARTIAL**
  - CultureForge: primary `fermentative`; alt `aerobic_chemotrophic`; recipe `composed`; O2 n/a; pH 7.7; T 43.0°C; salinity 2.39%
  - Detected caps (≥0.50): Fermentation=0.657, Aerobic respiration (ETC pathway)=0.516
  - Positive markers: autotrophy
  - Rationale: phosphite-oxidizing anaerobe (Deltaproteobacterium); primary fermentative — should be anaerobic lithotrophic with phosphite as donor; no PtxD detector wired
  - Source: Figueroa et al. 2018 mBio

- **gid 1095 — Desulfotignum phosphitoxidans DSM 13687** — **PASS**
  - CultureForge: primary `anaerobic_respiratory`; alt `fermentative`; recipe `composed`; O2 n/a; pH 7.5; T 33.9°C; salinity 2.88%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.818, Fermentation=0.65
  - Positive markers: acsB_cdhC, aprAB, autotrophy, cooS_cdhA, dsrAB, qmoA, terminal_oxidases
  - Rationale: phosphite-oxidizing sulfate reducer; anaerobic_respiratory ✓; dsr+apr+qmo ✓ — note that phosphite oxidation specifically not flagged
  - Source: DSMZ 13687; Poehlein et al. 2013 J Bacteriol

### cable_bacteria  (2 genomes — PASS 0 / PARTIAL 0 / FAIL 2 / INSUFFICIENT 0)

- **gid 1004 — Candidatus Electrothrix communis** — **FAIL**
  - CultureForge: primary `anaerobic_respiratory`; alt `none`; recipe `composed`; O2 n/a; pH 6.7; T 39.5°C; salinity 0.98%
  - Detected caps (≥0.50): Dissimilatory sulfate reduction=0.647
  - Positive markers: acsB_cdhC, aprAB, cooS_cdhA, dsrAB, qmoA, terminal_oxidases
  - Rationale: cable bacterium; primary anaerobic_respiratory misses the defining cable phenotype (long-distance electron transport via filaments); dsrAB hit detected; no cable cultivation mode in detector library
  - Source: Sereika et al. 2023 ISME J

- **gid 1008 — Candidatus Electronema palustre** — **FAIL**
  - CultureForge: primary `(none)`; alt `—`; recipe `escalated`; O2 n/a; pH 7.6; T 29.0°C; salinity 0.0%
  - Detected caps (≥0.50): Nitrogen fixation=0.532
  - Positive markers: dsrAB, nifH, qmoA
  - Rationale: cable bacterium; ESCALATED with only Nitrogen fixation (0.532) detected; no cable mode; dsrAB+nifH+qmoA markers present but unused
  - Source: Kjeldsen et al. 2019 PNAS

### unknown_MAG  (1 genomes — PASS 0 / PARTIAL 0 / FAIL 0 / INSUFFICIENT 1)

- **gid 1000 — PacBio bin.020 MAG** — **INSUFFICIENT_DATA**
  - CultureForge: primary `aerobic_chemotrophic`; alt `none`; recipe `composed`; O2 tolerant; pH 6.8; T 23.2°C; salinity 2.42%
  - Detected caps (≥0.50): Aerobic respiration=0.65
  - Positive markers: autotrophy, terminal_oxidases
  - Rationale: uncharacterized environmental MAG; no published taxonomy or cultivation data to validate against
  - Source: ST3_PacBio_bin20 internal


## 4. Systematic issues identified

Cross-reference of recurring patterns to specific gids. Each issue is named, scoped, and exemplified.

### ANME archaea classified as forward methanogenic

- **gid 1005 Candidatus Methanocomedens sp. (ANME-2a)** — primary `methanogenic`; recipe `composed` — ANME-2a SHOULD be anme_reverse_methanogenic like gid 28; instead classified as forward methanogenic — systematic miss; mcrA + acsB + cooS markers present (consistent with ANME)
- **gid 1006 Candidatus Methanophaga sp. (ANME-1)** — primary `methanogenic`; recipe `composed` — ANME-1 SHOULD be anme_reverse_methanogenic; classified as forward methanogenic — systematic miss
- **gid 1007 Candidatus Methanovorans sp. (ANME-3)** — primary `methanogenic`; recipe `composed` — ANME-3 SHOULD be anme_reverse_methanogenic; classified as forward methanogenic — systematic miss

### Ammonia-oxidizing archaea (AOA) always escalate

- **gid 1049 Nitrosopumilus maritimus SCM1** — primary `(none)`; recipe `escalated` — model ammonia-oxidizing archaeon; ESCALATED — only autotrophy + terminal_oxidases hit; archaeal amoA not in marker set or sequence too divergent from bacterial AMO
- **gid 1102 Nitrososphaera viennensis EN76** — primary `(none)`; recipe `escalated` — soil AOA; ESCALATED — same systematic issue as gid 1049, archaeal amoA not detected
- **gid 1106 Candidatus Nitrosocosmicus oleophilus MY3** — primary `(none)`; recipe `escalated` — soil AOA; ESCALATED — archaeal amoA not detected; same systematic issue

### Hyperthermophilic / thermoacidophilic anaerobic archaea escalate

- **gid 26 Picrophilus torridus DSM 9790** — primary `(none)`; recipe `escalated` — thermoacidophilic heterotroph (pH 0-3.5, T 60°C); ESCALATED — no aerobic_chemotrophic-acidophile profile; predicted pH 2.6 ✓ at least; markers sor+tetH+tqoDoxD detected but did not compose recipe
- **gid 1019 Thermococcus kodakarensis KOD1** — primary `(none)`; recipe `escalated` — hyperthermophilic S0-respiring fermenter; ESCALATED — no primary mode detected; like Pyrococcus furiosus should map to anaerobic_respiratory
- **gid 1046 Ignicoccus hospitalis KIN4/I** — primary `(none)`; recipe `escalated` — anaerobic hyperthermophilic H2/S0 autotroph (Crenarchaeota); ESCALATED with only autotrophy marker; no H2/S0 anaerobic chemolithoautotrophy mode in capability library
- **gid 1047 Caldivirga maquilingensis IC-167** — primary `(none)`; recipe `escalated` — thermoacidophilic facultatively anaerobic crenarchaeote (S0/thiosulfate reduction); ESCALATED with dsrAB+aprAB+autotrophy+tetH markers but no mode resolved
- **gid 1129 Stygiolobus azoricus DSM 6296** — primary `(none)`; recipe `escalated` — thermoacidophilic anaerobic S0 reducer (Sulfolobales); ESCALATED — no anaerobic crenarchaeote sulfur reduction mode; pH 4.0 ✓
- **gid 1070 Ferroplasma acidarmanus Fer1** — primary `(none)`; recipe `escalated` — acidophilic Fe(II)-oxidizing archaeon (Thermoplasmatales); ESCALATED — no acidophilic archaeal Fe oxidation mode in detector library; pH 2.7 ✓

### Anammox bacteria — cap detected but recipe-composer has no anammox mode

- **gid 30 Candidatus Scalindua japonica** — primary `(none)`; recipe `escalated` — anammox bacterium; Anammox capability detected at 0.95 ✓ but recipe escalates because composer has no anammox cultivation-mode → mapping; should compose with NH4+/NO2- as electron donor/acceptor
- **gid 1105 Candidatus Scalindua brodae** — primary `(none)`; recipe `escalated` — anammox bacterium; Anammox cap detected at 0.95 with hzsA+hdh+hao ✓ but recipe ESCALATED — same composer→mode mapping gap as gid 30
- **gid 1001 Candidatus Brocadia sinica JPN1 (smoke test)** — primary `lithotrophic_aerobic`; recipe `composed` — anammox; primary mode lithotrophic_aerobic is misleading (anammox is anaerobic NH4+/NO2-); recipe composed but using aerobic profile
- **gid 1002 Candidatus Brocadia fulgida** — primary `lithotrophic_aerobic`; recipe `composed` — anammox; primary mode lithotrophic_aerobic — wrong oxygen handling (should be anaerobic); recipe composed
- **gid 1090 Candidatus Jettenia caeni** — primary `lithotrophic_aerobic`; recipe `composed` — anammox bacterium; classified lithotrophic_aerobic — anammox is anaerobic NH4+/NO2- (should be its own anammox mode); recipe composed but aerobic profile wrong

### Cable bacteria — long-distance electron transport not modeled

- **gid 1004 Candidatus Electrothrix communis** — primary `anaerobic_respiratory`; recipe `composed` — cable bacterium; primary anaerobic_respiratory misses the defining cable phenotype (long-distance electron transport via filaments); dsrAB hit detected; no cable cultivation mode in detector library
- **gid 1008 Candidatus Electronema palustre** — primary `(none)`; recipe `escalated` — cable bacterium; ESCALATED with only Nitrogen fixation (0.532) detected; no cable mode; dsrAB+nifH+qmoA markers present but unused

### Wood-Ljungdahl false-positive drives primary mode=acetogenic in non-acetogens

- **gid 1031 Geobacter metallireducens GS-15** — primary `acetogenic`; recipe `composed` — Fe(III)-reducing anaerobe; classified primary=acetogenic — WRONG; WL false-positive (0.662) from acsB+cooS hits (Geobacter has CODH/acetyl-CoA-synthase but not for autotrophic WL); should be anaerobic_respiratory like its sister G. sulfurreducens
- **gid 1032 Rhodospirillum rubrum ATCC 11170** — primary `acetogenic`; recipe `composed` — purple non-sulfur phototroph; classified primary=acetogenic — WRONG; purple phototrophy detected at 0.768 with pufLM ✓ but WL (0.763) ranks slightly higher pushing primary to acetogenic; should be phototrophic
- **gid 1056 Azotobacter vinelandii DJ** — primary `acetogenic`; recipe `composed` — obligate aerobic free-living N-fixer; classified primary=acetogenic — WRONG; high O2-tolerant respiration is its hallmark; WL false-positive driving primary mode (acsB+cooS hits from CODH not WL acetogenesis)
- **gid 1079 Acetoanaerobium sticklandii DSM 519 (Clostridium sticklandii)** — primary `acetogenic`; recipe `composed` — Stickland amino-acid fermenter (pairwise oxidation/reduction of amino acids); classified primary=acetogenic — WRONG; despite Wood-Ljungdahl pathway in some pyranose conditions, primary growth is Stickland fermentation; acsB+cooS markers detected drive WL false-positive
- **gid 1126 Pelotomaculum schinkii HH** — primary `acetogenic`; recipe `composed` — obligate syntrophic propionate-oxidizing Firmicute; classified primary=acetogenic — WRONG; syntrophic should be primary (it grows on propionate ONLY in co-culture with H2 scavenger)
- **gid 1130 Syntrophorhabdus aromaticivorans** — primary `acetogenic`; recipe `composed` — obligate syntrophic aromatics degrader; classified acetogenic — WRONG; same systematic issue as 1126 (syntrophy mode lost to WL false-positive)

### Purple-phototrophy false-positive from pufLM in non-phototrophs

- **gid 1061 Methylorubrum extorquens AM1 (Methylobacterium)** — primary `phototrophic`; recipe `composed` — aerobic methylotroph (methanol/methylamine, NOT methane); classified primary=phototrophic — WRONG; pufLM false-positive (some Methylorubrum strains carry vestigial pufLM but they are not phototrophs); should be aerobic_chemotrophic with C1 substrates
- **gid 1133 Leptothrix discophora CCM 2812** — primary `phototrophic`; recipe `composed` — sheathed Fe(II)/Mn(II)-oxidizing β-proteobacterium; classified primary=phototrophic — WRONG; pufLM false-positive (Leptothrix has no anoxygenic photosynthesis); should be aerobic_chemotrophic (microaerophilic Fe/Mn oxidation)

### Syntrophic primary mode lost to fermentation/acetogenic mis-ranking

- **gid 1034 Syntrophus aciditrophicus SB** — primary `fermentative`; recipe `composed` — obligate syntrophic benzoate degrader; classified fermentative — syntrophic should be primary
- **gid 1038 Syntrophomonas wolfei subsp. wolfei Goettingen G311** — primary `fermentative`; recipe `composed` — duplicate of gid 21 (subsp. variant); classified fermentative — should be syntrophic like gid 21
- **gid 1041 Syntrophobacter fumaroxidans MPOB** — primary `anaerobic_respiratory`; recipe `composed` — syntrophic propionate oxidizer that can also reduce sulfate; classified anaerobic_respiratory ✓ in part; syntrophic lifestyle missed as primary
- **gid 1126 Pelotomaculum schinkii HH** — primary `acetogenic`; recipe `composed` — obligate syntrophic propionate-oxidizing Firmicute; classified primary=acetogenic — WRONG; syntrophic should be primary (it grows on propionate ONLY in co-culture with H2 scavenger)
- **gid 1130 Syntrophorhabdus aromaticivorans** — primary `acetogenic`; recipe `composed` — obligate syntrophic aromatics degrader; classified acetogenic — WRONG; same systematic issue as 1126 (syntrophy mode lost to WL false-positive)

### Microaerophile flag missing (recipe uses standard aerobic 21% O2)

- **gid 15 Campylobacter jejuni** — primary `aerobic_chemotrophic`; recipe `composed` — microaerophilic host-associated; aerobic_chemotrophic close but should flag microaerophile (5% O2); no physical-format hint; T 24.5°C is low (true ~42°C avian host)
- **gid 16 Paramagnetospirillum magneticum AMB-1** — primary `aerobic_chemotrophic`; recipe `composed` — microaerophilic magnetite-producing heterotroph; aerobic_chemotrophic acceptable but ideally flagged microaerophile; T 25.3°C, pH 6.5 ✓
- **gid 1020 Paramagnetospirillum magneticum AMB-1** — primary `aerobic_chemotrophic`; recipe `composed` — duplicate of gid 16; microaerophile; aerobic_chemotrophic acceptable
- **gid 1040 Magnetococcus marinus MC-1** — primary `lithotrophic_aerobic`; recipe `composed` — microaerophilic chemolithoautotrophic magnetite producer; lithotrophic_aerobic OK direction; should flag microaerophile (recipe uses default aerobic)
- **gid 1068 Gallionella capsiferriformans ES-2** — primary `aerobic_chemotrophic`; recipe `composed` — microaerophilic Fe(II) oxidizer; classified aerobic_chemotrophic — should be lithotrophic_aerobic (Fe-autotroph); microaerophile flag missing
- **gid 1072 Mariprofundus ferrooxydans PV-1** — primary `aerobic_chemotrophic`; recipe `composed` — marine microaerophilic Fe(II) oxidizer (Zetaproteobacterium); classified aerobic_chemotrophic — should be lithotrophic_aerobic; microaerophile flag missing
- **gid 1083 Beggiatoa alba B18LD** — primary `lithotrophic_aerobic`; recipe `composed` — filamentous chemolithoautotrophic S oxidizer; lithotrophic_aerobic ✓; should flag microaerophile (Beggiatoa lives at O2/sulfide interfaces) — recipe uses standard aerobic
- **gid 1098 Magnetospirillum gryphiswaldense MSR-1** — primary `lithotrophic_aerobic`; recipe `composed` — microaerophilic magnetite-producer; classified lithotrophic_aerobic — primary mode should be aerobic_chemotrophic (microaerophile) like gid 16/1020 (sister taxa); aerobic respiration cap is OK but lithotrophic label is misleading
- **gid 1108 Magnetospira sp. QH-2** — primary `lithotrophic_aerobic`; recipe `composed` — microaerophilic magnetite-producer; classified lithotrophic_aerobic — should be aerobic_chemotrophic microaerophile
- **gid 1014 Aquifex aeolicus VF5** — primary `lithotrophic_aerobic`; recipe `composed` — microaerophilic H2/S oxidizer; lithotrophic_aerobic ✓; T 90.3°C ✓; pH 6.4 ✓

### Heliobacterial photosynthesis not detected (BChl g)

- **gid 1051 Heliomicrobium modesticaldum Ice1 (Heliobacterium)** — primary `anaerobic_respiratory`; recipe `composed` — anoxygenic phototrophic Firmicute (heliobacteria); classified anaerobic_respiratory — WRONG; no purple/green phototrophy detected because heliobacteria use unique BChl g system (PufLM-like not in current marker set as heliobacterial reaction center)

### Anaerobic metalloid-oxyanion respiration (As/Se) not modeled

- **gid 1066 Bacillus selenitireducens MLS10** — primary `aerobic_chemotrophic`; recipe `composed` — alkaliphilic Se(IV)/As(V)-respiring anaerobe; classified aerobic_chemotrophic — WRONG; primary is anaerobic respiration of selenite/arsenate; aerobic respiration cap (0.85) is misleading (B. selenitireducens is anaerobic, not aerobic)
- **gid 1085 Sulfurospirillum barnesii SES-3** — primary `fermentative`; recipe `composed` — anaerobic As(V)/Se(VI)-respiring ε-proteobacterium; classified primary=fermentative — WRONG; primary lifestyle is anaerobic respiration on metalloid oxyanions or thiosulfate; nrfA marker ✓ (DNRA capable) but main mode is metalloid respiration

### Phosphite oxidation as energy mode not modeled

- **gid 1003 Candidatus Phosphitivorax anaerolimi** — primary `fermentative`; recipe `composed` — phosphite-oxidizing anaerobe (Deltaproteobacterium); primary fermentative — should be anaerobic lithotrophic with phosphite as donor; no PtxD detector wired

### Stickland fermentation mistaken for Wood-Ljungdahl acetogenesis

- **gid 1079 Acetoanaerobium sticklandii DSM 519 (Clostridium sticklandii)** — primary `acetogenic`; recipe `composed` — Stickland amino-acid fermenter (pairwise oxidation/reduction of amino acids); classified primary=acetogenic — WRONG; despite Wood-Ljungdahl pathway in some pyranose conditions, primary growth is Stickland fermentation; acsB+cooS markers detected drive WL false-positive

### Comammox correctly captured (positive control)

- **gid 1114 Candidatus Nitrospira inopinata** — primary `lithotrophic_aerobic`; recipe `composed` — complete ammonia oxidizer (comammox); lithotrophic_aerobic ✓ with both AOB AND NOB caps detected ✓ (amoA 0.916, nxrA 0.614)

### Nitrospina nxrA divergent from reference — zero markers detected

- **gid 1094 Nitrospina gracilis 3/211** — primary `(none)`; recipe `escalated` — marine NOB; ESCALATED — zero positive markers, no caps detected; nxrA likely too divergent from reference for BLAST hit (Nitrospina nxrA differs from Nitrospira/Nitrobacter)

### Vent ε-proteobacterial H2/S anaerobic respiration not modeled

- **gid 1127 Caminibacter mediatlanticus TB-2** — primary `(none)`; recipe `escalated` — vent ε-proteobacterial H2-oxidizing N/S reducer; ESCALATED — only autotrophy marker; no H2-oxidizing-anaerobic mode in capability library

### Acidophilic archaeal Fe(II) oxidation not modeled

- **gid 1070 Ferroplasma acidarmanus Fer1** — primary `(none)`; recipe `escalated` — acidophilic Fe(II)-oxidizing archaeon (Thermoplasmatales); ESCALATED — no acidophilic archaeal Fe oxidation mode in detector library; pH 2.7 ✓

### Neomoorella thermoacetica (model acetogen) classified fermentative — primary-mode ranking issue

- **gid 1112 Neomoorella thermoacetica DSM 521 (Moorella thermoacetica)** — primary `fermentative`; recipe `composed` — model thermophilic acetogen (heterotrophic acetogenesis); classified fermentative — WRONG; WL detected but primary mode should be acetogenic like Clostridium ljungdahlii/Sporomusa ovata

### Phase 5.0 fermentation-primary-mode bug (FIXED 2026-05-13, commit d4e9587)
- Already fixed; included for context.
- Symptom that drove the fix: obligate aerobes (e.g. Pseudomonas-like heterotrophs) being assigned primary mode `fermentative` because gapseq's full glycolysis pathway scored 1.00 and outranked aerobic respiration. The 2026-05-13 fix (commit d4e9587) re-ranks fermentation as a secondary mode when a strong acceptor metabolism is present. **An analogous fix is needed for Wood-Ljungdahl acetogenesis** (see item above).

## 5. Recommended fix priorities

Diagnostic only — these are the gaps the audit surfaced, ranked by biological-correctness impact (number of organisms touched × severity of the misclassification). **No code changes are part of this audit.**

### P1 — Re-rank primary mode when Wood-Ljungdahl is detected alongside a stronger respiratory or phototrophic acceptor signal.

Pattern is identical to the fermentation primary-mode bug fixed 2026-05-13 (d4e9587) but in the WL/acetogenic lane. Currently WL scores 0.66–0.76 from acsB+cooS hits in organisms that have CODH/acetyl-CoA-synthase for other reasons (anaplerotic, CO oxidation, central metabolism), and that score is ranked first. **Impact:** 6 FAILs (gids 1031, 1032, 1056, 1079, 1126, 1130) — Geobacter metallireducens, Rhodospirillum rubrum, Azotobacter vinelandii, Acetoanaerobium sticklandii, Pelotomaculum schinkii, Syntrophorhabdus aromaticivorans. **Plus** 1 FAIL (1112 Neomoorella thermoacetica) where the *opposite* ranking error happens — a real acetogen is mode-ranked as fermentative. Both are mode-ranking issues. **Biological rationale:** WL is a high-bar pathway; a *primary* acetogen requires (a) anaerobic lifestyle and (b) absence of strong respiratory acceptor signal. Use anaerobic-only / no-O2-respiration gating before WL can take the primary slot.

### P2 — Add ANME `anme_reverse_methanogenic` rule for ANME-1, ANME-2a, ANME-3 lineages (analogous to gid 28 Methanoperedens which IS correctly captured).

**Impact:** 3 FAILs (gids 1005, 1006, 1007). **Biological rationale:** ANME archaea encode mcrA and the C1 pathway like methanogens but run the pathway in *reverse* coupled to sulfate (ANME-1/2), nitrate (ANME-2d = Methanoperedens), or syntrophic partners. They cannot be cultivated as methanogens — wrong electron donor (CH4 vs H2/CO2), wrong electron acceptor (SO4 vs CO2), wrong gas phase. The Methanoperedens detector already exists; replicate its trigger logic (mcrA + sulfate-reduction or nitrate-reduction co-occurrence + ANME phylogenetic signal) for the other three ANME clades.

### P3 — Add anammox cultivation-mode mapping in the recipe composer.

**Impact:** 2 FAILs (gids 30, 1105 — both escalate) + 3 PARTIALs (1001, 1002, 1090 — mode falls back to `lithotrophic_aerobic` with wrong oxygen profile). **Biological rationale:** The capability detector already scores Anammox at 0.95 with hzsA + hdh + hao markers ✓; the gap is at the composer end. Anammox needs: anaerobic atmosphere, NH4+ as electron donor, NO2- as electron acceptor, NaHCO3/CO2 as C source, no organic carbon. Mapping is mechanical once the cultivation mode is registered.

### P4 — Add an `archaeal_AOA_amoA` marker entry covering Thaumarchaeota / Nitrososphaerales lineages.

**Impact:** 3 FAILs (gids 1049 Nitrosopumilus, 1102 Nitrososphaera, 1106 Nitrosocosmicus). **Biological rationale:** Bacterial AMO and archaeal AMO share <30% sequence identity. The current marker BLAST database is loaded only with bacterial AMO references, so AOA escalate to Tier 2 even though every AOA in the test set has a textbook physiology. UniProt accessions Q5JIJ3 (Nitrosopumilus AmoA-1), Q57F89 (Nitrososphaera AmoA), and equivalents make a complete reference set. Comammox Nitrospira inopinata (gid 1114) succeeds because *bacterial-lineage* amoA detection works, so the cultivation-mode profile is fine — only the marker references need extending.

### P5 — Add a microaerophile primary-mode label (or 1-3% O2 atmosphere modifier) for organisms with cydAB without low-affinity ctaABCDE.

**Impact:** ~10 PARTIALs across categories (gids 15, 16, 1014, 1020, 1040, 1068, 1072, 1083, 1098, 1108) — Campylobacter jejuni, Aquifex aeolicus, multiple Magnetospirillum / Magnetococcus / Magnetospira, Mariprofundus ferrooxydans, Gallionella capsiferriformans, Beggiatoa alba. **Biological rationale:** All of these are well-characterized microaerophiles; recipe-as-composed uses 21% O2 which is lethal or strongly inhibitory at standard partial pressures. Detection is genomically tractable (high-affinity cytochrome bd oxidase as sole terminal oxidase) and the recipe-output already supports a `Pressure / Gas phase` field — only need a modifier that lowers O2 to ~3-5% when the microaerophile flag is set.

### Secondary recommendations (lower-impact gaps)

**S1.** Cable bacteria mode (`cable_long_distance_electron_transport`) — 2 FAILs (gids 1004, 1008). Even a minimal placeholder rule (dsrAB + filament-forming + no canonical sulfide-oxidation pathway closure) would be better than the current escalation, since cable bacteria have a specific cultivation regime (sediment co-incubation with sulfide/O2 gradient).

**S2.** Heliobacterial photosynthesis marker — 1 FAIL (gid 1051 Heliomicrobium modesticaldum). The current pufLM detector keys to purple-bacterial reaction centers; heliobacteria use a homodimeric Type I reaction center with BChl g. Add a `pshA` marker (heliobacterial reaction center) and a `phototrophic_heliobacterial` mode mapping.

**S3.** Vent ε-proteobacterial H2/S anaerobic respiration mode — 1 FAIL (gid 1127 Caminibacter mediatlanticus). Common physiology among Nautiliales / Caminibacteraceae but no detector entry.

**S4.** Acidophilic archaeal Fe(II) oxidation mode — 1 FAIL (gid 1070 Ferroplasma acidarmanus). The bacterial cyc2-based detector does not fire for archaeal sequences; needs an archaeal-specific reference set.

**S5.** Anaerobic metalloid-oxyanion respiration (As(V), Se(VI)) — 2 FAILs (gids 1066 Bacillus selenitireducens, 1085 Sulfurospirillum barnesii). Markers like `arrA`, `serA` (selenate reductase) would resolve these.

**S6.** Phosphite oxidation as energy mode (`ptxD`) — 1 PARTIAL (gid 1003 Phosphitivorax anaerolimi). Currently fall-back to fermentative; needs ptxD detector.

**S7.** Aerobic anoxygenic phototroph (AAP) primary-mode rebalancing — gids 1073 Roseobacter litoralis and 1101 Gemmatimonas phototrophica are flagged `phototrophic` primary, but AAPs use BChl as a supplemental energy harvest and grow primarily heterotrophically (often >70% of energy from organic substrate oxidation). Primary-mode should be aerobic_chemotrophic with phototrophy as alt.

**S8.** Methylotroph (non-methanotroph) handling — gid 1061 Methylorubrum extorquens AM1 has a vestigial pufLM operon (some Methylobacteriaceae do) but is a methanol/methylamine methylotroph, not a phototroph. The pufLM marker alone should not push primary mode to `phototrophic`; require pufLM AND BChl synthesis gene context (bchE / bchY).

**S9.** Stickland fermentation distinct from Wood-Ljungdahl acetogenesis — gid 1079 Acetoanaerobium sticklandii. Coupled with P1, but worth a specific note: amino-acid Stickland reactions produce acetate via a different route than WL CO2 fixation; presence of grdAB / proline reductase markers should suppress WL primary mode.

**S10.** Nitrospina NXR reference — gid 1094 Nitrospina gracilis returns zero positive markers. Nitrospina nxrA is sequence-distinct from Nitrobacter and Nitrospira nxrA; widening the nxrA reference set would resolve this without a new mode.

**S11.** Spurious sulfur-oxidation false positives — `soxB` hits at moderate confidence appear in Nitrobacter hamburgensis (1037), Methylorubrum (1061), Leptothrix (1133), Magnetococcus (1040). For organisms with no published thiosulfate oxidation, this is most likely paralog noise; consider raising soxB bitscore cutoff or requiring soxAX+soxYZ co-detection.

**S12.** Temperature optimum systematically under-predicted for mesophiles with hot-spring or warm-host habitat — Lactiplantibacillus plantarum predicted 18.8°C (true 30-37°C, gid 10 and 1081); Chlorobaculum tepidum predicted 34.4°C (true 47-48°C, gid 1010); Methanobrevibacter smithii predicted 47.2°C (true 37°C, gid 1043). Pattern is GenomeSPOT bias — not a CultureForge composer issue per se. Recipe-side, the temperature flows through with high (0.87+) confidence, masking the under-prediction.

---

## Appendix A — Cross-reference to PHASE_6_BACKLOG.md

Items in the audit that the existing backlog (`docs/PHASE_6_BACKLOG.md`) already anticipates:

- **eggNOG-mapper integration** (backlog, high priority): would help with ANME (P2), cable bacteria (S1), AOA archaeal amoA (P4) by adding KEGG KO context to gapseq's pathway approach. Exemplars: gids 1005, 1006, 1007, 1004, 1008, 1049, 1102, 1106.
- **dbCAN / CAZy integration** (backlog, high priority): orthogonal to this audit's issues — none of the FAILs/PARTIALs are driven by carbon-substrate mis-selection. The audit did not surface CAZy-related miscalls.
- **HMM-based marker scans** (backlog, methodological): directly relevant to P4 (archaeal amoA), S2 (heliobacterial pshA), S5 (arrA, serA), S10 (Nitrospina nxrA). HMM profiles would catch these where BLAST identity threshold misses them.

Items the audit surfaces that are **NOT** already in the backlog and should be added:

- Recipe-composer `anammox` cultivation mode (P3).
- ANME-1/2a/3 detector extension (P2).
- Wood-Ljungdahl primary-mode gating (P1).
- Microaerophile O2 atmosphere modifier (P5).

## Appendix B — Genomes with composed recipes but PARTIAL/FAIL primary mode

These are the highest-risk false negatives for downstream users: CultureForge produced a recipe and an overall confidence, but the primary cultivation mode is biologically wrong. A naive user would run these recipes and the cultures would not grow. **Bold = FAIL with composed recipe**; italic = PARTIAL with composed recipe.

- **gid 1004 — Candidatus Electrothrix communis — predicted primary `anaerobic_respiratory`; expected `cable_long_distance_electron_transport`**
- **gid 1005 — Candidatus Methanocomedens sp. (ANME-2a) — predicted primary `methanogenic`; expected `anme_reverse_methanogenic`**
- **gid 1006 — Candidatus Methanophaga sp. (ANME-1) — predicted primary `methanogenic`; expected `anme_reverse_methanogenic`**
- **gid 1007 — Candidatus Methanovorans sp. (ANME-3) — predicted primary `methanogenic`; expected `anme_reverse_methanogenic`**
- **gid 1031 — Geobacter metallireducens GS-15 — predicted primary `acetogenic`; expected `anaerobic_respiratory`**
- **gid 1032 — Rhodospirillum rubrum ATCC 11170 — predicted primary `acetogenic`; expected `phototrophic`**
- **gid 1051 — Heliomicrobium modesticaldum Ice1 (Heliobacterium) — predicted primary `anaerobic_respiratory`; expected `phototrophic`**
- **gid 1056 — Azotobacter vinelandii DJ — predicted primary `acetogenic`; expected `aerobic_chemotrophic/lithotrophic_aerobic`**
- **gid 1061 — Methylorubrum extorquens AM1 (Methylobacterium) — predicted primary `phototrophic`; expected `aerobic_chemotrophic`**
- **gid 1066 — Bacillus selenitireducens MLS10 — predicted primary `aerobic_chemotrophic`; expected `anaerobic_respiratory`**
- **gid 1079 — Acetoanaerobium sticklandii DSM 519 (Clostridium sticklandii) — predicted primary `acetogenic`; expected `fermentative`**
- **gid 1085 — Sulfurospirillum barnesii SES-3 — predicted primary `fermentative`; expected `anaerobic_respiratory`**
- **gid 1112 — Neomoorella thermoacetica DSM 521 (Moorella thermoacetica) — predicted primary `fermentative`; expected `acetogenic`**
- **gid 1126 — Pelotomaculum schinkii HH — predicted primary `acetogenic`; expected `syntrophic`**
- **gid 1130 — Syntrophorhabdus aromaticivorans — predicted primary `acetogenic`; expected `syntrophic`**
- **gid 1133 — Leptothrix discophora CCM 2812 — predicted primary `phototrophic`; expected `aerobic_chemotrophic`**
- *gid 10 — Lactiplantibacillus plantarum (synonym Lactobacillus plantarum) — predicted primary `fermentative`; expected `fermentative`*
- *gid 14 — Sulfolobus acidocaldarius — predicted primary `aerobic_chemotrophic`; expected `aerobic_chemotrophic/lithotrophic_aerobic`*
- *gid 15 — Campylobacter jejuni — predicted primary `aerobic_chemotrophic`; expected `aerobic_chemotrophic`*
- *gid 17 — Sulfurimonas denitrificans — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic/anaerobic_respiratory`*
- *gid 23 — Nitrospira moscoviensis — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic`*
- *gid 1001 — Candidatus Brocadia sinica JPN1 (smoke test) — predicted primary `lithotrophic_aerobic`; expected `anammox`*
- *gid 1002 — Candidatus Brocadia fulgida — predicted primary `lithotrophic_aerobic`; expected `anammox`*
- *gid 1003 — Candidatus Phosphitivorax anaerolimi — predicted primary `fermentative`; expected `anaerobic_respiratory/fermentative`*
- *gid 1023 — Bradyrhizobium diazoefficiens USDA 110 — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic/aerobic_chemotrophic`*
- *gid 1027 — Pelagibacter ubique HTCC1062 — predicted primary `halophilic_with_rhodopsin`; expected `aerobic_chemotrophic/halophilic_with_rhodopsin`*
- *gid 1029 — Carboxydothermus hydrogenoformans Z-2901 — predicted primary `anaerobic_respiratory`; expected `anaerobic_respiratory/acetogenic`*
- *gid 1033 — Anaeromyxobacter dehalogenans 2CP-C — predicted primary `lithotrophic_aerobic`; expected `anaerobic_respiratory/aerobic_chemotrophic`*
- *gid 1034 — Syntrophus aciditrophicus SB — predicted primary `fermentative`; expected `syntrophic/fermentative`*
- *gid 1036 — Stutzerimonas stutzeri A1501 (Pseudomonas stutzeri) — predicted primary `aerobic_chemotrophic`; expected `aerobic_chemotrophic/anaerobic_respiratory`*
- *gid 1038 — Syntrophomonas wolfei subsp. wolfei Goettingen G311 — predicted primary `fermentative`; expected `syntrophic`*
- *gid 1040 — Magnetococcus marinus MC-1 — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic/aerobic_chemotrophic`*
- *gid 1041 — Syntrophobacter fumaroxidans MPOB — predicted primary `anaerobic_respiratory`; expected `syntrophic/anaerobic_respiratory`*
- *gid 1060 — Halorubrum lacusprofundi DSM 5036 — predicted primary `anaerobic_respiratory`; expected `aerobic_chemotrophic/halophilic_with_rhodopsin`*
- *gid 1065 — Frankia alni ACN14a — predicted primary `aerobic_chemotrophic`; expected `aerobic_chemotrophic/lithotrophic_aerobic`*
- *gid 1068 — Gallionella capsiferriformans ES-2 — predicted primary `aerobic_chemotrophic`; expected `lithotrophic_aerobic`*
- *gid 1072 — Mariprofundus ferrooxydans PV-1 — predicted primary `aerobic_chemotrophic`; expected `lithotrophic_aerobic`*
- *gid 1073 — Roseobacter litoralis Och 149 — predicted primary `phototrophic`; expected `phototrophic/aerobic_chemotrophic`*
- *gid 1075 — Sulfuricurvum kujiense DSM 16994 — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic/anaerobic_respiratory`*
- *gid 1078 — Cupriavidus metallidurans CH34 — predicted primary `lithotrophic_aerobic`; expected `aerobic_chemotrophic/lithotrophic_aerobic`*
- *gid 1083 — Beggiatoa alba B18LD — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic/aerobic_chemotrophic`*
- *gid 1089 — Leptospirillum ferrooxidans C2-3 — predicted primary `lithotrophic_aerobic`; expected `lithotrophic_aerobic`*
- *gid 1090 — Candidatus Jettenia caeni — predicted primary `lithotrophic_aerobic`; expected `anammox`*
- *gid 1098 — Magnetospirillum gryphiswaldense MSR-1 — predicted primary `lithotrophic_aerobic`; expected `aerobic_chemotrophic`*
- *gid 1101 — Gemmatimonas phototrophica — predicted primary `phototrophic`; expected `phototrophic/aerobic_chemotrophic`*
- *gid 1108 — Magnetospira sp. QH-2 — predicted primary `lithotrophic_aerobic`; expected `aerobic_chemotrophic`*
- *gid 1111 — Metallosphaera sedula ARS120-2 — predicted primary `aerobic_chemotrophic`; expected `lithotrophic_aerobic`*

---

## 6. Post-audit fix attempts (2026-05-14)

After this audit was complete, two of the five priority fixes were attempted in
Phase 5.0 session work. Both surfaced biological complexity that the
"structurally analogous fix" recommendation hadn't anticipated.

### P1 — Wood-Ljungdahl disqualifier (attempted, rolled back)

**Approach:** Add an `_apply_acetogenesis_disqualifiers` function modeled on the
`_apply_fermentation_disqualifiers` introduced in commit d4e9587. Used three
context filters: phototrophy cap, acceptor-metabolism cap, and syntrophy cap.

**Outcome:** Mixed. Cleanly resolved gid=1032 (Rhodospirillum rubrum) via the
phototrophy disqualifier. Partially resolved gid=1056 (Azotobacter vinelandii)
— capability score capped to secondary but recipe-mode selector still picked
acetogenic. Did NOT resolve gid=1031 (Geobacter — Fe(III) reduction detected
below 0.55 threshold), gid=1079 (Acetoanaerobium — no respiratory acceptor,
fermentation isn't in disqualifier acceptor list), or gids 1126/1130
(Pelotomaculum/Syntrophorhabdus — syntrophy capability scores below 0.60
disqualifier threshold).

**Root cause:** The fermentation disqualifier worked because aerobic respiration
is reliably detected at ≥ 0.55 for most aerobes. Acetogenesis false-positives,
in contrast, occur in organisms with heterogeneous "real primary modes" —
Fe(III) reducers (below acceptor-detection threshold without dedicated marker
support), Stickland fermenters (no respiratory acceptor at all), and syntrophs
(syntrophy detection itself is unreliable from genome alone). A single
disqualifier pattern can't catch all these cases without overcorrecting onto
real acetogens (Neomoorella thermoacetica, gid=1112, would have been
re-classified fermentative).

**Status:** Rolled back to commit d4e9587. P1 belongs in Phase 6 with one of:
(a) per-class detection improvements (better Fe(III) reduction marker support,
more reliable syntrophy detection), (b) Stickland-specific marker (grdAB
proline reductase), or (c) GenomeSPOT oxygen-tolerance gating ("acetogen
requires oxygen=not_tolerant") before WL can take primary slot.

### P2 — ANME-1/2a/3 detection extension (not attempted)

**Approach considered:** Extend the existing Phase 3.6 essential_marker_OR
trigger for `Anaerobic methane oxidation` (currently fires for gid=28
Methanoperedens via mcrA + dissimilatory nitrate reduction co-detection) to
also fire for ANME-1/2a/3 lineages.

**Blocker:** The existing trigger requires mcrA + (dsrAB OR mtrC_omcB OR
nitrate-reduction pathway). gids 1005/1006/1007 have mcrA hits but lack all
three acceptor signals. This is biologically correct: ANME-1/2a/3 perform
anaerobic methane oxidation in syntrophic consortia where the sulfate-reducing
partner is a separate organism (Desulfococcus, Desulfobulbus, etc.). The dsrAB
marker is in the PARTNER genome, not in the ANME MAG. Capability detection
can't see machinery that isn't there.

**Real fix requires one of:**
- Phylogenetic mcrA reference sequences that distinguish ANME-1/2/3-lineage
  mcrA from forward-methanogen mcrA (sequence-level discriminator; ANME-1 has
  a notably divergent mcrA from canonical methanogens)
- GTDB-Tk or similar taxonomy assignment, gating ANME mode by phylogenetic
  position
- External annotation / metagenomic context (which partner genomes are
  co-binned, etc.)

None of these is the simple "extend existing logic" the audit's P2
description suggested. ANME-1/2/3 detection is a real research problem, not a
threshold tweak.

**Status:** Deferred to Phase 5.1 or Phase 6 as a marker BLAST DB extension
(option 1 above) with curated ANME-lineage mcrA references.

### Implications for the framework

Both P1 and P2 surface the same meta-pattern: **the framework can detect
metabolisms whose machinery is present in the genome, but cannot infer
metabolisms that depend on environmental context (Stickland's substrate
availability) or syntrophic partnerships (ANME's external sulfate reducer).**
This is a fundamental limitation of any genome-only prediction tool and worth
documenting as such in the manuscript framing. CultureForge's strength is on
metabolisms with self-contained genomic signatures (sulfate reduction, forward
methanogenesis, oxygenic phototrophy, denitrification, etc.). Organisms whose
function emerges from community context fall outside its scope.

