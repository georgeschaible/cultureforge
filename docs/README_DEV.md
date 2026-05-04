# CultureForge

CultureForge predicts cultivation media for novel uncultured bacteria and archaea by integrating genome annotation (gapseq), growth condition prediction (GenomeSPOT), metal binding prediction (MeBiPred), genome quality control (CheckM2), and a custom capability detection framework with diagnostic enzyme markers and pathway integrity scoring.

## Quick Start

### Inspecting genomes

CultureForge maintains an inspection tool for examining what the system has learned about each genome.

```bash
python3 cultureforge.py inspect <identifier>
```

The identifier can be a numeric genome ID, an NCBI accession, or a species name. Use `--list` to see all available genomes.

```bash
python3 cultureforge.py inspect --list
python3 cultureforge.py inspect 8
python3 cultureforge.py inspect NC_000909.1
python3 cultureforge.py inspect "Methanococcus"
```

The full report includes genome quality (CheckM), growth condition predictions (GenomeSPOT), the capability profile with full evidence trails, gapseq pathway hits, diagnostic marker results, and the recommended action.

Use `--section` to limit output to specific portions:

```bash
python3 cultureforge.py inspect 8 --section capabilities
python3 cultureforge.py inspect "Methanococcus" --section quality
```

JSON output for programmatic use:

```bash
python3 cultureforge.py inspect 8 --json > methanococcus_report.json
```

## Recipe context

Before recipe synthesis (Phase 2c), CultureForge translates capability profiles
into structured recipe-relevant facts. Inspect this with:

```bash
python3 cultureforge.py inspect <genome> --section recipe-context
```

The recipe context includes atmosphere, carbon sources, electron donors and
acceptors, nitrogen sources, trace metals, cofactors, growth conditions, and
special requirements (such as syntrophic partner organisms or high-temperature
incubation). Each field carries an evidence trail showing where the value came from.

## Generating recipes

CultureForge generates cultivation media recipes from genome data:

```bash
python3 cultureforge.py inspect <genome> --section recipe
```

The recipe includes atmosphere (gas phase composition + pressure), ingredients
with concentrations and rationale (organized by category — buffer, salts, carbon
source, electron donor/acceptor, reducing agent, trace metals, vitamins,
supplements), incubation conditions (temperature, pH, light, shaking),
thermodynamic feasibility check (ΔG of dominant energy-conserving reaction
under default substrate activities), and uncertainty flags traced to
`LIMITATIONS.md` categories.

For organisms where multiple cultivation modes are detected, the recipe is
generated for the dominant mode (with biology-aware preference for specific
modes like methanogenic / acetogenic / phototrophic / lithotrophic over
generic aerobic/anaerobic/fermentative); alternatives are listed in the recipe header.

For organisms where capability detection failed catastrophically, the recipe
output is escalated (`escalated: true`) with an explicit reason — typical for
incomplete MAGs that lack diagnostic markers in their predicted proteome.

The `--json` mode includes the recipe object as a top-level `recipe` field.

See `RECIPE_EVALUATION.md` for the empirical evaluation across all 26 development +
blind organisms (21/26 biologically reasonable; 8/8 standard-medium comparisons match).

## Comparing recipes against published cultivation literature

Phase 2d adds a consistency layer that compares each generated recipe against
published media from the MediaDive / DSMZ corpus, surfacing structured ingredient-
and conditions-level differences:

```bash
python3 cultureforge.py inspect <genome> --section published-media
```

The output is structured for actionable use, not a numeric pass/fail. For each
organism the inspector shows:

- **Direct match** — when the species has a BacDive entry linked to one or more
  MediaDive media, the comparison runs against those references directly.
- **Functional neighbor match** — when no direct BacDive entry exists (e.g.,
  Candidatus organisms with no cultured representatives), the inspector finds
  the most functionally-similar organisms in the dev/blind set by capability-
  vector cosine similarity and uses their published media as proxies.
- **Ingredient-level diff** — categorized by severity (critical / important /
  minor): ingredients shared, ingredients only in references (potentially
  missing from CF), ingredients only in CF (potentially over-specified), and
  concentration disagreements (>2× difference vs reference median).
- **Cultivation-condition checks** — temperature (vs TEMPURA-derived expected
  optimum + matched-strain BacDive culture-temp records), pH (vs MediaDive
  min_pH/max_pH range + TEMPURA optima), atmosphere (vs majority-signal from
  reference medium names). Each fired mismatch deducts 0.20 from the aggregate
  agreement score.
