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

---

## 14. Pre-assembly amendment 2026-05-31 — Option 1 scope-filter operational refinements

**Status:** Pre-assembly amendment. Assembly status remains NOT begun. No
cohort candidate has been identified or recorded; no genome has been
downloaded; no scoring or inspection path has been run on any
candidate. This amendment is recorded BEFORE assembly begins,
consistent with §10 and following the same authority basis as §13.

### 14.1 — Why this amendment exists

§13 (2026-05-30) operationalized Option 1 as a broad NCBI `datasets`
MAG query with a three-clause post-query scope filter (host field
populated, env_* host-associated, isolation_source host-tissue) plus
the §3/§4 mechanical filter. The amendment text explicitly noted
that the filter would be eyeballed on first contact with real
BioSample data — depositor metadata in MIxS fields is inconsistent,
and a filter written from the ontology cannot be trusted blind.

The broad query was executed 2026-05-31 (150,024 hits total —
141,783 Bacteria + 8,241 Archaea). Eyeballing the kept/rejected
samples surfaced three operational gaps the original three-clause
filter did not handle correctly. This amendment records the three
refinements that were adopted in response, frames the direction of
change of each one, and shows that they leave the §13 scope
boundary itself unchanged.

The complete matching logic and term lists for all four scope
clauses, the positive-signal gate, and the Clause 1 env-vocab
exemption are encoded in `scripts/blind_test/filter_option1.py` —
the single source of truth for the filter. This amendment and the
filter script land in the same commit; the amendment text and the
filter implementation it references are locked together, with no
follow-up edit required to cross-reference them.

### 14.2 — Refinement A: Clause 4 — invertebrate-host rejection (context-aware)

**Gap.** The §13.2 three-clause filter enumerated mammalian and
vertebrate host-tissue terms but did NOT cover invertebrate hosts.
First-pass eyeball found 517 kept candidates whose `isolation_source`
read `coral metagenome`, `sponge metagenome`, `oyster metagenome`,
etc. — host-associated MAGs of non-vertebrate animals slipping
through.

**Refinement.** A fourth clause is added: any invertebrate-host
token (coral, sponge, oyster, bivalve, crustacean, echinoderm,
gastropod, polychaete, insect, termite, etc.) appearing in
`isolation_source` or any `env_*` field is evaluated context-aware.
A token in HOST context — followed by host-suffix terms like
`metagenome`, `microbiome`, `mucus`, `tissue`, `gut`, or preceded by
host-prefix terms like `associated with`, `isolated from`,
`endosymbiont of` — triggers rejection. A token in ENV context —
followed by environmental qualifiers like `reef sediment`, `reef
seawater`, `reef biome`, or preceded by `near`, `adjacent to` —
is preserved. A bare token without qualifier defaults to HOST
context (conservative — ambiguous cases reject).

**Representative case.** `isolation_source='coral metagenome'`
rejects; `env_broad_scale='coral reef'` (e.g. `Alteromonas
macleodii` reef-seawater MAGs) keeps.

**Effect (2026-05-31 run).** 516 records rejected on this clause
(sponge 362, coral 124, bivalve 14, oyster 10, crustacean 5,
ant 1). 111 reef-ecosystem MAGs preserved. Zero ENV-context false
rejects and zero HOST-context slip-throughs into KEEP — verified
by per-class eyeball.

**Direction.** STRICTER than §13 v1 — closes an enumeration gap
relative to the §13.2 scope boundary that already excluded
non-host-associated MAG provenance. Does not move the boundary.

Complete token list and pattern definitions in
`scripts/blind_test/filter_option1.py`
(`INVERTEBRATE_TOKENS`, `HOST_CONTEXT_SUFFIXES`,
`HOST_CONTEXT_PREFIXES`, `ENV_CONTEXT_SUFFIXES`,
`ENV_CONTEXT_PREFIXES`, `invertebrate_host_context`).

### 14.3 — Refinement B: positive-environmental-signal gate

**Gap.** The §13.2 three-clause filter was structured as "reject
if any host signal is present" → "keep otherwise." This implicit
"keep unless rejected" default meant that 10,379 MAGs with all
env_* fields AND `isolation_source` blank/missing were being kept
— not because positive evidence placed them in an environmental
habitat, but because absence of metadata gave nothing for the host
clauses to trigger on. The same mechanism that would silently admit
a host-associated MAG deposited with sparse metadata.

**Refinement.** The scope filter is gated by an explicit
positive-environmental-signal requirement applied after the four
rejection clauses. KEEP requires at least one of: a substantively
populated env_* MIxS field; an `isolation_source` matching an
environmental-habitat keyword (geological substrate, water body,
extreme habitat, biome, engineered environment, microbial community,
or ENVO IRI); or — per Refinement C — a `host` / `host_description`
value that passes the env-substrate-only test.

**Representative case.** `Aequorivita vladivostokensis` MAGs with
all env_* and `isolation_source` blank are now rejected as
`no_positive_env_signal` (organism name suggests marine origin but
the depositor recorded no positive signal); cases like `Acetobacteraceae
bacterium` with `isolation_source='soil from crater rim of Mt. Zao'`
keep on the soil keyword.

**Effect (2026-05-31 run).** 14,225 records rejected by this gate
alone — provenance-unverified MAGs that v1 admitted on
absence-of-rejection grounds.

**Direction.** STRICTER than §13 v1 — converts §13.2's scope test
from "no host signal detected" (negative) to "positive env signal
present" (affirmative). The §6 verification protocol establishes
quality and taxonomy after download but does NOT re-establish
provenance, so the positive-signal requirement must hold at the
candidate-identification step.

