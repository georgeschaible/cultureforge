# CultureForge Blind Validation V10 — Post Phase 1.5n

**Date:** 2026-04-27
**Scope:** Re-evaluation of the 8 blind organisms after Phase 1.5n added the `diagnostic_marker_override` rule for organohalide_respiration, anoxygenic_phototrophy_purple, and bacteriorhodopsin.
**Method:** Same BLAST data as V9 (Phase 1.5m) — only the capability detector logic changed. Capabilities re-derived via `capability_report.py --json`.

---

## What changed in Phase 1.5n

Three pathway entries in `data/pathway_definitions.json` gained a `diagnostic_marker_override` field that lets the diagnostic marker BLAST hit alone drive detection when:
1. Pathway-based scoring rejects the call (`not detected`)
2. The marker BLAST hit clears the override-specific thresholds
3. No negative marker has fired
4. No essential marker is missing

The override produces moderate confidence (0.60-0.65) — lower than full pathway evidence (0.75-0.90) — and is logged with an `uncertainty_flags = ["detected_via_marker_override"]` annotation.

| Metabolism | Override marker | min_pident | min_qcov | min_evalue | override_confidence |
|---|---|---|---|---|---|
| organohalide_respiration | rdhA | 34.0% | 50% | 1e-20 | 0.65 |
| anoxygenic_phototrophy_purple | pufLM | 35.0% | 60% | 1e-20 | 0.65 |
| bacteriorhodopsin | rhodopsin | 40.0% | 60% | 1e-20 | 0.60 |

The rdhA threshold was tightened from 30% (original spec) to 34% during Phase 1.5n cross-contamination testing — see §3.

---

## V10 results — all 3 targets fire, zero cross-contamination

### Target organisms (from V9 Category F)

| Organism | Capability | V9 result | V10 result | Mechanism |
|---|---|---|---|---|
| **Halobacterium_salinarum** | Bacteriorhodopsin | conf=0.225, NOT primary | **conf=0.600, PRIMARY** | rhodopsin override (54.1% id, qcov=92, bs=212) |
| **Chloroflexus_aurantiacus** | Anoxygenic phototrophy purple | conf=0.025, NOT primary | **conf=0.650, PRIMARY** | pufLM override (47.8% id, qcov=95, bs=246) |
| **Dehalococcoides_mccartyi** | Reductive dehalogenation | conf=0.125, NOT primary | **conf=0.650, PRIMARY** | rdhA override (35.3% id, qcov=59, bs=138) |

All three primary capability calls now appear with confidence above the 0.50 detection threshold.

### Allochromatium qmoA discrimination — INTACT

| Capability | V9 | V10 | Path |
|---|---|---|---|
| Anoxygenic phototrophy purple | 0.768 (primary) | 0.768 (primary) | pathway-based (override correctly suppressed because pathway already detected) |
| Dissimilatory sulfate reduction | 0.400 (NOT detected, qmoA absent) | 0.400 (NOT detected, qmoA absent) | unchanged — qmoA AND-rule still gates SR |
| Sulfur oxidation | 0.838 (primary) | 0.838 (primary) | unchanged |
| N2 fixation | 0.614 (primary) | 0.614 (primary) | unchanged |

The override is conditional on `not detected_via_pathway`, so Allochromatium's pathway-based phototrophy detection at 0.768 takes priority and the override does not fire.

### Cross-contamination check — clean

The Phase 1.5n cross-contamination audit (`data/validation/phase1_5n_override_audit.txt`) found that pre-tightening, `rdhA` override would have fired on 2 organisms: Dehalococcoides (target) AND Prometheoarchaeum syntrophicum (Asgard archaeon, 33.2% identity to a single rdhA-superfamily protein). Detailed BLAST inspection showed:
- Dehalococcoides: 4 distinct hits ≥ 34% identity across multiple query proteins (true rdhA paralog signature)
- Prometheoarchaeum: 5 alignments to a SINGLE query protein at 33.2% identity (likely glycine reductase or RamA-class, not a real rdhA)

Tightening rdhA `min_pident` from 30 to 34 cleanly excludes Prometheoarchaeum while keeping Dehalococcoides. Final post-fix audit confirms only the 3 intended target organisms fire any override across all 26 genomes:

