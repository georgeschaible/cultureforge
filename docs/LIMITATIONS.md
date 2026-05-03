# CultureForge Detection Layer Limitations

This document catalogs known limitations in the current detection layer. The
recipe composer (Phase 2c+) reads this catalog to determine when to flag
uncertainty in its output or refuse to compose a recipe.

For each limitation, the relevant metabolism's pathway_definitions.json
entry is annotated with a `known_limitations` field referencing this
document.

Last updated: 2026-05-02 (post-Phase-3.7)

---

## Validation status — capability tagging (Phase 3.7)

Each Phase 3 capability is tagged below with its validation provenance. **Validated-against-sentinel** means a named-strain genome (test-set or gid=900+ sentinel) was processed through the full pipeline and produced the expected primary cultivation mode + recipe. **Inferred-from-test-set-behavior** means the capability fires correctly on negative controls in the test set but has not been positive-control validated against a named-strain genome.

### Validated-against-sentinel (positive-control empirically verified)
- **aerobic_methanotrophy** — Methylococcus capsulatus Bath sentinel (gid=900, Phase 3.5)
- **anaerobic_respiratory_dnra** — Wolinella succinogenes DSM 1740 sentinel (gid=901, Phase 3.7)
- **lithotrophic_aerobic_nitrite (Type A clade)** — Nitrospira moscoviensis test-set genome (gid=23, Phase 3.3)
- **lithotrophic_aerobic_nitrite (Type B clade)** — Nitrobacter winogradskyi Nb-255 sentinel (gid=902, Phase 3.7)
- **methanogenesis (forward)** — Methanosarcina acetivorans C2A sentinel (gid=903) post-Phase-3.8 override + Methanocaldococcus jannaschii test-set genome (gid=8). Phase 3.8 added `diagnostic_marker_override` on mcrA (50% pident / 70% qcov / 0.65 override_confidence), enabling marker-only sentinel validation symmetric with the Phase 3.5+ pattern.
- **anme_reverse_methanogenesis (positive case, nitrate-coupled)** — Methanoperedens nitroreducens test-set genome (gid=28, Phase 3.6)
- **anme_reverse_methanogenesis (negative-control: forward methanogen)** — Methanosarcina acetivorans C2A sentinel (gid=903, Phase 3.7) and Methanocaldococcus jannaschii (gid=8). False-positive averted on canonical methanogens.

### Inferred-from-test-set-behavior (no named-strain positive-control sentinel)
- **anme_reverse_methanogenesis (sulfate-coupled, ANME-1/2/3)** — architecturally supported via dsrAB OR-branch but no test-set or sentinel genome representing this case.
- **anme_reverse_methanogenesis (iron-coupled, mtrC_omcB)** — architecturally supported via mtrC_omcB OR-branch but no test-set or sentinel genome.
- **Phase 3.1 manual condition overrides** — validated by command-line round-trip but no domain-specific test-set genome that exercises override behavior.
- **Phase 3.2 archaeal sulfur oxidation markers** — Sulfolobus acidocaldarius DSM 639 is a true negative (genuinely lacks the markers per literature); no positive-control archaeal sulfur oxidizer in test set.

---

## Category A: Wrong-recipe risk

Limitations where detection failure produces a fundamentally wrong recipe.
Organisms affected will not grow on the predicted medium.

### A.1 Reductive dehalogenase substrate specificity

- **Affected organisms**: Dehalococcoides, Dehalobacter, Desulfitobacterium, Sulfurospirillum
- **Metabolism**: Organohalide respiration
- **Symptom**: rdhA hit indicates organohalide respiration capability, but the specific halogenated substrate (PCE, TCE, DCE, vinyl chloride, chlorobenzenes, bromoethenes, fluorinated compounds) cannot be determined from the genome alone. Different Dehalococcoides strains require different chlorinated electron acceptors.
- **Root cause**: rdhA is a broad gene family with >60 characterized variants. BLAST detects the family but not the substrate class. No substrate-specific HMMs exist in CultureForge.
- **Severity**: Blocker for recipe accuracy — wrong electron acceptor = no growth.
- **Workaround**: Recipe composer should list all plausible halogenated substrates and recommend the user select based on isolation source chemistry or published literature for the specific strain/lineage. See also D.1.
- **Future fix**: Substrate-class-specific rdhA HMMs (Hug et al. 2013 classification); Tier 2 structural homology to characterized rdhA proteins with known substrate specificity.

### A.2 Nitrospira moscoviensis classification — RESOLVED Phase 3.3 (re-scoped from comammox amoA to canonical NOB nxrA)

- **Original framing (Phase 1.5m)**: comammox amoA divergence — assumed N. moscoviensis NSP M-1 was comammox and that detection failed due to short fragmentary comammox amoA references in UniProt.
- **Pre-Phase-3.3 verification (`nitrospira_verification.md`) revealed the original framing was wrong**: NSP M-1 is **NOT comammox** — it is the type-strain canonical nitrite oxidizer (Ehrich et al. 1995). Comammox was discovered in different species (*Ca.* N. inopinata, *Ca.* N. nitrosa, *Ca.* N. nitrificans). NSP M-1 has zero amoA orthologs (verified by both BLAST and direct NCBI Protein search) but encodes 5 strong nxrA paralogs at 94-96% pident to canonical Nitrospira nxrA. The actual gap was a missing nitrite-oxidation capability in CultureForge, not a missing comammox amoA reference.
- **Status (post-Phase-3.3)**: **RESOLVED for canonical NOB.** New `lithotrophic_aerobic_nitrite` capability + 8 verified nxrA references covering 4 NOB genera (Nitrospira × 3, Nitrobacter × 2, Nitrotoga × 2, Nitrolancea × 1). Two-clade architecture (Type A cytoplasmic + Type B periplasmic) handled via dual-clade reference set with OR logic. Empirical narG cross-reactivity assessment confirmed clean discrimination at 75% pident threshold (39-point gap between the 48% narG-family ceiling and the 87% NOB-intra-clade floor). N. moscoviensis now classifies correctly as `lithotrophic_aerobic` (nitrite oxidation, canonical NOB) at confidence 0.77 with aerobic / NaNO2 / NaHCO3 / pH 7.5 recipe matching DSMZ Medium 2399 architecture.
- **V12 score note**: improvement is not visible in the V12 numeric score (20% → 19%, essentially flat) because of pre-existing single-reference Jaccard brittleness (LIMITATIONS G.2) and ingredient-name normalization gaps with DSMZ 756d (which lists individual SL-10 components rather than aggregated). The recipe is biologically correct per direct architectural comparison with DSMZ Medium 2399; the metric just doesn't reflect it. This is the same pattern as Phase 3.2's Sulfolobus DSM 639 finding.
- **Comammox detection (deferred)**: nxrA + comammox-specific amoA combined would distinguish comammox from canonical NOB. No comammox organism exists in the current 26-organism test set, so comammox-specific amoA references are deferred to a future sub-phase if needed. The nxrA infrastructure is in place — when a comammox organism is encountered, both markers would fire and the routing logic can be extended.
- **References**: `data/diagnostic_markers/nitrite_oxidation_review.md`, `nitrospira_verification.md`, REFERENCE_CURATION.md "Marker: nxrA (Phase 3.3)" section.