Complete env-habitat keyword list and gate logic in
`scripts/blind_test/filter_option1.py`
(`ENV_HABITAT_KEYWORDS`, `KW_RE`, `has_positive_env_signal`).

### 14.4 — Refinement C: Clause 1 env-host-value exemption

**Gap.** Clause 1 of §13.2 was written assuming MIxS conformance:
a populated `host` field always names a biological host. Eyeball
found a coherent hydraulically-fractured-shale fluid microbiome
study (~975 MAGs, GCA_0551*/0554* series) whose depositor populated
MIxS `host` with `Subsurface shale` — a geological substrate, not
a biological organism. Strict Clause 1 was rejecting these on
depositor MIxS misuse, against the §13.2 scope intent.

**Refinement.** Clause 1 is split. A **strict pass** rejects on any
populated value in `host_taxid`, `host_scientific_name`,
`host_common_name`, `host_disease`, `host_age`, `host_sex`,
`host_body_site`, `host_subject_id`, or `host_tissue_sampled` — these
fields unambiguously signal a biological host. A **lenient pass**
exempts a populated `host` or `host_description` value if it matches
a conservative env-substrate vocabulary (geological substrates,
waters, ice, salts, engineered environment, ENVO IRIs) AND contains
NO biological-host indicator (vertebrate/invertebrate common names,
plant tissues, common crop names, host-tissue tokens, anything
organism-like). Exempted values ALSO satisfy Refinement B's
positive-signal gate.

**Representative case.** `host='Subsurface shale'` exempts and keeps;
`host='Homo sapiens'`, `host='soybean rhizosphere soil'`, or
`host='Antarctic seal'` rejects (the first on common animal name;
the second on `soybean` + `rhizosphere`; the third on `seal`,
recognizing that "Antarctic" alone is a regional descriptor not in
the env-substrate vocab).

**Conservatism principle.** This is a relief valve for depositor
MIxS misuse, not a permissive reading of Clause 1. The user-confirmed
line: "I'd rather lose a few real environmental MAGs than punch a
hole in it." Per that line, regional descriptors that are not
substrate-specific (`Antarctic`, `Arctic`, `North Atlantic`) are
deliberately NOT in the env-substrate vocab; 19 records with
`host='Antarctic …'` correctly remained rejected.

**Effect (2026-05-31 run).** 975 records exempted from Clause 1.
All 975 KEPT after full v3 evaluation (the coupled positive-signal
extension was necessary — without it, blank env_* and a non-
keyword-matched iso would have re-rejected them at the gate). 6 of
the 975 were subsequently dropped by §3/§4 mechanical filter on
`taxid_in_marker_refs` (correctly). Per-record eyeball of 30
recovered samples confirmed a single coherent fracking-fluid study,
anaerobic acetogens and hydrocarbon-degraders, zero host slippage.

**Direction.** CORRECTIVE relative to §13 v1 — recovers candidates
the §13.2 scope language affirms are in scope (subsurface
geological MAGs) but that strict literal Clause 1 was dropping on
depositor MIxS field misuse. The recovered candidates remain
subject to every other clause and gate.

Complete env-substrate vocab, biological-host indicator list, and
exemption logic in `scripts/blind_test/filter_option1.py`
(`ENV_HOST_VALUE_VOCAB`, `BIO_HOST_INDICATORS`,
`host_value_is_env_only`, `host_field_populated`).

### 14.5 — Direction-of-change and the scope-boundary claim

Two of the three refinements (A and B) are STRICTER than §13 v1:

- **A** closes an enumeration gap in the §13.2 host-tissue list
  (vertebrate-only) so that invertebrate-host MAGs — which the
  §13.2 scope decision excludes by intent — are actually excluded
  in execution.
- **B** changes the implicit default from "keep unless rejected"
  to "keep only if demonstrably environmental" — converting the
  §13.2 scope language from a negative test (no host signal) to
  an affirmative test (positive env signal), without changing the
  scope itself.

One of the three (C) is CORRECTIVE relative to §13 v1:

- **C** recovers MAGs the strict-MIxS reading of Clause 1 dropped
  due to depositor field misuse, while preserving conservative
  protections against punching a hole in Clause 1 (env-substrate
  vocab only, bio-host indicator denies the exemption, ambiguous
  values stay rejected, strict pass on the other host_* fields
  unchanged).

**The scope boundary itself — "environmental (non-host-associated)
MAG provenance, applied uniformly across all §7 categories" — is
unchanged.** No category is held to a stricter standard than any
other; the refinements are applied identically across all §7
tiers. Each refinement was adopted only after per-class eyeball
samples confirmed it sharpened toward the §13.2 intent rather
than tilting the lens for any category. The uniform-across-
categories guarantee from §13.2 is preserved.

### 14.6 — Final funnel and category coverage

**Funnel (2026-05-31 broad query + v3 filter):**

| Stage | Count | % of raw |
|---|---:|---:|
| Raw hits (Bacteria + Archaea) | 150,024 | 100.0% |
| After scope filter v3 (4 clauses + positive-signal gate + Clause 1 exemption) | 89,687 | 59.8% |
| After mechanical §3/§4 filter | 89,665 | 59.8% |

Mechanical rejections: 22 records, all on `taxid_in_marker_refs`
(§4 exclusion; the candidate's source organism is represented in
one of the 35 `data/diagnostic_markers/*_refs.fasta` /
`data/hydrogenase/hydrogenase_refs.fasta` files used to train
metabolic markers). Zero overlap with the 168-genome dev cohort
(expected: dev cohort predates 2026-01-01); zero hits on the
Thiovulum / `GCA_000276965.1` exclusion (also pre-2026-01-01).

