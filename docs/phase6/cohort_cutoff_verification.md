# Cohort Deposit-Date Cutoff Verification

**Date:** 2026-05-17
**Repo HEAD:** 74e2951 (post Task 1 overnight-docs commit; reference data unchanged since e3c4123)
**Task:** SESSION_TASKS_2026-05-17.md Task 2
**Status:** Read-only verification. No code, marker DB, or pathway definitions modified.

## Question

Is "MAG deposited after 2026-01-01" a safe non-overlap criterion for the
blind-test cohort? The stated risk: reference sequences in
`data/diagnostic_markers/*_refs.fasta` may have been drawn from UniProt
entries whose sequence content was created or updated in 2026, in which
case even a 2026-deposited MAG could already be represented in a marker
reference set (and would therefore not be a true blind test).

## Method

1. Enumerated all `*_refs.fasta` files and parsed every UniProt accession
   from the FASTA headers (standard `>sp|ACC|...` / `>tr|ACC|...` format).
2. Queried the UniProt REST API (`/uniprotkb/<acc>.json`) and recorded
   three `entryAudit` fields per accession:
   - `firstPublicDate` — when the entry first entered UniProt
   - `lastSequenceUpdateDate` — when the **sequence content** last changed
   - `lastAnnotationUpdateDate` — when **metadata only** last changed
3. The overlap-relevant dates are `firstPublicDate` and
   `lastSequenceUpdateDate`. `lastAnnotationUpdateDate` is **not** an
   overlap signal: UniProt routinely re-annotates decades-old entries
   without touching the sequence, so a 2026 annotation date on a 2010
   sequence carries no risk that the sequence derives from a 2026 MAG.
4. Coverage was made **exhaustive**, not sampled: the initial run sampled
   5 accessions per file (140 unique), and a follow-up run covered the
   remaining 21, so **all 161 unique accessions across all 32 files were
   checked**. Rate-limited at 0.25 s between calls; zero request errors.

## Marker files inspected

**32** reference files in `data/diagnostic_markers/`:

```
acsB_cdhC, amoA_archaeal, amoA, aprAB, autotrophy, cooS_cdhA, cyc2,
dsrAB, hao, hdh, hzsA, mcrA, mcrBG, mmoX, mtrC_omcB, nifH, nosZ, nrfA,
nxrA, pmoA, psaA_psbA, pscA_fmoA, pufLM, qmoA, rdhA, rhodopsin, sor,
soxB, terminal_oxidases, tetH, tqoDoxA, tqoDoxD
```

162 header records, **161 unique accessions** (one accession appears in
two files). All 161 were queried — full coverage, not a sample.

## Accessions sampled per file

Sampling design (superseded by exhaustive coverage, retained for the
record): 5 accessions per file selected at evenly spaced indices
(first, ~¼, ~½, ~¾, last); files with ≤5 accessions covered in full.
Files have 3–9 accessions each (median ~5), so the initial sample
already covered ~87% of unique accessions; the remaining 21 were then
checked individually. Net: **100% of unique accessions verified.**

## Critical result — sequence dates in 2025 or later

**Zero accessions have a `firstPublicDate` or `lastSequenceUpdateDate`
in 2026.** The latest sequence date anywhere in the reference set is
**2025-10-08**, on four accessions:

| Accession | File | Organism | firstPublic | lastSeqUpdate |
|-----------|------|----------|-------------|---------------|
| A0ABM8RCK9 | nxrA_refs.fasta | *Nitrospira defluvii* | 2025-10-08 | 2025-10-08 |
| A0ABN8AJF8 | nxrA_refs.fasta | *Ca.* Nitrotoga arctica | 2025-10-08 | 2025-10-08 |
| A0ABQ0K0A8 | hzsA_refs.fasta | *Ca.* Brocadia sinica JPN1 | 2025-10-08 | 2025-10-08 |
| A0ABR9NUT4 | mtrC_omcB_refs.fasta | *Geobacter anodireducens* | 2025-10-08 | 2025-10-08 |

These four are recent UniProt **TrEMBL ingest records** for sequences
from organisms whose genomes were published years earlier (*N. defluvii*
2010, *Brocadia sinica* ~2014, *G. anodireducens* 2015, *Nitrotoga
arctica* ~2007). The 2025-10-08 date is when UniProt released that
particular TrEMBL accession, not when any source genome was deposited.
**All four predate the 2026-01-01 cutoff**, so even under the most
conservative reading they cannot derive from a post-2026-01-01 MAG.