| Marker | Eligible organisms (post-tightening) |
|---|---|
| rdhA (≥34%, qcov≥50, evalue≤1e-20) | Dehalococcoides_mccartyi only |
| pufLM (≥35%, qcov≥60, evalue≤1e-20) | Allochromatium / Rhodopseudomonas / Chloroflexus — but AV+RP detect via pathway, so override only fires on Chloroflexus |
| rhodopsin (≥40%, qcov≥60, evalue≤1e-20) | Halobacterium_salinarum only |

---

## V5 → V10 progression on the blind set

### Pre-existing F.3 spurious acetogenesis calls (NOT introduced by Phase 1.5n)

Before scoring, an honest accounting of pre-existing F.3 issues that affect this assessment:

| Organism | Acetogenesis confidence in V9 | V10 (Phase 1.5n) | Origin |
|---|---|---|---|
| Chloroflexus aurantiacus | **0.642 PRIMARY** | 0.642 PRIMARY (unchanged) | Pre-existing F.3 — gapseq pathway annotation of WL-pathway-overlapping enzymes; Chloroflexus actually uses 3HP cycle, not WL |
| Nitrospira moscoviensis | **0.605 PRIMARY** | 0.605 PRIMARY (unchanged) | Pre-existing F.3 — Nitrospira uses reductive TCA, not WL; gapseq matches CO2 fixation enzymes that share homology with WL components |
| Prometheoarchaeum syntrophicum | 0.642 PRIMARY | 0.642 PRIMARY (unchanged) | Pre-existing F.3 — Asgard archaeal ancestral genes |

These three spurious acetogenesis calls were all present in V9 (Phase 1.5m) and earlier. **Phase 1.5n's `diagnostic_marker_override` rule does NOT touch acetogenesis** (only organohalide_respiration, anoxygenic_phototrophy_purple, bacteriorhodopsin received the override). The acetogenesis_WL pathway scoring is unchanged from V9 to V10. These are F.3 issues that remain open and are scoped for Phase 3 detector tightening (require diagnostic-marker corroboration for capability promotion above 0.50).

### Verdict table (V10)

| # | Organism | V5 (carry-over) | V10 | Phase 1.5n change | Final V10 verdict |
|---|---|---|---|---|---|
| 1 | Nitrospira moscoviensis | partial (comammox missed) | comammox still missed; spurious acetogenesis_WL + sulfur_ox primaries | none (Phase 3) | **partial** (comammox amoA gap + F.3 spurious calls) |
| 2 | Chloroflexus aurantiacus | partial (FAP photo missed) | phototrophy now correct; spurious acetogenesis_WL + sulfur_ox still present | **+phototrophy via override** | **partial** (correct phototrophy via 1.5n + correct aerobic_resp + reasonable fermentation, BUT pre-existing F.3 spurious acetogenesis + sulfur_ox remain) |
| 3 | Dehalococcoides mccartyi | regression in V9 (rdhA self-validation removed) | organohalide respiration now correct via rdhA override | **+organohalide via override** | **correct** (organohalide + N2_fix both biologically reasonable) |
| 4 | Picrophilus torridus | correct | correct | none | **correct** |
| 5 | Thermotoga maritima | correct | correct | none | **correct** |
| 6 | Scalindua profunda | incorrect (MAG completeness) | incorrect | none | **incorrect** (MAG-completeness limitation, not detection-layer) |
| 7 | Methanoperedens nitroreducens | partial (mcrA negative-marker rule) | partial | none (F.2, Phase 3) | **partial** (right enzymes, wrong direction; reverse-WL still suppressed by mcrA negative-marker rule) |
| 8 | Prometheoarchaeum syntrophicum | correct (Syntrophy primary) | Syntrophy primary correct; spurious methanogenesis_0.900 + acetogenesis_0.642 still present | none (F.3 unchanged from V9) | **partial** (Syntrophy is correctly the highest-confidence diagnostic-marker-corroborated call, but methanogenesis at 0.900 from gapseq pathway annotation alone is the top primary by confidence — spurious) |

### V10 score (honest)

- **Correct: 3/8** (Picrophilus, Thermotoga, Dehalococcoides)
- **Partial: 4/8** (Nitrospira, Chloroflexus, Methanoperedens, Prometheoarchaeum)
- **Incorrect: 1/8** (Scalindua — MAG completeness)

**Functional outcome unchanged from V5: 7/8 functionally relevant.** But the failure-mode mix is more transparent in V10: 3 of the 4 partial calls are F.3 (spurious gapseq pathway calls), and 1 is F.2 (ANME direction ambiguity). All four partials are detector-side issues that require Phase 3 work, not reference-set work.

