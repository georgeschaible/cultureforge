# Master List of Microbial Energy-Conserving Metabolisms

**Purpose:** Phase 3.3a coverage audit. Comprehensive enumeration of energy-conserving metabolisms in microbial physiology, used as the reference list against which CultureForge's current capability coverage is mapped.

**Scope:** Energy metabolism only. Nitrogen fixation, secondary metabolism, biosynthetic pathways, taxonomy-specific quirks are out of scope per the audit prompt.

**Reference sources:**
- Madigan MT, Bender KS, Buckley DH, Sattley WM, Stahl DA. *Brock Biology of Microorganisms* (15th ed., 2018). Chapters 13–15 (microbial metabolism + diversity).
- Konhauser KO. *Introduction to Geomicrobiology* (Wiley-Blackwell, 2007).
- KEGG pathway maps under "Energy metabolism" (00190, 00910, 00920, 00680, 00710, 00720, 00633) and "Carbon fixation" (00710, 00720, 00630).
- Falkowski PG, Fenchel T, Delong EF. 2008. The microbial engines that drive Earth's biogeochemical cycles. *Science* 320:1034.
- Ghosh W, Dam B. 2009. Biochemistry and molecular biology of lithotrophic sulfur oxidation by taxonomically and ecologically diverse bacteria and archaea. *FEMS Microbiol Rev* 33:999.
- Hügler M, Sievert SM. 2011. Beyond the Calvin cycle: autotrophic carbon fixation in the ocean. *Annu Rev Mar Sci* 3:261.
- Kuypers MMM, Marchant HK, Kartal B. 2018. The microbial nitrogen-cycling network. *Nat Rev Microbiol* 16:263.
- Knittel K, Boetius A. 2009. Anaerobic oxidation of methane: progress with an unknown process. *Annu Rev Microbiol* 63:311.
- Hedrich S, Schlömann M, Johnson DB. 2011. The iron-oxidizing proteobacteria. *Microbiology* 157:1551.
- Bryce C et al. 2018. Microbial anaerobic Fe(II) oxidation — Ecology, mechanisms and environmental implications. *Environ Microbiol* 20:3462.

