# Phase 5.0 — Candidate Genome List (For User Review)

**Status:** Draft awaiting **Checkpoint 1** review.
**File:** `data/release/phase5_0_genome_candidates.tsv` (47 candidates across 11 categories, plus 1 explicitly held-out marker row).

---

## What this is

A stratified candidate list for Phase 5.0 gap discovery. Each entry covers a specific metabolism category currently under-tested in CultureForge's 26-genome test set + 4-sentinel set. The point of Phase 5.0 is to process all of these through `cultureforge.py process-batch`, score predictions with the Phase 5.0 evaluation rubric, and catalog every failure mode found.

## Important verification requirement

**I (Claude Code) compiled the accessions from prior knowledge.** Several may be wrong. Before any downloads:

- Every `GCF_*.X` / `GCA_*.X` accession must be verified at https://www.ncbi.nlm.nih.gov/datasets/genome/ (search the organism name, confirm the accession matches the expected strain, copy the canonical accession back into the TSV).
- Every DSMZ medium number must be verified at https://mediadive.dsmz.de/.
- Every BacDive ID must be verified at https://bacdive.dsmz.de/.

Known issues I introduced:
- `Desulfobacter hydrogenophilus AcRS1` row marked `(VERIFY — listed accession was a memory error)`; correct accession needs lookup.
- `Halorubrum lacusprofundi DSM 5036` listed as `GCF_000022205.1` — this MAY be correct but please verify (was duplicated against the Desulfobacter row).
- Some Roseobacter / Pelagibacter / Halomonas accessions in the marine and halophile sections may be approximations.

Suggested workflow during Checkpoint 1 review:
1. Open the TSV, search each accession at NCBI Datasets, paste the canonical accession into the TSV.
2. Add or remove rows based on your research interests (the prompt explicitly invites adding candidates relevant to your work).
3. For organisms where you have personal cultivation experience, double-check the published-medium row entries.
4. Save the reviewed result as `data/release/phase5_0_genome_list_final.tsv` — that becomes the actual processing target.

## Structure

The TSV has 14 columns:

| Column | Description |
|---|---|
| category | Stratified bucket (sulfur_metabolism, nitrogen_metabolism, fermentation, etc.) |
| accession | NCBI assembly accession (GCA/GCF) — canonical, verifiable |
| organism | Strain name including subspecies/strain designation |
| file_path | Where to place the downloaded FASTA after download |
| biomass | gapseq biomass template (Gram_neg / Gram_pos / Archaea) |
| dsmz_or_ref | DSMZ medium number, BacDive ID, or paper citation for cultivation conditions |
| temp_c | Optimum growth temperature (°C) |
| ph | Optimum pH |
| salinity_pct | Optimum salinity (% w/v NaCl) |
| atmosphere | aerobic / anaerobic / microaerobic / methane-air / etc. |
| electron_donor | What the organism oxidizes for energy |
| electron_acceptor | What it reduces (or "none" for fermentation) |
| carbon_source | Where carbon comes from |
| notes | Specialty info; capability gaps the candidate fills; biomass override hints |

## Held-out genome — do NOT include

Row 1 of the TSV is a **sentinel marker** for the user's bin.020 ST-3 (unpublished *Thiovulum* sp.). It has `accession = (unpublished)` to make it impossible to download accidentally and to make Phase 5.0 reference work loudly skip it. The reason: bin.020 ST-3 is the user's generalization-test genome — it must not contribute reference sequences to any future marker curation. The Phase 5.0 batch processor reads the `accession` column and would refuse to process anything without a real accession.

## Distribution by category

| Category | Count | Rationale |
|---|---:|---|
| sulfur_metabolism | 8 | Highest priority: Phase 4.1 blind test on Thiovulum identified Sqr as a missing marker. Need diverse sulfur-cycling organisms (chemolithoautotrophic SOX, microaerophilic Sqr-pathway, hyperthermophilic Aquificales rTCA, archaeal SRB) |
| nitrogen_metabolism | 8 | Multiple gaps: AOA (Thaumarchaeota amoA — distinct from bacterial AOB), comammox (LIMITATIONS A.2 deferred), additional anammox isolates beyond Scalindua, N2 fixers (alternative nitrogenases — LIMITATIONS B.1) |
| fermentation | 6 | Phase 1 fermentation detection is broad (LIMITATIONS B.2). Stickland-pattern fermenters not represented; rumen / gut fermenters absent. |
| phototrophy | 4 | LIMITATIONS B.5 phototrophy gaps. Cyanobacteria (oxygenic phototrophy) entirely missing from test set. Heliobacteria represent a deferred Gram-positive phototroph case. |
| marine_user_interest | 4 | User research interest; tests marine ASW base composition (LIMITATIONS D.X candidate); magnetotactic bacteria are a niche case. |
| iron_metals | 4 | Phase 1.5n LIMITATIONS A.4 documented neutrophilic Fe oxidation as a gap (Mariprofundus, Gallionella). Shewanella as second metal reducer beyond Geobacter. |
| extreme_archaea | 4 | Hyperthermophilic Thermococcales + sulfur-cycling archaea — different from Methanocaldococcus and Sulfolobus. |
| sulfate_reduction | 3 | Test set has only Nitratidesulfovibrio (incomplete oxidizer). Need complete oxidizer (Desulfobacter), specialty alkane oxidizer (Desulfococcus). |
| methane_metabolism | 3 | Hyperthermophilic methanogen, gut methanogen, plus methylotroph (different from methanotroph; LIMITATIONS gap) |
| halophile_alkaliphile | 3 | Test set has Halobacterium only. Polyextremophile (Natranaerobius — hot + alkaline + halophilic simultaneously) is a stress test. |
| acetogenesis | 1 | Test set has Acetobacterium only. Sporomusa is a second acetogen with different characteristics. |

**Total: 47 candidates** (excluding the held-out user genome row).

## What this validates / discovers

If Phase 5.0 confirms the gap inventory the prompt anticipates, we expect to find:

- **Category A (missing marker)** failures clustered in sulfur metabolism (Sqr, aclA/B for rTCA), nitrogen metabolism (archaeal amoA distinct from bacterial; comammox-specific markers), and methylotrophy (mxaF / xoxF distinct from canonical methanotroph pmoA).
- **Category D (recipe composer routing)** failures clustered in marine cultivation (NaCl-baseline vs ASW), microaerophilic gradient cultivation (recipe always defaults to 100% air or 100% N2), and oxygenic phototrophy (no light-cultivation routing).
- **Category F (pathway not covered)** failures from comammox, methylotrophy, iron-oxidation neutrophilic, oxygenic phototrophy, alternative nitrogenases.
- **Category E (GenomeSPOT limitation)** failures from oxygen "tolerant" being too coarse (covers aerobic + microaerophilic + facultative), salinity threshold for halophile-mode triggering, archaeal predictions known to be unreliable.

The actual frequencies will be empirical, not estimated.

## Next steps after Checkpoint 1 approval

1. Save the reviewed list as `data/release/phase5_0_genome_list_final.tsv`.
2. Run `scripts/phase5_0_download_genomes.sh` (to be written next) to fetch all genomes via NCBI Datasets.
3. Update `data/diagnostic_markers/REFERENCE_CURATION.md` with the test-set exclusion list expanded to include all Phase 5.0 entries (Task 3.3).
4. Run `python3 cultureforge.py process-batch --list data/release/phase5_0_genome_list_final.tsv` (Task 4 — user runs in their terminal because of conda/runtime requirements; expected wall time 2-4 weeks).

These steps are gated on Checkpoint 1 — please review the list and either approve as-is, mark corrections needed, or replace specific candidates.
