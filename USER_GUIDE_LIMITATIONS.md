# CultureForge — User-Facing Limitations Guide

This document is for microbiologists preparing to submit a genome to CultureForge. For developer-facing limitation details organized by category, see `LIMITATIONS.md`.

---

## Quick reference: "Are you submitting X? Expect Y."

| Submitting... | Expected experience |
|---|---|
| A complete genome of a well-studied environmental organism (sulfate reducer, methanogen, NOB, methanotroph, etc.) | High-confidence recipe; primary mode classification correct; recipe ingredients aligned with cultivation literature |
| A complete genome of a fermentative or aerobic-chemoorganotrophic organism | Recipe will fire as `fermentative` or `aerobic_chemotrophic` — broad classifications. Use the published-media comparison section to refine ingredient choices |
| A near-complete MAG (>80% completeness) of an environmental organism with cultivable relatives | Reasonable recipe; check uncertainty flags; use --temperature / --ph / --salinity overrides if you know the source habitat |
| An incomplete MAG (<70% completeness) | Likely "escalated" status — pathway markers missing due to assembly gaps. Manual annotation may be required |
| A novel-lineage organism without close cultivable relatives at <80% 16S identity | Recipe based on functional-neighbor matching; treat as starting hypothesis. Phylogenetic-match confidence will be low |
| An Asgard archaeon, candidate phylum, or single-cell genome | CultureForge often reaches its limits here. Expect limited utility; check capability profile for honest assessment |
| An organism with a specialty metabolism not in the supported-19 set | May be misclassified as `fermentative` or `aerobic_chemotrophic` catch-all. Manual review needed |
| An organism with documented substrate-specificity ambiguity (Dehalococcoides) | Recipe will be biologically reasonable but generic; specific halogenated electron acceptor needs manual selection |

---

## Organism types that work well

CultureForge's coverage is strongest on environmental microbiology metabolisms where cultivation literature is mature:

- **Sulfate reducers** (Desulfovibrio, Desulfobacter class) — dsrAB + qmoA discriminator; recipe matches DSMZ Postgate-family media
- **Forward methanogens** (Methanocaldococcus, Methanosarcina, Methanobacterium class) — mcrA-based detection; recipe selects H2/CO2 or aceticlastic-class composition based on pathway content
- **ANME-2d (nitrate-coupled)** — Methanoperedens-class; CH4+N2 atmosphere + NaNO3 acceptor (Phase 3.6)
- **Aerobic methanotrophs** — Methylococcus, Methylosinus, Methylocystis, Methylocella class via pmoA / mmoX. Air+CH4 80:20, copper supplementation note (Phase 3.5)
- **Aerobic nitrite oxidizers (NOB)** — Nitrospira (Type A) and Nitrobacter / Nitrolancea / Nitrotoga (Type B) via nxrA. Recipe matches DSMZ Medium 756 / 2399 family (Phase 3.3)
- **Aerobic ammonia oxidizers (AOB)** — Nitrosomonas / Nitrosospira class via amoA
- **DNRA organisms** — Wolinella class via nrfA; formate + nitrate + bicarbonate (Phase 3.4)
- **Iron(II) oxidizers, acidophilic** — Acidithiobacillus class via cyc2
- **Iron(III) reducers** — Geobacter class via mtrC + omcB
- **Anoxygenic phototrophs** — purple bacteria (pufLM), green sulfur bacteria (pscA / fmoA), FAP-type Chloroflexi
- **Oxygenic phototrophs** — cyanobacteria via psaA + psbA
- **Bacteriorhodopsin-based phototrophy** — Halobacterium class
- **Acetogens** — Wood-Ljungdahl pathway (acsB_cdhC + cooS_cdhA, qmoA-negative)
- **Organohalide respirers** — Dehalococcoides / Dehalobacter / Desulfitobacterium via rdhA family (substrate ambiguity caveat)
- **Anammox bacteria** — Brocadia / Kuenenia class via hzsA + hdh (Scalindua profunda is escalated due to MAG-completeness, not detection limit)
- **Sulfur oxidizers** — bacterial SOX (soxB) + archaeal markers (tqoDoxD, tqoDoxA, tetH, sor)

---

## Organism types with caveats

### Incomplete MAGs (< 70% completeness)

The recipe may be escalated because pathway markers are missing due to assembly incompleteness rather than biology. Check the Quality section of the inspection report. Options:

- Manual annotation of the missing pathway and re-run with augmented gapseq output
- Use a more complete genome of a related organism as a proxy
- Accept the escalation and manually compose a recipe based on phylogenetic neighbors

### Novel lineages (< 80% 16S identity to anything cultivated)

Phylogenetic-match confidence drops; recipe falls back on functional-neighbor matching, which is approximate. The published-media comparison will use functional neighbors rather than direct matches — read the rationale carefully. The recipe should be treated as a starting hypothesis to test, not a precise prescription.

### Asgard archaea, candidate phyla, single-cell genomes

These routinely exceed CultureForge's reach. The capability profile may include false-positive gapseq pathway annotations (Phase 1.5n F.3 limitation). Read the capabilities section critically. Examples: Prometheoarchaeum syntrophicum has methanogenesis annotated at 0.900 confidence via gapseq pathway alone, but no mcrA — these are ancestral genes used for syntrophic propionate oxidation, not actual methanogenesis. The action layer will flag the discrepancy.

### Specialty metabolisms (selenate respiration, photoferrotrophy, cable bacteria, etc.)