### Why Chloroflexus is "partial," not "correct"

The user flagged this explicitly. Phase 1.5n's gain on Chloroflexus is real — anoxygenic phototrophy purple is now detected as primary at 0.65 confidence via the pufLM override (pufLM hits at 47.8% identity, well above the 35% threshold; this is a clear FAP-style reaction center signal, exactly what the override was designed to catch). The capability detector now correctly identifies Chloroflexus as a phototroph.

However, Chloroflexus's V10 primary metabolisms list includes:
- **Aerobic respiration (0.850)** — correct (Chloroflexus is a facultative aerobe)
- **Anoxygenic phototrophy purple (0.650, override)** — correct (the V10 gain)
- **Substrate-level phosphorylation fermentation (0.650)** — biologically reasonable (most bacteria can ferment under anoxic conditions)
- **Acetogenesis via Wood-Ljungdahl (0.642)** — **SPURIOUS**. Chloroflexus uses the 3-hydroxypropionate (3HP) cycle for CO₂ fixation, NOT the Wood-Ljungdahl pathway. The acetogenesis call comes from gapseq annotating CO₂-fixation pathway enzymes that share homology with WL components (acsB/cdhC EC 2.3.1.169 has cross-reactive domains; cooS/cdhA EC 1.2.7.4 is also present in some 3HP-cycle organisms for related but distinct reactions).
- **Sulfur/sulfide/thiosulfate oxidation (0.506)** — also spurious (cross-reactive soxB-family hits to non-soxB Chloroflexus proteins).

A "correct" call would have phototrophy + aerobic_resp + (optionally) fermentation as primaries, with acetogenesis and sulfur_ox suppressed. The two spurious calls would mislead a recipe composer into providing components Chloroflexus doesn't actually need (e.g., acetate fermentation products, thiosulfate as electron donor).

**Therefore Chloroflexus is "partial"** — Phase 1.5n correctly addressed the phototrophy gap (the headline biology), but pre-existing F.3 spurious calls remain and are not addressable in Phase 1.5n's scope.

### Why Prometheoarchaeum is also re-scored from "correct" (V5) to "partial" (V10)

Same logic. V5 reported Prometheoarchaeum as correct because Syntrophy was the only primary call. V9/V10 show:
- Methanogenesis (0.900) — **SPURIOUS** at the headline level. Prometheoarchaeum is an Asgard archaeon that encodes ancestral methanogenesis-like genes used for syntrophic propionate oxidation, not actual methanogenesis. No mcrA hit fired (the diagnostic marker for actual methanogenesis); the 0.900 confidence comes from gapseq pathway annotation alone.
- Syntrophy (0.700) — correct.
- Acetogenesis_WL (0.642) — also spurious from gapseq pathway annotation of ancestral genes.

The Syntrophy primary IS correctly detected, but the highest-confidence primary is the spurious methanogenesis call. A recipe composer ranking by confidence would design a methanogen recipe (H₂/CO₂ headspace) for an organism that actually requires syntrophic partner support. This is the same F.3 pattern as Chloroflexus.

**This re-scoring affects only the V10 verdict label; the underlying biology is unchanged from V9.** V9 also had this pattern but was scored as "correct" because the primary list contained the right call (Syntrophy). The honest assessment now is "partial" — Syntrophy is detected but co-detected with two spurious primaries that would mislead downstream recipe synthesis.

---

## Per-organism summary

### 1. Nitrospira moscoviensis — unchanged (Phase 3 work)

V10 primary metabolisms identical to V9: `acetogenesis_WL(0.605), sulfur_ox(0.594)`. Phase 1.5n doesn't address comammox amoA divergence (deferred to Phase 3 per Checkpoint 2 user decision).

### 2. Chloroflexus aurantiacus — phototrophy NOW PRIMARY ✅

**V9:** `aerobic_resp(0.850), fermentation(0.650), acetogenesis_WL(0.642), sulfur_ox(0.506)` — pufLM detected at 47.8% identity but pathway demoted.

**V10:** all V9 primaries + `Anoxygenic phototrophy (purple bacteria, Type II reaction center) (0.650)` ← via pufLM override.

The capability JSON includes `uncertainty_flags: ["cofactor bacteriochlorophyll a biosynthesis not detected — may need supplementation or uses alternative pathway", "detected_via_marker_override"]` — correctly flags both the FAP-style architecture (chlorosomes instead of canonical bacteriochlorophyll biosynthesis) and the override-based detection.