**Status legend** (per-entry annotations show CultureForge's current handling):
- **COVERED** — capability exists in pathway_definitions.json with diagnostic markers verified
- **PARTIAL** — capability exists but lineage/architecture coverage incomplete
- **GAP** — no capability or no diagnostic markers

---

## A. Aerobic respiration variants

### A1. Aerobic chemoorganotrophy [COVERED]

- **Description:** Heterotrophic respiration of organic substrates with O₂ as terminal electron acceptor via cytochrome oxidases.
- **Donor / acceptor / carbon:** organic carbon / O₂ / heterotrophic
- **Diagnostic enzymes:** Cytochrome c oxidase (cox), bd-type oxidase (cydAB), bo3 oxidase (cyo), cbb3 oxidase (ccoNOPQ), TCA cycle enzymes
- **Phylogenetic distribution:** Bacteria + Archaea, near-universal in aerobic lineages
- **Cultivation relevance:** Most cultured organisms; vast majority of culture-collection isolates
- **Frequency in submissions:** HIGH
- **Examples:** *E. coli*, *Bacillus*, *Pseudomonas*, *Staphylococcus*, most aerobic isolates
- **KEGG:** ko00190 Oxidative phosphorylation
- **CF status:** `aerobic_respiration` capability + `terminal_oxidases` marker (composite). Detected on 16/26 test organisms.

### A2. Aerobic ammonia oxidation (AOB and AOA) [PARTIAL]

- **Description:** Energy from NH₃ → NO₂⁻ via ammonia monooxygenase + hydroxylamine oxidoreductase. Bacteria (AOB, e.g. Nitrosomonas, Nitrosospira) and Thaumarchaeota (AOA, e.g. Nitrosopumilus).
- **Donor / acceptor / carbon:** NH₃ (or NH₄⁺) / O₂ / autotrophic (Calvin or 3HP/4HB)
- **Diagnostic enzymes:** amoCAB, hao (AOB); amoCAB (AOA, divergent)
- **Phylogenetic distribution:** β-/γ-Proteobacteria (AOB); Thaumarchaeota (AOA); Comammox in Nitrospirota
- **Cultivation relevance:** Cultured but slow growers; standard NOB media (DSMZ 2399)
- **Frequency in submissions:** MEDIUM-HIGH (relevant in environmental microbiology, soil/aquatic samples)
- **Examples:** *Nitrosomonas europaea*, *Nitrosospira multiformis*, *Nitrosopumilus maritimus*
- **KEGG:** ko00910 Nitrogen metabolism
- **CF status:** `ammonia_oxidation` capability with amoA + hao markers. AOB covered. AOA divergence may produce false negatives. Comammox amoA → see A3.

### A3. Aerobic nitrite oxidation (canonical NOB) [GAP] **← high-priority gap**

- **Description:** Energy from NO₂⁻ → NO₃⁻ via nitrite oxidoreductase (NXR). Largest known sink for nitrite in the global N cycle.
- **Donor / acceptor / carbon:** NO₂⁻ / O₂ / autotrophic (rTCA in Nitrospira; Calvin in Nitrobacter)
- **Diagnostic enzymes:** **nxrA** (alpha subunit, periplasmic-facing in Nitrospira / cytoplasmic-facing in Nitrobacter), nxrB (beta), nxrC
- **Phylogenetic distribution:** Nitrospirota (Nitrospira), Pseudomonadota (Nitrobacter, Nitrococcus), Chloroflexota (Nitrolancea), Nitrotogales (Nitrotoga)
- **Cultivation relevance:** Cultured but slow; standard NOB media (DSMZ 2399, K-medium)
- **Frequency in submissions:** MEDIUM-HIGH (any soil / aquatic / wastewater sample, common environmental microbiology submissions)
- **Examples:** *Nitrospira moscoviensis* NSP M-1 (in test set, currently misclassified), *Nitrobacter winogradskyi*, *Nitrolancea hollandica*
- **KEGG:** ko00910
- **CF status:** **NO capability defined.** Nitrospira moscoviensis (test set, gid 23) has 5 nxrA paralogs at 94–96% pident, but CultureForge has no `nitrite_oxidation` capability and no nxrA marker. Falls through to spurious acetogenesis classification (V12 score 20%). **This is the canonical Phase 3.3 fix.**

### A4. Comammox (complete ammonia oxidation in single organism) [GAP]

- **Description:** Single-organism complete nitrification: NH₃ → NO₃⁻. Discovered 2015. Comammox Nitrospira encode both amoCAB AND nxrAB.
- **Donor / acceptor / carbon:** NH₃ / O₂ / autotrophic
- **Diagnostic enzymes:** amoCAB (Clade A or Clade B comammox lineage, sequence-divergent from AOB amoA) + nxrAB
- **Phylogenetic distribution:** Specific Nitrospirota lineages only
- **Cultivation relevance:** Few isolates; Ca. Nitrospira inopinata is the type
- **Frequency in submissions:** MEDIUM (specialty environmental microbiology)
- **Examples:** *Ca.* Nitrospira inopinata, *Ca.* N. nitrosa, *Ca.* N. nitrificans
- **KEGG:** ko00910
- **CF status:** Documented as LIMITATIONS A.2. Existing amoA reference set has comammox fragments (138 aa, 65 aa) too short to clear qcov ≥ 60 threshold. Need full-length comammox amoA references. **Note:** No comammox organism in current 26-organism test set (verified Phase 3.3 verification — N. moscoviensis NSP M-1 is canonical NOB, not comammox).

### A5. Aerobic sulfur oxidation, bacterial SOX [COVERED]

- **Description:** Periplasmic SoxABXYZ multienzyme complex. Common in α-/β-/γ-proteobacteria and Epsilonproteobacteria.
- **Donor / acceptor / carbon:** S²⁻ / S⁰ / S₂O₃²⁻ / O₂ (or NO₃⁻) / autotrophic (Calvin) or mixotrophic
- **Diagnostic enzymes:** soxB (thiosulfohydrolase), soxA, soxX, soxY, soxZ
- **Phylogenetic distribution:** Many proteobacteria, Sulfurimonas, Allochromatium (purple sulfur), Thiobacillus, Paracoccus
- **Cultivation relevance:** Routine cultivation; many DSMZ media
- **Frequency in submissions:** MEDIUM
- **Examples:** *Acidithiobacillus ferrooxidans*, *Allochromatium vinosum*, *Sulfurimonas denitrificans*, *Paracoccus denitrificans*
- **KEGG:** ko00920
- **CF status:** `sulfur_oxidation` capability + soxB marker. Detected on 4 test organisms.

### A6. Aerobic sulfur oxidation, archaeal Sulfolobales [COVERED — Phase 3.2]

- **Description:** Different enzyme family than bacterial SOX. Uses TQO (DoxD+DoxA), TetH, SOR.
- **Donor / acceptor / carbon:** S⁰ / S²⁻ / S₂O₃²⁻ / S₄O₆²⁻ / O₂ / autotrophic (3HP/4HB cycle)
- **Diagnostic enzymes:** tqoDoxD, tqoDoxA, tetH, sor
- **Phylogenetic distribution:** Sulfolobales (Acidianus, Metallosphaera, Saccharolobus, Sulfodiicoccus, Sulfolobus, Sulfuracidifex, Sulfurisphaera)
- **Cultivation relevance:** Specialty thermoacidophile cultivation
- **Frequency in submissions:** LOW-MEDIUM
- **Examples:** *Acidianus ambivalens*, *Metallosphaera sedula*, *Sulfurisphaera tokodaii*
- **KEGG:** ko00920
- **CF status:** Added Phase 3.2 (Apr 2026). 4 markers, 15 verified accessions. Sulfolobus acidocaldarius DSM 639 in test set genuinely lacks these (true negative documented in REFERENCE_CURATION.md).

### A7. Acidophilic Fe(II) oxidation [COVERED]

- **Description:** Aerobic Fe²⁺ → Fe³⁺ at low pH (1–4). Outer-membrane cytochrome cyc2 transfers electrons across membrane.
- **Donor / acceptor / carbon:** Fe²⁺ / O₂ / autotrophic
- **Diagnostic enzymes:** cyc2 (outer-membrane cytochrome c), rusticyanin
- **Phylogenetic distribution:** Acidithiobacillus, Leptospirillum, Acidihalobacter, Mariprofundus
- **Cultivation relevance:** 9K medium (DSMZ 70)
- **Frequency in submissions:** LOW-MEDIUM
- **Examples:** *Acidithiobacillus ferrooxidans*, *Leptospirillum ferrooxidans*
- **KEGG:** No specific map (specialty pathway)
- **CF status:** `iron_ii_oxidation` capability + cyc2 marker (Phase 1.5l/m rebuild). Detected on 3 test organisms.

### A8. Neutrophilic / microaerophilic Fe(II) oxidation [GAP]

- **Description:** Fe²⁺ oxidation at near-neutral pH, often microaerobic. Different enzymes than acidophilic route.
- **Donor / acceptor / carbon:** Fe²⁺ / O₂ (microaerobic) / autotrophic
- **Diagnostic enzymes:** mtoA, mtoB (reverse-orientation MtrAB-family); Cyc2-PV-1 type cytochromes (distinct subclass from acidophilic Cyc2)
- **Phylogenetic distribution:** Gallionella, Mariprofundus, Sideroxydans, Ferriphaselus
- **Cultivation relevance:** Difficult — requires gradient cultivation; specialty media (DSMZ 803)
- **Frequency in submissions:** LOW (specialist environmental microbiology, freshwater sediments / iron seeps)
- **Examples:** *Gallionella ferruginea*, *Mariprofundus ferrooxydans* PV-1, *Sideroxydans lithotrophicus*
- **KEGG:** No specific map
- **CF status:** Documented as LIMITATIONS A.4. No mtoA/mtoB references; cyc2 reference set covers acidophilic only.

### A9. Microaerophilic chemolithotrophy (Helicobacter / Campylobacter / Sulfurimonas style) [PARTIAL]

- **Description:** Combines low-O₂ tolerance with chemolithoautotrophy or microaerobic heterotrophy. Often uses cbb3-type oxidase (high O₂ affinity).
- **Donor / acceptor / carbon:** organic / S²⁻ / O₂ at low partial pressure / mixed
- **Diagnostic enzymes:** cbb3 oxidase (ccoNOPQ); often paired with sulfur or hydrogen oxidation
- **Phylogenetic distribution:** Epsilonproteobacteria (Campylobacter, Helicobacter, Sulfurimonas), some Magnetospirillum
- **Frequency in submissions:** MEDIUM (any gut, oral, sediment-interface sample)
- **Examples:** *Campylobacter jejuni*, *Sulfurimonas denitrificans*, *Helicobacter pylori*
- **KEGG:** ko00190 (cbb3 branch)
- **CF status:** Inferred from composite signal in `derive_recipe_context._derive_atmosphere`: when lithotrophic_aerobic + anaerobic_respiratory both fire, atmosphere recommended is microaerobic. Works for Sulfurimonas. Standalone microaerophiles without sulfur oxidation (e.g., Campylobacter) require terminal-oxidase profile interpretation; currently OK for the test-set Campylobacter but no unified capability.

### A10. Aerobic methanotrophy [GAP]

- **Description:** Aerobic oxidation of CH₄ → CO₂ via particulate or soluble methane monooxygenase.
- **Donor / acceptor / carbon:** CH₄ / O₂ / autotrophic via formaldehyde or partial heterotrophic
- **Diagnostic enzymes:** **pmoA** (particulate methane monooxygenase, alpha subunit), **mmoX** (soluble methane monooxygenase, alpha subunit). pmoA is homologous to amoA — care needed in marker design.
- **Phylogenetic distribution:** Type I (γ-proteobacteria, Methylococcaceae), Type II (α-proteobacteria, Methylocystaceae), Verrucomicrobia, NC10 (Methylomirabilis)
- **Cultivation relevance:** Many cultured isolates; specialty media (DSMZ 921, NMS medium)
- **Frequency in submissions:** MEDIUM (relevant for environmental microbiology, peatlands, freshwater sediments, methane-cycle studies)
- **Examples:** *Methylococcus capsulatus* Bath, *Methylocystis*, *Methylosinus trichosporium* OB3b
- **KEGG:** ko00680 Methane metabolism
- **CF status:** No capability or markers. pmoA is sequence-related to amoA — cross-reactivity check needed when added.

### A11. CO oxidation (aerobic carboxydotrophy) [GAP]

- **Description:** Aerobic oxidation of CO → CO₂ via Mo/Cu-dependent CO dehydrogenase. Different enzyme from anaerobic Ni-CODH (acetogen / ANME branch).
- **Donor / acceptor / carbon:** CO / O₂ / autotrophic via Calvin or partial heterotrophic
- **Diagnostic enzymes:** **coxL** (large subunit, Mo-CODH; distinct from Ni-CODH cooS)
- **Phylogenetic distribution:** Mycobacteriaceae, Bradyrhizobiaceae, Burkholderiales, scattered
- **Frequency in submissions:** LOW
- **Examples:** *Oligotropha carboxidovorans*, *Mycobacterium smegmatis*
- **KEGG:** ko00680
- **CF status:** Anaerobic CO oxidation (cooS_cdhA, Ni-CODH) is partially covered as part of acetogenesis Wood-Ljungdahl branch. Aerobic Mo-CODH (coxL) is GAP.

### A12. Aerobic H₂ oxidation (knallgas) [PARTIAL]

- **Description:** H₂ + ½ O₂ → H₂O. Often coupled with autotrophic CO₂ fixation (knallgas reaction).
- **Donor / acceptor / carbon:** H₂ / O₂ / autotrophic (Calvin) or mixotrophic
- **Diagnostic enzymes:** [NiFe]-uptake hydrogenase (Group 1), often paired with Calvin enzymes (rbcL)
- **Phylogenetic distribution:** Cupriavidus (formerly Ralstonia), Aquifex, Hydrogenophaga
- **Frequency in submissions:** LOW-MEDIUM
- **Examples:** *Cupriavidus necator* H16, *Aquifex aeolicus*
- **KEGG:** ko00190 / ko00710
- **CF status:** Hydrogenases detected via `genome_hydrogenases` table (Phase 1.5j). [NiFe] Group 1 uptake hydrogenase identification informs gas-phase recommendation. No standalone "knallgas autotrophy" capability — likely fires under aerobic_chemotrophic + autotrophy markers but cultivation mode not distinguished.

---

## B. Anaerobic respiration variants

### B1. Denitrification (NO₃⁻ → N₂) [COVERED]

- **Description:** Stepwise reduction NO₃⁻ → NO₂⁻ → NO → N₂O → N₂. Most common anaerobic N-cycle metabolism.
- **Donor / acceptor / carbon:** organic or H₂ / NO₃⁻ / heterotrophic typically
- **Diagnostic enzymes:** narG/napA, nirS/nirK, norBC, **nosZ** (terminal — Clade I canonical, Clade II atypical)
- **Phylogenetic distribution:** widespread in Pseudomonadota, Bacteroidota; many environmental
- **Cultivation relevance:** Common
- **Frequency in submissions:** HIGH
- **Examples:** *Paracoccus denitrificans*, *Pseudomonas aeruginosa*, *Sulfurimonas denitrificans*, *Magnetospirillum*
- **KEGG:** ko00910
- **CF status:** `denitrification` capability + nosZ essential marker (Clade I only). LIMITATIONS E.4 documents Clade II nosZ gap.

### B2. DNRA (dissimilatory nitrate reduction to ammonium) [GAP] **← potential high-priority gap**

- **Description:** NO₃⁻ → NO₂⁻ → NH₄⁺. Competing fate vs denitrification; conserves N rather than losing as gas. Common in C-rich anaerobic sediments / animal guts.
- **Donor / acceptor / carbon:** organic / NO₃⁻ / heterotrophic
- **Diagnostic enzymes:** napA/narG (initial step), **nrfA** (cytochrome c nitrite reductase, terminal NH₄⁺-producing step) or nirBD (cytoplasmic nitrite reductase)
- **Phylogenetic distribution:** Many γ-proteobacteria, Epsilonproteobacteria, Bacteroidota; sediment + gut microbiome
- **Cultivation relevance:** Cultured (Wolinella, E. coli mixed-acid pathways)
- **Frequency in submissions:** MEDIUM-HIGH
- **Examples:** *Wolinella succinogenes*, *Sulfurospirillum*, *Geobacter lovleyi*, some *E. coli* strains
- **KEGG:** ko00910
- **CF status:** No capability. nrfA / nirB markers absent. Currently DNRA organisms would fall under aerobic_chemotrophic / fermentative classification (wrong primary mode for an anaerobic respirer).

### B3. Sulfate reduction (canonical) [COVERED]

- **Description:** SO₄²⁻ → S²⁻ via APS, sulfite, dsrAB. Energy conservation by membrane Qmo + Dsr complexes.
- **Donor / acceptor / carbon:** organic (lactate, acetate, H₂) / SO₄²⁻ / heterotrophic typically
- **Diagnostic enzymes:** **dsrAB** (dissimilatory sulfite reductase), **aprAB** (APS reductase), **qmoA** (Qmo membrane complex)
- **Phylogenetic distribution:** Desulfovibrionales, Desulfobacterales, Desulfobulbales, Archaeoglobales
- **Cultivation relevance:** Standard Postgate medium (DSMZ 63)
- **Frequency in submissions:** MEDIUM
- **Examples:** *Desulfovibrio vulgaris*, *Archaeoglobus fulgidus*, *Desulfobacter*
- **KEGG:** ko00920
- **CF status:** `dissimilatory_sulfate_reduction` capability with dsrAB AND qmoA essential markers (Phase 1.5k qmoA fix prevents reverse-dsr false positives). Detected on D. vulgaris.

### B4. Sulfite-only respiration / sulfite reduction without sulfate-uptake [PARTIAL]

- **Description:** Some organisms reduce SO₃²⁻ but not SO₄²⁻ (lack APS-reduction step or sulfate transporters).
- **Diagnostic enzymes:** dsrAB present, aprAB+qmoA absent
- **Phylogenetic distribution:** Some Desulfitobacterium, some clostridial lineages
- **Frequency in submissions:** LOW
- **CF status:** Currently capped at 0.40 confidence by qmoA-essential rule. Pattern detectable but routed away from sulfate_reduction primary classification.

### B5. Sulfur disproportionation [GAP]

- **Description:** Energy from disproportionation: S₂O₃²⁻ + H₂O → SO₄²⁻ + H₂S, or 4 S⁰ + 4 H₂O → SO₄²⁻ + 3 H₂S + 2 H⁺. Short-circuits sulfur cycle.
- **Donor / acceptor / carbon:** S₂O₃²⁻ or S⁰ (both donor and acceptor) / heterotrophic or autotrophic
- **Diagnostic enzymes:** Same dsrAB/aprAB as sulfate reduction. Distinguishing factor is lack of external donor + presence of intermediate sulfur substrates.
- **Phylogenetic distribution:** Desulfocapsa, some Desulfobulbus, Desulfurivibrio
- **Frequency in submissions:** LOW
- **Examples:** *Desulfocapsa sulfexigens*, *Desulfurivibrio alkaliphilus*
- **CF status:** Indistinguishable from sulfate reduction at marker level; would be flagged similarly. No dedicated capability.

### B6. Iron(III) reduction (extracellular EET, Geobacter / Shewanella style) [COVERED]

- **Description:** Reduction of insoluble Fe(III) oxides via outer-membrane multi-heme cytochromes; extracellular electron transfer.
- **Donor / acceptor / carbon:** organic acids or H₂ / Fe(III) (insoluble) / heterotrophic
- **Diagnostic enzymes:** **mtrC / omcB** (outer-membrane cytochromes); pili/nanowires
- **Phylogenetic distribution:** Geobacteraceae, Shewanellaceae primarily; Geothrix and Thermincola use different mechanisms
- **Frequency in submissions:** MEDIUM (subsurface microbiology, bioremediation samples)
- **Examples:** *Geobacter sulfurreducens*, *Shewanella oneidensis* MR-1
- **KEGG:** No standard map
- **CF status:** `iron_iii_reduction` capability + mtrC_omcB marker. Phase 1.5m expanded to Shewanella. LIMITATIONS D.2 notes non-Geobacter/Shewanella iron reducers (Geothrix, Thermincola, archaeal iron reducers) not covered.

### B7. Manganese(IV) reduction [GAP]

- **Description:** Mn(IV) → Mn(II) via similar EET architecture as Fe(III) reduction. Coupled to organic substrate oxidation.
- **Donor / acceptor / carbon:** organic / Mn(IV) / heterotrophic
- **Diagnostic enzymes:** Often shared with iron-reduction machinery (mtrC/omcB family); some specific outer-membrane reductases
- **Phylogenetic distribution:** Shewanella, Geobacter, some Desulfuromonas
- **Frequency in submissions:** LOW-MEDIUM (marine / freshwater sediment microbiology)
- **Examples:** *Shewanella oneidensis*, *Desulfuromonas acetoxidans*
- **KEGG:** No standard map
- **CF status:** GAP — no dedicated capability. Likely silent in CultureForge: a Shewanella-type genome would be captured under iron_iii_reduction via mtrC, but the metabolism would not be flagged as Mn-specific.

### B8. Selenate / selenite respiration [GAP, low-priority]

- **Description:** SeO₄²⁻ → SeO₃²⁻ → Se⁰ via specific selenate reductase.
- **Donor / acceptor / carbon:** organic / SeO₄²⁻ / heterotrophic
- **Diagnostic enzymes:** **serA** (or srdA) — selenate reductase
- **Phylogenetic distribution:** Bacillus selenitireducens, Sulfurospirillum, scattered
- **Frequency in submissions:** LOW
- **Examples:** *Bacillus selenitireducens*, *Sulfurospirillum barnesii*
- **CF status:** GAP. Specialized; deferred.

### B9. Arsenate respiration [GAP, low-priority]

- **Description:** AsO₄³⁻ → AsO₃³⁻ via arsenate reductase. Detoxification + energy conservation.
- **Diagnostic enzymes:** **arrA** (anaerobic arsenate reductase, large subunit)
- **Phylogenetic distribution:** Halobacteriales, Desulfotomaculum, Wolinella, scattered
- **Frequency in submissions:** LOW
- **Examples:** *Sulfurospirillum arsenophilum*, *Bacillus arseniciselenatis*
- **CF status:** GAP.

### B10. Chlorate / perchlorate respiration [GAP]

- **Description:** ClO₃⁻ / ClO₄⁻ → Cl⁻ via perchlorate reductase. Industrial / contamination relevance.
- **Diagnostic enzymes:** **pcrA** (perchlorate reductase) / **clrA** (chlorate reductase)
- **Phylogenetic distribution:** Dechloromonas, Azospira (formerly Dechlorosoma), scattered
- **Frequency in submissions:** LOW (specialty bioremediation contexts)
- **Examples:** *Dechloromonas aromatica*, *Azospira oryzae*
- **CF status:** GAP. Different acceptor than nitrate/sulfate; recipe needs ClO₃⁻/ClO₄⁻ as acceptor.

### B11. Organohalide respiration [COVERED]

- **Description:** Halogenated organic acceptors (PCE, TCE, vinyl chloride, chlorobenzene). Reductive dehalogenase couples to membrane respiration.
- **Donor / acceptor / carbon:** H₂ or formate / chlorinated organic / requires acetate + B12 supplements
- **Diagnostic enzymes:** **rdhA** (reductive dehalogenase, broad family)
- **Phylogenetic distribution:** Dehalococcoides, Dehalobacter, Desulfitobacterium, Sulfurospirillum
- **Cultivation relevance:** Specialty (DSMZ 1411 / 720)
- **Frequency in submissions:** LOW-MEDIUM (bioremediation / chlorinated-solvent sites)
- **Examples:** *Dehalococcoides mccartyi*, *Dehalobacter restrictus*
- **KEGG:** No standard map
- **CF status:** `organohalide_respiration` capability + rdhA marker + Phase 1.5n diagnostic_marker_override. LIMITATIONS A.1/D.1: substrate-class (PCE vs TCE vs DCE vs VC) ambiguity within the rdhA family.

### B12. Methanogenesis, hydrogenotrophic [COVERED]

- **Description:** 4 H₂ + CO₂ → CH₄ + 2 H₂O via Wolfe cycle. Requires unique cofactors (F420, coenzyme M, coenzyme B, methanofuran).
- **Donor / acceptor / carbon:** H₂ / CO₂ / autotrophic (CO₂ as carbon AND acceptor)
- **Diagnostic enzymes:** **mcrA** (methyl-coenzyme M reductase α), mcrBG (β/γ); + Wolfe-cycle enzymes (ftr, mch, mer, hmd)
- **Phylogenetic distribution:** Methanobacteriales, Methanococcales, Methanopyrales, Methanomicrobiales (most common archaeal methanogen lineage)
- **Cultivation relevance:** Specialty anaerobic; H₂/CO₂ headspace, strict anoxic
- **Frequency in submissions:** MEDIUM (gut / sediment / wetland samples)
- **Examples:** *Methanocaldococcus jannaschii*, *Methanothermobacter*, *Methanococcus*
- **KEGG:** ko00680
- **CF status:** `methanogenesis` capability + mcrA marker.

### B13. Methanogenesis, aceticlastic [PARTIAL]

- **Description:** CH₃COO⁻ → CH₄ + CO₂. Major source of biogenic methane in freshwater sediments.
- **Donor / acceptor / carbon:** acetate / acetate-derived methyl / heterotrophic
- **Diagnostic enzymes:** mcrA (same family) + acetate kinase / phosphotransacetylase / Cdh-pathway. Distinguishing feature: presence of acs/cdh complex used in reverse for acetate cleavage.
- **Phylogenetic distribution:** Methanosarcinales (Methanosarcina, Methanosaeta/Methanothrix)
- **Frequency in submissions:** MEDIUM
- **Examples:** *Methanosarcina barkeri*, *Methanothrix soehngenii*
- **CF status:** Falls under `methanogenesis` capability via mcrA. Substrate variant not distinguished (recipes assume hydrogenotrophic gas phase). For aceticlastic-only methanogens, recipe should be acetate as substrate, no H₂/CO₂.

### B14. Methanogenesis, methylotrophic / H₂-dependent methylotrophic [PARTIAL]

- **Description:** Methanol, methylamines, methylsulfides as methyl-group donors. H₂-dependent methylotrophy in Methanomassiliicoccales.
- **Diagnostic enzymes:** mcrA + mtaA (methanol-CoM methyltransferase); Methanomassiliicoccales lack the H₄MPT-Wolfe-cycle so detection requires distinguishing markers
- **Phylogenetic distribution:** Methanosarcinales (multi-substrate); Methanomassiliicoccales (H₂-dependent methylotrophic specialists, gut)
- **Frequency in submissions:** MEDIUM (gut / mangrove / hypersaline samples)
- **Examples:** *Methanomassiliicoccus luminyensis*, *Methanosarcina mazei*
- **CF status:** Falls under `methanogenesis` via mcrA (Methanosarcinales). Methanomassiliicoccales mcrA may be divergent — LIMITATIONS E.2 documents partial coverage.

### B15. ANME — anaerobic methane oxidation (reverse methanogenesis) [GAP — F.2 documented]

- **Description:** Methane consumption coupled to NO₃⁻ (Methanoperedens / ANME-2d), SO₄²⁻ (ANME-1, ANME-2), Fe(III)/Mn(IV) (some ANME-2). Operates the methanogenesis pathway in reverse.
- **Diagnostic enzymes:** mcrA (same family but reverse direction) + Wood-Ljungdahl reverse + electron-acceptor-specific terminal modules. Markers indistinguishable from methanogens.
- **Phylogenetic distribution:** ANME-1 (related to Methanomicrobiales), ANME-2 (Methanosarcinales), ANME-3, Ca. Methanoperedens (ANME-2d, NO₃⁻ acceptor)
- **Cultivation relevance:** Mostly uncultured; Methanoperedens nitroreducens enrichment culture exists.
- **Frequency in submissions:** LOW-MEDIUM (sediments, marine seeps, freshwater anaerobic methane sinks)
- **Examples:** *Ca.* Methanoperedens nitroreducens (in test set), ANME-2 archaea
- **KEGG:** ko00680 (operating reverse)
- **CF status:** Documented as LIMITATIONS C.1 (directional ambiguity) + F.2 (mcrA negative-marker rule blocks reverse-WL acetogenesis from re-firing). Methanoperedens currently classified as methanogenic + recipe predicts H₂/CO₂ (wrong; actual recipe is CH₄ + NO₃⁻).

### B16. Anammox [COVERED, MAG-completeness limited]

- **Description:** NH₄⁺ + NO₂⁻ → N₂ via hydrazine intermediate. Major N₂ source in marine OMZs and engineered N-removal.
- **Donor / acceptor / carbon:** NH₄⁺ / NO₂⁻ / autotrophic (Wood-Ljungdahl-type, Ca. Brocadiaceae)
- **Diagnostic enzymes:** **hzsA** (hydrazine synthase α), **hdh** (hydrazine dehydrogenase)
- **Phylogenetic distribution:** Planctomycetota Brocadiaceae (Ca. Brocadia, Kuenenia, Anammoxoglobus, Jettenia, Scalindua)
- **Cultivation relevance:** Specialty enrichment (DSMZ 1605); slow doubling.
- **Frequency in submissions:** MEDIUM (wastewater / marine OMZ samples)
- **Examples:** *Ca.* Kuenenia stuttgartiensis, *Ca.* Brocadia
- **KEGG:** ko00910
- **CF status:** `anammox` capability + hzsA + hdh markers. Test-set Scalindua profunda fails detection due to MAG completeness (LIMITATIONS E.1) — markers can detect Scalindua proteins at 60–76% identity but predicted-protein set lacks them.

### B17. N-DAMO (nitrite-dependent anaerobic methane oxidation) [GAP]

- **Description:** CH₄ + NO₂⁻ → CO₂ + N₂ + H₂O. Discovered ~2010 in NC10 phylum (Methylomirabilis).
- **Diagnostic enzymes:** pmoCAB (methane monooxygenase, particulate) + intra-aerobic O₂-generating enzyme (NO dismutase, nod); requires also nirS/nirK
- **Phylogenetic distribution:** Methylomirabilota (Ca. Methylomirabilis oxyfera and relatives)
- **Frequency in submissions:** LOW (specialty wetland / freshwater anoxic samples)
- **Examples:** *Ca.* Methylomirabilis oxyfera
- **CF status:** GAP. Distinct from aerobic methanotrophy; intra-aerobic O₂ generation is biochemically novel.

### B18. Acetogenesis (Wood-Ljungdahl) [COVERED]

- **Description:** 2 CO₂ + 4 H₂ → CH₃COO⁻ + 2 H₂O via the WL pathway. CO dehydrogenase / acetyl-CoA synthase bifunctional enzyme is the signature.
- **Donor / acceptor / carbon:** H₂ / CO₂ (or organic via mixed metabolism) / autotrophic
- **Diagnostic enzymes:** **acsB** (acetyl-CoA synthase α / CdhC) + **cooS / cdhA** (Ni-CODH); negative markers exclude methanogens, SRBs, iron reducers
- **Phylogenetic distribution:** Acetobacterium, Clostridium, Moorella, Sporomusa, Ca. Endolissoclinum
- **Cultivation relevance:** Specialty anaerobe (DSMZ 135 for Acetobacterium)
- **Frequency in submissions:** LOW-MEDIUM
- **Examples:** *Acetobacterium woodii*, *Moorella thermoacetica*
- **KEGG:** ko00720
- **CF status:** `acetogenesis_wood_ljungdahl` capability with multi-marker (acsB_cdhC + cooS_cdhA) + negative markers (mcrA, dsrAB, aprAB, mtrC_omcB). Phase 1.5n F.3 mitigation requires diagnostic-marker corroboration. Detected on Acetobacterium.

### B19. Hydrogenotrophic denitrification (autotrophic with H₂) [GAP]

- **Description:** H₂ + NO₃⁻ → N₂ + H₂O. Autotrophic CO₂ fixation in some cases. Common in deep subsurface, engineered systems.
- **Diagnostic enzymes:** Hydrogenase (Group 1 [NiFe]) + canonical denitrification (narG/napA, nirS/K, norBC, nosZ)
- **Phylogenetic distribution:** Paracoccus, Pseudomonas pseudoflava, Sulfurimonas (sulfide+H₂ flexibility)
- **Frequency in submissions:** LOW-MEDIUM (engineered groundwater treatment, deep subsurface)
- **Examples:** *Paracoccus denitrificans* (autotrophic capable), *Sulfurimonas denitrificans*
- **CF status:** Falls under denitrification capability; gas-phase recommendation depends on hydrogenase detection but not as a unified capability.

### B20. Sulfide-driven autotrophic denitrification (Thiobacillus denitrificans / Sulfurimonas) [PARTIAL]

- **Description:** S²⁻ → SO₄²⁻ coupled to NO₃⁻ → N₂. Combines sulfur oxidation + denitrification + autotrophic CO₂ fixation.
- **Diagnostic enzymes:** soxB + denitrification cassette + Calvin enzymes
- **Phylogenetic distribution:** Thiobacillus denitrificans, Sulfurimonas, Sulfuricurvum
- **Frequency in submissions:** MEDIUM (sulfide-rich anoxic or microoxic samples — sulfide contaminated groundwater, marine sediments)
- **Examples:** *Thiobacillus denitrificans*, *Sulfurimonas denitrificans* (test set)
- **CF status:** PARTIAL — detection fires both sulfur_oxidation and denitrification capabilities (correctly for Sulfurimonas in test set), but no unified "sulfide-denitrifier" recipe template — recipe composition mode-pick may produce mixed signals.

---

## C. Phototrophy variants

### C1. Anoxygenic phototrophy purple, Type II (Rhodobacter style) [COVERED]

- **Description:** Type II (quinone-pool) reaction center; purple bacteria (α/β-proteobacteria + γ-purple sulfur Allochromatium).
- **Donor / acceptor / carbon:** organic (purple non-sulfur) or H₂S (purple sulfur) / cyclic photophosphorylation / mixotrophic
- **Diagnostic enzymes:** **pufLM** (RC-L and RC-M subunits)
- **Phylogenetic distribution:** Rhodobacterales, Rhodospirillales, Allochromatium / Thiorhodaceae
- **Frequency in submissions:** MEDIUM
- **Examples:** *Rhodopseudomonas palustris*, *Rhodobacter capsulatus*, *Allochromatium vinosum*
- **KEGG:** No specific map (anoxygenic pathways)
- **CF status:** `anoxygenic_phototrophy_purple` capability + pufLM marker + Phase 1.5n override.

### C2. Anoxygenic phototrophy green sulfur, Type I (Chlorobium style) [COVERED]

- **Description:** Type I (FeS-cluster) reaction center in green sulfur bacteria; obligate anaerobic phototrophy with H₂S as donor.
- **Diagnostic enzymes:** **pscA** (RC core), **fmoA** (Fenna-Matthews-Olson antenna)
- **Phylogenetic distribution:** Chlorobiaceae (Chlorobaculum, Chlorobium, Prosthecochloris, Pelodictyon)
- **Frequency in submissions:** LOW
- **Examples:** *Chlorobaculum tepidum*, *Chlorobium phaeobacteroides*
- **CF status:** `anoxygenic_phototrophy_green_sulfur` capability + pscA_fmoA marker.

### C3. Anoxygenic phototrophy filamentous (Chloroflexus FAP) [COVERED]

- **Description:** Filamentous anoxygenic phototrophs use Type II RC like purple bacteria but in Chloroflexota lineage. Chlorosomes + 3HP cycle for CO₂ fixation.
- **Diagnostic enzymes:** pufLM (shared with purple)
- **Phylogenetic distribution:** Chloroflexales (FAP)
- **Examples:** *Chloroflexus aurantiacus*, *Roseiflexus*
- **CF status:** Detected via pufLM + Phase 1.5n diagnostic_marker_override (because gapseq doesn't annotate Chloroflexus's chlorosome / 3HP architecture as a standard purple-bacteria pathway).

### C4. Anoxygenic phototrophy aerobic (AAP — Roseobacter, Erythrobacter) [PARTIAL]

- **Description:** Some α-proteobacteria are aerobic anoxygenic phototrophs that use bacteriochlorophyll under aerobic conditions.
- **Diagnostic enzymes:** pufLM (shared with anaerobic purple)
- **Phylogenetic distribution:** Roseobacter clade, Erythrobacter, AAP marine species
- **Frequency in submissions:** LOW-MEDIUM (marine surface waters, coastal sediments)
- **Examples:** *Roseobacter denitrificans*, *Erythrobacter litoralis*
- **CF status:** Detected as anoxygenic_phototrophy_purple via pufLM, but routed to phototrophic primary mode + anaerobic atmosphere — wrong for AAP. No distinguishing capability or atmosphere logic.

### C5. Oxygenic phototrophy (cyanobacteria + algal chloroplasts) [COVERED]

- **Description:** Light-driven water splitting; PSI + PSII tandem. Universal in cyanobacteria + plant chloroplasts.
- **Diagnostic enzymes:** **psaA** (PSI core), **psbA** (D1 protein, PSII)
- **Phylogenetic distribution:** Cyanobacteria; not in 26-organism test set
- **Frequency in submissions:** LOW-MEDIUM (ecology / freshwater / bloom samples)
- **Examples:** *Synechococcus*, *Prochlorococcus*, *Anabaena*
- **CF status:** `oxygenic_phototrophy` capability + psaA_psbA marker. Marker file present; no test-set organism fires it but detection should work for Cyanobacteria submissions.

### C6. Heliobacterial phototrophy (Type I RC in Firmicutes) [GAP]

- **Description:** Heliobacterium / Heliobacillus anoxygenic phototrophs in Firmicutes. Bacteriochlorophyll g; Type I-like RC unrelated to purple bacterial Type II.
- **Diagnostic enzymes:** **pshA** (heliobacterial RC core, distinct family from pscA/pufLM)
- **Phylogenetic distribution:** Heliobacteriaceae (Firmicutes)
- **Frequency in submissions:** LOW
- **Examples:** *Heliobacterium modesticaldum*, *Heliobacillus mobilis*
- **CF status:** Documented as LIMITATIONS B.5. No pshA marker; would be missed entirely.

### C7. Photoferrotrophy (anaerobic Fe(II) oxidation by phototrophs) [GAP] **← potential high-priority gap**

- **Description:** Anaerobic Fe²⁺ → Fe³⁺ coupled to anoxygenic photosynthesis. Hypothesized origin of Banded Iron Formations.
- **Donor / acceptor / carbon:** Fe²⁺ / cyclic photophosphorylation (no terminal acceptor; light-driven) / autotrophic Calvin
- **Diagnostic enzymes:** Photosystem (pufLM or pscA) + uncharacterized Fe-oxidoreductase. PioABC in Rhodopseudomonas palustris TIE-1 is one characterized system.
- **Phylogenetic distribution:** Some Rhodobacter (Rhodobacter ferrooxidans SW2), Rhodopseudomonas palustris TIE-1, Chlorobium ferrooxidans KoFox
- **Frequency in submissions:** LOW-MEDIUM (specialty geomicrobiology / paleoenvironment samples)
- **Examples:** *Rhodobacter ferrooxidans* SW2, *R. palustris* TIE-1, *Chlorobium ferrooxidans* KoFox
- **CF status:** GAP. PioABC / FoxEYZ markers not in reference set. Currently photoferrotrophs detect as plain anoxygenic_phototrophy_purple (recipe lacks Fe²⁺ as donor).

### C8. Bacteriorhodopsin / proteorhodopsin [COVERED]

- **Description:** Light-driven proton pumping via retinal-binding rhodopsin. Supplementary energy in heterotrophs (proteorhodopsin in marine surface bacteria) or major energy source (bacteriorhodopsin in extreme halophiles).
- **Donor / acceptor / carbon:** light-driven proton gradient; carbon from organic substrates (heterotrophic in most cases) or autotrophic in some halophiles
- **Diagnostic enzymes:** **rhodopsin** (bacteriorhodopsin / proteorhodopsin / xanthorhodopsin family)
- **Phylogenetic distribution:** Halobacteriales (BR), marine SAR11 / Pelagibacteraceae (PR), some Flavobacteriaceae
- **Frequency in submissions:** LOW-MEDIUM (halophile samples, marine surface waters)
- **Examples:** *Halobacterium salinarum*, *Pelagibacter ubique*
- **CF status:** `bacteriorhodopsin` capability + rhodopsin marker + Phase 1.5n override. Halobacterium correctly detected.

---

## D. Fermentation

### D1. Mixed acid fermentation [COVERED]

- **Description:** Mixed C2-C4 organic acids (formate, acetate, lactate, succinate, ethanol) + CO₂ + H₂. Glucose / sugars as substrate.
- **Phylogenetic distribution:** Enterobacterales (E. coli, Klebsiella, Salmonella, Shigella)
- **Examples:** *Escherichia coli* (test set, facultative)
- **CF status:** `fermentation_mixed` capability (broad detector via glycolysis + fermentation-product pathways).

### D2. Lactic acid fermentation [COVERED]

- **Description:** Glucose / lactose → lactate (homofermentative) or lactate + acetate + ethanol + CO₂ (heterofermentative).
- **Phylogenetic distribution:** Lactobacillales
- **Examples:** *Lactobacillus plantarum* (test set), *Lactococcus*, *Streptococcus*
- **CF status:** Falls under `fermentation_mixed` broad detector.

### D3. Butyric acid / solventogenic fermentation [COVERED]

- **Description:** Glucose → acetate + butyrate + CO₂ + H₂ (acidogenic phase) → acetone/butanol/ethanol (solventogenic phase).
- **Phylogenetic distribution:** Clostridiaceae
- **Examples:** *Clostridium acetobutylicum* (test set)
- **CF status:** Falls under `fermentation_mixed`.

### D4. Propionic acid fermentation [COVERED]

- **Description:** Lactate or sugars → propionate + acetate + CO₂. Wood-Werkman cycle.
- **Phylogenetic distribution:** Propionibacteriaceae, Veillonella, some clostridia
- **CF status:** Falls under `fermentation_mixed`.

### D5. Specialty fermentations (purine, pyrimidine, amino acid) [COVERED, broad]

- **Description:** Stickland reaction (paired amino acid fermentation), purine fermentation (Clostridium purinilyticum-style), various niche fermentations.
- **CF status:** Captured under `fermentation_mixed` broad detector if glycolysis or appropriate substrate-specific pathways are annotated.

**Note on fermentation:** CultureForge's `fermentation_mixed` is a broad-detector capability covering most fermentation patterns. Distinguishing among the variants is not currently a recipe-quality issue because the recipes for fermentation are similar (organic carbon, no electron acceptor, anaerobic). LIMITATIONS B.2 documents the broad detection as accepted trade-off.

---

## E. Composite / specialized

### E1. Syntrophy (β-oxidation of fatty acids, propionate, butyrate; H₂-transfer dependent) [COVERED]

- **Description:** Fatty-acid oxidation thermodynamically dependent on H₂ removal by partner organism (typically methanogen or SRB). Single-organism culture not feasible.
- **Phylogenetic distribution:** Syntrophobacterales, Syntrophomonadaceae, some Geobacter
- **Examples:** *Syntrophomonas wolfei* (test set), *Syntrophobacter fumaroxidans*
- **CF status:** Composite syntrophy detector in `capability_detectors.py` uses fermentation-products + EtfAB-Bcd + low-fermentation-confidence pattern. Recipe assumes co-culture with methanogen partner.

### E2. Cable bacteria long-distance electron transfer [GAP]

- **Description:** Filamentous bacteria spanning oxic-anoxic interfaces; transfer electrons over centimeters via novel periplasmic conductive structures. Couples sulfide oxidation in deep sediment to O₂ reduction at surface.
- **Diagnostic enzymes:** Periplasmic conductive fibers (CcoP/CcoO components, but also novel structural proteins not yet fully characterized as marker-suitable)
- **Phylogenetic distribution:** Ca. Electrothrix, Ca. Electronema (Desulfobulbaceae)
- **Frequency in submissions:** LOW (specialty sediment biogeochemistry)
- **Examples:** *Ca.* Electrothrix communis, *Ca.* Electronema palustris
- **CF status:** GAP. Documented in LIMITATIONS U.5.

### E3. Hydrogenotrophic chemolithotrophy non-aerobic (sulfate-reducing on H₂) [PARTIAL]

- **Description:** H₂ + SO₄²⁻ → H₂S + H₂O. Subset of sulfate reduction with H₂ as electron donor instead of organic acids.
- **CF status:** Detected via dissimilatory_sulfate_reduction + hydrogenase signal; not a unified capability.

### E4. Magnetotaxis-supported metabolism [N/A — out of scope]

Not an energy metabolism per se. Magnetotaxis is a behavioral-physiological capability of magnetotactic bacteria; their underlying metabolism varies (Magnetospirillum is a microaerophilic chemolithotroph). Out of audit scope.

---

## Summary count

- **Total energy metabolisms enumerated:** ~38
  - Aerobic: 12
  - Anaerobic respiration: 20
  - Phototrophy: 8
  - Fermentation: 5 (largely captured by single broad detector)
  - Composite: 4
- **Currently COVERED:** ~17 (depending on how multi-substrate methanogenesis variants are counted)
- **PARTIAL:** ~8
- **GAP:** ~13

Detailed status mapping → see `coverage_map.md`.
