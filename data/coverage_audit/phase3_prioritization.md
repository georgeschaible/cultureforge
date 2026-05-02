# Phase 3 Gap Prioritization

**Purpose:** For each GAP and PARTIAL metabolism in the coverage map, estimate impact (frequency × severity × tractability) and rank for Phase 3 sub-phase scheduling.

**Scoring framework:**

| Dimension | HIGH | MEDIUM | LOW |
|---|---|---|---|
| **Frequency** in real microbial submissions | Common environmental microbiology metabolism | Significant but specialized | Rare or highly specialized |
| **Severity** of misclassification | CRITICAL — wrong primary mode, no growth on the predicted recipe | MAJOR — recipe in right neighborhood, missing key components | MINOR — supports growth, not optimal |
| **Tractability** of fix | SIMPLE — single marker, references available, similar to existing capabilities (1 sub-phase) | MODERATE — multi-marker, some curation work, new pathway architecture (1-2 sub-phases) | COMPLEX — new capability category, recipe composer changes, novel biology (2+ sub-phases) |

## Top-priority gaps

### Tier 1 — must-do for external testing readiness

#### Priority 1: Canonical nitrite oxidation (NOB) — A3

- **Frequency:** HIGH. Nitrification is universal in soil, freshwater, marine, wastewater microbiology. Any environmental sample submission has a real chance of containing Nitrospira / Nitrobacter.
- **Severity:** CRITICAL. Test-set Nitrospira moscoviensis currently misclassified as acetogenic (recipe is H₂/CO₂ at 39°C, completely wrong). The actual cultivation requires aerobic atmosphere with NaNO₂ as electron donor.
- **Tractability:** SIMPLE. nxrA is well-characterized, full-length references readily available (verified in `nitrospira_verification.md`). Single new diagnostic marker + new `lithotrophic_aerobic_nitrite` capability + recipe routing.
- **Impact estimate:** N. moscoviensis V12 score should improve from 20% → 60%+ after fix. Future NOB submissions correctly classified.
- **Recommended scope:** Phase 3.3 (already framed by verification work).
- **Estimated effort:** 5-7 days.

#### Priority 2: Aerobic methanotrophy — A10

- **Frequency:** MEDIUM-HIGH. Methanotrophs are common in soils, peatlands, freshwater sediments, methane-rich environments. Submission probability is real for environmental microbiology.
- **Severity:** CRITICAL when missed. Methanotrophs need methane in headspace; without detection they'd default to aerobic_chemotrophic with normal headspace.
- **Tractability:** MODERATE. pmoA and mmoX references are available, but pmoA is sequence-related to amoA — cross-reactivity check is required. Recipe composer needs methane-headspace recipe template (not currently in place).
- **Impact estimate:** No test-set organism, so V12 doesn't move; but external-testing readiness improves.
- **Recommended scope:** Phase 3.4 candidate.
- **Estimated effort:** 5-8 days (cross-reactivity check + recipe template work adds complexity).

#### Priority 3: DNRA — B2

- **Frequency:** MEDIUM-HIGH. Common in C-rich anaerobic sediments, animal guts, agricultural soils. Increasingly recognized as quantitatively important in N cycling.
- **Severity:** MAJOR. Wrong recipe — DNRA organism would currently look like aerobic_chemotrophic or fermentative depending on glycolysis pathway. Recipe needs anaerobic atmosphere with NO₃⁻ as acceptor.
- **Tractability:** SIMPLE-MODERATE. nrfA + nirBD markers are well-characterized. Recipe routing is similar to denitrification but terminal product is NH₄⁺ instead of N₂.
- **Impact estimate:** No test-set organism; external-testing readiness improves.
- **Recommended scope:** Phase 3.5 candidate.
- **Estimated effort:** 4-6 days.

### Tier 2 — important for completeness

#### Priority 4: ANME (reverse methanogenesis) — B15 / LIMITATIONS F.2

- **Frequency:** MEDIUM. Anaerobic methane-oxidizing archaea are quantitatively important in marine sediments and freshwater anoxic zones. Submission probability is real.
- **Severity:** CRITICAL. Test-set Methanoperedens nitroreducens is currently classified methanogenic with H₂/CO₂ recipe — biologically opposite of correct (CH₄ as substrate, NO₃⁻ as acceptor).
- **Tractability:** COMPLEX. mcrA detects ANME but doesn't distinguish forward vs reverse. The fix requires either (a) phylogenetic placement of mcrA into ANME clades vs methanogen clades, or (b) co-occurrence rules: ANME must have one of {NarG/napA, dsrAB, mtrC/omcB} as terminal-acceptor partner. Negative-marker rule from acetogenesis would need to be relaxed for the new ANME capability.
- **Impact estimate:** Methanoperedens V12 score 28% → could improve significantly if recipe correctly composed for CH₄ + NO₃⁻.
- **Recommended scope:** Phase 3.6 — but only if priorities 1-3 close cleanly.
- **Estimated effort:** 7-10 days (capability framework changes needed).

#### Priority 5: Aerobic anoxygenic phototrophy (AAP) atmosphere routing — C4

