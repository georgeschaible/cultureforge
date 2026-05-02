# CultureForge Marker Reference Curation

Authoritative record of every UniProt accession in `fetch_markers.sh` with verification details.

**Verification standard (Phase 1.5m):**
1. The accession was fetched from `rest.uniprot.org` and the protein description was read.
2. The protein name matches the intended marker function.
3. The source organism is biologically appropriate for the metabolism the marker diagnoses.
4. Swiss-Prot (reviewed) is preferred. TrEMBL (unreviewed) is used only when no Swiss-Prot entry exists in a biologically appropriate organism, with explicit justification.
5. **No reference may come from any species in the dev or blind validation sets.** Sequences from these organisms are excluded across ALL markers — not only the markers that diagnose them — to prevent self-validation contamination at the species level. The exclusion is by binomial; sequences from sister species in the same genus are permitted (e.g., *Methanococcus vannielii* is allowed even though *Methanocaldococcus jannaschii* is excluded).

Curation date: 2026-04-27 (Phase 1.5m).

### Excluded organisms (26 species)

The following organisms are in the development set (18) or blind validation set (8). No reference accession in `fetch_markers.sh` may come from any of these species.

**Development set (18):**
1. *Escherichia coli* K-12 MG1655
2. *Nitratidesulfovibrio vulgaris* Hildenborough (= *Desulfovibrio vulgaris*)
3. *Methanocaldococcus jannaschii* (= *Methanococcus jannaschii*)
4. *Thermus aquaticus*
5. *Lactobacillus plantarum*
6. *Acidithiobacillus ferrooxidans*
7. *Clostridium acetobutylicum*
8. *Geobacter sulfurreducens*
9. *Sulfolobus acidocaldarius*
10. *Campylobacter jejuni*
11. *Magnetospirillum magneticum*
12. *Sulfurimonas denitrificans*
13. *Nitrosomonas europaea*
14. *Rhodopseudomonas palustris*
15. *Halobacterium salinarum*
16. *Syntrophomonas wolfei*
17. *Acetobacterium woodii*
18. *Allochromatium vinosum*

**Blind validation set (8):**
19. *Candidatus Methanoperedens nitroreducens* (ANME-2d)
20. *Candidatus Prometheoarchaeum syntrophicum* (Asgard)
21. *Candidatus Scalindua profunda* (anammox)
22. *Chloroflexus aurantiacus* (FAP / anoxygenic phototroph)
23. *Dehalococcoides mccartyi* (organohalide respiration)
24. *Nitrospira moscoviensis* (comammox)
25. *Picrophilus torridus* (acidophilic archaeon)
26. *Thermotoga maritima* (hyperthermophile fermenter)

Sister-species rule: a reference from *Thermus thermophilus* is permitted even though *Thermus aquaticus* is excluded; a reference from *Methanococcus vannielii* is permitted even though *Methanocaldococcus jannaschii* is excluded; etc.

---

## Marker: mcrA

**Protein:** Methyl-coenzyme M reductase, alpha subunit (EC 2.8.4.1)
**Diagnoses:** Methanogenesis (terminal step) — required by all methanogenic archaea; also present in ANME (anaerobic methane oxidation) where it operates in reverse.
**Expected in:** Methanobacteriales, Methanococcales, Methanosarcinales, Methanocellales, Methanopyrales, Methanomassiliicoccales; ANME-1, ANME-2, ANME-3.
**Status:** **Rebuilt in Phase 1.5m.** Q58256 (*Methanocaldococcus jannaschii*) removed per dev-set rule. Replaced with Q49605 (*Methanopyrus kandleri*).

### Verified accessions

| Accession | Status | Length | Source organism | Order |
|---|---|---|---|---|
| P11558 | Swiss-Prot | 550 | *Methanothermobacter marburgensis* | Methanobacteriales |
| P07962 | Swiss-Prot | 570 | *Methanosarcina barkeri* | Methanosarcinales |
| Q8THH1 | Swiss-Prot | 570 | *Methanosarcina acetivorans* | Methanosarcinales |
| Q49605 | Swiss-Prot | 553 | *Methanopyrus kandleri* | Methanopyrales (hyperthermophile) |
| P07961 | Swiss-Prot | 553 | *Methanococcus vannielii* | Methanococcales |

### Search queries
- `protein_name:"methyl-coenzyme M reductase alpha" AND reviewed:true`

### Rejected / excluded
- **Q58256** (M. jannaschii) — REMOVED Phase 1.5m. Dev-set organism.
- **Q8TIY1** — Fun34-related protein (M. acetivorans), not McrA.
- **Q6LYP5** — FAD synthase (M. maripaludis), not McrA.
- **A5UL61** — cytidylate kinase (M. brevibacter), not McrA.

---

## Marker: mcrBG

**Protein:** Methyl-coenzyme M reductase, beta and gamma subunits (EC 2.8.4.1)
**Diagnoses:** Methanogenesis confirmatory marker — co-occurs with mcrA in all methanogens. Used as orthogonal evidence; an mcrA hit with no mcrBG raises suspicion of a partial/transferred annotation.
**Expected in:** Same as mcrA.
**Status:** **Rebuilt in Phase 1.5m.** Q58252 / Q58255 (*Methanocaldococcus jannaschii*) removed per dev-set rule. Replaced with P12972 (mcrB) and P12973 (mcrG) from *Methanothermus fervidus*.

### Verified accessions

| Accession | Status | Length | Source organism | Subunit |
|---|---|---|---|---|
| P11560 | Swiss-Prot | 443 | *Methanothermobacter marburgensis* | β |
| P07955 | Swiss-Prot | 434 | *Methanosarcina barkeri* | β |
| P12972 | Swiss-Prot | 438 | *Methanothermus fervidus* | β |
| P11562 | Swiss-Prot | 249 | *Methanothermobacter marburgensis* | γ |
| P07964 | Swiss-Prot | 248 | *Methanosarcina barkeri* | γ |
| P12973 | Swiss-Prot | 249 | *Methanothermus fervidus* | γ |

### Search queries
- `(gene_exact:mcrB OR gene_exact:mcrG) AND reviewed:true`

### Rejected / excluded
- **Q58252, Q58255** (M. jannaschii) — REMOVED Phase 1.5m. Dev-set organism.
- **P11559** (filed as mcrBG but is actually mcrA in M. voltae) — Phase 1.5l.
- **Q8TIY0** — methyltransferase FkbM domain (M. acetivorans), not mcrBG.
- **Q58257, Q58258** — methyltransferase mtrE / mtrD (M. jannaschii), wrong family.

---

## Marker: dsrAB

**Protein:** Dissimilatory sulfite reductase, alpha and beta subunits (EC 1.8.99.5)
**Diagnoses:** Sulfate reduction (forward direction) AND sulfide oxidation via reverse-dsr. Discrimination between forward and reverse direction requires the qmoA companion marker (Phase 1.5k AND-rule: forward SR detection requires dsrAB AND qmoA both positive).
**Expected in:** Forward — Desulfovibrionales, Desulfobacterales, Desulfobulbales, Desulfotomaculum, Archaeoglobales. Reverse — Chromatiales (e.g., *Allochromatium*), Chlorobaculum, Beggiatoa.
**Status:** **Rebuilt in Phase 1.5m.** Phase 1.5l set was 2 entries (P45574, P45575) both from *D. vulgaris* Hildenborough — a development-set organism. Per the dev-set rule, these are excluded. Replaced with 8 entries (4 alpha + 4 beta) from 4 distinct organisms across bacteria + archaea.

### Verified accessions

| Accession | Status | Length | Source organism | Family | Subunit |
|---|---|---|---|---|---|
| Q59109 | Swiss-Prot | 418 | *Archaeoglobus fulgidus* DSM 4304 | Archaeoglobaceae (archaea) | α |
| Q59110 | Swiss-Prot | 366 | *Archaeoglobus fulgidus* DSM 4304 | Archaeoglobaceae (archaea) | β |
| P94693 | Swiss-Prot | 198 (fragment) | *Megalodesulfovibrio gigas* DSM 1382 | Desulfovibrionaceae | α |
| P94694 | Swiss-Prot | 262 (fragment) | *Megalodesulfovibrio gigas* DSM 1382 | Desulfovibrionaceae | β |
| A0A7T5VCS7 | TrEMBL | 429 | *Desulfobulbus oligotrophicus* | Desulfobulbaceae | α |
| A0A7T5VCY6 | TrEMBL | 380 | *Desulfobulbus oligotrophicus* | Desulfobulbaceae | β |
| A0A328FC82 | TrEMBL | 441 | *Desulfobacter hydrogenophilus* | Desulfobacteraceae | α |
| A0A328FAA8 | TrEMBL | 382 | *Desulfobacter hydrogenophilus* | Desulfobacteraceae | β |

### Search queries
- `(protein_name:"dissimilatory-type subunit alpha" OR protein_name:"dissimilatory sulfite reductase alpha") AND reviewed:true`
- `gene_exact:dsrA AND organism_name:"Desulfobulbus"`
- `gene_exact:dsrA AND (organism_name:"Desulfobacter" OR organism_name:"Desulfomicrobium")`

### TrEMBL justification
Swiss-Prot dsrAB is exhausted at 7 entries: 3 from D. vulgaris (test set), 1 from Allochromatium vinosum (test set), 2 from Archaeoglobus, 2 from Megalodesulfovibrio (latter two are partial fragments). To achieve 4-organism phylogenetic diversity outside the test set, TrEMBL entries from Desulfobulbus oligotrophicus and Desulfobacter hydrogenophilus are added. Both are full-length (429 / 441 aa α; 380 / 382 aa β) and from genuine sulfate-reducing genera with documented physiology in the literature.

