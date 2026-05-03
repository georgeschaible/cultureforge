# CultureForge

> ⚠️ **Pre-publication notice:** CultureForge is in active development. A peer-reviewed manuscript describing the methodology is in preparation. If you use CultureForge in published work, please contact george.schaible@gmail.com for current citation guidance — `CITATION.cff` provides a placeholder citation that will be updated upon publication. The tool is provided as-is for research use and external validation.

CultureForge predicts cultivation media for novel and uncultured bacteria and archaea from genome sequence. Submit a genome (or a complete proteome), receive a media recipe — atmosphere, ingredients with concentrations, incubation conditions, thermodynamic feasibility, and a comparison against published DSMZ / BacDive recipes for related organisms.

## Who is this for?

Microbiologists working with novel uncultured organisms, cultivation researchers trying to bring environmentally-relevant organisms into pure culture, and environmental microbiologists who want a starting recipe rooted in genomic evidence rather than analogy guessing. CultureForge is most useful when:

- You have a complete or near-complete genome / MAG of an organism you want to cultivate
- The organism's nearest cultivable relatives have published media you can compare against
- You want to ground a cultivation strategy in metabolic-pathway evidence rather than habitat analogy alone

CultureForge is not a replacement for cultivation expertise — it is a starting point that surfaces what the genome implies about the organism's energy metabolism, electron acceptors, carbon source preferences, metal requirements, and environmental envelope.

## What does it produce?

For each genome, CultureForge produces an **inspection report** with up to 11 sections:

- **Quality** — genome completeness, contamination, taxonomic placement
- **Predictions** — environmental envelope predictions (T, pH, salinity, oxygen) from GenomeSPOT
- **Capabilities** — ranked metabolic capabilities with confidence scores (e.g., methanogenesis 0.85, anaerobic respiration 0.62)
- **Pathways** — gapseq pathway integrity per capability
- **Markers** — diagnostic marker BLAST hits (mcrA, nrfA, nxrA, pmoA, etc.) — the canonical enzymes that define each metabolism
- **Hydrogenases** — H2 metabolism enzyme classification
- **Action** — what to do next: cultivate, manually verify a flag, escalate to Tier 2 structural analysis, etc.
- **Recipe context** — environmental data (TEMPURA, BacDive, GenomeSPOT) consolidated into the recipe-composition inputs
- **Recipe** — the cultivation media recipe: gas phase, ingredients with concentrations, incubation conditions, thermodynamic feasibility check
- **Published media comparison** — ingredient + condition diff against DSMZ / BacDive media for the matched species or its functional neighbors

## Quick start

```bash
# Inspect a genome already loaded in the database
python3 cultureforge.py inspect <genome_id>

# Inspect with environmental overrides (use these when you know the source habitat)
python3 cultureforge.py inspect <genome_id> --temperature 70 --ph 6.5 --salinity 0.5

# View only the recipe
python3 cultureforge.py inspect <genome_id> --section recipe

# JSON output for downstream tooling
python3 cultureforge.py inspect <genome_id> --json --output recipe.json
```

To load a new genome, use the validation pipeline scripts (`run_validation_synthesize.py` for full processing including gapseq) or follow the sentinel pattern in `data/sentinel/` for marker-BLAST-only loads. See `README_DEV.md` for full processing instructions.

## Understanding the output

### Recipe sections
- **Primary cultivation mode** is the dominant metabolism the genome supports. Alternatives are listed separately. Read the primary mode label carefully — it carries the biology (e.g., "lithotrophic_aerobic (nitrite oxidation, canonical NOB)" tells you the organism is a nitrite oxidizer, not just any aerobic chemolithotroph).
- **Gas phase** specifies the headspace composition. CH4+air for methanotrophs, CH4+N2 for ANME, H2/CO2 for hydrogenotrophic methanogens / acetogens / sulfate reducers, air+CO2 for autotrophic aerobes.
- **Incubation conditions** (T, pH, atmosphere, shaking) come from TEMPURA / GenomeSPOT / BacDive in priority order, with user `--temperature / --ph / --salinity` overrides taking precedence at confidence 0.95.
- **Ingredients** are grouped by role (buffer / salt / electron donor / electron acceptor / carbon source / trace metal / vitamin / reducing agent / supplement). Each ingredient has a confidence score and a one-line rationale.
- **Thermodynamic check** computes ΔG for the proposed energy metabolism at the chosen temperature and conditions. "Feasible" / "borderline" / "infeasible" classification.
- **Uncertainty flags** highlight components or conditions where confidence is below 0.75 — try variants when running experiments.

### Confidence scores
- **≥ 0.85** = strong evidence (multiple corroborating signals: marker + pathway + transporter + cofactor)
- **0.65 – 0.85** = good evidence (typically marker + pathway, or strong override path)
- **0.50 – 0.65** = suggestive (pathway annotation alone, or marker just above threshold)
- **< 0.50** = below firing threshold (capability detected but rejected)

### "Escalated" status
Means CultureForge couldn't determine a primary cultivation mode. Most often this is a MAG-completeness issue — the relevant pathway markers are missing because the genome is incomplete. Sometimes it's a novel-lineage issue where the metabolism doesn't match any of the 19 supported capabilities. The action section will indicate which.

### Published-media comparison V12 score
Numeric percentage of ingredient overlap and condition agreement between the CultureForge recipe and the matched DSMZ / BacDive medium. **A low V12 score does not necessarily mean the recipe is wrong** — the metric has known calibration limitations (Jaccard brittleness on single-reference media, ingredient-name normalization gaps in DSMZ media that list individual SL-10 components vs CultureForge aggregating). Always read the per-organism diagnostic in `RECIPE_VALIDATION_V12.md`. See `USER_GUIDE_LIMITATIONS.md` for guidance on interpreting low scores.

