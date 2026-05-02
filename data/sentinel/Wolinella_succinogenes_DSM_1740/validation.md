# Phase 3.7 Sentinel Validation — Wolinella succinogenes DSM 1740

**NCBI assembly:** GCF_000196135.1 (Complete Genome, ASM19613v1)
**Genome ID in CultureForge DB:** 901
**Validates Phase:** 3.4 (DNRA via NrfA)
**Date validated:** 2026-05-01

## Pipeline notes

Marker BLAST only. Following the Phase 3.5 sentinel pattern (Methylococcus capsulatus Bath, gid=900): proteome downloaded from NCBI RefSeq, BLAST DB built against the curated marker references, no gapseq / GenomeSPOT / MeBiPred run. The DNRA capability uses `diagnostic_marker_override` (override_confidence=0.65, threshold pident≥65 / qcov≥80 / evalue≤1e-30), so the marker hit alone is sufficient to fire the capability and route the recipe composer.

The TEMPURA / GenomeSPOT absence means temperature defaults to 30°C (rather than the literature-correct 37°C) and pH defaults to 7.0. This is a known marker-only sentinel limitation, not a Phase 3.4 issue.

## Marker BLAST results

| Marker | Best hit | pident | bitscore | qcov | evalue | positive_call |
|---|---|---:|---:|---:|---:|:---:|
| nrfA | WP_011138866.1 | **100.0** | 1059 | 100 | 0.0 | YES |
| nifH | WP_011139245.1 | 73.2 | 436 | 99 | 7.9e-160 | YES |
| terminal_oxidases | WP_011138140.1 | 42.9 | 406 | 99 | 9.2e-141 | YES |

The Q9S1E5 reference is Wolinella's own NrfA, so the 100% self-hit is expected.

NOT detected (correctly): mcrA, dsrAB, qmoA, aprAB, amoA, hao, soxB, pmoA, mmoX, nxrA, mtrC_omcB, cyc2, hzsA, hdh, rdhA, pufLM, pscA_fmoA, psaA_psbA, rhodopsin, nosZ, autotrophy (Wolinella is a heterotroph), tqoDoxD/A, tetH, sor, acsB_cdhC, cooS_cdhA. Of these, dsrAB / mtrC_omcB negativity matters because they are the alternative-acceptor partners in the ANME OR-group; Wolinella correctly does not light up that signal (and is not an ANME archaeon — it's a Campylobacterota Epsilonproteobacterium).

## Verification criteria

| Criterion | Expected | Observed | Pass/Fail |
|---|---|---|:---:|
| nrfA marker fires above threshold | YES (>65% pident, >80% qcov) | 100% pident, 100% qcov | **PASS** |
| anaerobic_respiratory_dnra capability detected | YES | YES (essential_marker fires; recipe routes via dnra sub-mode) | **PASS** |
| Capability confidence ≥ 0.65 | YES | override_confidence=0.65 (override path, marker-only) | **PASS** |
| Primary cultivation mode = anaerobic_respiratory (DNRA via NrfA) | YES | "anaerobic_respiratory (DNRA via NrfA)" | **PASS** |
| Atmosphere is anaerobic | YES | N2/CO2 80:20 anaerobic | **PASS** |
| Electron acceptor = nitrate | YES | KNO3 15 mM | **PASS** |
| Electron donor includes formate | YES | Sodium formate 20 mM | **PASS** |
| Temperature ~37°C | YES (TEMPURA or GenomeSPOT) | 30°C default (no TEMPURA/GenomeSPOT loaded) | **GAP** |
| pH ~7 | YES | 7.0 default | PASS (within range) |
| Recipe matches DSMZ Medium 720 architecture | YES | Formate + nitrate + bicarbonate + Na2S + SL-10 + Wolin's vitamins, anaerobic — matches Medium 720 family | **PASS** |

## Verdict

**8/9 PASS, 1 GAP.** The temperature gap is a marker-only sentinel limitation: TEMPURA / GenomeSPOT data is not loaded for sentinels, so the recipe defaults to 30°C instead of the canonical Wolinella optimum of 37°C. This affects the sentinel report's literal output but is not a Phase 3.4 detection issue — the DNRA capability and recipe architecture validate cleanly.

The DNRA capability framework (Phase 3.4) is now empirically validated against a true obligate DNRA model organism. Prior validation was test-set non-firing (E. coli, Campylobacter, Desulfovibrio correctly stayed in their primary modes); this sentinel adds the positive-control validation that was previously inferred.

## Issue triage for Phase 3.8 scope

- **Marker-only sentinel temperature default**: Sentinels would benefit from a lightweight TEMPURA-lookup hook in the load pipeline (use the species name to fetch TEMPURA optimal_temp without requiring full integrate_tempura.py runs). Optional polish, not blocking.