### Rejected accessions (Phase 1.5l)
- **O28606** — sulfate adenylyltransferase (sat) from A. fulgidus, not dsrAB. Different enzyme.
- **O28607** — diphthamide synthase domain protein from A. fulgidus, unrelated.

### Dev-set exclusions
- **P45574, P45575** (D. vulgaris Hildenborough) — REMOVED. D. vulgaris is in the development set; including its own dsrAB is self-validation.
- **O33998** (Allochromatium vinosum dsrA) — NOT INCLUDED. Allochromatium is the qmoA-discrimination test organism.

---

## Marker: aprAB

**Protein:** Adenylyl-sulfate reductase, alpha and beta subunits (EC 1.8.99.2). Distinct from assimilatory APS reductase (gene cysH) which uses thioredoxin and operates in cysteine biosynthesis.
**Diagnoses:** Sulfate reduction (forward direction) — second step after sat (sulfate adenylyltransferase) and before dsrAB. Co-marker with dsrAB; high-confidence forward SR call requires both.
**Expected in:** Same as forward dsrAB — Desulfovibrionales, Desulfobacterales, Desulfobulbales, Archaeoglobales.
**Status:** **Rebuilt in Phase 1.5m.** Phase 1.5l set was 2 entries (T2G6Z9, T2G899), both from *Megalodesulfovibrio gigas*. Both are correct but provide no phylogenetic diversity. Expanded to 6 entries from 3 organisms.

### Verified accessions

| Accession | Status | Length | Source organism | Family | Subunit |
|---|---|---|---|---|---|
| T2G6Z9 | Swiss-Prot | 666 | *Megalodesulfovibrio gigas* DSM 1382 | Desulfovibrionaceae | α |
| T2G899 | Swiss-Prot | 167 | *Megalodesulfovibrio gigas* DSM 1382 | Desulfovibrionaceae | β |
| A0A7J2TKV3 | TrEMBL | 643 | *Archaeoglobus fulgidus* | Archaeoglobaceae (archaea) | α |
| A0A7C3MF07 | TrEMBL | 150 | *Archaeoglobus fulgidus* | Archaeoglobaceae (archaea) | β |
| A0A2G6MT98 | TrEMBL | 653 | *Desulfobacter postgatei* | Desulfobacteraceae | α |
| A0A2G6MTF3 | TrEMBL | 145 | *Desulfobacter postgatei* | Desulfobacteraceae | β |

### Search queries
- `id:APRA* OR id:APRB* AND reviewed:true`
- `gene_exact:aprA AND organism_name:"Archaeoglobus"`
- `gene_exact:aprA AND (organism_name:"Desulfobulbus" OR organism_name:"Desulfobacter")`

### TrEMBL justification
T2G6Z9 / T2G899 are the only Swiss-Prot entries for dissimilatory aprA/aprB (other Swiss-Prot hits with similar names are assimilatory cysH — different enzyme, different metabolism). To add phylogenetic breadth (archaeal + Desulfobacteraceae), TrEMBL entries from Archaeoglobus fulgidus and Desulfobacter postgatei are added. Lengths confirm full-length (643/653 α, 150/145 β are appropriate for the FAD-binding β subunit).

### Rejected candidates (Phase 1.5l)
- **Q725B6** — AgrB-like accessory gene regulator from *Listeria monocytogenes*. Wrong protein, wrong organism.
- **Q72AU3** — Glycine-tRNA ligase β from *D. vulgaris*. Wrong protein.

### Dev-set exclusions
None — Megalodesulfovibrio, Archaeoglobus, and Desulfobacter postgatei are not in the development set.

### Cross-reactivity warning
The Swiss-Prot search returned many `cysH`-style assimilatory APS reductase entries with similar names (e.g., `CYSH_MYCTU`, `CYSH_PSEAE`). These are explicitly excluded from this marker file because:
1. They diagnose sulfur assimilation for biosynthesis, not dissimilatory sulfate reduction for energy.
2. They are present in many non-SR organisms (E. coli, B. subtilis, mycobacteria) that should not be called as sulfate reducers.
3. Their gene name is `cysH`, not `aprA`.

---

## Marker: qmoA

**Protein:** Quinone-interacting membrane-bound oxidoreductase complex, subunit A (forward sulfate reduction discriminator)
**Diagnoses:** Forward dissimilatory sulfate reduction. Phase 1.5k load-bearing AND-rule: forward SR detection requires dsrAB AND qmoA both positive.
**Expected in:** Forward SRBs (Desulfovibrionales, Desulfobacterales). ABSENT in reverse-dsr sulfide oxidizers (e.g., Allochromatium).
**Status:** Verified clean Phase 1.5l + 1.5m. No changes needed.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| Q7X167 | TrEMBL | varies | *Desulfovibrio desulfuricans* |
| A0A8G2C1P1 | TrEMBL | varies | *Desulfomicrobium norvegicum* |
| A0A0U9HMV6 | TrEMBL | varies | *Thermodesulfovibrio aggregans* |
| S5VWR0 | TrEMBL | varies | *Megalodesulfovibrio gigas* |
| Q3IBM0 | TrEMBL | varies | uncultured SRB |
| A0A212JYQ4 | TrEMBL | varies | uncultured *Desulfovibrio* sp. |

### Cross-reactivity warning
qmoA belongs to the NfnAB/HdrA flavoprotein superfamily. Phase 1.5l hit-pattern audit found cross-reactive 30-39% identity hits in Methanococcus, Acidithiobacillus, Sulfolobus, Syntrophomonas (none of which are sulfate reducers). The dsrAB+qmoA AND-rule absorbs all four FALSE_POS rows; no downstream consequence. Documented so the threshold (currently `pident≥30`) isn't tightened without considering the AND-rule's existing protection.

### Dev-set exclusion
Q72CJ9 (D. vulgaris Hildenborough qmoA) was excluded from this set in Phase 1.5k.

---

## Marker: acsB_cdhC

**Protein:** Acetyl-CoA synthase α subunit / Acetyl-CoA decarbonylase-synthase complex β subunit (Wood-Ljungdahl methyl-branch terminal step). EC 2.3.1.169.
**Diagnoses:** Wood-Ljungdahl pathway operation — acetogenesis (forward, anabolic) or acetoclastic methanogenesis (reverse, catabolic). Phase 1.5j adds negative-marker discrimination: dsrAB / aprAB / mtrC_omcB rule out acetogenesis even when CODH/ACS is present.
**Expected in:** Acetogens (Acetobacterium, Moorella, Clostridium ljungdahlii), acetoclastic methanogens (Methanosarcina), CODH-using archaea (Archaeoglobus when oxidizing CO).
**Status:** All 5 accessions verified clean Phase 1.5l + 1.5m.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| P27988 | Swiss-Prot | varies | *Neomoorella thermoacetica* (acsA) |
| P27989 | Swiss-Prot | varies | *Neomoorella thermoacetica* (acsB) |
| P72021 | Swiss-Prot | varies | *Methanosarcina thermophila* (cdhC1) |
| O29868 | Swiss-Prot | varies | *Archaeoglobus fulgidus* (cdhC) |
| O27745 | Swiss-Prot | varies | *Methanothermobacter thermautotrophicus* (cdhC) |

### Note on gene-name confusion
UniProt's gene name `acsB` maps to "acetyl-CoA synthetase" (a ligase, EC 6.2.1.1) — DIFFERENT enzyme from the WL synthase (EC 2.3.1.169). The references above are by EC number / protein-name match, not by gene name `acsB`.

---

## Marker: cooS_cdhA

**Protein:** Carbon monoxide dehydrogenase / acetyl-CoA decarbonylase-synthase α subunit. EC 1.2.7.4.
**Diagnoses:** Wood-Ljungdahl carbonyl-branch and CO oxidation. Co-marker with acsB_cdhC.
**Expected in:** Same as acsB_cdhC.
**Status:** **Rebuilt in Phase 1.5m.** Q58138 (Methanocaldococcus jannaschii) excluded — dev-set organism.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| P31896 | Swiss-Prot | 639 | *Rhodospirillum rubrum* |
| O28429 | Swiss-Prot | 622 | *Archaeoglobus fulgidus* |
| A0A4P8R3D7 | TrEMBL | 628 | *Methanosarcina mazei* |
| Q8TXX3 | Swiss-Prot | 638 | *Methanopyrus kandleri* |

### Excluded
- **Q58138** (M. jannaschii cooS) — Phase 1.5m, dev-set rule.

---

## Marker: amoA

**Protein:** Ammonia monooxygenase, α subunit. EC 1.14.99.39.
**Diagnoses:** Aerobic ammonia oxidation — bacterial (AOB) or archaeal (AOA) or comammox (Nitrospira).
**Expected in:** Nitrosomonadales, Nitrospira spp. with comammox capability, Thaumarchaeota.
**Status:** **Rebuilt in Phase 1.5m.** Q04507 (Nitrosomonas europaea) excluded — dev-set organism. Phase 1.5l short-fragment refs (A0A7D4WXT9, A0A8D4WF74) retained as comammox coverage; both <140 aa but they are the only Nitrospira-clade entries available.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| O85076 | TrEMBL | 274 | *Nitrosospira multiformis* (AOB) |
| P95336 | TrEMBL | 274 | *Nitrosospira briensis* (AOB) |
| A0A7D4WXT9 | TrEMBL | 79 | *Ca.* Nitrospira inopinata (comammox; sister-species rule, N. moscoviensis is blind set) |
| A0A8D4WF74 | TrEMBL | 138 | uncultured *Nitrospira* sp. (comammox; not pinned to a species binomial) |

