# CultureForge Phase 3.3a Coverage Audit — Findings

**Date:** 2026-04-30 (post-Phase-3.2; pre-Phase-3.3 implementation)

**Audit deliverables:** This document synthesizes findings from
- `metabolism_master_list.md` — comprehensive metabolism enumeration (38 distinct metabolisms)
- `cultureforge_current_capabilities.md` — capability + marker inventory + per-organism classification status
- `coverage_map.md` — tabular gap analysis
- `phase3_prioritization.md` — ranked priority list
- `sentinel_organisms.md` — type-strain references for unaddressed metabolisms

## 1. Executive summary

| Metric | Count |
|---|---|
| Total energy metabolisms enumerated | ~38 (master list) |
| COVERED with diagnostic markers + correct test-set classification | 17 |
| PARTIAL (capability exists but lineage / architecture / context coverage incomplete) | ~11 |
| GAP (no capability, no markers) | ~13 |
| Test-set organisms with WRONG primary mode at the detection layer | 5 |
| Test-set organisms whose wrong-detection is fixed at the recipe-time mode pick | 2 (E. coli, Prometheoarchaeum) |
| Test-set organisms with WRONG recipe end-to-end (after recipe routing) | **3** |

The three remaining wrong-recipe organisms are:

1. **Nitrospira moscoviensis NSP M-1** (gid 23) — currently classified acetogenic with H₂/CO₂ recipe; should be lithoautotrophic NOB with NO₂⁻ as electron donor and aerobic atmosphere. This is a **GAP** — no nitrite-oxidation capability defined.
2. **Methanoperedens nitroreducens** (gid 28) — currently classified methanogenic with H₂/CO₂ recipe; should be ANME-2d with CH₄ + NO₃⁻ (reverse methanogenesis). This is a **directional ambiguity** in mcrA detection (LIMITATIONS C.1 + F.2).
3. **Scalindua profunda** (gid 30) — currently classified fermentative; should be anammox. This is a **MAG completeness** issue (LIMITATIONS E.1) — markers can detect Scalindua proteins at 60-76% identity but the predicted-protein set lacks them.

The audit confirms the impression from Phase 3.3 verification: CultureForge's coverage was assembled organically, and the most consequential gap is **canonical aerobic nitrite oxidation** — a major component of the global N cycle, performed by common environmental bacteria, currently invisible to the framework.

## 2. Top priority gaps

### Tier 1 (must address before external testing readiness)

1. **Canonical nitrite oxidation (NOB / nxrA)** — Phase 3.3 scope. HIGH frequency, CRITICAL severity, SIMPLE tractability. 5-7 days effort. Test-set Nitrospira moscoviensis directly affected.
2. **Aerobic methanotrophy (pmoA / mmoX)** — Phase 3.4 candidate. MEDIUM-HIGH frequency, CRITICAL severity, MODERATE tractability. 5-8 days effort. No test-set organism but high real-submission probability.
3. **DNRA (nrfA)** — Phase 3.5 candidate. MEDIUM-HIGH frequency, MAJOR severity, SIMPLE-MODERATE tractability. 4-6 days effort.

### Tier 2 (important for completeness)

4. **ANME directional fix (F.2 mitigation)** — Phase 3.6 candidate. MEDIUM frequency, CRITICAL severity, COMPLEX tractability. 7-10 days. Requires capability framework changes (relax acetogenesis negative-marker rule for new ANME category; add electron-acceptor co-occurrence rules).
5. **AAP atmosphere routing fix (C4)** — Phase 3.7 candidate. LOW-MEDIUM frequency, MAJOR severity, MODERATE tractability. 3-5 days. Recipe-router change rather than marker addition.

### Tier 3 (specialty / defer)

6-10. Photoferrotrophy, heliobacterial phototrophy, comammox amoA expansion, Mn(IV) reduction, neutrophilic Fe(II) oxidation. All LOW-MEDIUM frequency; specialty submissions.

### Tier 4 (defer indefinitely)

Selenate / arsenate / chlorate respiration, N-DAMO, sulfur disproportionation, cable bacteria, aerobic CO oxidation. LOW frequency or inherent biological complexity makes detection intractable from sequence data alone.

