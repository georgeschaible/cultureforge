# CultureForge Verification Discipline

**Status:** Permanent project artifact. Required reading for all Claude Code sessions doing curation, marker reference work, or external-identifier handling.

**Established:** 2026-05-04 (Phase 5.0 prep)

---

## Purpose

Prevent fabrication of external identifiers (NCBI accessions, DSMZ media, BacDive IDs, marker reference accessions) in project artifacts. The discipline below applies to every future task that produces or modifies external identifiers.

The rules are not aspirational. They are operational. A future Claude Code session that violates these rules is operating outside the project's quality-assurance contract, and any artifacts it produces are presumed compromised until verified.

---

## Cautionary tale: the 47% error rate

In Phase 4.1, an LLM-compiled candidate list of ~47 NCBI genome accessions was added to a project TSV without verification. When the list was checked post-creation against NCBI, **22 of 47 entries (47%) pointed to completely different organisms** than the TSV claimed:

- *Pseudomonas stutzeri* accession used for an unrelated *Burkholderia*
- A "Halorubrum lacusprofundi" entry whose accession returned a *Desulfobacter*
- Sulfur oxidizers replaced by gut commensals
- Cyanobacteria replaced by sulfate reducers
- Thermophilic Aquificales replaced by mesophilic Pseudomonadales

The error pattern was insidious because the fabricated accessions all had **plausible format** (`GCF_XXXXXXX.X`, `NC_XXXXXX.X`) — they could not be filtered by syntax. They could only be detected by querying NCBI for each one. Every fabricated accession was a real assembly belonging to a different organism, not a syntactically invalid string. The LLM produced format-correct hallucinations indistinguishable from valid entries.

Catching this required running every accession through `datasets summary genome accession` and comparing the returned organism name against the TSV's organism column. The cost: hours of post-creation cleanup, several rounds of substitution, plus the broader trust cost of having to reconfirm every prior claim about identifiers.

A second incident in early Phase 5.0 curation surfaced one additional fabricated accession (Desulfobacter hydrogenophilus → real accession was for Halorubrum lacusprofundi). That was caught by the same post-hoc verification, but only because the operator was already in a verification mindset.

**The lesson is durable: never trust an LLM-generated identifier without verification against the authoritative source.** This applies to identifiers from Claude Code sessions including the current one. Memory-recall identifiers are not allowed; database lookup is the only acceptable input.

---

## The Rules

### Rule 1 — Verify external identifiers at creation

Every external identifier written to a project file must be verified before writing using an authoritative source. **Verification happens in the same task that produces the identifier**, not as a separate post-creation pass.

| Identifier type | Authoritative source | Verification command |
|---|---|---|
| NCBI assembly accession (GCF/GCA) | NCBI Datasets | `datasets summary genome accession "<accession>"` |
| NCBI nucleotide accession (NC_ / NZ_) | NCBI Entrez | `efetch -db nuccore -id "<accession>" -format gb \| head -20` |
| NCBI Taxonomy ID | NCBI Taxonomy | `datasets summary taxonomy taxon "<taxid>"` |
| NCBI protein accession (marker references) | NCBI Entrez | `efetch -db protein -id "<accession>" -format gp \| head -20` |
| NCBI gene accession | NCBI Datasets | `datasets summary gene accession "<accession>"` |
| UniProt accession | UniProt REST API | `curl -fsS "https://rest.uniprot.org/uniprotkb/<accession>.json" \| jq .organism` |
| DSMZ medium number | MediaDive | manual web lookup at https://mediadive.dsmz.de/medium/<number> |
| BacDive ID | BacDive | manual web lookup at https://bacdive.dsmz.de/strain/<id> |
| Pfam ID | Pfam (InterPro) | manual lookup at https://www.ebi.ac.uk/interpro/entry/pfam/<id> |
| KEGG ID | KEGG | manual lookup at https://www.genome.jp/dbget-bin/www_bget?<id> |
| ATCC strain number | ATCC | manual lookup at https://www.atcc.org/products/<id> |
| Pathway / paper citation | published literature | DOI lookup; verify the paper exists and discusses the cited topic |

For automated verification (NCBI / UniProt), the command should run cleanly and the response parsed for the expected organism / function / product. For manual-lookup identifiers (DSMZ media, BacDive, etc.), the prompt should explicitly acknowledge the manual step rather than fabricate a value.

### Rule 2 — Verification produces machine-readable evidence

Verification output is captured in a structured file alongside the project artifact. For TSVs, every accession-bearing row has a corresponding entry in a verification log with this format:

```
identifier	authoritative_source_response	expected_value	match_status	verified_at
GCF_000005845.2	Escherichia coli str. K-12 substr. MG1655	Escherichia coli K-12 MG1655	OK	2026-05-04T08:30:00Z
GCF_000012605.1	Hydrogenovibrio crunogenus XCL-2	Thiomicrospira crunogena XCL-2	OK_RENAME	2026-05-04T14:32:00Z
GCF_FAKE_999.1	(no records returned)	Methanopyrus kandleri AV19	FAIL_NOT_FOUND	2026-05-04T14:35:00Z
```

`match_status` values:

| Value | Meaning | Action |
|---|---|---|
| `OK` | Expected and actual match exactly | Accept |
| `OK_RENAME` | Genus or species was renamed since deposit; document the rename | Accept; annotate the rename in the artifact's notes column |
| `OK_STRAIN_DROPPED` | NCBI returned organism without strain detail; metadata confirms strain | Accept |
| `OK_SUBSPECIES_DROPPED` | NCBI returned without subspecies/serovar; verifiable from metadata | Accept |
| `FAIL_NOT_FOUND` | Identifier doesn't exist or is retracted | Document as failed lookup; do NOT write to artifact |
| `FAIL_WRONG_ORGANISM` | Identifier returns a fundamentally different organism | Document as failed lookup; do NOT write to artifact |

