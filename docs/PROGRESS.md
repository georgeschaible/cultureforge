# CultureForge — Progress Log

Running record of what's built, validated, and outstanding. Update at the end
of every session. Cross-reference: see `CLAUDE.md` for the full architecture.

Last updated: 2026-05-02 (Phase 3.8 Part 1 COMPLETE: methanogenesis `diagnostic_marker_override` added — symmetric with the Phase 3.5+ override pattern (methanotrophy / DNRA / NOB). Override block on `mcrA` at min_pident=50, min_qcov=70, override_confidence=0.65. Empirical threshold verification: gid=8 Methanocaldococcus mcrA 83.7%, gid=28 Methanoperedens 70.1%, gid=903 Methanosarcina 100% — all fire; zero non-methanogen mcrA cross-reactivity in test set (only those 3 genomes have any mcrA hit). Verification: gid=903 Methanosarcina sentinel NOW classifies methanogenic primary (was escalated/no-primary in Phase 3.7 — closes the marker-only sentinel gap that surfaced in Phase 3.7). gid=8 Methanocaldococcus stays methanogenic primary at confidence 0.73 (gapseq path unchanged; override is additive). gid=28 Methanoperedens stays anme_reverse_methanogenic primary (Phase 3.6 priority ordering correctly supersedes methanogenesis at recipe time). V12 byte-identical to Phase 3.7 baseline across all 25 test organisms — the override is dormant for genomes that already have gapseq pathway data, only kicks in for marker-only sentinels. LIMITATIONS validation-status section updated: methanogenesis moved from "inferred from test-set behavior" to "validated against named-strain sentinel" (Methanosarcina acetivorans C2A). Phase 3.8 Part 2 (documentation polish — README rewrite, consolidated VALIDATION_REPORT, USER_GUIDE_LIMITATIONS, tester onboarding materials, PHASE_3_CLOSEOUT retrospective) follows.)

Earlier (2026-05-02): Phase 3.7 COMPLETE: empirical sentinel validation. Three new sentinel organisms loaded (gid=901-903, all marker-BLAST-only following the Phase 3.5 Methylococcus pattern; excluded from V12 by hardcoded ORGANISMS list): **Wolinella succinogenes DSM 1740 (gid=901, GCF_000196135.1)** validates Phase 3.4 DNRA — nrfA fires at 100% pident, anaerobic_respiratory_dnra primary, recipe matches DSMZ Medium 720 architecture (formate 20 mM + KNO3 15 mM + bicarbonate, anaerobic). **Nitrobacter winogradskyi Nb-255 (gid=902, GCF_000012725.1)** validates Phase 3.3 Type B clade arm — nxrA fires at 100% pident against Q3SQW5 (Type B self) and 96% against Q71RT9 (Type B Nitrobacter alkalicus), zero hits to Type A Nitrospira refs at 1e-30; lithotrophic_aerobic primary, recipe matches DSMZ Medium 756 (NaNO2 0.5 mM + NaHCO3 + phosphate pH 7.5, aerobic). **Methanosarcina acetivorans C2A (gid=903, GCF_000007345.1)** validates Phase 3.6 ANME false-positive prevention — mcrA at 100% pident plus full WL carbonyl branch (acsB_cdhC 92.8%, cooS_cdhA 91.7%) the strongest possible "looks like a methanogen" signal, but ANME OR-group correctly resolves all-negative (no dsrAB, no mtrC_omcB, no gapseq nitrate-pwy) → ANME capped at 0.40, false positive averted. Critical Phase 3.6 negative-control test PASSES decisively. Surfaced issues: (1) marker-only sentinels default to 30°C because TEMPURA/GenomeSPOT are not loaded — cosmetic, lightweight TEMPURA-lookup hook would resolve; (2) methanogenesis capability has no `diagnostic_marker_override` (unlike methanotrophy/DNRA/NOB), so marker-only sentinels can't fire methanogenic primary above 0.50 — Phase 3.8 candidate, symmetric with the Phase 3.5 methanotrophy override pattern. V12 validation byte-identical to Phase 3.6 baseline (sentinels properly excluded). Capability validation status now tagged **validated-against-sentinel** (methanotrophy, DNRA, NOB Type A+B, ANME-positive Methanoperedens, ANME-negative Methanosarcina+Methanocaldococcus) vs **inferred-from-test-set-only** (forward methanogenesis, sulfate/iron-coupled ANME, Phase 3.1/3.2 condition overrides + archaeal sulfur-ox markers). Total sentinels: 4 (gid=900 Methylococcus from 3.5 + gid=901-903 from 3.7). See data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md and per-sentinel validation.md files.)

Earlier (2026-05-01): Phase 3.6 COMPLETE: ANME directional mitigation. New `anme_reverse_methanogenesis` capability discriminates anaerobic methane oxidation from forward methanogenesis using `mcrA + (gapseq nitrate-reduction-pwy ≥100% complete OR dsrAB OR mtrC_omcB)` essential-marker logic. New **`essential_marker_OR` framework extension** in `capability_detectors.py` supports heterogeneous entries: marker-name strings AND pathway-pattern dicts (`{"type": "pathway_pattern", "pattern": "regex", "min_completeness": 100, "require_predicted": true}`). Pathway-pattern entries are explicitly a **fallback for divergent paralogs that escape curated-reference HMMER reach** — Methanoperedens napAB-like nitrate reductase has zero direct narG hits at evalue 1e-30 (best 24.5% pident at evalue 100), but gapseq's UniRef-based annotation cleanly catches 4 dissimilatory nitrate-reduction pathways at 100% completeness. Threshold (≥100% completeness + predicted=true) was empirically chosen against the test set: only Methanoperedens fires the (mcrA + nitrate pathway) signature; Methanocaldococcus has mcrA but ZERO nitrate-reduction pathways (correctly stays methanogenic). Pathway-pattern is NOT a convenience replacement for marker curation — it is the documented fallback when curated references can't reach divergent paralogs. New `_compose_anme_recipe` composer with acceptor-aware branching: nitrate (NaNO3 10 mM, ANME-2d/Methanoperedens, ΔG -517 kJ/mol), sulfate (Na2SO4 15 mM, ANME-1/2/3, ΔG -16.6 kJ/mol), iron (Fe(III) citrate 20 mM, fallback). Common substrate: CH4:N2 80:20 anaerobic atmosphere + Na2S reducing agent + NaHCO3 buffer + resazurin + static incubation + cultivation difficulty notice. New `anme` atmosphere category in `recipe_comparison.py` (CH4 without O2 → distinct from `methanotroph` CH4+O2); ANME treated as anaerobic-equivalent for BacDive comparison. Recipe-time mode picker: `anme_reverse_methanogenic` placed FIRST in `_SPECIFIC_MODES_PRIORITY` so methanogenic suppression happens via priority ordering rather than separate suppression rule. Cross-organism verification (26 test genomes): GID=28 Methanoperedens flips methanogenic→anme_reverse_methanogenic (ANME-2d, nitrate-coupled — correct); GID=8 Methanocaldococcus stays methanogenic (correct — has mcrA but no acceptor evidence; ANME capability capped at 0.40 by missing essential_marker_OR group); 24 other organisms unchanged. V12 validation: Methanoperedens **28% → 29%** (essentially flat — Methanoperedens has no direct DSMZ medium and falls back to functional-neighbor matching against 15 architecturally-mismatched mesophilic heterotroph references; the recipe is now biologically correct but the comparison set has no ANME-style references to match against). Methanocaldococcus 54% → 55% (noise, no regression). All other organism scores match V12 baseline within ±1 noise. LIMITATIONS F.2 (ANME directional ambiguity) marked RESOLVED for nitrate-coupled ANME-2d; sulfate-coupled ANME-1/2/3 architecturally supported but not in test set. C.1 (mcrA bidirectionality) RESOLVED. See `data/diagnostic_markers/anme_review.md` and `REFERENCE_CURATION.md` narG curation methodology note.)

Earlier (2026-05-01): Phase 3.5 COMPLETE: aerobic methanotrophy via pmoA + mmoX OR-logic. New `aerobic_methanotrophy` capability + 6 pmoA references (3-clade architecture — Type I × 2, Type II × 2, Type III Verrucomicrobia × 2) + 4 mmoX references (Type I + II; mmoX has 82-99% intra-family conservation). 2 Swiss-Prot reviewed (Methylococcus capsulatus pmoA Q607G3, mmoX P22869, Methylosinus trichosporium mmoX P27353); 8 TrEMBL across 7 distinct methanotroph genera. Test-set exclusion: no Nitrosomonas amoA in pmoA refs (the critical paralogy concern). Empirical pmoA × amoA cross-reactivity scan confirmed 8-10 point pident gap: amoA ceiling = 50% (Nitrosomonas), pmoA cross-Type-I-II floor = 58-60%; **60% pident threshold cleanly separates** without negative-marker logic. mmoX threshold 50% (zero cross-reactivity in test set). New methanotroph recipe composer: air+CH4 80:20 gas phase, phosphate buffer pH 7, NH4Cl nitrogen, SL-10 + Wolin's vitamins (with copper supplementation note), no reducing agent, vigorous shaking 200 rpm. New thermodynamic template `methanotrophic` (CH4 + 2 O2 → CO2 + 2 H2O, ΔG = -820 kJ/mol). New "methanotroph" atmosphere category. Sentinel validation against Methylococcus capsulatus Bath (GCF_000008325.1, downloaded from NCBI RefSeq, loaded as gid=900 with explicit "SENTINEL" prefix; excluded from V12 by validation script's hardcoded ORGANISMS list): pmoA fires at 100% pident, mmoX at 100%, methanotrophy capability at **0.80 confidence** (above 0.65 sentinel target), recipe produces methane-air gas phase + ΔG -820 kJ/mol feasibility, atmosphere correctly categorized as "methanotroph". End-to-end infrastructure verified. Cross-organism: zero false positives across 26 test organisms. V12 validation: byte-identical (no methanotroph in test set). LIMITATIONS A.10 marked RESOLVED for canonical Type I/II/III methanotrophs; N-DAMO and Methylacidiphilum-thermoacidophile-condition gaps documented for future sub-phases. See data/diagnostic_markers/methanotrophy_review.md and REFERENCE_CURATION.md.

Earlier (2026-05-01): Phase 3.4 COMPLETE — dissimilatory nitrate reduction to ammonium (DNRA) via nrfA. New `anaerobic_respiratory_dnra` capability + 6 verified nrfA references (5 Swiss-Prot reviewed + 1 TrEMBL across 5 genera: Wolinella, Sulfurospirillum, Shewanella, Mannheimia, Salmonella, Desulfovibrio). Test-set exclusion enforced (no E. coli P0ABK9, no Nitratidesulfovibrio Q72EF3, no Campylobacter). Wrong-protein traps caught: O33732 was suggested by prompt as Sulfurospirillum nrfA but UniProt confirms Shewanella frigidimarina nitrate reductase — replaced with verified Q9Z4P4. **Heme-motif analysis (CXXCK active-site Lys-coordinated heme — the diagnostic NrfA signature)** classified borderline 30-34% pident hits empirically: Syntrophomonas (CXXCK preserved) = real divergent NrfA; Geobacter (CXXCK preserved) = real divergent NrfA; Campylobacter (CXXCK absent) = non-NrfA multi-heme cytochrome (likely Otr-family). Per user-confirmed conservative discipline: 65% pident threshold catches canonical NrfA cleanly; divergent-NrfA gap in Bacillota/Geobacteraceae documented as known limitation (those organisms classify correctly via other primary modes). Recipe composer extended: new `dnra` sub-mode in `_classify_anaerobic_subtype` (now confidence-aware to handle multi-capability cases like D. vulgaris which has both dsrAB AND nrfA — sulfate reduction wins by higher confidence); new dnra branch in `_compose_anaerobic_respiratory_recipe` (KNO3 15 mM acceptor, sodium formate 20 mM donor, anaerobic atmosphere); new thermodynamic template (NO3- + formate → NH4+ + CO2, ΔG -598 kJ/mol). Phase 3.1 facultative-anaerobe rule extended: when only DNRA fires under anaerobic_respiratory mode and aerobic_chemotrophic conf ≥ 0.60, demote anaerobic_respiratory and let aerobic primary win (E. coli case). Cross-organism verification: D. vulgaris stays sulfate reduction primary (DNRA flagged); E. coli stays aerobic_chemotrophic primary (DNRA flagged); Scalindua flips fermentative→DNRA (both biologically wrong — Scalindua MAG has 99.8% pident to Salmonella nrfA, classic Enterobacteriaceae contamination of Brocadiaceae MAG, documented as E.1 addendum); 23 other organisms identical. V12 validation re-run: zero score changes across all 26 organisms. See data/diagnostic_markers/dnra_review.md and REFERENCE_CURATION.md.)

Earlier (2026-05-01): Phase 3.3 COMPLETE — canonical aerobic nitrite oxidation detection. New `lithotrophic_aerobic_nitrite` capability + 8 verified nxrA references (3 Nitrospira + 2 Nitrobacter + 2 Nitrotoga + 1 Nitrolancea, all TrEMBL — UniProt has no Swiss-Prot reviewed nxrA). Empirical narG cross-reactivity assessment confirmed a 39-point pident gap between cross-reactive false positives (max 48% — narG/narGHI in Methanoperedens / E. coli / Scalindua / Lactobacillus) and intra-clade NOB true positives (87% floor); 75% pident / 80% qcov threshold discriminates cleanly. Single-marker logic suffices; paired nxrAB not needed. Pathway definition uses `essential_marker=nxrA` to cap confidence at 0.40 when marker absent (gapseq EC annotations overlap with denitrification, otherwise 0.52 spurious detection). New `_compose_lithotrophic_aerobic_recipe` nitrite branch routes Nitrospira moscoviensis to aerobic atmosphere + NaNO2 0.5 mM (with toxicity warning) + NaHCO3 2.5 g/L + phosphate buffer pH 7.5 + standard trace metals/vitamins + no reducing agent. New thermodynamic template `lithotrophic_aerobic_nitrite` (NO2- + 0.5 O2 → NO3-; ΔG = -74 kJ/mol). Cross-organism verification: only Nitrospira changes; all 25 others retain identical primary mode. **V12 score essentially flat (20% → 19%) — but recipe now biologically correct** (was acetogenic/H2-CO2/39°C/pH 7; now lithotrophic/NaNO2/NaHCO3/39°C/pH 7.5 matching DSMZ Medium 2399 architecture). The flat score reflects pre-existing single-reference Jaccard brittleness (LIMITATIONS G.2) + ingredient-name normalization gaps (DSMZ 756d lists individual SL-10 components; CF aggregates) — not Phase 3.3 issues. Forward-compatible: the nxrA+amoA combination distinguishes comammox from canonical NOB; comammox amoA is deferred to a future sub-phase since no comammox organism exists in the test set. See data/diagnostic_markers/nitrite_oxidation_review.md and REFERENCE_CURATION.md.)

