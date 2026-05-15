# Test set audit findings (Phase 5.0 Task 2.1)

**Date:** 2026-05-04
**Audited:** 30 organisms (26 test-set gids 7-32 + 4 sentinels gids 900-903)
**Method:** Every accession verified via NCBI Datasets (GCF/GCA) or NCBI Entrez REST API (NC_/NZ_). Returned organism name compared against the database `notes` column. Loaded marker BLAST hit-gene contig prefixes also checked to confirm the analysis evidence matches the claimed organism.

## Audit results

- Total accessions audited: 30
- Match (exact or acceptable rename): 22
- Mismatches requiring investigation: **8**
- Failed lookups: 0

## Severity classification (per VERIFICATION_DISCIPLINE.md Rule 2)

| match_status | Count | Description |
|---|---:|---|
| `OK` | 19 | Accession + DB notes + loaded data all consistent |
| `OK_RENAME` | 2 | Genus or species was renamed since deposit; both metadata + loaded data are otherwise correct |
| `OK_METADATA_DRIFT` | 1 | DB notes contains an annotation drift (e.g., "subsp. ethanolicus" not in NCBI's strain field) but the underlying organism is correct |
| **`FAIL_WRONG_GENOME_LOADED`** | **3** | Wrong organism's genome was loaded from the start. Accession + loaded marker BLAST data agree with each other, but neither matches the DB `notes` claim about which organism this gid represents. |
| **`FAIL_FILE_POINTER_SCRAMBLE`** | **1** | Loaded marker BLAST data IS from the claimed organism (DB notes match marker contig prefix), but the `accession` field and `file_path` field point to a different file. Database analysis is correct; metadata pointers are wrong. |
| **`FAIL_LOADED_DATA_MISMATCH`** | **1** | Loaded marker BLAST data is from a third organism that matches NEITHER the DB notes nor the file-path filename. The validation work that referenced this gid was performed on the wrong organism. |

---

## Acceptable findings (22 organisms)

### OK — exact or strain-only-dropped match (19)

gids 7, 11, 12, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 27, 31, 32, 900, 901, 902, 903 (Methanosarcina acetivorans included). 

For sentinel set (900-903), all 4 verify cleanly. For most test-set entries, NCBI returns the same organism name as the DB notes, sometimes with strain-level detail expanded (e.g., "Campylobacter jejuni" → "Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819" — same organism, more detail).

### OK_RENAME — taxonomic reclassification (2)

| gid | Accession | Original name (DB) | Current name (NCBI) | Citation |
|---:|---|---|---|---|
| 10 | NC_004567.2 | *Lactobacillus plantarum* | *Lactiplantibacillus plantarum* WCFS1 | Zheng et al. 2020 — *Lactobacillus* genus split |
| 16 | NC_007626.1 | *Magnetospirillum magneticum* | *Paramagnetospirillum magneticum* AMB-1 | Lefèvre et al. 2020 — Magnetospirillum genus split |

Both are documented taxonomic renames. The biological identity of the genome is unchanged. Action: annotate the `notes` column to record both names; no impact on validation.

### OK_METADATA_DRIFT — strain field drift (1)

| gid | Accession | DB notes | NCBI returns | Status |
|---:|---|---|---|---|
| 13 | NC_002939.5 | "Geobacter sulfurreducens subsp. ethanolicus" | "Geobacter sulfurreducens PCA" | The PCA strain IS the type strain. The "subsp. ethanolicus" designation in DB notes appears to be an annotation drift (PCA was sometimes referred to as "ethanolic-type" in older literature, but it's not a formal subspecies). Action: clean up notes; no impact on validation. |

---

## Serious findings (8 organisms)

### FAIL_WRONG_GENOME_LOADED (3 — most serious)

These genomes have a fundamentally wrong organism in the loaded analysis. The accession returns one organism per NCBI; the DB notes claim a different organism; the loaded marker BLAST data agrees with the accession (NOT the notes). Conclusion: the wrong organism's genome was downloaded and processed from the start. All validation evidence labeled with the DB notes' name is actually about a different organism.

| gid | Accession | DB notes claim | NCBI returns | Loaded marker contigs | Severity |
|---:|---|---|---|---|---|
| **9** | NC_006461.1 | *Thermus aquaticus* | *Thermus thermophilus* HB8 | `NC_006461.1_*` (Thermus thermophilus contigs) | High — same genus, both extreme thermophiles, but wrong species |
| **17** | NC_009663.1 | *Sulfurimonas denitrificans* | *Sulfurovum* sp. NBC37-1 | `NC_009663.1_*` (Sulfurovum contigs) | High — different genus; both Campylobacterota sulfur-cycling but with different physiology |
| **26** | GCF_000010165.1 | *Picrophilus torridus* | *Brevibacillus brevis* NBRC 100599 | `NC_012491.1_*` (Brevibacillus contigs) | **Catastrophic** — thermoacidophilic archaeon claimed; mesophilic Gram-positive bacterium loaded. Phase 2e G.1 fix that "lifted Picrophilus torridus from 80% → 100% V12" was applied to *Brevibacillus brevis*. Phase 3 LIMITATIONS B.4 reasoning about "archaeal predictions" is misapplied (Brevibacillus is not an archaeon at all). |

### FAIL_FILE_POINTER_SCRAMBLE (1 — recoverable, but metadata is wrong)

| gid | Accession | DB notes claim | NCBI returns (for accession) | Loaded marker contigs (the actual data) | Severity |
|---:|---|---|---|---|---|
| **28** | GCA_000315995.1 | *Candidatus Methanoperedens nitroreducens* | *Salmonella enterica* serovar Thompson | `FZMP01000*` (Methanoperedens nitroreducens MAG contigs) | The loaded analysis IS Methanoperedens (consistent with DB notes); Phase 3.6 ANME validation was therefore on the correct biological organism. BUT the `accession` column is wrong (points to Salmonella) AND the `file_path` column points to a Salmonella FASTA file. Two metadata fields point to the wrong file; only the loaded marker / pathway data is correct. This is recoverable by updating `accession` and `file_path` to the correct Methanoperedens entries; no re-validation needed. |

### FAIL_LOADED_DATA_MISMATCH (1 — most concerning for downstream impact)

| gid | Accession | DB notes claim | NCBI returns (for accession) | Loaded marker contigs (the actual data) | Severity |
|---:|---|---|---|---|---|
| **30** | GCA_008000775.1 | *Candidatus Scalindua profunda* | *Promethearchaeum syntrophicum* | `AMSN01000*` (Salmonella enterica WGS contigs) | **Catastrophic.** Three different organisms involved: DB claims Scalindua, accession returns Prometheoarchaeum, loaded data is from Salmonella. The Phase 1.5+ "Scalindua escalates due to MAG completeness (LIMITATIONS E.1)" finding was actually about *Salmonella enterica* serovar Thompson — a complete-genome enterobacterium that should NOT escalate. The whole "Scalindua MAG completeness" narrative needs revisiting. |

### Documented OK but worth noting (case 4 isn't a fail; just an observation)

gid=29 (Prometheoarchaeum) — DB.notes says Prometheoarchaeum syntrophicum (✓), DB.file_path points to a Methanoperedens.fasta filename (mislabeled file), but the actual file content at that path IS Methanoperedens. Loaded marker contigs are `CP042905.*` = Prometheoarchaeum. So gid=29 has inconsistent file_path naming but the actual loaded analysis is correct (Prometheoarchaeum) and consistent with DB notes. Recoverable: rename the file or update file_path to a more accurate filename.

---

## Cross-cutting summary table

| gid | DB notes (intent) | Accession | NCBI for accession | Loaded data | Verdict |
|---:|---|---|---|---|---|
| 9 | T. aquaticus | NC_006461.1 | T. thermophilus HB8 | T. thermophilus | ❌ Wrong genome loaded |
| 13 | G. sulfurreducens subsp. ethanolicus | NC_002939.5 | G. sulfurreducens PCA | G. sulfurreducens PCA | ✅ OK (subspecies notation drift) |
| 17 | S. denitrificans | NC_009663.1 | Sulfurovum sp. NBC37-1 | Sulfurovum NBC37-1 | ❌ Wrong genome loaded |
| 26 | P. torridus | GCF_000010165.1 | B. brevis NBRC 100599 | B. brevis | ❌ Wrong genome loaded |
| 28 | M. nitroreducens | GCA_000315995.1 | Salmonella enterica | Methanoperedens (FZMP01) | ⚠️ File-pointer scramble; data correct |
| 29 | P. syntrophicum | GCA_900196725.1 | M. nitratireducens | Prometheoarchaeum (CP042905) | ⚠️ File-name scramble; data correct |
| 30 | Sc. profunda | GCA_008000775.1 | Promethearchaeum syntrophicum | Salmonella enterica (AMSN01) | ❌ Loaded data is third organism (Salmonella) |

---

## Impact assessment on prior validation work

This audit changes the interpretation of several prior reports. **None of the underlying CultureForge code is affected; the issue is in the test-set genome assignments.**

### Validations that were performed on a different organism than reported

- **gid=9 work** — All references to "Thermus aquaticus gid=9" actually evaluated *Thermus thermophilus* HB8. Both are extreme thermophiles in the same genus. Most thermophile-specific reasoning still applies; the species label is wrong.
- **gid=17 work** — All references to "Sulfurimonas denitrificans gid=17" actually evaluated *Sulfurovum* sp. NBC37-1. Both are sulfur-cycling Campylobacterota; the metabolism assessments may not transfer cleanly between the two genera.
- **gid=26 work** — All references to "Picrophilus torridus gid=26" actually evaluated *Brevibacillus brevis* NBRC 100599. **The most catastrophic mislabel.** Phase 2e claims about "Picrophilus torridus moved from 80% → 100% V12 by TEMPURA-first condition priority" were measuring *Brevibacillus brevis*. Phase 3 LIMITATIONS B.4 archaeal-prediction discussion is misapplied for this gid.
- **gid=30 work** — All references to "Scalindua profunda gid=30" actually evaluated *Salmonella enterica* serovar Thompson. The "Scalindua MAG completeness LIMITATIONS E.1" finding is wrong — Salmonella has a complete genome and shouldn't have escalated for that reason. Whatever escalation logic fired on gid=30 was responding to Salmonella's genome content, not to incomplete-MAG signals.

### Validations that are correct despite metadata errors

- **gid=28 (Methanoperedens) — Phase 3.6 ANME validation IS correct.** The loaded marker BLAST + gapseq data IS from Methanoperedens (FZMP01 contigs). Only the `accession` and `file_path` columns are wrong. The Phase 3.6 finding (mcrA at 70% pident + nitrate-pwy at 100% completeness driving anme_reverse_methanogenic primary mode) IS about Methanoperedens, not about Salmonella, despite the misleading metadata.
- **gid=29 (Prometheoarchaeum)** — File path filename is misleading but the actual file content + loaded analysis IS Prometheoarchaeum. Validation findings hold.

---

## Recommended actions

The Phase 5.0 prompt is explicit:

> If any test set genome has a fundamentally wrong accession (different species/genus from documented), this is a serious finding. Stop Phase 5.0 progress and consult the user about how to address — possibly involves correcting the database entry, re-running the relevant validation, or noting limitations in the manuscript.

For each FAIL category:

1. **gid=9 (T. aquaticus → T. thermophilus)**: Decide between (a) re-download genuine T. aquaticus assembly (e.g., GCF_004114415.1 or similar), reload + re-validate; (b) update DB notes to match what's actually there (T. thermophilus HB8) and re-interpret prior validation as about T. thermophilus; (c) document as known issue in the manuscript and decide manuscript framing.

2. **gid=17 (S. denitrificans → Sulfurovum sp. NBC37-1)**: Same options. Both are sulfur-cycling Campylobacterota deep-sea isolates so substantial overlap; choice depends on whether the manuscript references "S. denitrificans" specifically.

3. **gid=26 (P. torridus → B. brevis)**: Most urgent. Re-download genuine P. torridus assembly (GCF_000026285.1 — verify) and re-validate. The Phase 2e and Phase 3 narratives that cite gid=26 specifically need rewriting once the correct genome is loaded.

4. **gid=28 (file pointer scramble, data correct)**: Update DB.accession to genuine M. nitroreducens accession (verify which one points to FZMP01 contigs); update DB.file_path to correctly name the loaded FASTA. No re-validation needed.

5. **gid=30 (Scalindua → Salmonella)**: Most concerning interpretation-wise. Re-download genuine Scalindua profunda MAG, reload + re-validate. The "Scalindua MAG completeness escalation" narrative (LIMITATIONS E.1) needs rewriting based on the correct organism's outcome.

### Phase 5.0 implications

- **Phase 5.0 main work CANNOT proceed** until these are addressed. Adding 143 new entries to a test-set baseline that has 4 wrong-genome entries amplifies the integrity problem.
- **The 26-organism baseline that V12 has been measured against is not what the documentation claims.** Phase 4.1 V12-byte-identical checks were measured against the wrong-genome state — the byte-identity guarantee held within that wrong-genome state, but the reported numbers reflect a different organism set than documented.
- **manuscript impact:** Methods section needs a "test set composition" subsection acknowledging the audit + corrections. Pre-audit numbers cannot be cited for "Picrophilus torridus" without correction.

### Decision-tree handoff to user

For each fix path, the user needs to decide:

| Option | Pros | Cons |
|---|---|---|
| **A**. Re-download correct genomes for gids 9, 17, 26, 30; reload + re-validate | Corrects the test-set integrity issue; prior validation reports become accurate | Days of pipeline rerun; some prior phase narratives need rewriting |
| **B**. Update metadata to match what's actually loaded (T. thermophilus, Sulfurovum, B. brevis, Salmonella enterica), re-interpret prior validation | Faster; preserves continuity of validation reports | Manuscript needs to explain why test-set composition is "Brevibacillus brevis" instead of "Picrophilus torridus" — likely worse for narrative |
| **C**. Hybrid — Option A for the catastrophic mislabels (gid=26, gid=30); Option B for the same-genus/same-family cases (gid=9, gid=17) | Pragmatic | Methods section more complex |

**Recommended:** Option A for gid=26 (Brevibacillus → Picrophilus) and gid=30 (Salmonella → Scalindua) since the biological substitution is too severe to justify reframing. Option B may be defensible for gid=9 (within-genus thermophile substitution) and gid=17 (within-family sulfur-cycling substitution).

For gid=28 file-pointer scramble: just update DB.accession + DB.file_path. No re-validation needed.

For gid=10 + gid=16 taxonomic renames: just update DB.notes. Phase 3 documentation references can stay as-is with a note about the rename.

---

## What this means for the audit checkpoint

This is a HARD STOP. The Phase 5.0 main work to add 143 new genomes cannot proceed until the user reviews these findings and decides how to address. The Task 2.2 marker reference sampling audit can run while the user reviews these findings — but Task 3 (test-set exclusion list update) and beyond is gated on resolution of these test-set integrity issues.
