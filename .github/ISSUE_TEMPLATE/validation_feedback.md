---
name: Validation feedback
about: External-tester structured feedback on a CultureForge prediction
title: "[VALIDATION] "
labels: validation
---

<!-- Use the structure from TESTER_FEEDBACK_TEMPLATE.md for the most useful feedback. -->

## Tester name + affiliation


## CultureForge version
<!-- Date from inspect-report header or git commit hash -->

## Organism submitted
- Name:
- NCBI accession:
- Source: (cultivation collection / environmental MAG / single-cell genome / other)
- Genome completeness (CheckM2 or equivalent), if known:

## Expected biology
<!-- Briefly describe what you expect CultureForge to predict, based on your domain knowledge of this organism.
  - Primary cultivation mode you expect
  - Atmosphere you expect
  - Key electron donor / acceptor pair
  - Temperature / pH / salinity envelope
  - Reference cultivation protocol (DSMZ medium ID, paper citation, etc.)
-->

## Actual CultureForge output
<!-- Paste the relevant sections of the inspect report. Minimum: PRIMARY CULTIVATION MODE line, GAS PHASE, INCUBATION CONDITIONS, INGREDIENTS, THERMODYNAMIC CHECK, OVERALL CONFIDENCE, UNCERTAINTY FLAGS. If escalated, paste the escalation reason. -->

```
[Paste output here]
```

## Biological assessment
<!-- For each major recipe component, mark whether CultureForge's choice is correct, partially correct, or incorrect — and explain why. -->

| Component | ✓ / ⚠ / ✗ | Notes |
|---|:---:|---|
| Primary cultivation mode |  |  |
| Gas phase |  |  |
| Atmosphere category |  |  |
| Electron donor |  |  |
| Electron acceptor |  |  |
| Carbon source |  |  |
| Buffer |  |  |
| Reducing agent |  |  |
| Trace metals |  |  |
| Vitamins |  |  |
| Temperature |  |  |
| pH |  |  |
| Salinity |  |  |
| Thermodynamic feasibility verdict |  |  |

## Suggestions
<!-- What should CultureForge change to be more useful for this organism class?
  - Marker reference X is missing for this organism's lineage
  - Threshold Y is too strict / too lax
  - Recipe component Z should be added / removed / replaced
  - Confidence score is misleading because of W
-->

## Critical issues
<!-- Did CultureForge produce output that would mislead an experimentalist into a wrong cultivation strategy? Describe any false-positive or false-negative pattern and the cultivation consequence. -->

## Cultivation experience (optional)
<!-- If you have actually cultivated this organism, did the CultureForge recipe match what worked experimentally? If you tested the CultureForge recipe directly, what was the outcome (growth / partial / no growth, time to growth, biomass yield)? -->