### Excluded
- **Q04507** (N. europaea) — Phase 1.5m, dev-set rule. Was the only Swiss-Prot amoA; entire amoA set is now TrEMBL.

---

## Marker: hao

**Protein:** Hydroxylamine oxidoreductase. EC 1.7.2.6 / 1.7.2.9.
**Diagnoses:** Second step of aerobic ammonia oxidation (oxidizes NH₂OH to NO). Co-marker with amoA. Also catalyzes hydrazine oxidation in anammox (different reaction, same enzyme family).
**Expected in:** AOB (Nitrosomonadales, Nitrosococcus), anammox bacteria (Kuenenia, Brocadia).
**Status:** **Rebuilt in Phase 1.5m.** Q50925 (Nitrosomonas europaea) excluded — dev-set organism.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| M5DCM0 | TrEMBL | 580 | *Nitrosococcus oceani* (AOB) |
| A0A1I0GQH4 | TrEMBL | 573 | *Nitrosospira multiformis* (AOB) |
| Q1PX48 | Swiss-Prot | 536 | *Kuenenia stuttgartiensis* (anammox HAO) |

### Excluded
- **Q50925** (N. europaea) — Phase 1.5m, dev-set rule.

---

## Marker: soxB

**Protein:** Thiosulfohydrolase / SoxB protein (sulfur oxidation SOX pathway).
**Diagnoses:** Periplasmic thiosulfate / sulfide oxidation via SOX enzymatic complex. Diagnoses chemolithoautotrophic sulfur oxidation in α/β/γ-proteobacteria, Epsilonproteobacteria, and green sulfur bacteria.
**Expected in:** Paracoccus, Thiobacillus, Sulfurimonas, Allochromatium, Chlorobaculum, etc.
**Status:** Verified clean Phase 1.5l + 1.5m. No changes needed.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| P72177 | TrEMBL | varies | *Paracoccus denitrificans* |
| A0A5C4S040 | TrEMBL | varies | *Chlorobaculum thiosulfatiphilum* |
| A0A3D8P969 | TrEMBL | varies | *Paracoccus thiocyanatus* |

### Note
Swiss-Prot "soxB" maps to **sarcosine oxidase** (different enzyme entirely). All sulfur-SoxB references are necessarily TrEMBL.

---

## Marker: pufLM

**Protein:** Photosynthetic reaction center, L and M subunits (anoxygenic photosystem II — purple bacteria + Chloroflexales-style FAP).
**Diagnoses:** Anoxygenic phototrophy in purple bacteria (Rhodobacterales, Rhodospirillales) and FAP filamentous anoxygenic phototrophs (Chloroflexales).
**Expected in:** Rhodobacter, Cereibacter, Blastochloris, Rhodospirillum, Allochromatium (purple sulfur), Chloroflexus (FAP).
**Status:** **Rebuilt in Phase 1.5m.** P51762, P51763 (Allochromatium vinosum) excluded — dev-set organism.

| Accession | Status | Length | Source organism | Subunit |
|---|---|---|---|---|
| P0C0Y8 | Swiss-Prot | varies | *Cereibacter sphaeroides* | L |
| P19057 | Swiss-Prot | varies | *Rhodobacter capsulatus* | L |
| P06009 | Swiss-Prot | varies | *Blastochloris viridis* | L |
| P10717 | Swiss-Prot | varies | *Rhodospirillum rubrum* | L |
| P0C0Y9 | Swiss-Prot | varies | *Cereibacter sphaeroides* | M |
| P11847 | Swiss-Prot | varies | *Rhodobacter capsulatus* | M |
| P06010 | Swiss-Prot | varies | *Blastochloris viridis* | M |
| P10718 | Swiss-Prot | varies | *Rhodospirillum rubrum* | M |

### Excluded
- **P51762, P51763** (Allochromatium vinosum pufLM) — Phase 1.5m, dev-set rule.

### Note
Phase 1.5l originally added P02948 (pufA, light-harvesting α) and P06008 (puhA, RC-H) as cross-reactive paralogs; these were removed in Phase 1.5m to keep the marker file restricted to true L/M subunits.

---

## Marker: pscA_fmoA

**Protein:** Green sulfur bacteria reaction center components — fmoA (Fenna-Matthews-Olson light-harvesting protein), pscC (cytochrome c), pscD (RC 17 kDa).
**Diagnoses:** Anoxygenic phototrophy via Type-I reaction center (Chlorobiaceae).
**Expected in:** *Chlorobaculum*, *Chlorobium*, *Prosthecochloris*, *Pelodictyon*.
**Status:** Phase 1.5l set retained. No pscA Swiss-Prot or TrEMBL exists in canonical form; pscC, pscD, and fmoA collectively fingerprint the GSB reaction center.

| Accession | Status | Source organism | Component |
|---|---|---|---|
| Q46393 | Swiss-Prot | *Chlorobaculum tepidum* | fmoA |
| Q46135 | Swiss-Prot | *Chlorobaculum thiosulfatiphilum* | fmoA |
| O07091 | Swiss-Prot | *Chlorobaculum tepidum* | pscC |
| Q8KEP5 | Swiss-Prot | *Chlorobaculum tepidum* | pscD |

---

## Marker: psaA_psbA

**Protein:** Photosystem I P700 apoprotein A1 (psaA) + Photosystem II D1 (psbA). Oxygenic photosynthesis terminal subunits.
**Diagnoses:** Oxygenic phototrophy — cyanobacteria + plastids.
**Expected in:** *Synechocystis*, *Synechococcus*, *Thermostichus*, plus eukaryotic algae.
**Status:** Verified clean Phase 1.5m.

| Accession | Status | Length | Source organism | Subunit |
|---|---|---|---|---|
| P29254 | Swiss-Prot | varies | *Synechocystis* sp. PCC 6803 | psaA |
| P0A406 | Swiss-Prot | varies | *Synechococcus elongatus* | psaA |
| P16033 | Swiss-Prot | varies | *Synechocystis* sp. PCC 6803 | psbA2 |
| P14660 | Swiss-Prot | varies | *Synechocystis* sp. PCC 6803 | psbA |
| P51765 | Swiss-Prot | varies | *Thermostichus vulcanus* | psbA |

---

## Marker: rhodopsin

**Protein:** Microbial rhodopsins (bacteriorhodopsin in haloarchaea + proteorhodopsin in marine bacteria).
**Diagnoses:** Light-driven proton pumping — provides supplementary energy for haloarchaea + photoheterotrophic marine bacteria.
**Expected in:** Halobacteriaceae, marine γ-proteobacteria with proteorhodopsin gene clusters.
**Status:** **Rebuilt in Phase 1.5m.** P02945 (Halobacterium salinarum) excluded — dev-set organism. Replaced with Q5UXY6 + Q5V0R5 (Haloarcula marismortui BR-I and BR-II).

| Accession | Status | Length | Source organism |
|---|---|---|---|
| Q5UXY6 | Swiss-Prot | 250 | *Haloarcula marismortui* (BR-I) |
| Q5V0R5 | Swiss-Prot | 250 | *Haloarcula marismortui* (BR-II) |
| Q9F7P4 | Swiss-Prot | varies | γ-proteobacterium EBAC31A08 (proteorhodopsin) |

### Excluded
- **P02945** (Halobacterium salinarum bacteriorhodopsin) — Phase 1.5m, dev-set rule.

---

## Marker: nifH

**Protein:** Nitrogenase iron protein (component II of the nitrogenase complex).
**Diagnoses:** Biological N₂ fixation. Marker of choice across the entire diazotroph community.
**Expected in:** Free-living and symbiotic N₂ fixers — Azotobacter, Klebsiella, Rhizobiales, cyanobacteria, Clostridium, Methanococcales (some), etc.
**Status:** Verified clean Phase 1.5m.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| P00459 | Swiss-Prot | varies | *Azotobacter vinelandii* (nifH1) |
| P00458 | Swiss-Prot | varies | *Klebsiella pneumoniae* |
| P06117 | Swiss-Prot | varies | *Bradyrhizobium diazoefficiens* |
| P17303 | Swiss-Prot | varies | *Azospirillum brasilense* |
| P22921 | Swiss-Prot | varies | *Rhodospirillum rubrum* |

### Excluded earlier
- **P07328** (Phase 1.5l) — was nifD (different subunit), removed.

---

## Marker: nosZ

**Protein:** Nitrous oxide reductase. EC 1.7.2.4. Final step of denitrification (N₂O → N₂).
**Diagnoses:** Denitrification. Phase 1.5j makes nosZ an essential gating marker — denitrification capability requires positive nosZ hit (prevents partial-pathway false positives).
**Expected in:** Pseudomonas, Paracoccus, Rhizobiales, some Bacillus, Thiobacillus, Sulfurimonas.
**Status:** Verified clean Phase 1.5m.

| Accession | Status | Source organism |
|---|---|---|
| P19573 | Swiss-Prot | *Stutzerimonas stutzeri* (formerly Pseudomonas stutzeri) |
| Q51705 | Swiss-Prot | *Paracoccus denitrificans* |
| Q59105 | Swiss-Prot | *Cupriavidus necator* |
| P94127 | Swiss-Prot | *Achromobacter cycloclastes* |
| Q9HYL2 | Swiss-Prot | *Pseudomonas aeruginosa* |

