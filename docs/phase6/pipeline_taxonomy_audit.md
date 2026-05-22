# Pipeline Taxonomy & Quality-Tooling Audit

**Date:** 2026-05-17
**Repo HEAD:** 74e2951
**Task:** Read-only inspection — what taxonomic verification and quality-assessment tooling actually exists in the CultureForge pipeline, for blind-test cohort verification protocol pre-registration.
**Constraints honored:** Read-only. No installs, edits, or commits.

## Bottom line

The CultureForge pipeline has **no taxonomic classification step of any
kind** and **no operational genome-quality step**. CheckM2 is wired into
the code but is not installed here and has never been run on any genome
in the database. GTDB-Tk is entirely absent. The blind-test cohort
verification protocol cannot rely on in-pipeline taxonomy or QC — those
tools must be run externally or the protocol must use published
metadata.

---

## 1. GTDB-Tk: ABSENT

**Evidence:**

- `grep -rni "gtdb"` → 58 matches, **none** are GTDB-Tk invocation:
  - `docs/CLAUDE.md`, `docs/LIMITATIONS.md:453`, `docs/VALIDATION_SUMMARY.md:463`,
    `docs/phase5_0/predictions_audit.md:1636` — all **wishlist / future-work
    mentions** ("GTDB-Tk integration for phylogenetic distance estimation
    (U.x)"; "GTDB-Tk or similar … gating ANME mode by phylogeny").
  - `vendor/GenomeSPOT/genome_spot/taxonomy/taxonomy.py` (class
    `TaxonomyGTDB`) — this is the **vendored GenomeSPOT** library's helper
    that parses GTDB *metadata taxstrings* (`bac120_metadata.tsv.gz`) for
    its own model training/partitioning. It does **not** taxonomically
    classify a query genome; it maps known accessions to lineage strings.
- `find -name "*gtdb*"` (dirs and files) → **nothing** (no GTDB reference
  data, no `gtdbtk` package directory).
- `which gtdbtk` → **not in PATH**. `conda` / `pip` for gtdb → none
  (conda not available in this environment; pip has no gtdb).

**Conclusion:** GTDB-Tk is not installed, not vendored, not invoked, and
no GTDB classification reference data is present. The only "GTDB"
footprint is GenomeSPOT's internal taxstring parser, which is not a
classifier.

## 2. CheckM / CheckM2: PARTIAL (code-integrated, not installed, never run)

**Evidence — integration exists:**

- `run_checkm.py` — "Run CheckM2 (or CheckM1 fallback) on a genome FASTA
  and return quality metrics" (completeness, contamination,
  strain_heterogeneity, genome_size, gc_content, n50, checkm_version).
- `load_checkm.py` — loads CheckM metrics into the DB; defines a
  `genome_quality` table (`completeness`, `contamination`,
  `checkm_version`, `run_date`).
- `process_genome.py:306` `run_checkm2_if_available()` — step **[6/7]**
  of the pipeline, explicitly optional; logs "CheckM2 not installed —
  skipping (genome quality unknown)" when absent.
- `cultureforge.py --skip-checkm2` flag; report code prints "CheckM not
  available (genome stats only)" / "CheckM not run for this genome."
- DB schema confirms `genomes.completeness_pct`, `genomes.contamination_pct`
  ("CheckM, optional") and a dedicated `genome_quality` table.

**Evidence — not operational:**

- `which checkm2` / `which checkm` → **not in PATH**. conda/pip → none.
- DB census: `SELECT COUNT(*), COUNT(organism_id),
  SUM(completeness_pct IS NOT NULL) FROM genomes` → **168 genomes, 7 with
  organism link, 0 with CheckM completeness**. Not a single genome in the
  shipped database has CheckM-derived quality.
- `cultureforge.py` source comment: "most validation/blind genomes never
  had CheckM run."

**Conclusion:** CheckM2 is a designed-in but optional and currently
dormant step. The plumbing (runner, loader, schema, CLI flag) exists;
the binary does not, and no genome has ever been scored.

## 3. Existing taxonomy mechanism (how `genomes.notes` / species is populated)

There is **no automated taxonomy step**. The full pipeline
(`process_genome.py`) is:

1. Genome registration (gid ≥ 1000)
2. prodigal — protein prediction
3. gapseq — pathway / transporter annotation
4. GenomeSPOT — environmental envelope prediction
5. marker BLAST — diagnostic enzyme detection
6. CheckM2 — *optional* completeness/contamination QC
7. MeBiPred — *optional* metal-binding prediction

No step performs phylogenetic placement or taxonomic assignment.

Species/lineage information enters the DB by **one of two non-automated
routes**:

- **Dev cohort (curated):** the `organisms` table, populated from BacDive
  (`organism_to_bacdive`, `organism_to_published_media` tables). Only **7
  of 168** genome rows carry an `organism_id` FK; the rest have
  `organism_id = NULL`.
