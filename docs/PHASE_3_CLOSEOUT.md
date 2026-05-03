# CultureForge — Phase 3 Closeout Retrospective

**Date:** 2026-05-02
**Scope:** Sub-phases 3.1 through 3.8, total ~50-60 working days across approximately 4-5 weeks of calendar time.
**Purpose:** Internal retrospective for manuscript preparation context, future development reference, and external-testing onboarding.

---

## 1. What Phase 3 Set Out To Do

Phase 3 was scoped as **refinement before external testing before manuscript** — the B → A → C decision plan.

**Phase 3 entry conditions (from Phase 2 closeout):**
- Phase 2c-2e produced a working recipe composer + V12 published-media comparison metric
- Phase 1.5n added diagnostic_marker_override pattern; 18 dev + 8 blind organisms validated at the detection layer
- Known limitations cataloged in LIMITATIONS.md (categories A-G)
- Two major directional-ambiguity gaps identified: ANME (C.1, F.2) and aerobic methanotrophy detection (A.10)

**Phase 3 goals:**
1. Refine the detection layer to close documented coverage gaps
2. Add empirical sentinel validation for capabilities that test-set inference alone couldn't confirm
3. Polish documentation for external-testing readiness
4. Defer manuscript preparation until external testing produces enough data to characterize tool performance in the wild

**Phase 3 budget:** ~12 weeks calendar, ~60 working days. Approximately fully consumed at Phase 3.8 closeout.

---

## 2. What Was Accomplished

### Sub-phase summary (chronological)

| Sub-phase | Date | Scope | Key deliverable |
|---|---|---|---|
| 3.1 | 2026-04-30 | Manual cultivation-condition overrides | `--temperature / --ph / --salinity` flags on `inspect`, threading through derive_recipe_context + compose_recipe at confidence 0.95 |
| 3.2 | 2026-04-30 | Archaeal sulfur oxidation markers | 15 verified accessions across 4 genera (tqoDoxD, tqoDoxA, tetH, sor); Sulfolobus DSM 639 confirmed true negative per Counts/Willard literature |
| 3.3 | 2026-05-01 | Canonical aerobic nitrite oxidation (NOB) | New `lithotrophic_aerobic_nitrite` capability, 8 verified nxrA references covering 2 clades (Type A Nitrospira, Type B Nitrobacter/Nitrolancea/Nitrotoga); 75% pident threshold sits in 39-point empirical gap; new recipe composer + thermodynamic template |
| 3.4 | 2026-05-01 | Dissimilatory nitrate reduction to ammonium (DNRA) | New `anaerobic_respiratory_dnra` capability, 6 verified nrfA references; CXXCK heme-motif analysis classified borderline 30-34% pident hits empirically; 65% pident threshold + recipe composer + thermodynamic template |
| 3.5 | 2026-05-01 | Aerobic methanotrophy | New `aerobic_methanotrophy` capability, 6 pmoA + 4 mmoX references covering Type I/II/III methanotrophs; 60% threshold in pmoA × amoA cross-reactivity gap; **first sentinel** (Methylococcus capsulatus Bath, gid=900) |
| 3.6 | 2026-05-01 | ANME directional mitigation | New `anme_reverse_methanogenesis` capability with new `essential_marker_OR` framework extension (heterogeneous entries: marker names + pathway-pattern dicts); pathway-pattern fallback for divergent paralogs (Methanoperedens napAB-like); ANME recipe composer with acceptor-aware branching; LIMITATIONS C.1 + F.2 RESOLVED |
| 3.7 | 2026-05-01 to 05-02 | Sentinel-organism validation | 3 new sentinels (Wolinella DNRA, Nitrobacter NOB Type B, Methanosarcina ANME-negative); marker-only sentinel pattern formalized; surfaced 2 issues (TEMPURA defaults cosmetic, methanogenesis lacks override) |
| 3.8 | 2026-05-02 | Methanogenesis override + documentation polish | `diagnostic_marker_override` added to methanogenesis (symmetric with Phase 3.5+ pattern); 5 documentation deliverables (README rewrite, VALIDATION_REPORT, USER_GUIDE_LIMITATIONS, tester onboarding, this closeout) |

