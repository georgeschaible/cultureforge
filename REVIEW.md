# CultureForge Code Review

**Review date:** 2026-04-17  
**Files reviewed:** 24 Python files in the project root  
**Reviewer:** Claude Sonnet 4.6

---

## Fixes applied

**Session 2026-04-17:** All 6 Critical issues resolved (C-1 through C-6); Important issues I-1, I-2, I-3, I-4, I-5, I-7 resolved; Architecture Note items resolved: all 4 missing indices added, placeholder data deleted from production DB, S-4 dead test code moved behind --verbose flag.

---

## Module Dependency Map

```
synthesize_media.py
  ├── confidence.py          (direct import)
  ├── carbon_and_gas.py      (direct import) → confidence
  ├── compatibility.py       (direct import)
  ├── media_format.py        (direct import) → confidence
  ├── thermodynamics.py      (import as td)
  ├── phylo_match.py         (star-like import of 13 symbols)
  └── predict_media.py       (star-like import of 14 symbols)
        └── phylo_match.py   (import of 8 symbols)
              └── confidence.py

load_gapseq.py       → confidence
load_genomespot.py   → confidence
load_mebipred.py     → confidence
load_thermodynamics.py → thermodynamics

validate_confidence.py → predict_media, phylo_match, confidence
test_confidence.py   → confidence
test_thermodynamics.py → thermodynamics

# Standalone (no project imports):
build_database.py
integrate_tempura.py
download_mediadive.py
download_medium_strains.py
download_bacdive.py
fetch_16s_sequences.py
fetch_tempura_16s.py
build_blast_db.py
run_mebipred.py
```

No circular dependencies detected.

---

## Critical (must fix before Phase 2)

### C-1 — `build_database.py` drops tables without warning; loaders will fail if run out of order
**Files:** `build_database.py` lines 23-28  
**Issue:** `open_db()` unconditionally runs `DROP TABLE IF EXISTS media_compounds; DROP TABLE IF EXISTS organism_media; DROP TABLE IF EXISTS media; ...` every run. Any downstream data written by `load_gapseq.py`, `load_genomespot.py`, `integrate_tempura.py`, etc. that lives in FK-linked tables will be silently destroyed if `build_database.py` is re-run after the other loaders. There is no guard, no prompt, and no mention in the module docstring.  
**Fix:** **RESOLVED** — Add a `--rebuild` flag; default to error-out if the tables already contain data, or skip the drop and use `INSERT OR IGNORE`.

---

### C-2 — All loaders hard-code relative paths; break when called from any other directory
**Files:** `build_database.py` (line `DB = "data/cultureforge.db"`), `phylo_match.py` lines 26-27, `load_gapseq.py` lines 31-33, `load_genomespot.py` line 28, `load_mebipred.py` line 28, `load_thermodynamics.py` line 36, `integrate_tempura.py` lines 6-7, `build_blast_db.py` lines 14-16, `fetch_16s_sequences.py` lines 22-25, etc.  
**Issue:** Every module uses bare relative paths (`"data/cultureforge.db"`, `"data/blastdb/16s_ref"`, `"data/gapseq/ecoli"`). Running any script from a subdirectory — or importing the module from a test harness in a different cwd — silently creates a second database in the wrong place or raises `FileNotFoundError`.  
**Fix:** **RESOLVED** — Anchor all data paths to `pathlib.Path(__file__).parent / "data/..."` or accept them as CLI arguments.

---

### C-3 — `genome_carbon_sources` table queried in `media_format.py` but has no reusable CREATE TABLE
**Files:** `media_format.py` line 87  
**Issue:** `predict_format()` runs `SELECT COUNT(*) FROM genome_carbon_sources WHERE genome_id = ?`. This table exists in the current database (51 rows, created by a session-11 inline script) but has no `CREATE TABLE` in any reusable `.py` file. A fresh database build would hit `sqlite3.OperationalError: no such table`. The creation code lives only in a Bash-embedded Python snippet from session 11.  
**Fix:** **RESOLVED** — Move the `CREATE TABLE genome_carbon_sources` DDL into `carbon_and_gas.py` and call it from `synthesize_media.py` startup, or add a `load_carbon_sources.py` loader following the existing loader pattern.

---

