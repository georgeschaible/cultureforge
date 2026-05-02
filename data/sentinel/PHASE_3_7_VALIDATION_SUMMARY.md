# Phase 3.7 Cross-Sentinel Validation Summary

**Date:** 2026-05-02
**Scope:** Three sentinel organisms loaded as gid=901, 902, 903 (excluded from V12 by hardcoded ORGANISMS list, gid 7-32 only). Each sentinel validates a Phase 3 sub-phase capability that previously had only test-set inference rather than empirical positive-control validation.

## Pipeline pattern

All three sentinels use the **marker-BLAST-only pattern** established by Phase 3.5 Methylococcus capsulatus Bath (gid=900): proteome download from NCBI RefSeq, BLAST DB build against the curated marker references, no gapseq / GenomeSPOT / MeBiPred run. This pattern works for capabilities that use `diagnostic_marker_override` (override_confidence path); it does not work for capabilities that require gapseq pathway integrity scores.

## Per-sentinel results

| Sentinel | gid | Validates | Primary mode expected | Primary mode observed | Recipe matches reference | Verdict |
|---|---:|---|---|---|---|:---:|
| Wolinella succinogenes DSM 1740 | 901 | Phase 3.4 (DNRA via NrfA) | anaerobic_respiratory_dnra | anaerobic_respiratory (DNRA via NrfA) | DSMZ Medium 720 architecture: formate + nitrate + bicarbonate, anaerobic | **PASS** (8/9 criteria; 1 GAP: temp default) |
| Nitrobacter winogradskyi Nb-255 | 902 | Phase 3.3 (NOB Type B clade) | lithotrophic_aerobic_nitrite | lithotrophic_aerobic (nitrite oxidation, canonical NOB) | DSMZ Medium 756 architecture: NaNO2 + NaHCO3 + phosphate, aerobic | **PASS** (11/12 criteria; 1 GAP: temp default within 2°C) |
| Methanosarcina acetivorans C2A | 903 | Phase 3.6 (ANME false-positive prevention) | methanogenic (NOT anme) | escalated, but ANME correctly does NOT fire | n/a (escalated) | **PARTIAL PASS** (critical false-positive prevention: PASS; methanogenic-as-primary: GAP — see narrative) |

## What's now validated vs. inferred

After Phase 3.7, the validation status of Phase 3 capabilities is:

### Validated against named-strain sentinel
- **aerobic_methanotrophy** — Methylococcus capsulatus Bath sentinel (gid=900, Phase 3.5)
- **anaerobic_respiratory_dnra** — Wolinella succinogenes DSM 1740 sentinel (gid=901, Phase 3.7)
- **lithotrophic_aerobic_nitrite (Type B clade arm)** — Nitrobacter winogradskyi Nb-255 sentinel (gid=902, Phase 3.7)
- **lithotrophic_aerobic_nitrite (Type A clade arm)** — Nitrospira moscoviensis test-set genome (gid=23, Phase 3.3)
- **anme_reverse_methanogenesis (positive case, nitrate-coupled)** — Methanoperedens nitroreducens test-set genome (gid=28, Phase 3.6)
- **anme_reverse_methanogenesis (negative-control: forward methanogen)** — Methanosarcina acetivorans C2A sentinel (gid=903, Phase 3.7) **and** Methanocaldococcus jannaschii test-set genome (gid=8). Forward methanogen does NOT trigger ANME false positive.

### Validated against test-set genome only (no named-strain sentinel)
- **methanogenesis (forward)** — Methanocaldococcus jannaschii (gid=8), classifies methanogenic at 0.753. Sentinel-pattern reproduction blocked by gapseq dependency in capability score (no `diagnostic_marker_override`).
- **anme_reverse_methanogenesis (sulfate-coupled, ANME-1/2/3)** — architecturally supported via dsrAB OR-branch but no test-set or sentinel genome.
- **anme_reverse_methanogenesis (iron-coupled)** — architecturally supported via mtrC_omcB OR-branch but no test-set or sentinel genome.
- All other Phase 3.1 / 3.2 capabilities (manual condition overrides, archaeal sulfur oxidation markers) — validated only by test-set behavior, no positive-control sentinel.

