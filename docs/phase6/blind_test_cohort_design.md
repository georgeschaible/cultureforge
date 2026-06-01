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