### C-4 — `genome_hydrogenases` table queried in `carbon_and_gas.py` but has no reusable CREATE TABLE
**Files:** `carbon_and_gas.py` lines 237-246  
**Issue:** Same pattern as C-3. The table exists (18 rows) but was created by a session-11 inline script. No `.py` file contains the `CREATE TABLE genome_hydrogenases` statement. Additionally, `get_gas_phase_recommendation()` should guard with `try/except OperationalError` so it falls back gracefully to gapseq-only analysis when the table doesn't exist.  
**Fix:** **RESOLVED** — Create a `load_hydrogenases.py` loader (or add schema to `carbon_and_gas.py`) + add the try/except fallback.

---

### C-5 — `load_genomespot.py` mutates `ConfidenceScore.value` and `.rationale` directly (frozen dataclass bypass)
**Files:** `load_genomespot.py` lines 111-117  
**Issue:** `score_prediction()` assigns `conf.value = max(0.50, conf.value - 0.10)` and `conf.rationale += " [novel genome features: -0.10]"` on a `ConfidenceScore` dataclass. Because the class is not frozen, this succeeds silently, but it violates the immutability expectation implied by the module-level documentation in `confidence.py` and produces a `ConfidenceScore` whose `value` no longer matches the result of `__post_init__` validation (the validation ran on the original value, not the modified one).  
**Fix:** **RESOLVED** — Use `confidence.score(...)` with adjusted `raw_value` to apply penalties before construction, or construct a new `ConfidenceScore` with the penalised value rather than mutating in place.

---

### C-6 — `integrate_tempura.py` uses integer pseudo-IDs (>10M) that collide with `organisms.id INTEGER PRIMARY KEY`
**Files:** `integrate_tempura.py` lines 170-172  
**Issue:** TEMPURA-only organisms get IDs starting at `max(max_id + 1, 10_000_000)`. The `organisms` table in `build_database.py` uses `id INTEGER PRIMARY KEY` (without AUTOINCREMENT), and BacDive IDs are inserted directly. When BacDive eventually reaches 10M IDs (BacDive currently >200K but growing), the ranges collide. More immediately, `organisms.id` is used as `bacdive_id` in BLAST headers and in `phylo_match.py`'s `run_blast()` parser (`int(parts[1])`); TEMPURA pseudo-IDs are large integers that will be interpreted as BacDive IDs, causing silent mismatches.  
**Fix:** **RESOLVED** — Introduce a separate `source` column on `organisms` and make TEMPURA-only entries clearly identifiable at the DB level; use negative IDs or a separate `tempura_organisms` table.

---

## Important (should fix soon)

### I-1 — `predict_media.py` and `synthesize_media.py` duplicate the entire template-ranking loop
**Files:** `predict_media.py` lines 444-488, `synthesize_media.py` `pick_template()` lines 392-440  
**Issue:** `pick_template()` in `synthesize_media.py` is a near-copy of the scoring loop in `predict_media.py`'s `main()`. Both iterate `hit_data`, compute `identity_w × therm_w × ph_w × fb_w × cov_w`, and build `media_records`. The two copies have already diverged: `synthesize_media.py` tracks `phylo_identity_best` but `predict_media.py` does not; `predict_media.py` records `thermal_matches`/`thermal_mismatches` but `synthesize_media.py` does not.  
**Fix:** **RESOLVED** — Extract the ranking logic into a shared function in `phylo_match.py` or a new `rank_media.py` module.

---

### I-2 — `phylo_match.py` `format_results()` also duplicates the scoring loop (third copy)
**Files:** `phylo_match.py` lines 701-741  
**Issue:** `format_results()` contains a third independent implementation of the `identity × thermal × pH × fallback` scoring loop, used when running `phylo_match.py` standalone. All three copies must be kept in sync manually.  
**Fix:** **RESOLVED** — Same as I-1 — centralise the ranking function.

---

### I-3 — No connection pooling or context-manager usage; connections leak on exceptions
**Files:** `phylo_match.py` line 848, `predict_media.py` line 357, `synthesize_media.py` line 1032, `validate_confidence.py` line 121  
**Issue:** Database connections are opened with `sqlite3.connect(DB)` and closed at the end of `main()` with `conn.close()`. If any exception is raised before `conn.close()`, the connection leaks. In `validate_confidence.py` a separate connection is opened inside `run_case()` (line 121) but never explicitly closed.  
**Fix:** **RESOLVED** — Use `with sqlite3.connect(DB) as conn:` or `try/finally` blocks.

---

