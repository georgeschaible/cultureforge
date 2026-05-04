# Phase 4.1 — Database Cleanup Notes

**Date:** 2026-05-03
**Trigger:** Pre-Phase-4.1 blind-test attempt left a polluted database entry at gid=904 with E. coli's accession (NC_000913.3) but the user's blind-test gapseq output. This cleanup removes the bad entry AND restores gid=32 (E. coli) which was silently overwritten during the same incident.

---

## What happened

The user attempted to manually run gapseq + load it into the database for the blind-test genome `bin.020.fasta_assembly.fa`. The hardcoded `load_gapseq.py` script's `insert_genome()` function has an "idempotent reload" pattern that:

1. Looks up the existing genome row by accession (`NC_000913.3` for E. coli)
2. If found, deletes the existing row (and its pathway/transporter rows) — this freed gid=32
3. Inserts a new row via `INSERT INTO genomes (...)` with no explicit id — auto-increment assigned id=904 (the next available value, since 32 was just freed but SQLite auto-increment doesn't reuse)
4. Loaded the user's blind-test gapseq output (1922 pathways, 2170 transporters) under gid=904 — but tagged with E. coli's accession

Net result before cleanup:
- gid=32 (the original E. coli) silently lost
- gid=904 had E. coli's accession but the user's blind-test pathway data (the data was actually just E. coli's gapseq re-run, but the gid was wrong)
- V12 validation lost gid=32 from its 26-organism set

## Cleanup actions

### Step 1 — Document pre-cleanup state

| Table | gid=904 row count |
|---|---:|
| genomes | 1 (accession NC_000913.3) |
| genome_pathways | 1922 |
| genome_transporters | 2170 |
| genome_diagnostic_markers | 6 |
| (others) | 0 |

### Step 2 — Delete gid=904

DELETE statements run against all 11 tables that have a `genome_id` column (identified via `pragma_table_info` schema scan):

```sql
DELETE FROM genome_pathways          WHERE genome_id = 904;
DELETE FROM genome_transporters      WHERE genome_id = 904;
DELETE FROM genome_diagnostic_markers WHERE genome_id = 904;
DELETE FROM genome_growth_predictions WHERE genome_id = 904;
DELETE FROM genome_metal_profile     WHERE genome_id = 904;
DELETE FROM genome_carbon_sources    WHERE genome_id = 904;
DELETE FROM genome_hydrogenases      WHERE genome_id = 904;
DELETE FROM genome_reaction_markers  WHERE genome_id = 904;
DELETE FROM genome_quality           WHERE genome_id = 904;
DELETE FROM predictions              WHERE genome_id = 904;
DELETE FROM protein_metal_binding    WHERE genome_id = 904;
DELETE FROM genomes                  WHERE id        = 904;
```

### Step 3 — Restore gid=32

The original E. coli K-12 MG1655 entry was silently lost in the blind-test incident (Step 1 above). Restoration sequence:

1. Manual `INSERT INTO genomes` with id=32 explicitly specified, using the original metadata (accession `NC_000913.3`, file_path `data/genomes/ecoli_k12_mg1655.fasta`, biomass_template `Gram_neg`, length 4,641,652 bp, n_unique_genes 4319).
2. Re-run `load_gapseq.load_pathways(conn, 32, '.../ecoli_k12_mg1655-all-Pathways.tbl')` — loaded 1922 pathways.
3. Re-run `load_gapseq.load_transporters(conn, 32, '.../ecoli_k12_mg1655-Transporter.tbl')` — loaded 2170 transporters.
4. Re-run `load_gapseq.load_reaction_markers(conn, 32, '.../ecoli_k12_mg1655-all-Reactions.tbl')` — loaded 7 reaction markers.
5. Re-run `run_marker_blast.py data/gapseq/ecoli/ecoli_proteins.faa --genome-id 32` — fired nrfA at 90% pident, terminal_oxidases at 51.6% (canonical E. coli signature).
6. Re-run `load_genomespot.load(conn, 32, '.../ecoli.predictions.tsv')` — loaded 10 environmental envelope predictions.
7. Re-run `load_mebipred.load(conn, 32, '.../ecoli_predictions.tsv')` — loaded 4319 protein metal-binding predictions.

The existing hardcoded `load_*.py` scripts WERE used here because their per-marker loader functions are gid-parameterized (`load_pathways(conn, genome_id, path)`) — only the top-level orchestration logic is hardcoded. The Phase 4.1 prohibition is on modifying those scripts; calling their loader functions with explicit gid is fine.

### Step 4 — Verify post-cleanup state

| Check | Expected | Actual | OK? |
|---|:---:|:---:|:---:|
| Test set count (gids 7-32) | 26 | 26 | ✓ |
| Sentinel count (gids 900-903) | 4 | 4 | ✓ |
| gid=904 rows remaining | 0 | 0 | ✓ |
| gid=32 inspect: aerobic_chemotrophic primary | yes | yes | ✓ |
| gid=32 V12 score | 100% | 100% | ✓ |
| gid=32 confidence | high (0.82) | 0.82 | ✓ |

### Step 5 — Preserve gapseq blind-test output

The directory `data/gapseq/blind_test_organism_001/` (representing the user's ~3-hour gapseq run on the bin.020 PacBio assembly) is left untouched on disk. Phase 4.1's `process` wrapper, once built, can use this as test input for Task 5 (acceptance test) without re-running the slow gapseq step.

---

## Key takeaway for Phase 4.1 design

The root cause of the polluted gid=904 was the existing `load_gapseq.py:insert_genome()` "idempotent reload" pattern: when a script is re-run with the same accession, the old row is silently deleted and a new one is inserted with an auto-increment id. This works fine when the script is the only writer for that accession AND the test set isn't being modified — but when the script is run with a different organism's gapseq output and the same accession, it silently overwrites the existing row with stale-pointing data.

The Phase 4.1 `register_genome()` function in `register_genome.py` MUST avoid this pattern: refuse to register if the accession already exists (raise `ValueError`), forcing the user to explicitly deregister the conflicting entry first. This makes the failure mode loud rather than silent.

The Phase 4.1 `deregister_genome()` function MUST refuse to delete gids < 1000 — the test set and sentinels are protected by gid range. A user who hits an accession collision against a test-set entry must explicitly understand they'd be deleting test-set data, which is not what they want.
