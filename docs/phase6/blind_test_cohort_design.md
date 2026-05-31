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

---

## 13. Pre-assembly amendment 2026-05-30 — discovery-channel methodology

**Status:** Pre-assembly amendment. No cohort candidate has been
identified or recorded; no genome has been downloaded; no scoring or
inspection path has been run on any candidate. This amendment is
recorded BEFORE assembly begins, consistent with the §10
pre-registration commitment that the protocol cannot be altered
after assembly begins without an amendment record.

### 13.1 — Why this amendment exists

§5 names the discovery channels (Option 1: GenBank assembly query
for post-2026-01-01 MAGs; Option 2: PubMed / Google Scholar
literature search with four specified method-pattern queries) but
leaves two operational steps under-specified:

1. Option 1 §5 says "Pre-filter to ensure metabolic category
   coverage targets (§7)" but does not specify HOW the §7 categories
   map onto an NCBI Assembly query — NCBI's Assembly metadata has
   no "metabolic category" field.
2. Option 2 §5 says "Filter for papers where BOTH the MAG and
   cultivation conditions are clearly documented" but does not
   specify the threshold for "clearly documented."

A 2026-05-30 attempt to execute Option 2 via a generic web-search
channel surfaced the leakage risk: discovering candidates via
category-named queries ("methanogen cultivation 2025" etc.) lets
search visibility ∩ named category co-determine the candidate pool,
biasing toward headline-worthy organisms in the categories where
the literature is most mature. The criteria must drive discovery,
not filter its output. The attempt was halted before any candidate
was recorded; this amendment locks in faithful execution of §5's
discovery channels so that drift cannot recur silently.

### 13.2 — Option 1 operationalization: A3 (broad query + post-hoc binning)

**Discovery query.** Execute ONE broad NCBI `datasets summary
genome` query, with NO per-category pre-filter:

- `--assembly-source GenBank`
- `--released-after 2026-01-01`
- `--mag only` (the explicit MAG-only flag in `datasets` 16.x+)

Enumerate ALL hits to a stable JSON dump under
`data/validation/blind_test_batch1/` for reproducibility.

**Scope filter — environmental (non-host-associated) provenance,
applied uniformly across all §7 categories.** §5's Option 1
protocol bullet explicitly specifies "environmental samples"
alongside `assembly_type=MAG`. The pre-registration's broader
scope language confirms this is a real provenance boundary,
not an idle qualifier:

- §5 protocol bullet 2: "Filter for metagenomic origin
  (`assembly_type=MAG`, environmental samples)" — direct.
- §7 category targets — sulfate reduction, phototrophy,
  methanogenesis, methane metabolism, acetogenesis, anammox,
  ammonia oxidation, sulfur oxidation, lithoautotrophic iron,
  halophile, hyperthermophile, fermentative, extreme archaea,
  syntrophy, cable bacteria, ANME, microaerophile, comammox —
  are unambiguously environmental-biogeochemistry niches. NO
  host-associated metabolic guild (gut commensal SCFA-producer,
  oral spirochete, skin commensal, rumen fibrolytic, etc.)
  appears in any of the three tiers.
- §9 reviewer-defensibility table: "Cohort spans 3 quality
  bins, 8-10 metabolic categories, multiple environments" —
  the word *environments* (plural) is what the cohort
  describes itself as covering.
- CultureForge's broader project framing (`docs/CLAUDE.md`)
  is media prediction for "novel uncultured bacteria and
  archaea," with use cases (Hungate / serum-bottle anaerobic
  work, gradient tubes for microaerophiles, hyperthermophile
  mineral media, Hungate roll tubes for SRBs/methanogens) all
  in the environmental-cultivation paradigm. Host-associated
  MAGs (human gut/oral/skin, animal gut/rumen/skin) belong to
  a different cultivation paradigm (mucin-based media, gut
  bioreactors, defined microbial community work) the
  manuscript does not claim to serve.