### Excluded earlier
- **P24474** (Phase 1.5l) — was nirS, removed.
- **Q53198** (Phase 1.5l) — was transposase, removed.

---

## Marker: cyc2

**Protein:** Outer-membrane c-type cytochrome involved in extracellular Fe(II) oxidation.
**Diagnoses:** Acidophilic and neutrophilic iron oxidation. Acidophilic Cyc2 is monoheme (~150-225 aa); neutrophilic Cyc2 is multiheme (~400-500 aa). Both are functionally homologous Fe(II)-oxidizing outer-membrane cytochromes.
**Expected in:** *Acidithiobacillus* spp., *Leptospirillum*, *Acidihalobacter*, *Mariprofundus*, *Sideroxydans*, *Gallionella*.
**Status:** **Rebuilt in Phase 1.5m.** B7JAQ7, O33823 (Acidithiobacillus ferrooxidans) excluded — dev-set organism. All cyc2 references are necessarily TrEMBL (no Swiss-Prot exists for this protein family).

| Accession | Status | Length | Source organism | Type |
|---|---|---|---|---|
| A0A060UV08 | TrEMBL | ~180 | *Acidithiobacillus ferrivorans* | Acidophilic monoheme (sister-species rule) |
| K4EQ75 | TrEMBL | 225 | *Leptospirillum ferriphilum* | Acidophilic monoheme (annotated as putative; gene name cyc2) |
| B2ZFM8 | TrEMBL | 464 | *Acidihalobacter prosperus* | Acidophilic multiheme |
| A0A0H3ZGZ2 | TrEMBL | 439 | *Mariprofundus ferrooxydans* PV-1 | Neutrophilic multiheme |

### Excluded
- **B7JAQ7, O33823** (A. ferrooxidans cyc2) — Phase 1.5m, dev-set rule.
- **Q4A194** (Phase 1.5l) — barley Beclin-1, completely wrong protein. Removed.

---

## Marker: mtrC_omcB

**Protein:** Outer-membrane multi-heme cytochromes for extracellular Fe(III) reduction. mtrC = *Shewanella* MtrCAB system; omcB = *Geobacter* OmcB.
**Diagnoses:** Iron(III) reduction (and reduction of other extracellular electron acceptors).
**Expected in:** *Shewanella*, *Geobacter*, *Pelobacter*, related Geobacteraceae.
**Status:** **Rebuilt in Phase 1.5m.** Q749K5 (Geobacter sulfurreducens omcB) excluded — dev-set organism.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| P0DSN4 | Swiss-Prot | 650 | *Shewanella baltica* (MtrC) |
| E6XFS0 | TrEMBL | 654 | *Shewanella putrefaciens* (MtrC) |
| A0ABR9NUT4 | TrEMBL | 747 | *Geobacter anodireducens* (OmcB) |

### Excluded
- **Q749K5** (G. sulfurreducens omcB) — Phase 1.5m, dev-set rule.
- **Q74D43, Q74AE7** (Phase 1.5l) — sugar transporter and isomerase, wrong proteins.

---

## Marker: rdhA

**Protein:** Reductive dehalogenase (catalytic A subunit). EC 1.21.99.x.
**Diagnoses:** Organohalide respiration — uses chlorinated/brominated organics as electron acceptors.
**Expected in:** *Dehalococcoides*, *Desulfitobacterium*, *Dehalobacter*, *Sulfurospirillum*.
**Status:** **Rebuilt in Phase 1.5m.** Q3ZAB8, Q69GM4 (Dehalococcoides mccartyi) excluded — blind-set organism.

| Accession | Status | Length | Source organism |
|---|---|---|---|
| Q8L172 | Swiss-Prot | 551 | *Desulfitobacterium hafniense* (pceA) |
| O68252 | Swiss-Prot | 501 | *Sulfurospirillum multivorans* (pceA) |
| Q8GJ27 | Swiss-Prot | 551 | *Dehalobacter restrictus* (pceA) |
| Q8GJ31 | Swiss-Prot | 551 | *Desulfitobacterium hafniense* (pceA2) |
| Q848J2 | Swiss-Prot | 551 | *Desulfitobacterium hafniense* (pceA) |

### Excluded
- **Q3ZAB8** (D. mccartyi tceA) — Phase 1.5m, blind-set rule.
- **Q69GM4** (D. mccartyi vcrA) — Phase 1.5m, blind-set rule.
- **Q69GM3** (Phase 1.5l) — vcrB membrane anchor, not catalytic rdhA.

---

## Marker: autotrophy

**Protein:** Multi-pathway CO₂ fixation diagnostic — covers four distinct autotrophic pathways via their key enzymes.
**Diagnoses:** Autotrophic CO₂ fixation. Covers: rbcL (Calvin-Benson-Bassham), aclA (reductive TCA / rTCA), mcr (3-hydroxypropionate), 4hbd (3HP/4HB archaeal cycle).
**Expected in:** Cyanobacteria + many bacteria (CBB), Aquificales / Chlorobiaceae / Epsilonproteobacteria (rTCA), Chloroflexales / some Crenarchaeota (3HP), Sulfolobales / Thermoproteales (3HP/4HB).
**Status:** **Expanded in Phase 1.5m** to cover all four pathways per CLAUDE.md addendum specification.

| Accession | Status | Length | Source organism | Pathway marker |
|---|---|---|---|---|
| P54205 | Swiss-Prot | 472 | *Synechocystis* sp. | rbcL — CBB |
| P00880 | Swiss-Prot | 472 | *Synechococcus* sp. | rbcL — CBB |
| P04718 | Swiss-Prot | 466 | *Rhodospirillum rubrum* | cbbM (form II rbcL) — CBB |
| A0A0S4XNU1 | TrEMBL | 604 | *Sulfurovum* sp. | aclA — rTCA |
| A4YEN2 | Swiss-Prot | 357 | *Metallosphaera sedula* | mcr — 3HP |
| A0A2U9IIH9 | TrEMBL | 479 | *Acidianus brierleyi* | 4hbd — 3HP/4HB archaeal |

### Excluded
- **Q1JU64** (Phase 1.5l) — cow MHC class II antigen.
- **Q3IXP8** — hydroxypyruvate reductase (different enzyme).
- **Q8KFR1** — ribosomal protein.
- **Q9F721** — cytochrome bc.
- **A4YHK3** — DEAD-box helicase.

### Sister-species note
*Metallosphaera sedula* and *Acidianus brierleyi* are non-test-set archaea (Sulfolobales). *Chloroflexus aurantiacus* is in the blind set, so its mcr (Q6QQP7) was NOT used despite being the canonical Chloroflexus mcr; the Metallosphaera mcr is the preferred replacement.

---

## Marker: terminal_oxidases

**Protein:** Multi-architecture aerobic terminal oxidase diagnostic.
**Diagnoses:** Aerobic respiration. Covers four distinct heme-copper oxidase architectures (caa3, qox, aa3-Cox, cbb3) plus archaeal SoxB/QoxA terminal oxidases.
**Expected in:** All aerobes / facultative anaerobes / microaerophiles. Architecture varies by lineage.
**Status:** **Expanded in Phase 1.5m** per Phase 1.5l hit-pattern audit findings (Sulfolobus, Campylobacter, Sulfurimonas were missing detection).

| Accession | Status | Length | Source organism | Architecture |
|---|---|---|---|---|
| P82543 | Swiss-Prot | varies | *Thermus thermophilus* (cbaD) | caa3 — sister species (T. aquaticus excluded) |
| P34957 | Swiss-Prot | varies | *Bacillus subtilis* (qoxA) | quinol oxidase |
| P34956 | Swiss-Prot | varies | *Bacillus subtilis* (qoxB) | quinol oxidase |
| P08305 | Swiss-Prot | varies | *Paracoccus denitrificans* (ctaDI) | aa3 Cox subunit 1 |
| P08306 | Swiss-Prot | varies | *Paracoccus denitrificans* (ctaC) | aa3 Cox subunit 2 |
| Q05572 | Swiss-Prot | 539 | *Sinorhizobium meliloti* (fixN) | cbb3 |
| P98059 | Swiss-Prot | 532 | *Rhodobacter capsulatus* (ctaD) | cbb3-like |
| Q97VG9 | TrEMBL | 511 | *Saccharolobus solfataricus* (soxB) | archaeal terminal oxidase |
| F4B7C5 | TrEMBL | 506 | *Acidianus hospitalis* (qoxA) | archaeal quinol oxidase |

### Phase 1.5l excluded
- **Q56431** — pyrroline-5-carboxylate reductase fragment (Thermus). Wrong protein.
- **P39484** — glucose-1-dehydrogenase. Wrong protein.
- **Q4J781** — *Sulfolobus acidocaldarius* alcohol dehydrogenase. Wrong protein. Caused a documented detection regression (Phase 1.5l Sulfolobus aerobic respiration drop) that this Phase 1.5m expansion now resolves with proper archaeal SoxB/QoxA references.

### Sister-species rule
*Thermus thermophilus* (P82543) is allowed because the dev-set organism is *Thermus aquaticus* — a different species. *Saccharolobus solfataricus* and *Acidianus hospitalis* are different from the dev-set *Sulfolobus acidocaldarius*.

---

## Marker: hzsA