### A.3 Iron oxidation reference error (cyc2) — RESOLVED Phase 1.5l + 1.5m

- **Status**: FULLY RESOLVED. Phase 1.5l replaced the original wrong-protein cyc2 reference (barley Beclin-1) with verified Acidithiobacillus ferrooxidans Cyc2 accessions, but those self-validating refs were removed in Phase 1.5m. The current cyc2 reference set is 4 entries (A. ferrivorans + Leptospirillum + Acidihalobacter + Mariprofundus) with no test-set contamination. **A. ferrooxidans now detects Acidophilic Fe(II) oxidation as a primary capability via 85.7% identity to non-self refs (bs=810).** This is the headline test for the Phase 1.5m rebuild.

### A.4 Neutrophilic/microaerophilic iron oxidation not covered

- **Affected organisms**: Gallionella, Mariprofundus, Sideroxydans, Ferriphaselus
- **Metabolism**: Neutrophilic Fe(II) oxidation
- **Symptom**: No detection at all. These organisms use mtoA/mtoB (reverse of mtrAB) or Cyc2PV-1-type cytochromes, neither of which is in the marker database or pathway definitions.
- **Root cause**: Iron oxidation pathway definition only covers acidophilic route. Neutrophilic iron oxidizers use different electron transfer pathways.
- **Severity**: Blocker — recipe would lack Fe(II) electron donor and microaerobic atmosphere requirement.
- **Workaround**: None within current system. Manual annotation required.
- **Future fix**: Add mtoA/mtoB references; add neutrophilic iron oxidation as separate pathway in pathway_definitions.json.

### A.10 Aerobic methanotrophy detection — RESOLVED Phase 3.5 for canonical Type I/II/III methanotrophs

