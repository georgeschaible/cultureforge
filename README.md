# CultureForge

Predict cultivation media for novel and uncultured bacteria and archaea from genome sequence.

> ⚠️ **Pre-publication notice:** CultureForge is in active development. A peer-reviewed manuscript describing the methodology is in preparation. If you use CultureForge in published work, please contact george.schaible@gmail.com for current citation guidance.

## What it does

CultureForge takes a genome (or predicted proteome) and produces a cultivation media recipe — atmosphere, ingredients with concentrations, incubation conditions, and thermodynamic feasibility check. Recipes are grounded in pathway integrity scoring and curated diagnostic enzyme markers, then compared against published DSMZ and BacDive media for related organisms.

## Quick start

```bash
git clone https://github.com/georgeschaible/cultureforge.git
cd cultureforge

# Inspect a genome already in the database
python3 cultureforge.py inspect <genome_id>

# With environmental overrides
python3 cultureforge.py inspect <genome_id> --temperature 37 --ph 7

# JSON output for downstream tooling
python3 cultureforge.py inspect <genome_id> --json --output recipe.json
```

See [docs/tester/TESTER_QUICKSTART.md](docs/tester/TESTER_QUICKSTART.md) for full installation including external dependencies (gapseq, GenomeSPOT, MeBiPred, BLAST+) and database setup.

## What it covers

19 metabolic capabilities: methanogenesis, anaerobic methane oxidation (ANME), aerobic methanotrophy, sulfate reduction, denitrification, DNRA, nitrite oxidation, ammonia oxidation, sulfur oxidation, iron oxidation/reduction, anoxygenic and oxygenic phototrophy, bacteriorhodopsin, acetogenesis, organohalide respiration, anammox, fermentation, and aerobic chemoorganotrophy. See [docs/USER_GUIDE_LIMITATIONS.md](docs/USER_GUIDE_LIMITATIONS.md) for organism-type expectations.

## What it doesn't cover

Specialty metabolisms not currently supported: comammox, N-DAMO, photoferrotrophy, selenate/arsenate respiration, cable bacteria, sulfur disproportionation. Incomplete MAGs (<70% completeness) often produce escalated output rather than recipes.

## Validation

All 19 capabilities are validated against either test-set genomes or named-strain sentinels. Sentinels include *Methylococcus capsulatus* Bath, *Wolinella succinogenes* DSM 1740, *Nitrobacter winogradskyi* Nb-255, and *Methanosarcina acetivorans* C2A. Full evidence in [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md).

## Documentation

| Document | Audience |
|---|---|
| [docs/tester/TESTER_QUICKSTART.md](docs/tester/TESTER_QUICKSTART.md) | First-time users |
| [docs/USER_GUIDE_LIMITATIONS.md](docs/USER_GUIDE_LIMITATIONS.md) | Choosing whether to submit a given organism |
| [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md) | Reviewers, citing the tool |
| [docs/PHASE_3_CLOSEOUT.md](docs/PHASE_3_CLOSEOUT.md) | Methodology background |
| [docs/README_DEV.md](docs/README_DEV.md) | Developers, contributors |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | Developers (technical limitation catalog) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors |

## Citation

Pre-publication. See [CITATION.cff](CITATION.cff) for current citation guidance. Please contact george.schaible@gmail.com if you use CultureForge in published work.

## License

MIT. See [LICENSE](LICENSE).

## External dependencies

CultureForge integrates several external tools, each with their own license:

- **gapseq** (GPL-3): pathway annotation
- **GenomeSPOT** (MIT, vendored under `vendor/GenomeSPOT/`): growth condition prediction
- **MeBiPred**: metal binding prediction
- **CheckM2** (GPL-3): genome quality control
- **BLAST+** (NCBI, public domain): diagnostic marker scanning

Plus database connections to MediaDive (CC BY 4.0), BacDive (free academic use), and TEMPURA (CC BY-NC 3.0). Installation instructions in [docs/tester/TESTER_QUICKSTART.md](docs/tester/TESTER_QUICKSTART.md).
