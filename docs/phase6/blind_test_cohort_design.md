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

*Superseded by §20 (2026-06-08); the four original phrases above did not match field vocabulary in the 2024-2026 window — see §20 for the trigger, the replacement queries, and the diagnostic basis.*

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

---

## 18. Pre-assembly amendment 2026-06-01 — completeness pre-filter + CheckM2 binding-gate rule

**Status:** Pre-assembly amendment. No candidate has been
recorded in `docs/phase6/blind_test_cohort.tsv`. The §16-compliant
2026-06-01 8-candidate batch verified to 3 PASS / 5 FAIL on
completeness under §3, prompting the 2026-06-01 descriptive
ablation of the 89,665-survivor pool
(`data/validation/blind_test_batch1/completeness_ablation.tsv`).
This amendment locks the two-part rule into methodology BEFORE
the pool re-filtering and the next batch draw. Recorded in the
drafted-then-committed-before-it-binds sequence used for §13–§17.

### 18.1 — Why this amendment exists

The principle: a blind-test cohort's quality column must be a
real, uniform measurement — one tool, one version, applied
identically to every recorded member — not a patchwork of
depositor self-reports made with different versions that
disagree systematically. And the upstream pool must not
discard MAGs simply for being unmeasured, because "no published
quality data" is not itself a quality signal.

§3 and §6 pre-register a completeness / contamination threshold
(≥ 70% complete, ≤ 5% contamination) but leave two operational
questions under-specified: (a) what role published depositor
quality data plays in pool curation, and (b) whose measurement
is the binding one for recording a candidate into the cohort.

The questions surfaced when the §16-compliant 8-candidate batch
verified to 3 PASS / 5 FAIL on completeness under §3. The
2026-06-01 descriptive ablation established four evidence points:

1. **62.40% of the pool (55,953 / 89,665 MAGs) carries
   published completeness/contamination in BioSample
   metadata; 37.60% (33,712) has none.** The "partial data"
   case is empty in practice — depositors who publish
   completeness also publish contamination (CheckM produces
   both together).

2. **Published numbers are tool-version-heterogeneous.** Ten
   tool labels appear, dominated by unversioned `CheckM`
   (37,281 records) and `Anvio 7.1` (9,345 records, which wraps
   CheckM); `CheckM v1.1.3` (7,169), `CheckM2` (1,052),
   `CheckM2_v1.0.1` (581), and other variants make up the rest.
   Only ~3% cite a CheckM2 variant. CheckM and CheckM2 disagree
   systematically on some lineages — Patescibacteria,
   AAI-divergent archaea — so recording on published numbers
   would make the cohort's quality column an internally
   incomparable patchwork.

3. **A strict published-≥70% pre-filter (excluding all no-data
   MAGs) would structurally empty the hard categories.** Per
   the ablation: ANME (n=8) → 0 strict-passing; cable bacteria
   (n=2) → 0; extreme archaea (n=272) → 1; lithoautotrophic
   iron (n=35) → 0. These are the categories where the pool is
   dominated by no-data MAGs, not by failing MAGs. The batch-1
   ANME candidate `GCA_057266155.1` is the worked example —
   no published completeness, measured by CheckM2 v1.1.0 at
   82.79% / 2.51%, passes §3 cleanly.

4. **CheckM2 cost is negligible at cohort scale.** The
   2026-06-01 batch-1 verification measured 6 candidates in 69
   seconds on 12 threads (~5 minutes projected for a full
   30–40-organism cohort). The "measure on draw" alternative to
   a strict pool pre-filter is operationally trivial.

The two-part rule below flows directly from these four
findings: drop MAGs already known to fail quality (the only
role published data should play), keep MAGs that are passing
or unmeasured (the unmeasured-but-good case is real and
concentrated in the hard categories), and measure every
recorded candidate uniformly with the project's pinned CheckM2
so the cohort's quality column is internally consistent across
all recorded members. The rule is principled at the level of
"what is the quality column" and applies uniformly to every
candidate in every batch.

§18 supersedes the implicit "trust whatever quality data
exists" assumption that §3 / §6 read as before this amendment.
That assumption produces a tool-heterogeneous column on the
record side and an over-strict cut on the pool side; §18
replaces it with one binding tool on the record side and a
purely-corrective cut on the pool side.

### 18.2 — The clause: two parts

#### 18.2.A — Pool pre-filter (upstream, conservative)

A MAG is EXCLUDED from the §16 draw pool iff its BioSample
attributes report:

- `published_completeness < 70.0%`, OR
- `published_contamination > 5.0%`

Where `published_completeness` and `published_contamination`
are values of any BioSample attribute whose name
case-insensitively contains "completeness" or "contamination"
respectively, excluding attributes whose name also contains
"software" — i.e. the same field-name search the 2026-06-01
ablation used, which surfaced `completeness score` /
`contamination score` (55,915 records) and `Completeness (%)`
/ `Contamination (%)` (38 records) as the only naming
conventions in use.

A MAG is RETAINED if either:

- it has published completeness ≥ 70% AND published
  contamination ≤ 5% (published-passing), OR
- it has no published completeness OR contamination attribute
  (no-data — kept; measured at recording time per 18.2.B).

Rationale: "no published quality data" is not a quality
signal. The pre-filter's role is to drop MAGs the depositor
has self-flagged as failing, not to discard unmeasured ones.
The strict alternative — require published-≥70% — would empty
ANME, cable bacteria, extreme archaea, and lithoautotrophic
iron from the draw pool, the same categories §7 already
identifies as the hardest to fill.

Operationally, 18.2.A runs strictly downstream of all upstream
filters (§14 scope, §3 / §4 mechanical, §15 domain). Its
output is the new survivor pool the §16 draw operates on.

#### 18.2.B — CheckM2 binding quality gate (every recorded member)

Every candidate that will be RECORDED into
`docs/phase6/blind_test_cohort.tsv` MUST be verified by this
project's pinned CheckM2 install (currently version 1.1.0,
with the bundled DIAMOND reference DB
`uniref100.KO.1.dmnd` at the path resolved by
`checkm2 database --current`) and MUST clear:

- `checkm2_completeness ≥ 70.0%`, AND
- `checkm2_contamination ≤ 5.0%`

on the CheckM2-reported numbers. The depositor's published
quality numbers are used ONLY for the upstream pre-filter
exclusion in 18.2.A. They are NEVER used as the quality of
record, and they NEVER substitute for a CheckM2 measurement
on a candidate proposed for recording.

The CheckM2 version is pinned for cohort uniformity. A future
version bump (e.g. CheckM2 v1.2.x) requires its own
pre-assembly amendment specifying the new version and the
rationale; it does not silently propagate from a
`conda update`. Within a single recorded cohort, every member
is measured by the same CheckM2 version.