### Rule 3 — Verification is not deferred to user review

Future Claude Code sessions cannot deliver an artifact and ask the user to "please verify these accessions yourself." The verification is part of the task, not an offload. The user reviews verified output, not raw output.

If verification cannot be automated (e.g., DSMZ media lookups currently require web access that the sandbox doesn't have), the artifact must explicitly flag entries with `VERIFY — manual lookup required` rather than fabricate values. The fix is the user (or a future Claude Code session with web access) performs the manual lookup; the fix is NOT writing a guess in the meantime.

### Rule 4 — Failed lookups are documented, not guessed

If verification finds an identifier doesn't exist, has been retracted, points to a different organism, or otherwise can't be confirmed, the entry is **not** written to the project artifact. The failure is documented with:

- What was searched (taxon string, accession queried)
- What was returned (raw response or "no records")
- Why it failed (deprecated, wrong organism, no genome assembly, etc.)
- Action taken (substitute with verified alternative, drop from list, defer)

Substitutions are documented with explicit reasoning and the substitute is verified using the same workflow before replacing the failed entry.

### Rule 5 — Verify before reuse

When existing project artifacts (test set, sentinels, marker references) are referenced or extended, the underlying identifiers are **re-verified, not assumed correct from prior work**. The Phase 5.0 audit task does this for the existing CultureForge state. Future audits should do the same when extending established lists.

---

## Marker curation specifics

For curating new diagnostic marker reference protein sequences in future Phase 5.1+ work, additional rules apply:

1. **Test-set exclusion enforcement.** Reference protein sequences MUST come from organisms NOT in any of:
   - The 26-organism dev/blind test set (gids 7-32)
   - The 4 sentinels (gids 900-903)
   - The 143-organism Phase 5.0 expanded test set
   - The held-out bin.020 ST-3 (Thiovulum)

   The single source of truth for the exclusion list is `data/diagnostic_markers/REFERENCE_CURATION.md`. Future marker curation cross-checks every candidate accession against this list before adding.

2. **Per-marker verification log.** Each new or revised marker reference set carries a verification log documenting:
   - Search queries used to find candidates
   - Candidates considered (verified accessions returning the expected protein)
   - Candidates rejected (with reason: in test set, wrong protein, low quality, etc.)
   - Final selection rationale

3. **Threshold derivation requires empirical separation gap analysis.** The pident / qcov / evalue thresholds for a marker are derived from:
   - Best self-hit pident across the marker reference set (intra-marker conservation floor)
   - Best cross-reactivity pident against the test set (heterologous-marker ceiling)
   - The empirical gap between these two distributions

   Arbitrary defaults like "60% pident" are not acceptable thresholds. The threshold must sit in the empirical gap, derived from a documented cross-reactivity scan.

4. **Sentinel validation when no test-set genome covers the new capability.** A new marker that introduces a new capability requires sentinel validation against a named-strain genome (loaded as gid >= 900, excluded from V12 by hardcoded ORGANISMS list). The sentinel result is documented in the marker's curation log.

---

## Audit cadence

The verification discipline applies forward (every new artifact). It also requires periodic re-audit of existing artifacts:

- **Test set + sentinel genome accessions**: audited at Phase 5.0 start; re-audit on any major test-set change (e.g., when expanded test sets are added in Phase 5.0+)
- **Marker reference FASTAs**: sampled audit at Phase 5.0 start; comprehensive audit only if sampling reveals systemic issues (>15% failure rate)
- **Pathway definitions JSON**: audited when capability detection logic changes
- **DSMZ medium / BacDive ID references in TSVs**: re-checked when external databases publish breaking changes (rare)

The Phase 5.0 audit task is the first systematic application of Rule 5 to the project. Subsequent audits at Phase 6, 7, etc., apply the same workflow to whatever new artifacts have accumulated.

---

## What this discipline does NOT cover

These categories are project-internal and don't require external verification:

- **Internal IDs** — gids, marker_id sequences, prediction_confidence row IDs. These are project-internal and assigned by SQLite auto-increment or explicit insertion.
- **Cultivation parameters** (temperature, pH, salinity, atmosphere) when sourced from a named publication — the citation is the verification. The parameter value is not separately verifiable against an authoritative database in most cases.
- **File paths in the working directory** — these are environment-specific and not portable; verification of file existence at runtime is sufficient.
- **In-code constants** (thresholds, weights, biomass templates) — these are derived from project work, not external identifiers.

---

## Operational summary

> Before writing any external identifier (NCBI accession, DSMZ medium, BacDive ID, marker reference, etc.) into a project artifact, verify it against the authoritative source. Capture the verification evidence. If verification fails, document and don't write. If verification cannot be automated in the current environment, flag explicitly rather than guess.

The 47% error rate is the empirical floor for what happens when this rule is not followed. The cost of verification is small relative to the cost of cleanup.

---

## Citation history

The discipline is named after two specific incidents:

1. **Phase 4.1 candidate list incident (2026-05-03)** — 22 of 47 LLM-generated NCBI accessions pointed to wrong organisms. Caught by post-hoc verification.
2. **Phase 5.0 curation Desulfobacter hydrogenophilus incident (2026-05-04)** — fabricated accession duplicated against an unrelated archaeon. Caught by duplicate-detection pass.

Both incidents are documented in their respective phase progress logs (`docs/PROGRESS.md`). Future incidents that reveal new failure modes should be added to the cautionary-tale section above to keep the document current.
