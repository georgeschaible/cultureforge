# CultureForge — GitHub Readiness Scan Report

**Date:** 2026-05-02
**Scope:** Pre-public-release scan: hardcoded paths, credentials, personal info, generated files, internal-context references, documentation cross-references, and validation-statistics accuracy.

---

## Section 1: Codebase scan findings

### 1.1 Hardcoded absolute paths

**Severity:** Medium — most are in shell scripts intended for the development environment; reproducibility cost if not parameterized but not a blocker for first push.

| File | Line | Current value | Recommended fix |
|---|---:|---|---|
| `run_marker_blast.py` | 108 | `"PATH": "/home/george/miniconda3/envs/gapseq/bin:" + os.environ.get(...)` | Make conditional: only inject when conda env path exists; fall back to `os.environ["PATH"]` |
| `build_marker_blast_db.py` | 64 | `"PATH": "/home/george/miniconda3/envs/gapseq/bin:..."` | Same conditional fix |
| `run_blind_correct.sh` | 3-4 | `/home/george/miniconda3/envs/gapseq/bin`, `/home/george/cultureforge` | Replace with `${PATH}` and `$(dirname "$0")` |
| `run_gapseq_dvulgaris.sh` | 6-7 | `/home/george/cultureforge/data/...` | Replace with `$(dirname "$0")/data/...` |
| `run_gapseq_ecoli.sh` | 10-11 | Same | Same fix |
| `run_blind_v2_gapseq.sh` | 3-4 | Same | Same fix |
| `run_blind_gapseq.sh` | 5 | `ROOT=/home/george/cultureforge` | `ROOT="$(cd "$(dirname "$0")" && pwd)"` |
| `run_blind_all.sh` | 3-4 | Same | Same fix |
| `run_validation_sequential.sh` | 9 | `PROJ=/home/george/cultureforge` | Same fix |
| `run_validation_batch.sh` | 7 | Same | Same fix |
| `data/build_phase2d_caches.py` | 27 | `ROOT = Path("/home/george/cultureforge")` | `ROOT = Path(__file__).resolve().parent.parent` |
| `data/diagnostic_markers/scan_test_set_conflicts.py` | 15 | Same pattern | Same fix |
| `data/validation/run_phase1_5m_blind_capability.sh` | 6, 8 | Same | Same fix; PY hardcoded `/home/george/miniconda3/envs/genomespot/bin/python` |
| `data/validation/run_phase1_5m_capability.sh` | 7, 9 | Same | Same fix |
| `data/validation/run_phase2d_validation.py` | 16 | `ROOT = Path("/home/george/cultureforge")` | `ROOT = Path(__file__).resolve().parents[2]` |
| `data/validation/run_phase1_5l_hit_patterns.py` | 19, 22, 327 | Same + BLASTP path | Replace ROOT with `__file__`-derived; BLASTP fall back to `shutil.which("blastp")` |
| `data/validation/run_phase1_5n_capability.sh` | 7, 10 | Same | Same fix |
| `data/validation/apply_curation_flips_1_5m.py` | 16 | Same ROOT | Same fix |
| `data/validation/run_phase1_5m_hit_patterns.py` | 19, 23 | Same | Same fix |
| `PROGRESS.md` | 286 | `/home/george/cultureforge/` | Replace with `<project-root>` or remove the line |
| `RECIPE_VALIDATION_V12.md` | 7 | `/home/george/cultureforge/RECIPE_VALIDATION_V11.md` | Replace with relative path |

**`.claude/settings.local.json`** has dozens of hardcoded paths but this file is Claude Code session state and will be gitignored; not addressed here.

### 1.2 Credentials and authentication

**Status: CLEAN.** No API keys, passwords, or tokens are embedded in tracked Python source.

