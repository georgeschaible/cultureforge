# CultureForge — Suggested Genomes for External Validation

This is an optional list. Testers can submit any genome they want. The list below identifies organism types where CultureForge has documented gaps or limited validation evidence — submissions of these would close known validation holes.

Submissions are not required, but high-priority for the validation gap they would close.

---

## Architecturally-supported but no positive-control genome

These metabolisms are supported in the detector + recipe composer but have not been validated against a positive-control genome.

### Sulfate-coupled ANME (ANME-1, ANME-2, ANME-3)

- **Why interesting:** The Phase 3.6 ANME directional discriminator architecturally supports the dsrAB OR-branch (sulfate-coupled ANME), but no test-set or sentinel genome covers this case.
- **Suggested submissions:** Methanophagales (ANME-1) MAGs from sulfate-methane-transition zones, ANME-2a/b/c MAGs from cold-seep environments, ANME-3 MAGs.
- **Expected output:** `anme_reverse_methanogenic` primary mode, `anme` atmosphere, Na2SO4 ~15 mM as terminal electron acceptor, ΔG ≈ -16.6 kJ/mol.
- **Critical test:** The dsrAB OR-branch should fire (capability OR-group satisfied), routing to the sulfate-coupled recipe variant rather than the nitrate-coupled one (which fires for Methanoperedens).

### Iron-coupled ANME

- **Why interesting:** mtrC_omcB OR-branch in the Phase 3.6 discriminator. No genome representing this case in the test set.
- **Suggested submissions:** ANME MAGs from iron-rich sediments where mtrC / omcB family proteins are encoded.
- **Expected output:** `anme_reverse_methanogenic` primary, `anme` atmosphere, Fe(III) citrate ~20 mM as electron acceptor (fallback branch).

### Comammox Nitrospira

- **Why interesting:** Comammox combines AOB + NOB metabolism in a single organism. The Nitrospira inopinata-class amoA is divergent from canonical AOB amoA; current CultureForge would classify this as NOB (nxrA fires), missing the ammonia-oxidation half. Phase 3.3 deferred comammox amoA pending a comammox in the test set.
- **Suggested submissions:** Nitrospira inopinata, Nitrospira nitrosa, Nitrospira nitrificans genomes.
- **Expected output (current):** lithotrophic_aerobic (nitrite oxidation, canonical NOB) — incomplete classification.
- **Critical test:** This would surface the comammox detection gap as a documented limitation, validating the deferred-decision rationale or motivating a Phase 4 addition.

### Anammox bacteria with complete MAGs

- **Why interesting:** The blind set has Scalindua profunda which escalates due to MAG completeness (LIMITATIONS E.1). A high-quality anammox MAG would validate the hzsA + hdh detection path positively.
- **Suggested submissions:** Brocadia anammoxidans, Kuenenia stuttgartiensis, Anammoxoglobus propionicus.
- **Expected output:** anammox primary mode (architecturally supported), N2/CO2 atmosphere, NH4Cl + NaNO2 as the energy substrates.

---

## Specialty metabolisms not currently covered

These are deferred / out-of-scope. Submitting them would surface failure modes and document expected behavior on uncovered metabolisms.

### Selenate / arsenate respirers

- **Examples:** Bacillus selenitireducens, Geobacter sulfurreducens variants with arsenate reduction.
- **Expected behavior:** No specific marker; classification will fall to the dominant other metabolism (often `anaerobic_respiratory` or `fermentative`). Manual review needed.

### Cable bacteria (Desulfobulbaceae long-distance electron transport)

- **Examples:** Candidatus Electrothrix communis, Ca. Electronema palustris.
- **Expected behavior:** Out of scope. Genome content may classify as fermentative or as a sulfate reducer; LDET-specific cultivation needs are not represented.

### Photoferrotrophs

- **Examples:** Chlorobium ferrooxidans, Rhodopseudomonas palustris CGA009 (Fe-oxidizing variant).
- **Expected behavior:** phototrophic primary mode should fire (already covered), but Fe(II) substrate-specific recipe routing is missing.

### N-DAMO (Methylomirabilis intra-aerobic methane oxidation in NC10)

- **Examples:** Methylomirabilis oxyfera, Ca. Methylomirabilis lanthanidiphila.
- **Expected behavior:** Out of scope (biochemically distinct from canonical methanotrophy — internal O2 generation from NO via dismutation, then methane oxidation with the generated O2). Currently no specific detection.

### Sulfur-disproportionating bacteria

- **Examples:** Desulfocapsa thiozymogenes, Desulfobulbus mediterraneus (some strains).
- **Expected behavior:** May classify as sulfate reducer (dsrAB present) but the metabolism is sulfur disproportionation. Detection of disproportionation specifically is not implemented.

---

## Hyperthermophilic / extreme-environment organisms

These aren't gaps in coverage but offer additional validation breadth.

### Hyperthermophilic forward methanogens

- **Examples:** Methanopyrus kandleri, Methanocaldococcus species other than gid=8.
- **Why useful:** Validates methanogenesis detection across temperature range — current sentinel coverage is mesophilic (Methanosarcina) + hyperthermophilic (Methanocaldococcus). A second hyperthermophilic methanogen would tighten the temperature-envelope confidence.

### Acidophilic / alkaliphilic extremes

- **Examples:** Picrophilus oshimae (pH 0.06 culture), Natranaerobius thermophilus (pH 9.5).
- **Why useful:** Validates pH-envelope predictions at the extremes.

### Psychrophilic organisms

- **Examples:** Psychrobacter cryohalolentis, Colwellia psychrerythraea.
- **Why useful:** Validates temperature predictions at the cold extreme; current test set is mesophilic-to-hyperthermophilic biased.

---

## Organisms with documented substrate ambiguity

These would surface CultureForge's behavior on known ambiguity cases, validating that the tool flags rather than guesses.

### Dehalococcoides (rdhA family substrate diversity)

- **Examples:** D. mccartyi strain 195 (PCE specialist) vs. strain CBDB1 (chlorobenzene specialist) vs. strain VS (vinyl-chloride respirer).
- **Why useful:** LIMITATIONS D.1 documents that rdhA family detection cannot subtype substrate specificity. Submissions of multiple Dehalococcoides strains would let testers compare CultureForge's identical output vs. the substrate-specific cultivation literature.

### Geobacter species with iron-reduction electron transfer diversity

- **Examples:** G. sulfurreducens, G. metallireducens, G. uraniireducens.
- **Why useful:** LIMITATIONS D.2 documents that mtrC / omcB detection captures iron reduction broadly but doesn't distinguish soluble Fe(III) vs. mineral Fe(III) preference.

---

## How to submit

1. Pick a genome from the suggestions above (or any genome of your own interest).
2. Process through CultureForge using the `TESTER_QUICKSTART.md` instructions.
3. Fill out `TESTER_FEEDBACK_TEMPLATE.md`.
4. Submit feedback to (TBD distribution channel — see project lead).

If you want to submit a genome that isn't on this list, that's also welcome. The suggestions above are the highest-priority validation gaps; feedback on any organism is useful.
