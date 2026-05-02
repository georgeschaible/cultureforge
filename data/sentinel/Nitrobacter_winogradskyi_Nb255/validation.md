# Phase 3.7 Sentinel Validation — Nitrobacter winogradskyi Nb-255

**NCBI assembly:** GCF_000012725.1 (Complete Genome, ASM1272v1)
**Genome ID in CultureForge DB:** 902
**Validates Phase:** 3.3 (canonical aerobic nitrite oxidation, Type B periplasmic clade)
**Date validated:** 2026-05-01

## Pipeline notes

Marker BLAST only (matching the Phase 3.5 sentinel pattern). The NOB capability uses `diagnostic_marker_override` (override_confidence=0.70, threshold pident≥75 / qcov≥80 / evalue≤1e-30), so the marker hit alone is sufficient to fire the capability and route the recipe composer.

## Marker BLAST results

| Marker | Best hit | Best ref | pident | bitscore | qcov | evalue | positive_call |
|---|---|---|---:|---:|---:|---:|:---:|
| nxrA | WP_011315305.1 | Q3SQW5 (Nitrobacter winogradskyi self) | **100.0** | 2533 | 100 | 0.0 | YES |
| nxrA | WP_011314088.1 | Q71RT9 (Nitrobacter alkalicus, Type B) | 96.4 | 2444 | 99 | 0.0 | YES |
| autotrophy | WP_011315233.1 | RuBisCO large subunit | 76.2 | 724 | 99 | 0.0 | YES |
| terminal_oxidases | WP_011313559.1 | aerobic respiration | 60.1 | 619 | 95 | 0.0 | YES |
| cyc2 | WP_041344635.1 | iron-oxidation marker (weak) | 33.8 | 115 | 92 | 1.6e-35 | YES |

The cyc2 hit is weak (33.8%, marginally above the 30% threshold) and is a known cross-reactivity of the cyc2 reference set with cytochrome c family proteins — it does not promote iron oxidation as a primary mode (capability would fail other gates). NOT a Phase 3.3 issue.

### Type B clade verification (Phase 3.3 dual-clade architecture)

| Reference | Clade | Best Nitrobacter hit pident |
|---|---|---:|
| Q3SQW5 — Nitrobacter winogradskyi | **Type B** | 100.0% (self) |
| Q71RT9 — Nitrobacter alkalicus | **Type B** | 96.4% |
| A0A894Z0L1 — Nitrolancea hollandica | **Type B** | 67.5% (below 75% threshold) |
| A0A0S4KRS1 — Nitrospira inopinata | Type A | (no hit at evalue 1e-30) |
| A0A1W1I298 — Nitrospira japonica | Type A | (no hit) |
| A0ABM8RCK9 — Nitrospira defluvii | Type A | (no hit) |

Best Type B hit (Q3SQW5, self) at 100% vs no hits at all to Type A references confirms that Nitrobacter is being detected via the Type B clade arm of the dual-clade reference architecture. Phase 3.3's Type B clade was inferred from cross-reactivity scans during reference curation; this sentinel adds the empirical positive-control validation.

NOT detected (correctly): mcrA, dsrAB, qmoA, nrfA, amoA, hao, soxB, pmoA, mmoX, mtrC_omcB, hzsA, hdh, rdhA, pufLM, pscA_fmoA, psaA_psbA, rhodopsin, nosZ, tqoDoxD/A, tetH, sor, acsB_cdhC, cooS_cdhA. Specifically amoA negativity matters because it is the primary cross-reactivity concern for nxrA (different reaction, related family); Nitrobacter correctly does not light up amoA (it is pure NOB, not comammox or AOB).

## Verification criteria

| Criterion | Expected | Observed | Pass/Fail |
|---|---|---|:---:|
| nxrA marker fires above threshold | YES (>75% pident, >80% qcov) | 100% pident, 100% qcov | **PASS** |
| Hits Type B clade refs (Q3SQW5, Q71RT9) more than Type A | YES | Q3SQW5 100% / Q71RT9 96% / no Type A hits | **PASS** |
| lithotrophic_aerobic_nitrite capability detected | YES | YES (essential_marker fires; recipe routes via nitrite branch) | **PASS** |
| Capability confidence ≥ 0.65 | YES | override_confidence=0.70 | **PASS** |
| Primary cultivation mode = lithotrophic_aerobic (nitrite oxidation, canonical NOB) | YES | "lithotrophic_aerobic (nitrite oxidation, canonical NOB)" | **PASS** |
| Atmosphere = aerobic | YES | air + 2% CO2 | **PASS** |
| Electron donor = NaNO2 with toxicity note | YES | NaNO2 0.5 mM with explicit toxicity warning + replenishment note | **PASS** |
| Carbon source = bicarbonate | YES | NaHCO3 2.5 g/L | **PASS** |
| Temperature ~28°C | YES | 30°C default (no TEMPURA/GenomeSPOT loaded) | **GAP** (close — within 2°C) |
| pH ~7.5 | YES | 7.5 (recipe composer's NOB-specific override of the 7.0 default) | **PASS** |
| Recipe matches DSMZ Medium 756 architecture | YES | NaNO2 + NaHCO3 + phosphate buffer pH 7.5 + SL-10 + Wolin's vitamins, aerobic, no reducing agent — matches Medium 756 family | **PASS** |
| ΔG = -74 kJ/mol | YES | -74.0 kJ/mol, feasible | **PASS** |

## Verdict

**11/12 PASS, 1 GAP (close).** The 30°C default vs Nitrobacter's literature 28°C optimum is within 2°C and reflects the marker-only sentinel pattern (TEMPURA / GenomeSPOT not loaded for sentinels). NOT a Phase 3.3 issue.

The Type B clade arm of the Phase 3.3 dual-clade nxrA reference architecture is now empirically validated. Phase 3.3 prior validation was Type A only (Nitrospira moscoviensis test-set genome); Type B was inferred from reference curation. This sentinel closes that gap.

## Issue triage for Phase 3.8 scope

- Same temperature-default polish item as Wolinella sentinel (lightweight TEMPURA-lookup hook in sentinel load pipeline). Not blocking.