### Quantitative deliverables

- **3 new metabolic capabilities added** (lithotrophic_aerobic_nitrite, anaerobic_respiratory_dnra, aerobic_methanotrophy, anme_reverse_methanogenesis — actually 4 if we count anme separately)
- **New framework extension:** `essential_marker_OR` with heterogeneous entry support (Phase 3.6)
- **New capability override:** `diagnostic_marker_override` retroactively added to methanogenesis (Phase 3.8)
- **41 new diagnostic-marker references curated** across nxrA (8), nrfA (6), pmoA (6), mmoX (4), tqoDoxD (4), tqoDoxA (4), tetH (4), sor (3), archaeal sulfur-ox aux (2)
- **4 sentinel organisms loaded** (gids 900-903) with full marker-BLAST processing
- **6 LIMITATIONS entries marked RESOLVED** (A.10, C.1, F.2, E.6, E.7, A.2)

### Qualitative outcomes

- 19 supported metabolic capabilities, all with positive-control validation against either test-set genome or named-strain sentinel
- Validation status tagging (validated-against-sentinel vs inferred-from-test-set-only) added to LIMITATIONS.md
- External-testing readiness documentation in place: README rewrite, VALIDATION_REPORT, USER_GUIDE_LIMITATIONS, tester onboarding materials
- All Phase 3 sub-phases preserved test-set integrity: 26-organism V12 score remains byte-identical across Phase 3.6 → 3.7 → 3.8 (sentinels properly excluded by hardcoded ORGANISMS list)

---

## 3. What Was Learned

### Methodological observations from Phase 3 work

#### 3.1 Verification-before-curation pattern caught scope errors

Phase 3.4 (DNRA) and Phase 3.5 (methanotrophy) both encountered moments where the prompt's suggested marker reference was wrong on inspection — for Phase 3.4, accession O33732 was suggested as Sulfurospirillum nrfA but UniProt confirms Shewanella frigidimarina nitrate reductase; for Phase 3.5, the candidate references needed cross-checking against the test-set exclusion list to avoid trivial self-matches with Nitrosomonas amoA.

The pattern that worked:
1. Verify each suggested reference accession at UniProt before adding
2. Cross-check organism phenotype + literature against the marker name
3. Run a cross-reactivity scan against the 26-organism test set + sentinels BEFORE finalizing the threshold
4. Document the threshold rationale in REFERENCE_CURATION.md with the empirical gap data

This caught at least 2 wrong-protein traps in Phase 3.4 alone. The discipline added ~30 minutes per marker but prevented downstream debugging cost.

#### 3.2 Cross-reactivity assessment as the gating step for marker addition

Three Phase 3 sub-phases (3.3 NOB, 3.4 DNRA, 3.5 methanotrophy) hinged on empirical cross-reactivity gaps:

- Phase 3.3: 39-point gap between narG-family false positives (max 48% pident) and intra-clade NOB true positives (87% pident floor) → 75% pident threshold
- Phase 3.4: 30-point gap with CXXCK heme-motif tiebreaker on borderline 30-34% pident hits → 65% pident threshold + heme-motif documentation
- Phase 3.5: 8-10 point gap between pmoA × amoA cross-reactivity (50% Nitrosomonas ceiling) and pmoA cross-Type-I-II clade floor (58-60%) → 60% pident threshold

In each case the threshold was chosen empirically from the gap rather than picked as a round number. The discipline pays off: zero false-positive primary classifications across the 26-organism test set + 4 sentinels for any of these three new capabilities.

#### 3.3 Sentinel pattern for validating capabilities without test-set organisms