## 3. Phase 3 trajectory recommendation

Given the 12-week Phase 3 budget (~60 working days) and ~11 weeks remaining after Phase 3.2 closure:

**Recommended sequence (Tier 1 + Tier 2):**

| Sub-phase | Scope | Effort | Cumulative |
|---|---|---|---|
| Phase 3.3 | Canonical NOB (+ optional comammox amoA bundle) | 5-8 d | 8 d |
| Phase 3.4 | DNRA — architecturally similar to 3.3, builds on lithotrophic infrastructure | 4-6 d | 14 d |
| Phase 3.5 | Aerobic methanotrophy — highest external-readiness gain | 5-8 d | 22 d |
| Phase 3.6 | ANME F.2 mitigation — capability framework work | 7-10 d | 32 d |
| Phase 3.7 | One of: AAP routing / photoferrotrophy / heliobacterial — driven by user need | 3-7 d | 39 d |
| Phase 3.8 | Reserve for unforeseen issues + documentation polish | — | ~8-12 d |

**Total Tier 1+2 effort:** 24-39 days. Fits within budget with comfortable slack for unforeseen issues (every Phase 3 sub-phase to date has surfaced unexpected biology — Phase 3.2 found Sulfolobus DSM 639 lacks the canonical Sulfolobales sulfur-ox enzymes; Phase 3.3 verification found N. moscoviensis NSP M-1 lacks comammox amoA. Buffer for similar surprises is essential.).

**Decision points:**

1. After Phase 3.4 (DNRA): re-evaluate whether external testing should start in parallel. Tier 1 completed at this point.
2. After Phase 3.5 (methanotrophy): all major aerobic respiration variants except Cu-CODH are covered. Natural launch point for limited external testing in parallel with Tier 2 work.
3. After Phase 3.6 (ANME): validation of capability-framework changes. If F.2 mitigation works cleanly, Phase 3.7 priority becomes more flexible.

## 4. KEGG integration assessment

**Question:** would integrating KEGG pathway coverage solve CultureForge's coverage gap problem?

**Assessment: NO, KEGG integration would not solve the core problem.**

CultureForge already uses gapseq for pathway integrity scoring, and gapseq's pathway database includes most of KEGG's energy-metabolism pathways. The gapseq pathway scores ARE in the framework already.

The actual coverage gap is **diagnostic-marker-based capability detection** — i.e., the ability to BLAST predicted proteins against curated reference enzymes and use those hits to discriminate between metabolisms with similar pathway content. This is a different layer than pathway integrity.

For example: gapseq sees both ANME archaea and methanogens as having the methanogenesis pathway (both have mcrA + Wolfe-cycle enzymes). The discriminator between them is electron-acceptor partner detection (NarG, dsrAB, mtrC) and phylogenetic context — none of which a KEGG pathway map directly addresses.

Similarly, KEGG would add nitrite oxidation as a generic pathway entry, but the actual fix for Nitrospira moscoviensis is curated nxrA references with appropriate BLAST thresholds — not a generic KEGG pathway lookup.

**Recommendation:** treat KEGG as an ongoing reference for pathway-coverage cross-checks (it informs which metabolisms exist and what enzymes serve them — both already used during this audit), but do NOT integrate KEGG as a runtime data source. The runtime architecture (gapseq pathway integrity + curated diagnostic markers + pathway_definitions.json) is the right one; the gap is in marker / capability curation, which is what Phase 3 sub-phases address.

If at some point KEGG pathway IDs are useful to expose in JSON output for downstream tools, that's a small addition (per-step KEGG cross-references in pathway_definitions.json). But that's not a Phase 3 sub-phase — it would be a documentation polish, not a coverage fix.

## 5. External testing readiness assessment

**Current state (post-Phase-3.2):**

- 21 of 26 test-set organisms produce biologically-reasonable recipes (Phase 2c finding)
- 3 organisms produce wrong recipes attributable to GAPs (Nitrospira → no NOB; Methanoperedens → no ANME directional; Scalindua → MAG completeness)
- Phase 3.1 user-override flags provide an escape hatch for novel organisms (TEMPURA-not-in / GenomeSPOT-mispredicts cases)
- Phase 2e integration cleanup means the metric is honest and the JSON output is well-structured

