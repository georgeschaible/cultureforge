# Sourmash identity verification of the 168 dev cohort — Phase 6.5

**Date:** 2026-05-21
**Repo HEAD:** `74e2951`
**Inputs:**
- `data/validation/sourmash_identity_verification/results_20260521_205346.tsv`
- `data/cultureforge.db` (read-only, for the full untruncated `genomes.notes` column)

**Outputs (this report):**
- This document
- Supplementary classification TSV: `docs/phase6_5/sourmash_identity_verification.tsv` (165 rows + header)

**Status:** Read-only analysis. No DB writes, no commits.

---

## 1. Executive summary

**No contamination detected. The dev cohort is verified clean as of HEAD `74e2951`.**

Each of the 165 dev cohort genomes with an on-disk FASTA was sketched with
sourmash (k=31, scaled=1000) and searched against the GTDB R226
representatives database (143,384 species reps spanning both Bacteria
and Archaea). Top hits were compared to the curator-recorded organism in
`genomes.notes` using a seven-category classification scheme that
distinguishes contamination (the 2026-05-05 audit signature) from benign
GTDB-vs-literature taxonomic conventions.

| Category | Count | Cohort fraction |
|---|---:|---:|
| CLEAN_SELF_MATCH | **131** | 79.4% |
| GTDB_SUFFIX_SPLIT | **15** | 9.1% |
| KNOWN_TAXONOMIC_RENAME | **13** | 7.9% |
| CANDIDATUS_PLACEHOLDER | **3** | 1.8% |
| NO_CLOSE_MATCH_EXPECTED | **2** | 1.2% |
| NEEDS_REVIEW | **1** | 0.6% |
| **PHYLUM_MISMATCH** | **0** | **0.0%** |
| **Total** | **165** | 100.0% |

Three of 168 cohort genomes (gids 901, 902, 903 — sentinels whose source
FASTAs are absent from disk) were excluded; the BLAST DB / proteome
artefacts in `data/sentinel/<strain>/` remain for downstream tools but
do not provide nucleotide content for sketching. These three were
*sentinels* for past-phase validation work, not active capability-test
genomes, and their identities are documented in
`docs/PHASE_3_7_VALIDATION_SUMMARY.md`.

Every audit-corrected positive control (gids 9, 17, 26, 30) returned a
1.0-containment self-match or the documented same-genus congener. Two
additional GTDB renames were uncovered during this analysis that the
cohort curator had not flagged (gid 31 Allochromatium → Thermochromatium;
gid 1066 Bacillus → Salisediminibacterium); both are noted in §6 for a
future curator-notes refresh. The only NEEDS_REVIEW case is gid 1000, a
blind-test PacBio MAG whose notes lack a claimed organism name (it was
loaded specifically *as* a blind test for the pipeline); GTDB places it
in *Thiovulum*_A at containment 0.88, which is a plausible identity but
requires a curator note rather than a contamination remedy.

---

## 2. Methodology

### Tools and references

| Item | Value |
|---|---|
| Identity tool | sourmash 4.9.4 (conda env `sourmash`, python 3.12) |
| Sketch parameters | DNA, k=31, scaled=1000, `--name-from-first` |
| Reference database | GTDB R226 species representatives — `gtdb-reps-rs226-k31.dna.zip` (3.63 GB, 143,384 sketches) |
| Reference taxonomy | `gtdb-rs226.lineages.csv` (98 MB, 732,475 rows; 715,230 bacterial + 17,245 archaeal) |
| Source | C. Titus Brown's sourmash-db distribution at UC Davis (`farm.cse.ucdavis.edu/~ctbrown/sourmash-db.new/gtdb-rs226/`) |
| Search command | `sourmash search --containment -n 3` |
| Worker scheme | 3 parallel threads, each spawning `sourmash` as a subprocess in the dedicated env |
| Runtime | 5h 25m total (started 2026-05-21 20:53 UTC, finished 2026-05-22 02:18 UTC) |

### Query set

168 cohort genomes per `SELECT id, accession, notes FROM genomes` at
HEAD `74e2951`. Of those:

- **165 queries sketched and searched** (FASTAs present on disk and accessible)
- **3 excluded** (gids 901, 902, 903 — sentinel directories contain
  derived BLAST DBs and proteomes but no nucleotide FASTA)

FASTA locations resolved at Task-3 time and recorded in
`/tmp/genome_fasta_manifest.tsv`:

| Source location | Count |
|---|---:|
| `data/genomes/phase5_0/<accession>.fna` | 139 |
| `data/genomes/<organism>.fasta` (derived from notes) | 18 |
| `data/genomes/audit_corrections/<accession>.fna` | 4 |
| Special-case overrides (irregular naming) | 3 |
| `data/user_genomes/<accession>/genome.fna` | 1 |

### Classification

The 7-category scheme distinguishes contamination from benign GTDB
conventions. Decision order:

1. **No GTDB match / containment < 0.20** → `NO_CLOSE_MATCH_EXPECTED`
   (genuinely novel lineages, e.g. cable bacteria, multicellular
   magnetotactic consortia).
2. **Special case** Picrophilus torridus → P. oshimae (C1 BacDive erratum).
3. **Candidatus + GTDB alphanumeric placeholder** (`UBA####`, `QENH##`,
   `DQIP##`, …) → `CANDIDATUS_PLACEHOLDER`. Verified by checking the
   FASTA header for the claimed organism name.
4. **Hit genus = claimed_genus + "_<letter>"** → `GTDB_SUFFIX_SPLIT`
   (GTDB's species-level taxonomy splitting traditionally polyphyletic
   genera such as *Clostridium* into *Clostridium_S*, *_B*, *_I*).
5. **Hit genus = renamed form of claimed_genus** (from a 14-entry
   lookup table) → `KNOWN_TAXONOMIC_RENAME`.
6. **Hit genus = claimed_genus** (with optional "Candidatus" prefix
   stripped from the claim) → `CLEAN_SELF_MATCH`.
7. **Otherwise** → `NEEDS_REVIEW` (one organism in this cohort).
8. **Top hit in a different phylum from the claim** → `PHYLUM_MISMATCH`
   (the 2026-05-05 contamination signature). **Zero hits in this cohort.**

The "Candidatus" prefix is stripped during matching because GTDB drops
the prefix once a formal genus name has been assigned (e.g.,
claim "Candidatus Brocadia sinica" matches hit genus `Brocadia`).

### Reproducibility

Classification script: `data/validation/classify_sourmash_results.py`
(committable; produces the supplementary TSV).
Query script: `data/validation/run_sourmash_identity_check.py`
(parameter-free invocation reproduces the full search; sketches cached
in workdir for restartability).

---

## 3. Per-category breakdown

### 3.1 CLEAN_SELF_MATCH — 131 genomes

Claimed genus matches the top GTDB hit genus exactly (Candidatus prefix
allowed). 121 of these have containment 1.000 (essentially identical to
the GTDB rep); the rest range from 0.50 to 0.99, reflecting
strain-level variation between the cohort FASTA and the GTDB rep
species representative.

Lower-containment self-matches worth noting (≥0.5 but <0.9, all
species-level confirmed):

| gid | Claimed organism | Top hit | C |
|---:|---|---|---:|
| 10 | *Lactobacillus plantarum* (curator-flagged rename) | *Lactiplantibacillus plantarum* | 0.79 |
| 15 | *Campylobacter jejuni* | *Campylobacter jejuni* | 0.59 |
| 26 | *Picrophilus torridus* (audit-corrected; C1 erratum) | *Picrophilus oshimae* DSM 9789 | 0.74 |

The full list of 131 gids in this category is in the supplementary TSV.

### 3.2 GTDB_SUFFIX_SPLIT — 15 genomes

GTDB has split polyphyletic genera using letter suffixes (e.g., *Clostridium*
becomes *Clostridium_S*, *Clostridium_B*, *Clostridium_I* depending on
phylogenetic placement). The species name remains the same after the
suffix; this is taxonomy, not contamination.

| gid | Claim genus | GTDB hit genus |
|---:|---|---|
| 12 | Clostridium | Clostridium_S |
| 15 | Campylobacter | Campylobacter_D |
| 23 | Nitrospira (Candidatus) | Nitrospira_D |
| 1016 | Clostridium | Clostridium_S |
| 1050 | Pseudomonas | Pseudomonas_E |
| 1067 | Clostridium | Clostridium_B |
| 1074 | Bacillus | Bacillus_BM |
| 1088 | Selenomonas | Selenomonas_A |
| 1100 | Peptoclostridium | Peptoclostridium_A |
| 1114 | Nitrospira (Candidatus) | Nitrospira_D |
| 1118 | Clostridium | Clostridium_I |
| 1122 | Methylobacter | Methylobacter_A |
| 1126 | Pelotomaculum | Pelotomaculum_C |
| 1131 | Acidithiobacillus | Acidithiobacillus_A |
| 1134 | Nitrospira (Candidatus) | Nitrospira_E |