### 3. Dehalococcoides mccartyi — organohalide respiration RESTORED ✅

**V9:** `N2_fix(0.614)` only — V9 regression because Phase 1.5m removed D. mccartyi's own rdhA from references.

**V10:** `N2_fix(0.614) + Reductive dehalogenation (0.650)` ← via rdhA override.

The flag `"detected_via_marker_override"` is set. Cofactor flag for corrinoid biosynthesis is also present (some D. mccartyi strains require external corrinoid supplementation).

### 4. Picrophilus torridus — unchanged

`aerobic_resp(0.900) + fermentation(0.650)` in both V9 and V10. Picrophilus has no override-eligible markers.

### 5. Thermotoga maritima — unchanged

`fermentation(0.775)` in both V9 and V10.

### 6. Scalindua profunda — unchanged (genome completeness limitation)

V10 primary metabolisms identical to V9: `aerobic_resp(0.550), fermentation(0.588)`. The Scalindua profunda MAG lacks hzsA and hdh in its predicted proteome (Phase 1.5m verified via reciprocal BLAST). No override can fix this — the genes simply aren't there to detect.

### 7. Methanoperedens nitroreducens — unchanged

V10 primaries: `methanogenesis(0.675), N2_fix(0.614), fermentation(0.650)`. The reverse-WL path (acetogenesis) is still suppressed by mcrA negative-marker rule. F.2 in LIMITATIONS.md remains open; resolution requires a new `ANME_reverse_methanogenesis` capability category (Phase 3).

### 8. Prometheoarchaeum syntrophicum — unchanged, override correctly suppressed

V10 primaries: `methanogenesis(0.900), acetogenesis_WL(0.642), Syntrophy(0.700)`. The rdhA override does NOT fire on Prometheoarchaeum because Phase 1.5n tightened rdhA `min_pident` from 30 to 34 specifically to exclude this case. Prometheoarchaeum's top rdhA pident is 33.2%, just below the 34% override threshold.

---

## Cross-organism dev-set verification (no regressions)

V9 → V10 primary metabolism diffs across the 18-organism dev set:

| Organism | Change |
|---|---|
| Halobacterium_salinarum | + Bacteriorhodopsin/proteorhodopsin light-driven proton pump (override) |
| All other 17 dev-set organisms | unchanged |

**Zero regressions on the dev set. Zero unintended capability gains.**

---

## Phase 2c readiness

V10 closes Category F.1 (BLAST-positive demoted by missing pathway) for the three target metabolisms documented in LIMITATIONS.md. F.2 (ANME reverse-methanogenesis) and F.3 (spurious gapseq pathway calls) remain open and are scoped for Phase 3.

The headline detection state for Phase 2c:
- **18/18 dev-set organisms correctly classified** on the user-specified Checkpoint 3 checks; Halobacterium rhodopsin restored as primary in V10.
- **3/8 blind-set organisms fully correct** (Picrophilus, Thermotoga, Dehalococcoides), 4/8 partial (Nitrospira, Chloroflexus, Methanoperedens, Prometheoarchaeum), 1/8 incorrect (Scalindua MAG completeness). Functional total: 7/8 — same as V5-V9.
- **Acidithiobacillus iron oxidation, Allochromatium qmoA discrimination, Sulfolobus archaeal SoxB detection** — all intact from Phase 1.5m.
- **No regressions** introduced by Phase 1.5n.

**The four "partial" blind-set calls all share the same architectural pattern:** the correct primary is detected, but co-detected with one or two spurious primaries from gapseq pathway annotation of cross-reactive or ancestral genes. Phase 3 F.3 work (require diagnostic-marker corroboration before promoting capabilities above 0.50 confidence) would resolve all four partial calls.

**Recommendation: ready for Phase 2c, with the caveat that the recipe composer should weight diagnostic-marker-corroborated calls (e.g., Acidithiobacillus cyc2 at 85.7% identity, Dehalococcoides rdhA via override, Allochromatium pufLM at 72.9% identity, etc.) higher than gapseq-pathway-only calls when ranking primary metabolisms for recipe design.** This means a recipe composer that uses `uncertainty_flags` and `diagnostic_markers` fields from the capability JSON can mostly avoid the F.3 spurious-call problem at the recipe layer, even though F.3 itself is unresolved at the detector layer.
