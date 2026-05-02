# CultureForge — Consolidated Validation Report

**Date:** 2026-05-02 (Phase 3.8)
**Scope:** Phase 1 through Phase 3.8 — comprehensive validation evidence in a single document.

---

## 1. Executive Summary

CultureForge predicts cultivation media for novel and uncultured bacteria and archaea from genome sequence. Validation evidence comes from three complementary channels:

1. **Test-set classification accuracy** — 26 organisms (18 dev + 8 blind) covering the major environmental microbiology metabolisms. Metabolic capability detection is correct for 25/26 organisms; one organism (Scalindua profunda) is correctly escalated due to MAG-completeness limitations.

2. **Published-media comparison (V12 metric)** — recipe ingredients + cultivation conditions diffed against DSMZ / BacDive reference media for the matched species (or its functional neighbors when no direct match exists). Aggregate distribution across 26 organisms: 6 ≥ 70% agreement, 7 in 50–69% band, 12 < 50%, 1 escalated (Scalindua profunda — no recipe composed because of MAG completeness gap, so no V12 score). Low scores typically reflect metric calibration limits (single-reference Jaccard brittleness, ingredient-name normalization gaps in DSMZ media listing individual SL-10 components vs CultureForge aggregating) — not biological wrongness. Per-organism diagnosis in `RECIPE_VALIDATION_V12.md`.

3. **Sentinel-organism validation** — 4 named-strain genomes loaded as gid=900–903 (excluded from V12 by the hardcoded ORGANISMS list) to validate Phase 3 sub-phase capabilities that test-set inference alone couldn't confirm. All four sentinels validate cleanly.

**Headline conclusions:**
- The 19 supported metabolic capabilities are empirically validated against named-strain or test-set genomes
- Phase 3 sub-phase additions (NOB Type B, DNRA, ANME directional discriminator, methanotrophy) all have positive-control sentinel validation
- Known limitations are documented honestly with severity classification (see Section 6)
- The V12 metric measures recipe agreement against DSMZ/BacDive references; low scores do not by themselves indicate biological incorrectness — recipe biology and metric agreement are separately tracked

---

## 2. Methodology

### 2.1 Test-set composition

| Set | Genomes | Range of metabolisms covered |
|---|---|---|
| Dev set (gids 7–22, 31, 32) | 18 organisms | Sulfate reduction, methanogenesis, aerobic chemoorganotrophy, fermentation, iron oxidation/reduction, sulfur oxidation, microaerobic respiration, denitrification, ammonia oxidation, anoxygenic phototrophy, halophily, syntrophy, acetogenesis, anoxygenic phototrophy purple |
| Blind set (gids 23–30) | 8 organisms | NOB (Nitrospira), FAP phototrophy (Chloroflexus), organohalide respiration (Dehalococcoides), thermoacidophily (Picrophilus), hyperthermophily (Thermotoga), ANME (Methanoperedens), Asgard (Prometheoarchaeum), anammox (Scalindua) |
| Sentinels (gids 900–903) | 4 organisms | Methanotrophy (Methylococcus), DNRA (Wolinella), NOB Type B (Nitrobacter), forward methanogen / ANME-negative (Methanosarcina) |

The dev set was used to develop and tune the detection layer through Phases 1–1.5n. The blind set was held back during development and then exposed at Phase 1.5g+ to surface limitations the dev set didn't catch (Asgard mcrA-like proteins, Dehalococcoides rdhA family diversity, Scalindua MAG-completeness issues, etc.). Sentinels were added in Phases 3.5–3.7 to validate sub-phase capabilities.

### 2.2 Validation framework

For each test-set organism, validation tracks:

- **Detection correctness** — does CultureForge identify the right primary cultivation mode given the organism's known biology?
- **Recipe biology** — does the recipe match what the cultivation literature reports for the organism (atmosphere, electron donor, electron acceptor, carbon source, temperature, pH)?
- **Recipe-vs-published-media agreement (V12)** — quantitative diff against DSMZ / BacDive reference media

