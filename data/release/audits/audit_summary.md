# Phase 5.0 Audit Summary — HARD CHECKPOINT

**Date:** 2026-05-04
**Status:** Audit complete. **Phase 5.0 main work paused** pending user review and decision per the prompt's hard-stop policy.

---

## Top-line findings

| Audit | Status | Severity |
|---|---|---|
| Test-set genome accessions (gids 7-32, 900-903) — accession + loaded data integrity | **8 of 30 organisms have integrity issues** | 4 **catastrophic**, 1 **recoverable**, 3 **acceptable (renames + drift)** |
| Marker reference accession sampling (31 of 156) | **31/31 accessions verify cleanly** | But 5 marker FASTAs draw from sentinel organisms — test-set-exclusion violation |

The audit confirmed the verify-at-creation discipline value: it surfaced 5 test-set integrity issues that were invisible from the existing documentation. Three of them (gid=9 Thermus, gid=17 Sulfurimonas, gid=26 Picrophilus) involve the wrong organism being loaded since the test set was first built. One (gid=30 Scalindua → Salmonella) is a fully scrambled assignment where the loaded data is from a third organism. These have implications for the manuscript narrative about test-set composition and validation findings.

---

## Test-set audit findings (full detail in `test_set_audit_findings.md`)

### Catastrophic — wrong genome loaded from the start (4)

| gid | DB notes claim | Actually loaded | Severity |
|---:|---|---|---|
| 9 | *Thermus aquaticus* | *Thermus thermophilus* HB8 | High — same genus thermophile, but wrong species |
| 17 | *Sulfurimonas denitrificans* | *Sulfurovum* sp. NBC37-1 | High — different genus, different physiology |
| 26 | *Picrophilus torridus* | *Brevibacillus brevis* NBRC 100599 | **Catastrophic** — thermoacidophilic archaeon claimed; mesophilic Gram-positive bacterium loaded |
| 30 | *Candidatus Scalindua profunda* | *Salmonella enterica* serovar Thompson | **Catastrophic** — anammox MAG claimed; Enterobacterium loaded |

### Recoverable metadata-only error (1)

| gid | DB notes (correct) | DB.accession (wrong) | DB.file_path (wrong) | Loaded data (correct) |
|---:|---|---|---|---|
| 28 | Methanoperedens nitroreducens ✓ | GCA_000315995.1 (Salmonella) | Candidatus_Scalindua_profunda.fasta (Salmonella file) | FZMP01* (Methanoperedens MAG) ✓ |

The Phase 3.6 ANME validation IS biologically correct — the loaded marker BLAST + gapseq evidence is genuinely Methanoperedens. Only the metadata pointers are wrong.

### Acceptable findings (3)

- gid=10: Lactobacillus → Lactiplantibacillus plantarum (taxonomic rename, Zheng et al. 2020) — OK_RENAME
- gid=16: Magnetospirillum → Paramagnetospirillum magneticum (taxonomic rename, Lefèvre et al. 2020) — OK_RENAME
- gid=13: "Geobacter sulfurreducens subsp. ethanolicus" in DB notes; NCBI returns G. sulfurreducens PCA (type strain). Annotation drift only — OK_METADATA_DRIFT

---

## Marker reference audit findings (full detail in `marker_audit_findings.md`)

### Step 1: Are the accessions correct? **YES — 31/31 verify cleanly**

Every sampled UniProt accession returns the expected protein from the expected organism. No fabricated, retracted, or wrong-organism marker references found.

### Step 2: Test-set exclusion compliance — **5 violations**

| Marker | Reference draws from | Sentinel gid | Phase impact |
|---|---|---:|---|
| mcrA | Methanosarcina acetivorans C2A | 903 | Phase 3.6 / 3.8 "100% pident self-hit" was self-recognition |
| mmoX | Methylococcus capsulatus Bath | 900 | Phase 3.5 mmoX sentinel was self-hit |
| nrfA | Wolinella succinogenes DSM 1740 | 901 | Phase 3.7 DNRA sentinel was self-hit |
| nxrA | Nitrobacter winogradskyi Nb-255 | 902 | Phase 3.7 NOB Type B sentinel was self-hit |
| pmoA | Methylococcus capsulatus Bath | 900 | Phase 3.5 pmoA sentinel was self-hit |

Sentinel "100% pident on the sentinel organism" results from Phase 3.5 / 3.7 / 3.8 were measuring self-recognition by construction. The reference protein was IN the BLAST DB; the sentinel's proteome contained the same sequence; 100% identity was guaranteed. These results don't validate generalization, they validate that BLAST finds proteins where they were extracted from.