**Decision (recorded 2026-05-30):** the blind-test cohort is
restricted to environmental (non-host-associated) MAG
provenance. The unfiltered reading (include host-associated
MAGs) is explicitly rejected as inconsistent with §5 / §7 /
§9 scope language and with the project's overall framing.

**Operational filter.** `datasets summary genome` does not
directly filter on BioSample MIxS environment fields, so the
scope filter is applied post-query against the BioSample
metadata of each hit. A hit is rejected if ANY of the
following hold (concrete ENVO IRIs and exact field syntax
pinned at execution time, recorded inline with the per-batch
verification doc):

- Linked BioSample has a populated `host`, `host_taxid`, or
  `host_scientific_name` field.
- Linked BioSample `env_broad_scale` / `env_local_scale` /
  `env_medium` MIxS term resolves under the ENVO branch for
  host-associated habitats (e.g. ENVO:00009003
  "animal-associated habitat", ENVO:01000219
  "human-associated habitat", ENVO subterms for
  gut/oral/skin/rumen environments).
- Linked BioSample `isolation_source` text matches
  host-tissue terms (gut, oral cavity, skin, sputum, feces,
  intestine, rumen, mucosa, biofilm-on-host).

**Uniform across categories, not category pre-filter.** This
filter is applied IDENTICALLY across all §7 categories. It
draws ONE provenance boundary that every candidate crosses or
fails on the same terms; it does NOT pre-bias *which*
metabolic categories survive (no category is held to a
stricter standard than another). As such, it does NOT violate
the A3 leakage-prevention guarantee — it is a scope boundary,
not a tilted lens.

**Interaction with the shortfall rule.** If a §7 category
appears unfillable AFTER both the scope filter and the
mechanical §3/§4 filter, the shortfall rule still governs:
document the shortfall, do NOT relax scope to host-associated
candidates to backfill. The shortfall in a category, under
this scope boundary and this deposit window, is the
information — the cohort honestly reflects what
environmental-MAG availability looked like, rather than
silently widening to organisms the method's working range
does not claim.

**Mechanical filtering.** Apply the mechanical §3 / §4 checks to
the enumerated set:

- accession not present in `cultureforge.db.genomes`
- accession source organism not represented in any
  `data/diagnostic_markers/*_refs.fasta` (taxonomic-name
  pre-check; the sequence-level diamond/blast check per §6 step
  4 follows after download)
- explicitly NOT Thiovulum / `GCA_000276965.1` per the orphan
  finding recorded 2026-05-30 in `docs/PHASE_6_BACKLOG.md`

**Post-hoc category binning.** Bin the surviving hits by inferred
§7 metabolic category using taxonomy + BioSample environment
metadata available in the NCBI summary record. Sample from the
binned survivors to fill the §7 per-category quotas for the
batch.