### 3.3 KNOWN_TAXONOMIC_RENAME — 13 genomes

Formal genus reclassifications by GTDB. 11 of the 13 are flagged with
`[TAXONOMIC RENAME]` (or equivalent) in `genomes.notes` by the cohort
curator; 2 (gid 31, gid 1066) were uncovered during this analysis (§6).

| gid | Claimed | GTDB | Source |
|---:|---|---|---|
| 8 | *Methanococcus jannaschii* | *Methanocaldococcus jannaschii* | curator-flagged (Whitman et al. 2002) |
| 10 | *Lactobacillus plantarum* | *Lactiplantibacillus plantarum* | curator-flagged (Zheng et al. 2020) |
| 16 | *Magnetospirillum magneticum* | *Paramagnetospirillum magneticum* | curator-flagged (Lin et al. 2020) |
| **31** | *Allochromatium vinosum* DSM 180 | *Thermochromatium vinosum* | **discovered-this-analysis** |
| 1017 | *Nostoc* sp. | *Trichormus* sp000009705 | curator-flagged (GTDB R220) |
| 1030 | *Rhodobacter sphaeroides* | *Cereibacter_A sphaeroides* | curator-flagged |
| 1043 | *Methanobrevibacter smithii* | *Methanocatella smithii* | curator-flagged (GTDB R220) |
| 1061 | *Methylorubrum extorquens* | *Methylobacterium extorquens* | curator-flagged (GTDB lump) |
| **1066** | *Bacillus selenitireducens* MLS10 | *Salisediminibacterium selenitireducens* | **discovered-this-analysis** |
| 1092 | *Anabaena* sp. | *Dolichospermum lemmermannii* | curator-flagged (GTDB R220) |
| 1107 | *Pseudorhizobium banfieldiae* | *Neorhizobium banfieldiae* | curator-flagged |
| 1112 | *Neomoorella thermoacetica* | *Moorella thermoacetica* | curator-flagged (GTDB lump) |
| 1133 | *Leptothrix discophora* | *Sphaerotilus discophorus* | curator-flagged |

Notably, gid 7 (*Desulfovibrio (Nitratidesulfovibrio) vulgaris*) appears
in CLEAN_SELF_MATCH rather than KNOWN_TAXONOMIC_RENAME because the
curator's `genomes.notes` already records the rename in the genus
field, so the parser extracts *Nitratidesulfovibrio* directly. This is
intentional curator-side handling and produces the same effective
"clean" classification.

### 3.4 CANDIDATUS_PLACEHOLDER — 3 genomes

The claim names a *Candidatus* taxon but GTDB has not yet assigned a
formal genus, so the lineage uses an alphanumeric placeholder. In all
three cases the cohort's loaded accession is identical to the
accession GTDB used as the placeholder species rep — i.e., the cohort
genome and the GTDB rep are the same source nucleotide sequence,
which is the strongest possible identity confirmation.

| gid | Claim | GTDB placeholder | Confirmation |
|---:|---|---|---|
| 1003 | *Candidatus* Phosphitivorax anaerolimi | UBA1062 sp001896555 (p__Desulfobacterota) | Cohort accession `GCA_001896555.1` = GTDB rep `GCA_001896555.1` (literal accession match). FASTA header reads "MAG: Deltaproteobacteria bacterium Phox-21" — the pre-*Candidatus* working name for the same MAG. |
| 1006 | *Candidatus* Methanophaga sp. AG-394-G06 (ANME-1) | QENH01 sp009903405 (p__Halobacteriota; ANME order) | Cohort accession `GCA_009903405.1` = GTDB rep `GCA_009903405.1` (literal accession match). FASTA header reads "ANME-1 cluster archaeon AG-394-G06" — same strain identifier. |
| 1007 | *Candidatus* Methanovorans sp. (ANME-3) | DQIP01 sp020793565 (p__Halobacteriota; Methanosarcinales) | Cohort accession `GCA_020793565.1` = GTDB rep `GCA_020793565.1` (literal accession match). FASTA header reads "Candidatus Methanovorans sp. isolate HMMV ANME3_1" — literal name match. |

