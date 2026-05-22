# Blind-Test Cohort Design

**Date:** 2026-05-17
**Repo HEAD:** e3c4123 (post-Phase 6 A1/A4/C1)
**Status:** Design document — cohort assembly is a subsequent task

## 1. Purpose

This document specifies the design of a blind-test cohort for validating CultureForge's performance on MAGs not seen during framework development. It anchors the manuscript's central claim of broad applicability to diverse MAGs, targeting an open methodology journal (PLOS Comp Bio / Bioinformatics / Microbiome tier).

This document is the DESIGN. Cohort assembly is a downstream task, documented separately.

## 2. The manuscript claim being validated

[Working draft — to be refined during D2 manuscript outline work]

CultureForge predicts cultivation media for novel metagenome-assembled genomes (MAGs) directly from genome sequence, without requiring prior cultivation history, curated trait annotations, or phylogenetic proximity to cultured isolates. It is the first such tool to handle the genome-only-no-curation niche.

The blind-test cohort must provide evidence for:
- The tool generalizes to MAGs not used during development
- Performance varies by metabolic category in a characterized, documented way
- The tool's working range and limitations are honestly bounded

The cohort does NOT need to support a uniform high-performance claim (>90% on every MAG). Performance breakdown by category is the methodologically defensible framing.

## 3. Inclusion criteria

A MAG is eligible for the blind-test cohort if ALL of the following hold:

- **Provenance:** MAG metadata, source paper, and sequencing accession publicly available
- **Quality:** CheckM2 completeness ≥70%, contamination ≤5% (preferred ≥90% / ≤3%)
- **Taxonomic resolution:** Resolvable to at least Family level (Genus/Species preferred)
- **Deposit date:** GenBank/JGI public deposit after 2026-01-01 (Option 1 source) OR cultivation-pair criterion met (Option 2 source — see §5)
- **Non-overlap with dev cohort:** Not in `genomes` table of `cultureforge.db` (mechanical check)
- **Non-overlap with reference sets:** Genome accession does not match any sequence in any `data/diagnostic_markers/*_refs.fasta` (mechanical check)

## 4. Exclusion criteria

A MAG is excluded if ANY of the following hold:

- Used during framework development (in 168-organism dev cohort)
- Contributed sequences to any marker DB reference set
- Tagged "redundant" with a dev cohort organism (>95% ANI to any dev cohort genome)
- MAG quality below thresholds in §3
- Cultivation conditions ambiguous or contested in the source literature (Option 2 only)

## 5. Source strategies

### Option 1: Recent post-development GenBank/JGI MAGs (target 15-20 organisms)

**Protocol:**
- Query GenBank assembly database for MAGs deposited after 2026-01-01
- Filter for metagenomic origin (`assembly_type=MAG`, environmental samples)
- Apply quality and exclusion criteria (§3, §4)
- Pre-filter to ensure metabolic category coverage targets (§7)

**Use case:** Demonstrates generalization to organisms with no cultivation history. Cannot be V12-scored (no reference media). Audit-style biological-plausibility scoring only.

### Option 2: Cultivation-pair MAGs from recent papers (target 15-20 organisms)

**Protocol:**
- Literature search PubMed and Google Scholar for papers 2024-2026 matching patterns like:
  - "MAG-guided cultivation"
  - "successfully cultured" + "metagenome-assembled genome"
  - "isolation following metagenomic analysis"
  - "axenic culture" + "previously uncultured"
- Filter for papers where BOTH the MAG and cultivation conditions are clearly documented
- Extract: MAG accession, predicted/inferred conditions, actually-used cultivation medium

**Use case:** Provides ground-truth comparison. Eligible for both audit-style and V12-style scoring. Higher manuscript value because the prediction-vs-reality comparison is the stronger evidence.

### Mix target

Final cohort: 30-40 organisms total, weighted ~50/50 between Options 1 and 2 in initial assembly. Allow adjustment based on actual availability (Option 2 may be harder to source 20 of; under-supply backfilled from Option 1).

## 6. Quality verification protocol

For each candidate organism, before inclusion in the cohort:

1. Download genome FASTA from NCBI/JGI
2. Run CheckM2 (or use published quality scores if available and CheckM2-derived)
3. Verify deposit date >2026-01-01 from NCBI Assembly metadata
4. Run reference-set non-overlap check (sequence-level diamond/blast against all `*_refs.fasta` — report top hits per genome, flag any >95% identity matches)
5. Verify taxonomic assignment via GTDB-Tk (or use published lineage with provenance check)
6. For Option 2: verify cultivation paper, extract conditions

Output: per-organism row in `docs/phase6/blind_test_cohort.tsv` with all metadata, links, and verification results.

## 7. Metabolic category coverage targets

Target distribution across 30-40 organisms:

**Strong categories (5-7 organisms total):** dev-cohort PASS rate ≥80%
- Sulfate reduction, phototrophy, methanogenesis, methane metabolism, acetogenesis
- Purpose: demonstrate generalization in well-handled niches

**Mid-strength categories (15-20 organisms total):** dev-cohort PASS rate 50-80%
- Anammox, ammonia oxidation, sulfur oxidation, lithoautotrophic iron, halophile, hyperthermophile, fermentative
- Purpose: characterize the tool's main working range

**Weak/limitation categories (5-10 organisms total):** dev-cohort PASS rate <50%
- Extreme archaea, syntrophy, cable bacteria, ANME, microaerophile, comammox
- Purpose: honest documentation of where the tool struggles

Exact organism-to-category assignment determined during cohort assembly based on actual availability.

## 8. Scoring methodology

**Layer 1 — Biological plausibility audit (all 30-40 organisms):**
- For each organism, run `python3 cultureforge.py inspect <gid> --section capabilities` and `--section recipe`
- Score against expected biology (PASS / PARTIAL / FAIL with rationale)
- This mirrors the dev-cohort predictions audit methodology

**Layer 2 — Recipe agreement scoring (Option 2 organisms only, ~15-20 organisms):**
- Compare predicted recipe to actually-used cultivation conditions from source paper
- Score 0-100% using the V12 methodology (recipe component matching)
- Report per-organism and cohort-level aggregates

**Reporting:**
- Overall PASS / PARTIAL / FAIL rate (Layer 1)
- Per-category breakdown (Layer 1)
- Mean and median agreement (Layer 2, where applicable)
- Per-organism detail in supplementary materials

## 9. Reviewer-defensibility considerations

Anticipated reviewer objections and how the protocol addresses each:

| Objection | Protocol response |
|-----------|-------------------|
| "Tuned on the test set you built the framework on" | Blind-test cohort is post-development deposit + cultivation-pair MAGs; non-overlap mechanically verified |
| "Cherry-picked organisms favorable to the tool" | Selection by deposit date and literature search, not by organism identity; full inclusion/exclusion criteria documented; protocol pre-registered (this document) |
| "Cohort too small for statistical claims" | Per-category breakdown rather than single-number headline; cohort size justified by methodology-journal expectations |
| "What about real MAG quality (CheckM2 variability)?" | Quality thresholds documented; subset analysis at higher quality thresholds reported |
| "How representative is this of 'all MAGs'?" | Cohort spans 3 quality bins, 8-10 metabolic categories, multiple environments; explicit documentation of where it does and doesn't cover |

## 10. Pre-registration commitment

This document is pre-registered in git history before cohort assembly begins. The protocol cannot be altered after assembly begins without an amendment record. This is the methodological backbone of the manuscript's defensibility.

## 11. Deliverables

- `docs/phase6/blind_test_cohort_design.md` (this document)
- `docs/phase6/blind_test_cohort.tsv` (assembled cohort, separate deliverable)
- `docs/phase6/blind_test_results.md` (after running CultureForge on the cohort)
- Source paper bibliography for Option 2 organisms
- Supplementary materials for manuscript

## 12. Open questions for next session

- Final journal target (PLOS Comp Bio, Bioinformatics, Microbiome, or other)
- Whether to include any non-MAG isolate genomes (likely no — MAGs only matches the niche claim)
- Whether to do per-organism inspection or batch processing for blind-test scoring
- How to handle Option 2 organisms where cultivation conditions are described loosely (e.g., "standard rich medium" — V12 scoring unreliable)