- **Aggregate agreement score** — frequency-weighted high-frequency consensus
  for n ≥ 3 reference media, Jaccard `|∩|/|∪|` for n ≤ 2.

**The diff output is the primary actionable deliverable.** The aggregate
agreement score is informational and serves as a triage signal — high agreement
(≥70%) means the recipe lands in the published-media distribution; low
agreement is *diagnostic* (the inspector explains *why* the score is what it
is via the diff list and condition-mismatch entries), pointing the user to
specific ingredients to consider adding/dropping or specific conditions to
verify.

See `RECIPE_VALIDATION_V11.md` for the full validation results across all 26
organisms, including known metric limitations (TEMPURA pH coverage sparse;
single-reference Jaccard brittleness; GenomeSPOT temperature mispredictions
for some organisms).

## Manual cultivation condition overrides

When you have domain knowledge that the automated pipeline lacks (e.g., a
novel organism not in TEMPURA, or a species where GenomeSPOT mispredicts),
you can override cultivation conditions directly:

```bash
python3 cultureforge.py inspect "Lactobacillus" --temperature 30
python3 cultureforge.py inspect "Picrophilus" --ph 0.7 --temperature 60
python3 cultureforge.py inspect "Halobacterium" --salinity 250
```

Overrides apply to the recipe immediately and are tracked transparently —
the inspector shows a `USER OVERRIDES APPLIED:` annotation in the recipe
header, the per-field source string in the rationale switches to
`user_override`, and JSON output carries a `user_overrides` field at the
top level alongside per-field source labels in `recipe.conditions`.

Override ranges (inputs outside these ranges are rejected with a clear
error message):

- `--temperature`: 0–130 °C
- `--ph`: 0–14
- `--salinity`: 0–400 g/L NaCl

Each flag is independent. Override only what you know; the rest is derived
normally (TEMPURA-first, GenomeSPOT-fallback per Phase 2e).

## Architecture

See `CLAUDE.md` for the full architecture document including database schema, tiered analysis design, and all addenda.

## Validation

See `VALIDATION_TIMELINE.md` for the V1-V11 validation progression. Current status:
- Dev set: 18/18 user-specified detection checks pass (post Phase 1.5n).
- Blind set: 5/8 fully correct + 4 partial + 1 incorrect (Scalindua escalated; honest scoring).
- Recipe evaluation (Phase 2c): 21/26 biologically reasonable recipes; 8/8 standard-medium comparisons match.
- Published-media validation (Phase 2e, V12): 7/26 ≥70% agreement, 7/26 in 50-69% band, 12/26 <50%. Phase 2e G.1 fix (TEMPURA-first condition priority) lifted 5 organism scores by +20 to +40 points; G.4 BacDive atmosphere supplement correctly newly-flags Campylobacter as aerobic-vs-microaerobic mismatch. Per `RECIPE_VALIDATION_V12.md`.
- Phase 3 sub-phase capabilities are validated against named type strains via the **sentinel pattern** (gid=900+, excluded from V12). 4 sentinels loaded as of Phase 3.7: Methylococcus capsulatus Bath (Phase 3.5 aerobic methanotrophy), Wolinella succinogenes DSM 1740 (Phase 3.4 DNRA), Nitrobacter winogradskyi Nb-255 (Phase 3.3 NOB Type B clade), Methanosarcina acetivorans C2A (Phase 3.6 ANME-negative control). Per `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md`. Capability tagging — validated-against-sentinel vs inferred-from-test-set-only — is in `LIMITATIONS.md` "Validation status" section.

## Phase 4.1 wrapper architecture

The Phase 4.1 `process` subcommand orchestrates the full pipeline for new genomes:

```
cultureforge.py process --input <genome.fna>
    │
    ├─► register_genome.register_genome()   # gid >= 1000, refuses duplicate accession
    ├─► process_genome.run_prodigal()       # apt prodigal; -p single
    ├─► process_genome.run_gapseq()         # conda env "gapseq"; find → find-transport → draft
    ├─► process_genome.run_genomespot()     # vendored; runs via project Python
    ├─► process_genome.run_marker_blast()   # apt blastp; against data/diagnostic_markers/blastdb_*
    ├─► process_genome.run_checkm2_if_available()      # optional; conda env "checkm2"
    └─► process_genome.run_mebipred_if_available()     # optional; pip install mymetal
            │
            ├─► loaders/gapseq_generic.py        → genome_pathways, genome_transporters, genome_reaction_markers
            ├─► loaders/genomespot_generic.py    → genome_growth_predictions
            ├─► loaders/marker_blast_generic.py  → genome_diagnostic_markers
            └─► loaders/mebipred_generic.py      → protein_metal_binding, genome_metal_profile
```