The CheckM2 numbers and the tool version are recorded in the
per-batch verification artifact (e.g.
`verification_batch1.tsv` and `checkm2_quality_report.tsv`),
so the rule's application is auditable from the artifacts
alone.

### 18.3 — Direction of change

**Stricter on what counts as the quality of record; neutral
on the pool's category coverage; corrective on the pool's
known-failing exclusions.** §18 does not move the scope
boundary or alter any §14 / §15 / §16 / §17 rule. It
pre-filters the pool to drop known-failing MAGs while
preserving the no-data MAGs that strict-mode would empty hard
categories of, and it elevates this project's CheckM2 as the
binding quality measurement so the cohort's quality column is
internally consistent.

Direction relative to the original §3 + the implicit
"trust whatever quality data exists" assumption: the
trust-whatever assumption is replaced by a uniform
measurement rule. Direction relative to the §6 verification
step as amended by §17: §6.C already accepted CheckM2 or
BioSample-published CheckM; §18 makes CheckM2 mandatory and
specifies the published role precisely (pre-filter only,
never recording).

Same "declare-then-apply-uniformly" model as §14 / §15 / §16
/ §17.

### 18.4 — Effect on the 2026-05-31 funnel and on the §16-compliant batch

The 2026-05-31 funnel (141,783 Bacteria + 8,241 Archaea raw →
89,687 scope → 89,665 mechanical) is unchanged at the scope
and mechanical stages. §18.2.A applies AFTER §14 / §3 / §4 /
§15 and BEFORE the §16 draw — the pool the draw operates on
is now the §18-pre-filtered version of `survivors_v3.tsv`.

The §16-compliant 2026-06-01 8-candidate batch was drawn from
the pre-§18 pool. Of those 8, 3 PASS the §18.2.B binding gate
(CheckM2 ≥ 70% / ≤ 5%): `GCA_054919905.1` (Methanohalophilus
halophile, 96.38% / 0.12%), `GCA_055897235.1` (Thermotogota
hyperthermophile, 84.17% / 0.28%), `GCA_057266155.1`
(Methanophagales archaeon ANME, 82.79% / 2.51%). The other 5
FAIL under §18.2.B and §3. Recording a cohort under §18
requires a re-draw against the §18.2.A-pre-filtered pool —
see 18.7.

### 18.5 — Amended §3 and §6 operational form

§3's threshold values (completeness ≥ 70%, contamination
≤ 5%) are unchanged. What §18 amends is what the thresholds
are measured ON, and at which step.

**Amended §3 — quality thresholds, in operational form:**

  - **Quality of record** (value used to admit a candidate
    into the cohort): CheckM2 (pinned project version) on the
    locally staged FASTA — never the depositor's published
    number.
  - **Pool eligibility** (value used to exclude a MAG from
    the draw pool): depositor's published completeness /
    contamination when present (excluded if <70% / >5%);
    MAGs with no published data are pool-eligible and have
    their quality measured at recording time per the binding
    gate.

**Amended §6 — verification pipeline, in operational form
(extends the §17-amended form):**

  - **Step 6.0 — Pool pre-filter (§18.2.A).** Before any §16
    draw, the survivor pool is filtered to exclude MAGs with
    `published_completeness < 70%` or
    `published_contamination > 5%`. The output is the
    §18-pre-filtered survivor pool, recorded as a new artifact
    (e.g. `survivors_v4.tsv`) with its own per-category bin
    counts.
  - **Step 6.A** — unchanged (held-out ANI via `skani dist`).
  - **Step 6.B** — unchanged (§17 alignment-fraction floor).
  - **Step 6.C — Quality (§18.2.B).** Run CheckM2 (pinned
    project version) on the staged candidate genome. Record
    the CheckM2 completeness, contamination, model used, and
    CheckM2 version. Apply the §3 thresholds. Depositor-
    published numbers from the BioSample are recorded for
    transparency but are NOT used as the quality of record.
  - **Step 6.D** — unchanged (overall verdict combining
    held-out + quality).

§3's and §6's original text is preserved; the amended form
above is the operational §3 / §6 in force from §18 forward,
the same append-only supersession pattern §14 / §15 / §16 /
§17 use.

### 18.6 — Shortfalls

§13.2's category-pool shortfalls, §16's BioProject-exhaustion
shortfalls, §17-induced FAIL / INCONCLUSIVE classifications,
and §18-induced shortfalls (a category whose §18-pre-filtered
pool is too small, or where a draw's CheckM2 verification
yields no PASS-ing candidate) are all treated identically at
the cohort-composition level: documented under-fill, no
backfill from another category, no relaxation of any rule.

### 18.7 — Operational consequences (tracked separately from this commit)

§18 triggers two implementation actions, recorded as TO-DO at
amendment time:

1. **Re-filter the 89,665-survivor pool under §18.2.A.** The
   §18-pre-filtered pool will be written as a new artifact
   (e.g. `survivors_v4.tsv`) with its own per-category bin
   counts. The resulting pool size and per-category counts are
   recorded at implementation time, NOT pre-committed in this
   amendment — the binding number is what the actual re-filter
   run produces.

2. **Re-run the §16 draw against the §18-pre-filtered pool.**
   The 2026-06-01 8-candidate `proposed_batch1.tsv` is
   superseded: it was drawn from the pre-§18 pool and its
   strong tier is empty under §18.2.B. The next draw uses the
   same committed `scripts/blind_test/draw_batch.py` against
   the §18-pre-filtered pool, with a fresh recorded seed
   (per §16's reproducibility contract).

### 18.8 — Related-but-separate opportunity (NOT part of §18)

CheckM2 v1.1.0 is now installed and is the binding tool for
§18.2.B. The dev-cohort `genome_quality` table — historically
empty per the phase-6 backlog — could be backfilled using the
same install, which would close a long-standing gap and make
the dev-cohort quality column comparable to the blind-test
cohort's. This is flagged as a related opportunity, NOT part
of §18 and NOT a §18-induced action: it touches the dev
cohort, not the blind-test pool, and is recorded as its own
task on the project backlog.

### 18.9 — Unchanged

§7 category coverage targets; §13.2 broad-query parameters
and discovery channel; §14 scope-filter clauses; §15
Bacteria + Archaea domain; §16 one-per-BioProject sampling
constraint; §17 alignment-fraction floor; §4 mechanical
filter; §3's threshold values (the threshold values
themselves are unchanged — §18 governs what they are
measured on, not what they are).

### 18.10 — State at amendment time

- No candidate is recorded in `docs/phase6/blind_test_cohort.tsv`.
- No `cultureforge.py inspect` / scoring / prediction path has
  been run on any candidate.
- The §16-compliant 8-candidate `proposed_batch1.tsv` is
  preserved as the pre-§18 draw record, NOT recorded into the
  cohort manifest; it is superseded by the §18-compliant
  re-draw that follows.
