# CultureForge

Predict cultivation media for novel and uncultured bacteria and archaea from genome sequence.

> ⚠️ **Pre-publication notice:** CultureForge is in active development. A peer-reviewed manuscript describing the methodology is in preparation. If you use CultureForge in published work, please contact george.schaible@gmail.com for current citation guidance.

## What it does

CultureForge takes a genome (or predicted proteome) and produces a cultivation media recipe — atmosphere, ingredients with concentrations, incubation conditions, and thermodynamic feasibility check. Recipes are grounded in pathway integrity scoring and curated diagnostic enzyme markers, then compared against published DSMZ and BacDive media for related organisms.

## Installation

CultureForge orchestrates several external bioinformatics tools. Realistic installation takes 30–60 minutes.

```bash
# 1. System tools (apt or equivalent)
sudo apt install prodigal ncbi-blast+

# 2. The main external tool — gapseq, in its own conda env
conda create -n gapseq -c bioconda gapseq

# 3. Optional but recommended
conda create -n checkm2 -c bioconda checkm2     # genome QC
pip install mymetal                              # MeBiPred metal binding

# 4. Clone CultureForge
git clone https://github.com/georgeschaible/cultureforge.git
cd cultureforge

# 5. Verify the in-repo database loads
python3 cultureforge.py inspect 8 --section recipe
```

GenomeSPOT is vendored under `vendor/GenomeSPOT/` and runs via the project Python — no separate install needed for it.

The `process` subcommand finds gapseq automatically by looking for a conda env named `gapseq`. To override, set `CULTUREFORGE_GAPSEQ_BIN=/path/to/gapseq/env/bin`.

## Usage

**Process a new genome end-to-end:**

```bash
python3 cultureforge.py process \
    --input my_genome.fna \
    --accession my_organism
```

This runs prodigal → gapseq → GenomeSPOT → marker BLAST → optional CheckM2/MeBiPred and registers the genome in the database. Total runtime: 1–2 hours per genome (gapseq is the slow step). The genome is assigned `gid >= 1000` to keep it separate from the test set.

**View the cultivation recipe:**

```bash
python3 cultureforge.py inspect my_organism
```

**Inspect a test-set genome already in the database:**

```bash
python3 cultureforge.py inspect 8                       # by gid
python3 cultureforge.py inspect NC_000909.1             # by accession
python3 cultureforge.py inspect 8 --section recipe      # one section only
python3 cultureforge.py inspect 8 --json --output out.json
```

**Override environmental conditions** (use when you have domain knowledge):

```bash
python3 cultureforge.py inspect my_organism --temperature 37 --ph 7 --salinity 0.5
```

**One-shot process + inspect:**

```bash
python3 cultureforge.py process --input my_genome.fna --inspect > recipe.txt
```

See [docs/tester/TESTER_QUICKSTART.md](docs/tester/TESTER_QUICKSTART.md) for installation troubleshooting and per-tool details.

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