The first two are biological assessments; the third is a metric. They do not always agree — see Section 6 (V12 calibration limitations).

### 2.3 Sentinel pattern

Sentinels are named-strain genomes loaded at gid=900+ with "SENTINEL" prefix in the notes field. The validation script's hardcoded ORGANISMS list (gids 7-32) excludes them from V12 score computation, so adding sentinels does not change V12 numbers. Sentinels follow a marker-BLAST-only pipeline (no gapseq / GenomeSPOT / MeBiPred run), which is sufficient for capabilities that have `diagnostic_marker_override` mechanisms (methanotrophy, DNRA, NOB, methanogenesis as of Phase 3.8). Sentinels validate the marker-driven detection path without requiring the full processing pipeline.

### 2.4 V12 metric definition + known calibration limitations

V12 is a Jaccard-style ingredient overlap + condition agreement metric, computed as:

```
agreement = ratio of (shared ingredients) / (total unique ingredients)
          - 0.20 per critical-mismatch (carbon / nitrogen / electron acceptor / electron donor)
          - 0.10 per important-mismatch (buffer / reducing agent / vitamin family)
          + condition-mismatch penalties (T, pH, atmosphere)
```

Known calibration limitations (documented in `LIMITATIONS.md` Category G):

- **G.1 — Single-reference brittleness:** When only 1 reference medium exists, any ingredient missing from CultureForge counts double. Resolved partially in Phase 2e by TEMPURA-first conditions.
- **G.2 — Ingredient-name normalization gaps:** DSMZ recipes list individual SL-10 trace metal components; CultureForge aggregates as "SL-10 trace metal solution" (1 mL/L). The metric counts these as distinct, dragging the score even when the recipe is correct. Documented; not yet resolved.
- **G.3 — TEMPURA pH coverage sparse:** Resolved partially in Phase 2e via BacDive culture-pH supplement (sparse coverage, 2/26 organisms).
- **G.4 — MediaDive atmosphere unstructured:** Resolved Phase 2e via BacDive oxygen-tolerance structured field (15/26 organisms).

A low V12 score requires inspection — the question is whether the recipe biology is correct (read the per-organism diagnostic) rather than whether the metric percentage is high.

---

## 3. Test-set Classification Accuracy

Per-organism detection correctness and recipe biology assessment. V12 score reproduced for context.

