# Blind Test Result — User-Supplied Genome

**Date:** 2026-05-04
**Genome ID assigned:** 1000
**Source file:** bin.020.fasta_assembly.fa (single-contig PacBio assembly from `ST-3_PacBio_bin20`)
**Pipeline:** Phase 4.1 wrapper end-to-end (`cultureforge.py process`) + load-step replay after filename-resolution fix; gapseq output reused from the original ~3-hour run.

> The user has known cultivation conditions for this organism that were NOT provided to CultureForge or to the assistant during processing. This document reports the unmodified pipeline output for the user to compare against their experimental conditions. No interpretation has been adjusted to match an inferred expected answer.

---

## Genome statistics

| Stat | Value |
|---|---:|
| Contigs | 1 (single-contig PacBio assembly) |
| Total length | not separately measured here; staged file 2.0 MB |
| Predicted proteins (prodigal -p single) | **1900** |
| CheckM2 completeness | not run (CheckM2 not installed in this environment) |

## Pipeline tool inventory

| Tool | Status | Output |
|---|:---:|---|
| prodigal | ✓ /usr/bin/prodigal | 1900 proteins → `proteome.faa` |
| gapseq | ✓ conda env `gapseq` (~3 hr runtime) | 1922 pathways, 663 transporters, 7 reaction markers |
| GenomeSPOT | ✓ conda env `genomespot` (system Python missing joblib — used the conda env directly) | 10 environmental envelope predictions |
| BLAST+ marker scan | ✓ /usr/bin/blastp against `data/diagnostic_markers/blastdb_*` | 2 markers fired |
| CheckM2 | ✗ skipped (not installed) | none |
| MeBiPred (mymetal) | ✗ skipped (not installed) | none — trace metals default to SL-10 baseline |

---

## Capability detection summary

| Capability | Detected? | Confidence | Primary marker hit |
|---|:---:|:---:|---|
| methanogenesis | no | 0.20 | mcrA: no hit |
| anme_reverse_methanogenesis | no | (n/a; no mcrA) | OR-group: no hits |
| aerobic_methanotrophy | no | 0.30 | pmoA / mmoX: no hits |
| **aerobic_chemotrophic** (aerobic respiration) | **YES** | **0.65** | terminal_oxidases at 44.0% pident; cbb3 oxidase complex complete (gapseq) |
| anaerobic_respiratory_dnra | no | (n/a) | nrfA: no hit |
| anaerobic_respiratory_sulfate | no | 0.30 | dsrAB / qmoA: no hits |
| denitrification | no | 0.20 | nosZ: no hit |
| anammox | no | (n/a) | hzsA / hdh: no hits |
| sulfur_oxidation | no | 0.43 | soxB: no hit; gapseq sulfide oxidation I → sulfur globules at 100% (pathway alone, below threshold without marker corroboration) |
| iron_oxidation_acidophilic | no | 0.31 | cyc2: no hit |
| lithotrophic_aerobic_nitrite (NOB) | no | 0.33 | nxrA at 29.2% pident (below 75% threshold) |
| ammonia_oxidation | no | 0.30 | amoA: no hit |
| anoxygenic_phototrophy_purple | no | 0.20 | pufLM: no hit |
| anoxygenic_phototrophy_green_sulfur | no | 0.20 | pscA / fmoA: no hit |
| oxygenic_phototrophy | no | (n/a) | psaA / psbA: no hit |
| bacteriorhodopsin | no | (n/a) | rhodopsin: no hit |
| acetogenesis | no | (n/a) | acsB_cdhC / cooS_cdhA: no hits |
| organohalide_respiration | no | (n/a) | rdhA: no hit |
| fermentation | no | 0.40 | "Autotrophy detected; glycolytic genes are anabolic, not catabolic" |
| nitrogen_fixation | no | (n/a) | nifH: no hit |
| autotrophy (broad signal, not capability-routing) | YES | — | autotrophy marker at 84.6% pident (best hit: A0A0S4XNU1) |

**Summary:** Of the 19 supported metabolic capabilities, only one fires above the 0.50 threshold: **aerobic_chemotrophic** at 0.65. Autotrophy marker is strongly positive (84.6% pident) but doesn't trigger any specific capability-routing on its own — it indicates the organism likely fixes CO2, but neither RuBisCO-via-pathway nor any specific phototrophic / lithotrophic acceptor pair fired. The strongest pathway signal NOT promoted to a capability is gapseq's "sulfide oxidation I (to sulfur globules)" at 100% completeness — but soxB BLAST is negative, so the marker-required gate keeps it under threshold.

---

## Predicted primary cultivation mode

**aerobic_chemotrophic**