**Scope rejection by reason label (v3):**

| Label | n |
|---|---:|
| `env_host_token` (Clause 2) | 24,475 |
| `host_field` (Clause 1, strict + non-exempted lenient) | 17,864 |
| `no_positive_env_signal` (Refinement B gate) | 14,225 |
| `iso_host_tissue` (Clause 3) | 3,257 |
| `invertebrate_host` (Clause 4 / Refinement A) | 516 |

**Reproducibility artifacts** (persisted under
`data/validation/blind_test_batch1/`; untracked per `.gitignore`
addition recorded in §13.5):

- `broad_query_bacteria.jsonl` — raw bacterial MAG records
- `broad_query_archaea.jsonl` — raw archaeal MAG records
- `scope_filter_kept_v3.jsonl` — post-scope keepers
- `scope_filter_rejected_v3.jsonl` — rejection records with
  reason label, triggering field, and matched token
- `mechanical_filter_rejected_v3.tsv` — mechanical drops
- `survivors_v3.tsv` — final survivors with category tags
- `category_bins_v3.tsv` — per-category counts

### 14.7 — Documented batch-1 shortfalls

Post-hoc binning of 89,665 survivors against the §7 category list
shows 92% UNBINNED — the binning is name-based (organism name +
env-text regex), and most MAGs carry generic family/order-level
names that do not name a metabolic guild. True category coverage
is higher than the bin counts; the bins surface the easiest hits,
not the ceiling.

Three §7 categories register at-or-near zero in the bin counter
for batch 1 and are recorded here as documented under-fills under
the §13.2 shortfall rule:

| Category | Tier | Bin count |
|---|---|---:|
| comammox | weak | 0 |
| cable bacteria | weak | 2 |

ANME registered 8 in v3 (improved from 2 in v2 with the
Refinement-C recovery — ANME-adjacent guilds appear in subsurface
shale environments) and is not flagged as a shortfall at this
batch.

**Action per §13.2 shortfall rule.** These shortfalls are carried
forward to subsequent batches in the multi-batch cohort
assembly. No category-targeted backfill, no scope relaxation, no
A2 habitat-proxy fallback is invoked at this batch. A2 fallback
is revisited only if a category remains empty near cohort
completion across multiple batches — a deliberate "genuinely
unfillable" decision then, not a first-batch patch.

### 14.8 — What this amendment does NOT change

- §3 inclusion criteria, §4 exclusion criteria, §6 per-candidate
  verification protocol, §7 category targets, §8 scoring
  methodology, §9 reviewer-defensibility frame, §10
  pre-registration commitment — all unchanged.