### I-4 — `synthesize_media.py` `recipe_ph` logic is wrong; uses `effective_temp` as a truthy guard for pH
**Files:** `synthesize_media.py` line 1180  
**Issue:** `recipe_ph = args.ph or (effective_temp and 7.0) or 7.0`. This means: if `args.ph` is falsy (None or 0.0), use 7.0 if there is any effective temperature, else 7.0. The expression `effective_temp and 7.0` is semantically nonsensical — a temperature value has nothing to do with defaulting the pH. The result is always 7.0 when `args.ph` is not supplied, which is probably correct, but by accident.  
**Fix:** **RESOLVED** — `recipe_ph = args.ph if args.ph is not None else 7.0`

---

### I-5 — Hardcoded BLAST database path suffix `.ndb` may not exist for older BLAST versions
**Files:** `phylo_match.py` line 838  
**Issue:** `if not os.path.exists(BLAST_DB + ".ndb"):` — `.ndb` is a BLAST+ 2.12+ format file. Earlier BLAST+ versions produce `.nin` instead. On systems with older BLAST+, the check always fails (prints "BLAST database not found"), even when a working database exists.  
**Fix:** **RESOLVED** — Check for `.ndb` OR `.nin`; or call `blastdbcheck` to verify the database is functional.

---

### I-6 — `confidence.record()` has no commit; callers must commit externally or risk partial writes
**Files:** `confidence.py` lines 425-446  
**Issue:** `record()` inserts a row into `prediction_confidences` but does not call `conn.commit()`. Callers in `load_gapseq.py` commit after each full batch (correct), but the intent is not documented. A caller who forgets to commit will silently lose all confidence records for a session.  
**Fix:** Document explicitly at the top of `record()` that the caller must commit, or accept a `commit=False` parameter and commit internally by default.

---

### I-7 — `build_database.py` `bacdive_trait()` opens files inline without a context manager
**Files:** `build_database.py` line 218  
**Issue:** `traits = bacdive_trait(json.load(open(bd_path)))` — the file opened by `open(bd_path)` is never explicitly closed. On CPython this is collected by reference counting, but it is not guaranteed on other implementations and will produce ResourceWarning in test runs.  
**Fix:** **RESOLVED** — `with open(bd_path) as fh: traits = bacdive_trait(json.load(fh))`

---

### I-8 — `load_mebipred.py` idempotent delete uses `f"DELETE ... IN ({qs})"` with `(table, *ids)` — SQL injection risk
**Files:** `load_mebipred.py` lines 181-184  
**Issue:** The delete loop builds `f"DELETE FROM prediction_confidences WHERE related_table=? AND related_id IN ({qs})"` and passes `(table, *ids)` as parameters. The `qs` is constructed from `"?" * len(ids)` which is safe, but `table` is a string from a local list `[("protein_metal_binding", ...), ...]` — currently not user-supplied, so not an active injection risk. However the same pattern is used in `load_genomespot.py` line 135 with `old_ids` that could be long (for large proteomes), generating extremely long SQL strings.  
**Fix:** Use a single `DELETE ... WHERE genome_id = ? AND related_table = ?` join query instead of listing IDs.

---

### I-9 — `media_format.py` has a non-registerd source `"media_format"` in confidence module
**Files:** `media_format.py` line 186, `confidence.py` lines 87-103  
**Issue:** `predict_format()` constructs `ConfidenceScore(value=conf_val, source="media_format", ...)`. The string `"media_format"` is not in `SOURCE_BASELINES` or `SOURCE_RATIONALES` in `confidence.py`. This means the source will not be seeded into `source_confidence` by `populate_source_table()`, and any call to `score("media_format", ...)` will return the generic 0.50 default rather than a meaningful baseline.  
**Fix:** Add `"media_format": (0.60, 0.90)` to `SOURCE_BASELINES` (decision tree output is inherently uncertain) and register the corresponding rationale.

---

### I-10 — `synthesize_media.py` uses `conn.executescript(SCHEMA_SQL)` inside `persist_prediction()` which auto-commits any open transaction
**Files:** `synthesize_media.py` line 717  
**Issue:** `sqlite3.Connection.executescript()` issues an implicit `COMMIT` before executing the script. If `persist_prediction()` is called while an explicit transaction is open (e.g., during `--simulate-knockout`, where `conn.execute("BEGIN")` was called at line 1045), `executescript` will commit the transaction, causing the simulation data to be permanently written rather than rolled back.  
**Fix:** Use `conn.execute(...)` for each DDL statement individually (since the tables are created with `IF NOT EXISTS`), or call `executescript` only once at startup before any data transactions.