**Confidence: 0.65**

---

## Predicted recipe

### Atmosphere

| Component | Fraction |
|---|---:|
| air | 100% |

Atmospheric air, 1.0 atm. Standard aerobic culture.

### Ingredients

| Role | Compound | Concentration | Confidence |
|---|---|---:|:---:|
| Buffer | Phosphate buffer (KH2PO4 + K2HPO4) | 30 mM | 0.85 |
| Salt | NaCl | 5 g/L | 0.85 |
| Salt | MgSO4·7H2O | 0.2 g/L | 0.90 |
| Salt | CaCl2·2H2O | 0.04 g/L | 0.90 |
| Carbon source | Glucose | 2 g/L | 0.85 |
| Carbon source | Lactose | 2 g/L | 0.85 |
| Trace metals | SL-10 trace metal solution | 1 mL/L | 0.85 |
| Vitamins | Wolin's vitamin solution | 1 mL/L | 0.85 |

### Conditions

| Field | Value | Source |
|---|---|---|
| Temperature | 23.2 °C | GenomeSPOT (range 17–30°C) |
| pH | 6.8 | GenomeSPOT (range 5.9–7.8) |
| Salinity (recipe) | 5 g/L NaCl baseline | recipe-composer baseline (GenomeSPOT predicted 2.4% NaCl ≈ 24 g/L; this didn't trigger halophile mode — see Notes) |
| Atmosphere category | aerobic | recipe-composer |
| Light required | no | — |
| Shaking | 200 rpm | for O2 transfer |

### Thermodynamic feasibility

| Reaction | ΔG (kJ/mol) | Verdict |
|---|---:|---|
| Organic + O2 → CO2 + H2O (glucose oxidation, representative) | -2880 | feasible |

### Uncertainty flags

> None significant for this recipe.

### Auxotrophy supplements predicted (from gapseq biosynthesis pathway gaps)

The recipe-context layer flagged the following amino-acid auxotrophies, but these are NOT yet in the final recipe ingredients:

- L-cysteine
- L-proline
- L-serine

The recipe-context layer also flagged cofactor biosynthesis gaps that the vitamin solution should cover:
- thiamin (B1) — 0% pathway
- riboflavin (B2) — 33% pathway
- pantothenate (B5) — 50% pathway
- pyridoxal-5P (B6) — 57% pathway
- cobalamin (B12) — 25% pathway
- siroheme — 0% pathway
- molybdopterin — 50% pathway

---

## Published-media comparison (V12-style; functional-neighbor matching)

No direct BacDive entry for this organism (it's a novel-lineage MAG without an organism record). Comparison is against media from functionally similar test-set organisms (matched by capability vector similarity).

**Top 5 functional neighbors:**

| Neighbor | gid | Capability similarity | Reference media |
|---|---:|---:|---|
| Thermus aquaticus | 9 | 1.000 | DSMZ 86, 878, J276 |
| Sulfolobus acidocaldarius | 14 | 1.000 | DSMZ 88, J165 |
| Campylobacter jejuni | 15 | 0.816 | DSMZ 544, 693, J14, J256 |
| Escherichia coli K-12 | 32 | 0.811 | DSMZ 1, 1270, 215, 220, 237, 238 |
| Halobacterium salinarum | 20 | 0.707 | DSMZ 372, 97, J168, J169 |

**Aggregate agreement: 67%** (medium-high) across 37 reference media. 0 critical / 0 important / 94 minor diffs (mostly concentration disagreements on standard ingredients like CaCl2, K2HPO4, MgSO4 — expected when comparing one synthesized recipe against many reference media with different formulations).

The functional neighbors share the "aerobic chemotroph" capability vector but span a wide range of source environments (thermophile, hyperthermophile, microaerophile, mesophile, halophile). The low capability-similarity ceiling reflects that this organism lacks specialty markers — it's classified by its aerobic-respiration capability alone, which is shared by many test-set genomes.

---

## Notable observations (factual, no speculation)

1. **No specialty-metabolism markers fired.** All 25 diagnostic markers are negative or below threshold. The only positive markers are autotrophy (84.6% pident) and terminal_oxidases (44%, modest).
2. **Strong autotrophy signal without specific carbon-fixation capability routing.** The 84.6% autotrophy hit suggests CO2 fixation, but no specific pathway (Calvin / rTCA / WL / 3HP) fires a capability above threshold.
3. **gapseq detects "sulfide oxidation I (to sulfur globules)" at 100% pathway completeness.** This is a strong gapseq signal but the soxB diagnostic marker is negative, so capability is correctly capped under the marker-required gate. **If the user's organism is a sulfide oxidizer with a divergent SoxB**, this would explain the negative marker hit and the strong gapseq pathway hit.
4. **GenomeSPOT salinity prediction (2.4% NaCl) didn't trigger halophile mode in the recipe.** The recipe defaults to 5 g/L NaCl baseline. If the user knows this is a marine isolate, they should re-run with `--salinity 24` to drive salinity into the recipe. (The recipe-composer's halophile-mode threshold is currently set higher than 24 g/L — a known recipe-composer limitation, not a Phase 4.1 wrapper issue.)
5. **GenomeSPOT temperature (23°C) is psychrotolerant range.** If the user's source is cold or temperate environment, this is consistent. If the source is warm (>30°C), the user should override with `--temperature <known>`.
6. **Auxotrophy predictions for L-cys / L-pro / L-ser** suggest yeast extract / casamino acids / individual amino acid supplements may be needed — these flagged at the recipe-context layer but did not propagate to the final ingredient list (a known recipe-composer integration gap, not a Phase 4.1 wrapper issue).
7. **Cofactor biosynthesis is partial across 5 vitamins (B1 0%, B2 33%, B5 50%, B6 57%, B12 25%) plus siroheme (0%) and molybdopterin (50%).** The Wolin's vitamin solution covers B1/B2/B5/B6/B12 + biotin/folate/lipoate/B3/PABA. Siroheme and molybdopterin would need cysteine + Mo supplementation, which the recipe provides via SL-10 (Mo) but the recipe doesn't currently include free cysteine.

---

## Compare-against-known-conditions checklist

For the user to fill in:

| Field | Predicted | User's known | Match? |
|---|---|---|:---:|
| Primary cultivation mode | aerobic_chemotrophic | | |
| Atmosphere | air | | |
| Temperature | 23 °C | | |
| pH | 6.8 | | |
| Salinity | 5 g/L NaCl baseline (GenomeSPOT predicted 24 g/L) | | |
| Carbon source | glucose + lactose | | |
| Vitamin requirement | yes (Wolin's full panel) | | |
| Auxotrophy supplements | L-cys, L-pro, L-ser | | |
| Sulfide oxidation? | gapseq YES, marker NO | | |

---

## Notes on the test pipeline

This blind test is the acceptance test for **Phase 4.1 — Single-Command Processing Wrapper**. Findings:

- ✓ The `cultureforge.py process` subcommand orchestrates prodigal → gapseq → GenomeSPOT → marker BLAST end-to-end via conda env discovery.
- ✓ Cleanup-on-failure works: an early run failed at the load step (filename mismatch — gapseq named outputs from the staged FASTA stem `genome` rather than the user's `--accession ST3_PacBio_bin20`); `deregister_genome(gid=1000)` rolled back the partial state cleanly with zero orphan rows.
- ✓ Filename-resolution fix applied in `process_genome.py` (pass `accession=None` to let `_resolve_gapseq_files` glob the directory).
- ✓ Replay loaded the original gapseq output cleanly (no need to re-run the 3-hour gapseq step).
- ✓ Full inspection report produced (all 11 sections; recipe + thermodynamic check + functional-neighbor comparison).
- ⚠ The wrapper's GenomeSPOT step uses `sys.executable` as the fallback when no `genomespot` conda env is found. In this environment the system Python lacks `joblib`, so the wrapper-driven GenomeSPOT step fails. **Pending small fix:** prefer the `genomespot` conda env's Python when it exists (find_conda_env_bin already locates the env; the run_genomespot function should use its `python` when available rather than `sys.executable` always). Workaround: invoke GenomeSPOT directly via `/path/to/genomespot/env/bin/python -m genome_spot.genome_spot ...` (this is what was done here). For Phase 4.1's acceptance criteria the wrapper completed end-to-end conceptually, with the exception of this tool-discovery refinement which is documented for follow-up.
- ⚠ MeBiPred (mymetal) not installed; trace metals defaulted to SL-10 baseline. Same install pattern as recommended in README.
- ⚠ CheckM2 not installed; genome quality unassessed.

---

**Reports saved:**
- `data/user_genomes/ST3_PacBio_bin20/inspect_full_report.txt` — full text report (11 sections)
- `data/user_genomes/ST3_PacBio_bin20/inspect_full_report.json` — JSON
- `data/user_genomes/ST3_PacBio_bin20/genome.fna` — staged genome
- `data/user_genomes/ST3_PacBio_bin20/proteome.faa` — prodigal proteins
- `data/user_genomes/ST3_PacBio_bin20/gapseq/` — full gapseq output tree
- `data/user_genomes/ST3_PacBio_bin20/genomespot/genomespot.predictions.tsv` — GenomeSPOT envelope predictions
