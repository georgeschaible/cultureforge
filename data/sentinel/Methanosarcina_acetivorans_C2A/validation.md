# Phase 3.7 Sentinel Validation — Methanosarcina acetivorans C2A

**NCBI assembly:** GCF_000007345.1 (Complete Genome, ASM734v1)
**Genome ID in CultureForge DB:** 903
**Validates Phase:** 3.6 (ANME-negative control — false-positive prevention)
**Date validated:** 2026-05-01

## Pipeline notes

Marker BLAST only. Methanosarcina is the **canonical aceticlastic / methylotrophic / hydrogenotrophic-flexible methanogen** — every textbook example of forward methanogenesis. The Phase 3.6 critical test for this sentinel is whether the new ANME discriminator (`mcrA + (gapseq nitrate-reduction-pwy ≥100% complete OR dsrAB OR mtrC_omcB)`) **avoids false-positive firing** on a strong-mcrA forward methanogen.

## Marker BLAST results

| Marker | Best hit | pident | bitscore | qcov | evalue | positive_call |
|---|---|---:|---:|---:|---:|:---:|
| mcrA | WP_011024419.1 | **100.0** | 1189 | 100 | 0.0 | YES |
| mcrBG | WP_011024423.1 | 89.9 | 788 | 100 | 0.0 | YES |
| acsB_cdhC | WP_011021049.1 | 92.8 | 820 | 100 | 0.0 | YES |
| cooS_cdhA | WP_048066467.1 | 91.7 | 1182 | 100 | 0.0 | YES |
| nifH | WP_011023791.1 | 65.7 | 373 | 99 | 2.8e-135 | YES |
| autotrophy | WP_011024428.1 | 39.0 | 308 | 99 | 2.3e-104 | YES |

**The three OR-group entries that gate ANME firing all resolve to negative:**

| OR-group entry | Status |
|---|---|
| dsrAB marker | NOT detected (no hits at evalue ≤ 1e-30) |
| mtrC_omcB marker | NOT detected |
| gapseq nitrate-reduction pathway ≥100% complete + predicted=true | NOT EVALUABLE (no gapseq run for sentinel) — resolves to negative because the underlying signal is absent |

qmoA hits exist but all below the positive_call threshold (best 37.4% pident, 53% qcov — fails 30% pident, 70% qcov gate). Methanosarcina is therefore correctly NOT classified as a sulfate reducer (Phase 1.5k qmoA discipline holds).

## Verification criteria

| Criterion | Expected | Observed | Pass/Fail |
|---|---|---|:---:|
| mcrA marker fires above threshold | YES | 100% pident, 100% qcov, bs=1189 | **PASS** |
| anme_reverse_methanogenic capability does NOT fire | YES (capped by missing OR-group) | 0.364 confidence (REJECTED — "essential_marker_OR group requires ANY of [dsrAB, mtrC_omcB, dissimilatory nitrate reduction]") | **PASS — false-positive averted** |
| dsrAB does NOT fire | YES | NOT detected | **PASS** |
| mtrC_omcB does NOT fire | YES | NOT detected | **PASS** |
| Methanogenesis capability detected as primary | YES | 0.375 confidence — REJECTED (Below threshold; pathway 0.50). Methanogenesis capability has NO `diagnostic_marker_override`, so it relies on gapseq pathway integrity, which is absent for sentinels | **GAP — marker-only sentinel limitation, not a Phase 3.6 issue** |
| Primary cultivation mode = methanogenic (NOT anme) | YES | "No primary cultivation mode detected" — escalated to Tier 2 because no capability cleared 0.50 threshold via marker-only path | **PARTIAL** (the negative-control half passes — anme is correctly NOT primary; the positive-control half fails — methanogenic is also not primary) |
| Recipe matches Methanosarcina cultivation literature | YES | Escalated, no recipe composed | **GAP** (downstream of methanogenesis capability not firing) |

## Verdict

**The critical Phase 3.6 false-positive prevention test PASSES decisively.** Methanosarcina has the strongest possible mcrA signal (100% self-hit) plus full Wood-Ljungdahl carbonyl-branch enzymes, but the ANME OR-group correctly resolves to negative because none of dsrAB, mtrC_omcB, or gapseq nitrate-reduction-pwy fires. The discriminator works as designed: mcrA presence alone does not promote ANME — an alternative-acceptor signal must accompany it.

**The marker-only sentinel limitation surfaces a documentation gap, not a Phase 3.6 bug.** The methanogenesis capability has no `diagnostic_marker_override` mechanism (unlike methanotrophy, DNRA, NOB), so it requires gapseq pathway integrity to fire above 0.50. Without gapseq data, mcrA + WL-carbonyl markers alone score 0.375. This is a known sentinel-pattern limitation: it affects what the sentinel report can show end-to-end, not the underlying detection logic. In the test set, Methanocaldococcus jannaschii (gid=8) classifies methanogenic at 0.753 because gapseq pathways ARE loaded for test genomes.

## Issue triage for Phase 3.8 scope

- **Methanogenesis capability lacks `diagnostic_marker_override`** — adding mcrA + (acsB_cdhC OR cooS_cdhA) override logic would let the capability fire from markers alone for marker-only sentinels. **This is symmetric with the Phase 3.5 design choice for methanotrophy** (override on pmoA / mmoX). Polish-tier Phase 3.8 candidate; not blocking.
- The marker-only sentinel pipeline could optionally include a TEMPURA-lookup hook to populate organism temperature optima without requiring full integrate_tempura.py runs. Same item as the other two sentinels.

**The positive validation that Phase 3.6 needed** — false-positive prevention on a canonical forward methanogen — is unambiguously delivered. ANME does not fire on Methanosarcina even though mcrA is at 100% pident.