---

### I-11 — `predict_media.py` `print_report()` uses a hardcoded string `"12,318 reference sequences"` which will become stale
**Files:** `predict_media.py` line 808  
**Issue:** The provenance block prints `"16S BLAST against 12,318 reference sequences"` regardless of the actual database size. As new TEMPURA/BacDive sequences are added, this number becomes inaccurate.  
**Fix:** Query `SELECT COUNT(*) FROM organisms WHERE ...` or count FASTA records at BLAST database build time and store the count as a metadata file.

---

## Minor (fix when convenient)

### M-1 — `infer_query_thermal_class()` in `phylo_match.py` shadows the module-level `confidence` import with a local variable
**Files:** `phylo_match.py` line 263  
**Issue:** Inside `infer_query_thermal_class()`, the variable `confidence = votes[best_class] / total_vote` (line 263) shadows the `import confidence` at the top of the file. Any use of `confidence.score(...)` or `confidence.ConfidenceScore(...)` after line 263 within that function would silently fail with `AttributeError: 'float' object has no attribute 'score'`. Currently no such call exists inside that function, but it is a latent bug.  
**Fix:** Rename the local variable to `confidence_fraction` or `conf_frac`.

---

### M-2 — `integrate_tempura.py` `aggregate_tempura()` uses floor-median (integer division)
**Files:** `integrate_tempura.py` line 97  
**Issue:** `entry["topt"] = sorted_t[len(sorted_t) // 2]` computes a floor-median, which for an even-length list always picks the lower of the two central values. This is a minor scientific inaccuracy that could matter when two studies disagree by several degrees.  
**Fix:** Use `statistics.median()` for a proper median.

---

### M-3 — `integrate_tempura.py` column name `"16S_accssion"` is a typo inherited from TEMPURA
**Files:** `integrate_tempura.py` line 87  
**Issue:** `r["16S_accssion"]` — the key is misspelled (should be `"16S_accession"`). This will fail silently (returning `None`) if TEMPURA ever fixes the typo in a future release, or fail with `KeyError` if the field is removed.  
**Fix:** Add a comment noting the typo comes from the source data and is intentional; or use `r.get("16S_accssion") or r.get("16S_accession")`.

---

### M-4 — `compatibility.py` `check_compatibility()` calls `populate_rules(conn)` on every invocation
**Files:** `compatibility.py` lines 207, 139-155  
**Issue:** `check_compatibility()` calls `populate_rules(conn)` unconditionally at the top, which deletes all existing rules and re-inserts them from the in-memory constant. This runs on every recipe check (called once per `synthesize_media.py` run), doing an unnecessary DELETE + 13× INSERT.  
**Fix:** Check whether rules already exist: `if conn.execute("SELECT COUNT(*) FROM precipitation_rules").fetchone()[0] > 0: return`. Or cache the rules check in the module.

---

### M-5 — `synthesize_media.py` `_template_has_metal_salt()` constructs regex objects on every call
**Files:** `synthesize_media.py` lines 562-573  
**Issue:** Inside `_template_has_metal_salt()`, the list of `re.compile(p, ...)` patterns is rebuilt from scratch on every invocation. This function is called once per metal per `add_metal_supplements()` call.  
**Fix:** Pre-compile the regex patterns at module level (or cache them with `functools.lru_cache`).

---

### M-6 — `load_thermodynamics.py` `load_compounds()` deletes then re-inserts each compound row one at a time
**Files:** `load_thermodynamics.py` lines 74-82  
**Issue:** For each row in the TSV, the loader does `DELETE ... WHERE compound_name=? AND phase=?` followed by `td.insert_compound(...)`. This is O(n) individual transactions. For large thermodynamic tables (307 compounds × 370 reactions = ~677 rows) performance is acceptable, but the pattern is inconsistent with the batch approach used in `load_gapseq.py`.  
**Fix:** Use `INSERT OR REPLACE` (the table already has a `UNIQUE (compound_name, phase)` constraint) or do a single `DELETE FROM thermodynamic_compounds` before the loop when a full reload is intended.

---

### M-7 — `synthesize_media.py` `Component` uses `__slots__` but `confidence` attribute name clashes with the imported module
**Files:** `synthesize_media.py` lines 354-368  
**Issue:** `Component.__slots__` declares `"confidence"` as a slot name, which works fine. However, in the same file `import confidence` is at the top, and within `add_energy_metabolism_components()` at line 651, `confidence.score(...)` is called. The slot name on an *instance* does not shadow the module name, so this is not actually a bug today — but the naming is confusing and could cause mistakes when reading or extending the code.  
**Fix:** Rename the slot and attribute to `confidence_obj` (the `__init__` parameter is already named `confidence_obj`; the slot is named `confidence` — they should match).