CultureForge does not currently cover:
- Selenate / selenite / arsenate respiration (no curated markers)
- Cable-bacteria long-distance electron transport (LDET, out of scope)
- Photoferrotrophy as substrate-specific metabolism (partial coverage via phototrophy)
- N-DAMO (Methylomirabilis intra-aerobic methane oxidation in NC10) — biochemically distinct from canonical methanotrophy
- Comammox (one-organism nitrification, Nitrospira inopinata class) — deferred until a comammox is in the test set

For these organisms, expect a fallback classification (often `fermentative` or `aerobic_chemotrophic`). Use the genome's own pathway annotations to identify what's missing.

---

## Common output patterns and what they mean

### "Escalated — no recipe composed"

CultureForge couldn't determine a primary cultivation mode. Most often this is a MAG-completeness issue. The action section indicates the type:

- **MAG completeness:** missing pathway markers — manual annotation may help
- **Novel-lineage:** no functional-neighbor match — use phylogenetic relatives as starting point
- **Specialty-metabolism:** the metabolism isn't in the supported-19 set — manual review needed

### Low published-media comparison V12 score

A low V12 score does not necessarily mean the recipe is wrong. Known calibration issues:

- **Single-reference Jaccard brittleness:** when only 1 DSMZ medium exists for the organism, any ingredient missing from CultureForge counts double
- **Ingredient-name normalization gaps:** DSMZ recipes list individual SL-10 trace metal components (FeCl2, ZnSO4, MnCl2, etc.); CultureForge aggregates as "SL-10 trace metal solution (1 mL/L)". The metric counts these as distinct, dragging the score even when the recipe is correct
- **Functional-neighbor matching:** when no direct medium exists, comparison uses media from related organisms with possibly different metabolism — large diff is expected and not a recipe error

To assess actual biological correctness, read the recipe's primary mode label, gas phase, and ingredient roles, then compare against your domain knowledge. Use the per-organism diagnostic in `RECIPE_VALIDATION_V12.md` for context.

### Multi-modal organism classifications

When an organism supports multiple metabolisms (e.g., facultative aerobic-anaerobic, mixotrophic phototroph, chemoorganotroph + chemolithotroph), the primary cultivation mode is selected by:

1. The Phase 3.6 priority order in `_SPECIFIC_MODES_PRIORITY` (anme_reverse_methanogenic > methanogenic > methanotrophic > etc.)
2. Diagnostic-marker corroboration filter (Phase 1.5n) — only marker-supported modes get promoted
3. Confidence-aware tie-breaking (e.g., Desulfovibrio with both dsrAB and nrfA — sulfate reduction wins by higher confidence; DNRA flagged in alternative modes)

The alternative modes are listed alongside the primary. If the alternative is closer to the experimental intent, use --temperature / --ph / --salinity to push the recipe in that direction.

### "ANME directional ambiguity" uncertainty flag

Methanogen-class genomes that don't trigger the ANME OR-group (no dsrAB, no mtrC_omcB, no gapseq nitrate-pwy) but are suspected ANME from external context get this flag. The recipe defaults to forward methanogenesis but the flag suggests alternative-acceptor cultivation if direction is uncertain.

---

## What to do when output looks wrong

### Use environmental overrides

If you have domain knowledge the tool lacks (e.g., GenomeSPOT predicted 30°C but you isolated this organism from a hot spring at 70°C), override at the command line:

```bash
python3 cultureforge.py inspect <gid> --temperature 70 --pH 6.5 --salinity 0.5
```

Overrides take precedence at confidence 0.95, beating GenomeSPOT/TEMPURA.

### Read the published-media comparison carefully

Even at low V12 scores, the comparison surfaces specific ingredient differences you may want to test variants on. The "ref_only" rows tell you what published media include that CultureForge omits — assess whether each is biologically required for your organism.

### Check uncertainty flags

The recipe section ends with explicit uncertainty flags for components below 0.75 confidence. These are designed to surface where to vary in experiments. Read them as a starting point for combinatorial testing rather than as a confirmed recipe.

### Manual annotation augmentation

If the genome is missing a key marker due to assembly incompleteness or annotation gap, you can:

1. Run a manual BLAST against the relevant marker reference (in `data/diagnostic_markers/<marker>_refs.fasta`)
2. If the gene IS present but missed by gapseq, add it manually to `genome_pathways` with appropriate completeness/predicted flags
3. Re-run inspect

This requires database-level access; consult `README_DEV.md`.

### Submit feedback

If CultureForge produces a recipe that doesn't match your experimental experience, submit feedback using the structure in `TESTER_FEEDBACK_TEMPLATE.md`. Include:

- The genome / accession
- The primary cultivation mode CultureForge selected
- The expected biology based on your experience
- Which recipe components were wrong and what they should be
- Any cultivation-protocol references

This feedback drives the validation set evolution and post-Phase-3 capability additions.

---

## Reference to developer documentation

For developer-facing detail on each limitation:

- `LIMITATIONS.md` — Catalog organized by category (A: wrong-recipe risk, B: suboptimal-recipe risk, C: directional ambiguity, D: subcategory ambiguity, E: coverage gaps, F: detector-side limitations, G: V12 metric calibration). Each entry includes affected organisms, root cause, severity, and (where applicable) future-fix design.
- `data/diagnostic_markers/REFERENCE_CURATION.md` — Per-marker curation rationale, thresholds, cross-reactivity scans
- `data/diagnostic_markers/<topic>_review.md` — Sub-phase literature reviews
- `VALIDATION_REPORT.md` — Consolidated validation across Phases 1–3.8