- §13 scope boundary ("environmental, non-host-associated MAG
  provenance, applied uniformly across all §7 categories") —
  unchanged.
- §13.2 discovery query (broad NCBI `datasets summary genome`
  with `--assembly-source GenBank --released-after 2026-01-01
  --mag only`) — unchanged.
- §13.2 mechanical filter (not in `cultureforge.db.genomes`, not
  in marker `*_refs.fasta`, not Thiovulum / `GCA_000276965.1`) —
  unchanged.
- §13.2 shortfall rule (no category-targeted backfill, A2 fallback
  by case only) — unchanged.
- §13.3 Option 2 operationalization (four registered PubMed
  queries via E-utilities, human-judgment documentation
  threshold, verify-or-fall-back on cultivation conditions) —
  unchanged. Option 2 has not begun.
- 30–40 cohort target, ~50/50 Option 1 / Option 2 mix, >95% ANI
  held-out threshold, dev-cohort sourmash sketch reference at
  `data/validation/dev_cohort_sketches_k31_s1000.zip` — all
  unchanged.
- No-peeking rule unchanged; no `cultureforge.py inspect` or
  scoring path has run on any blind-test candidate.

### 14.9 — State of the cohort at amendment time

- **Assembly status:** NOT begun. No candidate identified, no
  candidate recorded, no genome downloaded, no scoring/inspect
  run.
- **Reproducibility:** the 2026-05-31 v3 broad-query results are
  persisted under `data/validation/blind_test_batch1/` (untracked
  per §13.5 `.gitignore` rule for `data/blind_test/`; the
  parallel `data/validation/blind_test_batch1/` artifacts are
  intentionally also untracked at this stage and will be packaged
  for repro at lock time per §13.5 carry-forward).
- **Open repo-side artifacts** (all doc/data-setup, no scoring):
  - Dev-cohort comparison reference (manifest + sketch zip) under
    `data/validation/` (untracked)
  - `.gitignore` rule for `data/blind_test/` (uncommitted, carried
    for the eventual Task 4 batch commit)
  - Backlog entries appended to `docs/PHASE_6_BACKLOG.md`
    (uncommitted, carried for the eventual Task 4 batch commit)
  - §13 amendment committed 2026-05-30 (SHA `3e098bb`, pushed to
    origin/main)
  - This §14 amendment (committed alongside
    `scripts/blind_test/filter_option1.py`, the referenced
    authoritative filter implementation)

### 14.10 — Authority

§10 of this document permits amendments before assembly begins.
This amendment is recorded before assembly begins — the v3 broad-
query enumeration and filtering completed 2026-05-31, but no
sampling from the cleaned pool to §7 quotas has occurred and no
candidate has been recorded into a manifest. The drafted-then-
committed-before-execution model from §13 is preserved: this
amendment text is reviewed and committed BEFORE any sampling step
runs against the cleaned pool.

**Drafted:** 2026-05-31 (during the blind-test cohort first-batch
session, after the v3 filter was eyeballed and confirmed and
before §7 quota sampling).
**Trigger:** filter eyeballing surfaced three operational gaps
during execution of §13.2 against real BioSample data. The
refinements were adopted on a per-class basis after eyeball
samples confirmed each one sharpened toward §13.2's stated scope
intent without moving the scope boundary itself.
**Relationship to §13:** §14 is operationally downstream of §13.
§13 specifies WHAT the discovery channel is (broad query, scope
filter, mechanical filter, shortfall rule); §14 records HOW the
scope filter was operationalized in the encounter with real
metadata, including where the §13.2 enumeration was incomplete
(Refinement A), where the implicit default needed to be made
affirmative (Refinement B), and where strict-MIxS reading
mis-rejected environmental records on depositor field misuse
(Refinement C). §13's scope boundary and shortfall rule are
unchanged.

---

## 15. Pre-assembly amendment 2026-05-31 — Option 1 taxonomic-domain restriction (Bacteria + Archaea)

**Status:** Pre-assembly amendment. Assembly status remains NOT
begun. No cohort candidate has been identified or recorded; no
genome has been downloaded; no scoring or inspection path has been
run on any candidate. This amendment is recorded BEFORE assembly
begins, consistent with §10 and following the same authority basis
as §13 and §14.

### 15.1 — Why this amendment exists

§13.2 pinned the Option 1 discovery query parameters
(`--assembly-source GenBank`, `--released-after 2026-01-01`,
`--mag only`) but left the taxonomic domain of the broad query to
a per-run command invocation. The 2026-05-31 run executed the
query as two parallel `datasets summary genome` calls with
`taxon "bacteria"` and `taxon "archaea"` respectively, enforcing
a prokaryote-only candidate pool by construction (150,024 raw
hits = 141,783 Bacteria + 8,241 Archaea, zero eukaryotic MAGs).
Nothing in §13.2 or §14 itself forced that taxon scoping, however
— it lived only in the operator's per-run command record.

The prokaryote-only domain of CultureForge is already stated at
the project-vision level: `docs/CLAUDE.md` opens with *"AI
platform that predicts cultivation media for novel uncultured
bacteria and archaea …"*. The §13.2 environmental-scope reasoning
cites that vision sentence indirectly as one of its four
supporting signals. The cohort design doc itself, however, does
not contain a top-level scope clause naming the taxonomic domain;
the prokaryote restriction is implicit in the §7 category list
(every category — methanogenesis, anammox, ANME, comammox, cable
bacteria, sulfate reduction, syntrophy, hyperthermophile, etc. —
is a prokaryotic guild) but is nowhere stated as a discovery-query
clause.

This amendment closes that documentation gap. It records the
already-applied taxonomic scoping into the locked discovery
methodology so that every future batch's broad query is bound by
it, rather than the restriction continuing to live only in
per-run commands.

### 15.2 — The clause

**Option 1 discovery query — taxonomic domain (locked).** The
Option 1 broad NCBI `datasets summary genome` query is
restricted to:

- **Bacteria** (NCBI taxid `2`)
- **Archaea** (NCBI taxid `2157`)

Eukaryotic MAGs (fungi, protists, microalgae, eukaryotic phototrophs,
metazoan MAGs of any kind) are OUT of scope for CultureForge and
therefore out of scope for the blind-test cohort. This restriction
applies uniformly across all batches of the multi-batch cohort
assembly. The taxonomic-domain restriction is added alongside —
not in place of — the other locked discovery-query parameters from
§13.2 (`--assembly-source GenBank`, `--released-after 2026-01-01`,
`--mag only`).

**Operational form.** Because `datasets summary genome` requires
either a taxon or an accession subcommand, the broad query is
issued as two parallel invocations (`taxon "bacteria"` and
`taxon "archaea"`) with the §13.2 / §14 flags identical between
them, and the JSONL outputs are concatenated downstream as a
single combined hit list. This is the same operational form used
on 2026-05-31 and is the form that all future batches must
follow.

### 15.3 — Direction of change

**Documentation-only.** This amendment does not change what ran
on 2026-05-31, does not change the §13.2 scope filter, does not
change the §14 refinements, and does not change the §3/§4
mechanical filter. The 2026-05-31 broad query was already
prokaryote-only by construction (141,783 + 8,241 = 150,024 raw
hits, zero eukaryotes); this amendment merely records that the
constraint applies to all future batches as a locked
methodological clause rather than as a per-run operator choice.

The CultureForge applicability domain (Bacteria + Archaea,
eukaryotes excluded) is unchanged — it was already the project
scope per `docs/CLAUDE.md`. The cohort-design enforcement of
that scope is what §15 newly records.

### 15.4 — What this amendment does NOT change

- §1, §2, §3, §4, §6, §7, §8, §9, §10 of the cohort design — all
  unchanged.
- §13 discovery-channel methodology — unchanged (§15 adds one
  locked parameter to the §13.2 broad-query specification; it
  does not modify any of the §13.2 parameters already pinned).
- §14 scope-filter operational refinements — unchanged.
- The 2026-05-31 funnel numbers (150,024 raw → 89,687 scope →
  89,665 mechanical) — unchanged (the broad query was already
  prokaryote-only).
- Documented batch-1 shortfalls per §14.7 (comammox 0, cable
  bacteria 2) — unchanged.
- §13.3 Option 2 operationalization — unchanged. Option 2 has
  not begun. (Option 2 is a literature-search channel; the
  taxonomic-domain restriction applies there too, by the same
  CultureForge-applicability reasoning, but operationalization
  of that restriction for Option 2 is deferred to when Option 2
  runs.)
- 30–40 cohort target, ~50/50 mix, >95% ANI held-out threshold,
  dev-cohort reference, no-peeking rule — all unchanged.

### 15.5 — State of the cohort at amendment time

- **Assembly status:** NOT begun. No candidate identified, no
  candidate recorded, no genome downloaded, no scoring or
  inspect path run.
- **2026-05-31 broad-query state:** Bacteria + Archaea JSONL
  dumps under `data/validation/blind_test_batch1/` (untracked);
  scope-survivor / mechanical-survivor counts as recorded in
  §14.6. No re-run is required — the query already conformed to
  the §15 clause.
- **Open repo-side artifacts** (all doc/data-setup, no scoring):
  - Dev-cohort comparison reference (manifest + sketch zip)
    under `data/validation/` (untracked)
  - `.gitignore` rule for `data/blind_test/` (uncommitted,
    carried for the eventual Task 4 batch commit)
  - Backlog entries appended to `docs/PHASE_6_BACKLOG.md`
    (uncommitted, carried for the eventual Task 4 batch commit)
  - §13 amendment committed 2026-05-30 (SHA `3e098bb`, on
    origin/main)
  - §14 amendment + `scripts/blind_test/filter_option1.py`
    committed 2026-05-31 (locally HEAD; not yet pushed at the
    time of §15 drafting)
  - This §15 amendment

### 15.6 — Authority

§10 of this document permits amendments before assembly begins.
This amendment is recorded before assembly begins — no candidate
has been sampled from the cleaned pool to fill any §7 quota, no
manifest has been written. The drafted-then-committed-before-
execution model from §13 and §14 is preserved.

**Drafted:** 2026-05-31 (immediately after §14 commit, before
any §7 quota sampling).

**Trigger:** during pre-sampling review, the manuscript author
noted that the prokaryote-only constraint — already enforced
on 2026-05-31 by the operator's per-run taxon-argument choice
and stated at the project-vision level in `docs/CLAUDE.md` — was
not written into the cohort discovery methodology. §15 closes
that documentation gap.

**Relationship to §13 and §14.** §13 specified WHAT the
discovery channel is and §14 recorded HOW the scope filter was
operationalized on first contact with real data. §15 records
the TAXONOMIC DOMAIN to which both apply, completing the
discovery-methodology specification so that future batches'
queries are bound by the same domain the 2026-05-31 query was
bound by in practice. None of §13's scope boundary, §14's
direction-of-change framing, or the project Vision's
applicability claim is changed.

---

## 16. Pre-assembly amendment 2026-06-01 — sampling-procedure constraint: at most one MAG per BioProject

**Status:** Pre-assembly amendment. Batch 1 assembly has NOT begun
— no candidate has been recorded in
`docs/phase6/blind_test_cohort.tsv`, no genome has been downloaded,
no skani / ANI / CheckM2 / inspect / scoring path has been run on
any candidate. This amendment is recorded BEFORE the batch-1
sampling step that it governs, consistent with the §10
pre-registration commitment that the protocol cannot be altered
after assembly begins without an amendment record, and consistent
with the drafted-then-committed-before-execution sequence used for
§13, §14, and §15.

### 16.1 — Why this amendment exists

The §13.2 discovery-channel methodology and the §14 scope-filter
refinements specify HOW candidates are identified and which records
pass the scope and mechanical filters, but they leave the per-batch
sampling step (the random draw from the cleaned survivor pool onto
§7 category quotas) under-specified beyond "random sample from each
category's binned survivors with a recorded seed."

A 2026-06-01 first-contact draw against the cleaned 89,665-survivor
pool (seed `20260601`, tier quotas strong=2 / mid=4 / weak=2)
surfaced the gap: the strong-acetogenesis pick (`GCA_055112295.1`,
*Thermacetogenium phaeum*) and the weak-ANME pick
(`GCA_055141645.1`, *Candidatus Methanophagales archaeon
ANME-1-THS*) both came from BioProject `PRJNA308326` — the same
Subsurface-shale hydraulically-fractured-fluid study, different
geographic sites but a single depositor study. A quarter of an
8-MAG batch from one BioProject undercuts the independence a
blind-test cohort needs: one study's MAG-calling pipeline,
sample-handling artifacts, geochemistry, and metadata conventions
become a shared exposure across the affected candidates rather
than independent test signals.

The criteria must drive the draw uniformly. Surgically removing the
second-drawn shale MAG and replacing it would be unrecorded
post-hoc curation — the exact failure mode the §10 pre-registration
commitment is designed to prevent. Instead, the constraint is
declared as a rule, applied uniformly to every category in the
draw, and recorded here BEFORE the re-draw runs, so the committed
methodology matches what ran and the rule binds every future
batch's sampling step the same way. This follows the §14 model:
discovered on first contact with real draw output, applied
uniformly across all categories, recorded as a faithful refinement
of the pre-registered procedure rather than as a one-off
intervention.

### 16.2 — The clause: at most one MAG per BioProject accession per batch

Within a single batch, no two drawn candidates may share a
BioProject accession. The binding identifier is the BioProject
accession reported by NCBI on the Assembly record — specifically
`assembly_info.biosample.bioproject_accession` (or, equivalently,
the accession on the BioSample's `bioprojects[]` list) as it
appears in the broad-query JSONL artifact.

When a category's randomly-drawn survivor shares a BioProject with
an already-drawn candidate **earlier in this batch's draw order**,
the survivor is rejected and the category's draw is re-attempted
against its survivor pool with the rejected accession excluded
from the re-attempt. The re-attempt continues until either a
non-conflicting survivor is drawn or the category's pool is
exhausted. In the exhaustion case, the slot is left short and
documented identically to a §13.2 shortfall (under-fill recorded,
no backfill from another category, no relaxation of the §16
constraint).

Draw order is fixed and reproducible: tier `strong` first, then
`mid`, then `weak`; within each tier, categories are processed in
the alphabetical order of the category names that `random.sample`
returned (i.e. `chosen_cats.sort()` after the tier-level
`random.sample`, then iterated in sorted order for the
per-category `random.choice`). This ordering is recorded in the
draw output so the rule's application is reproducible from the
recorded seed alone.

Records with a missing or empty BioProject accession are treated
as distinct from every other record (i.e. they do not conflict
with anything via this rule). The rationale: BioProject is the
binding signal for shared study provenance; absence of a
BioProject is not itself evidence of shared exposure.

Cross-batch carryover: this clause binds within a single batch. A
future batch may draw from BioProjects that earlier batches drew
from, but each batch's internal one-per-BioProject constraint
still holds. Whether to extend a no-cross-batch-BioProject-overlap
rule to the multi-batch cohort is a separate question, to be
decided when batch 2 is sampled — not pre-empted here.

### 16.3 — Direction of change: sampling-methodology refinement, applied uniformly

**Stricter on within-batch independence; neutral on coverage.** §16
does not move the scope boundary, change the 89,665-survivor pool,
or shift any §7 category quota; it constrains how a batch is drawn
from that fixed pool so that a single depositor study cannot
dominate a batch. Any category can still be filled from its pool as
long as that pool contains at least one BioProject not already
represented earlier in the batch's draw order. Applied uniformly
across all categories in every batch, not selectively to the
categories where the conflict first surfaced — the same
"declare-then-apply" model as §14's refinements and §15's domain
restriction.

### 16.4 — Effect on the 2026-05-31 funnel and on the 89,665-survivor pool

None. The §13.2 broad query, the §14 scope filter, and the §3 / §4
mechanical filter ran on 2026-05-31 and produced the locked
141,783 Bacteria + 8,241 Archaea raw → 89,687 scope → 89,665
mechanical pool documented in §14.6. §16 is a sampling-step
constraint that applies AFTER the survivor pool is fixed; it does
not re-open any earlier filter and does not require re-running the
scope or mechanical steps. The same `survivors_v3.tsv` artifact
remains the authoritative input to the draw; only the draw
procedure changes.

### 16.5 — Implementation: `scripts/blind_test/draw_batch.py`

The executable form of §16.2 lives at
`scripts/blind_test/draw_batch.py`, committed in the same commit as
this amendment alongside `scripts/blind_test/filter_option1.py`
(the §14 scope-filter authority). The script takes the random seed
and per-tier quotas (`--seed`, `--strong`, `--mid`, `--weak`) as
CLI parameters, reads the cleaned survivor pool produced by
`filter_option1.py`, and writes the proposed-candidate TSV to a
caller-specified path under
`data/validation/blind_test_<batch>/`. Its `draw_batch()` function
implements §16.2 — maintaining a running set of drawn BioProject
accessions, rejecting and re-drawing on conflict, leaving slots
short on pool exhaustion. The proposed-batch TSV records the
seed, the tier quotas, the draw order, an explicit citation to
§16, and the list of §16-rejected accessions (each annotated
with the BioProject it conflicted against), so the rule's
application is auditable from the artifact alone — and the
batch is reproducible from the recorded seed + quotas + input
artifacts.

The §16.2 doc text controls; the script is the executable form,
not an alternative authority. Any future batch must run through
this script (or a successor under the same path) so the rule
binds uniformly.

### 16.6 — Shortfalls

§13.2's shortfall rule (`comammox = 0`, `cable bacteria = 2` as
documented batch-1 under-fills) remains in force as written. §16
may additionally cause a category's slot to be left short if that
category's pool contains only BioProjects already represented
earlier in the batch's draw order. A §16-induced shortfall is
documented identically to a §13.2 shortfall (under-fill recorded
in the proposed-batch artifact, no backfill from another category,
no relaxation of the §16 constraint). In the expected case for
batch 1 — pool sizes well above the 8-slot draw for most
categories — §16-induced shortfalls should be rare, but the
small-pool weak-tier categories (ANME = 8, cable bacteria = 2)
are the realistic places they could surface.

### 16.7 — Unchanged

§7 category coverage targets, §13.2 broad-query parameters and the
A2-fallback-deferred default, §14 scope-filter clauses (Clause 4
invertebrate-host, positive-environmental-signal gate, Clause 1
env-host-value exemption), §15 Bacteria + Archaea taxon
restriction, and all §3 / §4 mechanical filters all remain in
force as written. §16 adds a constraint to the sampling step
between "cleaned survivor pool" and "proposed batch"; nothing
upstream of that step changes.

### 16.8 — State at amendment time

- No candidate is recorded in `docs/phase6/blind_test_cohort.tsv`.
- No genome has been downloaded.
- No skani / ANI / CheckM2 / inspect / scoring path has been run
  on any candidate.
- The 2026-06-01 first-contact draw at seed `20260601` produced a
  proposed 8-candidate list that surfaced the BioProject-concentration
  concern (candidates 1 and 7 both from `PRJNA308326`). That list
  was held transiently in
  `data/validation/blind_test_batch1/proposed_batch1.tsv` as a
  pre-amendment artifact, was NOT recorded as the selected batch
  in `docs/phase6/blind_test_cohort.tsv`, and is superseded by the
  §16-compliant re-draw that follows this amendment. The
  re-drawn `proposed_batch1.tsv` is the authoritative
  proposed-batch-1 artifact going forward.

### 16.9 — Authority

Where this amendment conflicts with §5 (which calls for
random-sampling from the cleaned pool without further constraint),
this amendment controls for sampling within a single batch.
§13, §14, §15, and §16 together form the locked
sampling-and-discovery methodology for the blind-test cohort.

---

## 17. Pre-assembly amendment 2026-06-01 — verification-step refinement: held-out ANI requires meaningful alignment

**Status:** Pre-assembly amendment. No candidate is recorded in
`docs/phase6/blind_test_cohort.tsv`. No `cultureforge.py inspect`
/ scoring / prediction path has been run on any candidate. The
2026-06-01 first-contact verification produced a per-candidate
skani table that surfaced the alignment-fraction question; this
amendment locks the AF floor into the §6 verification methodology
BEFORE the verification re-evaluation that follows. Recorded in
the drafted-then-committed-before-execution sequence used for
§13–§16.

### 17.1 — Why this amendment exists

The principle: an ANI ≥95% claim is an organism-level claim only
when ANI is computed over a meaningful fraction of either
genome. ANI estimated from a vanishing alignment is not a noisy
ANI — it is an undefined ANI, dominated by sketch noise on a
handful of universally-conserved k-mers (ribosomal proteins,
rRNA fragments) across genomes that may share nothing else. §4
and §13.2 lock the held-out rule at "any candidate ≥95% ANI to
a dev-cohort organism FAILS the held-out check" but are silent
on the alignment-fraction precondition that makes the ANI metric
interpretable in the first place. §17 closes that
under-specification.

The question surfaced operationally. A 2026-06-01 skani run of
the 8 §16-compliant candidates against the 168 dev-cohort FASTAs
produced one ANI ≥95% hit: candidate `GCA_055112295.1`
(*Thermacetogenium phaeum*, batch-1 acetogenesis) vs. dev gid
1029 (*Carboxydothermus hydrogenoformans*, Phase 5.0 main
acetogenesis) at **96.47% ANI** with `AF_query = 0.08%` and
`AF_ref = 0.05%`. All seven of that candidate's dev-Firmicutes
hits sit in the same regime — *Thermoanaerobacter kivui* 94.51%
at 0.05% / 0.09%, *Pelotomaculum schinkii* 94.51% at 0.03% /
0.09%, *Sporomusa ovata* 93.37% at 0.02% / 0.08%, *Neomoorella
thermoacetica* 90.07% at 0.05% / 0.08% — phylogenetically
dispersed Firmicutes in distinct families, all returning ANI
~87–96% on alignment fractions of 0.02–0.09%. The pattern is
diagnostic of a sketch artifact, not organism-level similarity:
*Thermacetogenium phaeum* and *Carboxydothermus hydrogenoformans*
are organisms in different families.

For contrast, the only ANI hit in the same run with non-trivial
alignment was candidate `GCA_057266155.1` (*Candidatus
Methanophagales archaeon*, batch-1 ANME) vs. dev gid 1006
(*Candidatus Methanophaga* sp. AG-394-G06, also ANME) at
**93.42% ANI** with `AF_query = 28.78%` and `AF_ref = 39.11%`.
Roughly a third of both genomes aligned, ANI computed over real
shared content: a genuine genus-level signal that correctly
passes the 95% rule on its own merit (below threshold). The
contrast is the worked example: 0.05% AF is the noise floor;
~30% AF is the signal floor. The 95% ANI rule needs an AF floor
to distinguish them.

The 15% AF threshold is independently justified, not a
candidate-specific rescue:

- skani's own documentation states that the ANI estimate is
  reliable only above ~15% alignment fraction; below that, the
  metric is dominated by k-mer noise from conserved cores rather
  than aligned content.
- Standard MAG-vs-MAG ANI practice treats ANI hits with AF
  below ~15% as not interpretable for species-level inference.

The clause is therefore principled at two levels — the metric's
own reliability domain and field convention — and is applied
uniformly to every candidate in every batch, not selectively to
the candidate that surfaced the question. Under the same rule, a
future candidate with `AF = 0.04%` / `99.9% ANI` to some dev
organism would be correctly classified as "no meaningful
alignment, ANI artifact, held-out PASS"; a future candidate with
`AF = 25%` / `95.2% ANI` would be correctly classified as
held-out FAIL. The 2026-06-01 candidate is an instance of the
rule's first case, not its rationale.

Surgically excepting `GCA_055112295.1` from the held-out rule
would be unrecorded post-hoc curation — the failure mode §10
exists to prevent. Declaring the AF floor as a rule, applying
it uniformly, and recording it BEFORE the verification
re-evaluation runs preserves the integrity of the pre-registered
methodology and binds every future batch's verification step
the same way.

### 17.2 — The clause: alignment-fraction floor on the held-out ANI rule

The §4 / §13.2 held-out check binds only on skani-reported ANI
hits that satisfy BOTH of the following conditions, computed by
`skani dist` (default learned-ANI mode):

- ANI ≥ 95.0%, AND
- AF_query ≥ 15.0% AND AF_ref ≥ 15.0%

(`AF_query` is the fraction of the candidate genome that
aligned to the dev reference; `AF_ref` is the fraction of the
dev reference that aligned to the candidate. skani column
names: `Align_fraction_query`, `Align_fraction_ref`.)

A candidate FAILS the held-out check (and is dropped per §4 /
§13.2) iff at least one of its skani hits against the dev
cohort satisfies BOTH thresholds. ANI hits with ANI ≥ 95% but
with `AF_query < 15%` OR `AF_ref < 15%` are recorded for
transparency in the per-batch verification artifact but do NOT
trigger exclusion — such hits are sketch artifacts on a tiny
shared fragment (typically universally-conserved markers), not
organism-level similarity.

The reasoning is not "ANI ≥ 95% sometimes lies." It is "ANI is
not defined when alignment is vanishing." Below 15% AF, the
metric the rule depends on is itself unreliable; the rule
therefore does not have authority to bind. The 95% ANI threshold
is unchanged.

Operationally:

```
held_out_FAIL ⇔ ∃ dev_ref : ANI(candidate, dev_ref) ≥ 95%
                              AND AF_query(candidate, dev_ref) ≥ 15%
                              AND AF_ref(candidate, dev_ref) ≥ 15%
```

The per-batch verification artifact (e.g.
`data/validation/blind_test_batch1/verification_batch1.tsv`)
records, for each candidate, the maximum-ANI dev hit AND its
AF values AND a textual flag indicating which of the two
thresholds the hit satisfies, so the rule's application is
auditable from the artifact alone.

### 17.3 — Direction of change: verification-step refinement, applied uniformly

**Neutral on novel candidates; stricter on classification
rigor.** §17 does not move the scope boundary, change the
89,665-survivor pool, alter the §16-compliant 8-candidate batch,
or relax the 95% ANI threshold. The 95% rule still binds; §17
gates whether the ANI metric is reliable in the first place.
The set of candidates that pass held-out under §17 is a superset
of the set that would pass without it only when the
not-passed-without-§17 candidates are precisely those with ANI
≥ 95% on alignment fractions too small for the metric to be
interpretable — which is the artifact case the field excludes by
convention.

Same "declare-then-apply-uniformly" model as §14 / §15 / §16.

### 17.4 — Effect on the 2026-05-31 funnel and on the §16-compliant batch

No effect on the funnel, the survivor pool, the §16-compliant
sampling procedure, or the 8 §16-compliant candidates. The
artifacts `survivors_v3.tsv` and `proposed_batch1.tsv` are
unchanged.

§17 applies to the §6 verification step that runs after
sampling. The 2026-06-01 first-contact verification table
`verification_batch1.tsv` is a pre-amendment artifact; the
§17-amended re-evaluation that follows supersedes it.

### 17.5 — §6 verification methodology, as amended

The §6 verification pipeline is, with §17 in force:

  **Step 6.A — Held-out ANI.** Run `skani dist` for each
  candidate against the dev-cohort FASTAs listed in
  `data/validation/dev_cohort_fasta_manifest.tsv`. For each
  candidate, record the maximum-ANI hit: `ANI`, `AF_query`,
  `AF_ref`, dev `gid`, dev `accession`, dev organism note.

  **Step 6.B — Apply the §17.2 floor.** A candidate is
  `held_out_FAIL` iff at least one hit satisfies ANI ≥ 95% AND
  `AF_query` ≥ 15% AND `AF_ref` ≥ 15%. Otherwise
  `held_out_PASS`, recorded with the raw skani values for
  transparency.

  **Step 6.C — Quality.** Apply the §3 thresholds (completeness
  ≥ 70%, contamination ≤ 5%). If depositor-published CheckM /
  CheckM2 data is present in the BioSample attributes, use it;
  otherwise run CheckM2 locally on the staged candidate
  genome. Without CheckM2 and without BioSample-published data,
  the candidate is recorded as `quality_INCONCLUSIVE` and
  cannot enter the cohort until completeness / contamination
  data is obtained.

  **Step 6.D — Overall verdict.** `PASS` only if
  `held_out_PASS` AND `quality_PASS`. `FAIL` if either
  `held_out_FAIL` or `quality_FAIL`. `INCONCLUSIVE` if
  `held_out_PASS` but quality has not been measured; in that
  state the candidate cannot be recorded into the cohort
  manifest until the quality measurement is supplied.

§6's original text is preserved; the methodology above is its
operational form in force from §17 forward, the same way §14 /
§15 / §16 supersede portions of §3 / §4 / §5 / §13.2 without
rewriting the original sections.

### 17.6 — Shortfalls

§13.2's category-pool shortfalls, §16's BioProject-exhaustion
shortfalls, and §17-induced `FAIL` or `INCONCLUSIVE`
classifications are all treated identically at the
cohort-composition level: documented under-fill, no backfill
from another category, no relaxation of any rule.

### 17.7 — Unchanged

§7 category coverage targets; §13.2 broad-query parameters
and discovery channel; §14 scope-filter clauses; §15
Bacteria + Archaea domain; §16 one-per-BioProject sampling
constraint; §3 / §4 mechanical filter and the 95% ANI
threshold (the ANI threshold is unchanged — §17 governs when
it binds, not what it is); all upstream filter artifacts.

### 17.8 — State at amendment time

- No candidate is recorded in `docs/phase6/blind_test_cohort.tsv`.
- No `cultureforge.py inspect` / scoring / prediction path has
  been run on any candidate.
- The §16-compliant 8-candidate batch is locked at
  `data/validation/blind_test_batch1/proposed_batch1.tsv`
  (committed-script @ `4389db7` + seed `20260601` + quotas
  `2/4/2` reproduce it).
- The 2026-06-01 first-contact verification table
  `verification_batch1.tsv` is a pre-amendment artifact and is
  superseded by the §17-amended re-evaluation that follows.
- CheckM2 is not installed on this host; resolving the
  `quality_INCONCLUSIVE` rows in the re-evaluation requires
  either installing CheckM2 or surfacing BioSample-published
  CheckM data not detected in the first-contact pass.

### 17.9 — Authority

§17 amends §6 (verification methodology) and refines the
operational form of §4 / §13.2 (the held-out rule).
Together §13 (discovery), §14 (scope filter), §15
(Bacteria + Archaea domain), §16 (sampling constraint), and
§17 (held-out alignment-fraction floor) form the locked
sampling-discovery-verification methodology for the
blind-test cohort.