## Issues surfaced

### Marker-only sentinel pipeline limitations
1. **TEMPURA / GenomeSPOT temperature defaults** (Wolinella, Nitrobacter): Sentinels default to 30°C because no TEMPURA / GenomeSPOT data is loaded. Wolinella optimum is ~37°C; Nitrobacter optimum is ~28°C. Recipe outputs are biologically reasonable but not species-specific. **Severity: cosmetic.** A lightweight TEMPURA-lookup hook in the sentinel-load pipeline would resolve this without requiring full integrate_tempura.py runs.

2. **Methanogenesis capability requires gapseq pathway data** (Methanosarcina): The `methanogenesis` capability has no `diagnostic_marker_override` mechanism (unlike `aerobic_methanotrophy`, `anaerobic_respiratory_dnra`, `lithotrophic_aerobic_nitrite`). Without gapseq pathway integrity scores, mcrA + acsB_cdhC + cooS_cdhA markers score 0.375 — below the 0.50 firing threshold. **Severity: blocks marker-only sentinel pattern for forward methanogens.** The fix is symmetric with Phase 3.5's methanotrophy override: add a `diagnostic_marker_override` keyed on mcrA (with WL-carbonyl markers as an OR-supporting signal). Phase 3.8 candidate.

### Phase 3.6 false-positive prevention validation
**The critical Phase 3.6 test passes decisively.** Methanosarcina acetivorans has 100% pident mcrA self-hit + complete Wood-Ljungdahl carbonyl branch (acsB_cdhC at 92.8%, cooS_cdhA at 91.7%) — the strongest possible "looks like a methanogen" signal. The ANME discriminator's OR-group (dsrAB / mtrC_omcB / gapseq nitrate-pwy) correctly resolves to all-negative on Methanosarcina, capping ANME confidence at 0.40. mcrA presence alone does not promote ANME. The Phase 3.6 architecture works as designed.

## V12 validation byte-identity verification

After loading sentinels gid=901, 902, 903:
- gid=7 (Nitratidesulfovibrio vulgaris): 67% — matches Phase 3.6 baseline
- gid=8 (Methanocaldococcus jannaschii): 55% — matches Phase 3.6 baseline
- gid=28 (Methanoperedens nitroreducens): 29% — matches Phase 3.6 baseline
- gid=32 (E. coli): 100% — matches Phase 3.6 baseline

V12 scores are byte-identical to the Phase 3.6 closeout baseline. Sentinels are correctly excluded by the hardcoded ORGANISMS list in the validation script. No regression from sentinel additions.

## Recommendation for Phase 3.8 scope

Phase 3.7 validation surfaced two actionable items:

1. **Methanogenesis `diagnostic_marker_override`** (medium priority): Adds symmetry with the methanotrophy override pattern, enables marker-only sentinel validation of forward methanogens, and would not change behavior for test-set genomes (which have gapseq pathway data). Low risk, low effort.

2. **Sentinel-pipeline TEMPURA-lookup hook** (low priority, polish): Would let sentinels report species-specific temperature optima without requiring full integrate_tempura.py runs. Cosmetic improvement to sentinel reports.

Neither item is blocking. Both could be deferred to a later sub-phase if Phase 3.8 priorities are user-facing documentation, README rewrite, and external-testing onboarding materials.

**Overall verdict:** Phase 3.7's empirical validation goal is achieved. The three Phase 3 sub-phases that previously had only test-set inference (Phase 3.3 Type B NOB, Phase 3.4 DNRA, Phase 3.6 ANME-negative control) now have positive-control sentinel validation against named type strains. The capability framework is empirically sound; the surfaced issues are pipeline-pattern limitations rather than detection-logic bugs.