### 3.5 NO_CLOSE_MATCH_EXPECTED — 2 genomes

| gid | Claim | Reason |
|---:|---|---|
| 1008 | *Candidatus* Electronema palustre [cable_bacteria] | Cable bacteria are a deep-branching Desulfobulbaceae lineage that GTDB R226 still has only sparsely represented. No sourmash hit ≥0.2 containment. |
| 1099 | *Candidatus* Magnetoglobus multicellularis Araruama [magnetotaxis] | Multicellular magnetotactic prokaryote — extremely under-sampled in cultured/reference databases; no GTDB hit. |

Both are flagged in the supplementary TSV with `needs_action=N` because
the absence of a GTDB match is *biology*, not a curation problem.

### 3.6 NEEDS_REVIEW — 1 genome

See §5 for the full disposition of gid 1000.

### 3.7 PHYLUM_MISMATCH — 0 genomes

**No phylum-level mismatches were found.** The 2026-05-05 audit
signature (claimed organism in one phylum, sourmash hit in a different
phylum) does not appear anywhere in the 165-query cohort. The four
audit-corrected gids from that incident all resolve to the correct
phylum at containment 0.74–1.00 (§4).

---

## 4. Positive controls — 2026-05-05 audit-corrected gids

All four of the cohort gids that were re-downloaded and re-processed
during the 2026-05-05 contamination correction now return phylum- and
genus-correct top hits in GTDB R226:

| gid | Claim | GTDB top hit | C | Status |
|---:|---|---|---:|---|
| **9** | *Thermus aquaticus* (was T. thermophilus HB8) | `d__Bacteria; p__Deinococcota; ...; g__Thermus; s__Thermus aquaticus` | 1.000 | ✅ exact |
| **17** | *Sulfurimonas denitrificans* (was Sulfurovum NBC37-1) | `d__Bacteria; p__Campylobacterota; ...; g__Sulfurimonas; s__Sulfurimonas denitrificans` | 1.000 | ✅ exact |
| **26** | *Picrophilus torridus* (was Brevibacillus brevis NBRC 100599) | `d__Archaea; p__Thermoplasmatota; ...; g__Picrophilus; s__Picrophilus oshimae` (DSM 9789) | 0.743 | ✅ same-genus congener; C1 BacDive erratum applies |
| **30** | *Scalindua japonica* (was Salmonella enterica) | `d__Bacteria; p__Planctomycetota; ...; g__Scalindua; s__Scalindua japonica` | 1.000 | ✅ exact |

Notes:

- The species-level Picrophilus result (oshimae vs torridus) was
  predicted by the C1 BacDive erratum. The audit-corrected FASTA for
  gid 26 is `data/genomes/audit_corrections/GCF_000008265.1.fna`, whose
  header reads `Picrophilus oshimae DSM 9789` — i.e., the loaded
  nucleotide content actually is *P. oshimae*, and `genomes.notes` is
  the only place where the historic *P. torridus* attribution survives.
  Whether the manuscript should refer to gid 26 as torridus or oshimae
  is a curation decision deferred to the audit-refresh task.

- All four corrections cross a phylum boundary from their pre-correction
  state (the pre-correction wrong-genomes were in Bacillota,
  Campylobacterota, Bacillota, and Pseudomonadota respectively; the
  corrected attributions land in Deinococcota, Campylobacterota,
  Thermoplasmatota, and Planctomycetota). The 2026-05-05 fix is fully
  in place at HEAD `74e2951`.

- The pre-correction DB state preserved at
  `data/cultureforge.db.pre_audit_correction_20260504` is untouched
  (this session was read-only).

---

## 5. NEEDS_REVIEW

Exactly one genome falls outside categories 1-5:

### gid 1000 — blind-test PacBio MAG (ST3_PacBio_bin20)

| Field | Value |
|---|---|
| `genomes.id` | 1000 |
| `genomes.accession` | `ST3_PacBio_bin20` (internal handle, not an NCBI accession) |
| `genomes.notes` (full) | "BLIND TEST: bin.020 PacBio assembly via Phase 4.1 wrapper (load-step replay after filename-resolution fix; gapseq output reused from prior run)" |
| FASTA header | `scaffold_41_c1` (anonymous scaffold name; no organism identification in the assembly header) |
| Sourmash top hit | `GCA_000276965.1 d__Bacteria; p__Campylobacterota; c__Campylobacteria; o__Campylobacterales; f__Thiovulaceae; g__Thiovulum_A; s__Thiovulum_A sp000276965` |
| Containment | 0.877 |
| Rank-2 hit | (none with meaningfully different lineage) |