**One result survives:** the Phase 3.6 Methanosarcina ANME-negative test. The mcrA self-hit is also affected, but the **negative-result** aspect (ANME OR-group correctly resolves all-negative because dsrAB / mtrC_omcB / nitrate-pwy are genuinely absent in Methanosarcina's genome) is independent of the marker-self-hit issue and remains valid.

No marker reference draws from a non-sentinel test-set organism (gids 7-32).

---

## What changes about the validation narrative

### Findings that are completely intact

- The 26-organism test-set V12 distribution (gids 7-32 minus the 4 with wrong-genome / wrong-data issues = 22 genomes) — those 22 organisms verify correctly and prior validation reports for them stand.
- The Phase 3.6 ANME directional discriminator on **gid=28 Methanoperedens** — the loaded data IS Methanoperedens, so the Phase 3.6 validation is biologically correct.
- Phase 3.6 ANME-negative-control's negative aspect on Methanosarcina (no false-positive ANME firing) — genuine generalization since the OR-group's negative resolution doesn't depend on mcrA self-recognition.
- All Phase 1-4 capability detector framework code (no code changes affected by the audit).

### Findings that need correction or reframing

- **gid=26** any V12 / recipe-evaluation reference to "Picrophilus torridus" actually evaluated Brevibacillus brevis. Phase 2e's "Picrophilus torridus moved 80% → 100% by TEMPURA-first" measured Brevibacillus.
- **gid=30** any reference to "Scalindua profunda escalates due to MAG completeness (LIMITATIONS E.1)" actually evaluated Salmonella enterica. The "MAG completeness" framing is wrong; Salmonella has a complete genome.
- **gid=9** any reference to "Thermus aquaticus" measured Thermus thermophilus HB8 (within-genus thermophile but wrong species).
- **gid=17** any reference to "Sulfurimonas denitrificans" measured Sulfurovum sp. NBC37-1 (different genus).
- **Phase 3.5 / 3.7 / 3.8 sentinel "100% pident self-hit" claims** need to be re-framed as self-recognition tests rather than generalization tests.

---

## Hard-stop decisions for the user

The Phase 5.0 prompt requires user input before continuation. Specific decisions:

### Decision 1 — How to address the 4 wrong-genome cases (gid=9, 17, 26, 30)

**Option A — Re-download correct genomes and re-validate.** Pros: corrects test-set integrity; prior validation reports become accurate. Cons: days of pipeline rerun; some prior phase narratives need rewriting. Required for the catastrophic mislabels (gid=26 Picrophilus, gid=30 Scalindua) where the biological substitution is severe.

**Option B — Update DB metadata to match what's actually loaded; re-interpret prior validation as about the actually-loaded organism.** Pros: faster, preserves continuity. Cons: changes the test-set composition documented in PHASE_3_CLOSEOUT.md, README.md, manuscript. Defensible for within-genus or within-family substitutions (gid=9 Thermus species swap, gid=17 within-family Campylobacterota).

**Option C — Hybrid.** Option A for catastrophic cases (26, 30); Option B for within-genus / within-family cases (9, 17). My recommendation.

### Decision 2 — How to address gid=28 (file pointer scramble, data correct)

Just update DB.accession + DB.file_path columns. No re-validation. Recoverable trivially. (No major decision; the Phase 3.6 ANME validation stands.)

### Decision 3 — How to address gid=29 (file_path filename misleading; data correct)

Just rename the file or update file_path. No re-validation. Even more trivial than gid=28.

### Decision 4 — How to address the marker self-recognition issue

**Option A — Change marker references** to use proteins from organisms NOT in the sentinel set, then re-curate. Adds ~5 days of careful curation.

**Option B — Change sentinel selection** to use organisms whose own proteins are NOT in the reference set. Adds ~5 days of sentinel-replacement work + re-validation.

**Option C — Re-frame existing results in any future manuscript.** The Phase 3.5 / 3.7 / 3.8 sentinel "100% pident" claims become "self-recognition confirmation", and additional sentinels are added for true generalization. This is the lowest-friction option but requires the manuscript to acknowledge the methodological subtlety.

**My recommendation:** Option C (re-frame) for the existing sentinels + Option A for any NEW marker references curated in Phase 5.1+. Going forward, follow `VERIFICATION_DISCIPLINE.md` Marker Curation Specifics #1 (test-set exclusion enforcement) without exception.

### Decision 5 — Phase 5.0 main work continuation

After Decisions 1-4 are resolved, the test-set baseline is clean enough to add the 143 Phase 5.0 organisms. Until then:

- Phase 5.0 Task 3 (test-set exclusion list update) is BLOCKED — the list would document a corrupted state.
- Phase 5.0 Task 4 (genome downloads) is BLOCKED — adding 143 genomes to a baseline with 4 wrong-genome entries amplifies the integrity problem.
- Phase 5.0 Task 5 (batch processing) is BLOCKED — would compute metrics against a corrupted baseline.

The path forward depends on Decisions 1-4. Estimated time:
- Hybrid resolution path (Option C for Decision 1): 1-2 weeks for re-download + re-validation + re-framing existing sentinels
- Then Phase 5.0 main work resumes from Task 3

---

## Files produced this audit

- `data/release/audits/existing_test_set.tsv` — DB extract for test set + sentinels
- `data/release/audits/test_set_verification.tsv` — accession → NCBI organism for all 30 entries
- `data/release/audits/test_set_audit_findings.md` — detailed test-set findings
- `data/release/audits/marker_audit_results.tsv` — sampled marker UniProt verification results
- `data/release/audits/marker_audit_findings.md` — detailed marker findings
- `data/release/audits/audit_summary.md` — this document

---

## What I'm asking the user to do

1. Read this audit summary.
2. Decide on Decisions 1-4 above.
3. Reply with your decisions; I'll proceed accordingly.

The Phase 5.0 main work pauses here per the prompt's hard-checkpoint requirement. The 143 Phase 5.0 candidate genomes remain locked at `data/release/phase5_0_genome_list_final.tsv` — they are not yet downloaded or processed. The held-out bin.020 ST-3 is not affected by this audit and remains held out.