- **User-loaded genomes:** `register_genome.py` takes a free-text
  `notes` argument (e.g. `notes="User-loaded genome: Wolinella
  succinogenes"`) and an optional `organism_id` "typically NULL". The
  species label is whatever the operator types — there is no
  verification of it against the sequence.

So "taxonomy" in CultureForge is **operator-asserted free text**, not
computed.

## 4. How the 2026-05-05 audit correction discovered the contamination

This is the de facto "verification machinery" — and it is **not a tool**.

- gid 30 (`GCF_002443295.1`, *Ca.* Scalindua japonica MAG) previously
  held **Salmonella** sequence data
  (`docs/phase5_0/a4_inspection_report.md:26,206,344`).
- Detection mechanism (`docs/LIMITATIONS.md:227`, Phase 3.4 addendum):
  the **nrfA marker-BLAST cross-reactivity scan** surfaced a Scalindua
  proteome hit at **99.8% identity to *Salmonella enteritidis* nrfA**
  (100% qcov, bs=1004). A Brocadiaceae MAG sharing 99.8% identity with a
  Gammaproteobacterial enzyme is **biologically impossible**, so a human
  reading the marker-BLAST output inferred Enterobacteriaceae DNA
  contamination of the MAG assembly.
- Correction was **manual**: the MAG was re-downloaded and re-processed
  (audit note "2026-05-05: gid 30 previously held Salmonella data;
  re-downloaded + re-processed").
- git log 2026-05-01…05-10 shows only repo-reorg/release commits — the
  audit correction is recorded in docs, not as a tooling commit.

**Key point:** the contamination was caught by **human
biological-plausibility review of marker-BLAST output**, not by GTDB-Tk,
CheckM, or any automated check. `docs/LIMITATIONS.md:227` explicitly
states that an automated "cross-phylum high-identity sanity check (flag
markers hitting >95% identity to a phylogenetically distant reference)"
is a **deferred Phase 3 candidate** — i.e. **not implemented at HEAD**
(grep for such a check in `*.py` finds only the unrelated pmoA×amoA
calibration comments, no contamination guard).

## 5. Available alternatives (if GTDB-Tk / CheckM2 unavailable)

None installed in this environment:

| Tool | Status |
|------|--------|
| `mash` | not in PATH |
| `dRep` | not in PATH |
| `busco` / `busco5` | not in PATH |
| `dfast_qc` | not in PATH |
| `fastANI` | not in PATH |
| `skani` | not in PATH |

No genome-distance, completeness, or classification alternative is
available locally. The only sequence-comparison tooling the pipeline
itself uses is **BLAST against the curated `data/diagnostic_markers/`
reference sets** (`run_marker_blast.py`).

## 6. Recommendation — what verification tooling we actually have

For the blind-test cohort, the **honest inventory of in-repo
verification capability** is:

1. **Taxonomy:** none in-pipeline. The protocol's "verify taxonomic
   assignment via GTDB-Tk" step (design doc §6.5) **cannot be satisfied
   by the existing pipeline**. Options: (a) run GTDB-Tk externally as a
   documented pre-processing step, or (b) rely on the **published lineage
   from each MAG's source paper/NCBI** with a provenance note — the
   design doc already allows this fallback and it is the only one
   currently executable.
2. **Quality (completeness/contamination):** CheckM2 is code-ready but
   not installed and never run. Either install CheckM2 to use the
   existing `run_checkm.py` → `genome_quality` path, or rely on
   **published CheckM2 scores** from the source MAG paper (design doc
   §6.2 already permits "use published quality scores if CheckM2-derived").
3. **Reference-set non-overlap:** **this we genuinely have.**
   `run_marker_blast.py` BLASTs candidate proteomes against all
   `data/diagnostic_markers/*_refs.fasta`. The design doc's §6 step-4
   non-overlap screen (flag >95% identity hits) is executable today and
   is also the exact mechanism that caught the 2026-05-05 contamination.
4. **Contamination sanity check:** only **manual** biological-plausibility
   review of marker-BLAST cross-hits. No automated cross-phylum guard
   exists; if the protocol depends on detecting contaminated MAGs, that
   review must be a documented manual step, not an assumed tool.

**Net:** pre-register the protocol around what exists — marker-BLAST
non-overlap screening (in-pipeline) plus **published, provenance-checked
taxonomy and CheckM2 scores** from source papers — and explicitly flag
GTDB-Tk classification and in-pipeline CheckM2 as **external/optional
steps not currently part of CultureForge**, so the methods section does
not over-claim automated verification the codebase does not perform.

---

*Inspection performed read-only at HEAD 74e2951. No code, database,
pathway definitions, or marker sets modified. No commits.*
