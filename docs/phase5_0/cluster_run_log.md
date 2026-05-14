# Phase 5.0 Cluster Gapseq Run

## Summary

In May 2026, gapseq pathway analysis for the Phase 5.0 organism set was performed
on the UCSB CNSI Pod cluster (pod-login1.cnsi.ucsb.edu) rather than on the home
workstation. This was necessary because gapseq on WSL2 stalled repeatedly during
batch processing of multiple genomes. The cluster batch completed 135 genomes
successfully in approximately 2 hours of wall-clock time.

## Inputs

- **Source TSV**: `data/release/phase5_0_genome_list_final.tsv` (full version with
  cultivation conditions) — on Pod, a minimal 3-column variant was used because
  the full TSV is gitignored and could not be transferred easily during travel.
- **Audit correction genomes** (4): GCF_001280255.1 (Thermus aquaticus YT-1),
  GCF_000012965.1 (Sulfurimonas denitrificans DSM 1251),
  GCF_000008265.1 (Picrophilus torridus DSM 9790),
  GCF_002443295.1 (Scalindua japonica MAG — substituted for unavailable S. profunda).

## Outputs

All gapseq outputs transferred to `data/cluster_gapseq_outputs/<accession>/`.
Each directory contains:

- `<accession>-all-Pathways.tbl` — pathway completeness predictions
- `<accession>-all-Reactions.tbl` — reaction-level details
- `<accession>-all-find_aligner.log` — small log file
- `<accession>.faa.gz` — empty placeholder file (gapseq artifact)

**Counts**:
- 135 total directories
- 110 with 1933-line Pathways.tbl (Bacteria mode, full output)
- 25 with 419-line Pathways.tbl (Archaea mode, full output)
- 0 empty/failed

**Total size**: 1.5 GB

## Pod environment

- **gapseq location**: `/home/gschaible/gapseq/` (git-cloned, source install)
- **gapseq version**: 2.0.0
- **Conda env**: `gapseq_deps` (BLAST 2.16, prodigal, hmmer, glpk, etc.)
- **R**: module `R/4.5.1` at `/sw/R/R-4.5.1/`
- **R personal library**: `/home/gschaible/R/library/` (data.table, stringr, stringi, getopt, R.utils)
- **Reference sequence DB**: `/home/gschaible/gapseq/dat/seq/` (Bacteria + Archaea, version 1.4, zenodoID 16908828, date 2025-12-01)
- **Working directory**: `/home/gschaible/cultureforge_cluster/`

## SLURM workflow

Array job submitted via `~/phase5_0_gapseq_array.sh` on Pod:

- Partition: batch
- Resources: 8 CPUs, 16 GB RAM, 4-hour time limit per task
- Array: 1-131 with %20 concurrency limit (131 tasks for the 131 genomes; audit corrections processed separately first)
- Per-task runtime: 6-30 minutes (Archaea faster, Bacteria slower; varies with genome size)
- Total wall time: ~2-3 hours
- Errors: 0

## Known gaps (NCBI suppressions)

Two accessions in the minimal TSV resolve in NCBI metadata but do not have
downloadable genome FASTAs (status: "suppressed"). Processing skipped these:

| Accession | Organism | Status |
|---|---|---|
| GCF_000012605.1 | Hydrogenovibrio crunogenus XCL-2 | suppressed at NCBI |
| GCF_000315115.1 | Candidatus Kuenenia stuttgartiensis | suppressed at NCBI |

Potential replacements to investigate later:

- **Kuenenia stuttgartiensis CSTR1**: GenBank CP049055 / assembly GCA_011059055.1 (Ding & Adrian 2020)
- **Hydrogenovibrio**: Look at sister strains: H. thermophilus MA2-6 (JOMK01000001),
  H. marinus MH-110 (JOML01000001), or the H. crunogenus SP-41 strain (Hansen 2019).

These can be processed as a small follow-up batch when needed.

## Reproducibility

The cluster setup is documented step-by-step in this file's git history. Key
challenges resolved during setup:

1. gapseq 1.x conda install failed due to r-glpkapi/glpk version conflicts.
   Solution: source install + manual R package installation.