- The §17-amended `verification_batch1.tsv` records the
  8-candidate verification (3 PASS / 5 FAIL). Its
  CheckM2-derived rows are §18-consistent and can be reused;
  the 2 depositor-CheckM-derived rows (#2, #3) are FAIL under
  both §3 and §18.2.B.
- CheckM2 v1.1.0 is installed in the `checkm2` conda env; the
  DIAMOND DB
  `/home/george/databases/CheckM2_database/uniref100.KO.1.dmnd`
  (3.08 GB) is verified and registered.

### 18.11 — Authority

§18 amends §3 (quality thresholds — clarifies what they are
measured on) and §6 (verification methodology — adds Step 6.0
and refines Step 6.C). Together §13 (discovery), §14 (scope
filter), §15 (Bacteria + Archaea domain), §16 (sampling
constraint), §17 (held-out alignment-fraction floor), and §18
(completeness pre-filter + CheckM2 binding-gate rule) form
the locked sampling-discovery-verification methodology for
the blind-test cohort.

---

## 19. Pre-assembly amendment 2026-06-07 — Option 2 channel operationalization of §14 scope + §16 independence

**Status:** Pre-assembly amendment for the Option 2 literature channel. Option 2 has NOT begun: no PubMed query has been executed, no candidate paper has been surfaced, no candidate organism has been recorded. This amendment is recorded BEFORE Option 2 assembly begins, consistent with the §10 pre-registration commitment and the §15.4 explicit deferral: "operationalization of [the §15 / §14 / §16] restriction for Option 2 is deferred to when Option 2 runs." At the time of drafting, Option 1 batch 1 is recorded in `docs/phase6/blind_test_cohort.tsv` (7 verified candidates + 1 documented §13.2 comammox shortfall, commit `888047d` on `origin/main`).

### 19.1 — Why this amendment exists

§13 / §14 / §15 / §16 / §17 / §18 collectively pin the discovery, scope, sampling, and verification rules for the blind-test cohort. They were drafted and operationalized against the Option 1 pipeline shape — broad NCBI `datasets summary genome` query → BioSample MIxS metadata filter → mechanical §3 / §4 filter → category bin → seeded random sample → per-candidate verification — because that was the channel running at amendment time. The amendments were always intended to apply uniformly across discovery channels per the "declare-then-apply-uniformly" principle restated in §14.5, §15.3, §16.3, §17.3, and §18.3.

But the operationalization is channel-shape-dependent. Two rules in particular do not translate cleanly:

1. **§14 (scope filter — environmental, non-host-associated)** is written against BioSample MIxS fields (`env_broad_scale` / `env_local_scale` / `env_medium` MIxS terms, `host` / `host_taxid` / `host_scientific_name`, `isolation_source` text). The Option 2 literature channel surfaces papers, not BioSample records — provenance is described in the paper's prose, and the per-paper inclusion call is by §13.3 a human judgment. There is no structured metadata field for a script to operate on.

2. **§16 (one MAG per BioProject per batch)** is written against the BioProject accession field on the NCBI assembly record. The Option 2 channel's "source" is not obviously the same atomic unit: a single paper (PMID) may describe one isolate cultivated from a single environment, or several isolates across several environments, or one isolate whose genome was deposited under a BioProject that contains many other unrelated MAGs. The relevant independence unit — and the threshold at which the rule binds — is not knowable until the search reveals the actual per-source distribution.

§19 fills these two operationalization gaps. It does NOT touch §13.3 (the four verbatim PubMed queries, dedup, human-judgment inclusion call, verify-or-fall-back on cultivation conditions) — those are settled. It does NOT touch §8 (scoring methodology) — the Layer 1 plausibility audit + Layer 2 V12 recipe-agreement scoring split for Option 2 organisms is settled. It does NOT touch any per-candidate quality rule — §6 verification, §15 domain, §17 ANI AF floor, §18 CheckM2 binding gate apply to Option 2 organisms unchanged (§19.5 enumerates).

### 19.2 — The clauses: two parts

#### 19.2.A — §14 scope for the literature channel: per-paper human judgment with recorded scope rationale

The §14 scope boundary — environmental (non-host-associated), Bacteria + Archaea per §15 — applies to Option 2 candidates. The boundary is the same; the determination method differs because the input shape differs.

**The clause.** For each paper accepted into Option 2 per §13.3's inclusion call, the manuscript author MUST record an explicit one-line scope rationale on the paper's manifest row. The rationale states:

- the organism's stated environmental origin as described in the paper (e.g., "deep-sea hydrothermal sediment from the Lau Basin"; "anoxic freshwater sediment, Lake Lugano"; "halite crust, Atacama Desert"); and
- explicit confirmation that the organism is NOT host-associated, NOT clinical, and NOT eukaryotic (the §15 domain restriction).

Format on the Option 2 manifest row: a `scope_rationale` column carrying free-text prose of the above form. The rationale is what the paper itself says, transcribed faithfully — it is NOT inferred, NOT extrapolated, and NOT softened to make a borderline organism pass. If the paper's stated environmental origin falls outside the §14 / §15 boundary — host-associated, clinical, or eukaryotic — the paper is rejected at the §13.3 inclusion step on scope grounds and a one-line `scope_rejection_note` is recorded against the PMID instead. The specific host categories that fall under "host-associated" are the ones enumerated in §14; §19.A does NOT re-list them, because the Option 2 determination is a human reading of the paper against the §14 boundary, not a token match against §14's list.

**No scope-filter script for Option 2.** Unlike §14's `scripts/blind_test/filter_option1.py`, there is no `filter_option2.py` and no token-matching pass against MIxS fields, because there are no MIxS fields in the literature channel's input. The scope determination is folded into §13.3's existing per-paper human-judgment inclusion call — the inclusion call is now explicitly scope-aware, and the scope rationale is now a recorded artifact rather than an implicit "the manuscript author read it and judged."

**Honest framing.** This is the same §14 scope boundary applied through human reading rather than a metadata filter, because the literature channel provides prose rather than structured BioSample metadata. The principle is unchanged; only the operationalization differs. The recorded scope rationale is the audit trail that lets a reviewer reconstruct each scope determination from the manifest alone, without having to re-read every paper.

**Interaction with §13.3 verify-or-fall-back.** §13.3's "If the cultivation conditions cannot be confirmed from retrievable text […] record `cultivation_conditions = 'unverified — source not retrievable'`" rule continues to govern cultivation-condition extraction. The §19.A scope rationale is a separate field on a separate axis: the scope determination depends only on the paper's environmental-origin description (typically present in any paper's Methods section even when the cultivation recipe is paywalled or sparse), so it should rarely be "unverified." If the environmental origin is genuinely not retrievable from the abstract + available text, the paper is rejected at the §13.3 inclusion step (no scope rationale → no admission), not admitted-with-unknown-scope.

#### 19.2.B — §16 independence for the literature channel: mechanical check, parameterized threshold

The §16 anti-concentration principle — no single source dominates the sampled set — applies to Option 2 candidates. The independence unit and the binding threshold are parameterized to what the search reveals, not pre-committed, because the per-source distribution of the Option 2 corpus is not knowable until §13.3 has been executed.

**The clause.** Once the §13.3-included Option 2 candidate set is assembled (post-inclusion-judgment, post-§19.A scope determination, but pre-verification), a recorded mechanical computation MUST run over the included set's accessions:

- group the included organisms by **PMID** (the paper from which the organism was discovered);
- group the included organisms by **BioProject accession** (the deposit umbrella under which the genome assembly lives);
- record the per-PMID count and the per-BioProject count distributions inline with the Option 2 batch verification record.

**Threshold N.** If any single PMID contributes more than N organisms to the included set, OR any single BioProject contributes more than N organisms to the included set, the §16 one-per-source rule binds for that group: one organism is kept (selected by the recorded tie-break rule below) and the remaining organisms in the over-represented group are either excluded from the batch, or — if exclusion would empty a §7 category that otherwise has no candidate — recorded as a documented over-representation note inline with the verification record (the same shortfall-style honesty as §13.2's category shortfall rule).

The value of N is set at execution time and recorded then, NOT pre-committed in this amendment. Same "report-at-implementation, not pre-committed" model as §18.4's pool count: the threshold is a function of the actual distribution the search reveals. Concretely, if the corpus is many papers each contributing one organism (independence trivially satisfied — the modal per-PMID and per-BioProject count is 1 with no over-representation), N is recorded as "n/a — no group exceeded 1 organism" and no exclusion runs. If the corpus is few papers each describing several isolates (e.g., one paper describes a 5-organism syntrophic consortium), N is set with the per-source distribution visible — typically N = 1, unless an over-representation reflects a methodologically-relevant group structure that the manuscript author explicitly judges as worth preserving (e.g., a paper that defines a novel taxon family with several characterized members may warrant N = 2 with the rationale recorded). The choice of N and the rationale for it are recorded on the same row as the per-source distribution.

**Tie-break (which one to keep within an over-represented group).** When more than one organism from the same PMID or same BioProject would be kept under the §13.3 inclusion call, the one retained for the batch is selected by this priority:

1. The organism whose §7 category is otherwise empty or under-represented in the batch (preserves §7 coverage);
2. If category-tied, the deterministic first by accession (lexicographic on `GCA_*` / `GCF_*`).

The tie-break is deliberately neutral on scoring favorability. A documentation-completeness criterion (rank by how thoroughly the paper documents the cultivation recipe) was considered and rejected, because "most completely documented" correlates with "most favorably scoreable" on §8 Layer 2, and the cohort's defensibility rests on selection being provably uncorrelated with scoring outcome. The cost of dropping that criterion — that the retained organism may occasionally be the documentation-poorer of an over-represented group — is absorbed by §13.3's verify-or-fall-back rule: that organism contributes a Layer 1 plausibility score and records `cultivation_conditions = "unverified — source not retrievable"` for Layer 2 rather than failing the cohort. The selection rationale (which §7 category was preserved, which accession won lex order) is recorded on the manifest row alongside the scope rationale.

**Both axes checked, not either-or.** The check runs on PMID-grouping AND BioProject-grouping independently. A paper and a BioProject are not the same atomic unit — a single paper may deposit under multiple BioProjects, and a single BioProject may underlie multiple unrelated papers — so source concentration on either axis warrants the check. The recorded distribution covers both.

**Mechanical, not eyeball.** The check is a recorded computation — counts per PMID, counts per BioProject, sorted descending, recorded inline with the batch verification record — not a judgment-call read of the candidate list. This is the same "tilted lens vs. neutral mechanism" distinction §13.2 / §14 / §15 / §16 make: the mechanism's neutrality is what makes the result defensible, not the human's confidence in it.

### 19.3 — Direction of change: pipeline-shape adaptation, applied uniformly

**Neutral on scope and independence principles; adapts only the operationalization to the channel's input shape.** §19 does not move the §14 scope boundary, does not relax the §16 anti-concentration principle, and does not introduce any new candidate-property restriction. It specifies the mechanism by which §14 and §16 bind in a channel where the Option 1 pipeline's input fields (BioSample MIxS metadata, BioProject accession on a `datasets summary genome` record) are not the directly-available input fields.

Same "declare-then-apply-uniformly" model as §14 / §15 / §16 / §17 / §18: the principle is declared once, the operationalization is honest about what is mechanical and what is human-judgment, and the per-candidate rules are channel-invariant.

The asymmetry in §19's two parts — §19.A is human-judgment-with-recorded-rationale and §19.B is mechanical-with-parameterized-threshold — is deliberate and not arbitrary. It tracks the asymmetry of what the channel provides: prose for provenance (where the field doesn't exist to script against), accession identifiers for grouping (where mechanical counting is straightforward once the included set is assembled).

### 19.4 — Effect on the recorded batch and on the survivor pool

No effect on the recorded Option 1 batch 1 manifest (`docs/phase6/blind_test_cohort.tsv` @ `888047d`). No effect on the Option 1 §18.2.A survivor pool (`data/validation/blind_test_batch1/survivors_v4.tsv`, md5 `42f65af83cbd48c91e331b36d6306787`, 72,796 records). §19 governs only the Option 2 channel, which has not begun.

### 19.5 — Per-candidate rules that apply to Option 2 unchanged

Once an Option 2 candidate has been admitted by §13.3 + §19.A and survived the §19.B independence check, the per-candidate rules that govern recording into the cohort manifest apply unchanged:

- **§6 verification protocol** (FASTA download, CheckM2 quality, deposit-date check, reference-set non-overlap, GTDB-Tk taxonomic assignment, AND the §6 step 6 Option-2-specific "verify cultivation paper, extract conditions" add-on) — applies to Option 2 candidates as written.
- **§15 taxonomic domain (Bacteria + Archaea, no eukaryotes / viruses / archaeal-host-cells)** — applies to Option 2 candidates as written; the §19.A scope rationale explicitly confirms this for each paper, so it is also surfaced at the inclusion-judgment step.
- **§17 held-out ANI alignment-fraction floor** — applies to Option 2 candidates as written. Each Option 2 candidate is sketched with skani at `-s 50 --min-af 0`, compared against the 168-genome dev-cohort reference at `data/validation/dev_cohort_sketches_k31_s1000.zip`, and held to the §17 alignment-fraction floor as well as the §13.4 95% ANI threshold.
- **§18.2.B CheckM2 binding-gate rule** — applies to Option 2 candidates as written. Each Option 2 candidate has CheckM2 v1.1.0 (DB `/home/george/databases/CheckM2_database/uniref100.KO.1.dmnd`) run on its FASTA; published CheckM / CheckM2 values from the source paper are not recorded into the manifest in lieu of this measurement (per §18.2.B).

These rules are listed here to make explicit that §19 does not touch them. They were always meant to apply to Option 2; §19's silence on them means "unchanged," not "deferred."

### 19.6 — Shortfalls and interaction with the §13.2 / §14.7 shortfall rule

If the §13.3 + §19.A + §19.B sieve produces fewer Option 2 organisms than the ~15-20 §5 target, OR fewer organisms in a §7 category than the category's quota, the shortfall rule from §13.2 / §14.7 still governs: document the shortfall inline with the Option 2 batch verification record; do NOT relax §19.A scope to admit host-associated papers, do NOT relax §19.B independence to admit over-represented groups, do NOT broaden §13.3's four query strings to category-named variants. The shortfall is information about what the cultivation-pair literature looks like in 2024–2026, not an obstacle to route around. Under-supply backfilled from Option 1, per §5's existing mix-target rule, remains the recorded fallback for cohort-level shortfalls.

### 19.7 — Unchanged

- §1, §2, §3, §4, §5 (the original Option 2 protocol and the 30-40 / ~50/50 mix target), §6, §7, §8, §9, §10 of the cohort design — all unchanged.
- §13.3 Option 2 operationalization (four verbatim PubMed query strings, PMID dedup, human-judgment inclusion call, verify-or-fall-back on cultivation conditions) — unchanged. §19 sits adjacent to §13.3, not on top of it: §19.A and §19.B run alongside §13.3's existing per-paper workflow rather than replacing any of it.
- §13.4 held-out threshold (>95% ANI to any dev-cohort genome) and dev-cohort sourmash sketch reference (`data/validation/dev_cohort_sketches_k31_s1000.zip`, k=31, scaled=1000) — unchanged.
- §13.2 Option 1 operationalization (broad query parameters, scope filter, mechanical filter, category binning, shortfall rule) — unchanged.
- §14 / §15 / §16 / §17 / §18 — all unchanged in their Option 1 operationalization. §19 does not retroactively re-operationalize any of them for Option 1.
- The no-peeking rule — unchanged. No `cultureforge.py inspect` / scoring / prediction path runs on any Option 2 candidate prior to cohort lock, just as it has not run on any Option 1 candidate.

### 19.8 — State at amendment time

- **Option 1 batch 1:** recorded. `docs/phase6/blind_test_cohort.tsv` carries 7 verified candidates (BT001–BT007) + 1 documented §13.2 comammox shortfall (BT008), committed at `888047d` and pushed to `origin/main`. The full Option 1 draw provenance is reproducible via the four committed scripts at their recorded SHAs (`filter_option1.py` @ `0d5a7b8`, `refilter_v4.py` @ `225a2b3`, `draw_batch.py` @ `4389db7`, `redraw_batch.py` @ `e42a294`).
- **Option 2:** NOT begun. No PubMed query executed. No candidate paper surfaced. No Option 2 candidate organism recorded. No FASTA downloaded for an Option 2 candidate. No skani / CheckM2 / inspect / scoring path run on any Option 2 candidate.
- **Carry-forward artifacts:** none yet for Option 2. The dev-cohort sourmash sketch and manifest under `data/validation/` remain the reference standup for §13.4's held-out check and will be reused for Option 2 candidates without modification.
- **Open repo-side artifact:** the §19 amendment text (this section, drafted before any Option 2 query runs).
- **Manifest schema reconciliation pending.** The Option 2 manifest row will introduce columns not present in the committed Option 1 manifest (`docs/phase6/blind_test_cohort.tsv` @ `888047d`) — at minimum `scope_rationale` (per §19.A), `scope_rejection_note` (sibling-record axis for §13.3 / §19.A rejections), per-source distribution fields (`pmid_group_size`, `bioproject_group_size`), and the §19.B tie-break selection rationale. Reconciliation with the committed Option 1 25-column schema — either extend with Option-2-only columns left blank for Option 1 rows, or maintain the two channels as separate manifest TSVs joined on `cohort_id` — is a foreseeable join at recording time, flagged here so it is not rediscovered then.

### 19.9 — Authority

§10 of this document permits amendments before assembly begins. The relevant assembly scope for §19 is Option 2 assembly, which has not begun. §15.4 explicitly defers operationalization of the §15 / §14 / §16 principle for Option 2 to "when Option 2 runs" — §19 is recorded immediately before Option 2 runs, satisfying that deferral on its own terms and consistent with §10's pre-registration commitment for the Option 2 channel.

**Drafted:** 2026-06-07 (post-Option-1-batch-1 commit `888047d`, pre-Option-2-query-execution).
**Trigger:** the §15.4 explicit deferral now becomes live: with Option 1 batch 1 recorded and Option 2 next on the work plan, the operationalization of §14 scope and §16 independence for the literature channel can no longer remain unspecified without contradicting the "declare-then-apply-uniformly" model.

## 20. Pre-assembly amendment 2026-06-08 — Option 2 §13.3 PubMed query strings revised after registered-phrase failure

**Status:** Pre-assembly amendment for the Option 2 literature channel. Option 2 discovery has NOT begun under the amended queries: at the time of drafting, the four §13.3-registered query strings have been executed verbatim (2026-06-07, recorded at `data/validation/option2/pubmed_query_findings.md`) and returned 4/4 zero literal-phrase hits; no candidate paper has been admitted to Option 2; the replacement query set defined below has been mechanics-validated for literal-match safety against PubMed (2026-06-08, recorded at `data/validation/option2/phrase_safety_check_paired.tsv`) but has NOT been executed as discovery. This amendment is recorded BEFORE the amended queries run as discovery, consistent with §10's pre-registration commitment.

This is the most selection-sensitive amendment in the project — it replaces the registered search terms that determine which papers can become Option 2 candidates, and it does so after a diagnostic revealed the originals failed. The framing below is correspondingly explicit about what keeps the replacement from being results-driven query-tuning: the replacement queries were chosen on a-priori field-vocabulary grounds before any candidate paper was inspected, the validation step retrieved hit counts only (no PMIDs, no titles, no abstracts), and the specific papers surfaced by the methods-validation diagnostic are quarantined and not used as a candidate pool.

### 20.1 — Why this amendment exists

**The trigger.** The four §13.3-registered PubMed query strings, executed verbatim 2026-06-07 against NCBI E-utilities (`esearch.fcgi`) with date window 2024/01/01 → 2026/06/07 and `datetype=pdat`, returned 4/4 zero literal-phrase hits. Recorded inline at `data/validation/option2/pubmed_query_findings.md`.

Two of the four registered phrases were not present in PubMed's phrase index. PubMed silently auto-expanded them into broader token-AND booleans:

- Query 1, `"MAG-guided cultivation"` — phrase not in index; auto-expanded to `"mag guided"[All Fields] AND (cultivation-stems)[All Fields]`; 0 hits even after broadening.
- Query 3, `"isolation following metagenomic analysis"` — phrase not in index; auto-expanded to `(isolate-stems) AND (follow-stems) AND (metagenome) AND (analysis-stems)`; returned 394 hits, of which 0/394 contain the literal §13.3 phrase in title or abstract (case-insensitive substring verification recorded in the findings).

The other two registered phrases (queries 2 and 4) are in PubMed's phrase index, ran as literal matches, and returned 0 hits each. The 0 results from queries 2 and 4 are honest literal-phrase results; the 0 from query 1 and the 394 from query 3 are PubMed's broader paraphrase, not the registered phrase. Under either reading, the literal §13.3 phrases matched nothing in the 2024-2026 window. The registered phrases did not match how the cultivation-pair literature in window describes the work.

**Why amend rather than declare a §13.3 shortfall.** A methods-validation diagnostic, recorded at `data/validation/option2/diagnostic_probe.md` and explicitly labeled `METHODS-VALIDATION DIAGNOSTIC ONLY. NOT §13.3 DISCOVERY. THE RESULTS BELOW ARE NOT A CANDIDATE POOL AND WILL NOT BE DRAWN FROM. NO INCLUSION JUDGMENT IS APPLIED TO ANY HIT SURFACED HERE`, was run after the 4/4-zero result to determine whether the result reflects (a) a near-empty field, (b) bad proxy phrases, or (c) PubMed phrase-index mechanics.

The diagnostic decisively ruled out (a). Broad probes returned non-zero populations (`cultivated AND "metagenome-assembled genome"` → 15 hits; `isolation AND "metagenome-assembled genome"` → 55 hits), confirming MAG+cultivation literature exists in the 2024-2026 window. A ground-truth check on a known cultivation-pair paper confirmed the same point decisively: PMID 40742112 (Kambara et al., *Applied and Environmental Microbiology* 2025-Aug, "First isolation of a methanotrophic Mycobacterium," from the JAMSTEC X-star institute) is in PubMed, in window, unambiguously a cultivation-pair paper in scope for Option 2, and contains NONE of the four §13.3 registered phrases anywhere in its title or abstract. The diagnosis was *predominantly (b) phrasing mismatch, with (c) phrase-index mechanics compounding for queries 1 and 3; (a) decisively ruled out*.

Declaring a §13.3 shortfall under these circumstances would record a false finding. The 4/4-zero result, treated as the field's true state, would tell a reviewer "no cultivation-pair work exists in 2024-2026 PubMed under the registered phrasing" — true on its face but misleading as a finding about the field, because the diagnostic establishes that the field exists and uses different vocabulary. The amendment honors §10's pre-registration commitment by replacing the failed phrases under an amendment record rather than silently re-querying; it does so because the alternative (recording a 4/4-zero result as the field's emptiness) would itself violate the pre-registration's deeper commitment to accurate findings.

### 20.2 — The clause: revised §13.3 PubMed query strings

§13.3's four registered query strings are SUPERSEDED by the four paired query strings below. The four originals remain on the §13.3 record (preserved append-only as historical pre-registration text, marked superseded-by-§20 in place; cf. §20.10) but are no longer the active discovery queries. The new registered query strings, executed against PubMed via NCBI E-utilities with date window 2024/01/01 → 2026/06/07 (`datetype=pdat`):

1. `"isolation and characterization"[Title/Abstract] AND ("metagenome-assembled genome"[Title/Abstract] OR "metagenomic"[Title/Abstract])`
2. `"first isolation"[Title/Abstract] AND ("metagenome"[Title/Abstract] OR "uncultured"[Title/Abstract])`
3. `("previously uncultured"[Title/Abstract] OR "previously uncultivated"[Title/Abstract]) AND ("isolation"[Title/Abstract] OR "cultivation"[Title/Abstract] OR "enrichment"[Title/Abstract])`
4. `"enrichment culture"[Title/Abstract] AND ("metagenome-assembled genome"[Title/Abstract] OR "metagenomic"[Title/Abstract])`

**Paired structure.** Each registered query combines a cultivation/isolation half with a metagenome/MAG/uncultured half — `AND`-joined across the pair, with within-half synonyms `OR`-joined. The pairing preserves §13.3's original "cultivation-PAIR" intent: a paper qualifies only if its title or abstract evidences both cultivation activity AND a genome-from-metagenomics relationship. The replacement is a vocabulary correction to the proxy strings; the underlying scope (cultivation papers anchored to MAG-from-metagenomics work in environmental, non-host Bacteria + Archaea) is unchanged.

**`[Title/Abstract]` field-tag operationalization.** Every quoted phrase in the four new queries carries an explicit `[Title/Abstract]` field tag. This is the §20 operational addition that addresses the (c) component of the original failure: field-tagging suppresses PubMed's silent phrase-index auto-expansion. With `[Title/Abstract]` applied to every quoted phrase, PubMed treats the phrase as a literal title-or-abstract substring rather than a candidate for token-broadening; absence of the phrase from PubMed's `quotedphrasesnotfound` warning list in the `esearch` JSON response is the audit signal that auto-expansion was suppressed and the literal match ran. The §13.3 execution step under the §20-amended queries MUST verify `quotedphrasesnotfound` is empty for every executed query and record the result inline with the §13.3 carry-forward.

### 20.3 — Diagnostic-hit quarantine

The methods-validation diagnostic recorded at `data/validation/option2/diagnostic_probe.md` incidentally surfaced specific papers — the 15-hit `cultivated AND "metagenome-assembled genome"` probe, the 55-hit `isolation AND "metagenome-assembled genome"` probe, the 394-hit auto-expansion of query 3, the 12-hit `Imachi H[Author]` probe (of which one, PMID 40742112, is the ground-truth Kambara/Imachi cultivation-pair paper), and various smaller-count probes (`"first cultivated"` → 9, `"first isolate"` → 54, etc.).

**These papers are QUARANTINED.** They are NOT a candidate pool. They were NOT used to select the §20 replacement queries. They WILL NOT be drawn from. The diagnostic's role was strictly to characterize whether the 4/4-zero result reflects a near-empty field or a phrasing mismatch; once that question was answered, the specific papers the diagnostic surfaced have no further role in the cohort.

The §20 replacement queries will run fresh as locked §13.3 discovery after §20 commits. Whatever they return is the Option 2 corpus, even if it differs from what the diagnostic incidentally surfaced — even if PMID 40742112 is not among the §20 returns, even if §20 returns a paper the diagnostic missed, even if the overlap is total or empty. The §20 corpus is defined by what the §20 queries return when executed after §20 is committed, NOT by what the diagnostic happened to put in front of the manuscript author's eye while answering the prior methodological question.

This quarantine is the substantive (not just rhetorical) guard against results-driven query-tuning. If §20 had allowed the replacement queries to be tuned to maximize capture of the diagnostic's specific hits, the amendment would be selecting the corpus by yield — the failure mode §13 was originally created to prevent (cf. §13.1's "generic web-search drift" framing). The quarantine makes the diagnostic methodological evidence, not a candidate sieve.

### 20.4 — How the replacement queries were chosen

The replacement queries were finalized on CONCEPTUAL / a-priori field-vocabulary grounds — the standard ways cultivation-pair work is described in microbiology and environmental microbiology prose. The phrasings predate the §20 amendment and predate the diagnostic; they are field-vocabulary terms — what microbiologists already write when describing this kind of work. Concretely:

- `"isolation and characterization"` is the canonical title-construct of a strain-description paper. Pairing with metagenome / MAG terms targets the cultivation-pair subset.
- `"first isolation"` is the canonical title-construct of a "first axenic culture of a previously uncultured group" paper. Pairing with metagenome / uncultured terms targets the MAG-anchored subset.
- `"previously uncultured"` / `"previously uncultivated"` are the canonical adjectives applied to organisms that cultivation-pair work brings into pure culture. Pairing the OR'd pair with isolation / cultivation / enrichment terms targets the cultivation-pair subset.
- `"enrichment culture"` is the canonical title-construct of an enrichment-derivation paper. Pairing with metagenome / MAG terms targets the genome-from-metagenomics subset.

These are vocabulary judgments by the manuscript author. They are NOT reverse-engineered from the diagnostic's specific hits — they are statements of what the field calls this kind of work, made before any §20 candidate paper has been inspected.

**Mechanics-only validation.** The four replacement queries were validated for MECHANICS ONLY against PubMed, recorded at `data/validation/option2/phrase_safety_check_paired.tsv` (executed 2026-06-08). The validation harness submitted each query with `retmax=0` — PubMed returned hit count, query translation, and the `quotedphrasesnotfound` warning list, but no PMIDs, titles, abstracts, journals, authors, or accession identifiers were returned on the wire, retrieved into Claude's context, or written to disk. The validation confirmed:

- All four queries: literal-match YES (`quotedphrasesnotfound` empty for every query).
- All four queries: no auto-expansion (the `[Title/Abstract]` tag suppressed PubMed's phrase-index broadening).
- All four queries: PubMed's `querytranslation` echoed the submitted Boolean AND / OR structure verbatim, with the date window AND'd in at the end — no re-parenthesization, no token expansion of any quoted phrase, no field-tag dropping.

The four queries returned **counts** only at validation: Q1 = 14, Q2 = 0, Q3 = 18, Q4 = 25. These counts are uncapped and undeduplicated across queries (dedup would require PMID retrieval and is deferred to the §13.3 discovery execution step under the amended queries). They are reported here as the mechanics-validation output, not as a candidate-corpus inventory.

**Yield-blindness.** The query set was finalized BLIND to which specific papers each query would surface. Counts and mechanics only. No paper was inspected during the §20 design step. No title was read. No abstract was read. No accession was retrieved. The selection of these four queries was therefore concept-first and yield-blind — the structural guarantee that §20 is a vocabulary correction rather than results-driven curation.

**Q2's zero is retained deliberately.** Query 2 — `"first isolation"[Title/Abstract] AND ("metagenome"[Title/Abstract] OR "uncultured"[Title/Abstract])` — returned 0 hits at mechanics validation. It is KEPT in the registered set anyway, on conceptual grounds: "first isolation" papers are a recognized class of cultivation-pair literature on their own merits, and pairing with metagenome / uncultured is the canonical metagenome-anchored qualifier; the query targets a distinct conceptual subset that the other three queries do not span. Dropping Q2 from the registered set on the grounds that it returned 0 at validation would be precisely the results-driven curation this amendment exists to avoid — dropping a zero-hit query because it returned zero is selection-by-yield, the failure mode in miniature. The 0 is recorded as the validated mechanics outcome — a real finding about this phrasing's literal-match yield in the 2024-2026 window — not a defect to curate away. The visible evidence that the registered set was NOT tuned to hit-yielding queries is that Q2 is in it. If §20 had been allowed to back-fit queries to a target yield, Q2 would not be there.

### 20.5 — Direction of change: vocabulary correction, applied uniformly

Neutral on scope and on the cultivation-PAIR principle. §20 is a phrase-set replacement at §13.3, and only at §13.3. The phrases that compose the discovery query are replaced because the original phrases failed to match how the literature in window describes the work; the principle the discovery query operationalizes — find papers documenting cultivation activity AND a MAG-from-metagenomics relationship within the §14 / §15 scope boundary — is unchanged, and no per-candidate quality rule is touched. §20.6 carries the per-section inventory of what is unchanged downstream of §13.3.

Same "declare-then-apply-uniformly" model as §14 / §15 / §16 / §17 / §18 / §19: the replacement queries are declared in this amendment and applied uniformly to the entire 2024-01-01 → 2026-06-07 window. No retroactive re-querying of any prior window. No subset-of-window or category-named variants. No mid-execution adjustments to the query strings once §20 is committed.

### 20.6 — What §20 does NOT change

- **§13.3 workflow downstream of the queries.** PMID dedup, abstract + parseable-accessions retrieval via `efetch`, human-judgment inclusion call by the manuscript author, verify-or-fall-back on cultivation conditions — all unchanged. Claude's role under §13.3 remains execute-dedup-surface; the inclusion call remains the manuscript author's, not Claude's.
- **§13.4 held-out threshold and dev-cohort reference standup.** Unchanged. The 168-genome dev-cohort sourmash sketch at `data/validation/dev_cohort_sketches_k31_s1000.zip` (k=31, scaled=1000) remains the reference for §13.4's > 95% ANI held-out check.
- **§19 Option 2 channel operationalization.** §19.A (per-paper scope rationale recorded under human judgment, §14 boundary applied through reading) and §19.B (mechanical per-PMID / per-BioProject independence check with parameterized N at execution) apply unchanged to whatever the §20-amended queries return.
- **§6 verification protocol** (including the §6-step-6 cultivation-paper add-on), **§15 domain restriction**, **§17 ANI alignment-fraction floor**, **§18.2.B CheckM2 binding gate.** All per-candidate quality rules apply to Option 2 candidates unchanged, as enumerated in §19.5.
- **§5 mix-target and §13.2 / §14.7 shortfall rule.** Unchanged. If the §20-amended queries produce fewer Option 2 candidates than the ~15-20 §5 target, the shortfall rule still governs: document the shortfall inline with the Option 2 batch verification record, do not relax §19.A scope or §19.B independence to make up the gap, do not broaden the §20 queries to category-named variants or post-hoc add a fifth query.
- **§10 pre-registration commitment.** Unchanged. §20 is itself the amendment record for the §13.3 query replacement, recorded before the amended queries run as discovery.
- **No-peeking rule.** Unchanged. No `cultureforge.py inspect` / scoring / prediction path runs on any Option 2 candidate prior to cohort lock, just as it has not run on any Option 1 candidate. The §20 mechanics-validation step retrieved counts and query translations only — no PMIDs, no titles, no abstracts — and therefore introduced no peeking exposure.

### 20.7 — Sequencing: §20 commits before discovery runs

§20 commits BEFORE the §13.3 discovery step is re-executed under the amended queries. The amendment locks the replacement query set first; only after §20 is on `origin/main` does the §13.3 discovery step execute the §20 queries, retrieve PMIDs + abstracts + parseable accessions via `efetch`, dedup, and surface the candidate list to the manuscript author for the §13.3 inclusion judgment + §19.A scope rationale + §19.B mechanical independence computation.

This is the same sequencing §13 / §14 / §15 / §16 / §17 / §18 / §19 followed: amend, commit, then run. A reviewer can verify by `git log` ordering that the §20 query strings landed on `origin/main` before any §13.3-amended carry-forward dated after this amendment was written.

### 20.8 — State at amendment time

- **Option 1 batch 1:** recorded. `docs/phase6/blind_test_cohort.tsv` carries 7 verified candidates (BT001–BT007) + 1 documented §13.2 comammox shortfall (BT008), committed at `888047d`, pushed to `origin/main`. Unaffected by §20.
- **§19:** committed at `9f13704` on `origin/main`. The §14-scope / §16-independence operationalization for the Option 2 channel applies to whatever the §20-amended queries return. Unaffected by §20.
- **Option 2 discovery (under §20-amended queries):** NOT begun. No §20 query has been executed as discovery. No Option 2 candidate paper has been surfaced under the §20 queries. No Option 2 candidate organism has been recorded. No FASTA downloaded for an Option 2 candidate. No skani / CheckM2 / `inspect` / scoring path run on any Option 2 candidate.
- **Pre-amendment carry-forward audit trail.** Untracked under `data/validation/option2/` (gitignored, never committed, never staged): `pubmed_query_findings.md` (§13.3 verbatim-query execution record), `diagnostic_probe.md` (methods-validation diagnostic), `pubmed_query_counts.tsv` / `pubmed_query_pmids.tsv` / `pubmed_hits.tsv` / `efetch_raw.xml` (raw execution artifacts from the 2026-06-07 §13.3 verbatim run), and `phrase_safety_check_paired.tsv` (§20 mechanics-validation TSV from 2026-06-08, counts and mechanics only). These artifacts are the audit trail for the §20 trigger and validation; they are NOT the corpus.
- **Diagnostic-hit quarantine reaffirmed.** Per §20.3, the diagnostic-surfaced material (the 15-hit / 55-hit / 394-hit sets, PMID 40742112, the Imachi-author hits, and all other diagnostic probe outputs) is QUARANTINED — not a candidate pool, not used to select the §20 replacement queries.
- **Manifest schema reconciliation still pending,** per §19.8. The Option 2 manifest row will introduce columns not present in the committed Option 1 manifest at `888047d` (at minimum `scope_rationale`, `scope_rejection_note`, `pmid_group_size`, `bioproject_group_size`, §19.B tie-break selection rationale). §20 does not resolve this — it remains a foreseeable join at Option 2 recording time.

### 20.9 — Authority

§10 of this document permits amendments before assembly begins. The relevant assembly scope for §20 is Option 2 assembly, which has not begun: no Option 2 candidate paper has been admitted under the §13.3-registered queries (the 4/4-zero result is the entirety of Option 2's pre-§20 recorded state); no Option 2 candidate organism has been recorded; no FASTA has been downloaded. §15.4's "operationalization … deferred to when Option 2 runs" framing applies symmetrically to query-string replacement: the trigger for replacement (the 4/4-zero literal-phrase result) materialized in the same pre-discovery window §15.4 anticipated, and §20 is recorded immediately before Option 2 runs under the amended queries.

**Drafted:** 2026-06-08 (post-§19 commit `9f13704`, post-2026-06-07 §13.3 verbatim-query execution returning 4/4 zero literal-phrase hits, post-methods-validation diagnostic, post-2026-06-08 mechanics-validation of the §20 replacement query set, pre-§20-amended discovery execution).

**Trigger:** the 4/4-zero literal-phrase result from executing §13.3's registered queries verbatim 2026-06-07 (`data/validation/option2/pubmed_query_findings.md`), in combination with the methods-validation diagnostic's confirmation that cultivation-pair papers exist in the 2024-2026 window (`data/validation/option2/diagnostic_probe.md`, including the PMID 40742112 ground-truth check), made silent re-querying impossible (would violate §10) and shortfall declaration false (the diagnostic disproved the field-emptiness reading). The amendment replaces the registered phrases under amendment record rather than tuning silently or recording a finding the diagnostic contradicts.

### 20.10 — Superseded §13.3 query strings (append-only record)

For audit-trail continuity, the four pre-§20 §13.3 registered query strings — registered at §13.3 drafting (2026-05-30), executed verbatim 2026-06-07, returning 4/4 zero literal-phrase hits — are preserved here verbatim:

1. `"MAG-guided cultivation"` — not in PubMed phrase index; auto-expanded to `"mag guided"[All Fields] AND (cultivability OR cultivable OR cultivate OR cultivated OR cultivates OR cultivating OR cultivation OR cultivations OR cultivator OR cultivators)[All Fields]`; 0 hits even after broadening.
2. `"successfully cultured" AND "metagenome-assembled genome"` — both phrases in index, literal match ran as `"successfully cultured"[All Fields] AND "metagenome-assembled genome"[All Fields]`, 0 hits.
3. `"isolation following metagenomic analysis"` — not in PubMed phrase index; auto-expanded to `(isolate-stems) AND (follow-stems) AND ("metagenome"[MeSH Terms] OR metagenome-stems)[All Fields] AND (analysis-stems)[All Fields]`; returned 394 broadened hits, 0/394 of which contain the literal phrase in title or abstract.
4. `"axenic culture" AND "previously uncultured"` — both phrases in index, literal match ran as `"axenic culture"[All Fields] AND "previously uncultured"[All Fields]`, 0 hits.

These four phrases are SUPERSEDED by the §20.2 replacement set. They are NOT deleted from §13.3, where they remain on the record as the pre-amendment registration; the in-place §13.3 supersession annotation (added in this same commit, immediately after the four phrases in §13.3) reads: *"Superseded by §20 (2026-06-08); the four original phrases above did not match field vocabulary in the 2024-2026 window — see §20 for the trigger, the replacement queries, and the diagnostic basis."*

The pre-§20 carry-forward artifacts under `data/validation/option2/` (the verbatim-query execution records and the methods-validation diagnostic) remain the audit trail for the supersession trigger.