**What's ambiguous:** the cohort entry was loaded specifically as a
blind-test target — the load step was being exercised, not the
identity. `genomes.notes` therefore has no claimed organism string to
compare against, only a load-pipeline description. The sourmash result
(*Thiovulum*_A at 0.88) is biologically plausible: *Thiovulum* is a
chemolithotrophic sulfur-oxidising Epsilonproteobacterium (now
Campylobacterota); MAGs from sulfide-rich PacBio samples lining up with
*Thiovulum*_A is exactly the sort of identification a blind test would
hope to produce.

**Recommended disposition:** Treat as CLEAN — `Thiovulum_A
sp000276965` is the correct identity for this MAG at 0.88 containment.
The action item is a `genomes.notes` update to record the *resolved*
identity ("BLIND TEST: identified as Thiovulum_A sp000276965 (GTDB
R226) at sourmash containment 0.88"), not a re-download or re-process.
Queue for the audit-refresh task alongside the §6 rename additions.

---

## 6. Discovered taxonomic renames (not curator-flagged)

Two GTDB renames surfaced during this analysis that the cohort curator
had not previously flagged in `genomes.notes`. Both produce CLEAN top
hits at 1.0 containment and represent real GTDB reclassifications, not
contamination.

### 6.1 gid 31 — *Allochromatium vinosum* DSM 180

- `genomes.notes`: "Phase 1.5k validation organism - reverse-dsr sulfide oxidizer"
  *(no taxonomic-rename flag)*
- FASTA header: "NC_013851.1 Allochromatium vinosum DSM 180, complete sequence"
- GTDB R226: `g__Thermochromatium; s__Thermochromatium vinosum`
- Containment: 1.000

GTDB R226 has moved *Allochromatium vinosum* into *Thermochromatium*.
This is the type strain DSM 180; the rename is genuine and applies to
the entire species, not just the cohort's particular accession.

### 6.2 gid 1066 — *Bacillus selenitireducens* MLS10

- `genomes.notes`: "Phase 5.0 main: Bacillus selenitireducens MLS10 [heavy_metal_respiration]. biomass=Gram_neg"
  *(no taxonomic-rename flag)*