`lastAnnotationUpdateDate` was 2025+ for 139 of 161 accessions — but
this is the routine UniProt-wide re-annotation released ~2026-01-28
(metadata only). Every one of those 139 retained a
`lastSequenceUpdateDate` in its original pre-2025 year, so the sequence
content is unchanged and predates the cutoff. This is the expected,
benign pattern and is **not** an overlap signal.

## A1 archaeal AOA references (explicit check)

The six accessions added 2026-05-15 in this session
(`amoA_archaeal_refs.fasta`):

| Accession | firstPublic | lastSeqUpdate | lastAnnUpdate |
|-----------|-------------|---------------|---------------|
| D9J260 | 2010-10-05 | 2010-10-05 | 2026-01-28 |
| D9J261 | 2010-10-05 | 2010-10-05 | 2026-01-28 |
| F4N9Y5 | 2011-06-28 | 2011-06-28 | 2026-01-28 |
| A0A060HNG6 | 2014-09-03 | 2014-09-03 | 2026-01-28 |
| A0A5B8ZQK3 | 2019-11-13 | 2019-11-13 | 2026-01-28 |
| A0A654M1Z2 | 2020-04-22 | 2020-04-22 | 2026-01-28 |

**All six have sequence content from 2010–2020.** Only their annotation
metadata was refreshed in the 2026-01-28 UniProt re-annotation. Adding
these accessions to the repo on 2026-05-15 introduced **no 2026 sequence
material** — they are old, well-characterized AOA reference sequences.
The A1 references are safe under the 2026-01-01 cutoff.

## pathway_definitions.json

No version stamps, retrieval dates, or external-data provenance fields.
The only occurrences of "2024/2025/2026" are inside human-readable
`rationale` / `limitation_summary` prose describing **internal CultureForge
phase work** (e.g. "Phase 6 A4", "pre-2026-05-05 gid-30 ... MAG"). None
of these reference dated external sequence material that could enter a
reference set. No dated material of concern.

## git log — reference data added since 2026-01-01

```
git log --since="2026-01-01" --diff-filter=A -- \
  'data/diagnostic_markers/*' 'data/pathway_definitions.json'
```

Two commits added reference data in 2026:

- **4be3d23** — "A1: split archaeal AOA detection into amoA_archaeal
  marker + override" (2026-05-15). Added `amoA_archaeal_refs.fasta`.
  Its six accessions are individually verified above: all sequence
  dates 2010–2020. Safe.
- **5fc529c** — "Initial public release of CultureForge
  (pre-publication)". The original bulk import of all reference data.

No other 2026 additions. No reference file was added or its sequences
modified by a commit sourcing 2026 sequence material.

## Verdict

**SAFE.** 2026-01-01 is a sound non-overlap cutoff for the blind-test
cohort, on the following exhaustively verified basis:

1. **Zero of 161 unique reference accessions** have a `firstPublicDate`
   or `lastSequenceUpdateDate` in 2026. The latest sequence date in the
   entire reference set is 2025-10-08 (4 accessions), all comfortably
   before the cutoff.
2. A reference sequence can only overlap a post-2026-01-01 MAG if its
   UniProt sequence content was created/updated on or after that MAG's
   deposit (2026+). No such accession exists. The criterion is
   therefore logically sound, not merely empirically clean.
3. The 139 accessions with 2026 annotation dates had **metadata only**
   refreshed; sequence content is unchanged and predates the cutoff.
4. The six 2026-05-15-added A1 AOA references carry 2010–2020 sequence
   content — the repo addition introduced no new-era sequence data.
5. `pathway_definitions.json` carries no dated external provenance.
6. Coverage is **exhaustive** (all 161 unique accessions, all 32
   files), so this verdict carries no "sample only" caveat.

No alternative cutoff or accession-exclusion list is required. The
mechanical reference-set non-overlap check in the design document
(`§3`, `§6` step 4 — sequence-level identity screen of each candidate
genome against `*_refs.fasta`) remains the appropriate defense-in-depth
backstop and should still be run per cohort candidate.

---

*Verification performed read-only. No edits to code, marker databases,
or pathway definitions. No commits made in this task.*