---

### M-8 — `predict_media.py` has a separate LOW/MODERATE/GOOD/HIGH confidence system that duplicates `confidence.py`
**Files:** `predict_media.py` lines 588-596  
**Issue:** `print_report()` re-implements a four-tier classification (`LOW/MODERATE/GOOD/HIGH`) using raw thresholds (88% identity → GOOD, 95% → HIGH) instead of calling `confidence.category()`. The threshold values are slightly different from those in `confidence.py` (e.g., the module uses 0.80/0.95 boundaries, but this code uses 90/95/97% identity directly). Two classification systems for the same concept.  
**Fix:** Use `confidence.score("phylo_16s", "identity_pct", best_id).category` for the report label.

---

### M-9 — `fetch_16s_sequences.py` opens the output FASTA in append mode without truncating on first run
**Files:** `fetch_16s_sequences.py` line 76  
**Issue:** `fasta_handle = open(FASTA_OUT, "a")` appends to the file. The resumption logic on lines 65-72 checks which accessions are already present. However if the file was partially downloaded and then corrupted mid-record, the deduplication check (which only looks at `>` headers) would not detect the corruption and would append duplicates or partial sequences.  
**Fix:** Implement a proper checkpoint file (e.g., `16s_downloaded.json`) that lists completed accessions, rather than parsing the FASTA for deduplication.

---

### M-10 — `run_mebipred.py` silences TensorFlow with environment variables set after import
**Files:** `run_mebipred.py` lines 22-25  
**Issue:** `os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")` is called near the top of the file, before the TF imports. But `TF_USE_LEGACY_KERAS = "1"` is also set here. If TensorFlow is already imported (e.g., in a test or interactive session), changing `os.environ` after the fact has no effect. This is a common TF pitfall.  
**Fix:** Document that this script must be the first thing to import TensorFlow in the process. For robust suppression, set these in the calling shell or a wrapper script.

---

### M-11 — `phylo_match.py` `get_organism_info()` runs two queries: SELECT * then SELECT * LIMIT 0 for column names
**Files:** `phylo_match.py` lines 358-366  
**Issue:** `get_organism_info()` fetches the row with `SELECT *` then gets column names with a second `SELECT * FROM organisms LIMIT 0`. This is called once per BLAST hit (potentially 10-20 times per query). The column-name query can be eliminated.  
**Fix:** Hardcode the column list (the schema is stable) or use `conn.row_factory = sqlite3.Row` at connection open time and index columns by name.

---

## Style (cosmetic / conventions)

### S-1 — Inconsistent docstring style between files
`confidence.py`, `thermodynamics.py`, `compatibility.py` have complete Google-style or NumPy-style docstrings on all public functions. `build_database.py`, `integrate_tempura.py`, and all downloader scripts have module docstrings but no function-level docstrings. Phase 2 contributors will need to reverse-engineer function intent from reading the body.

---

### S-2 — `from __future__ import annotations` used only in some files
Present in `confidence.py`, `compatibility.py`, `thermodynamics.py`, `load_thermodynamics.py`, `synthesize_media.py`. Absent from `phylo_match.py`, `predict_media.py`, `carbon_and_gas.py`, `media_format.py`, and all loader/downloader scripts. Should be uniform (either all or none) for Python 3.9 compatibility.

---

### S-3 — Magic numbers for thermal class boundaries in two places
`THERMAL_CLASSES` in `phylo_match.py` (line 30-35) defines the same 20/45/80°C thresholds that `predict_media.py` implicitly uses. `media_format.py` uses `> 65°C` for gellan gum — a third, related threshold. These should all come from a single constants file.

---

### S-4 — `load_gapseq.py` has a `TEST_QUERY` string and print block that are effectively dead code
**Files:** `load_gapseq.py` lines 396-505  
**RESOLVED** — The bottom half of `load_gapseq.py`'s `main()` (from line 469 onwards) runs a test query and prints results to stdout. This is useful during development but is not behind a `--verbose` flag and cannot be suppressed when the loader is called programmatically as part of a pipeline.

---