Earlier (2026-04-30): Phase 3.2 COMPLETE — archaeal sulfur oxidation markers added (tqoDoxD, tqoDoxA, tetH, sor; 15 verified accessions across 4 genera). Pathway `sulfur_oxidation` extended; no framework changes. Sulfolobus DSM 639 honest finding: genuinely lacks the canonical Sulfolobales sulfur-ox enzymes per Counts/Willard literature. V12 unchanged.

Earlier (2026-04-30): Phase 3.1 COMPLETE — manual cultivation-condition override flags `--temperature`, `--ph`, `--salinity` added to `cultureforge inspect`. Range-validated. Overrides thread through `derive_recipe_context` and `compose_recipe`. Default behavior unchanged.

Earlier (2026-04-30): Phase 2e COMPLETE — integration cleanup. G.1 condition priority swapped to TEMPURA-first with species-name fallback (5 recipes substantially more accurate); JSON output `published_media_comparison` promoted to top-level; G.3 BacDive culture-pH supplement; G.4 BacDive oxygen-tolerance now drives atmosphere check.

Earlier (2026-04-28): Phase 2d COMPLETE — MediaDive/BacDive consistency layer integrated with cache-primary architecture. 26/26 organisms produce comparison reports (20 direct + 6 functional-neighbor). 7/26 organisms ≥70% agreement post-Path-2(c) calibration; metric diagnostic, not pass/fail.

Earlier (2026-04-27): Phase 1.5l-1.5n complete. Phase 1.5l verified marker references; Phase 1.5m enforced 26-organism dev+blind exclusion across all 23 markers; Phase 1.5n added diagnostic_marker_override for 3 Category-F.1 metabolisms.

---