**Protein:** Hydrazine synthase, α subunit. Catalyses NH₂OH + NH₃ → N₂H₄.
**Diagnoses:** Anaerobic ammonium oxidation (anammox).
**Expected in:** *Ca.* Brocadia, *Ca.* Kuenenia, *Ca.* Jettenia, *Ca.* Anammoxoglobus, *Ca.* Anammoximicrobium, *Ca.* Scalindua.
**Status:** **Expanded in Phase 1.5m (Checkpoint 2 follow-up).** Added 3 entries from Brocadiaceae sister-species to maximise intra-family diversity.

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| Q1Q0T2 | Swiss-Prot | 809 | *Kuenenia stuttgartiensis* | Canonical type strain |
| A0A2Z6A915 | TrEMBL | fragment | uncultured *Ca.* Brocadia sp. | |
| G9ITI6 | TrEMBL | 636 | *Ca.* Brocadia anammoxidans | |
| G9ITI8 | TrEMBL | 810 | *Ca.* Jettenia asiatica | |
| A0A533QHC9 | TrEMBL | 810 | *Ca.* Jettenia ecosi | Phase 1.5m addition |
| A0A1V4ATP2 | TrEMBL | 821 | *Ca.* Brocadia carolinensis | Phase 1.5m addition |
| A0ABQ0K0A8 | TrEMBL | 809 | *Ca.* Brocadia sinica JPN1 | Phase 1.5m addition |

### Blind-set exclusion
*Candidatus Scalindua profunda* is in the blind set. No Scalindua hzsA reference is included.

### UniProt coverage gap (Anammoxoglobus / Anammoximicrobium)
Despite the user-requested expansion to *Anammoxoglobus* and *Anammoximicrobium* (Brocadiaceae sister-genera to Scalindua), **UniProt has zero hzsA entries from either genus** (search performed 2026-04-27). The expansion was therefore made within Brocadiaceae using sister-species of organisms already in the reference set: Brocadia carolinensis + B. sinica + Jettenia ecosi. This broadens intra-Brocadiaceae coverage but does not bridge the family-level gap to Scalinduaceae.

### Scalindua detection diagnosis (Phase 1.5m hit-pattern audit)
Reciprocal BLAST shows the references DO catch Scalindua-clade hzsA at 60-64% identity (Scalindua japonica A0A286U438 → reference set, top bs ~1074, 64% pident). The Phase 1.5m MISS_FN on Scalindua_profunda × hzsA is therefore **NOT a reference-coverage problem** — it is a proteome-completeness problem. The Scalindua profunda MAG used for blind validation does not contain hzsA in its predicted proteins (Scalindua japonica hzsA → Scalindua profunda proteome, 0 hits at e≤1e-5). A future fix would require either a more complete Scalindua profunda assembly or accepting this organism as un-detectable until the underlying genomic data improves.

---

## Marker: hdh

**Protein:** Hydrazine dehydrogenase. Catalyses N₂H₄ → N₂.
**Diagnoses:** Anammox confirmatory marker.
**Expected in:** Same as hzsA.
**Status:** **Expanded in Phase 1.5m (Checkpoint 2 follow-up).** Added 1 entry (longer Kuenenia hdh annotation).

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| Q1PW30 | Swiss-Prot | 582 | *Kuenenia stuttgartiensis* (canonical hdh) | |
| Q1PX48 | Swiss-Prot | 536 | *Kuenenia stuttgartiensis* (hao paralog, cross-reactive) | |
| A0A6G7GWX3 | TrEMBL | 642 | *Kuenenia stuttgartiensis* (longer hdh isoform) | Phase 1.5m addition |

### Constraint
hdh has very thin UniProt coverage outside Kuenenia and Scalindua (Scalindua excluded by rule). Brocadia/Jettenia hdh entries are not deposited in UniProt as of the Phase 1.5m audit. The 3-reference set is biologically defensible because (a) hdh is highly conserved within anammox bacteria, (b) the wider hzsA marker provides phylogenetic diversity, and (c) detection requires both hzsA AND hdh signals so single-genus hdh is robust as a confirmatory check.

### Scalindua detection diagnosis (Phase 1.5m hit-pattern audit)
Same finding as hzsA. References catch Scalindua-clade hdh at ~76% identity (Scalindua arabica A0A941W3I3 → reference set, bs ~947, 76.5% pident). The Scalindua profunda MAG simply lacks hdh in its predicted proteome (0 hits at e≤1e-5 from Scalindua arabica hdh probe). Same proteome-completeness limitation applies.

---

## Marker: tqoDoxD (Phase 3.2)

**Protein:** Thiosulfate:quinone oxidoreductase, large subunit (DoxD).
**Diagnoses:** Membrane-bound thiosulfate oxidation in Sulfolobales archaea (and homologous bacterial DoxXA in Acidithiobacillus). Distinct from bacterial soxB (which is absent from Sulfolobales).
**Expected in:** *Acidianus*, *Metallosphaera*, *Saccharolobus*, *Sulfodiicoccus*, *Sulfolobus*, *Sulfuracidifex*, *Sulfurisphaera* (broadly conserved across Sulfolobales sulfur oxidizers per Counts et al. 2021; Willard et al. 2024).
**Status:** **Added in Phase 3.2.** All references hand-verified against UniProt; test-set exclusion enforced.

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P97207 | Swiss-Prot | 184 | *Acidianus ambivalens* | Canonical reference (Müller et al. 2004 biochemical characterization) |
| Q97XJ3 | TrEMBL | 183 | *Saccharolobus solfataricus* P2 | doxD locus |
| Q96ZH9 | TrEMBL | 180 | *Sulfurisphaera tokodaii* (formerly *Sulfolobus tokodaii*) | locus STK_18550 |
| A4YDN8 | TrEMBL | 182 | *Metallosphaera sedula* | locus Msed_0363 |

### Cross-reactivity (Phase 3.2 BLAST scan)
- *Acidithiobacillus ferrooxidans*: 36.0% pident, 41% qcov, bs=70 — biologically expected (bacterial DoxXA homologs to archaeal TQO; Acidithiobacillus does oxidize thiosulfate). Below standard qcov≥70 threshold so does not fire as positive call.
- All other non-sulfur-oxidizing test organisms: <35% pident or <60% qcov; below threshold.

---

## Marker: tqoDoxA (Phase 3.2)

**Protein:** Thiosulfate:quinone oxidoreductase, small subunit (DoxA). Paired with DoxD in the doxDA operon.
**Diagnoses:** Same as tqoDoxD — confirmatory subunit. Hits on both DoxD AND DoxA raise capability confidence.
**Expected in:** Same Sulfolobales lineage as tqoDoxD.
**Status:** **Added in Phase 3.2.**

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P97224 | Swiss-Prot | 168 | *Acidianus ambivalens* | Paired with P97207 |
| Q97XJ4 | TrEMBL | 171 | *Saccharolobus solfataricus* P2 | locus SSO1741 |
| F9VNN5 | TrEMBL | 168 | *Sulfurisphaera tokodaii* | locus STK_18560 |
| A4YDN9 | TrEMBL | 166 | *Metallosphaera sedula* | locus Msed_0364 |

### Cross-reactivity
No non-sulfur-oxidizer hits clear standard thresholds (best non-target: Clostridium 26.5% pident, 8% qcov — both below threshold).

---

## Marker: tetH (Phase 3.2)

**Protein:** Tetrathionate hydrolase (extracellular, acidophilic). Catalyzes S₄O₆²⁻ + H₂O → S₂O₃²⁻ + SO₄²⁻ + S⁰.
**Diagnoses:** Tetrathionate utilization in acidophilic sulfur oxidizers. Functions optimally at very low pH (Protze et al. 2011 reported activity optimum pH 1).
**Expected in:** *Acidianus*, also bacterial *Acidithiobacillus* (which has its own TetH variant).
**Status:** **Added in Phase 3.2.** UniProt coverage outside *Acidianus* is sparse — reflects literature, not curation gap.

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| G8YXZ9 | Swiss-Prot | 535 | *Acidianus ambivalens* | tth1; Protze et al. 2011 biochemical reference |
| F4B6C8 | TrEMBL | 516 | *Acidianus hospitalis* W1 | locus Ahos_1670 |
| G8YY01 | TrEMBL | 449 | *Acidianus ambivalens* | tth2 paralog |

### Cross-reactivity (Phase 3.2 BLAST scan)
- ***Acidithiobacillus ferrooxidans*: 37.7% pident, 87% qcov, bs=250 — strongest cross-organism hit in the entire scan.** This WILL fire as a positive call at standard thresholds. Biologically expected: Acidithiobacillus has tetrathionate hydrolase activity. Already detected as sulfur oxidizer via bacterial soxB; the tetH hit is biologically consistent and adds corroborating evidence. Document as **biologically consistent cross-detection, not a false positive.**
- Other non-sulfur-oxidizer hits: all <30% pident with low qcov; below threshold.

### Coverage note
TetH is genus-restricted in our reference set (*Acidianus* dominant). UniProt coverage of TetH in *Metallosphaera* and *Sulfurisphaera* is currently absent or annotated under different protein names. The 3-reference *Acidianus*-dominant set is biologically defensible because TetH is well-conserved within Sulfolobales acidophilic sulfur oxidizers; if a future organism's TetH proves divergent, this entry can be expanded.

---

## Marker: sor (Phase 3.2)