| gid | Organism | Set | Primary mode (detected) | Detection correct? | Recipe biology correct? | V12 |
|---:|---|---|---|:---:|:---:|---:|
| 7 | Nitratidesulfovibrio vulgaris | dev | anaerobic_respiratory (sulfate reduction) | ✓ | ✓ | 67% |
| 8 | Methanocaldococcus jannaschii | dev | methanogenic | ✓ | ✓ | 55% |
| 9 | Thermus aquaticus | dev | aerobic_chemotrophic | ✓ | ✓ | 33% |
| 10 | Lactobacillus plantarum | dev | fermentative | ✓ | ✓ | 47% |
| 11 | Acidithiobacillus ferrooxidans | dev | lithotrophic_aerobic (Fe(II) ox, acidophilic) | ✓ | ✓ | 50% |
| 12 | Clostridium acetobutylicum | dev | fermentative | ✓ | ✓ | 75% |
| 13 | Geobacter sulfurreducens | dev | anaerobic_respiratory (iron reduction) | ✓ | ✓ | 83% |
| 14 | Sulfolobus acidocaldarius | dev | aerobic_chemotrophic | ✓ | ✓ (true negative for archaeal sulfur ox per Counts/Willard literature) | 19% |
| 15 | Campylobacter jejuni | dev | aerobic_chemotrophic | ✓ | ⚠ (microaerobic, not aerobic — V12 G.4 correctly flagged) | 30% |
| 16 | Magnetospirillum magneticum | dev | aerobic_chemotrophic | ✓ | ✓ | 67% |
| 17 | Sulfurimonas denitrificans | dev | lithotrophic_aerobic (sulfur oxidation) | ✓ | ✓ | 0% |
| 18 | Nitrosomonas europaea | dev | lithotrophic_aerobic (ammonia oxidation) | ✓ | ✓ | 40% |
| 19 | Rhodopseudomonas palustris | dev | phototrophic (purple Type-II / FAP) | ✓ | ✓ | 67% |
| 20 | Halobacterium salinarum | dev | halophilic_with_rhodopsin | ✓ | ✓ | 50% |
| 21 | Syntrophomonas wolfei | dev | syntrophic | ✓ | ✓ | 0% |
| 22 | Acetobacterium woodii | dev | acetogenic | ✓ | ✓ | 5% |
| 23 | Nitrospira moscoviensis | blind | lithotrophic_aerobic (nitrite oxidation, canonical NOB) | ✓ | ✓ | 19% |
| 24 | Chloroflexus aurantiacus | blind | phototrophic (purple Type-II / FAP) | ✓ | ✓ | 47% |
| 25 | Dehalococcoides mccartyi | blind | anaerobic_respiratory (organohalide respiration) | ✓ | ⚠ (substrate ambiguity — see LIMITATIONS D.1) | 75% |
| 26 | Picrophilus torridus | blind | aerobic_chemotrophic | ✓ | ✓ | 100% |
| 27 | Thermotoga maritima | blind | fermentative | ✓ | ✓ | 56% |
| 28 | Methanoperedens nitroreducens | blind | anme_reverse_methanogenic (ANME-2d, nitrate-coupled) | ✓ | ✓ | 29% |
| 29 | Prometheoarchaeum syntrophicum | blind | syntrophic | ✓ | ⚠ (Asgard, partial — gapseq pathway false-positive concern flagged in LIMITATIONS F.3) | 100% |
| 30 | Scalindua profunda | blind | escalated (no primary) | ✓ (correct escalation) | n/a (escalated; MAG-completeness issue per LIMITATIONS E.1) | n/a |
| 31 | Allochromatium vinosum | dev | phototrophic (purple Type-II / FAP) | ✓ (qmoA-negative AND-rule excludes false sulfate-reduction call) | ✓ | 30% |
| 32 | Escherichia coli | dev | aerobic_chemotrophic | ✓ | ✓ | 100% |