### S-5 — `synthesize_media.py` `main()` is 260 lines; should be decomposed
**Files:** `synthesize_media.py` lines 985-1244  
The `main()` function chains 10 numbered steps with inline logic for knockout simulation, thermodynamic viability injection, compatibility penalty application, and overall confidence composition. These should each be their own named function to allow unit testing of individual steps.

---

### S-6 — `compatibility.py` `format_warnings()` uses Unicode symbols (✗, ⚠, ○)
**Files:** `compatibility.py` lines 393-394  
These render correctly in terminals with UTF-8 locale but may produce garbled output or `UnicodeEncodeError` on Windows terminals or if stdout is redirected to a file opened in ASCII mode. Consider using ASCII alternatives (`[!]`, `[W]`, `[ ]`) or wrapping with `sys.stdout.buffer.write`.

---

## Architecture Notes

### Testing gaps

| Module | Test coverage |
|---|---|
| `confidence.py` | Good — `test_confidence.py` covers scoring, combine, DB, and realistic scenarios |
| `thermodynamics.py` | Good — `test_thermodynamics.py` covers interpolation, viability, math, and persistence |
| `phylo_match.py` | None — zero unit tests for `run_blast()`, `get_media_with_fallback()`, `infer_query_thermal_class()`, etc. |
| `predict_media.py` | None — only tested indirectly via `validate_confidence.py` end-to-end runs |
| `synthesize_media.py` | None |
| `compatibility.py` | None |
| `carbon_and_gas.py` | None |
| `media_format.py` | None |
| `load_gapseq.py` | None |
| `load_genomespot.py` | None |
| `load_mebipred.py` | None |
| `build_database.py` | None |
| `integrate_tempura.py` | None |
| All downloaders | None |

`validate_confidence.py` provides integration-level smoke tests for the confidence pipeline but requires a populated database and BLAST database to run — it cannot be used in CI without data.

### Missing database indices

- **RESOLVED** — `organisms(ncbi_taxid)` — queried in `integrate_tempura.py` `merge_into_existing()` line 113 with no index
- **RESOLVED** — `organisms(species)` — queried repeatedly in `integrate_tempura.py` and `phylo_match.py` fallback queries with no index
- **RESOLVED** — `media_compounds(compound_id)` — only `media_id` is indexed; reverse lookups (find media containing a compound) are unindexed full-table scans
- **RESOLVED** — `organism_media` — indexed on `organism_id` and `media_id` but not on `growth` — every media retrieval filters `WHERE om.growth = 1`

### N+1 query patterns

- `predict_media.py` `main()` lines 424-428: for each of the top-N hits, calls `get_organism_info()` (1 query) + `get_media_with_fallback()` (1-3 queries depending on fallback level). With N=10 hits this is 10-40 round-trips. Fine for SQLite locally; would need batching for a web API.
- `predict_media.py` lines 460-463: calls `get_media_recipe()` per unique medium ID. With 50 candidate media this is 50 separate queries.

### Orphaned / not-yet-used schema elements

- `genome_carbon_sources` — referenced in `media_format.py` but never created (see C-3)
- `genome_hydrogenases` — referenced in `carbon_and_gas.py` but never created (see C-4)
- `media_solutions` — mentioned in CLAUDE.md schema spec but not created by `build_database.py`
- `organism_traits` — mentioned in CLAUDE.md schema spec but not created
- `organism_environments` — mentioned in CLAUDE.md schema spec but not created
- `genome_auxotrophies` is a VIEW (defined in `load_gapseq.py`), but `predict_media.py` calls `get_auxotrophies()` which queries it directly as a table — works, but only after `load_gapseq.py` has been run at least once to create the view

### Placeholder data in production path

`thermodynamics.py` contains `PLACEHOLDER_COMPOUNDS` and `PLACEHOLDER_REACTIONS` with placeholder knallgas values (lines 394-438). The real A&S data (63 compounds + 44 reactions) is now loaded alongside the 3 placeholder compounds + 1 placeholder reaction. The `seed_placeholders()` function skips if real data exists, so the placeholders don't affect viability checks (which use named reactions like "Sulfate reduction to H2S (H2 donor)" that come from the real data). However, the placeholder rows should be cleaned up to avoid confusion; and any call to `td.get_reaction("knallgas_H2_O2")` would still return the placeholder values rather than the real A&S "Knallgas reaction (dissolved)".  
**Fix:** **RESOLVED** — Delete the 3+1 placeholder rows from the DB now that real data is loaded; or rename them to avoid collisions with real reaction names.