## What CultureForge can and cannot do

### Metabolisms covered well (validated against named-strain sentinels or test-set genomes)
- Aerobic methanotrophy (Type I / II / III, pmoA + mmoX)
- Methanogenesis (hydrogenotrophic, aceticlastic, methylotrophic; mcrA)
- Anaerobic methane oxidation (ANME-2d nitrate-coupled; sulfate / iron architecturally supported)
- Aerobic nitrite oxidation (canonical NOB, Type A Nitrospira + Type B Nitrobacter clades)
- Aerobic ammonia oxidation (AOB amoA, comammox not yet covered as primary)
- Dissimilatory nitrate reduction to ammonium (DNRA, nrfA)
- Dissimilatory sulfate reduction (dsrAB + qmoA)
- Sulfur oxidation (bacterial SOX + archaeal markers)
- Iron(II) oxidation, acidophilic (Acidithiobacillus class via cyc2)
- Iron(III) reduction (Geobacter class via mtrC / omcB)
- Anoxygenic phototrophy (purple bacteria pufLM, green sulfur pscA / fmoA)
- Oxygenic phototrophy (cyanobacteria psaA + psbA)
- Bacteriorhodopsin / proteorhodopsin
- Acetogenesis (Wood-Ljungdahl)
- Organohalide respiration (rdhA family)
- Anammox (hzsA + hdh)
- Fermentation (broad detection)
- Aerobic chemoorganotrophic respiration (terminal oxidases)

### Metabolisms with documented gaps
- Comammox amoA (Nitrospira inopinata-class) — deferred; not in test set
- N-DAMO (Methylomirabilis intra-aerobic methane oxidation, NC10 phylum) — biochemically distinct from canonical methanotrophy, out of scope
- Selenate / arsenate respiration — no curated markers
- Cable-bacteria long-distance electron transport (LDET) — out of scope
- Photoferrotrophy — partially covered by phototrophy detection, no Fe(II) substrate-specific recipe routing

See `USER_GUIDE_LIMITATIONS.md` for organism-type expectations and `LIMITATIONS.md` (developer-facing) for the full catalog.

### Where output may be less reliable
- **Incomplete MAGs** (< 70% completeness) — pathway markers may be missing due to assembly incompleteness rather than biology. Check the Quality section.
- **Truly novel lineages** with no cultivable relatives at < 80% 16S identity — phylogenetic-match confidence drops; recipe falls back on functional-neighbor matching, which is approximate.
- **Specialty metabolisms** not in the supported-19 set — fermentative or aerobic_chemotrophic catch-all classifications may be assigned incorrectly.
- **Asgard archaea, candidate phyla** — single-cell genomes / MAGs from these lineages routinely exceed CultureForge's reach; recipes should be treated as starting hypotheses.

## Validation summary

CultureForge has been validated through three complementary channels:

1. **Test-set classification** — 26 organisms across 18 dev + 8 blind set, spanning the major environmental microbiology metabolisms. Per-organism detection accuracy: see `VALIDATION_REPORT.md`.

2. **Published-media comparison (V12)** — recipe ingredients + conditions diffed against DSMZ / BacDive media for the matched species. Aggregate distribution across 26 organisms: 6 ≥ 70% agreement, 7 in 50–69%, 12 < 50%, 1 escalated (no recipe composed — Scalindua profunda, MAG-completeness gap). Low scores typically reflect metric calibration limits (single-reference brittleness, ingredient-name normalization gaps) rather than biological wrongness — see `RECIPE_VALIDATION_V12.md` for per-organism diagnosis.

3. **Sentinel validation** — named-strain genomes loaded as gid=900+ (excluded from V12) to validate Phase 3 sub-phase capabilities that test-set inference alone couldn't confirm. 4 sentinels as of Phase 3.8: Methylococcus capsulatus Bath (Phase 3.5 methanotrophy), Wolinella succinogenes DSM 1740 (Phase 3.4 DNRA), Nitrobacter winogradskyi Nb-255 (Phase 3.3 NOB Type B clade), Methanosarcina acetivorans C2A (Phase 3.6 ANME negative control + Phase 3.8 methanogenesis-override positive control). Per `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md`.

A full consolidated validation narrative is in `VALIDATION_REPORT.md`.

## For developers

Implementation details, contribution guide, and architecture documentation are in:

- `README_DEV.md` — Implementation README (validation pipeline scripts, database schema, key files)
- `CLAUDE.md` — Full architecture document including all addenda (confidence framework, tiered compute, thermodynamic engine, MeBiPred / hydrogenase / CAZy integrations, Media Compatibility Engine plans, ANME directional mitigation)
- `LIMITATIONS.md` — Detection-layer limitations catalog organized by category (developer-facing)
- `PROGRESS.md` — Per-session progress log
- `VALIDATION_TIMELINE.md` — V1-V12 validation progression
- `data/diagnostic_markers/REFERENCE_CURATION.md` — Per-marker curation rationale, thresholds, cross-reactivity scans

## References

- `USER_GUIDE_LIMITATIONS.md` — User-facing limitations document organized by impact
- `VALIDATION_REPORT.md` — Consolidated validation report
- `RECIPE_VALIDATION_V12.md` — V12 published-media comparison results
- `RECIPE_EVALUATION.md` — Per-organism Phase 2c recipe evaluation
- `TESTER_QUICKSTART.md` — External-tester onboarding
- `TESTER_FEEDBACK_TEMPLATE.md` — Tester feedback structure
- `TESTER_GENOMES_OF_INTEREST.md` — Suggested external-validation organism types
- `PHASE_3_CLOSEOUT.md` — Phase 3 retrospective
- `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` — Sentinel validation cross-summary
- Per-sentinel reports under `data/sentinel/<organism>/validation.md`