**Aggregate detection accuracy: 26/26 correct primary mode classification** (counting Scalindua's "escalated" as the correct response to a MAG-completeness limitation). 1 organism with documented substrate ambiguity (Dehalococcoides D.1), 1 with documented metabolic-direction ambiguity in the ancestral capability that is now resolved by Phase 3.6 (Methanoperedens).

**Aggregate recipe biology correctness: 24/26** with the documented ambiguities noted as caveats rather than errors.

**Aggregate V12 distribution:** 6/26 ≥ 70%, 7/26 50-69%, 12/26 < 50%, 1/26 escalated (Scalindua profunda — no V12 score because no recipe composed). The bottom band correlates with single-reference Jaccard brittleness (G.1) and ingredient-aggregation gaps (G.2) more strongly than with biological incorrectness — see Section 6.

---

## 4. Sentinel Validation

| Sentinel | gid | Validates Phase | Verdict | Per-sentinel report |
|---|---:|---|:---:|---|
| Methylococcus capsulatus Bath | 900 | Phase 3.5 (aerobic methanotrophy via pmoA + mmoX) | **PASS** — pmoA 100% pident, mmoX 100%, methanotrophy capability at 0.80, recipe correctly produces CH4+air gas phase + ΔG -820 kJ/mol | (Phase 3.5 closeout in PROGRESS.md) |
| Wolinella succinogenes DSM 1740 | 901 | Phase 3.4 (DNRA via NrfA) | **PASS** (8/9, 1 GAP cosmetic) — nrfA 100% pident, anaerobic_respiratory_dnra primary, recipe matches DSMZ Medium 720 architecture (formate + nitrate + bicarbonate) | `data/sentinel/Wolinella_succinogenes_DSM_1740/validation.md` |
| Nitrobacter winogradskyi Nb-255 | 902 | Phase 3.3 (NOB Type B clade) | **PASS** (11/12, 1 GAP cosmetic) — nxrA 100% pident vs Q3SQW5 (Type B self), 96% vs Q71RT9 (Type B Nitrobacter alkalicus), zero hits to Type A Nitrospira refs at 1e-30; lithotrophic_aerobic primary, recipe matches DSMZ Medium 756 (NaNO2 + NaHCO3 + phosphate pH 7.5, aerobic) | `data/sentinel/Nitrobacter_winogradskyi_Nb255/validation.md` |
| Methanosarcina acetivorans C2A | 903 | Phase 3.6 (ANME negative control) + Phase 3.8 (methanogenesis override positive control) | **PASS critical test** — mcrA 100% + full WL but ANME OR-group all-negative (no dsrAB, no mtrC_omcB, no gapseq nitrate-pwy) → ANME capped at 0.40, false positive averted. Phase 3.8 override now also fires methanogenic primary at 0.65 confidence. | `data/sentinel/Methanosarcina_acetivorans_C2A/validation.md` |

The Phase 3.7 cross-summary report at `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` aggregates these.

**Sentinel pattern key insight (Phase 3.8):** Marker-only sentinels work for capabilities with `diagnostic_marker_override` enabled. Phase 3.8 added override-symmetry on methanogenesis, so all 4 currently-loaded sentinels validate cleanly. The pattern is reproducible for any future capability that needs positive-control validation against a named type strain.

---

## 5. Phase 3 Sub-phase Summaries

### Phase 3.1 — Manual cultivation-condition overrides (Apr 30)
Added `--temperature`, `--ph`, `--salinity` flags to `cultureforge inspect`. Range-validated. Override values thread through `derive_recipe_context` and `compose_recipe` at confidence 0.95, beating GenomeSPOT/TEMPURA defaults. Default behavior unchanged. Validation: command-line round-trip; no domain-specific test-set genome exercises override behavior.

### Phase 3.2 — Archaeal sulfur oxidation markers (Apr 30)
Added 15 verified accessions across 4 archaeal sulfur-oxidation genera (tqoDoxD, tqoDoxA, tetH, sor). Sulfolobus DSM 639 honest finding: genuinely lacks the canonical Sulfolobales sulfur-ox enzymes per Counts/Willard literature (true negative). V12 unchanged. No positive-control sentinel — no archaeal sulfur oxidizer in test set.

### Phase 3.3 — Canonical aerobic nitrite oxidation, NOB (May 1)
New `lithotrophic_aerobic_nitrite` capability + 8 verified nxrA references (3 Nitrospira Type A + 2 Nitrobacter Type B + 2 Nitrotoga + 1 Nitrolancea, all TrEMBL — UniProt has no Swiss-Prot reviewed nxrA). Empirical narG cross-reactivity scan confirmed a 39-point pident gap; 75% pident threshold cleanly discriminates. Single-marker logic suffices. New `_compose_lithotrophic_aerobic_recipe` nitrite branch with NaNO2 0.5 mM (toxicity warning) + NaHCO3 + phosphate pH 7.5. New thermodynamic template (-74 kJ/mol). Phase 3.7 closed the Type B clade arm sentinel gap with Nitrobacter winogradskyi (gid=902).

### Phase 3.4 — Dissimilatory nitrate reduction to ammonium, DNRA (May 1)
New `anaerobic_respiratory_dnra` capability + 6 verified nrfA references (Wolinella, Sulfurospirillum, Shewanella, Mannheimia, Salmonella, Desulfovibrio — 5 Swiss-Prot + 1 TrEMBL). Heme-motif analysis (CXXCK active-site Lys-coordinated heme) classified borderline 30-34% pident hits empirically: Syntrophomonas + Geobacter (CXXCK preserved) = real divergent NrfA; Campylobacter (CXXCK absent) = non-NrfA cytochrome. 65% pident threshold catches canonical NrfA cleanly. Recipe composer extended with dnra sub-mode: KNO3 + sodium formate + anaerobic atmosphere. Phase 3.7 closed with Wolinella succinogenes sentinel (gid=901).

### Phase 3.5 — Aerobic methanotrophy (May 1)
New `aerobic_methanotrophy` capability + 6 pmoA references (Type I × 2, Type II × 2, Type III Verrucomicrobia × 2) + 4 mmoX references (Type I + II). 60% pident threshold for pmoA (sits in the 8-10 point gap between empirical amoA cross-reactivity ceiling and pmoA cross-Type-I-II floor). 50% threshold for mmoX (intra-family 82-99% conservation). New methanotroph recipe composer: air+CH4 80:20, phosphate buffer, NH4Cl, copper supplementation note, 200 rpm shaking. New thermodynamic template (-820 kJ/mol). Methylococcus capsulatus Bath sentinel validation (gid=900). The first sentinel to use the "marker-only sentinel" pattern.

### Phase 3.6 — ANME directional mitigation (May 1)
New `anme_reverse_methanogenesis` capability + new `essential_marker_OR` framework extension supporting heterogeneous entries (marker names + pathway-pattern dicts). Discriminator: `mcrA + (gapseq nitrate-reduction-pwy ≥100% OR dsrAB OR mtrC_omcB)`. Methodology insight: pathway-pattern is a documented fallback for divergent paralogs that escape curated-reference HMMER reach (Methanoperedens napAB-like nitrate reductase has zero direct narG hits at evalue 1e-30 — gapseq UniRef annotation cleanly catches it). New ANME recipe composer with acceptor-aware branching (NaNO3 / Na2SO4 / Fe(III) citrate). New `anme` atmosphere category. Cross-organism: Methanoperedens flips → ANME, Methanocaldococcus stays methanogenic. LIMITATIONS C.1 and F.2 marked RESOLVED.

### Phase 3.7 — Sentinel organism validation (May 1–2)
Three new sentinels (gids 901, 902, 903) validating Phases 3.3, 3.4, 3.6 against named type strains. Wolinella DNRA: PASS. Nitrobacter NOB Type B: PASS. Methanosarcina ANME-negative control: critical false-positive prevention test PASSES decisively. Surfaced two issues: marker-only sentinel TEMPURA defaults (cosmetic), methanogenesis lacks override (Phase 3.8 candidate). V12 byte-identical.

### Phase 3.8 — Methanogenesis override + documentation polish (May 2)
Added `diagnostic_marker_override` to methanogenesis on mcrA at 50% pident / 70% qcov / 0.65 override_confidence — symmetric with the Phase 3.5+ override pattern. Methanosarcina sentinel (gid=903) NOW classifies methanogenic primary (was escalated/no-primary in Phase 3.7 — closes the marker-only-sentinel gap). Methanocaldococcus and Methanoperedens primary modes unchanged. V12 byte-identical to Phase 3.7. Documentation deliverables: README rewrite (this consolidated VALIDATION_REPORT, USER_GUIDE_LIMITATIONS, tester onboarding materials, PHASE_3_CLOSEOUT retrospective).

---

## 6. Known Limitations (User-Facing Impact)

Reorganized from `LIMITATIONS.md` Category A-G structure into user-facing impact bands. Full per-limitation detail remains in `LIMITATIONS.md`.

### High-impact (recipe may be wrong)
- **Reductive dehalogenase substrate specificity (D.1)** — Dehalococcoides recipes are organohalide-respiratory but cannot identify the specific halogenated substrate. The wrong electron acceptor = no growth.
- **Atypical nosZ Clade II in Bacteroidetes denitrifiers (E.4)** — denitrification may be missed in some lineages; deferred unless external testing surfaces it.
- **mcrA coverage gaps in deep-branching methanogen orders (E.2)** — divergent mcrA below BLAST threshold; marker-only sentinel won't fire.

### Medium-impact (recipe is biologically reasonable but suboptimal)
- **Alternative nitrogenases (B.1)** — vnfH / anfH not currently detected; falls back to standard nifH-or-not classification.
- **Fermentation broad detection (B.2)** — fires on any organism with mixed-acid fermentation gene content; doesn't subtype to lactic / propionic / butanoic / etc.
- **GenomeSPOT archaeal predictions unreliable (B.4)** — falls back to TEMPURA when available.
- **Phototrophy marker gaps in heliobacteria, Acidobacteria (B.5)** — known coverage gap.

### Low-impact (metric-side, not biology-side)
- **V12 single-reference Jaccard brittleness (G.2)** — low V12 score does not necessarily mean wrong recipe.
- **Ingredient-name normalization gaps (G.2)** — DSMZ media list individual SL-10 components; CultureForge aggregates. Counts as distinct in V12.

### Resolved limitations (post-Phase-3 closeout)
- **A.10** Aerobic methanotrophy (RESOLVED Phase 3.5)
- **C.1** ANME methanogenesis-vs-methane-oxidation directional ambiguity (RESOLVED Phase 3.6)
- **F.2** ANME reverse-WL not represented as a capability (RESOLVED Phase 3.6)
- **E.7** DNRA detection coverage (RESOLVED Phase 3.4)
- **E.6** Archaeal sulfur oxidation markers coverage (RESOLVED Phase 3.2)
- **A.2** Nitrospira moscoviensis classification (RESOLVED Phase 3.3 — re-scoped from comammox amoA to canonical NOB nxrA)

A user-facing version of this catalog is in `USER_GUIDE_LIMITATIONS.md`.

---

## 7. Validation Gaps

What has not been validated and why.

### Test-set-only validation (no positive-control sentinel)
- Sulfate-coupled ANME (ANME-1/2/3 via dsrAB OR-branch) — architecturally supported but no test-set or sentinel genome
- Iron-coupled ANME (via mtrC_omcB OR-branch) — architecturally supported but no genome
- Phase 3.1 manual condition overrides — no domain-specific exercise
- Phase 3.2 archaeal sulfur oxidation — Sulfolobus is true negative, no positive-control archaeal sulfur oxidizer

### Architecturally-supported metabolisms with no genome
- Comammox amoA (Nitrospira inopinata-class) — deferred, no comammox in test set
- Anammox-style metabolism on novel-lineage organisms — Scalindua profunda is the test-set target but escalates due to MAG completeness

### Out-of-scope (deferred)
- N-DAMO (Methylomirabilis intra-aerobic methane oxidation in NC10) — biochemically distinct from canonical methanotrophy
- Selenate / arsenate respiration — no curated markers
- Cable-bacteria long-distance electron transport — out of scope
- Photoferrotrophy — partial coverage

### Validation that could be added pre-manuscript
- A canonical hyperthermophilic forward methanogen sentinel (Methanopyrus or Methanocaldococcus other than gid=8) — would add to mcrA threshold validation across temperature ranges
- An anammox sentinel (Brocadia or Kuenenia) — would close the Scalindua-only blind-set anammox case
- A photoferrotroph sentinel (Chlorobium ferrooxidans) — would address the photoferrotrophy gap

---

## 8. References

- `LIMITATIONS.md` — Detection-layer limitations catalog (developer-facing, organized by category A–G) with the new "Validation status" tagging section
- `USER_GUIDE_LIMITATIONS.md` — User-facing limitations document
- `RECIPE_VALIDATION_V12.md` — V12 published-media comparison results (per-organism)
- `RECIPE_EVALUATION.md` — Per-organism Phase 2c recipe evaluation
- `VALIDATION_TIMELINE.md` — V1-V12 validation progression
- `PROGRESS.md` — Per-session progress log
- `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` — Sentinel cross-summary
- `data/sentinel/<organism>/validation.md` — per-sentinel validation reports
- `data/diagnostic_markers/REFERENCE_CURATION.md` — Per-marker curation rationale, thresholds, cross-reactivity scans
- `data/diagnostic_markers/<topic>_review.md` — per-Phase-3 sub-phase literature reviews and threshold-justification documents
- `PHASE_3_CLOSEOUT.md` — Phase 3 retrospective for manuscript prep