- **Frequency:** LOW-MEDIUM. Common in marine surface waters but rare in cultivation submissions.
- **Severity:** MAJOR. AAP organisms detected as anoxygenic_phototrophy_purple but recipe routes to anaerobic atmosphere. Real fix is recipe-routing logic, not marker addition.
- **Tractability:** MODERATE. Requires adding aerobic-context distinguishing logic to anoxygenic_phototrophy_purple capability, possibly using terminal-oxidase profile co-detection.
- **Impact estimate:** No test-set organism; specialty fix.
- **Recommended scope:** Defer or bundle with other recipe-routing fixes.
- **Estimated effort:** 3-5 days.

### Tier 3 — specialty improvements

#### Priority 6: Photoferrotrophy — C7

- **Frequency:** LOW-MEDIUM. Niche but biologically important (banded iron formations, modern Fe-cycling environments). Specialty submissions.
- **Severity:** MAJOR. Photoferrotrophs would route to plain anoxygenic_phototrophy_purple (wrong donor — they need Fe²⁺ explicitly).
- **Tractability:** MODERATE. PioABC / FoxEYZ markers need curation; references available but limited.
- **Recommended scope:** Phase 3.7+ candidate.
- **Estimated effort:** 5-7 days.

#### Priority 7: Heliobacterial phototrophy (pshA) — C6

- **Frequency:** LOW.
- **Severity:** CRITICAL when encountered. Heliobacterial RC is absent from current marker set; would be missed.
- **Tractability:** SIMPLE-MODERATE. pshA references available; new capability follows pufLM/pscA template.
- **Recommended scope:** Phase 3.7+ candidate or bundle with photoferrotrophy.
- **Estimated effort:** 3-5 days.

#### Priority 8: Comammox amoA — A4 / LIMITATIONS A.2

- **Frequency:** MEDIUM (specialty environmental microbiology).
- **Severity:** CRITICAL — comammox organisms would route to plain heterotrophic recipe.
- **Tractability:** SIMPLE-MODERATE. Full-length comammox amoA references available; existing amoA reference set just needs expansion. Cross-reactivity with AOB amoA needs check.
- **Recommended scope:** Could bundle into Phase 3.3 (canonical NOB) since both involve nxrA + amoA detection logic. Or defer.
- **Estimated effort:** 3-5 days standalone; ~1 day extra if bundled with Phase 3.3.

#### Priority 9: Manganese(IV) reduction — B7

- **Frequency:** LOW-MEDIUM.
- **Severity:** MAJOR (wrong terminal acceptor in recipe).
- **Tractability:** MODERATE. Markers shared with iron reduction (Shewanella mtrC); distinguishing-substrate logic less clear.
- **Recommended scope:** Defer.

#### Priority 10: Neutrophilic Fe(II) oxidation — A8 / LIMITATIONS A.4

- **Frequency:** LOW (specialist iron-cycling samples).
- **Severity:** CRITICAL when encountered.
- **Tractability:** MODERATE-COMPLEX. mtoA / mtoB references available; new capability needed.
- **Recommended scope:** Defer to later in Phase 3 or post-Phase-3.

### Tier 4 — low priority / defer indefinitely

The following gaps have LOW frequency or impact and can be deferred without affecting external-testing readiness materially:

- Selenate respiration (B8)
- Arsenate respiration (B9)
- Chlorate / perchlorate respiration (B10)
- N-DAMO (B17)
- Sulfur disproportionation (B5)
- Cable bacteria EET (E2)
- Aerobic CO oxidation Mo-CODH (A11)

## Cumulative effort estimate for Tier 1 + Tier 2

| Sub-phase | Scope | Est days |
|---|---|---|
| Phase 3.3 | Canonical nitrite oxidation (+ optional comammox amoA bundle) | 5-8 |
| Phase 3.4 | Aerobic methanotrophy | 5-8 |
| Phase 3.5 | DNRA | 4-6 |
| Phase 3.6 | ANME directional / F.2 mitigation | 7-10 |
| Phase 3.7 | AAP routing OR photoferrotrophy OR heliobacterial — pick one | 3-7 |
| **Total Tier 1+2** | | **24-39 days** |

12-week (~60 working day) Phase 3 budget would cover Tier 1 + Tier 2 with moderate slack for the unforeseen issues that always surface (e.g., Phase 3.2's Sulfolobus DSM 639 gene-content surprise, Phase 3.3's pivot from comammox amoA to canonical nxr).

## Recommended Phase 3 ordering

1. **Phase 3.3 (now)** — canonical nitrite oxidation + optional comammox amoA bundle
2. **Phase 3.4** — DNRA (similar architectural pattern to Phase 3.3, builds on the lithotrophic-aerobic infrastructure)
3. **Phase 3.5** — aerobic methanotrophy (highest external-readiness gain among non-nitrogen metabolisms)
4. **Phase 3.6** — ANME F.2 mitigation (capability framework work; requires care)
5. **Phase 3.7** — pick one of: AAP routing fix, photoferrotrophy, heliobacterial — based on whether the user has an external test sample requiring it
6. **Phase 3.8 (reserve)** — buffer for unforeseen issues + documentation polish

After Phase 3.5 (aerobic methanotrophy) is the natural decision point to launch external testing in parallel: by then, all major aerobic respiration variants except niche ones are covered, and the most impactful anaerobic gaps (DNRA, ANME) are either closed or characterized.