## Phase 1 — Data Foundation

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| MediaDive media + recipes | ✅ done | 3,336 media, 1,211 compounds, 61,335 medium-compound rows. Source: `data/mediadive/` (3,336 detail JSONs + 2,705 strain-mapping JSONs). Loader: `download_mediadive.py`, `download_medium_strains.py`, `build_database.py`. |
| BacDive strain detail | ✅ substantially complete | 30,538 / ~37,000 medium-linked strains downloaded (82%). Background download finished session 13. Source: `data/bacdive/strains/`. Loader: `download_bacdive.py`. |
| TEMPURA growth temperatures | ✅ done | 8,639 strains (CC BY-NC 3.0). 1,136 matched existing organisms by NCBI tax ID, 4,890 by species name, 2,612 inserted as TEMPURA-only. Loader: `integrate_tempura.py`. After merge: 9,146 organisms now have `optimal_temp`, 8,633 have min/max range. |
| Unified SQLite DB | ✅ done | `data/cultureforge.db`. Schema: `media`, `compounds`, `media_compounds`, `organisms`, `organism_media`, plus genome tables (see Phase 2). |
| 16S reference + BLAST DB | ✅ done | 12,318 sequences total (9,651 from BacDive's 16S accessions + 2,667 from TEMPURA). Stored at `data/16s_reference.fasta`; BLAST DB at `data/blastdb/16s_ref.*`. Built by `fetch_16s_sequences.py` + `fetch_tempura_16s.py` + `build_blast_db.py`. |
| Phylogenetic matcher | ✅ done | `phylo_match.py`. Features: identity-based confidence flag (LOW/MODERATE/GOOD/HIGH), 4-class thermal scoring (psychro/meso/thermo/hyperthermo) with TEMPURA-derived T_opt, user environmental overrides (`--temperature`, `--ph`, `--salinity`), genus + family fallback for media (uses derive-genus-from-species for organisms with NULL `genus` column). |

### Not yet started

| Component | Phase | Why we'll need it |
|---|---|---|
| BRENDA enzyme cofactor data | 1 | Validates cofactor/metal predictions from MeBiPred + provides cofactor lookup for annotated enzymes. |
| ProTraits carbon source utilization | 1 | Cross-reference for predicted carbon sources from gapseq. |
| Amend & Shock thermodynamic tables | 1 (per addendum) | Verify metabolic viability at user T/P/composition before designing media. 307 compounds + 370 reactions to digitize. |

---

## Phase 2 — Metabolic Intelligence (started)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| gapseq install | ✅ done | Conda env `gapseq` (gapseq 1.4.0, R 4.5.3, BLAST 2.17.0, exonerate, barrnap 0.9, HMMER 3.4). All 3 self-tests passed. |
| gapseq pipeline runner | ✅ done | `run_gapseq_ecoli.sh` — runs `find -p all` → `find-transport` → `draft` → `fill`. Total runtime on E. coli: ~3 hr (find dominates at 2.4 hr). Outputs go to `data/gapseq/<organism>/`. |
| gapseq schema + loader | ✅ done | `load_gapseq.py`. Tables: `genomes`, `genome_pathways`, `genome_transporters`, `essential_compounds` (32 reference compounds with anchored LIKE patterns). View: `genome_auxotrophies` (derived; "no functional biosynthesis pathway" means auxotroph). Session 3: records per-pathway + per-transporter confidences through the confidence module. |
| GenomeSPOT | ✅ done | Installed in dedicated `genomespot` conda env (Python 3.11 + prodigal + scikit-learn 1.2.2). Source at `vendor/GenomeSPOT/`. Per-genome runtime ~3 sec after prodigal (~30 sec). Loader: `load_genomespot.py`. New table: `genome_growth_predictions`. E. coli K-12 predictions loaded: T_opt=30°C ±5.6, pH_opt=7.40 ±0.90, salinity_opt=2.28% ±2.0, oxygen=tolerant (p=0.71). Each prediction scored through confidence module (0.50-0.95 band per addendum). |
| MeBiPred | ✅ done | `pip install mymetal` in `genomespot` env (needed `SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True` and `tf_keras` for Keras 2 model-JSON compat). Predicts binding for 10 metals (Ca, Co, Cu, Fe, K, Mg, Mn, Na, Ni, Zn) — note: the CLAUDE.md addendum lists "10+" including Mo, but the trained model does not include Mo/W/V/Se. Runtime ~30 sec for 4,319 E. coli proteins. Runner: `run_mebipred.py`. Loader: `load_mebipred.py`. New tables: `protein_metal_binding` (43,190 rows) + `genome_metal_profile` (10 rows per genome). E. coli profile matches known biology: Mg 27.6% > Ca 19.8% > K 15.6% > Fe 15.4% > Na 14.9% > Ni 12.7% > Mn 11.5% > Zn 7.1% > Cu 6.0% > Co 3.3%. |
| Media Composition Synthesizer | ✅ done | `synthesize_media.py` — composes a tailored recipe by layering supplements onto a phylogenetic template rather than just recommending existing media. Pipeline: 16S → phylo relatives → pick top template → classify each template compound's role (base_salt / carbon_source / nitrogen_source / trace_metal / buffer / complex_source / amino_acid / vitamin / gelling_agent / etc.) → layer auxotrophy supplements not covered (direct or complex) → layer trace-metal salts for MeBiPred-strong metals not already in template → optional --energy-metabolism overlay for electron donor/acceptor sets → compose overall confidence via `combine("min", critical_components, agreement_bonus=True)` → emit variation matrix for uncertain components → persist to `predictions` + `recipe_components` tables. |
| Reaction Energetics Engine | ✅ done | `thermodynamics.py` module: `thermodynamic_compounds` + `metabolic_reactions` tables, `interpolate_dg()` (piecewise linear across 12 reference temperatures 2-200°C), `dg_standard_reaction()` (interpolates pre-tabulated ΔG°r OR falls back to summing compound ΔG°f with stoichiometry), `delta_gr()` (Nernst-style ΔGr = ΔG°r + R·T·ln(Qr) with activity-aware corrections), `viability()` classifier (viable / marginal / not_viable per addendum 1 thresholds). TSV loader `load_thermodynamics.py` (DictReader-based). Data digitized from Amend & Shock 2001 PDF: **63 compounds** (Tables 4.1, 5.1, 6.1, 7.1 spanning H-O, H-O-N, H-O-S, H-O-C systems) + **44 reactions** (Tables 4.2/4.3, 5.2/5.3, 6.2/6.3, 7.2/7.3). Digitization performed by PDF text extraction (pdfplumber) with OCR-artifact correction (minus-sign-as-"3" systematic fix). |
| Tier 1 prediction script | ✅ done | `predict_media.py` — full genome-input pipeline. Steps: barrnap 16S extraction → BLAST → gapseq lookup (DB) → auxotrophy + transporter retrieval → per-medium coverage analysis → ranked recommendations with supplement summary. Reuses `phylo_match.py` functions. |

### Validated

- **E. coli K-12 MG1655 (NC_000913.3)** — full gapseq run loaded. 1,922 pathways scanned, 550 predicted; 2,170 transporter entries; 1,173 gene products; biomass=Gram_neg; gap-filled growth rate 1.435/hr. Correctly classified as prototroph (0 auxotrophies). Top recommended media: Columbia Blood, Trypticase Soy Yeast Extract, Nutrient Agar.
- **L-lysine knockout simulation** — 5 lysine biosynthesis pathways set to predicted=0/comp=20 in a transaction. View correctly reports L-lysine as auxotrophic. All standard peptone-based media correctly cover lysine via complex sources (biologically accurate — peptones contain all 20 AAs).
- **Cobalamin (B12) knockout simulation** — correctly partitions media: animal-tissue extracts (meat extract, beef extract, yeast extract, BHI) cover B12; plant-derived media (CASO Agar, Trypticase Soy Broth, Trypto-Soya — pure casein/soy peptone) flag SUPPLEMENT REQUIRED. Biologically correct.
- **E. coli 16S → media** (16S-only matcher) — Top hit *E. coli* @ 100% identity, neighbors are Shigella/Salmonella/Citrobacter (correct). Top recommendation: Columbia Blood Medium (10/10 relatives use it).
- **Thermus aquaticus 16S → media** (16S-only, with `--temperature 70`) — Without TEMPURA: top hit was mesophilic Deinococcus at 82%. After TEMPURA + temperature override + genus fallback: top hits are 4 *Thermus* species at 94-96% identity, top recommendation is **THERMUS 162 MEDIUM** (the classic isolation medium).

### Not yet started

| Component | Phase | Why we'll need it |
|---|---|---|
| GenomeSPOT growth condition prediction | 2 | Replaces user-supplied `--temperature`/`--ph`/`--salinity` with genome-derived predictions; provides a second opinion that combines with TEMPURA via the confidence framework. |
| MeBiPred metal binding | 2 (per addendum) | Trace metal requirements (Zn/Fe/Mn/Cu/Co/Mo/Ni/W/Se/V) from genome — currently we have zero metal-binding info in the recipe assembly. Critical for unusual metabolisms (e.g. Thermus aquaticus needs tungsten). |
| ESMFold + Foldseek (Tier 2) | 2 | Structure-based function recovery for hypothetical proteins flagged by gapseq. |
| Reaction Energetics Engine (Amend & Shock) | 2 (per addendum) | ΔGr viability check before recommending media for specific energy metabolisms. |
| Media Composition Synthesizer | 2 | Compose *novel* recipes by mixing components rather than only recommending existing media. CLAUDE.md calls this the "core innovation." Requires the confidence framework. |
| De novo synthesizer | ✅ done | `synthesize_denovo.py` — builds recipes from genomic evidence alone (no template). Decision tree: methanogen → SRB → iron reducer → sulfur oxidizer → ammonia oxidizer → denitrifier → microaerophile → aerobic heterotroph → fermenter. Uses gapseq pathways, reaction markers (terminal oxidases, catalase, hao), GenomeSPOT, MeBiPred. Concentration calibration from MediaDive (metabolism-specific medians). 10/10 classification accuracy. Session 18: carbon source gate, nitrogen options, atmosphere override, marine salinity. Session 18b: biological audit — multi-evidence autotrophy scoring (replaces hard metabolism-type gate), functional composition calibration (replaces taxonomy-proxy queries), oxidase-profile-primary atmosphere (replaces metabolism-type overrides). |
| Reaction marker loader | ✅ done | `load_gapseq.py:load_reaction_markers()` — scans gapseq all-Reactions.tbl for 7 marker reactions (bd oxidase, bo3 oxidase, cytc oxidase, cbb3 oxidase, catalase, hao, amo). Stores good_blast counts, best bitscore, complex_complete status in `genome_reaction_markers` table. |

---

## Confidence Framework — ✅ BUILT AND VALIDATED

Central module: `confidence.py`. API: `ConfidenceScore` dataclass, `score()`, `combine()`, `explain()`, `category()`, `populate_source_table()`, `record()`. All 15 baseline sources from the addendum populated in the `source_confidence` table.

**Retrofitted components:**
- `phylo_match.py` — replaced LOW/MODERATE/GOOD/HIGH strings with continuous `ConfidenceScore` from `score("phylo_16s", "identity_pct", ...)`. Every BLAST hit now carries a `phylo_conf` attribute. Category plus numeric percentage shown in output.
- `load_gapseq.py` — records per-pathway (1,922 rows for E. coli) and per-transporter (2,170 rows) confidences in `prediction_confidences` table on load. Confidences now range from 0.20-0.95 for pathways and 0.59-0.95 for transporters (realistic spread).
- `predict_media.py` — recipe-level composition via `combine("min", [phylo, thermal, medium, coverage], agreement_bonus=True)`. Output now shows overall confidence category + per-component breakdown + ⚠ flags for components <0.75 + provenance block listing contributing tools + uncertainty recommendations.

**Unit tests** (`test_confidence.py`): 42 tests covering edge cases — empty lists, single score, all combine methods (min/mean/weighted_mean/independent), agreement bonus application, disagreement handling, DB idempotency, monotonic phylogenetic scoring. All pass.

**End-to-end validation** (`validate_confidence.py`) — 6/6 cases pass:
| Case | Input | Result | Criterion |
|---|---|---|---|
| 1 | E. coli K-12 (prototroph) | **90% [HIGH]** | ≥0.85 ✓ |
| 2 | Thermus aquaticus 16S + `--temperature 70` | **80% [HIGH]** | 0.75-0.90 ✓ |
| 3 | Synthetic novel 16S (~72% identity, 28% mutated) | **30% [LOW]** with Tier 2/3 recommendation | <0.60 and Tier rec ✓ |
| 4a | E. coli **without GenomeSPOT** (single-source thermal) | **70% [MEDIUM]** | ≤0.80 ✓ (capped by thermal = 0.70) |
| 4b | E. coli **with GenomeSPOT** (BacDive+GenomeSPOT agree) | **90% [HIGH]** | ≥0.80 ✓ (thermal 0.85 via 2-source agreement) |
| 5 | E. coli metal profile (Fe/Mg/Zn) | **95% [VERY HIGH]** | all three ≥0.80 ✓ |

Case 4 demonstrates the multi-source agreement rule: adding GenomeSPOT's 30°C prediction alongside BacDive's 30°C promotes thermal from 0.70 (single source) to 0.85 (two sources agree), promoting the overall verdict from MEDIUM to HIGH. E. coli is not in TEMPURA (extremophile-focused), so a 3-source-agreement test requires a thermophile genome — deferred.

Case 5 confirms the core bacterial metals (Fe, Mg, Zn) are all predicted at HIGH+ confidence for E. coli. The multi-protein boost (+0.10 for n_binding≥5) lifts every metal to 0.95, so for a prototrophic reference organism the metal profile is uniformly strong — discrimination is in the *fraction* and *n_binding* columns, not the confidence.

### Database tables added this session (session 2)

| Table/view | Rows | Purpose |
|---|---|---|
| `source_confidence` | 15 | Baseline reliability per data source |
| `prediction_confidences` | 4,092+ | Per-prediction log (session 2: 1,922 pathway + 2,170 transporter; session 3: +10 GenomeSPOT predictions for E. coli) |

### Database tables added session 3

| Table/view | Rows | Purpose |
|---|---|---|
| `genome_growth_predictions` | 10 | GenomeSPOT predictions for E. coli K-12 (T/pH/salinity/oxygen, each with error + novelty + warning + computed confidence) |

### Database tables added session 4

| Table/view | Rows | Purpose |
|---|---|---|
| `protein_metal_binding` | 43,190 | Per-protein × metal MeBiPred prediction (4,319 proteins × 10 metals for E. coli). Stores binding probability, above-threshold flag, high-confidence flag, and confidence. |
| `genome_metal_profile` | 10 | Aggregated per-genome metal profile (n_binding, n_high_confidence, max_probability, fraction_of_proteome, confidence, is_anomaly, anomaly_note, media_component, typical_concentration). Anomaly rule: fraction > typical ceiling OR max_p > 0.95 on rare metal (Cu/Co/Ni). |

### Database tables added session 5

| Table/view | Rows | Purpose |
|---|---|---|
| `predictions` | 1 | One row per synthesized recipe — genome_id, input_accession, template_media_id+name, overall_confidence, category, user overrides, energy_metabolism, n_components, n_uncertain, timestamp. |
| `recipe_components` | 15 | One row per compound in a synthesized recipe — prediction_id FK, component_name, compound_name, concentration, units, role, is_critical flag, component_confidence, confidence_source, uncertainty_flag, uncertainty_note. Per CLAUDE.md fix #5 from session 5 schema review. |

### Database tables added / populated session 7

| Table/view | Rows | Purpose |
|---|---|---|
| `thermodynamic_compounds` | 63 | Per CLAUDE.md Addendum 1 — ΔG°f (kJ/mol) at 12 reference temperatures 2-200°C for each compound. Covers H-O (10 compounds), H-O-N (13), H-O-S (27), H-O-C_inorganic (13) systems from Amend & Shock 2001 Tables 4.1/5.1/6.1/7.1. |
| `metabolic_reactions` | 44 | Per CLAUDE.md Addendum 1 — ΔG°r at 12 temperatures + stoichiometry JSON + known organisms. Covers 2 H-O, 11 H-O-N, 22 H-O-S, 9 H-O-C reactions from A&S Tables 4.2-7.3. |

### D. vulgaris Hildenborough end-to-end validation (session 8)

Full pipeline run on *Desulfovibrio (Nitratidesulfovibrio) vulgaris* Hildenborough (NC_002937.3, 3.57 Mbp, organism_id=4105 / DSM 644). This is a strict anaerobic sulfate reducer with [NiFe]-hydrogenases — a fundamentally different physiology from E. coli.

**Per-tool results:**

| Tool | Key prediction | Reality | Correct? |
|---|---|---|---|
| 16S phylo match | 99.8% identity to *N. vulgaris* | Direct hit ✓ | ✓ |
| GenomeSPOT | **oxygen: not tolerant (p=0.98)** | Strict anaerobe | ✓ |
| GenomeSPOT | T_opt 28.8°C | Real 30-37°C (within 1σ) | ✓ |
| GenomeSPOT | pH 7.3 | Real ~7.0-7.5 | ✓ |
| MeBiPred | **Fe 19.4%** (vs E. coli 15.4%) | Cytochrome c₃ + Fe-S clusters | ✓ |
| MeBiPred | **Ni 15.7% (anomaly flag)** | [NiFe]-hydrogenases | ✓ |
| gapseq | **10 auxotrophies** including L-serine (0%), thiamin B1, riboflavin B2, pyridoxal B6 | Known yeast-extract dependency | ✓ |
| gapseq | **H₂S as top produced metabolite** (0.83 mmol/gDW/hr) | Sulfate reducer → H₂S | ✓ |
| Thermodynamics | Sulfate reduction at 37°C: **ΔGr = −141.4 kJ/mol → VIABLE** | Well-characterised metabolism | ✓ |

**Synthesized recipe vs. Postgate Medium C (DSMZ #63):**

| Category | Result |
|---|---|
| Template picked | **DESULFOVIBRIO (POSTGATE) MEDIUM** — correct ✓ (phylogenetic match) |
| Base components (lactate, sulfate, MgSO₄, NH₄Cl, K₂HPO₄, yeast extract, CaCl₂, FeSO₄, resazurin, reducing agents) | **All 11 matched exactly** from template ✓ |
| 8/10 auxotrophies (amino acids + vitamins) | **Covered by yeast extract** (complex-source detection) ✓ |
| 2 auxotrophies NOT in template | **Heme + molybdopterin supplements added** at 0.65-0.72 confidence with variation matrix ⚠ |
| 5 trace metals added | NiCl₂ (hydrogenase), MnCl₂, ZnSO₄, CuSO₄, CoCl₂ — MeBiPred-driven |
| Energy overlay | Redundant +Na₂SO₄/lactate (template already has them) — harmless |
| Thermodynamic check | ΔGr = −141.4 kJ/mol ✓ VIABLE |
| Overall confidence | **MEDIUM (0.65)** — dragged down by the heme auxotrophy uncertainty (partial pathway 66%) |

**Assessment:** The synthesizer correctly reproduced Postgate Medium C as its base, identified the right organism-specific supplements, and added trace metals that modern trace element solutions (like SL-10) would provide. The confidence is appropriately conservative (MEDIUM) given the partial-pathway heme uncertainty — an experimentalist would see the variation matrix and test ±heme. The thermodynamic viability check confirms sulfate reduction is strongly exergonic at 37°C with realistic activities.

**Bugs found and fixed (session 9):**
1. **Stock concentration display** — MediaDive's `g_l` is per-sub-solution, not per-final-medium. FeSO₄ showed 50 g/L (stock) instead of 0.5 g/L (final). **Fixed:** synthesize_template_as_components now uses `amount` (grams per 1L total medium) when the unit is "g", falling back to `g_per_L` only for ml/other units. FeSO₄ now correctly shows 500 mg/L. Thioglycolate 100 mg/L. Ascorbic acid 100 mg/L.
2. **Energy overlay deduplication** — template already had Na-DL-lactate and Na₂SO₄ but the `--energy-metabolism sulfate-reduction` overlay re-added them. **Fixed:** `add_energy_metabolism_components` now checks existing compound names with both substring and word-level matching (catches "Na-DL-lactate" ↔ "Sodium lactate" via shared word "lactate"). D. vulgaris now shows 0 energy overlay components (correctly deduped).
3. **Cofactor concentration** — heme supplement defaulted to 500 mg/L (generic amino-acid level). Real hemin supplementation is 1-10 mg/L. **Fixed:** added `COFACTOR_CONCENTRATION_OVERRIDES` dict with biologically appropriate concentrations for 12 cofactors/vitamins (heme 5 mg/L, molybdopterin 1 mg/L, biotin 20 µg/L, B12 100 µg/L, etc.). Amino acid supplements also reduced from 500 mg/L to 50 mg/L.

### Thermodynamics validation (session 7)

| Reaction | ΔG°r at 25°C | Expected (A&S Table) | Status |
|---|---|---|---|
| **Knallgas** (H2(aq) + 0.5 O2(aq) → H2O(l)) | **−263.17 kJ/mol** | ≈ −263 | PASS |
| **Methanogenesis** (CO2(aq) + 4 H2(aq) → CH4(aq) + 2 H2O(l)) | **−193.73 kJ/mol** | ≈ −194 | PASS |
| **Sulfate reduction** (SO4²⁻ + 4 H2(aq) + 2 H⁺ → H2S(aq) + 4 H2O(l)) | −303.08 at 25°C (std state); **−90.05 at 100°C** with realistic activities (28 mM SO4, 10 μM H2, 0.1 mM H2S, pH 7) | N/A (Nernst demo) | Correct behavior: activity correction reduces |ΔGr| by ~225 kJ/mol from standard state |

### Synthesizer validation (E. coli K-12 MG1655)

| Scenario | Template | Layered additions | Overall | Behaviour |
|---|---|---|---|---|
| Real E. coli (prototroph) | COLUMBIA BLOOD MEDIUM | 5 trace-metal supplements (Ni, Mn, Zn, Cu, Co) | **90% [HIGH]** | Template has Fe via meat extract + Mg/Ca/K/Na via complex sources, but lacks direct salts for Ni/Mn/Zn/Cu/Co so those are added at MeBiPred-predicted concentrations. |
| Cobalamin knockout on COLUMBIA BLOOD | COLUMBIA BLOOD MEDIUM | 0 auxotrophy (B12 covered via meat extract) | **90% [HIGH]** | Complex-source check catches B12 via animal tissue → no supplement needed. Biologically correct. |
| Cobalamin knockout on CASO AGAR (plant peptones only) | CASO AGAR (Merck 105458) | **B12 supplement at 0.86 confidence** | HIGH | Plant peptones don't provide B12 → supplement added with variation-matrix entry. |
| `--energy-metabolism sulfate-reduction` | COLUMBIA BLOOD MEDIUM | Na2SO4 (e-acceptor) + Sodium lactate (e-donor) at 0.95 user_supplied confidence | — | Electron donor/acceptor overlay from CLAUDE.md reference table working. |

### Metal profile integration (session 4)

`predict_media.py` now includes a **PREDICTED METAL REQUIREMENTS** section per candidate genome, showing:
- Per-metal table: `n_bind`, `n_high_confidence` (p≥0.75), `max_probability`, `fraction_of_proteome`, composite confidence, canonical media component with concentration range
- "Strong metal requirements" summary (n_bind ≥ 5 AND max_p ≥ 0.75)
- Anomaly flags from `_check_anomaly`: fraction exceeding typical ceiling OR max_p > 0.95 on a rare metal (Cu/Co/Ni)
- Explicit note that MeBiPred cannot predict W/V/Se — organisms with unusual metabolism (tungsten-using hyperthermophilic methanogens, vanadium nitrogenases, selenoproteins) need BRENDA cross-reference (not yet integrated) to catch those

For E. coli specifically, every metal hits 0.95 confidence (multi-protein boost saturates the cap) and two gentle anomaly flags fire: Ni at 12.7% (slightly over the 10% ceiling; consistent with E. coli's [NiFe]-hydrogenases) and Cu/Co where max_p=1.00 on the rare-metal list. None concerning — they're essentially "look harder if you care" flags.

### Database tables added session 17

| Table | Rows | Purpose |
|---|---|---|
| `genome_reaction_markers` | 84 (7 markers × 12 genomes) | Gene-level detection of terminal oxidases (bd, bo3, cbb3, cytc), catalase, hao, amo from gapseq reaction tables. Primary signal: `complex_complete` (gapseq's multi-subunit assessment). |

### Thermal inference retrofit (session 3)

`phylo_match.infer_thermal_multisource(conn, hits, genome_id=None, user_temp=None)` is now the canonical thermal-class resolver. It:
1. Accepts `user_temp` as an override (→ 0.95 confidence)
2. Collects GenomeSPOT's `temperature_optimum` prediction (if genome loaded)
3. Collects TEMPURA / BacDive T_opt from the linked organism (with species-level fallback when the direct organism record is sparse)
4. Falls back to phylogenetic inference from relatives when no direct data exists (→ 0.70 single-source confidence)
5. Applies the addendum's agreement rules: all three → 0.95, two of three → 0.85, one → 0.70, disagreement → 0.50 + flag

`predict_media.py` now displays per-source thermal provenance ("Thermal class: MESOPHILE (~30°C, confidence 85%) [sources: GenomeSPOT=30°C, BacDive=30°C]").

---

## Tiered Compute — NOT STARTED

Current `predict_media.py` is conceptually Tier 1 (sequence + metabolic) but lacks GenomeSPOT, MeBiPred, BRENDA, thermodynamics, and recipe synthesizer. No tier flag yet (`--tier fast/standard/deep`). No `genome_analyses` cache table.

Tier 1 fast-mode latency target: ~5-15 min. Current bottleneck: gapseq find at ~2.4 hr per genome. Tier 2/3 (ESMFold/Foldseek/HHPred/AlphaFold2) not started.

---

## Database snapshot

| Table | Rows |
|---|---|
| `media` | 3,336 |
| `compounds` | 1,211 |
| `media_compounds` | 61,335 |
| `organisms` | 37,802 |
| `organism_media` | 55,193 |
| `organisms` with `optimal_temp` | 9,146 |
| `organisms` with min/max temp from TEMPURA | 8,633 |
| `genomes` | 12 (E. coli K-12, D. vulgaris + 10 validation organisms) |
| `genome_pathways` | 1,922 |
| `genome_transporters` | 2,170 |
| `essential_compounds` | 32 |
| `source_confidence` | 15 |
| `prediction_confidences` | 9,910 (+15 this session — one per recipe_component) |
| `genome_growth_predictions` | 10 |
| `protein_metal_binding` | 43,190 |
| `genome_metal_profile` | 10 |
| `predictions` | 1 |
| `recipe_components` | 15 |
| `thermodynamic_compounds` | 63 (from A&S 2001 Tables 4.1/5.1/6.1/7.1) |
| `metabolic_reactions` | 44 (from A&S 2001 Tables 4.2-4.3/5.2-5.3/6.2-6.3/7.2-7.3) |
| `genome_reaction_markers` | 84 (7 markers × 12 genomes) |
| 16S BLAST DB sequences | 12,318 |

---

## Known limitations

1. **BacDive only ~6.5% downloaded** (6,575 / ~100,000). Download was running in background and stopped; partial coverage means some genera are entirely missing 16S sequences.
2. **12 genomes with metabolic data** (E. coli, D. vulgaris + 10 validation organisms spanning 3 domains, 8 metabolic types, T range 22-85°C, pH range 2-7.5). Full validation results in VALIDATION_SUMMARY.md: template accuracy 70%, de novo energy metabolism classification 100% (10/10), thermodynamic viability 100%, temperature within ±10°C 80%. Remaining issue: GenomeSPOT misclassifies archaeal aerobes (Sulfolobus); microaerophile detection now working via gene-level terminal oxidase detection.
3. **gapseq is too slow for "fast" tier** (~3 hr per genome). The CLAUDE.md addendum acknowledges this and suggests pre-computing for common reference genomes, OR redefining Tier 1 as "same-day" rather than "coffee-break."
4. **Auxotrophy detection is heuristic** — pattern matching against MetaCyc pathway names. Anchored patterns work for the 32 essentials we curated, but adding new compounds requires curating a new pattern. No molecular formula or ChEBI ID matching yet.
5. **Coverage analysis uses substring matching on compound names**, not synonym resolution. A medium listing "vitamin B12" would be matched, but more obscure synonyms could be missed.
6. ~~**Phylogenetic-only confidence flags are discrete**~~ — resolved this session (continuous ConfidenceScore + propagation into recipe-level composition).
7. **No pH/temp drift correction** — the third addendum notes neutral pH shifts from 7.4 at 0°C to 5.6 at 200°C. We use literal pH values from MediaDive without temperature compensation.
8. **No ChEBI / molecular-formula compound identifiers** — `compounds` table has just `(id, name)`. CLAUDE.md schema calls for CAS, ChEBI, formula, MW.
9. **No predictions/experiments/feedback tables** — every prediction is recomputed from scratch, no learning from user-reported outcomes yet.

---

## File inventory

Everything lives at the project root (clone-relative paths used throughout).

**Data download / loaders:**
- `download_mediadive.py`, `download_medium_strains.py`, `download_bacdive.py`
- `fetch_16s_sequences.py`, `fetch_tempura_16s.py`, `build_blast_db.py`
- `integrate_tempura.py`, `build_database.py`
- `load_gapseq.py`

**Core modules:**
- `confidence.py` — central scoring framework (ConfidenceScore, score, combine, explain)

**Pipelines:**
- `phylo_match.py` — 16S → relatives → media (Tier 1, sequence-only). Retrofitted to confidence framework; adds `infer_thermal_multisource` for GenomeSPOT+TEMPURA+BacDive combination.
- `predict_media.py` — genome → relatives + auxotrophies + GenomeSPOT + media (Tier 1, full). Outputs per-component confidence, per-source thermal provenance, uncertainty flags.
- `load_gapseq.py` — loads pathway/transporter output, records confidences.
- `load_genomespot.py` — loads GenomeSPOT TSV, records per-prediction confidences.
- `run_mebipred.py` — runs MeBiPred predict() internals on a protein FASTA, emits per-protein × metal TSV.
- `load_mebipred.py` — loads MeBiPred TSV, builds genome metal profile with multi-protein boost per addendum 3.
- `synthesize_media.py` — Media Composition Synthesizer (template-based). Layers auxotrophy + metal + energy-metabolism supplements onto a phylogenetic template; runs thermodynamic viability check + precipitation compatibility scan; persists to `predictions` + `recipe_components`.
- `synthesize_denovo.py` — De Novo Media Synthesizer. Builds recipes from genomic evidence without templates. Decision tree energy metabolism classification using gapseq pathways + reaction markers. 10/10 validation accuracy.
- `media_constants.py` — Shared constants for both synthesizers (metal supplements, cofactors, buffer pH ranges, carbon source preferences, reducing agents, metabolism-taxonomy proxies).
- `compatibility.py` — Media Compatibility Engine (Tier A). 13 curated precipitation rules, severity-ranked warnings, auto-generated preparation instructions (Solution A/B/C breakdown).
- `carbon_and_gas.py` — Carbon source verification (gapseq pathway → substrate mapping, 40+ substrates) + gas phase recommendation (BLAST-confirmed hydrogenase classification + gapseq H₂ pathways → headspace composition).
- `media_format.py` — Physical format prediction (decision tree: solid/liquid/semi-solid/gradient/Hungate/gellan based on oxygen/flagella/temperature/pH).
- `thermodynamics.py` — Reaction Energetics Engine. Interpolation + Nernst ΔGr calculator + viability classifier. Loaded with 63 compounds + 44 reactions from Amend & Shock 2001.
- `load_thermodynamics.py` — DictReader-based TSV loader for A&S data. Two modes: `compounds` and `reactions`.
- `data/thermo/build_tsvs.py` — script that produced the compound/reaction TSVs from digitized A&S data.
- `data/thermo/compounds.tsv` — 63 rows (Tables 4.1, 5.1, 6.1, 7.1)
- `data/thermo/reactions.tsv` — 44 rows (Tables 4.2-4.3, 5.2-5.3, 6.2-6.3, 7.2-7.3)
- `run_gapseq_ecoli.sh` — gapseq orchestration script

**Tests & validation:**
- `test_confidence.py` — 42 unit tests (all pass)
- `test_thermodynamics.py` — 26 unit tests covering interpolation, persistence, Nernst math, viability classification, placeholder knallgas smoke test (all pass)
- `validate_confidence.py` — 6-case end-to-end validation (all pass, now includes MeBiPred metal profile sanity)
- Combined: **68 unit tests + 6 validation cases — all passing**

**External environments:**
- conda env `gapseq` — gapseq 1.4.0, R 4.5.3, BLAST 2.17.0, barrnap 0.9
- conda env `genomespot` — Python 3.11, prodigal, GenomeSPOT 1.0.1, MeBiPred 1.0.9 (pinned numpy<2, sklearn==1.2.2, tf_keras 2.21 for Keras 2 model compat)

**Data:**
- `data/cultureforge.db` (SQLite database)
- `data/mediadive/`, `data/bacdive/`, `data/tempura/`
- `data/genomes/ecoli_k12_mg1655.fasta`, `data/genomes/dvulgaris_hildenborough.fasta`
- `data/gapseq/dvulgaris/` (9 output files from gapseq 1.4.0)
- `data/genomespot/dvulgaris/`, `data/mebipred/dvulgaris/`
- `data/selective_inhibitors_database.csv` — 25 curated inhibitors (for future suppression feature)
- `data/hydrogenase/hydrogenase_refs.fasta` — 9 canonical hydrogenase catalytic subunit sequences ([NiFe] G1-G4, [FeFe] GA)
- `data/hydrogenase/{ecoli,dvulgaris}_hits.tsv` — BLAST results
- `data/validation/ecoli_full_report.txt` — complete synthesizer output for E. coli K-12 (151 lines)
- `data/validation/dvulgaris_full_report.txt` — complete synthesizer output for D. vulgaris Hildenborough with sulfate-reduction at 37°C (213 lines)
- `data/gapseq/ecoli/` (9 output files)
- `data/blastdb/16s_ref.*`
- `data/16s_reference.fasta`

---

## Next priorities (ordered)

Per CLAUDE.md addendum 3 (implementation order) + addendum 4 (CAZy/dbCAN + Hydrogenase suggested slot), current status:
1. ~~`confidence.py` module + retrofit existing components~~ — ✅ session 2
2. ~~GenomeSPOT integration~~ — ✅ session 3
3. ~~MeBiPred integration~~ — ✅ session 4
4. ~~Media Composition Synthesizer~~ — ✅ session 5
5. ~~Reaction Energetics Engine~~ — ✅ session 7. 63 compounds + 44 reactions from A&S 2001 Tables 4.1-7.3 digitized and loaded. Knallgas −263.17 kJ/mol at 25°C (PASS); methanogenesis −193.73 (PASS). Nernst calculator with activity corrections working. **Wired into synthesize_media.py** — when `--energy-metabolism` is specified, the synthesizer looks up the A&S reaction, computes ΔGr at the inferred growth temperature with default or user-supplied activities (`--activity SPECIES=VALUE`), and emits a THERMODYNAMIC VIABILITY section. If ΔGr > 0, a critical component at 0.25 confidence is injected and a −0.15 penalty applied to overall recipe confidence, driving the verdict to LOW. Validated: methanogenesis at 100°C VIABLE (−88 kJ/mol), at 150°C with 1e-8 H2 NOT VIABLE (+65.7), sulfate reduction at 55°C VIABLE (−135).
6. ~~CAZy/dbCAN integration~~ — ✅ session 11 (partial). dbCAN server (bcb.unl.edu) is down — all database downloads return HTML error pages. Built **gapseq pathway-based carbon source extraction** as alternative: `carbon_and_gas.py` maps gapseq degradation/utilization pathways to 40+ carbon substrates, verifies template carbon sources against the organism's predicted capabilities. New table: `genome_carbon_sources` (33 for E. coli, 18 for D. vulgaris). Wired into synthesizer: CARBON SOURCE ANALYSIS section. `genome_cazymes` table (per-gene CAZy family annotation) deferred until dbCAN server recovers.
7. ~~Hydrogenase Database integration~~ — ✅ session 11. Built 9-sequence reference FASTA from canonical [NiFe] Group 1-4 + [FeFe] Group A catalytic subunits (UniProt accessions from D. vulgaris, R. eutropha, Synechocystis, E. coli, Methanothermobacter, Methanosarcina, Clostridium). BLAST protein search against predicted proteomes. New table: `genome_hydrogenases`. Results: E. coli — 7 hits ([NiFe] G4 HycE at 100%id, G2, [FeFe] GA); D. vulgaris — 11 hits ([NiFe] G1 HynB at 100%id, G2, G4, [FeFe] GA×3). Gas phase recommendation wired into synthesizer: D. vulgaris → N₂:CO₂ (80:20) with H₂:CO₂ option; E. coli → aerobic (air).
8. ~~Media Compatibility / Precipitation Check~~ — ✅ Tier A (session 10). `compatibility.py`: 13 curated precipitation rules in `precipitation_rules` table (Fe-PO₄, Fe-S, Ca-CO₃, Ca-PO₄, Ca-SO₄, Mg-PO₄-NH₄, Mn-CO₃, Cu-S, Zn-S, Ni-S, Co-S, Fe(OH)₃). `check_compatibility()` scans recipe + implicit metabolic products (is_sulfidogenic adds H₂S). `generate_prep_instructions()` produces Solution A/B/C breakdown with order-of-addition. Wired into `synthesize_media.py` — runs automatically after recipe composition; adds COMPATIBILITY WARNINGS section + PREPARATION INSTRUCTIONS. Confidence penalty: HIGH −0.10, multiple HIGH −0.15, MEDIUM −0.05. Validated: D. vulgaris flags 6 HIGH + 1 MEDIUM + 1 LOW (Fe-PO₄, FeS, CuS, ZnS, NiS, CoS, Ca-PO₄, CaSO₄); E. coli flags only 1 MEDIUM + 1 LOW. Tier B (PHREEQC) deferred.
9. ~~Physical Media Format Prediction~~ — ✅ session 11. `media_format.py`: decision tree from CLAUDE.md addendum 5. Uses GenomeSPOT oxygen prediction + gapseq pathway annotations (flagella, chemotaxis, sulfide/iron oxidation, carbon diversity). Recommends format (liquid/solid/semi-solid/gradient/Hungate), solidifying agent (agar vs gellan gum for thermophiles/acidophiles), and flags strict-anaerobe handling. Wired into synthesizer: PHYSICAL FORMAT section. Validated: E. coli → solid agar plates (0.85 conf); D. vulgaris → Hungate/Balch tubes (0.90 conf) with strict-anaerobe warning. Bug fix: SRBs with reverse sulfide-oxidation genes no longer get gradient-tube recommendation.
10. **BRENDA inhibitor data** (for selective suppression feature from addendum 3). Unlocks the rare-metal detection (Mo/W/V/Se) that MeBiPred can't do. Curated selective inhibitors CSV (25 entries) already copied to `data/selective_inhibitors_database.csv`.
9. **SILVA integration** (expand 16S reference beyond BacDive-linked strains). Our current BLAST DB holds 12,318 sequences — every one is tied to a BacDive strain with cultivation data. SILVA adds ~2M curated rRNA sequences including large coverage of **uncultivated** lineages (candidate phyla, MAGs, environmental clones) that the BacDive-anchored DB cannot see. For truly novel queries (e.g. the Case 3 validation, <80% identity to anything), SILVA would put the organism into a concrete phylogenetic context — "closest to the SILVA record for uncultivated candidate phylum X" — upgrading a pure LOW score into a placed-but-uncultivated signal that can then be routed into Tier 2/3 structural analysis. Deferred because: (a) a SILVA hit alone doesn't yield a recipe — SILVA carries no media data, so its value is mostly as a *classifier* that tells the pipeline whether to trust phylogenetic inference or escalate to structure-based methods; (b) the synthesizer and metabolic/metal predictors all directly improve *recipe quality* for organisms we already place, which is the larger immediate win; (c) once Tier 2 (ESMFold+Foldseek) lands, SILVA's "uncultivated cousin" classification becomes the trigger for that structural fallback — so pairing the two is natural.
10. **Tier 2** (ESMFold + Foldseek for hypothetical proteins)
11. **Tier system wrapper** (`--tier fast/standard/deep`)
12. **Selective Suppression feature** (per addendum 3; depends on BRENDA + synthesizer)

Independent infrastructure work (parallel):
- BacDive download is running again (7,830 / ~37,000); check progress next session
- Run gapseq on validation genomes (Thermus aquaticus, Methanococcus, Desulfovibrio) — each ~3 hr
- Add ChEBI/CAS/formula columns to `compounds` table for better synonym resolution

---

## Phase 2c — Recipe Composer (2026-04-28)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| Recipe schema (`recipe.py`) | ✅ done | Recipe + Ingredient + GasPhase + IncubationConditions + ThermodynamicCheck dataclasses. Every ingredient carries rationale + confidence + derived_from for full evidence trail. |
| Composer (`compose_recipe.py`) | ✅ done | 9 mode-specific composer functions (methanogenic, aerobic_chemotrophic, anaerobic_respiratory, phototrophic, fermentative, lithotrophic_aerobic, acetogenic, syntrophic, halophilic_with_rhodopsin) + common-basal helper (SL-10 trace metals, Wolin's vitamins, phosphate/PIPES buffer, baseline salts) + mode-specific adjustments. |
| Specificity-aware mode picker | ✅ done | `_pick_primary_mode_for_recipe`: prefers specific modes (lithotrophic, halophilic, methanogenic, etc.) over generic (aerobic_chemotrophic, fermentative). Critical for Acidithiobacillus, Halobacterium, Allochromatium routing. |
| Sub-mode classifier with capability profile | ✅ done | `_classify_anaerobic_subtype` queries CapabilityProfile directly to see capability names like "Reductive dehalogenation"; correctly routes Dehalococcoides to organohalide branch (not sulfate). |
| Autotrophic carbon source filter | ✅ done | `_filter_carbon_sources_for_mode` suppresses spurious organic carbon for obligate-autotroph modes (lithotrophic, methanogenic, acetogenic). |
| F.3 mitigation (diagnostic-marker corroboration) | ✅ done | Marker-required modes (methanogenic, acetogenic, lithotrophic, phototrophic, halophilic) only win priority if their underlying capability has a diagnostic_markers_hit entry. Demotes spurious gapseq-pathway-only calls (Chloroflexus acetogenic → phototrophic; Prometheoarchaeum methanogenic → syntrophic). |
| Thermodynamic gating | ✅ done | Reaction templates per cultivation mode with delta_g_standard at 25°C; ΔG > 0 escalates to ESCALATE_STRUCTURAL (except syntrophic, which is conditionally feasible with partner). |
| LIMITATIONS.md flag mapping | ✅ done | A.1/D.1 (organohalide substrate), A.2 (comammox amoA), C.1 (ANME directional), C.2 (reverse-dsr), E.1 (Scalindua MAG completeness), F.1 (override) all auto-flagged. |
| Inspector Section 10 | ✅ done | `cultureforge inspect <genome> --section recipe` renders gas phase, conditions, ingredients (categorized), thermodynamic check, uncertainty flags, limitations, overall confidence. JSON output includes `recipe` field. |
| `synthesize_denovo.py::determine_energy_metabolism()` | ✅ deleted | Replaced with deprecation stub raising NotImplementedError. Per prompt directive. |
| Empirical evaluation (`RECIPE_EVALUATION.md`) | ✅ done | Per-organism evaluation across 18 dev + 8 blind: 20/26 biologically reasonable; 8/8 standard-medium comparisons match. |

### Phase 2c headline results

- **Acidithiobacillus ferrooxidans**: 9K-medium-style recipe (FeSO₄ donor at pH 2.0) generated correctly via cyc2 detection at 85.7% identity from non-self references (Phase 1.5n cyc2 rebuild + Phase 2c Fix #1 specificity-aware routing).
- **Dehalococcoides mccartyi**: Organohalide respiration recipe (PCE acceptor + H₂ donor + B12) generated via Phase 1.5n rdhA override at 35.3% identity + Phase 2c sub-mode classifier reading capability profile directly.
- **Chloroflexus aurantiacus**: Phototrophic recipe (was acetogenic in V10 due to F.3 spurious gapseq) — correctly routed to phototrophic via Phase 2c F.3 mitigation requiring diagnostic-marker corroboration. pufLM at 47.8% identity is the corroborating signal.
- **Prometheoarchaeum syntrophicum**: Syntrophic recipe (was methanogenic in V10 due to F.3 spurious 0.900 methanogenesis call without mcrA marker) — F.3 mitigation correctly demotes uncorroborated methanogenic and promotes syntrophic.
- **Scalindua profunda**: Correctly escalated (E.1 MAG-completeness) rather than producing a wrong fermentation recipe.

### Files added

- `recipe.py` — Recipe + supporting dataclasses
- `compose_recipe.py` — Recipe composer with all 9 mode-specific functions
- `RECIPE_EVALUATION.md` — Per-organism empirical evaluation
- `data/validation/run_phase2c_recipes.py` — re-runnable recipe generation
- `docs/recipe_examples/` — 26 text + 26 JSON recipes + summary TSV

### Files modified

- `cultureforge.py` — Section 10 (recipe) renderer + JSON `recipe` field + `--section recipe` CLI flag
- `synthesize_denovo.py` — `determine_energy_metabolism()` replaced with deprecation stub
- `README.md` — Recipe section added + Phase 2c key files listed
- `PROGRESS.md` — this entry

### Phase 2c — E. coli ranking fix (2026-04-28)

User review of Phase 2c results flagged that E. coli's primary cultivation mode came out as `fermentative`, when lab convention is to grow E. coli aerobically. The detection isn't biologically wrong (E. coli is a facultative anaerobe with strong fermentation pathway evidence — gapseq scores it at 0.65 vs aerobic respiration at 0.60), but practically wrong for users' expectations.

**Fix** (in `compose_recipe.py::_pick_primary_mode_for_recipe`):

A **facultative-anaerobe ranking rule** added between the specific-modes priority loop and the highest-confidence fallback:

```python
if "aerobic_chemotrophic" in detected and "fermentative" in detected:
    has_obligate_anaerobe_mode = bool(detected & {
        "methanogenic", "anaerobic_respiratory", "syntrophic", "acetogenic"
    })
    is_strict_anaerobe_genomespot = (genomespot_oxygen in
        {"not_tolerant", "anaerobe", "strict_anaerobe"})
    aerobic_conf = mode_confidence["aerobic_chemotrophic"]
    if (not has_obligate_anaerobe_mode
            and not is_strict_anaerobe_genomespot
            and aerobic_conf >= 0.60):
        return "aerobic_chemotrophic"
```

**Threshold rationale (0.60, not the prompt's suggested 0.65):** E. coli's aerobic_chemotrophic confidence is exactly 0.60, below 0.65. Survey of all 5 organisms with both aerobic and fermentative detected:

| Organism | aerobic | fermentative | rule fires? |
|---|---|---|---|
| Campylobacter jejuni | 0.900 | 0.637 | yes (already aerobic — no change) |
| **E. coli** | **0.600** | **0.650** | **yes (PRIMARY FLIPS)** |
| Chloroflexus aurantiacus | 0.850 | 0.650 | no — has acetogenic (obligate-anaerobe gate) |
| Picrophilus torridus | 0.900 | 0.650 | yes (already aerobic — no change) |
| Scalindua profunda | 0.550 | 0.588 | no — below 0.60 threshold (escalates per E.1) |

Threshold 0.60 captures E. coli without flipping Scalindua's escalation path.

**Verification:** Diff on `phase2c_summary.tsv` before vs after the fix shows ONE row changed (E. coli line 19, fermentative→aerobic_chemotrophic, gas N₂→air). All 25 other organisms produce byte-identical recipes. Lactobacillus stays fermentative (rule's gate fails because aerobic_chemotrophic isn't detected at all). Clostridium stays fermentative (same reason). Methanococcus / Syntrophomonas / Campylobacter / Chloroflexus all unchanged.

**Updated tally:** 20/26 → **21/26 biologically reasonable**; E. coli moves from "partial (debatable)" to "correct."

Files updated:
- `compose_recipe.py` — facultative-anaerobe rule added to `_pick_primary_mode_for_recipe`
- `RECIPE_EVALUATION.md` — E. coli section rewritten + addendum at end documenting the fix
- `docs/recipe_examples/Escherichia_coli_recipe.{txt,json}` — regenerated
- `docs/recipe_examples/phase2c_summary.tsv` — regenerated

---

## Phase 2d — MediaDive/BacDive Consistency Layer (2026-04-28)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| API investigation (Task 1) | ✅ done | `data/mediadive_api_notes.md` + `data/bacdive_api_notes.md`. Both APIs are public, no-auth. MediaDive supports `/medium/{id}` + `/medium-strains/{id}` (forward only — reverse strain→media must be derived locally). BacDive supports `/fetch/{id}` + `/taxon/{name}` + `/culturecollectionno/{ccno}` (no `/search` endpoint despite the prompt's pseudocode). |
| Cache schema (Task 2.3) | ✅ done | 4 SQLite tables added: `mediadive_cache` (3,336 rows), `bacdive_cache` (30,538 rows), `organism_to_bacdive` (934 mappings), `organism_to_published_media` (81 links). All populated from local Phase 1 JSONs (3,336 MediaDive + 30,538 BacDive). |
| MediaDive client (Task 2.1) | ✅ done | `mediadive_client.py` — cache-primary `fetch_medium_by_id`, `fetch_media_for_strain`, `search_media_by_organism`, `get_medium_ingredients`. Live-API fallback with `time.sleep(0.2)` rate limiting. |
| BacDive client (Task 2.2) | ✅ done | `bacdive_client.py` — cache-primary `fetch_strain_details`, `search_strain_by_name`, `fetch_strains_by_taxon`, `get_matched_bacdive_ids`. |
| Capability vector (Task 3.1) | ✅ done | `capability_vector.py` — 19-dimension dict-based vector, plain-Python cosine similarity (no numpy/scipy dep). |
| BacDive→capability mapping (Task 3.2) | ✅ done (minimum-viable) | `data/bacdive_capability_mapping.md`. Covers oxygen tolerance, metabolite utilization, halophily, key enzymes per Checkpoint A scope. Long-tail BacDive fields documented as informational only. |
| Functional neighbor matching (Task 3.3) | ✅ done | `find_functional_neighbors` uses CultureForge capability profiles (BacDive `Physiology and metabolism` is too sparse — most strains carry only `oxygen tolerance`). Matches against the 20 dev/blind organisms with direct media links. Biologically sensible: Methanoperedens→Methanococcus, Prometheoarchaeum→Methanococcus+Syntrophomonas, Magnetospirillum→Rhodopseudomonas, Dehalococcoides→Geobacter. |
| Recipe comparison engine (Task 4) | ✅ done | `recipe_comparison.py` — ingredient diff (shared/cf_only/ref_only/concentration_disagree) + cultivation conditions (T/pH/atmosphere) check + Jaccard scoring for n≤2 references, frequency-weighted for n≥3. Composite-stock-solution expansion (full SL-10 + Wolin's vitamins per DSMZ 320 + DSMZ 141). |
| Inspector Section 11 (Task 5) | ✅ done | `--section published-media` renders the comparison report with severity-grouped diffs, condition mismatches, and aggregate agreement score. JSON output also includes the recipe + comparison data. |
| Validation pass (Task 6) | ✅ done | All 26 organisms processed via `data/validation/run_phase2d_validation.py`. Output: `docs/recipe_examples/phase2d_validation_summary.tsv` + `RECIPE_VALIDATION_V11.md` (full per-organism analysis). |

### Phase 2d headline results

After Path 2(c) metric calibration (full SL-10/Wolin's expansion + Jaccard for n≤2 + cultivation-condition penalties via TEMPURA cross-check):

| Match type | Count | ≥70% | 50-69% | <50% |
|---|---|---|---|---|
| Direct (BacDive species match) | 20 | 3 (E. coli 100%, Geobacter 83%, Clostridium 75%) | 4 | 13 |
| Functional neighbor | 6 | 4 (Prometheoarchaeum 100%, Scalindua 100%, Picrophilus 80%, Dehalococcoides 75%) | 1 | 1 |
| **Total** | **26** | **7** | **5** | **14** |

The strict 80% Definition-of-Done target (`80%+ direct-match @ >70% agreement`) was not met (3/20 = 15%), but the shortfall traces to documented metric data-coverage issues (G.1 GenomeSPOT temperature mispredictions; G.2 single-reference Jaccard brittleness; G.3 TEMPURA pH sparse) — not failures of the Phase 2d integration logic. The structured diff output IS the actionable deliverable; the aggregate score is informational with caveats.

### Picrophilus diagnostic test (per user direction)

The Path 2(c) Fix #3 diagnostic case: Picrophilus dropped from 100% → 80% after the cultivation-condition checks were added. The TEMPURA Picrophilus-oshimae temperature check (optimum 60°C vs CF recipe 30°C) correctly fired a -0.20 penalty. The shortfall to the user's expected 30-50% is because TEMPURA has no `optimal_ph` for Picrophilus oshimae (so the pH check can't fire — Picrophilus's actual ~0.7 pH isn't in our data). The principle (TEMPURA cross-check correctly flags target-organism condition mismatches even when reference media match the recipe) is established and working.

### Files added

- `mediadive_client.py`, `bacdive_client.py` — Phase 2d API clients
- `capability_vector.py` — capability-vector encoding + functional-neighbor matching
- `recipe_comparison.py` — ingredient + conditions diff engine
- `data/build_phase2d_caches.py` — one-shot population of the 4 cache tables
- `data/mediadive_api_notes.md`, `data/bacdive_api_notes.md`, `data/bacdive_capability_mapping.md`
- `data/validation/run_phase2d_validation.py` — re-runnable validation pipeline
- `RECIPE_VALIDATION_V11.md` — full per-organism validation report
- `docs/recipe_examples/phase2d_validation_summary.tsv`

### Files modified

- `cultureforge.py` — Section 11 (published-media) renderer + `--section published-media` CLI flag
- `LIMITATIONS.md` — Category G added (G.1 GenomeSPOT temperature; G.2 single-reference Jaccard; G.3 TEMPURA pH sparse; G.4 atmosphere unstructured)
- `README.md` — Phase 2d consistency-layer description added; metric framing as "diagnostic, not pass/fail"
- `PROGRESS.md` — this entry

### Database tables added

| Table | Rows | Purpose |
|---|---|---|
| `mediadive_cache` | 3,336 | Raw + summary fields per MediaDive medium (one-shot from local JSONs) |
| `bacdive_cache` | 30,538 | Raw + summary fields per BacDive strain |
| `organism_to_bacdive` | 934 | Genome → BacDive ID mappings (species_name_exact / genus_reclassification_synonym / bacdive_cache_substring) |
| `organism_to_published_media` | 81 | Genome → MediaDive medium IDs (relationship: direct / functional_neighbor) |

---

## Phase 2e — Integration Cleanup (2026-04-30)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| G.1 — TEMPURA-first condition priority | ✅ done | `derive_recipe_context._derive_conditions()` and new `_lookup_tempura()` helper. TEMPURA wins over GenomeSPOT for both temperature and pH; species-name fallback (genus reclassification synonyms + Candidatus stripping) catches the 14 unlinked-organism_id genomes. Per-field source tracked in `cond.source` as `"temp:tempura, ph:genomespot"`. Affected: Methanococcus, Halobacterium, Picrophilus, Thermotoga, Chloroflexus all now use TEMPURA temperatures. |
| JSON `published_media_comparison` top-level | ✅ done | `_build_json` adds parallel `published_media_comparison` field (was nested inside `recipe`). New `_build_comparison_json` helper; same logic as text-mode `_section_published_media`. |
| Deprecation stub verification | ✅ verified | `synthesize_denovo.determine_energy_metabolism()` has zero live callers outside the function that itself is dead code (no external callers either). Marked for Phase 3 cleanup. |
| `inspect --list` polish | ✅ done | Species column auto-widens to fit longest cleaned name (43 chars for `Geobacter sulfurreducens subsp. ethanolicus`); CheckM column shows `(n=1)` header explaining sparse coverage. |
| G.3 — BacDive culture-pH supplement | ✅ done (data-limited) | `recipe_comparison._lookup_bacdive_ph` parses BacDive `Culture and growth conditions / culture pH` (handles dict / list / range strings; prefers `type=optimum` → `type=growth` → any positive). Wired as 2nd-priority pH source after TEMPURA in `_check_cultivation_conditions`. Local cache only carries pH for Halobacterium and E. coli among the 26; neither produces a >2-unit mismatch. Architecturally correct; data coverage limits practical impact. |
| G.4 — BacDive oxygen-tolerance for atmosphere | ✅ done | `_lookup_bacdive_atmosphere` reads `Physiology and metabolism / oxygen tolerance` and returns majority category (aerobic / anaerobic / microaerobic / facultative). Replaces medium-name heuristic as primary atmosphere reference. Facultative organisms match anything (no false positives on E. coli). 15 of 26 species have BacDive signal. |
| Atmosphere category bugfix | ✅ done | `"aerobe" in "anaerobe"` substring bug fixed by reordering checks (anaerobic-first). Caught by Methanococcus debug case. |
| Genus-fallback synonym fix | ✅ done | `_check_cultivation_conditions` previously fell back from `species = "Methanococcus jannaschii"` to `species LIKE "Methanococcus %"`, picking up mesophilic sister species and falsely flagging the 85°C TEMPURA-derived recipe as off. Now applies same `_GENUS_SYNONYMS_FOR_BD` mapping before genus fallback. |

### Phase 2e validation deltas (V11 → V12)

5 organisms improved, 1 organism correctly newly-flagged, 20 unchanged.

| Organism | V11 | V12 | Δ | Reason |
|---|---|---|---|---|
| Chloroflexus aurantiacus | 7% | 47% | +40 | TEMPURA T 30→56°C |
| Thermotoga maritima | 19% | 55% | +36 | TEMPURA T 30→80°C |
| Methanococcus jannaschii | 34% | 54% | +20 | TEMPURA synonym + condition-check fix |
| Halobacterium salinarum | 30% | 50% | +20 | TEMPURA T 30→50°C |
| Picrophilus torridus | 80% | 100% | +20 | TEMPURA T 30→60°C |
| Campylobacter jejuni | 50% | 30% | −20 | True-positive: BacDive 37/39 microaerobic vs CF aerobic |

Aggregate: ≥70% 7→7, 50-69% 5→7, <50% 14→12.

### Files added

- `RECIPE_VALIDATION_V12.md` — full per-organism delta + verdict
- helpers in `recipe_comparison.py`: `_parse_ph_string`, `_bacdive_culture_ph`, `_lookup_bacdive_ph`, `_bacdive_oxygen_category`, `_lookup_bacdive_atmosphere`, `_cf_atmosphere_category`, `_GENUS_SYNONYMS_FOR_BD`
- helper in `derive_recipe_context.py`: `_lookup_tempura`, `_TEMPURA_GENUS_SYNONYMS`
- helper in `cultureforge.py`: `_build_comparison_json`

### Files modified

- `derive_recipe_context.py` — `_derive_conditions` rewritten; `cond_conf` substring check
- `compose_recipe.py:305-308` — rationale formatting for new per-field source string
- `cultureforge.py` — `_build_json` includes top-level `published_media_comparison`; `_cmd_list` widened species column + clearer CheckM header
- `recipe_comparison.py` — `_check_cultivation_conditions` uses TEMPURA synonym + BacDive pH/atmosphere fallbacks
- `LIMITATIONS.md` — G.1 RESOLVED, G.3 PARTIALLY RESOLVED, G.4 RESOLVED
- `README.md` — validation status updated to V12 numbers
- `PROGRESS.md` — this entry

---

## Phase 3.1 — Manual Override Flags (2026-04-30)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| CLI flags `--temperature` / `--ph` / `--salinity` | ✅ done | Added to `cultureforge inspect`. Range-validated at parse time (0-130°C, 0-14 pH, 0-400 g/L NaCl) with clear error messages and non-zero exit. |
| Override propagation through pipeline | ✅ done | `derive_recipe_context(genome_id, conn, overrides=None)` and `compose_recipe(genome_id, conn, overrides=None)` accept an `overrides` dict. `_derive_conditions` applies user values before TEMPURA/GenomeSPOT lookups, marking source as `user_override`. Section renderers (`_section_recipe_context`, `_section_recipe`, `_section_published_media`) and `_build_json` accept and forward overrides. |
| Salinity numeric field | ✅ done | New `GrowthConditions.salinity_g_per_l: Optional[float]` field (existing `salinity_category` retained). Composer uses the override (when set) for NaCl concentration in both the basal non-halophile branch (5 g/L default) and the halophile composer (250 g/L default). |
| Display / transparency | ✅ done | Recipe header shows `USER OVERRIDES APPLIED: temperature=30°C, pH=0.7, salinity=250 g/L` whenever any override is set. Recipe rationale switches to `(user_override)` for the affected field. JSON includes top-level `user_overrides` plus per-field source string in `recipe.conditions.rationale`. |

### Verification

| Test | Result |
|---|---|
| Invalid inputs rejected (T=200, T=-10, pH=15, pH=-1, salinity=-5, salinity=500) | ✅ all rejected with clear messages |
| Edge values accepted (T=0, T=122, pH=0.5, pH=13, salinity=0, salinity=350) | ✅ all accepted |
| Lactobacillus `--temperature 30` | ✅ recipe T = 30°C with `(user_override)` source label |
| Campylobacter `--temperature 37` | ✅ recipe T = 37°C |
| Picrophilus `--temperature 60 --ph 0.7` | ✅ both overrides applied; per-field source = `user_override` |
| Halobacterium `--salinity 100` | ✅ NaCl ingredient = 100 g/L (overrides halophile-default 250 g/L) |
| Default no-overrides byte-identity | ✅ recipe + recipe-context sections deterministic and unchanged from pre-3.1 baseline; pre-existing nondeterminism in published-media diff display is unrelated |
| V12 validation re-run with no overrides | ✅ byte-identical to pre-3.1 V12 scores |
| Methanococcus smoke test | ✅ T=85°C, ΔG=-135.6 kJ/mol, conf 0.73 (unchanged) |

### Files modified

- `cultureforge.py` — CLI flags + validation; `_build_json` / `_section_recipe_context` / `_section_recipe` / `_section_published_media` accept `overrides`; recipe header `USER OVERRIDES APPLIED` annotation; top-level JSON `user_overrides`
- `derive_recipe_context.py` — `derive_recipe_context()` and `_derive_conditions()` accept `overrides=None`; user-override path produces `temp/ph/salinity:user_override` source labels
- `compose_recipe.py` — `compose_recipe()` accepts `overrides=None`; basal-NaCl and halophile-NaCl ingredients respect `salinity_g_per_l` override; rationale parser updated for new per-field source format
- `recipe_context.py` — `GrowthConditions.salinity_g_per_l` field added
- `README.md` — new "Manual cultivation condition overrides" section
- `LIMITATIONS.md` — G.1 residual notes that `--temperature` flag is now the user-accessible workaround
- `PROGRESS.md` — this entry

---

## Phase 3.2 — Archaeal Sulfur Oxidation Markers (2026-04-30)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| Literature review (Task 1, Checkpoint A) | ✅ done | `data/diagnostic_markers/archaeal_sulfur_oxidation_review.md`. Confirmed Sulfolobales archaea use TQO/DoxDA + TetH + SOR rather than bacterial soxB. Counts 2021 / Willard 2024 / Protze 2011 / Müller 2004 / Kletzin 1989 reviewed. |
| 4 new markers + 15 verified UniProt accessions | ✅ done | tqoDoxD (P97207, Q97XJ3, Q96ZH9, A4YDN8); tqoDoxA (P97224, Q97XJ4, F9VNN5, A4YDN9); tetH (G8YXZ9, F4B6C8, G8YY01); sor (P29082, Q972K4, Q977W3, A4ZIS7). All hand-fetched from UniProt and protein names verified. Wrong-protein traps identified and excluded (P29086/P29087/P29088 = sor-flanking-region ORFs, not SOR). |
| Test-set exclusion | ✅ enforced | Every accession's source organism checked against the 26-organism dev/blind list. No S. acidocaldarius proteins. Primary references all from Acidianus ambivalens; diversity from Saccharolobus solfataricus, Sulfurisphaera tokodaii, Metallosphaera sedula, Sulfuracidifex metallicus, Acidianus hospitalis, Acidianus tengchongensis. |
| FASTA + BLAST DB build | ✅ done | `fetch_markers.sh` extended with 4 new build_ref blocks. `build_marker_blast_db.py` produces 4 new BLAST databases (blastdb_tqoDoxD, blastdb_tqoDoxA, blastdb_tetH, blastdb_sor). |
| Cross-contamination scan | ✅ done | BLAST scan of all 4 markers against all 26 test proteomes. Only one positive call on a non-target organism: **Acidithiobacillus ferrooxidans tetH at 37.5%/87% qcov, bs=252** — biologically expected (per user clarification: bacterial DoxXA/TetH homologs to archaeal TQO/TetH; Acidithiobacillus does have tetrathionate hydrolase activity). All other non-sulfur-oxidizers fall below thresholds. No false positives on Methanococcus, E. coli, Lactobacillus, Picrophilus, Acetobacterium, etc. |
| Pathway definition update | ✅ done | `sulfur_oxidation` capability extended with 4 new diagnostic-marker-bearing steps (DoxD/DoxA/TetH/SOR). No capability framework changes. Description updated to "Sulfur/sulfide/thiosulfate oxidation (bacterial SOX + archaeal TQO/TetH/SOR)". |
| REFERENCE_CURATION.md sections | ✅ done | 4 new marker sections following existing Phase 1.5m format. Includes literature references, accession tables, cross-reactivity notes. |

### Key biological finding (Task 4 verification)

**Sulfolobus acidocaldarius DSM 639 lacks detectable orthologs to all four archaeal sulfur oxidation markers.**

Empirical evidence:
- BLAST best hits at >30% pident exist but qcov is <40% in all cases (e.g., DoxD: 30.3% pident over 36% qcov, e=8e-5; SOR: 22.4% pident over 32% qcov; TetH: 30% pident over 14% qcov).
- UniProt direct search for S. acidocaldarius doxD/doxA/tetH/sor returns zero results.
- A broader UniProt search ("Sulfolobus acidocaldarius" + thiosulfate/tetrathionate/"sulfur oxygenase") returns only a sulfurtransferase (rhodanese, different enzyme) and unrelated proteins.

This is biologically correct, not a tool failure. Counts et al. 2021 and Willard et al. 2024 classify S. acidocaldarius as a "limited" sulfur biooxidizer compared to other Sulfolobales — the DSM 639 reference genome simply does not encode the canonical Sulfolobales sulfur-oxidation gene complement.

**Phase 3.2 therefore delivers correct biology for the Sulfolobales lineage but does not move the V12 headline score for the existing test-set target.** The markers will catch Acidianus, Metallosphaera, Sulfurisphaera, Sulfuracidifex, Saccharolobus solfataricus when those appear in future test sets.

### V12 validation re-run

Zero score changes across all 26 organisms. Only delta is Dehalococcoides functional-neighbor count (4→5; score still 75%) — a downstream effect of Acidithiobacillus's capability vector now including a tetH detection, which slightly shifts neighbor selection.

No regressions on bacterial sulfur oxidizers:
- *Acidithiobacillus*: aerobic_chemotrophic 0.85, lithotrophic_aerobic 0.56 (sulfur oxidation 0.555). soxB-based detection retained; tetH adds corroborating evidence.
- *Allochromatium*: phototrophic 0.77, lithotrophic_aerobic 0.66 (sulfur oxidation 0.655). Unchanged.
- *Sulfurimonas*: lithotrophic_aerobic 0.61 (sulfur oxidation 0.606). Unchanged.

### Files added

- `data/diagnostic_markers/archaeal_sulfur_oxidation_review.md` — 7-section literature review + reference availability audit + Sulfolobus acidocaldarius honest finding
- `data/diagnostic_markers/tqoDoxD_refs.fasta` (4 seqs)
- `data/diagnostic_markers/tqoDoxA_refs.fasta` (4 seqs)
- `data/diagnostic_markers/tetH_refs.fasta` (3 seqs)
- `data/diagnostic_markers/sor_refs.fasta` (4 seqs)
- 4 new BLAST databases (blastdb_tqoDoxD, blastdb_tqoDoxA, blastdb_tetH, blastdb_sor)

### Files modified

- `fetch_markers.sh` — 4 new build_ref blocks for archaeal sulfur oxidation
- `data/pathway_definitions.json` — `sulfur_oxidation` capability extended with 4 new steps
- `data/diagnostic_markers/REFERENCE_CURATION.md` — 4 new marker sections (Phase 3.2)
- `LIMITATIONS.md` — A.4 archaeal sulfur oxidation status updated
- `PROGRESS.md` — this entry

### Database

`genome_diagnostic_markers` now contains `tetH` rows for genome_id=11 (Acidithiobacillus): 2 positive calls. Other archaeal markers produced no rows above the strict default thresholds (evalue 1e-30, pident 30, qcov 70) — consistent with the Sulfolobales-only conservation pattern.

---

## Phase 3.3 — Canonical Aerobic Nitrite Oxidation (2026-05-01)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| Pre-implementation verification | ✅ done | `nitrospira_verification.md` — established that N. moscoviensis NSP M-1 lacks comammox amoA but has 5 nxrA paralogs at 94-96% pident. Pivoted Phase 3.3 scope from comammox amoA to canonical NOB nxrA. |
| Coverage audit (Phase 3.3a) | ✅ done | `data/coverage_audit/` — 6 documents enumerating ~38 metabolisms, mapping coverage, prioritizing gaps. Confirmed canonical NOB as the highest-priority Tier-1 gap. |
| Literature review + marker selection (Task 1, Checkpoint A) | ✅ done | `nitrite_oxidation_review.md` — 8 verified nxrA candidates across 4 NOB genera. All TrEMBL (no Swiss-Prot reviewed nxrA exists in UniProt). |
| narG cross-reactivity assessment (Task 1.4) | ✅ done | Empirical scan against all 26 test proteomes. narG-family cross-reactivity caps at 48% pident at full coverage (Methanoperedens, E. coli, Scalindua, Lactobacillus). Intra-clade NOB floor: 87% pident. 39-point gap → 75% pident threshold discriminates cleanly. Single-marker logic sufficient; paired nxrAB not needed. |
| 8 verified UniProt accessions | ✅ done | A0A0S4KRS1 (Ca. N. inopinata), A0A1W1I298 (N. japonica), A0ABM8RCK9 (N. defluvii), Q3SQW5 (Nitrobacter winogradskyi Nb-255), Q71RT9 (N. alkalicus), A0A916FC48 (Ca. Nitrotoga fabula), A0ABN8AJF8 (Ca. Nitrotoga arctica), A0A894Z0L1 (Nitrolancea hollandica). Test-set exclusion enforced — no Nitrospira moscoviensis NSP M-1 proteins. Wrong-protein traps excluded (Q3BJV5-Q3BJV9 are 85-100 aa N. winogradskyi nxrA fragments). |
| Two-clade reference architecture | ✅ confirmed | Type A (cytoplasmic, Nitrospira/Nitrotoga) and Type B (periplasmic, Nitrobacter/Nitrolancea) share <25% identity. OR-logic best-hit determines lineage. |
| `nxrA` marker thresholds in run_marker_blast.py | ✅ done | pident 75.0, qcov 80.0, evalue 1e-30 (consistent with nitrite_oxidation_review.md recommendation). |
| FASTA + BLAST DB build | ✅ done | `data/diagnostic_markers/nxrA_refs.fasta` (8 seqs); `blastdb_nxrA` built; `fetch_markers.sh` extended. |
| New `lithotrophic_aerobic_nitrite` capability in pathway_definitions.json | ✅ done | 4 pathway steps (NXR / CO2 fixation / aerobic respiration / ammonia assimilation). diagnostic_marker_override at 75% pident → 0.70 confidence (Phase 1.5n pattern). **essential_marker = "nxrA"** caps confidence at 0.40 when marker absent — prevents spurious 0.52 firings on denitrifiers (gapseq EC overlap with narG-family). |
| Cultivation-mode group routing | ✅ done | Added "Aerobic nitrite oxidation" to lithotrophic_aerobic mode group in capability_detectors.py. Mode-picker corroboration (`_MODE_DIAGNOSTIC_MARKERS["lithotrophic_aerobic"]`) extended with nxrA + Phase 3.2 archaeal sulfur markers. |
| Recipe composer: nitrite branch | ✅ done | New nitrite branch in `_compose_lithotrophic_aerobic_recipe` — adds NaNO2 0.5 mM electron donor with toxicity warning; replaces generic CO2 carbon with NaHCO3 2.5 g/L; auto-adjusts pH to 7.5 if context has neutral default; reduces shaking 150→120 rpm to avoid nitrite stripping. |
| Electron donor derivation | ✅ done | `_derive_electron_donors` in derive_recipe_context.py adds NO2- when nitrite oxidation capability detected. |
| New thermodynamic template | ✅ done | `lithotrophic_aerobic_nitrite`: NO2⁻ + 0.5 O2 → NO3⁻, ΔG = -74 kJ/mol. Routed via electron-donor text matching in _apply_thermodynamic_check. |

### Verification

| Test | Result |
|---|---|
| Marker BLAST against 26 proteomes | 1 positive call (Nitrospira gid 23 at 96% pident, 25 hits across 5 paralogs); 4 below-threshold hits at 44-48% (Methanoperedens, E. coli, Scalindua, Lactobacillus); 21 organisms with no rows |
| Cross-organism capability detection | Only Nitrospira changes (acetogenic primary → lithotrophic_aerobic primary at 0.77). All 25 others identical. |
| Cross-organism recipe-time mode pick | Only Nitrospira changes (acetogenic recipe → lithotrophic_aerobic [nitrite oxidation, canonical NOB]) |
| Spurious nitrite oxidation firings | 0 (essential_marker rule caps non-nxrA-hit organisms at conf 0.20-0.40) |
| Nitrospira recipe components | Aerobic atmosphere ✓ NaNO2 0.5 mM with toxicity warning ✓ NaHCO3 2.5 g/L ✓ Phosphate buffer pH 7.5 ✓ SL-10 trace metals ✓ Wolin's vitamins ✓ No reducing agent ✓ ΔG -74 kJ/mol feasible ✓ |
| V12 validation re-run | 25 organisms unchanged; Nitrospira 20% → 19% (essentially flat — single-reference Jaccard brittleness against DSMZ 756d) |

### Honest finding: V12 score didn't move despite biological correctness

The recipe is now biologically correct (matches DSMZ Medium 2399 architecture for canonical NOB cultivation). The flat V12 score (20% → 19%) reflects pre-existing metric limitations:

1. **Single-reference Jaccard brittleness** (LIMITATIONS G.2) — Nitrospira moscoviensis has only 1 published reference medium in MediaDive (756d). Jaccard scoring penalizes any ingredient name mismatch as "missing".
2. **Ingredient-name normalization gaps** — DSMZ Medium 756d lists individual SL-10 trace components (CuSO4·5H2O, MnSO4·H2O, (NH4)6Mo7O24, KH2PO4, CaCO3) rather than aggregated SL-10. CF recipe uses "SL-10 trace metal solution" as a composite ingredient. The Phase 2e composite expansion (G.4 fix) covers DSMZ-320 component expansion in the comparison engine but doesn't fully resolve KH2PO4 (different K-phosphate salt vs CF's K2HPO4) or CaCO3 (vs CF's CaCl2).

This is the same biology-vs-metric divergence pattern documented in Phase 3.2 for Sulfolobus DSM 639 — recipe correctness can be confirmed by direct architectural comparison with DSMZ media even when the V12 numeric score doesn't reflect it. The Phase 2c evaluation (RECIPE_EVALUATION.md) tracks biological reasonableness; the V12 score is a triage signal with documented caveats.

### Files added

- `data/diagnostic_markers/nitrite_oxidation_review.md` — literature review, narG cross-reactivity assessment, threshold rationale
- `data/diagnostic_markers/nxrA_refs.fasta` (8 seqs)
- `data/diagnostic_markers/blastdb_nxrA.*` (BLAST database)

### Files modified

- `fetch_markers.sh` — added nxrA build_ref block
- `run_marker_blast.py` — added nxrA threshold (pident 75 / qcov 80 / evalue 1e-30)
- `data/pathway_definitions.json` — new `lithotrophic_aerobic_nitrite` capability with diagnostic_marker_override + essential_marker rule
- `capability_detectors.py` — `CULTIVATION_MODE_GROUPS["lithotrophic_aerobic"]` extended with "Aerobic nitrite oxidation"
- `compose_recipe.py` — `_MODE_DIAGNOSTIC_MARKERS["lithotrophic_aerobic"]` extended with nxrA + Phase 3.2 sulfur markers; nitrite branch in `_compose_lithotrophic_aerobic_recipe`; new `lithotrophic_aerobic_nitrite` thermodynamic template; nitrite branch in `_apply_thermodynamic_check` template-key picker
- `derive_recipe_context.py` — `_derive_electron_donors` adds NO2- when nitrite oxidation detected
- `data/diagnostic_markers/REFERENCE_CURATION.md` — nxrA marker section
- `LIMITATIONS.md` — A.2 entry updated (canonical NOB resolved; comammox detection deferred)
- `PROGRESS.md` — this entry

### Forward compatibility

The nxrA + amoA combination distinguishes comammox from canonical NOB. When a comammox organism is added to the test set or encountered in submissions, both markers will fire and a future capability `comammox` (or extended logic in `lithotrophic_aerobic_nitrite`) can route to the comammox-appropriate recipe. Comammox-specific full-length amoA references are not added in Phase 3.3 because no comammox organism exists in the current 26-organism test set; deferred to a future sub-phase if needed.

---

## Phase 3.4 — Dissimilatory Nitrate Reduction to Ammonium / DNRA (2026-05-01)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| Literature review + cross-reactivity assessment (Task 1, Checkpoint A) | ✅ done | `dnra_review.md`. Empirical 26-genome scan + heme-motif analysis (CXXCK active-site signature). 65% pident threshold confirmed. |
| 6 verified UniProt accessions across 5 genera | ✅ done | Q9S1E5 (Wolinella, SP), Q9Z4P4 (Sulfurospirillum, SP), Q8EAC7 (Shewanella, SP), Q06PW6 (Mannheimia, SP), B5QZA1 (Salmonella, SP), Q8VNU2 (Desulfovibrio, TrEMBL). 5 of 6 are Swiss-Prot reviewed — substantially better than typical Phase 3 marker quality. |
| Test-set exclusions enforced | ✅ verified | E. coli (P0ABK9), Nitratidesulfovibrio vulgaris (Q72EF3), Campylobacter all excluded. Wrong-protein traps caught: O33732 (=Shewanella frigidimarina nitrate reductase, NOT Sulfurospirillum nrfA as suggested in prompt), V5Z1T4/Q6ZXS7 (D. desulfuricans nrfA fragments). |
| FASTA + BLAST DB build | ✅ done | `data/diagnostic_markers/nrfA_refs.fasta` (6 seqs); `blastdb_nrfA` built; `fetch_markers.sh` extended. |
| nrfA marker thresholds in run_marker_blast.py | ✅ done | pident 65 / qcov 80 / evalue 1e-30 — conservative threshold per heme-motif analysis. |
| New `anaerobic_respiratory_dnra` capability in pathway_definitions.json | ✅ done | 4 pathway steps (NrfA + NarG/NapA + electron transport + nrfH partner). diagnostic_marker_override at 65% pident → 0.65 confidence. **essential_marker = "nrfA"** caps at 0.40 when absent (prevents spurious firings on denitrifiers via gapseq EC overlap). |
| Cultivation-mode group routing | ✅ done | "Dissimilatory nitrate reduction to ammonium" added to anaerobic_respiratory mode group in capability_detectors.py. nrfA added to `_MODE_DIAGNOSTIC_MARKERS["anaerobic_respiratory"]` for F.3 corroboration. |
| Sub-mode classifier (Phase 3.4 confidence-aware refactor) | ✅ done | `_classify_anaerobic_subtype` now uses CapabilityProfile-confidence-aware selection when conn available (prefers highest-confidence anaerobic-respiratory capability). Falls back to text-match priority otherwise. Fixes the case where D. vulgaris has BOTH dsrAB (0.82) AND nrfA (0.65) — sulfate reduction correctly wins. |
| Recipe composer dnra branch | ✅ done | New `dnra` branch in `_compose_anaerobic_respiratory_recipe`: KNO3 15 mM electron acceptor with NrfA mechanism rationale, sodium formate 20 mM donor (DSMZ Medium 720 family canonical donor), anaerobic atmosphere. Reuses common basal components for Wolinella-class obligates. |
| Phase 3.1 facultative-anaerobe rule extension | ✅ done | When `anaerobic_respiratory` is in detected_set BUT the only contributing capability is DNRA (not sulfate reduction / iron reduction / organohalide / anammox / denitrification), demote anaerobic_respiratory so the existing aerobic vs fermentative facultative rule fires correctly. Keeps E. coli aerobic primary despite nrfA hit. |
| Electron-acceptor derivation | ✅ done | NO3- as electron acceptor when DNRA capability detected (`_derive_electron_acceptors`). |
| New thermodynamic template | ✅ done | `anaerobic_respiratory_dnra`: 4 HCOO- + NO3- + 7 H+ → 4 CO2 + NH4+ + 3 H2O, ΔG = -598 kJ/mol. |

### Key empirical finding: heme-motif analysis discriminates real NrfA from cross-reactivity

The Phase 3.4 cross-reactivity scan revealed a less-clean pident gap than Phase 3.3's nxrA — borderline hits at 30-34% identity. Counting **CXXCH heme-binding motifs + CXXCK Lys-axial active-site heme** (the diagnostic NrfA signature) cleanly resolved each borderline case:

| Hit | pident | CXXCH | CXXCK | Verdict |
|---|---|---|---|---|
| Scalindua (99.8%) | high | 4 | 1 (CWSCK) | NrfA architecture, but biologically implausible — **MAG contamination from Enterobacteriaceae** |
| E. coli (90%) | high | 4 | 1 (CWSCK) | Real canonical NrfA |
| D. vulgaris (68.8%) | high | 4 | 1 (CWNCK) | Real canonical NrfA (Delta-class W→N substitution) |
| Syntrophomonas (34%) | borderline | 4 | 1 (CFTCK) | Real divergent NrfA — Bacillota DNRA |
| Geobacter (32.9%) | borderline | 4 | 1 (CLTCK) | Real divergent NrfA — Geobacter DNRA |
| Campylobacter (29.7%) | borderline | 5 | **0 (NONE)** | **NOT canonical NrfA** — different multi-heme cytochrome (5 hemes, no Lys-axial active site). Likely Otr-family. Out of Phase 3.4 scope. |

The CXXCK active-site motif is unambiguous — pentaheme NrfA has it, octaheme Otr/HAO doesn't. Applying this analytical lens early prevented setting thresholds on noisy pident alone.

### V12 validation

Zero score changes across all 26 organisms. The DNRA addition is appropriately non-disruptive: no obligate DNRA organism exists in the test set, and the facultative E. coli + D. vulgaris keep their pre-existing primary modes via the extended facultative-anaerobe rule + confidence-aware sub-mode classifier.

### Files added

- `data/diagnostic_markers/dnra_review.md` — literature review, cross-reactivity assessment with heme-motif analysis, threshold rationale
- `data/diagnostic_markers/nrfA_refs.fasta` (6 seqs)
- `data/diagnostic_markers/blastdb_nrfA.*` (BLAST database)

### Files modified

- `fetch_markers.sh` — added nrfA build_ref block with O33732 wrong-protein-trap documentation
- `run_marker_blast.py` — added nrfA threshold (pident 65 / qcov 80 / evalue 1e-30)
- `data/pathway_definitions.json` — new `anaerobic_respiratory_dnra` capability
- `capability_detectors.py` — `CULTIVATION_MODE_GROUPS["anaerobic_respiratory"]` extended with "Dissimilatory nitrate reduction to ammonium"
- `compose_recipe.py` —
  - `_MODE_DIAGNOSTIC_MARKERS["anaerobic_respiratory"]` initialized with nrfA + existing markers (dsrAB, qmoA, mtrC_omcB, rdhA, hzsA, hdh, nosZ)
  - `_classify_anaerobic_subtype` refactored to confidence-aware selection
  - new `dnra` branch in `_compose_anaerobic_respiratory_recipe`
  - new thermodynamic template `anaerobic_respiratory_dnra`
  - facultative-anaerobe rule extended to demote anaerobic_respiratory when only DNRA fires under it
- `derive_recipe_context.py` — `_derive_electron_acceptors` adds NO3- with "dnra" derived_from when DNRA capability detected
- `data/diagnostic_markers/REFERENCE_CURATION.md` — nrfA marker section
- `LIMITATIONS.md` — B.2 marked RESOLVED for canonical NrfA; new note on divergent-NrfA gap; E.1 addendum on Scalindua MAG-contamination Salmonella nrfA signature
- `PROGRESS.md` — this entry

### Documented gaps (deferred to future sub-phases)

1. **Divergent NrfA in Bacillota / Geobacteraceae** (~32-34% pident). Real NrfA architecture (CXXCK preserved) but below 65% threshold. Affected test-set organisms (Syntrophomonas, Geobacter) classify correctly via other primary modes (syntrophic, iron reduction). Future enhancement: paired nrfA + nrfH operon-marker logic with relaxed pident.
2. **Otr-family DNRA** in Epsilonproteobacteria (Campylobacter-class) — different enzyme architecture (octaheme cytochrome c, no CXXCK). Separate marker territory; not in Phase 3.4 scope.
3. **Scalindua MAG contamination signature** — the 99.8% pident hit to Salmonella nrfA on a Brocadiaceae MAG is biologically impossible. Reflects upstream MAG quality issue (LIMITATIONS E.1). A more robust solution would be cross-phylum high-identity sanity check; deferred as separate Phase 3 sub-phase if needed.

### Sentinel organism note

For empirical Phase 3.4 validation against an obligate DNRA organism (no such organism exists in the current 26-organism test set), **Wolinella succinogenes DSM 1740 (GCF_000196135.1, Complete Genome)** would be the ideal sentinel. Documentation only — not added to test set in Phase 3.4 scope.

---

## Phase 3.5 — Aerobic Methanotrophy (2026-05-01)

### Built and integrated

| Component | Status | Notes |
|---|---|---|
| Literature review + cross-reactivity assessment (Task 1, Checkpoint A) | ✅ done | `methanotrophy_review.md`. Empirical pmoA × amoA cross-reactivity confirmed 8-10 point pident gap. |
| 6 verified pmoA references (3 clades, 4 genera) | ✅ done | Q607G3 (Methylococcus capsulatus, **Swiss-Prot**), A4PDX7 (Methylocaldum), Q50541 (Methylosinus), O06122 (Methylocystis), I0JZS9 (Methylacidiphilum fumariolicum), A9QPD9 (Methylacidiphilum infernorum). Type I (× 2), Type II (× 2), Type III Verrucomicrobia (× 2). |
| 4 verified mmoX references | ✅ done | P22869 (Methylococcus, **Swiss-Prot**), P27353 (Methylosinus, **Swiss-Prot**), Q3YA75 (Methylomonas), Q3T939 (Methylocella). Type I (× 2), Type II (× 2). 82-99% intra-family conservation. |
| Test-set exclusions verified | ✅ | No Nitrosomonas amoA in pmoA refs. No methanotroph-related proteins in test-set genomes (only Nitrosomonas pmoA/amoA cross-paralog at 50%, below threshold). |
| FASTA + BLAST DB builds | ✅ done | `data/diagnostic_markers/{pmoA,mmoX}_refs.fasta` + `blastdb_{pmoA,mmoX}` |
| Marker thresholds | ✅ done | pmoA: pident 60 / qcov 80 / evalue 1e-30. mmoX: pident 50 / qcov 70 / evalue 1e-30. |
| New `aerobic_methanotrophy` capability in pathway_definitions.json | ✅ done | OR-logic across pmoA, mmoX. 5 pathway steps (pMMO, sMMO, methanol DH, formaldehyde/formate metabolism, aerobic respiration). diagnostic_marker_override at 60%/0.70 confidence. |
| New `methanotrophic` cultivation mode group | ✅ done | Added to capability_detectors.py CULTIVATION_MODE_GROUPS. Added to compose_recipe.py _SPECIFIC_MODES_PRIORITY (between methanogenic and acetogenic). pmoA + mmoX added to _MODE_DIAGNOSTIC_MARKERS for F.3 corroboration. |
| New `_compose_methanotrophy_recipe()` in compose_recipe.py | ✅ done | air+CH4 80:20 gas phase at 1 atm; phosphate buffer (K2HPO4 + KH2PO4) at pH 7; NH4Cl nitrogen; SL-10 + Wolin's; copper supplementation note for pMMO biosynthesis; no reducing agent; vigorous shaking 200 rpm. CH4 explicitly listed as carbon source (gas phase, not liquid). |
| New thermodynamic template `methanotrophic` | ✅ done | CH4 + 2 O2 → CO2 + 2 H2O, ΔG = -820 kJ/mol. CH4_aq already in DEFAULT_ACTIVITIES at 1e-6 M. |
| New "methanotroph" atmosphere category | ✅ done | recipe_comparison._cf_atmosphere_category checks for `air + CH4` together → "methanotroph"; distinct from plain "aerobic" (no CH4) or "anaerobic" (H2/CO2 methanogen). |
| Atmosphere derivation in derive_recipe_context | ✅ done | When methanotrophic mode detected, atmosphere = SPECIAL_GAS with gases=["air","CH4"]. CH4 added as electron donor with 0.95 confidence in `_derive_electron_donors`. |

### Sentinel validation against Methylococcus capsulatus Bath

Per the user's pushback on deferring sentinel validation: **end-to-end infrastructure verified against the canonical methanotroph type strain.**

- **Genome**: GCF_000008325.1 (Methylococcus capsulatus Bath, NCBI RefSeq, 2971 predicted proteins) downloaded from NCBI FTP.
- **DB load**: inserted at `genomes.id=900` with explicit "SENTINEL: Methylococcus capsulatus Bath" prefix in notes. The validation script (`run_phase2d_validation.py`) uses a hardcoded ORGANISMS list with gids 7-32, so the sentinel is automatically excluded from V12 — confirmed byte-identical V12 output with sentinel present.
- **Marker BLAST**: pmoA fires at 100% pident / 100% qcov (Q607G3 self-hit), all 6 pmoA refs hit gene WP_010961050.1 in the 39.9-100% range (dual-clade architecture demonstrated). mmoX fires at 100% pident (P22869 self-hit), all 4 mmoX refs hit WP_010960482.1 at 81-100%.
- **Capability detection**: aerobic_methanotrophy at **0.80 confidence** (above 0.65 sentinel target). Mode-picker correctly preferred methanotrophic over aerobic_chemotrophic (which sits secondary at 0.50).
- **Recipe**: PRIMARY CULTIVATION MODE = methanotrophic. Gas phase = air 80% + CH4 20% at 1.0 atm. Buffer = K2HPO4 1.4 g/L + KH2PO4 0.7 g/L. Nitrogen = NH4Cl 0.5 g/L. CH4 listed explicitly as carbon source (20% v/v gas phase). SL-10 trace metals + Wolin's vitamins. Shaking 200 rpm. No reducing agent. Temperature 30°C / pH 7.0 (defaults — no TEMPURA / GenomeSPOT data loaded for sentinel; this is OK for infrastructure verification).
- **Thermodynamic check**: Reaction "CH4 + 2 O2 → CO2 + 2 H2O", ΔG = -820.0 kJ/mol, feasibility=feasible. ✓
- **Atmosphere category**: `_cf_atmosphere_category({"air": 0.8, "CH4": 0.2})` → "methanotroph" (verified). Plain aerobic media won't match; methanotroph-specific published media will.

**All 6 sentinel validation criteria from the user's prompt passed.**

### Cross-organism verification (26 test genomes)

Zero false positives. Only Nitrosomonas europaea showed any pmoA hits (50% pident max, 12 hits across pmoA refs × Nitrosomonas amoA paralogs) — all below the 60% threshold, confirming the empirical 8-10 point pident gap is sufficient discrimination. mmoX produced zero hits across all 26 test genomes.

### V12 validation

Byte-identical to pre-Phase-3.5 (no methanotroph in test set). Sentinel at gid=900 is excluded from V12 by the validation script's hardcoded ORGANISMS list.

### Files added

- `data/diagnostic_markers/methanotrophy_review.md` — literature review + cross-reactivity assessment + threshold rationale
- `data/diagnostic_markers/pmoA_refs.fasta` (6 seqs) + `blastdb_pmoA.*`
- `data/diagnostic_markers/mmoX_refs.fasta` (4 seqs) + `blastdb_mmoX.*`
- `data/sentinel/Methylococcus_capsulatus_Bath/proteome.faa` — sentinel proteome (2971 sequences from NCBI RefSeq GCF_000008325.1; downloaded for validation, retained as reference but not part of test set)

### Files modified

- `fetch_markers.sh` — added pmoA + mmoX build_ref blocks
- `run_marker_blast.py` — added pmoA + mmoX thresholds (60%/80% and 50%/70%)
- `data/pathway_definitions.json` — new `aerobic_methanotrophy` capability with OR-logic dual-marker structure
- `capability_detectors.py` — added `methanotrophic` mode group with "Aerobic methanotrophy" pattern
- `compose_recipe.py` —
  - `_SPECIFIC_MODES_PRIORITY` extended with `methanotrophic`
  - `_MARKER_REQUIRED_MODES` includes `methanotrophic`
  - `_MODE_DIAGNOSTIC_MARKERS["methanotrophic"]` = ["pmoA", "mmoX"]
  - new `_compose_methanotrophy_recipe()` function
  - new `methanotrophic` thermodynamic template (CH4 + 2 O2 → CO2 + 2 H2O, -820 kJ/mol)
  - `_MODE_COMPOSERS["methanotrophic"]` registered
- `derive_recipe_context.py` —
  - atmosphere derivation: methanotrophic → SPECIAL_GAS with ["air", "CH4"]
  - electron-donor derivation: CH4 added with 0.95 confidence when methanotrophic mode detected
- `recipe_comparison.py` — `_cf_atmosphere_category` checks for air+CH4 → "methanotroph" (new category, distinct from "aerobic")
- `data/diagnostic_markers/REFERENCE_CURATION.md` — pmoA + mmoX marker sections appended
- `LIMITATIONS.md` — A.10 added and marked RESOLVED for canonical Type I/II/III methanotrophs; N-DAMO and Methylacidiphilum-extremophile gaps documented
- `PROGRESS.md` — this entry

### Documented gaps (deferred to future sub-phases)

1. **N-DAMO** (anaerobic methane oxidation in NC10 phylum / *Ca.* Methylomirabilis) — biochemically distinct from canonical aerobic methanotrophy (intra-aerobic O2 generation via NO dismutase). Would require new capability + nitrite-reductase coupling logic. Out of Phase 3.5 scope.
2. **Methylacidiphilum thermoacidophile cultivation conditions** — Verrucomicrobia methanotrophs grow at pH 1-3 and 60°C. Capability detection works (Type III pmoA refs catch them) but recipe composer's pH/temperature derivation depends on TEMPURA/GenomeSPOT data which may need user overrides for these extremophiles. Phase 3.1 `--ph` and `--temperature` overrides handle this case.
3. **AAP / methanotroph gradient organisms** — aerobic anoxygenic phototrophs and microaerobic methanotrophs near oxic-anoxic interfaces could blur classification, but no test-set or sentinel organism falls here.

### Sentinel disposition

The Methylococcus capsulatus Bath sentinel entry remains in the database at gid=900 with the explicit "SENTINEL: ..." prefix in `notes`. It is automatically excluded from V12 validation by the script's hardcoded ORGANISMS list. The sentinel is preserved as a reference data point for future validation work (e.g., when N-DAMO or other methanotrophic capabilities are added, this sentinel provides a known-positive test case for regression testing). To remove it entirely if desired: `DELETE FROM genomes WHERE id = 900; DELETE FROM genome_diagnostic_markers WHERE genome_id = 900;`.
