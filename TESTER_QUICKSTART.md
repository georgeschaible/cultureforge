# CultureForge — Tester Quickstart

This is the minimal guide to get a tester productive within ~30 minutes. For the full README, see `README.md`. For developer-facing detail, see `README_DEV.md`.

---

## 1. What CultureForge does (60 seconds)

You give it a genome (or a complete proteome). It gives you a cultivation media recipe — atmosphere, ingredients with concentrations, incubation conditions, thermodynamic feasibility, and a comparison against published DSMZ / BacDive recipes.

The recipe is grounded in:
- Diagnostic-marker BLAST hits (mcrA, nrfA, nxrA, etc. — the canonical enzymes that define each metabolism)
- gapseq pathway integrity scoring
- Environmental envelope predictions (T, pH, salinity, oxygen) from GenomeSPOT / TEMPURA / BacDive
- Metal binding requirements from MeBiPred
- Thermodynamic viability check

You should treat the recipe as a starting point, not a confirmed recipe — your experimental validation closes the loop.

---

## 2. Setup (5 minutes)

CultureForge expects a Python 3.10+ environment with the project root checked out.

```bash
cd /path/to/cultureforge
python3 --version    # confirm 3.10+
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"  # confirm SQLite available
ls data/cultureforge.db    # confirm database is present
which blastp makeblastdb   # confirm BLAST+ is installed
```

If `cultureforge.db` is missing, you need a database snapshot — see `README_DEV.md` for build instructions, or request a snapshot from the project maintainer.

---

## 3. Inspecting a genome already in the database (2 minutes)

The test set contains 26 organisms (gids 7-32) plus 4 sentinels (gids 900-903). Pick any to try:

```bash
# Full inspection report (all 11 sections)
python3 cultureforge.py inspect 32   # E. coli — high-confidence aerobic chemoorganotroph

# Just the recipe
python3 cultureforge.py inspect 32 --section recipe

# Capability profile (which metabolisms fired and at what confidence)
python3 cultureforge.py inspect 32 --section capabilities

# Published-media comparison (DSMZ / BacDive diff)
python3 cultureforge.py inspect 32 --section published-media

# JSON output for downstream tooling
python3 cultureforge.py inspect 32 --json --output recipe.json
```

To list available genomes:

```bash
python3 cultureforge.py inspect --list
```

Suggested first-look genomes:
- **gid=32 (E. coli):** classic aerobic chemoorganotroph — should produce a clean LB-style recipe with V12 100%
- **gid=8 (Methanocaldococcus jannaschii):** hyperthermophilic methanogen — recipe should be H2/CO2 anaerobic at 85°C
- **gid=28 (Methanoperedens nitroreducens):** ANME-2d — recipe should be CH4/N2 anaerobic with NaNO3 acceptor
- **gid=903 (Methanosarcina acetivorans, sentinel):** forward methanogen — Phase 3.8 sentinel demonstrating override path

---

## 4. Submitting a new genome (15 minutes)

The full processing pipeline (gapseq + GenomeSPOT + MeBiPred + CheckM2 + marker BLAST) takes 2-3 hours per genome and requires the external tools to be installed. For a tester scenario where these tools may not be available, the simplified marker-BLAST-only sentinel pattern works for many use cases:

```bash
# 1. Download the proteome (NCBI RefSeq)
mkdir -p data/sentinel/<organism_name>
cd data/sentinel/<organism_name>
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/<...path...>/protein.faa.gz
gunzip protein.faa.gz
mv protein.faa proteome.faa
cd ../../..

# 2. Register in the database (use a unique gid in the 901-999 range to avoid V12 collision)
python3 -c "
import sqlite3
conn = sqlite3.connect('data/cultureforge.db')
conn.execute('INSERT INTO genomes (id, accession, source, file_path, biomass_template, notes) VALUES (?, ?, ?, ?, ?, ?)',
             (901, 'GCF_XXXXX', 'NCBI_RefSeq', 'data/sentinel/<organism>/proteome.faa', 'Gram_neg', 'TESTER: <organism>'))
conn.commit()
"

# 3. Run marker BLAST
python3 run_marker_blast.py data/sentinel/<organism>/proteome.faa --genome-id 901

# 4. Inspect
python3 cultureforge.py inspect 901
```