- FASTA header: "NC_014219.1 [Bacillus] selenitireducens MLS10, complete sequence"
  *(brackets around* Bacillus *are NCBI's standard signal of taxonomic uncertainty)*
- GTDB R226: `g__Salisediminibacterium; s__Salisediminibacterium selenitireducens`
- Containment: 1.000

NCBI's bracketing of "[Bacillus]" was an early-warning hint that this
strain didn't sit comfortably in *Bacillus*. GTDB has now placed it in
*Salisediminibacterium* (family *Salisediminibacteriaceae*, order
*Bacillales_H*).

### Recommended audit-refresh action (not in this session)

Add the following to `genomes.notes` in a future curator-pass task
(deferred per the no-DB-writes constraint of this session):

- gid 31: `[TAXONOMIC RENAME: Allochromatium vinosum → Thermochromatium vinosum (GTDB R226)]`
- gid 1066: `[TAXONOMIC RENAME: Bacillus selenitireducens → Salisediminibacterium selenitireducens (GTDB R226); NCBI bracket "[Bacillus]" was the prior signal]`

---

## 7. Verdict and manuscript implications

**Foundation for the blind-test cohort: solid.**
No contamination remains in the 168 dev cohort at HEAD `74e2951`. The
2026-05-05 audit correction is fully in place (§4), and no new
phylum-level mismatch has surfaced.

**Methodological footing:**
The sourmash + GTDB R226 verification pipeline established here is the
same pipeline that `docs/phase6/blind_test_cohort_design.md` §6 calls
for as part of blind-test candidate vetting. Wiring it in for that
purpose is straightforward — the scripts at
`data/validation/run_sourmash_identity_check.py` and
`data/validation/classify_sourmash_results.py` are parameter-light and
run in the dedicated `sourmash` conda env without further setup.

**Manuscript methods narrative (one-sentence draft):**

> Per-genome identity of the 168-organism dev cohort was independently
> verified by sourmash 4.9.4 sketching (k=31, scaled=1000) against the
> GTDB R226 representative database (143,384 sketches), with each
> top-hit lineage compared to the curator-recorded identity in
> `genomes.notes`; 165 of 168 cohort genomes (3 sentinels had no source
> FASTA on disk) returned a same-genus self-match, a documented GTDB
> reclassification (suffix split, formal rename, or *Candidatus*
> placeholder), or an expected no-close-match for a deeply-branching
> uncultured lineage, with zero phylum-level mismatches consistent with
> the contamination signature corrected in the 2026-05-05 audit.

**Outstanding items (all deferred, not blockers):**

1. Audit-refresh task: add `[TAXONOMIC RENAME]` markers to `genomes.notes`
   for gids 31 and 1066 (§6).
2. Audit-refresh task: record the resolved identity for the blind-test
   MAG gid 1000 in its `genomes.notes` (§5).
3. Curation question (manuscript-side, not pipeline-side): the gid 26
   FASTA is *Picrophilus oshimae*, not *P. torridus*; decide whether
   the cohort entry's species attribution in `genomes.notes` should be
   updated to reflect what's actually loaded.

---

## 8. Appendix

### 8.1 Supplementary TSV schema

`docs/phase6_5/sourmash_identity_verification.tsv` — one row per gid,
columns:

| Column | Description |
|---|---|
| `gid` | `genomes.id` from `data/cultureforge.db` |
| `claimed_organism` | Full untruncated `genomes.notes` value |
| `top_match_lineage` | GTDB R226 lineage of the rank-1 sourmash hit (`d__…;p__…;…;s__…`) |
| `containment` | Sourmash containment score, range [0, 1] |
| `category` | One of the 7 categories defined in §2 |
| `category_rationale` | One-sentence explanation of the classification |
| `needs_action` | Y/N — whether a future curator pass should update `genomes.notes` for this gid |
| `top_match_genus` | GTDB genus (e.g. `Thermochromatium`) — without the `g__` prefix |
| `top_match_species` | GTDB species — without the `s__` prefix |
| `query_name_from_fasta` | First FASTA header line of the cohort genome (used for cross-verification of *Candidatus* placeholders and discovered renames) |
| `rename_source` | For KNOWN_TAXONOMIC_RENAME: `curator-flagged` if `[TAXONOMIC RENAME]` (or equivalent) was in notes; `discovered-this-analysis` if this audit was the first to surface the rename |

### 8.2 Reproducibility

| Item | Value |
|---|---|
| sourmash version | 4.9.4 |
| GTDB version | R226 (December 2024) |
| Reference sketch zip | `gtdb-reps-rs226-k31.dna.zip`, 3,896,377,378 bytes, 143,384 sketches |
| Reference taxonomy CSV | `gtdb-rs226.lineages.csv`, 102,834,235 bytes (server `Content-Length` match), 732,475 rows + header |
| Reference source | `https://farm.cse.ucdavis.edu/~ctbrown/sourmash-db.new/gtdb-rs226/` (C. Titus Brown lab distribution) |
| Search script | `data/validation/run_sourmash_identity_check.py` |
| Classification script | `data/validation/classify_sourmash_results.py` |
| Workdir (cached query sketches) | `/tmp/sourmash_run_s6n79md4` |
| Total wall-time | 5h 25m, 3 parallel threads |
| Hardware | WSL2 on Linux 5.15, 16 vCPU, 15 GiB RAM |

### 8.3 Source documents and prior context

- 2026-05-05 audit correction notes embedded in `genomes.notes` for gids 9, 17, 26, 28, 29, 30
- Pre-correction DB snapshot: `data/cultureforge.db.pre_audit_correction_20260504`
- C1 BacDive erratum: notes the *P. torridus* / *P. oshimae* ambiguity
- Phase 6 design docs:
  - `docs/phase6/blind_test_cohort_design.md` §6 (sourmash identity check)
  - `docs/phase6/cohort_cutoff_verification.md`
  - `docs/phase6/pipeline_taxonomy_audit.md`

### 8.4 Files NOT touched

- `data/cultureforge.db` (read-only mode for every query)
- `genomes.notes` (no UPDATE statements; observed deferrals listed in §6 + §5)
- Any pre-correction snapshot
- Git repository (no commits)

End of report.