- **Affected organisms**: Methylococcaceae (Methylococcus, Methylomonas, Methylocaldum, Methylobacter), Methylocystaceae (Methylosinus, Methylocystis), Beijerinckiaceae (Methylocella, Methylocapsa), Verrucomicrobia methanotrophs (Methylacidiphilum).
- **Metabolism**: Aerobic methanotrophy (CH4 → CO2 via pMMO and/or sMMO).
- **Status (Phase 3.5)**: **RESOLVED** for canonical Type I, Type II, and Type III methanotrophs. New `aerobic_methanotrophy` capability with OR logic across two markers (pmoA, mmoX). 6 verified pmoA references covering 4 genera and all 3 lineage types (Type I × 2, Type II × 2, Type III × 2; dual-clade architecture). 4 verified mmoX references covering Type I and Type II (Type III lacks sMMO). 2 Swiss-Prot reviewed (Q607G3 Methylococcus pmoA, P22869 Methylococcus mmoX, P27353 Methylosinus mmoX) plus 7 TrEMBL across 5 distinct genera.
- **Empirical pmoA × amoA cross-reactivity assessment**: 8-10 point pident gap between amoA cross-reactivity ceiling (50%, Nitrosomonas test set) and pmoA cross-Type-I-II floor (58-60%). 60% threshold cleanly separates. mmoX has zero cross-reactivity in test set (highly conserved 82-99% intra-family).
- **Sentinel validation**: M. capsulatus Bath (GCF_000008325.1) loaded as one-off sentinel (gid=900, excluded from V12 by validation script's hardcoded ORGANISMS list). Result: pmoA fires at 100% pident, mmoX at 100% pident, methanotrophy capability detected at 0.80 confidence, recipe correctly produces air+CH4 80:20 gas phase + phosphate buffer pH 7 + NH4Cl + SL-10 + Wolin's vitamins, ΔG = -820 kJ/mol thermodynamically feasible. Atmosphere correctly categorized as "methanotroph" via the new `_cf_atmosphere_category` branch. End-to-end infrastructure verified.
- **New recipe infrastructure**: This is the first cultivation mode in CultureForge requiring methane in the gas phase. New `_compose_methanotrophy_recipe()` function; new methanotrophic mode group; new "methanotroph" atmosphere category; new ΔG template (CH4 + 2 O2 → CO2 + 2 H2O, -820 kJ/mol); CH4_aq already present in DEFAULT_ACTIVITIES at 1e-6 M.
- **Documented edge cases** (deferred to future sub-phases):
  - **N-DAMO** (NC10 phylum *Ca.* Methylomirabilis) — anaerobic methane oxidation with intra-aerobic O2 generation. Biochemically distinct from canonical aerobic methanotrophy; uses pmoA-related but functionally divergent enzyme. Out of Phase 3.5 scope.
  - **Methanotrophic Verrucomicrobia at unusual conditions** (Methylacidiphilum thermophilic / acidophilic — pH 1-3, 60°C) — capability detection works via Type III references; recipe composer's pH/temperature derivation depends on TEMPURA/GenomeSPOT data which may need overrides for these extremophiles.
  - **AAP / methanotroph gradient** — aerobic anoxygenic phototrophs and microaerobic methanotrophs near oxic-anoxic interfaces could blur classification but no test-set organism falls here.
- **References**: `data/diagnostic_markers/methanotrophy_review.md` (literature review + cross-reactivity); REFERENCE_CURATION.md "Marker: pmoA" + "Marker: mmoX" sections.

---

## Category B: Suboptimal-recipe risk

Limitations where detection produces a recipe that supports growth but
misses optimization opportunities or includes unnecessary components.

### B.1 Alternative nitrogenase coverage (vnfH, anfH)

- **Affected organisms**: Azotobacter, Rhodospirillum, some methanogens with vanadium or iron-only nitrogenases
- **Metabolism**: Nitrogen fixation
- **Symptom**: nifH (Mo-dependent nitrogenase) is the only reference. Organisms with vnfH (vanadium nitrogenase) or anfH (iron-only nitrogenase) as their primary or alternative nitrogenase may not have nifH detected, leading to missed N2 fixation capability.
- **Root cause**: nifH reference set (3 sequences) covers only Mo-dependent nitrogenase. vnfH and anfH diverge enough to fall below BLAST thresholds.
- **Severity**: Suboptimal — recipe defaults to NH4+ when N2 could be supported. Also misses the V or Fe-only metal cofactor requirement.
- **Workaround**: Recipe includes NH4+ as nitrogen source regardless; organism will grow but N2 fixation option isn't offered.
- **Future fix**: Add vnfH and anfH reference sequences; include V and Fe-only nitrogenase metal requirements in trace element recommendation.

### B.2 Fermentation broad detection (accepted trade-off)

- **Affected organisms**: 12/17 development set organisms detect fermentation
- **Metabolism**: Substrate-level phosphorylation / fermentation
- **Symptom**: Fermentation detected for organisms that primarily use other metabolisms. Glycolysis is near-universal; this makes fermentation the most common co-detected capability.
- **Root cause**: Fermentation pathway definition requires glycolysis + any fermentation product pathway, both of which are present in most bacteria.
- **Severity**: Low — parallel detection framework handles this correctly. Fermentation co-occurring with aerobic respiration means "facultative" (biologically correct). Recipe composer should use primary metabolism, not fermentation, to drive recipe design.
- **Workaround**: Recipe composer ranks by primary metabolism; fermentation informs "alternative growth mode" section only.
- **Future fix**: None needed. This is accepted behavior. Could tighten with EtfAB-Bcd electron-bifurcating complex detection for obligate fermenters vs. facultative glycolysis.

### B.3 Hydrogen metabolism incomplete

- **Affected organisms**: Organisms with [Fe]-only Hmd hydrogenase, some Group 4 [NiFe] hydrogenase variants
- **Metabolism**: Hydrogen metabolism / gas phase composition
- **Symptom**: Headspace gas composition recommendation may miss H2 requirement or H2 production, leading to suboptimal gas phase.
- **Root cause**: Hydrogenase BLAST database covers [NiFe] Groups 1-4 and [FeFe] Groups A-C but may miss [Fe]-only Hmd (specific to some methanogens) and divergent Group 4 variants.
- **Severity**: Suboptimal gas phase recommendation. Organism may grow but more slowly than with optimized H2:CO2 ratio.
- **Workaround**: Methanogen recipes should always include H2:CO2 headspace regardless of hydrogenase detection.
- **Future fix**: Add [Fe]-only Hmd reference sequences; expand Group 4 [NiFe] coverage.

### B.4 GenomeSPOT archaeal predictions unreliable

- **Affected organisms**: All archaea
- **Metabolism**: Growth conditions (temperature, pH, salinity, oxygen)
- **Symptom**: GenomeSPOT oxygen prediction skipped for archaea (Phase 1.5i fix). Temperature and pH predictions may also be less reliable for archaea because the training set is bacteria-dominated.
- **Root cause**: GenomeSPOT predicts "not tolerant" for known obligate aerobic archaea (Sulfolobus). The model was trained predominantly on bacterial genomes.
- **Severity**: Suboptimal — growth conditions may be inaccurate. Currently mitigated by TEMPURA cross-reference and user-supplied overrides.
- **Workaround**: For archaea, rely on TEMPURA data and user-supplied environmental parameters rather than GenomeSPOT predictions.
- **Future fix**: Retrain GenomeSPOT with archaeal training data, or use a separate archaeal growth condition model.

### B.5 Phototrophy marker gaps (heliobacteria, Acidobacteria)

- **Affected organisms**: Heliobacterium, Heliophilum (Type I RC in Firmicutes); Ca. Chloracidobacterium (Acidobacteria phototroph)
- **Metabolism**: Anoxygenic phototrophy
- **Symptom**: pufLM (purple bacteria Type II RC) and pscA/fmoA (green sulfur bacteria Type I RC) reference sets don't cover heliobacterial or acidobacterial reaction centers. These organisms would be misclassified as non-phototrophs.
- **Root cause**: Heliobacterial RC shares ancestry with Type I but diverges significantly. Chloracidobacterium has a unique antenna system.
- **Severity**: Suboptimal to wrong — recipe would lack light requirement and potentially use wrong carbon source.
- **Workaround**: None within current system.
- **Future fix**: Add heliobacterial pshA and Chloracidobacterium RC references.

---

## Category C: Directional ambiguity

Limitations where detection identifies enzymes correctly but cannot
determine the direction of the reaction.

### C.1 ANME archaea (methanogenesis vs methane oxidation) — RESOLVED Phase 3.6

- **Affected organisms**: Ca. Methanoperedens, ANME-1, ANME-2, ANME-3 clades
- **Metabolism**: Methanogenesis / anaerobic methane oxidation
- **Status**: RESOLVED Phase 3.6. New `anme_reverse_methanogenesis` capability discriminates ANME from forward methanogenesis using the signature `mcrA + (gapseq nitrate-reduction-pwy ≥100% complete OR dsrAB OR mtrC_omcB)`. The recipe-time mode picker places `anme_reverse_methanogenic` before `methanogenic` in `_SPECIFIC_MODES_PRIORITY`, so any genome with mcrA AND a credible alternative-acceptor signal routes to an ANME recipe (CH4:N2 80:20 atmosphere + acceptor-aware branching: NaNO3 / Na2SO4 / Fe(III) citrate). Forward methanogens like Methanocaldococcus jannaschii (mcrA present, no acceptor signal) correctly stay methanogenic — ANME capability is capped at 0.40 by the missing essential_marker_OR group.
- **Test-set verification**: GID=28 Methanoperedens flips methanogenic → anme_reverse_methanogenic (ANME-2d, nitrate-coupled). GID=8 Methanocaldococcus stays methanogenic. No false positives across 26 test genomes.
- **Architectural note on pathway-pattern fallback**: Methanoperedens has zero direct narG hits at evalue 1e-30 (best 24.5% pident) — the curated narG references can't reach its divergent napAB-like nitrate reductase. The signature is therefore satisfied via gapseq's UniRef-based pathway annotation (`pattern: "dissimilatory nitrate reduction"`, `min_completeness: 100`, `require_predicted: true`). The pathway-pattern entry is documented as a **fallback for divergent paralogs that escape curated-reference HMMER reach**, not a convenience replacement for marker curation.
- **Residual gap**: sulfate-coupled ANME-1/2/3 are architecturally supported (the dsrAB OR-branch fires the same signature) but no sulfate-coupled ANME is in the test set; iron-coupled fallback is similarly architectural-only.

### C.2 Reverse-dsr sulfide oxidation (partially resolved)

- **Affected organisms**: Allochromatium, Chlorobaculum, Thiocapsa, some Magnetospirillum strains
- **Metabolism**: Sulfate reduction vs. sulfide oxidation
- **Symptom**: dsrAB detected in organisms that run reverse dsr (sulfide → sulfur/sulfate direction).
- **Root cause**: dsrAB enzyme is the same protein in both directions.
- **Severity**: Was blocker; now mostly resolved.
- **Status**: MOSTLY RESOLVED by Phase 1.5k qmoA fix. Forward sulfate reduction now requires both dsrAB AND qmoA. Allochromatium validated as correctly excluded. Residual risk: organisms that have evolved qmoA loss while retaining forward dsr capability (theoretical, no known examples).
- **Workaround**: qmoA AND requirement handles the major case. For edge cases, check if sulfur oxidation pathway is also detected (suggests reverse-dsr direction).
- **Future fix**: None needed for common cases. Deep-branching SRBs with divergent qmoA might need expanded reference set.

---

## Category D: Subcategory ambiguity

Limitations where the detection identifies the metabolism but not which
substrate variant is relevant.

### D.1 Organohalide respiration substrate class

- **Affected organisms**: Dehalococcoides mccartyi strains, Dehalobacter, Desulfitobacterium
- **Metabolism**: Organohalide respiration
- **Symptom**: rdhA detected but substrate specificity unknown. A Dehalococcoides strain that respires only vinyl chloride will not grow on PCE, and vice versa.
- **Root cause**: rdhA family contains 60+ variants with different substrate specificities. Current BLAST reference (9 sequences) detects the family but cannot subtype.
- **Severity**: High within the metabolism — fundamentally wrong electron acceptor = no growth.
- **Workaround**: Recipe composer should list all plausible halogenated substrates (PCE, TCE, cis-DCE, vinyl chloride, chlorobenzenes) and recommend testing based on isolation source chemistry.
- **Future fix**: Substrate-class-specific rdhA HMMs; Tier 2 structural homology.

### D.2 Iron reduction electron transfer diversity

- **Affected organisms**: Non-Geobacter iron reducers (Shewanella, Geothrix, Rhodoferax, archaeal iron reducers)
- **Metabolism**: Dissimilatory Fe(III) reduction
- **Symptom**: mtrC/omcB reference only covers Geobacter/Shewanella-type outer membrane cytochromes. Firmicutes (Thermincola), archaeal (Ferroglobus), and Geothrix-class iron reducers use different electron transfer mechanisms.
- **Root cause**: Iron reduction has evolved independently multiple times with different molecular machinery.
- **Severity**: Metabolism missed entirely for non-Geobacter lineages.
- **Workaround**: Iron reducer lineages not in the Geobacteraceae/Shewanellaceae will have no iron reduction detected. Recipe defaults to alternative metabolism.
- **Future fix**: Add references for Shewanella mtrABC, Thermincola/Carboxydothermus dmkA, Geothrix electron shuttle pathway. Consider broad "iron reduction" HMM.

---

## Category E: Coverage gaps (silent failure)

Limitations where the detection misses the metabolism entirely on certain
phylogenetic lineages. The recipe looks fine but is wrong.

### E.1 Scalindua profunda detection failure — RECLASSIFIED Phase 1.5m as MAG-completeness, not reference-coverage

- **Affected organisms**: Ca. Scalindua profunda
- **Metabolism**: Anaerobic ammonium oxidation (anammox)
- **Symptom**: hzsA + hdh both return zero BLAST hits at e≤1e-5 against the 7-reference hzsA set + 3-reference hdh set. Aerobic respiration detected instead (false primary).
- **Root cause (revised in Phase 1.5m)**: Phase 1.5m hzsA expansion to 7 references (Kuenenia + 4 Brocadiaceae sister-species + 1 Jettenia ecosi + uncultured Brocadia) was tested via reciprocal BLAST. Result: **the references DO catch Scalindua-clade hzsA at 60-64% identity** (Scalindua japonica probe → reference set, top bs=1074). And the 3-reference hdh set catches Scalindua-clade hdh at 76% identity (Scalindua arabica probe → reference set, bs=947). **The detection failure is therefore a MAG completeness problem, not a reference coverage problem — the Scalindua profunda predicted-protein set lacks both genes** (Scalindua japonica hzsA → Scalindua profunda proteome = 0 hits at e≤1e-5).
- **Severity**: Blocker — recipe would be fundamentally wrong (aerobic heterotroph instead of anaerobic chemolithoautotroph).
- **Workaround**: For Brocadiaceae genomes with no anammox detection: confirm proteome completeness before flagging for manual review. If hzsA/hdh genes are missing from the predicted proteome, it likely indicates an incomplete MAG rather than a missing capability.
- **Future fix**: Either obtain a more complete Scalindua profunda assembly, or accept this organism as un-detectable from the current MAG. UniProt has zero entries for *Anammoxoglobus* and *Anammoximicrobium* (the closest non-Scalindua sister-genera) so phylogenetic-coverage expansion within the reference set is at the limit of what UniProt provides. Tier 2 structural homology would not help if the gene is absent from the predicted proteome.
- **Phase 3.4 addendum — MAG contamination signature**: The Phase 3.4 nrfA cross-reactivity scan revealed a Scalindua proteome hit at **99.8% pident to Salmonella enteritidis nrfA** (full coverage, 100% qcov, bs=1004). This is biologically impossible — a Brocadiaceae MAG cannot share 99.8% identity with a Gammaproteobacterial enzyme. The signature is **Enterobacteriaceae DNA contamination of the Scalindua MAG assembly** (a known issue with anammox MAGs from sediment metagenomic samples). Practical effect on Phase 3.4: the new `anaerobic_respiratory_dnra` capability fires on Scalindua at confidence 0.65, and the recipe composer routes it to a DNRA-primary recipe — biologically wrong (real Scalindua is anammox), but reflecting the proteome content. This is a fundamentally different problem from the original E.1 (real anammox markers absent from MAG); it's the same MAG-quality root cause but manifesting as a false-positive contaminant signal rather than a false-negative missing-gene signal. Both issues would be resolved by a higher-quality Scalindua reference assembly. A more robust automated solution would be a cross-phylum high-identity sanity check (flag cases where a marker hits at >95% identity to a phylogenetically distant reference as possible MAG contamination); deferred as a separate Phase 3 sub-phase candidate.

### E.2 mcrA coverage gaps in methanogen diversity

- **Affected organisms**: Deep-branching methanogens (Methanomassiliicoccales, Methanofastidiosales, Methanonatronarchaeales, some DPANN)
- **Metabolism**: Methanogenesis
- **Symptom**: mcrA reference set (5 sequences) covers Methanobacteriales, Methanosarcinales, Methanococcales, and Methanobrevibacteraceae — 3 of 7 major methanogen orders well-represented. Deep-branching lineages may have divergent mcrA that falls below BLAST thresholds.
- **Root cause**: mcrA is highly conserved within characterized methanogens but newly-discovered methanogen lineages (especially those not yet in Swiss-Prot) may have divergent sequences.
- **Severity**: Moderate — most known methanogens are covered, but novel methanogen MAGs from unusual environments may be missed.
- **Workaround**: Methanogen MAGs with no mcrA hit should be flagged if 16S/phylogenetic placement suggests methanogen affinity.
- **Future fix**: Expand mcrA reference set with Methanomassiliicoccales and other novel lineage representatives.

### E.3 dsrAB coverage — IMPROVED Phase 1.5m

- **Affected organisms (residual)**: Thermodesulfobacteria, novel deep-branching MAG lineages
- **Metabolism**: Sulfate reduction
- **Status (revised in Phase 1.5m)**: dsrAB reference set expanded from 2 entries (D. vulgaris) to 8 entries (4 alpha + 4 beta) spanning 4 distinct organisms across bacteria + archaea: Archaeoglobus fulgidus (Swiss-Prot), Megalodesulfovibrio gigas (Swiss-Prot fragments), Desulfobulbus oligotrophicus (TrEMBL), Desulfobacter hydrogenophilus (TrEMBL). D. vulgaris's own dsrAB (P45574, P45575) was REMOVED to eliminate self-validation contamination. D. vulgaris sulfate reduction is now detected at 0.818 confidence via 50-80% identity to non-self refs.
- **Severity (revised)**: Moderate. Common SRBs across Desulfovibrionales, Desulfobacterales, Desulfobulbales, and Archaeoglobales are now covered. Thermodesulfovibrionia and very deep MAG lineages may still be missed.
- **Workaround**: For deep-branching SRB MAGs with dsrAB pathway hits below threshold but no qmoA, inspect operon context manually.
- **Future fix**: Expand to Thermodesulfobacteria-class entries when UniProt coverage permits.

### E.5 mtrC/omcB coverage — IMPROVED Phase 1.5m

- **Affected organisms (residual)**: Non-Geobacter, non-Shewanella iron reducers (Geothrix, archaeal iron reducers, Firmicutes Thermincola)
- **Metabolism**: Dissimilatory Fe(III) reduction
- **Status (revised in Phase 1.5m)**: Reference set expanded to 3 entries: Shewanella baltica MtrC (Swiss-Prot), Shewanella putrefaciens MtrC (TrEMBL, full-length), Geobacter anodireducens OmcB (TrEMBL, full-length). G. sulfurreducens's own omcB (Q749K5) REMOVED for test-set exclusion. G. sulfurreducens iron reduction now detected at 0.597 confidence via 50-80% identity to non-self refs. See D.2 for non-Geobacter/Shewanella iron reducer gaps.

### E.4 Atypical nosZ (Clade II) in Bacteroidetes denitrifiers

- **Affected organisms**: Bacteroidetes, Epsilonproteobacteria, some Firmicutes with atypical (Clade II) nosZ
- **Metabolism**: Denitrification
- **Symptom**: nosZ essential marker requirement may miss organisms with Clade II (atypical-Z) nosZ. These organisms can complete denitrification to N2 but their nosZ is divergent from the typical (Clade I) nosZ references.
- **Root cause**: nosZ reference set (3 sequences) covers only Clade I nosZ (Pseudomonas, Alcaligenes, Paracoccus). Clade II nosZ shares <50% identity with Clade I.
- **Severity**: Moderate — denitrification would be detected at pathway level but capped at 0.40 by missing nosZ essential marker, resulting in false negative.
- **Workaround**: Organisms with high denitrification pathway completeness but no nosZ hit should be flagged as possible Clade II nosZ carriers.
- **Future fix**: Add Clade II nosZ reference sequences from Bacteroidetes and Epsilonproteobacteria.

### E.6 Archaeal sulfur oxidation markers — coverage IN PLACE Phase 3.2; Sulfolobus acidocaldarius DSM 639 is a true negative

- **Affected organisms**: *Sulfolobus acidocaldarius* (test set), *Acidianus*, *Metallosphaera*, *Saccharolobus*, *Sulfodiicoccus*, *Sulfuracidifex*, *Sulfurisphaera* (Sulfolobales archaeal sulfur oxidizers).
- **Metabolism**: Lithotrophic sulfur oxidation in thermoacidophilic archaea
- **Status (Phase 3.2)**: Marker coverage **IN PLACE**. Four new diagnostic markers added: tqoDoxD, tqoDoxA, tetH, sor — 15 verified UniProt accessions across 4 genera (Acidianus, Metallosphaera, Saccharolobus, Sulfurisphaera). Pathway `sulfur_oxidation` extended to include archaeal enzymes alongside bacterial soxB. The capability now reads "Sulfur oxidation (bacterial SOX + archaeal TQO/TetH/SOR)".
- **Honest finding for the test-set target**: *Sulfolobus acidocaldarius* DSM 639 (the genome in our test set) **lacks detectable orthologs to all four archaeal markers**. UniProt has zero doxD/doxA/tetH/sor entries for this species. Empirical BLAST shows best hits at 30% pident over <40% qcov — well below detection thresholds. This is consistent with Counts et al. 2021 / Willard et al. 2024 classifying S. acidocaldarius as a "limited" sulfur biooxidizer compared to other Sulfolobales. The DSM 639 reference genome simply does not encode the canonical Sulfolobales sulfur-oxidation gene complement.
- **Workaround**: For Sulfolobus acidocaldarius DSM 639 specifically, accept that aerobic_chemotrophic is the biologically correct primary cultivation mode given the gene content. Use `--temperature 75 --ph 3` (Phase 3.1 overrides) if you want to manually shift the recipe toward acidophilic conditions. For other Sulfolobales (Acidianus, Metallosphaera, Saccharolobus solfataricus, Sulfurisphaera tokodaii, Sulfuracidifex metallicus), Phase 3.2 markers will detect sulfur oxidation correctly when those organisms are encountered.
- **Cross-detection note**: Bacterial Acidithiobacillus has a TetH homolog that fires at 37.5%/87% qcov, biologically consistent with the published phenotype (tetrathionate hydrolysis activity is documented in Acidithiobacillus). This adds corroborating evidence to existing soxB-based detection, not a false positive.
- **Future fix**: Not needed for the test set as constituted. If a future test set adds *Acidianus brierleyi*, *Metallosphaera sedula*, or other Sulfolobales sulfur oxidizers, Phase 3.2 markers will detect them at thresholds tuned to the canonical references.

### E.7 DNRA detection — coverage IN PLACE Phase 3.4; canonical NrfA only

- **Affected organisms**: Wolinella succinogenes, Sulfurospirillum (Epsilonproteobacteria DNRA model organisms); facultative DNRA-capable Enterobacteriaceae (E. coli, Salmonella) and Pasteurellaceae; Desulfovibrio (sulfate-reducing + DNRA-capable Deltaproteobacteria).
- **Metabolism**: Dissimilatory nitrate reduction to ammonium (DNRA) via canonical NrfA pentaheme cytochrome c nitrite reductase.
- **Status (Phase 3.4)**: Coverage **IN PLACE** for canonical NrfA-based DNRA. Six verified UniProt references across 5 genera (Wolinella, Sulfurospirillum, Shewanella, Mannheimia, Salmonella, Desulfovibrio); 5 of 6 are Swiss-Prot reviewed. New `anaerobic_respiratory_dnra` capability with essential_marker = nrfA + diagnostic_marker_override at 65% pident → 0.65 confidence. New thermodynamic template (NO3- + formate → NH4+ + CO2). New recipe-composer dnra branch (KNO3 acceptor, sodium formate donor, anaerobic atmosphere) for obligate DNRA organisms. Phase 3.1 facultative-anaerobe rule extended to demote DNRA when aerobic_chemotrophic is strong (E. coli case).
- **Test-set verification**: D. vulgaris correctly stays sulfate reduction primary (DNRA flagged as alternative); E. coli correctly stays aerobic_chemotrophic primary (DNRA flagged); 23 other organisms unchanged. V12 score: zero changes (no obligate DNRA organism in test set).
- **Documented gap (divergent NrfA in some lineages)**: Empirical 26-genome scan with **CXXCK heme-motif analysis** identified 2 organisms with real divergent NrfA below the 65% pident threshold:
  - *Syntrophomonas wolfei* (NrfA at 34% pident; CFTCK active-site motif preserved) — Bacillota DNRA
  - *Geobacter sulfurreducens* (NrfA at 33% pident; CLTCK motif preserved) — Geobacteraceae DNRA
  - Both organisms classify correctly via other primary modes (syntrophic / iron reduction respectively); adding DNRA detection at the lower pident wouldn't change their primary cultivation mode but would risk NirB sulfite-reductase or other multi-heme-cytochrome cross-reactivity in untested submissions. Per Phase 1.5m / 3.3 conservative-thresholds-first discipline, divergent-NrfA detection is deferred.
- **Otr-family DNRA gap**: *Campylobacter jejuni* (test set) has a 540-aa multi-heme cytochrome c (5 CXXCH motifs, no CXXCK active-site Lys-axial heme) at 29.7% pident to canonical NrfA — this is a different enzyme architecture, likely Otr-family (octaheme nitrite reductase). C. jejuni's reported DNRA capability uses this non-NrfA enzyme. Phase 3.4 (nrfA-only scope) correctly excludes it. Future Phase 3 sub-phase candidate if Otr-based DNRA detection becomes important.
- **Future fix (if needed)**: Paired nrfA + nrfH operon-marker logic with relaxed pident threshold (~30-40%) and co-occurrence requirement. nrfH is the small (~150 aa) tetraheme cytochrome c quinol-dehydrogenase membrane partner, co-encoded with nrfA in the canonical DNRA operon. Requiring both markers above threshold would catch divergent NrfA without elevated NirB/Otr false-positive risk. Reserved as Phase 3 enhancement option.
- **References**: `data/diagnostic_markers/dnra_review.md` (literature review + heme-motif analysis); REFERENCE_CURATION.md "Marker: nrfA (Phase 3.4)" section.

---

## Category F: Detector-side limitations (surfaced Phase 1.5m V9)

Limitations where the marker BLAST signal is correct but the capability detector demotes or misroutes the call. These are scoped for Phase 1.5n and do not require additional reference work.

### F.1 BLAST-positive markers demoted by missing gapseq pathway annotation — RESOLVED Phase 1.5n for the 3 target metabolisms

- **Status (post-Phase-1.5n)**: RESOLVED for organohalide_respiration, anoxygenic_phototrophy_purple, and bacteriorhodopsin. The `diagnostic_marker_override` rule (added to pathway_definitions.json) lets the diagnostic marker BLAST hit alone drive detection when pathway-based scoring fails. The override fires conditionally: only when `not detected_via_pathway`, no negative marker fired, no essential marker missing, and the marker hit clears override-specific thresholds. Produces moderate confidence (0.60-0.65), annotated with `uncertainty_flags = ["detected_via_marker_override"]`.
- **V10 verification**: Dehalococcoides reductive dehalogenation (0.125 → 0.650 PRIMARY), Chloroflexus phototrophy purple (0.025 → 0.650 PRIMARY), Halobacterium bacteriorhodopsin (0.225 → 0.600 PRIMARY). Zero regressions on the other 23 organisms. Cross-contamination check passed (rdhA `min_pident` tightened from 30 to 34 to exclude Prometheoarchaeum's single rdhA-superfamily homolog).
- **Residual scope**: F.1 may still apply to other metabolisms not addressed in this phase (e.g., metabolisms with diagnostic markers that share homology with non-pathway proteins). When evaluating new metabolisms, decide whether the diagnostic marker is *unique* to the pathway before adding the override. If the marker has multiple known functions (e.g., generic cytochrome c oxidases), pathway-integrity scoring should remain the primary signal.
- **Original notes (V9 state, retained for context)**:
  - Halobacterium salinarum × rhodopsin (52% identity, bs=212) — capability previously demoted because retinal/carotenoid biosynthesis pathways were `predicted=0` in gapseq output. Override now fires.
  - Chloroflexus aurantiacus × pufLM (47.8% identity, bs=246, 10 hits) — capability previously demoted because Chloroflexus uses FAP-style architecture (chlorosomes, 3HP cycle) rather than purple-bacteria pathway annotations. Override now fires.
  - Dehalococcoides mccartyi × rdhA (35.3% identity, multiple paralogs) — capability previously demoted because gapseq lacks a `reductive dehalogenation` pathway annotation for D. mccartyi (the V9 regression caused by Phase 1.5m's removal of D. mccartyi's own rdhA from references). Override now fires at 35.3% identity to non-self refs.

### F.2 ANME reverse-Wood-Ljungdahl direction not represented as a capability — RESOLVED Phase 3.6

- **Affected organisms**: Methanoperedens nitroreducens, ANME-1, ANME-2, ANME-3 clades
- **Metabolism**: Reverse methanogenesis with Wood-Ljungdahl carbonyl branch (anaerobic methane oxidation coupled to nitrate / sulfate reduction)
- **Status**: RESOLVED Phase 3.6. New `anme_reverse_methanogenesis` capability fires when `mcrA + (gapseq nitrate-reduction-pwy ≥100% OR dsrAB OR mtrC_omcB)` is satisfied. Mode picker routes the genome to `_compose_anme_recipe` (CH4:N2 80:20 atmosphere + acceptor-aware ingredient selection). The signature is implemented via the new **`essential_marker_OR` framework extension** — see C.1 for architectural detail. F.2 is the detector-side complement to C.1; both are now resolved together.
- **Architectural side-effect (intentionally retained)**: The acetogenesis pathway still uses `negative_markers: [mcrA, dsrAB, aprAB, mtrC_omcB]` so Methanoperedens does not also light up an acetogenesis call. The reverse-WL operation in ANME is represented as the dedicated `anme_reverse_methanogenesis` capability rather than as a directional reinterpretation of the existing acetogenesis call.

### F.3 Spurious capability calls from gapseq pathway annotation alone

- **Affected organisms / capabilities (V9 examples)**:
  - Prometheoarchaeum syntrophicum × Methanogenesis (0.900 confidence) — Asgard archaeon with NO mcrA hit but gapseq annotates a complete methanogenesis-like pathway (these are ancestral genes used for syntrophic propionate oxidation).
  - Nitrospira moscoviensis × Acetogenesis (0.605) — comammox bacterium called as acetogen via gapseq pathway annotation of CO2 fixation enzymes.
  - Chloroflexus aurantiacus × Sulfur oxidation (0.506) — FAP phototroph called as sulfur oxidizer via cross-reactive soxB-family hits.
- **Symptom**: Capability fires as primary on organisms where the gene-content matches the pathway but the metabolism is not actually expressed.
- **Root cause**: Gapseq pathway integrity is one of the dominant terms in the confidence formula. When gapseq annotates ancestral or functionally-repurposed genes as complete pathways, the capability is promoted regardless of biological context. Diagnostic markers (which would discriminate) don't fire on these organisms — but the absence of markers is not penalized.
- **Severity**: Moderate — affects blind-set partial assessments more than dev-set primary calls. The recipe composer would over-list capabilities.
- **Future fix (Phase 1.5n)**: Tighten pathway-integrity scoring to require positive support from at least one diagnostic marker for capability promotion above 0.50 confidence (i.e., `pathway_score > 0.7` AND `at_least_one_diagnostic_marker_above_threshold` to clear primary status). Or: require multi-evidence corroboration (transporters + cofactors + markers + pathway) before promoting any capability above 0.50.

---

## Category G: Phase 2d external-validation metric limitations

These limitations affect the V11 published-media comparison numeric scores
(see `RECIPE_VALIDATION_V11.md`). They do not affect the underlying recipe
correctness — Phase 2c (RECIPE_EVALUATION.md) established that 21/26 recipes
are biologically reasonable, and Phase 2d's structured diff output is the
actionable deliverable. The agreement score is a triage signal with caveats.

### G.1 GenomeSPOT temperature mispredictions — RESOLVED Phase 2e

- **Status**: RESOLVED. `derive_recipe_context._derive_conditions()` now uses TEMPURA-first priority for both temperature and pH, with a new `_lookup_tempura()` helper that performs species-name fallback (genus reclassification synonyms + `Candidatus` stripping) when the genome-organism linkage is NULL — which it is for 14 of the 26 dev/blind genomes. After the fix, recipe temperatures are TEMPURA-derived for: Methanococcus jannaschii (85°C via Methanocaldococcus synonym), Halobacterium salinarum (50°C), Picrophilus torridus (60°C), Thermotoga maritima (80°C), Chloroflexus aurantiacus (56°C). A subtle parallel bug in `recipe_comparison._check_cultivation_conditions` was also fixed: previously the species lookup there fell back from `species = "Methanococcus jannaschii"` to `species LIKE "Methanococcus %"`, picking up mesophilic sister species and falsely flagging the 85°C TEMPURA-derived recipe as off. Same synonym map now applied.
- **Residual scope**: Lactobacillus plantarum and Campylobacter jejuni are NOT in TEMPURA at all, so the GenomeSPOT prediction (18.8°C / 24.5°C) remains. These represent a different problem (TEMPURA coverage gap, not condition-priority bug) and would need either GenomeSPOT retraining or a third data source (e.g., BacDive culture-temp records — currently used only for the metric's reference check, not the recipe composer).
- **User-accessible workaround (Phase 3.1)**: `cultureforge inspect <genome> --temperature <°C> [--ph <value>] [--salinity <g/L>]` lets users supply known-good conditions directly. The override path bypasses TEMPURA/GenomeSPOT for the specified field and labels the recipe `USER OVERRIDES APPLIED:`. This converts the residual GenomeSPOT-calibration issue from a tool-blocking limitation into a user-accessible feature for novel organisms not in TEMPURA.
- **V12 score impact**: Halobacterium 30→50%, Thermotoga 19→55%, Chloroflexus 7→47%, Picrophilus 80→100%, Methanococcus 34→54%.

### G.2 Single-reference Jaccard structural brittleness

- **Affected organisms**: Organisms with only 1 published reference medium in MediaDive — *Acetobacterium woodii* (DSMZ 135 only), *Nitrosomonas europaea* (single ref), *Allochromatium vinosum* (Pfennig's medium only), *Nitrospira moscoviensis* (single ref), *Chloroflexus aurantiacus* (DSMZ 87 only), *Sulfurimonas denitrificans* (single ref).
- **Symptom**: Jaccard `|∩|/|∪|` scoring is harsh when n=1: every reference ingredient that CF doesn't have counts as a "miss" in the union denominator. Even when CF and the reference share their core biology, they often disagree on minor components (specific salts, vitamin solution naming) because the single reference medium reflects one lab's specific cultivation protocol, not a consensus.
- **Symptom (specific)**: Acetobacterium woodii recipe scores 4% despite the underlying recipe being a correct H₂/CO₂ acetogen recipe matching DSMZ 135 in mode + key components — the score is dragged down by Jaccard penalties on individual ingredients.
- **Root cause**: Jaccard is intrinsically brittle for small reference samples. The frequency-weighted high-frequency-consensus metric (used for n ≥ 3) doesn't have this problem because it focuses on the consensus subset rather than every distinct ingredient.
- **Severity**: The numeric score for these 6 organisms is misleading; it doesn't reflect biological correctness. The diff output (which ingredients agree, which don't) is informative regardless.
- **Workaround**: Read the diff output, not the aggregate score, for any organism where the inspector reports n=1 reference media.
- **Future fix**: Either expand MediaDive coverage by linking more BacDive strains to media (most n=1 organisms simply have only one DSMZ medium per species), or use a different scoring metric for low-n cases (e.g., weighted-overlap with strain-level domain-specific weights, or asymmetric Jaccard that doesn't penalize CF for missing reference-only ingredients with low biological importance).

### G.3 TEMPURA pH coverage is sparse — PARTIALLY RESOLVED Phase 2e

- **Status**: PARTIALLY RESOLVED. `recipe_comparison._lookup_bacdive_ph()` now extracts a representative culture-pH value from `bacdive_cache` records (parses `culture pH` field across dict / list / range-string variants; prefers `type=optimum` → `type=growth` → any positive entry). Wired as 2nd-priority pH source after TEMPURA in `_check_cultivation_conditions`.
- **Residual scope**: BacDive pH coverage in our local cache is genuinely sparse for the 26 organisms — only Halobacterium salinarum (median pH 7.25) and E. coli (median pH 8.5) produce parseable values, and neither >2 units off recipe. The architectural fix is in place, but data coverage remains the limiter for organisms like Picrophilus (BacDive cache rows for Picrophilus oshimae lack the `culture pH` field; the high-quality acidophile records the prompt anticipated are not in our cache).
- **Future fix**: A more complete BacDive download pass (current cache is 30,538 of ~100,000 BacDive strains) might increase coverage. Alternatively, scrape DSMZ medium PDFs for pH ranges as an additional source.
- **V12 score impact**: No score changes — the fix doesn't surface mismatches for this set, but is correctly architected for organisms whose BacDive records do carry pH.

### G.4 Atmosphere unstructured in MediaDive — RESOLVED Phase 2e

- **Status**: RESOLVED via BacDive supplement. `recipe_comparison._lookup_bacdive_atmosphere()` reads `Physiology and metabolism / oxygen tolerance` from `bacdive_cache` and returns the majority category (aerobic / anaerobic / microaerobic / facultative) across all matched strains. This is now the primary atmosphere reference; the medium-name heuristic falls back only when BacDive has no signal. 15 of 26 species in our set have BacDive oxygen-tolerance records. Facultative organisms match anything (no false positives on E. coli).
- **Bug fix included**: The category-mapping function had a substring bug (`"aerobe" in "anaerobe"` returns True), which was causing Methanococcus to be categorized aerobic via its `anaerobe` BacDive label. Fixed by checking anaerobic-first in the regex chain.
- **V12 score impact**: Campylobacter 50→30% (true-positive flag — CF recipe is aerobic but BacDive 37/39 strains are microaerobic; the recipe genuinely needs a microaerobic gas-phase fix). Methanococcus condition-check no longer false-flags atmosphere (atmospheric H2/CO2 anaerobic correctly matches BacDive anaerobe label).
- **Future fix**: For organisms not in BacDive (Candidatus lineages), a per-medium atmosphere curation from DSMZ PDF text would close the remaining gap.

---

## Uncharacterized risk areas

The following organism categories have NOT been tested against the detection
system and may contain unrecognized limitations:

### U.1 Deep subsurface and hadalpelagic organisms
- Ultra-low-energy metabolisms, potentially novel electron donors/acceptors
- Growth conditions may be extreme (high pressure, low temperature, minimal nutrients)
- GenomeSPOT and TEMPURA may not have relevant training data

### U.2 Truly uncultured MAGs (>20% phylogenetic distance from nearest cultured relative)
- Pathway annotations from gapseq become unreliable at large phylogenetic distances
- Novel metabolic pathways may not be in any reference database
- Risk of systematically wrong predictions for organisms from underexplored environments

### U.3 Asgard archaea beyond Prometheoarchaeum
- Lokiarchaeota, Thorarchaeota, Odinarchaeota, Heimdallarchaeota
- Eukaryotic-like features may confound annotation
- Energy metabolism poorly characterized; may require symbiotic partnerships

### U.4 Novel phyla (Candidatus lineages with no cultured representatives)
- CPR (Candidate Phyla Radiation), DPANN archaea
- Extremely small genomes with reduced metabolic capacity
- Likely obligate symbionts or parasites — recipe composition may be meaningless

### U.5 Electrochemically-active organisms
- Organisms using extracellular electron transfer mechanisms not captured by current pathway definitions
- Geobacter-type EET is partially covered but cable bacteria (Ca. Electrothrix, Ca. Electronema) and other novel EET mechanisms are not

---

## Recipe composer integration rules

The Phase 2c recipe composer should apply these rules when generating recipes:

1. **Category A organisms**: Refuse to compose a complete recipe. Output diagnostic explaining the limitation. Recommend Tier 2 structural analysis or manual expert review. Provide partial recipe for components that ARE reliably detected.

2. **Category B organisms**: Compose recipe but include uncertainty flag section. Note which components may be suboptimal and why. Suggest experimental variants that would cover the alternative.

3. **Category C organisms**: Compose recipe based on detected enzymes. Flag the directional ambiguity prominently in the output header. Provide alternative recipes for each plausible direction (e.g., "If methanogen: H2/CO2 headspace; If ANME: CH4 + electron acceptor").

4. **Category D organisms**: Compose recipe with placeholder for the ambiguous substrate. List all possible options ranked by literature prevalence for the organism's lineage.

5. **Category E organisms**: Cannot detect the limitation. The recipe may be silently wrong. Include a general confidence disclaimer: "This organism is from a lineage with limited marker coverage. If the organism fails to grow, consider Tier 2 analysis."

6. **Uncharacterized risk areas (U.x)**: Include phylogenetic distance warning when the nearest 16S match is <90% identity. Add "novel lineage" flag to the output.

---

## Future work

Limitations prioritized for resolution:

### Resolved by Phase 1.5n
- ✅ F.1 (BLAST-positive demoted) — three target metabolisms now use `diagnostic_marker_override` (Halobacterium rhodopsin, Chloroflexus pufLM, Dehalococcoides rdhA all detected as primary)

### Remaining detector-side work (Phase 3)
- F.2 — Add `ANME_reverse_methanogenesis` capability category (Methanoperedens reverse-WL still suppressed by mcrA negative-marker rule)
- F.3 — Tighten pathway-integrity scoring to require diagnostic-marker corroboration for capability promotion (Prometheoarchaeum spurious methanogenesis, Nitrospira spurious acetogenesis, Chloroflexus spurious sulfur_ox)
- Optional: lower rdhA pathway threshold OR add Thermus thermophilus full-length ba3 oxidase reference (sister-species rule allows; would close the Thermus terminal_oxidases qcov failure)

### Resolved by Phase 1.5l + 1.5m
- ✅ A.3 cyc2 reference (was barley Beclin-1 in V5; now 4 verified non-self iron-oxidation refs detecting A. ferrooxidans at 85.7% id)
- ✅ Sulfolobus terminal_oxidases regression (1.5l opened it via correct removal of Sulfolobus alcohol DH; 1.5m closed it via Saccharolobus solfataricus SoxB at 81.9% id)
- ✅ Campylobacter, Sulfurimonas terminal_oxidases coverage (1.5l MISS_FN; cbb3 added in 1.5m)
- ✅ Sulfurimonas autotrophy (rTCA aclA added in 1.5m)
- ✅ Wrong-protein contamination across ~50% of accessions (replaced + verified in 1.5l/1.5m)
- ✅ Self-validation contamination (D. vulgaris dsrAB, Allochromatium pufLM, A. ferrooxidans cyc2, Halobacterium rhodopsin, etc. — all removed in 1.5m)
- ✅ Dev-set vs blind-set test-set exclusion rule (enforced and audited in 1.5m)
- ✅ Dehalococcoides organohalide respiration (regression in V9 from test-set exclusion; restored in V10 via Phase 1.5n rdhA override at 35.3% identity)
- ✅ Chloroflexus FAP phototrophy primary detection (pufLM detection at 47.8% identity in V9 demoted by missing pathway; promoted in V10 via Phase 1.5n override)
- ✅ Halobacterium rhodopsin primary detection (BLAST positive at 52% identity in V9 demoted by missing retinal pathway; promoted in V10 via Phase 1.5n override)

### Near-term (Phase 3)
- Expand nosZ to include Clade II references (E.4)
- Expand mcrA with Methanomassiliicoccales representatives (E.2)
- Add vnfH and anfH nitrogenase references (B.1)

### Medium-term (Phase 3-4)
- Build substrate-class-specific rdhA HMMs (A.1 / D.1)
- Add neutrophilic iron oxidation pathway (mtoA/mtoB) (A.4)
- Add heliobacterial and Acidobacteria phototrophy markers (B.5)
- Expand iron reduction coverage beyond Geobacteraceae / Shewanella (D.2)
- Full-length comammox amoA references from genome assemblies (A.2 — explicitly deferred to Phase 3 per Checkpoint 2 user decision)

### Long-term (Phase 4+)
- ANME directional inference from phylogenetic placement (C.1 — biological complement to F.2 detector fix)
- Tier 2 structural analysis for all silent-failure organisms (E.x)
- GTDB-Tk integration for phylogenetic distance estimation (U.x)
- Scalindua-type detection — note that E.1 was reclassified in Phase 1.5m as a MAG-completeness issue; Tier 2 won't help if the gene is absent from predicted proteins. Resolution requires either better Scalindua profunda assembly or accepting un-detectability for incomplete MAGs.