Caveats with marker-only loading:
- Capabilities that require gapseq pathway integrity (acetogenesis, oxygenic phototrophy) won't fire as primary
- TEMPURA / GenomeSPOT data isn't loaded → temperature defaults to 30°C, pH to 7.0
- Metal requirement profiles (MeBiPred) are absent → trace-element profile is the SL-10 baseline rather than organism-specific

For full pipeline processing, follow `README_DEV.md` (requires gapseq, GenomeSPOT, MeBiPred installed).

---

## 5. Interpreting output (5 minutes)

### Primary cultivation mode

The label carries the biology. Examples:
- `aerobic_chemotrophic` — generic aerobic heterotroph or chemolithotroph
- `lithotrophic_aerobic (nitrite oxidation, canonical NOB)` — Type A or B NOB
- `anme_reverse_methanogenic (ANME-2d, nitrate-coupled)` — ANME with nitrate acceptor

Read the label, not just the category.

### Confidence interpretation

- **≥ 0.85:** strong evidence
- **0.65 – 0.85:** good evidence (typically marker + pathway, or strong override path)
- **0.50 – 0.65:** suggestive
- **< 0.50:** rejected

### Recipe sections

- **Gas phase:** headspace composition (e.g., CH4:air 80:20 for methanotrophs, H2:CO2 80:20 for hydrogenotrophic methanogens)
- **Ingredients:** grouped by role (buffer / salt / electron donor / acceptor / carbon source / trace metal / vitamin / reducing agent / supplement). Each has a confidence and a one-line rationale.
- **Thermodynamic check:** ΔG for the proposed energy metabolism at the chosen conditions. "Feasible" / "borderline" / "infeasible".
- **Uncertainty flags:** highlight components below 0.75 confidence — try variants in experiments.
- **Published-media comparison:** diff against DSMZ / BacDive media for the matched species or its functional neighbors.

---

## 6. Common output patterns

| Pattern | Meaning | What to do |
|---|---|---|
| "Escalated — no recipe composed" | CultureForge couldn't determine primary mode (usually MAG completeness) | Manual annotation may help; check Quality section |
| Low V12 score (< 50%) | Metric measured ingredient-level diff against DSMZ; doesn't always reflect biology | Read recipe biology + per-organism diagnostic in `RECIPE_VALIDATION_V12.md` |
| Multi-modal organism (alternatives listed) | Genome supports multiple metabolisms; primary picked by Phase 3.6 priority + marker corroboration | Use --temperature / --ph / --salinity to push toward the alternative if it's closer to experimental intent |
| "ANME directional ambiguity" flag | mcrA fires but ANME OR-group is incomplete | Recipe defaults to forward methanogenesis; consider alt-acceptor variant if direction uncertain |

---

## 7. Reporting feedback

Use `TESTER_FEEDBACK_TEMPLATE.md` for structured feedback. The template ensures comparable feedback across testers. Key fields:

- Organism / accession submitted
- Expected biology (your domain knowledge)
- Actual CultureForge output (paste relevant sections)
- Biological assessment of recipe correctness
- Suggestions / issues / cultivation-protocol references

Submit feedback to: (TBD — see project lead for distribution channel)

---

## 8. References

- `README.md` — Full user-facing introduction
- `USER_GUIDE_LIMITATIONS.md` — What CultureForge can and cannot do, in user-facing language
- `VALIDATION_REPORT.md` — Consolidated validation evidence across Phases 1–3.8
- `TESTER_FEEDBACK_TEMPLATE.md` — Feedback structure
- `TESTER_GENOMES_OF_INTEREST.md` — Suggested external-validation organism types

For developer-facing detail (database schema, full pipeline scripts, contribution guide):
- `README_DEV.md`
- `CLAUDE.md`
- `LIMITATIONS.md`