**Protein:** Sulfur oxygenase reductase (cytoplasmic, soluble). Catalyzes S⁰ + O₂ + H₂O → SO₃²⁻ + S₂O₃²⁻ + H₂S.
**Diagnoses:** Cytoplasmic elemental-sulfur oxidation in lineage-restricted Sulfolobales (Acidianus, Metallosphaera, Sulfuracidifex, Sulfurisphaera tokodaii). ABSENT from Sulfolobus acidocaldarius and Saccharolobus solfataricus.
**Expected in:** *Acidianus ambivalens*, *A. brierleyi*, *A. tengchongensis*, *A. hospitalis*, *Sulfurisphaera tokodaii*, *Sulfuracidifex metallicus*, *Metallosphaera* (some species).
**Status:** **Added in Phase 3.2.** SOR Swiss-Prot reference is well-characterized (Kletzin 1989/1992).

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P29082 | Swiss-Prot | 309 | *Acidianus ambivalens* | Canonical Kletzin 1989/1992 reference |
| Q972K4 | TrEMBL | 311 | *Sulfurisphaera tokodaii* | locus STK_11270 |
| Q977W3 | TrEMBL | 308 | *Acidianus tengchongensis* | |
| A4ZIS7 | TrEMBL | 316 | *Sulfuracidifex metallicus* (formerly *Sulfolobus metallicus*) | |