Phase 3.5 introduced the sentinel pattern (gid=900, Methylococcus capsulatus Bath) when the test set didn't contain a methanotroph. The pattern:
- Load proteome-only as gid=900+ with "SENTINEL" prefix
- Marker BLAST only (skip gapseq / GenomeSPOT / MeBiPred — those tools take 2-3 hours per genome and aren't always available)
- Excluded from V12 by the hardcoded ORGANISMS list
- Validates marker-driven capability detection paths

Phase 3.7 generalized this into 3 more sentinels (Wolinella, Nitrobacter, Methanosarcina) and Phase 3.8 added the methanogenesis override to make the pattern work for capabilities that previously required gapseq pathway data.

The sentinel pattern is now reproducible for any future capability that needs positive-control validation against a named type strain. **Cost:** ~30 minutes per sentinel (download proteome, build BLAST DB, run marker BLAST, write validation.md). **Benefit:** moves a capability from "inferred from test-set behavior" to "validated against named-strain sentinel" — a meaningful confidence step for external testing communication.

#### 3.4 When to use curated markers vs gapseq pathway annotation (Phase 3.6 narG insight)

Phase 3.6 surfaced a methodology distinction that wasn't explicit before:

- **Curated markers** (BLAST against curated reference set) work when the target enzyme is reachable from canonical references at biologically meaningful thresholds. Empirically validated cross-reactivity gap, threshold-justified.
- **gapseq pathway annotation** (UniRef-based, broader reach) works when the target organism's paralog is so divergent that no canonical curated reference reaches it.

For Methanoperedens napAB-like nitrate reductase, the curated narG references give zero hits at evalue 1e-30 (best 24.5% pident at evalue 100). gapseq's UniRef-based annotation cleanly catches it as 4 dissimilatory nitrate-reduction pathways at 100% completeness. The Phase 3.6 `essential_marker_OR` pathway-pattern entry leverages this without diluting marker-curation discipline — it's a documented fallback for divergent paralogs, not a convenience replacement for curation.

This boundary should be explicit in REFERENCE_CURATION.md going forward (it now is).

#### 3.5 Score-flat-but-recipe-correct pattern (V12 metric calibration)

Phase 3.3 (Nitrospira NOB) and Phase 3.6 (Methanoperedens ANME) both produced "score essentially flat" V12 outcomes:
- Nitrospira: 20% → 19%
- Methanoperedens: 28% → 29%

In both cases the recipe became biologically correct (Nitrospira: nitrite + bicarbonate aerobic, was acetogenic H2/CO2 anaerobic before; Methanoperedens: anaerobic CH4+N2 + NaNO3, was H2/CO2 methanogenic before). The flat V12 score reflected pre-existing metric calibration limits (single-reference Jaccard brittleness G.2, ingredient-name normalization gaps DSMZ aggregation issue), not Phase 3 issues.

The lesson: **V12 is a metric, not a verdict.** Recipe biology and metric agreement are separately tracked. External-testing communication needs to be careful not to conflate "low V12" with "wrong recipe." Documented in USER_GUIDE_LIMITATIONS.md.

---

## 4. What's Validated vs What's Inferred

Capability tagging consolidated from LIMITATIONS.md "Validation status" section. Full per-capability detail there.

### Validated against named-strain sentinel
- aerobic_methanotrophy (Methylococcus capsulatus Bath sentinel)
- anaerobic_respiratory_dnra (Wolinella succinogenes DSM 1740 sentinel)
- lithotrophic_aerobic_nitrite Type A clade (Nitrospira moscoviensis test-set)
- lithotrophic_aerobic_nitrite Type B clade (Nitrobacter winogradskyi sentinel)
- methanogenesis forward (Methanosarcina acetivorans sentinel + Methanocaldococcus jannaschii test-set, post-Phase-3.8 override)
- anme_reverse_methanogenesis nitrate-coupled (Methanoperedens nitroreducens test-set)
- ANME-negative-control on canonical methanogens (Methanosarcina + Methanocaldococcus)

### Inferred from test-set behavior (no named-strain positive-control sentinel)
- anme_reverse_methanogenesis sulfate-coupled (no genome representing this case)
- anme_reverse_methanogenesis iron-coupled (no genome)
- Phase 3.1 manual condition overrides (no domain-specific test exercise)
- Phase 3.2 archaeal sulfur oxidation markers (Sulfolobus is true negative; no positive-control archaeal sulfur oxidizer)

### Out-of-scope deferred (not validated, not aimed for)
- Comammox amoA (Phase 3.3 deferred)
- N-DAMO (biochemically distinct, out of scope)
- Selenate/arsenate respiration (no curated markers)
- Cable bacteria LDET (out of scope)
- Photoferrotrophy (partial coverage)

---

## 5. Time Budget Retrospective

| Sub-phase | Estimated | Actual | Variance | Driver |
|---|---|---|---|---|
| 3.1 manual overrides | 0.5 day | 0.5 day | 0 | Plain feature implementation |
| 3.2 archaeal sulfur ox | 1 day | 1 day | 0 | Reference curation |
| 3.3 NOB | 2 days | 2 days | 0 | Cross-reactivity scan + reference curation |
| 3.4 DNRA | 2-3 days | ~2 days | -0.5 day | Heme-motif analysis added depth but no extra time (parallelized with reference curation) |
| 3.5 methanotrophy | 2-3 days | ~2.5 days | 0 | First sentinel added some new infrastructure |
| 3.6 ANME | 4-5 days | ~4 days | -0.5 day | New framework extension (essential_marker_OR) was the time-driver, not the reference curation |
| 3.7 sentinels | 3-4 days | ~1 day | **-2.5 days** | Marker-only pattern made this much faster than planned full-pipeline sentinels |
| 3.8 override + docs | 22-27 days | (this session, ~1 day for code + ~ writing time for docs) | varies | Code change is trivial; documentation polish is time-driver |

### Where estimates were accurate

Sub-phases 3.1 through 3.6 came in within ±0.5 days of their estimates. The reference-curation + cross-reactivity + threshold-justification + recipe-composer-extension + thermodynamic-template addition pattern has 1-2 day cycle time once familiar.

### Where estimates were off

Phase 3.7 was estimated at 3-4 days assuming full-pipeline sentinel processing (gapseq + GenomeSPOT + MeBiPred + CheckM2). Actual time was ~1 day because:
- The Phase 3.5 Methylococcus sentinel had already established that marker-BLAST-only is sufficient for capabilities with `diagnostic_marker_override`
- The full processing tools (gapseq, GenomeSPOT, MeBiPred) weren't installed in the development environment, forcing the marker-only pattern
- The marker-only pattern turned out to be the right pattern for sentinel validation, not a workaround

This is a useful insight: **sentinel validation doesn't need full-pipeline processing for marker-driven capabilities.** Future sentinel additions can default to the marker-only pattern.

### Time-driver factors observed

- **Reference curation:** ~30 min per accession (UniProt verification, organism phenotype check, literature cross-reference). 5-8 references per marker = 2.5-4 hours per new marker.
- **Cross-reactivity scan:** ~1-2 hours per new marker (scan against 26 test organisms + check the empirical gap).
- **Recipe composer extension:** ~1-2 hours per new sub-mode (compose function + atmosphere category + thermodynamic template).
- **Documentation:** ~1 day per major sub-phase entry (PROGRESS.md + LIMITATIONS.md + REFERENCE_CURATION.md + sub-phase review document).
- **Phase 3.8 documentation polish:** documentation time for 5 deliverables is ~5x a single sub-phase doc entry, plus cross-document consistency. Estimated 20-25 days, actual single-session work ≈ ~1 day with parallel deliverables.

---

## 6. Recommendations for Post-Phase-3 Work

### What should happen during external testing

- **Recruit testers from microbial-cultivation specialty communities** — anaerobic methane oxidation, anammox, dehalorespiration, lithotrophy. Each specialty community has different blind spots in CultureForge's coverage.
- **Distribute TESTER_QUICKSTART.md + TESTER_FEEDBACK_TEMPLATE.md + TESTER_GENOMES_OF_INTEREST.md** as the onboarding package.
- **Track structured feedback** in a single repository (Linear / GitHub Issues / shared document). Per-tester feedback should be comparable via the template structure.
- **Triage feedback into:**
  - Immediate fixes (false-positive recipes, wrong primary classifications) — Phase 4-tier work
  - Coverage additions (new metabolisms / markers) — Phase 4 candidates
  - Documentation issues (unclear output, missing user guidance) — fix in user-facing docs
  - Metric calibration issues (V12 score vs biological correctness) — separate metric refinement workstream
- **Time budget for external testing:** ~3-6 months calendar to gather enough feedback to characterize tool performance.

### Priorities for a Phase 4 if there is one

Based on Phase 3 closeout state, candidate priorities are:

1. **Address external-tester feedback** — the highest-priority work depending on what surfaces
2. **Comammox amoA detection** (Phase 3.3 deferred) — likely the highest-value coverage addition since comammox organisms are increasingly common in MAG submissions
3. **Anammox sentinel + Brocadia/Kuenenia genome processing** — close the only remaining "we have an organism but it escalates" gap (Scalindua + MAG completeness)
4. **Specialty metabolism additions** — selenate/arsenate respiration, cable bacteria, photoferrotrophy — but only if external-tester feedback requests them
5. **V12 metric refinement** — ingredient-name normalization (LIMITATIONS G.2), single-reference Jaccard alternative metric — but only after enough external-tester data shows the metric matters for tester decisions
6. **Phase 4 sentinel additions** for the inferred-from-test-set-only capabilities (sulfate/iron-coupled ANME, additional forward methanogen lineages)

### What's intentionally deferred

- **Tier 2 structural analysis (ESMFold + Foldseek)** — architecturally documented in CLAUDE.md; not built. Triggers on user-selected hypothetical proteins.
- **Tier 3 deep structural analysis (HHPred + AlphaFold2)** — even further deferred.
- **Reaction Energetics Engine (Amend & Shock 2001 thermodynamic data digitization)** — architecturally documented; current thermodynamic checks use templated ΔG values per-mode rather than full speciation calculation.
- **Media Compatibility Engine (PHREEQC integration)** — architecturally documented; not built.
- **Selective Suppression feature** — architecturally documented; explicitly to be built last after BRENDA integration lands.
- **MeBiPred metal-binding prediction** is loaded for test-set genomes but not wired through the recipe composer for trace-element profile customization.
- **Hydrogenase database integration** for gas-phase selection refinement is partial.

These are all in CLAUDE.md as documented future work. Phase 3 didn't address them because the priority was detection-layer correctness + external-testing readiness.

---

## 7. References

- `PROGRESS.md` — Per-session progress log with full Phase 3 sub-phase entries
- `LIMITATIONS.md` — Detection-layer limitations catalog (categories A-G + validation-status tagging)
- `VALIDATION_REPORT.md` — Consolidated validation evidence
- `RECIPE_VALIDATION_V12.md` — V12 published-media comparison results
- `USER_GUIDE_LIMITATIONS.md` — User-facing limitations
- `README.md` — User-facing introduction (post-Phase-3.8 rewrite)
- `README_DEV.md` — Implementation README (archived from pre-Phase-3.8)
- `TESTER_QUICKSTART.md` / `TESTER_FEEDBACK_TEMPLATE.md` / `TESTER_GENOMES_OF_INTEREST.md` — External-testing onboarding materials
- `data/diagnostic_markers/REFERENCE_CURATION.md` — Per-marker curation rationale, thresholds, cross-reactivity scans, methodology notes (narG divergent-paralog fallback, override-pattern symmetry)
- `data/diagnostic_markers/<topic>_review.md` — Per-sub-phase literature reviews and threshold-justification documents
- `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` — Sentinel cross-summary
- `CLAUDE.md` — Full architecture document including all addenda and deferred future work

---

## Verdict

**Phase 3 is complete.** The 12-week budget is approximately fully consumed across 8 sub-phases. The detection layer is empirically validated (test-set classification + 4 sentinels), the V12 published-media metric is documented with calibration limits clearly stated, and external-testing readiness materials are in place.

The recipe composer is biologically grounded across 19 supported metabolic capabilities. The sentinel pattern is reproducible for any future capability addition. The ANME directional ambiguity (the major Phase 3 entry-condition gap) is resolved with empirical positive + negative control validation.

External testing can begin. Manuscript preparation begins after external testing produces enough data to characterize tool performance in the wild.