**Limited external testing now:** plausible. External testers should be told:
- Tool is experimental
- Documented gaps (LIMITATIONS.md categories A-F + new G) cover the known wrong-recipe situations
- Expect ~80% of common cultivation-tractable organisms to receive reasonable recipes
- Lithoautotrophic nitrite oxidizers (Nitrospira, Nitrobacter) are a known GAP — recipe will be wrong; flag as Phase 3.3
- ANME archaea are a known GAP — recipe direction wrong; flag as Phase 3.6
- For organisms not in TEMPURA, manually supply `--temperature` etc. via Phase 3.1 overrides

**Full external testing readiness:** after Phase 3.5 (methanotrophy). At that point:
- All major aerobic respiration variants covered
- DNRA + canonical NOB closes the largest anaerobic + aerobic N-cycle gaps
- Methanotrophy closes the largest C-cycle gap

ANME directional fix (Phase 3.6) is desirable but not blocking — ANME organisms are uncommon in typical environmental microbiology submissions; the wrong recipe is documented; users can override the methanogenic call manually.

**Realistic timeline to "external-testing-ready" state:** ~3 weeks of focused Phase 3 work (Phases 3.3 + 3.4 + 3.5).

If external testing happens in parallel with Phase 3 work — recommended at the Phase 3.4/3.5 boundary — total time to broadly-applicable tool is the same but feedback loop tightens.

## 6. Verdict

**Top 3-5 priority gaps in order:**

1. **Phase 3.3 — Canonical aerobic nitrite oxidation (nxrA-based).** Fixes Nitrospira moscoviensis directly. Highest impact, simplest tractability, already pre-verified.
2. **Phase 3.4 — DNRA (nrfA-based).** Architecturally similar to Phase 3.3 — same lithotrophic-aerobic-acceptor pattern. Second-highest tractability.
3. **Phase 3.5 — Aerobic methanotrophy (pmoA + mmoX).** Closes the largest aerobic-respiration gap. MODERATE tractability due to pmoA / amoA cross-reactivity check.
4. **Phase 3.6 — ANME directional / F.2 mitigation.** Capability framework changes; fixes Methanoperedens. Higher complexity but high impact.
5. **Phase 3.7 — Reserve / specialty (AAP, photoferrotrophy, or heliobacterial).** Driven by external-testing feedback or user priority.

After this audit, **proceed with Phase 3.3** as the next concrete sub-phase.

## 7. Process observations from this audit

Three observations about the methodology, useful for ongoing Phase 3 governance:

1. **Pre-implementation verification has caught two scope errors so far** (Phase 3.2: Sulfolobus DSM 639 lacks the canonical Sulfolobales sulfur-ox enzymes; Phase 3.3: N. moscoviensis NSP M-1 lacks comammox amoA but has nxrA). Continuing the verification-before-curation pattern for each sub-phase is high-value.

2. **The audit surface area is narrower than the master list suggests.** ~38 metabolisms enumerated, but only ~5 gaps materially affect external-testing readiness. The rest are specialty / rare. Avoiding scope creep by sticking to Tier 1+2 for the 12-week budget is realistic.

3. **The capability framework is sufficient.** Phase 3 sub-phase work is reference curation + pathway-definition extension — not framework redesign. The one exception is Phase 3.6 (ANME directional), which requires careful work on the negative-marker rule architecture. That sub-phase deserves its own checkpoint when scoped.

---

## Files

- `data/coverage_audit/metabolism_master_list.md` (38 metabolisms)
- `data/coverage_audit/cultureforge_current_capabilities.md` (current state)
- `data/coverage_audit/coverage_map.md` (tabular gap analysis)
- `data/coverage_audit/phase3_prioritization.md` (ranked priorities)
- `data/coverage_audit/sentinel_organisms.md` (type-strain references)
- `data/coverage_audit/AUDIT_FINDINGS.md` (this document)
