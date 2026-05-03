# CultureForge — Tester Feedback Template

Use this template to submit structured feedback. Copy the sections below into your feedback channel (email, GitHub issue, shared document — see project lead for distribution channel).

---

## Submission metadata

- **Tester name:**
- **Tester affiliation:**
- **Date of submission:**
- **CultureForge version (date from inspect-report header):**

## Organism submitted

- **Organism name:**
- **NCBI assembly accession:** (e.g., GCF_XXXXXXX.X)
- **Source:** (cultivation-collection strain / environmental MAG / single-cell genome / other)
- **Genome completeness (CheckM2 or equivalent), if known:**
- **Reason for submission:** (validation of expected output / probing a known gap / novel-organism prediction / other)

## Expected biology

Briefly describe what you expect CultureForge to predict, based on your domain knowledge of this organism. Include:

- **Primary cultivation mode you expect:** (e.g., methanogenic / aerobic_chemotrophic / lithotrophic_aerobic (Fe(II) ox) / etc.)
- **Atmosphere you expect:** (e.g., H2/CO2 80:20 / air / CH4 + air 80:20 / etc.)
- **Key electron donor / acceptor pair:** (e.g., H2 + SO4²⁻ / CH4 + O2 / formate + NO3⁻ / etc.)
- **Temperature / pH / salinity envelope:**
- **Reference cultivation protocol (DSMZ medium ID, paper citation, etc.):**

## Actual CultureForge output

Paste the relevant sections of the inspect report. Minimum:

- The "PRIMARY CULTIVATION MODE" line
- The "GAS PHASE" block
- The "INCUBATION CONDITIONS" block
- The "INGREDIENTS" block
- The "THERMODYNAMIC CHECK" block
- The "OVERALL CONFIDENCE" line
- Any "UNCERTAINTY FLAGS"

If the recipe escalated, paste the escalation reason.

## Biological assessment

For each major recipe component, mark whether CultureForge's choice is correct, partially correct, or incorrect — and explain why.

| Component | Correct? | Notes |
|---|:---:|---|
| Primary cultivation mode classification | ✓ / ⚠ / ✗ | |
| Gas phase composition | ✓ / ⚠ / ✗ | |
| Atmosphere category (aerobic / anaerobic / microaerobic / etc.) | ✓ / ⚠ / ✗ | |
| Electron donor | ✓ / ⚠ / ✗ | |
| Electron acceptor | ✓ / ⚠ / ✗ | |
| Carbon source | ✓ / ⚠ / ✗ | |
| Buffer | ✓ / ⚠ / ✗ | |
| Reducing agent | ✓ / ⚠ / ✗ | |
| Trace metals | ✓ / ⚠ / ✗ | |
| Vitamins | ✓ / ⚠ / ✗ | |
| Temperature | ✓ / ⚠ / ✗ | |
| pH | ✓ / ⚠ / ✗ | |
| Salinity | ✓ / ⚠ / ✗ | |
| Thermodynamic feasibility verdict | ✓ / ⚠ / ✗ | |

## Recipe-vs-published-media diff (if applicable)

Did the published-media comparison section flag specific ingredients as missing or extra? Were those flags biologically meaningful?

## Suggestions

What should CultureForge change to be more useful for this organism class? Examples:

- Marker reference X is missing for this organism's lineage
- Threshold Y is too strict / too lax
- Recipe component Z should be added / removed / replaced
- Confidence score is misleading because of W

## Critical issues

Did CultureForge produce output that would mislead an experimentalist into a wrong cultivation strategy? If yes, describe the false-positive or false-negative pattern and the cultivation consequence.

## Cultivation experience (optional)

If you have actually cultivated this organism, did the CultureForge recipe match what worked experimentally? If you tested the CultureForge recipe directly, what was the outcome (growth / partial growth / no growth, time to growth, biomass yield)?

## Other observations

Any other context, suggestions, or observations.

---

**Thank you for the feedback.** This template structure makes feedback comparable across testers and lets the development team triage issues efficiently. Free-form comments are also welcome at the bottom; the structured fields above are the priority.