### Excluded
- **P29086** (309-region transporter ORF), **P29087** (sor 5'-region ORF), **P29088** (77 aa fragment) — flanking-region ORFs from the Kletzin sequencing project that share UniProt accession-range neighborhood with the sor gene. NOT SOR proteins. Excluded as wrong-protein.

### Cross-reactivity (Phase 3.2 BLAST scan)
- *Rhodopseudomonas palustris*: 48.6% pident, 35% qcov, bs=34 — interesting (R. palustris encodes a peroxiredoxin-like SOR-family enzyme; 35% qcov is well below threshold so does not fire). No effect.
- All other non-sulfur-oxidizers: no hits at all (this is the most lineage-restricted marker).

### Sulfolobus acidocaldarius DSM 639 note
Per the empirical Phase 3.2 BLAST scan (best SOR hit on S. acidocaldarius: 22.4% pident, 32% qcov), S. acidocaldarius DSM 639 **lacks a detectable sor ortholog**. UniProt has no `sor`-named entry for this species. This is biologically consistent with Counts et al. 2021 / Willard et al. 2024 classifying S. acidocaldarius as a "limited" sulfur biooxidizer compared to other Sulfolobales. Phase 3.2 markers therefore do NOT detect S. acidocaldarius DSM 639 as a sulfur oxidizer; they are valid for the broader Sulfolobales lineage and will catch *Acidianus*, *Metallosphaera*, *Sulfurisphaera tokodaii*, *Sulfuracidifex* if those appear in future test sets.

---

## Marker: nxrA (Phase 3.3)

**Protein:** Nitrite oxidoreductase, alpha subunit. Membrane-bound molybdoenzyme catalyzing NO₂⁻ → NO₃⁻; the central energy-conserving reaction in canonical NOB.
**Diagnoses:** Aerobic nitrite oxidation by canonical Nitrospira / Nitrobacter / Nitrotoga / Nitrolancea / Nitrococcus lineages. Comammox organisms also have nxrA (paired with comammox-specific amoA — comammox vs canonical detection requires both markers, deferred to a future sub-phase).
**Expected in:** *Nitrospira* (Type A clade), *Nitrobacter* (Type B), *Nitrotoga* (Type A), *Nitrolancea* (Type B), *Nitrococcus*.
**Status:** **Added in Phase 3.3.** All 8 references hand-verified against UniProt; test-set exclusion enforced (no Nitrospira moscoviensis NSP M-1 proteins).

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| A0A0S4KRS1 | TrEMBL | 1145 | *Ca.* Nitrospira inopinata | Type A clade; comammox organism but its nxrA is canonical-style |
| A0A1W1I298 | TrEMBL | 1145 | *Nitrospira japonica* | Type A; locus NSJP_0817 |
| A0ABM8RCK9 | TrEMBL | 1147 | *Nitrospira defluvii* | Type A |
| Q3SQW5 | TrEMBL | 1214 | *Nitrobacter winogradskyi* Nb-255 | Type B; locus Nwi_2068 |
| Q71RT9 | TrEMBL | 1201 | *Nitrobacter alkalicus* | Type B |
| A0A916FC48 | TrEMBL | 1169 | *Ca.* Nitrotoga fabula | Type A |
| A0ABN8AJF8 | TrEMBL | 1169 | *Ca.* Nitrotoga arctica | Type A |
| A0A894Z0L1 | TrEMBL | 1221 | *Nitrolancea hollandica* | Type B; first non-Pseudomonadota / non-Nitrospirota NOB |

### Two-clade architecture

The 8 references split into two well-separated clades sharing only ~24% identity:
- **Type A** (cytoplasmic nxrAB): Nitrospira / Nitrotoga / Nitrococcus
- **Type B** (periplasmic nxrAB): Nitrobacter / Nitrolancea

Within-clade identity is 87-93% (intra-genus) or 35-37% (cross-genus, both Type A). Across clades, identity drops to <25% — the BLAST hits barely register without coverage filters. Detection works via OR-logic: each query genome BLASTs against all 8 refs and the best hit (any clade) determines the call.

### Wrong-protein traps (excluded)

- **Q3BJV5, Q3BJV6, Q3BJV7, Q3BJV8, Q3BJV9** — Nitrobacter winogradskyi nxrA fragments (85-100 aa). Only the full-length Q3SQW5 (1214 aa) and Q3SUK2 (1214 aa) used.

### Swiss-Prot status

UniProt has **no Swiss-Prot reviewed nxrA entry**. The reviewed entries for this protein family are filed under "Nitrate reductase (quinone)" — a name shared with narG (the reverse-direction enzyme). All references are necessarily TrEMBL, with verification by protein name + organism phenotype + literature cross-reference. This matches the established pattern from Phase 1.5m for diagnostic enzymes lacking Swiss-Prot reviewed entries (soxB, qmoA, hzsA precedent).

### Thresholds (Phase 3.3 calibrated)

| Field | Value | Rationale |
|---|---|---|
| min_pident | **75.0** | Empirical narG cross-reactivity ceiling = 48% pident. Within-clade NOB floor = 87%. Threshold sits in the 39-point gap. |
| min_qcov | 80 | Full-length hits expected; small truncation tolerance |
| min_evalue | 1e-30 | Standard CultureForge stringency |
| min_bitscore | 1500 | Length-aware safety margin |

### Cross-reactivity (Phase 3.3 BLAST scan against 26 test-set proteomes)

- **Nitrospira moscoviensis NSP M-1** (target): 96.1% pident, 100% qcov, 25 hits across 5 nxrA paralogs. ✓
- **narG-bearing organisms** (cross-reactivity, all below threshold):
  - Methanoperedens nitroreducens: 48.0% pident (ANME-2d narG-like nitrate reductase)
  - E. coli K-12 MG1655: 45.9% pident (narGHI nitrate reductase)
  - Scalindua profunda: 45.8% pident (anammox narG-related)
  - Lactobacillus plantarum: 44.1% pident (DMSO-reductase superfamily homolog)
- All 21 other test organisms: 0 hits at evalue ≤ 1e-30.

The 75% pident threshold cleanly separates true NOB (best hit 96%) from DMSO-reductase superfamily false positives (best hit 48%). Empirical narG cross-reactivity assessment: see `data/diagnostic_markers/nitrite_oxidation_review.md`.

### essential_marker rule

The `lithotrophic_aerobic_nitrite` capability uses `essential_marker = "nxrA"` to cap confidence at 0.40 when the marker is absent at the 75%/80% threshold. Without this rule, gapseq's pathway-integrity scoring fires the capability at ~0.52 on many denitrifiers (because the gapseq EC annotations overlap with denitrification narG) and on aerobes generally (terminal oxidase + ammonia assimilation are near-universal).

### Literature

- Spieck E, Lipski A. 2011. Cultivation, growth physiology, and chemotaxonomy of nitrite-oxidizing bacteria. *Methods Enzymol* 486:109-130.
- Daims H, Lücker S, Wagner M. 2016. A new perspective on microbes formerly known as nitrite-oxidizing bacteria. *Trends Microbiol* 24:699-712.
- Lücker S et al. 2010. A Nitrospira metagenome illuminates the physiology and evolution of globally important nitrite-oxidizing bacteria. *PNAS* 107:13479-13484.
- Sorokin DY et al. 2012. Nitrification expanded: discovery, physiology and genomics of a nitrite-oxidizing bacterium from the phylum Chloroflexi. *ISME J* 6:2245-2256. (Nitrolancea hollandica)

---

## Marker: nrfA (Phase 3.4)

**Protein:** Cytochrome c-552 / cytochrome c nitrite reductase, alpha subunit. Pentaheme c-type cytochrome (4 CXXCH + 1 CXXCK active-site Lys-coordinated heme — the CXXCK motif is the key diagnostic distinguishing NrfA from related multi-heme cytochromes c).
**Diagnoses:** Dissimilatory nitrate reduction to ammonium (DNRA) via canonical NrfA pathway. NO2- + 6 H+ + 6 e- → NH4+ + 2 H2O.
**Expected in:** Wolinella / Sulfurospirillum (Epsilonproteobacteria), Enterobacteriaceae (E. coli, Salmonella), Pasteurellaceae (Mannheimia), Shewanellaceae, Desulfovibrionaceae (sister to test-set Nitratidesulfovibrio), some Bacillota.
**Status:** **Added in Phase 3.4.** 6 references hand-verified; test-set exclusion enforced (no E. coli P0ABK9, no Nitratidesulfovibrio Q72EF3, no Campylobacter).

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| Q9S1E5 | Swiss-Prot | 507 | *Wolinella succinogenes* DSM 1740 | Canonical reference (Einsle et al. 2002 structural reference); annotation score 5/5 |
| Q9Z4P4 | Swiss-Prot | 514 | *Sulfurospirillum deleyianum* | Sister-Epsilon DNRA |
| Q8EAC7 | Swiss-Prot | 467 | *Shewanella oneidensis* MR-1 | Gammaproteobacteria DNRA |
| Q06PW6 | Swiss-Prot | 500 | *Mannheimia haemolytica* | Pasteurellaceae |
| B5QZA1 | Swiss-Prot | 478 | *Salmonella enteritidis* PT4 | Enterobacteriaceae |
| Q8VNU2 | TrEMBL | 514 | *Desulfovibrio desulfuricans* | Sister-genus to test-set Nitratidesulfovibrio (sister-species rule applies); the only TrEMBL ref in this set |

5 of 6 references are Swiss-Prot reviewed — substantially better than typical Phase 3 marker reference quality.

### Wrong-protein traps (excluded)

- **O33732** — Originally suggested as "Sulfurospirillum deleyianum nrfA" in the Phase 3.4 prompt, but UniProt confirms it is *Shewanella frigidimarina* nitrate reductase (938 aa, NOT nrfA). Replaced with the correctly identified Q9Z4P4.
- **V5Z1T4 (290 aa), Q6ZXS7 (167 aa)** — Fragmentary D. desulfuricans nrfA entries. Only the full-length Q8VNU2 (514 aa) used.

### Empirical cross-reactivity assessment + heme-motif analysis

Phase 3.4 BLAST scan against all 26 test-set proteomes followed by CXXCK active-site motif counting on each hit:

| Test genome | pident | qcov | CXXCH | CXXCK | Verdict |
|---|---|---|---|---|---|
| Scalindua profunda | **99.8%** | 100% | 4 | **1 (CWSCK)** | NrfA architecture **but biologically implausible** in Brocadiaceae MAG — **MAG contamination from Enterobacteriaceae**. Documented as E.1 addendum. |
| E. coli K-12 | **90.0%** | 100% | 4 | **1 (CWSCK)** | Real canonical NrfA (test-set excluded from refs). Recipe-time mode picker keeps aerobic_chemotrophic primary via facultative-anaerobe rule. |
| D. vulgaris | **68.8%** | 96% | 4 | **1 (CWNCK)** | Real canonical NrfA. Sub-mode classifier keeps sulfate reduction primary (higher confidence). |
| Syntrophomonas wolfei | **34.0%** | 89% | 4 | **1 (CFTCK)** | Real divergent NrfA — Bacillota DNRA. **Below 65% threshold; not detected.** Documented as a known gap. |
| Geobacter sulfurreducens | **32.9%** | 78% | 4 | **1 (CLTCK)** | Real divergent NrfA — Geobacter DNRA. **Below 65% threshold; not detected.** Same gap. |
| Campylobacter jejuni | **29.7%** | 83% | 5 | **0 (NONE)** | **NOT canonical NrfA** — different multi-heme cytochrome c architecture (5 hemes, no CXXCK Lys-axial active site). Likely Otr-family. Phase 3.4 nrfA-only scope correctly excludes it. |
| 20 other organisms | 0 hits | — | — | — | True negatives at evalue ≤ 1e-30. |

### Threshold rationale

NrfA is more sequence-divergent than NxrA (Phase 3.3): cross-class identity drops to ~32% (Delta vs Gamma vs Epsilon). **65% threshold sits in the gap** between canonical NrfA (68%+) and the borderline-divergent + non-NrfA cluster (≤34%). Canonical NrfA fully captured; divergent NrfA missed but documented.

Per-marker thresholds in `run_marker_blast.py`:

| Field | Value |
|---|---|
| min_pident | **65.0** |
| min_qcov | 80 |
| min_evalue | 1e-30 |
| min_bitscore (target) | 1500 |

### essential_marker rule

`anaerobic_respiratory_dnra` capability uses `essential_marker = "nrfA"` to cap confidence at 0.40 when the marker is absent. Without it, gapseq's pathway-integrity scoring fires on denitrifiers (which share the nitrate-reduction step at the EC level).

### diagnostic_marker_override

When nrfA hits clear the 65%/80% threshold, the override gives confidence 0.65 (Phase 1.5n pattern). Pathway-integrity score acts as additional support. See dnra_review.md for detailed empirical analysis.

### Literature

- Simon J. 2002. Enzymology and bioenergetics of respiratory nitrite ammonification. *FEMS Microbiol Rev* 26:285-309.
- Einsle O et al. 2002. Mechanism of the six-electron reduction of nitrite to ammonia by cytochrome c nitrite reductase. *JACS* 124:11737-11745.
- Welsh A et al. 2014. Refined NrfA phylogeny improves PCR-based nrfA gene detection. *Appl Environ Microbiol* 80:2110-2119.
- Kraft B et al. 2014. The environmental controls that govern the end product of bacterial nitrate respiration. *Science* 345:676-679.

---

## Marker: pmoA (Phase 3.5)

**Protein:** Particulate methane monooxygenase, α subunit (~247 aa). Membrane-bound, copper-dependent. Encoded in pmoCAB operon.
**Diagnoses:** Aerobic methanotrophy via the particulate methane monooxygenase. Most methanotrophs encode pMMO; some Type II also encode soluble MMO (mmoX) as alternative.
**Expected in:** Type I (Methylococcaceae — Methylococcus, Methylomonas, Methylocaldum), Type II (Methylocystaceae, Beijerinckiaceae — Methylosinus, Methylocystis, Methylocella), Type III (Verrucomicrobia — Methylacidiphilum).
**Status:** **Added in Phase 3.5.**

| Accession | Status | Length | Source organism | Type |
|---|---|---|---|---|
| Q607G3 | Swiss-Prot | 247 | *Methylococcus capsulatus* Bath | Type I |
| A4PDX7 | TrEMBL | 247 | *Methylocaldum* sp. T-025 | Type I (thermophile) |
| Q50541 | TrEMBL | 252 | *Methylosinus trichosporium* | Type II |
| O06122 | TrEMBL | 252 | *Methylocystis* sp. M | Type II |
| I0JZS9 | TrEMBL | 245 | *Methylacidiphilum fumariolicum* SolV | Type III (Verrucomicrobia) |
| A9QPD9 | TrEMBL | 249 | *Methylacidiphilum infernorum* V4 | Type III |

### Three-clade architecture

| Pair | pident | Notes |
|---|---|---|
| Type I × Type I (intra-Methylococcaceae) | 85% | tight |
| Type II × Type II (intra-Methylocystaceae) | 86% | tight |
| Type I × Type II | 58-60% | cross-clade |
| Type I/II × Type III | 36-55% | Verrucomicrobia highly divergent |

Dual-clade reference architecture: each lineage represented; OR-logic best-hit determines lineage. Within-clade hits typically 80%+; cross-clade stays below 60%.

### The pmoA × amoA paralogy and the 60% threshold

pmoA and amoA (ammonia monooxygenase α subunit) are evolutionary paralogs sharing the same fold and ~250 aa length. Empirical Phase 3.5 cross-reactivity scan:

| Test | pident | qcov | Notes |
|---|---|---|---|
| Methylococcus pmoA × Nitrosospira amoA (direct ref-vs-ref) | **50.0-50.2%** | 96% | Cross-reactivity ceiling |
| pmoA refs vs Nitrosomonas europaea proteome (test set) | 38-50% | 90-98% | All below threshold |
| pmoA cross-Type-I-II clade floor | **58-60%** | — | Within-family |

**8-10 point discrimination gap** between amoA cross-reactivity ceiling (50%) and pmoA cross-clade floor (58%). The 60% threshold sits cleanly in the gap.

### Thresholds

| Field | Value |
|---|---|
| min_pident | **60.0** |
| min_qcov | 80 |
| min_evalue | 1e-30 |

### Cross-reactivity (Phase 3.5 BLAST scan against 26 test proteomes)

- **Nitrosomonas europaea**: best hit 50.0% pident, 96% qcov (Methylococcus pmoA × Nitrosomonas amoA paralog) — below threshold ✓
- All 25 other test organisms: 0 hits at evalue ≤ 1e-30 — pmoA family is methanotroph-specific outside the amoA paralog

### Sentinel validation (Methylococcus capsulatus Bath, GCF_000008325.1)

The proteome of M. capsulatus Bath (NCBI RefSeq GCF_000008325.1, 2971 predicted proteins) was used as a one-off sentinel target — no test-set methanotroph exists. Loaded as genome_id=900 with explicit "SENTINEL" prefix in notes; excluded from V12 validation by design (the validation script uses a hardcoded ORGANISMS list with gids 7-32). Result: pmoA fires at 100.0% pident (Q607G3 is from this organism); aerobic_methanotrophy capability detected at 0.80 confidence; recipe correctly produces air+CH4 80:20 gas phase, phosphate buffer pH 7, NaNO3, SL-10 trace metals + Wolin's vitamins, no reducing agent; thermodynamic check ΔG = -820 kJ/mol feasible.

### Literature

- Hanson RS, Hanson TE. 1996. Methanotrophic bacteria. *Microbiol Rev* 60:439-471.
- Op den Camp HJ et al. 2009. Environmental, genomic and taxonomic perspectives on methanotrophic Verrucomicrobia. *Environ Microbiol Rep* 1:293-306.
- Tavormina PL et al. 2011. A novel family of functional operons encoding methane/ammonia monooxygenase-related proteins. *Environ Microbiol Rep* 3:91-100.
- Knief C. 2015. Diversity and habitat preferences of cultivated and uncultivated aerobic methanotrophic bacteria evaluated based on pmoA. *Front Microbiol* 6:1346.

---

## Marker: mmoX (Phase 3.5)

**Protein:** Soluble methane monooxygenase, hydroxylase α subunit (~526 aa). Cytoplasmic, iron-dependent. Encoded in mmoXYBZDC operon. Expressed under copper limitation in some Type II methanotrophs.
**Diagnoses:** Aerobic methanotrophy via the soluble methane monooxygenase. Subset of methanotrophs encode sMMO alongside pMMO; Type III Verrucomicrobia methanotrophs lack sMMO.
**Expected in:** Type I (Methylococcus, Methylomonas), Type II (Methylosinus, Methylocystis, Methylocella).
**Status:** **Added in Phase 3.5.**

| Accession | Status | Length | Source organism | Type |
|---|---|---|---|---|
| P22869 | Swiss-Prot | 527 | *Methylococcus capsulatus* Bath | Type I |
| P27353 | Swiss-Prot | 526 | *Methylosinus trichosporium* | Type II |
| Q3YA75 | TrEMBL | 526 | *Methylomonas* sp. GYJ3 | Type I |
| Q3T939 | TrEMBL | 526 | *Methylocella silvestris* | Type II Beijerinckiaceae |

### Single tight family

mmoX has high intra-family conservation across genera:

| Pair | pident |
|---|---|
| All cross-genus mmoX pairs (Methylococcus / Methylosinus / Methylomonas / Methylocella) | **82-99%** |

This is much tighter than pmoA's three-clade architecture, reflecting the slower evolution of the soluble enzyme.

### Thresholds

| Field | Value |
|---|---|
| min_pident | **50.0** |
| min_qcov | 70 |
| min_evalue | 1e-30 |

The 50% threshold is generous because the family is so conserved (intra-family 82%+) and zero cross-reactivity exists in the test set. Even a divergent novel methanotroph mmoX would clear 50% easily.

### Cross-reactivity (Phase 3.5 BLAST scan against 26 test proteomes)

**Zero hits at evalue ≤ 1e-30.** mmoX is highly methanotroph-specific. No related proteins in the 26 test organisms produce any detectable hit.

### Sentinel validation

M. capsulatus Bath proteome: mmoX fires at 100.0% pident (P22869 self-hit), bs=1107. All 4 mmoX references hit the same gene (WP_010960482.1) at 81-100% pident.

### Literature

Same as pmoA. mmoX biochemistry: Lipscomb JD. 1994. Mechanism of methane monooxygenase. *Annu Rev Microbiol* 48:371-399.

---

## Methodology note: `diagnostic_marker_override` symmetry (Phase 3.8)

The Phase 3.5 methanotrophy capability introduced `diagnostic_marker_override` as a marker-based firing path: when the canonical diagnostic marker (pmoA / mmoX) BLAST-hits at threshold, the capability fires with the override_confidence directly, bypassing the gapseq pathway-integrity score. This is the **right path for capabilities whose diagnostic marker is a single tightly-conserved enzyme that defines the metabolism**.

Phases 3.3 (NOB / nxrA), 3.4 (DNRA / nrfA), and 3.5 (methanotrophy / pmoA + mmoX) all added overrides at capability creation. Phase 3.8 extended this pattern retroactively to **methanogenesis** — the older capability that predated the override mechanism. The methanogenesis override is symmetric with the Phase 3.5+ pattern:

- **Marker:** mcrA (THE canonical methanogenesis diagnostic — methyl-coenzyme M reductase α subunit)
- **min_pident:** 50.0% (captures forward methanogens at 80%+ pident, ANME at 70%+ pident, with comfortable headroom against the empirical zero non-methanogen mcrA cross-reactivity in the test set)
- **min_qcov:** 70% (consistent with Phase 3.4 DNRA threshold for partial-genome MAGs)
- **override_confidence:** 0.65 (matches Phase 3.4 DNRA — mcrA presence alone is suggestive; full pathway integrity with Wolfe-cycle cofactor biosynthesis F420 + CoM + CoB provides higher confidence via the regular pathway-scoring path when gapseq data is loaded)

The override does not change behavior for genomes with gapseq pathway data loaded (regular pathway scoring already fires methanogenesis above threshold there). It enables marker-only sentinel validation: Methanosarcina acetivorans C2A (gid=903) was previously escalated/no-primary in Phase 3.7 because the marker-only sentinel pattern doesn't load gapseq data; post-override it classifies methanogenic primary at 0.65 confidence. ANME suppression continues to work via the Phase 3.6 priority ordering at recipe-time mode picking, not at the capability detection layer.

Other older capabilities that may benefit from retroactive override addition (deferred unless external testing surfaces a need): acetogenesis_wood_ljungdahl (acsB_cdhC + cooS_cdhA), oxygenic_phototrophy (psaA + psbA), bacteriorhodopsin (rhodopsin marker). None of these have surfaced a marker-only sentinel use case as of Phase 3.8.

---

## Curation methodology note: narG and divergent paralogs (Phase 3.6)

**Why narG is not curated as a diagnostic marker for ANME nitrate-coupled metabolism.**

Phase 3.6 introduced the `anme_reverse_methanogenesis` capability, which fires on `mcrA + (gapseq nitrate-reduction-pwy ≥100% complete OR dsrAB OR mtrC_omcB)`. The first OR-branch — the gapseq pathway-pattern entry — was chosen instead of curating narG references because the empirical curation reach is insufficient for Methanoperedens.

### Empirical observation

BLAST scan of Methanoperedens nitroreducens (gid=28) proteome against curated narG-family references:

| evalue cutoff | best hit | pident |
|---|---|---|
| 1e-30 | **none** | — |
| 1e-10 | none | — |
| 1.0 | weak hit | **24.5%** at evalue 100 |

In other words, Methanoperedens's napAB-like nitrate reductase is so divergent that no canonical narG reference reaches it at any biologically meaningful threshold. This is because Methanoperedens uses an archaeal narGH-related but distinct enzyme architecture — different metal cofactor coordination, different catalytic core — and ANME-2d is the only well-studied representative.

### What this means for curation

To detect Methanoperedens nitrate reduction via curated references, the reference set would need to include the Methanoperedens napA/narG itself or a close ANME-2d homolog. This would require:

1. Sequencing or sourcing a verified Methanoperedens narG/napA accession (currently TrEMBL-only, no Swiss-Prot).
2. Validating that the chosen reference does not cross-react against canonical denitrifier narG (the principal contaminant of nitrate-reductase BLAST searches; see `nitrite_oxidation_review.md` for the same problem in Phase 3.3).
3. Independently verifying the threshold against forward methanogens that incidentally have nitrogen-cycle related enzymes (Methanocaldococcus has none — the test case is clean — but novel test organisms would re-open the question).

This is curation work that is justifiable for canonical narG (denitrifier-side, future Phase 3.7+ work), but not for Methanoperedens-only detection where the genus has only one cultivated/sequenced representative.

### Why pathway-pattern is the correct fallback here

The gapseq UniRef-based annotation already catches Methanoperedens's nitrate reduction at full pathway completeness (4 dissimilatory nitrate-reduction pathways at 100% completeness, all `predicted=true`). gapseq's UniRef reach is broader than any curated single-marker reference set because it operates against the full UniRef cluster space. For divergent paralogs, this is exactly the right tool.

The new `essential_marker_OR` pathway-pattern entry (`{"type": "pathway_pattern", "pattern": "dissimilatory nitrate reduction", "min_completeness": 100, "require_predicted": true}`) lets the capability use this signal **without diluting the marker curation discipline** — the entry is explicitly a fallback, documented in this section and in CLAUDE.md, and it requires gapseq's strictest call (100% completeness AND predicted=true) to fire.

### Discipline boundary

Pathway-pattern entries should be used only when:

1. The target organism's relevant paralog is too divergent to reach with curated references at biologically meaningful thresholds (verified empirically — Methanoperedens narG case).
2. gapseq's pathway annotation provides a more sensitive signal (verified empirically — 100% completeness on Methanoperedens vs zero curated narG hits).
3. The threshold (`min_completeness`, `require_predicted`) is justified by cross-organism specificity scan against the test set (verified empirically — only Methanoperedens fires the (mcrA + nitrate pathway) signature; Methanocaldococcus has zero nitrate-reduction pathways).

Pathway-pattern is **not** a convenience replacement for marker curation. The default discipline remains: curate references, set thresholds against empirical cross-reactivity, document in this file. Pathway-pattern is the exception path for divergent paralogs that escape curation reach.

### Future work

If denitrifier-side narG becomes a needed marker (e.g., for distinguishing canonical denitrification from DNRA in Phase 3.7 contexts), curate it as a normal marker entry against `data/diagnostic_markers/narG_refs.fasta` with explicit thresholds and cross-reactivity scan against the test set. The Methanoperedens-divergent narG would still need pathway-pattern fallback.

---