2. R packages had to be installed via system R (later via R/4.5.1 module),
   not conda env's R, to maintain binary compatibility across login + compute nodes.
3. `version_seqDB.json` file is required by gapseq find but was not created by
   `gapseq update-sequences`. Manual creation required (see SLURM script for format).
4. `.Renviron` requires absolute path for R_LIBS_USER (`~` and `$HOME` not expanded).
5. SLURM compute nodes do not have system R at /usr/bin/R — must `module load R/4.5.1`
   in job scripts.
6. Prodigal pre-translation was used (gapseq's pyrodigal not installed). The wrapper
   uses pre-translated .faa as input, bypassing gapseq's auto-translation step.


## Follow-up batch (May 13, 2026)

A follow-up batch of 9 organisms was processed after initial transfer revealed
my reconstructed minimal TSV had omitted them. These are well-known reference
strains across iron_metals, methane_metabolism, fermentation, magnetotaxis,
syntrophy, phototrophy, sulfur_metabolism, and carbon_fixation categories.

**Genomes processed**:

| Accession | Organism | Category |
|---|---|---|
| GCF_000007985.2 | Geobacter sulfurreducens PCA | iron_metals |
| GCF_000008325.1 | Methylococcus capsulatus Bath | methane_metabolism |
| GCF_000008765.1 | Clostridium acetobutylicum ATCC 824 | fermentation |
| GCF_000009985.1 | Paramagnetospirillum magneticum AMB-1 | magnetotaxis |
| GCF_000014725.1 | Syntrophomonas wolfei subsp wolfei Goettingen G311 | syntrophy |
| GCF_000018865.1 | Chloroflexus aurantiacus J-10-fl | phototrophy |
| GCF_000025485.1 | Allochromatium vinosum DSM 180 | sulfur_metabolism |
| GCF_000203855.3 | Lactiplantibacillus plantarum WCFS1 | fermentation |
| GCF_000247605.1 | Acetobacterium woodii DSM 1030 | carbon_fixation |

**SLURM job**: 229818 (array 1-9)
**Wall time**: ~10 minutes total (parallel execution on cluster nodes)
**Results**: 9 of 9 successful, all with 1933-line Pathways.tbl (Bacteria mode)
**Total cluster outputs now**: 144 (135 initial + 9 follow-up)

## Final Phase 5.0 processing status (post-followup)

- **Successfully processed**: 140 Phase 5.0 organisms
- **Audit corrections**: 4 (gids 9, 17, 26, 30 — gid=17 overlaps with Phase 5.0 list)
- **Permanently unavailable**: 2 (NCBI-suppressed: GCF_000012605.1, GCF_000315115.1)
- **Held-out**: 1 (bin.020 ST-3 Thiovulum sp. ES — never in Phase 5.0 reference set)
- **Phase 5.0 coverage**: 140/143 = 97.9%


## Transporter batch (May 13, 2026)

After initial transfer, discovered that the SLURM scripts only ran `gapseq find -p all`
and did not produce the `<accession>-Transporter.tbl` files that downstream
CultureForge logic requires (capability_detectors.py, predict_media.py both query
`genome_transporters` table; transporter evidence contributes to pathway confidence
scoring per the recipe composer).

A transport-only SLURM array (job 230026) was submitted for all 144 accessions to
produce the missing Transporter.tbl files using `gapseq find-transport -b 200 -K 8`.

**Key discovery**: `gapseq find-transport` does NOT accept the `-D` flag (custom
database directory) that `gapseq find` accepts. It reads from `~/gapseq/dat/seq/`
by default. The initial run failed in seconds due to this flag mismatch.

**Wall time**: ~5 minutes (find-transport is fast — small transporter reference DB)
**Results**: 144/144 successful
**Transporter substrates detected per genome**: 1065 to 6588+ (range)

After this batch, each cluster output directory contains the complete file set
that `loaders/gapseq_generic.py` expects:

- `<accession>-all-Pathways.tbl`
- `<accession>-all-Reactions.tbl`
- `<accession>-Transporter.tbl`