- `bacdive_client.py` and `download_bacdive.py` use the public `https://api.bacdive.dsmz.de/fetch/{id}` endpoint without authentication. (Note: BacDive's full API does require auth for some endpoints; current code uses the unauthenticated cache-fallback pattern.)
- `mediadive_client.py` and `download_mediadive.py` use `https://mediadive.dsmz.de/rest` without auth.
- No `.env`, `credentials.*`, or `config.local.*` files exist in the project.
- `vendor/GenomeSPOT/.../download_trait_data.py` (vendored MIT-licensed code from Cultivarium) does have BacDive authentication code, but it reads credentials from a user-supplied file at runtime — no credentials embedded.

### 1.3 Personal information

| File | Line | Item | Decision |
|---|---:|---|---|
| `fetch_16s_sequences.py` | 19 | `Entrez.email = "george.schaible@gmail.com"` | Replace with `os.environ.get("ENTREZ_EMAIL", "your-email@example.com")` and document in README |
| `fetch_tempura_16s.py` | 16 | Same | Same fix |
| `PHASE_1_5_FIXES.md` | 153 | `"George to review the full distribution..."` (development note) | Replace with neutral phrasing or remove sentence |

Author name in citation files (LICENSE, CITATION.cff, README) is appropriate and required for attribution.

### 1.4 Generated files / large binaries

| Item | Size | Plan |
|---|---:|---|
| `data/cultureforge.db` | 410 MB | gitignore (option A from prompt — don't ship; document rebuild) |
| `data/16s_reference.fasta` | 93 MB | gitignore — generated reference |
| `data/blastdb/16s_ref.*` | 25 MB | gitignore — built from FASTA |
| `data/genomes/*.fasta` | 92 MB | gitignore — downloaded genome assemblies |
| `data/gapseq/*` | 341 MB | gitignore — gapseq output (RDS, XML, TBL) |
| `data/bacdive/strains/*.json` | 304 MB | gitignore — cached BacDive records (rebuildable) |
| `data/mediadive/all_media.json` | 20 MB | gitignore — cached MediaDive records |
| `data/mediadive/*.json`, `data/mediadive/medium_strains/*.json` | varies | gitignore — same |
| `data/validation/*.log` | varies | gitignore |
| `data/*.log` | varies | gitignore |
| `data/diagnostic_markers/blastdb_*.{phr,pin,psq,pdb,pot,ptf,pto}` | varies | gitignore — built from `.fasta` reference files |
| `__pycache__/`, `data/__pycache__/`, `vendor/.../__pycache__/` | small | gitignore standard Python pattern |
| `vendor/GenomeSPOT/genome_spot.egg-info` | small | gitignore |
| `data/sentinel/*/genome_db.{phr,pin,psq,...}` | small | gitignore — built from proteome.faa |
| `cultureforge.db` (root, 0 bytes) | 0 | **Delete stub file** before push (leftover from earlier session) |
| `cultureforge.sqlite` (root, 0 bytes) | 0 | **Delete stub file** before push |

**Vendored `vendor/GenomeSPOT/`** is 53 MB MIT-licensed code (Cultivarium 2024) — keep with attribution; not gitignored.

**Reference FASTA files in `data/diagnostic_markers/*_refs.fasta`** are small (curated marker references, typically <100 KB each) and ARE part of the project — keep tracked, do not gitignore.

### 1.5 Internal-context references

**Status: CLEAN.** Only one reference: `CLAUDE.md` line 235 mentions "Claude Code" in the architecture roadmap as a tool that could be used to generate a web interface (forward-looking, neutral context). Acceptable for public release.

`PROGRESS.md` and `PHASE_3_CLOSEOUT.md` reference specific dates (2026-04 / 2026-05) documenting development timeline — appropriate transparency for academic open-source release.

---

## Section 2: Documentation cross-reference findings

### 2.1 Documented features vs actual code

| Documented | Actual | Status |
|---|---|---|
| `inspect <genome_id>` accepts numeric ID | YES (handles int conversion) | OK |
| `inspect <accession>` (NCBI accession string) | YES (matches against `genomes.accession`) | OK |
| `inspect <species_name>` (fuzzy match) | Partial — fuzzy match works against `organisms.species`, but test-set genomes have species in `notes` field with underscores (e.g., `"Validation organism: Methanococcus_jannaschii"`). Match by space-separated species name fails | **Documentation inaccurate** — README/TESTER_QUICKSTART should not promise space-separated species name matching. Recommend numeric ID as primary identifier in docs |
| `--temperature 70` | YES | OK |
| `--pH 6.5` (capital H) | NO — flag is `--ph` (lowercase) | **Documentation bug** — README rewrite (Phase 3.8) wrote `--pH`; actual implementation is `--ph`. Fix in docs |
| `--salinity 0.5` | YES | OK |
| `--section recipe` (and other sections) | YES (8 sections supported) | OK |
| `--json --output recipe.json` | YES | OK |
| `--list` shows test-set genomes | YES | OK |
| Marker-BLAST-only sentinel pattern | YES | OK |

### 2.2 Internal documentation links

All cross-referenced .md files exist at the expected paths. **No broken links** in the user-facing documentation. References to `data/diagnostic_markers/REFERENCE_CURATION.md` and `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` resolve correctly.

### 2.3 Validation statistics accuracy

| Cited in docs | Actual current | Discrepancy |
|---|---|---|
| 7/26 ≥70%, 7/26 in 50-69%, 12/26 <50% | 6 ≥70%, 7 in 50-69%, 12 <50%, 1 escalated (Scalindua, no score) | One organism's status changed: Scalindua profunda escalated post-Phase-3.4 E.1 reclassification. The 26-row table assumed Scalindua at 100% (functional-neighbor); now no V12 score |

**Recommended fix:** Update docs to "6/26 ≥70%, 7/26 in 50-69%, 12/26 <50%, 1/26 escalated (Scalindua, no V12 score)" or simply "6 / 7 / 12 / 1-escalated."

---

## Section 3: Standard files needed (Task 3 — to be added)

- [ ] `LICENSE` (MIT, with explicit author name)
- [ ] `CITATION.cff` (with author info, ORCID, GitHub username)
- [ ] `.gitignore` (covering all generated/cached files identified in 1.4)
- [ ] `CONTRIBUTING.md`
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md`
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md`
- [ ] `.github/ISSUE_TEMPLATE/validation_feedback.md`
- [ ] README pre-publication disclaimer at top

**User-supplied fields needed before commit:**
- Full author name (for LICENSE + CITATION.cff)
- Affiliation (for CITATION.cff)
- ORCID (optional, for CITATION.cff)
- GitHub username (for CITATION.cff URL fields)
- Contact email for citation guidance / disclaimer
- Decision on database distribution strategy (Option A: don't ship, document rebuild — recommended)

---

## Section 4: Repository setup decisions

### Database distribution

**Recommended: Option A — don't ship the database.**

Rationale:
- Repo size stays manageable (~50-60 MB without DB; ~410+ MB with)
- Reproducibility documented via the validation pipeline scripts
- Eliminates Git LFS quota or external-hosting dependency for first push
- Future enhancement: ship the DB via GitHub Release attachment or external download

Document in README: "To reproduce the validation results, follow the build pipeline scripts in `data/validation/`. Pre-built database snapshots may be made available via release attachments after first public push."

### Documentation organization

**Recommended: keep current flat structure for first push.**

Rationale:
- All major docs at project root makes them immediately discoverable
- Reorganizing to `docs/` directory would require updating ~20 cross-references across docs
- Current structure already separates user-facing (README, USER_GUIDE_LIMITATIONS, TESTER_*) from developer-facing (README_DEV, LIMITATIONS, CLAUDE) by filename convention
- Reorganization can happen post-first-push if needed

Add note in README: "All major documentation is at the project root for ease of discovery. Files prefixed `TESTER_*` are external-tester onboarding; `*_DEV.md` and `LIMITATIONS.md` are developer-facing."

---

## Section 5: Issues to resolve in Task 5

1. **Fix README/TESTER_QUICKSTART**: change `--pH` → `--ph` references
2. **Fix README/TESTER_QUICKSTART**: clarify identifier matching — recommend numeric IDs as primary; species-name fuzzy match is best-effort
3. **Update validation statistics**: change 7/7/12 → 6/7/12/1-escalated in README, VALIDATION_REPORT, USER_GUIDE_LIMITATIONS, PHASE_3_CLOSEOUT, TESTER_QUICKSTART
4. **Fix `Entrez.email`**: replace hardcoded george.schaible@gmail.com in fetch_16s_sequences.py + fetch_tempura_16s.py with env-var lookup
5. **Fix `PHASE_1_5_FIXES.md` line 153**: replace "George to review..." with neutral phrasing
6. **Make hardcoded conda paths conditional**: in run_marker_blast.py and build_marker_blast_db.py, only inject the conda PATH when the directory exists
7. **Replace `ROOT = Path("/home/george/cultureforge")`** in 6 Python utility scripts with `Path(__file__).resolve().parents[N]`
8. **Replace `ROOT=/home/george/cultureforge`** in 8 shell scripts with `$(cd "$(dirname "$0")" && pwd)` pattern
9. **Delete stub files**: `cultureforge.db` and `cultureforge.sqlite` (zero-byte) at project root
10. **Update CLAUDE.md line 235**: optional — the "Claude Code" reference is OK to keep but could be neutralized to "modern AI-assisted development tools"

Issues 1-3 and 9 are the highest priority for first push. Issues 4-8 improve reproducibility but are not blockers. Issue 10 is cosmetic.

---

## Section 6: Smoke-test results

**Pre-fix:**

```
python3 cultureforge.py inspect --list                       OK (lists 26 organisms + sentinels)
python3 cultureforge.py inspect 8 --section recipe          OK (Methanocaldococcus methanogenic)
python3 cultureforge.py inspect 32 --section recipe         OK (E. coli aerobic chemoorganotrophic)
python3 cultureforge.py inspect 28 --section recipe         OK (Methanoperedens ANME-2d nitrate-coupled)
python3 cultureforge.py inspect 901 --section recipe        OK (Wolinella DNRA, sentinel)
python3 cultureforge.py inspect 902 --section recipe        OK (Nitrobacter NOB Type B, sentinel)
python3 cultureforge.py inspect 903 --section recipe        OK (Methanosarcina methanogenic, sentinel)
python3 cultureforge.py inspect 8 --json                    OK
python3 cultureforge.py inspect 8 --temperature 70 --ph 6.5 --salinity 0.5  OK
python3 cultureforge.py inspect 8 --temperature 70 --pH 6.5  FAILS  (capital --pH not recognized)
python3 cultureforge.py inspect "Methanococcus jannaschii"  FAILS  (space-separated species name doesn't match underscore-stored notes)
python3 cultureforge.py inspect Methanocaldococcus          FAILS  (no match — gid=8 stored as Methanococcus_jannaschii in notes)
python3 cultureforge.py inspect 8                           OK (numeric ID always works)
```

**Recommendation:** for first push, all numeric ID + accession + `--section` + `--json` paths work cleanly. The two failing cases (`--pH` capital flag, space-separated species name) need documentation fixes (Issue 1, 2 above). Numeric IDs are the reliable user-facing path.

---

## Section 7: Post-`git init` findings (added after live staging test)

When the user ran `git init && git add -A` and inspected staged files, several issues that the initial scan missed surfaced — **all now resolved**:

### Critical issues found and fixed

1. **`data/thermo/amend_shock_2001.pdf` (1.25 MB)** — Copyrighted PDF (Amend & Shock 2001 FEMS Microbiol Rev). Public redistribution is a copyright violation. **Fixed:** added `data/thermo/*.pdf` to .gitignore.

2. **`data/tempura/tempura.csv` (1.4 MB)** — TEMPURA is CC BY-NC 3.0 (non-commercial). Incompatible with MIT-licensed redistribution. **Fixed:** added `data/tempura/tempura.csv` and `data/tempura/new_16s_accessions.json` to .gitignore. Users download from togodb.org/db/tempura.

3. **`vendor/GenomeSPOT/.git/` (33 MB embedded git history)** — Triggered the "embedded git repository" warning and bloated the repo. **Fixed:** deleted `vendor/GenomeSPOT/.git/`; added the path to .gitignore as belt-and-braces.

4. **`data/mediadive/media/*.json` (3,336 cached medium recipes)** — The original .gitignore had `data/mediadive/medium_*.json` but the actual cached files live at `data/mediadive/media/<id>.json`. The pattern was wrong. **Fixed:** added `data/mediadive/media/` and `data/mediadive/index.json` to .gitignore. MediaDive is CC BY 4.0 so technically redistributable, but 3,336 small files is bloat — better to have users rebuild via `download_mediadive.py`.

5. **`vendor/GenomeSPOT/notebooks/` (13 MB), `tests/test_data/` (5.5 MB), `data/holdouts/` (~900 KB), `build/`** — Bulky non-runtime content. **Fixed:** added each to .gitignore. The vendored runtime (source code + LICENSE + sklearn model `.joblib` files) remains tracked.

6. **Derived 16S indices, CAZyme generated inputs, validation profile dumps** — Several large generated files (`data/16s_accessions.json`, `data/cazyme/*/uniInput.faa`, `data/validation/phase*_capability_profiles.txt`). **Fixed:** added each to .gitignore.

### Repository size impact

| Metric | Before live staging test | After all fixes |
|---|---:|---:|
| Staged files | 3,798 | 503 |
| Working-tree size of staged files | ~90 MB | 4.3 MB |
| Embedded git repo warning | Yes (vendor/GenomeSPOT) | None |
| Copyrighted PDF in repo | Yes (1.25 MB) | None |
| CC-BY-NC TEMPURA CSV in repo | Yes (1.4 MB) | None |

### Verified gitignore exclusions

```
data/cultureforge.db                       → .gitignore:56:data/cultureforge.db
data/thermo/amend_shock_2001.pdf          → .gitignore:71:data/thermo/*.pdf
data/tempura/tempura.csv                  → .gitignore:75:data/tempura/tempura.csv
data/mediadive/media/<id>.json            → .gitignore:65:data/mediadive/media/
data/bacdive/strains/<id>.json            → .gitignore:62:data/bacdive/strains/
__pycache__/                              → .gitignore:2:__pycache__/
.claude/                                  → .gitignore:53:.claude/
data/diagnostic_markers/blastdb_*.phr     → .gitignore:92:data/diagnostic_markers/blastdb_*.phr
```

### What stays tracked

- 31 diagnostic-marker FASTA reference files (`data/diagnostic_markers/*_refs.fasta`)
- `data/pathway_definitions.json` (the central capability definitions)
- 4 sentinel validation reports (`data/sentinel/`)
- 66 files of the slimmed vendor/GenomeSPOT (LICENSE, README, source, sklearn models)
- All Python source files
- 25+ markdown documentation files
- LICENSE, CITATION.cff, CONTRIBUTING.md, .gitignore, .github/ISSUE_TEMPLATE/

### Lesson learned

**Always run a live `git init && git add -A && git ls-files` test before declaring repo readiness, not just a static scan.** The static `find` and `du` scans I ran initially missed:
- That `data/mediadive/media/` was a different path from the `data/mediadive/medium_*.json` pattern I'd written
- That `vendor/GenomeSPOT/.git/` would trigger embedded-repo warnings (only visible after `git add`)
- That CC BY-NC vs MIT licensing incompatibility for TEMPURA wasn't reflected in the initial gitignore

The live-staging check should be added as the FIRST step of any future readiness pass.

---

## Final assessment

**The repository is structurally ready for first public push** after Tasks 3 (add standard files) and Task 5 (issue resolution) complete. The core code paths work cleanly; the documentation cross-references resolve; no credentials or sensitive personal info is embedded in tracked source.

**Pre-push completion checklist:**
- [ ] Task 3: standard OSS files written
- [ ] Task 5: Issues 1, 2, 3, 9 resolved (high priority)
- [ ] Task 5: Issues 4-8 resolved (medium priority — reproducibility polish)
- [ ] Author info filled into LICENSE, CITATION.cff, README disclaimer, CONTRIBUTING.md
- [ ] `.gitignore` confirmed comprehensive via `git status --ignored`
- [ ] Final smoke test passes
- [ ] Initial commit message drafted

Estimated time to push-ready: 1-2 hours after author info is supplied.