**Shortfall rule (the leakage-prevention guarantee).** If the
broad query does NOT yield enough survivors to fill a §7 quota
in any category — especially the weak/limitation categories
(extreme archaea, syntrophy, cable bacteria, ANME, microaerophile,
comammox) where post-2026-01-01 deposits are likely sparse —
that category MAY come up short. Under NO circumstance does a
shortfall trigger a category-targeted re-search (e.g. "cable
bacteria MAG deposited 2026"), because targeted searching of a
sparse category re-introduces precisely the visibility bias this
amendment is meant to eliminate, and would do so in the categories
where it would most flatter the method (low-deposit categories
where any cherry-picked hit dominates the small-sample average).

If a category appears genuinely unfillable from the broad query,
assembly STOPS and the shortfall is documented inline with the
batch verification record (`<artifact-dir>/blind_batch1_verification.md`
per §6). A case-by-case documented A2-style habitat-proxy
fallback (restrict by BioSample `env_broad_scale` / `env_local_scale`
/ `env_medium` fields for the missing category only) MAY be
considered then, with the fallback decision recorded as its own
narrower per-category amendment — never applied silently and
never applied as a default.

### 13.3 — Option 2 operationalization: registered PubMed queries + human-judgment threshold

**Discovery queries.** Execute the FOUR query strings already
specified in §5 — verbatim, no broader paraphrases, no
category-named variants — against PubMed via NCBI E-utilities
(`esearch` / `efetch`). The four strings, reproduced from §5:

- `"MAG-guided cultivation"`
- `"successfully cultured" AND "metagenome-assembled genome"`
- `"isolation following metagenomic analysis"`
- `"axenic culture" AND "previously uncultured"`

Date window: 2024-01-01 to present (per §5's "papers 2024-2026").

**Per-hit processing.** Dedup the merged hit list by PMID. For
each unique hit, retrieve the abstract + parseable accession
candidates via `efetch` (inline `GCA_…` / `GCF_…` patterns in the
abstract or the data-availability statement, when present).

**Human-judgment documentation threshold.** Surface the resulting
deduped paper list to the manuscript author (George) for the
"clearly documented MAG + cultivation conditions" judgment. This
judgment is NOT made unilaterally by Claude. Claude's role is
limited to executing the queries, deduping, and surfacing
abstracts + parseable accessions; the inclusion call for each
paper is George's.

**Verify-or-fall-back on cultivation conditions.** For any paper
accepted into Option 2, full-text retrieval may then be attempted
to extract cultivation conditions for the manifest. If the
cultivation conditions cannot be confirmed from retrievable text
(paywalled journal, abstract insufficient, supplementary not
public), record `cultivation_conditions = "unverified — source
not retrievable"` in the manifest. Do NOT infer conditions from
the abstract alone or extrapolate from related literature.

### 13.4 — What this amendment does NOT change

- §3 inclusion criteria, §4 exclusion criteria, §6 per-candidate
  verification protocol, §7 category targets, §8 scoring
  methodology, and §10 pre-registration commitment are unchanged.
- The 30-40 cohort target and ~50/50 Option 1 / Option 2 mix are
  unchanged.
- The held-out threshold (>95% ANI to any dev cohort genome) is
  unchanged. The dev-cohort comparison reference standup completed
  2026-05-30 — persisted 168-genome sourmash sketch at
  `data/validation/dev_cohort_sketches_k31_s1000.zip` (k=31,
  scaled=1000) with provenance manifest at
  `data/validation/dev_cohort_fasta_manifest.tsv` — is the
  reference set for the held-out check.
- The "no peeking" rule is unchanged; no `cultureforge.py inspect`
  or scoring path runs on any blind-test candidate prior to
  cohort lock.

### 13.5 — State of the cohort at amendment time

- **Assembly status:** NOT begun. No candidate identified, no
  candidate recorded, no genome downloaded, no scoring run.
- **Repo-side artifacts to date** (all doc/data-setup, no scoring):
  - Dev-cohort comparison reference (manifest + sketch zip) under
    `data/validation/`
  - `.gitignore` rule adding `data/blind_test/` (untracked
    storage for downloaded candidate FASTAs)
  - Backlog entries appended to `docs/PHASE_6_BACKLOG.md` for
    genome-storage fragility and the burned
    `data/sentinel/blind_test_organism_001/` Thiovulum orphan
  - This amendment (§13)

### 13.6 — Authority

§10 of this document explicitly permits amendments before assembly
begins ("The protocol cannot be altered after assembly begins
without an amendment record"). This amendment is recorded before
assembly begins and is itself the amendment record for the
discovery-channel operationalization specified above.

**Drafted:** 2026-05-30 (during blind-test cohort first-batch
session, after Task 2.0 dev-cohort reference build and before
Task 2.1 candidate identification).
**Trigger:** generic web-search drift during a Task 2.1 attempt
was flagged by the manuscript author before any candidate was
recorded; the four drift-affected web-search results have been
quarantined (not used as candidate input) and Task 2.1 will
resume only after this amendment is reviewed and committed.