### Conda environment discovery

`process_genome.find_tool(name, conda_env)` searches in this order:

1. `CULTUREFORGE_<TOOL>_BIN` env var (e.g. `CULTUREFORGE_GAPSEQ_BIN=/path/to/env/bin`)
2. `conda env list --json` → look for an env with the named name → check `<env>/bin/<tool>`
3. `shutil.which(tool)` on the ambient PATH

This means a user with `conda create -n gapseq -c bioconda gapseq` gets gapseq found automatically without needing to `conda activate gapseq` before running.

### gid convention

- **gids 7-32**: V12 test set — frozen; modifications require V12 byte-identical re-verification
- **gids 900-903**: sentinels — protected by `deregister_genome` gid-range guard
- **gids >= 1000**: user-loaded genomes via `cultureforge.py process` — auto-assigned by `register_genome` starting from `USER_GID_MIN = 1000`

### Cleanup-on-failure

`process_genome.process_genome()` wraps the pipeline stages in try/except. Any unhandled exception triggers `register_genome.deregister_genome(gid)` to remove the partial database state across all 14 genome_id-referencing tables. The user retries from a clean slate.

### What stays untouched (Phase 4.1 prohibition)

The existing `load_gapseq.py`, `load_genomespot.py`, `load_mebipred.py`, `run_marker_blast.py` scripts produced the test-set data correctly via their hardcoded `main()` orchestrations. Their per-marker loader functions (`load_pathways`, `load`, `blast_all_markers`, etc.) are already gid-parameterized and are reused by the new generic loaders. The hardcoded `main()` orchestrations are intentionally NOT replaced — they remain the reproducibility anchor for the existing test-set data.

### Adding new optional tools (e.g. dbCAN for CAZy annotation)

1. Add `run_<tool>_if_available()` to `process_genome.py` mirroring `run_checkm2_if_available()`:
   - Returns `None` and prints `[N/M] <tool> not installed — skipping (...)` if missing
   - Returns the path to its output if it ran successfully
2. Add `loaders/<tool>_generic.py` wrapping the existing `load_<tool>.py:load()` function (or write a fresh loader if there isn't one)
3. Wire into `process_genome.process_genome()` in the appropriate stage slot
4. Add `--skip-<tool>` flag in `cultureforge.py` argparse

## Key Files

- `cultureforge.py` — Main entry point (`inspect` + Phase 4.1 `process` subcommands)
- `register_genome.py` — Phase 4.1 generic registration with duplicate-accession refusal + test-set/sentinel deregister protection
- `process_genome.py` — Phase 4.1 end-to-end pipeline wrapper
- `loaders/` — Phase 4.1 thin façades over the existing load_*.py loader functions, parameterized for any gid
- `load_gapseq.py`, `load_genomespot.py`, `load_mebipred.py`, `run_marker_blast.py` — original hardcoded test-set loaders. PHASE 4.1 PROHIBITION: do not modify (reproducibility anchor for test-set data)
- `capability_detectors.py` — Parallel pathway-integrity detectors with diagnostic-marker override (Phase 1.5n)
- `data/pathway_definitions.json` — Declarative metabolism definitions
- `recipe_context.py` + `derive_recipe_context.py` — Phase 2b RecipeContext layer
- `recipe.py` + `compose_recipe.py` — Phase 2c recipe composer with thermodynamic gating
- `mediadive_client.py` + `bacdive_client.py` — Phase 2d external API clients (cache-primary, live fallback)
- `capability_vector.py` — Phase 2d capability-vector encoding + functional-neighbor matching
- `recipe_comparison.py` — Phase 2d ingredient + conditions diff engine
- `RECIPE_EVALUATION.md` — Per-organism empirical evaluation of generated recipes (Phase 2c)
- `RECIPE_VALIDATION_V11.md` — Phase 2d external-validation results
- `LIMITATIONS.md` — Detection-layer limitations catalog (categories A–G)
- `data/cultureforge.db` — SQLite database with all integrated data including the Phase 2d cache tables
- `synthesize_denovo.py` — Phase 1 de novo synthesizer; `determine_energy_metabolism()` deleted as of Phase 2c (replaced by `compose_recipe.compose_recipe()`)
