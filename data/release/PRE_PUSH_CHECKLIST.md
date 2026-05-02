# CultureForge — Pre-Push Checklist + Initial Commit Guidance

**Status:** Ready for first public push pending the user-supplied fields below.

---

## User-supplied fields needed before commit

The following placeholders need to be filled in by the user. Search-and-replace each:

| Placeholder | Where it appears | What to replace with |
|---|---|---|
| `[YOUR NAME]` | LICENSE | Full author name (e.g., "Jane Q. Doe") |
| `[FIRST NAME]`, `[LAST NAME]` | CITATION.cff | Same — split into given-names / family-names |
| `[AFFILIATION]` | CITATION.cff | Institution / lab name (e.g., "Volland Lab, Montana State University") |
| `[GITHUB_USERNAME]` | CITATION.cff (3 lines) | GitHub username (e.g., "georgeschaible") |
| `[CONTACT_EMAIL]` | README.md (disclaimer), CITATION.cff (preferred-citation notes), CONTRIBUTING.md (3 places) | Author contact email for citation guidance and contributions |
| `# orcid: ...` (commented out) | CITATION.cff | Uncomment + fill ORCID URL if available |

Suggested one-liner search:

```bash
grep -rn '\[YOUR NAME\]\|\[FIRST NAME\]\|\[LAST NAME\]\|\[AFFILIATION\]\|\[GITHUB_USERNAME\]\|\[CONTACT_EMAIL\]' \
    LICENSE CITATION.cff CONTRIBUTING.md README.md
```

After replacement, verify nothing remains:

```bash
grep -rn '\[YOUR NAME\]\|\[CONTACT_EMAIL\]\|\[GITHUB_USERNAME\]' --include="*.md" --include="*.cff" .
```

---

## Pre-commit checklist

Run each of these from the project root before `git commit`. Confirm the expected output for each.

### 1. Standard files present

```bash
for f in LICENSE CITATION.cff .gitignore CONTRIBUTING.md README.md; do
  test -f "$f" && echo "✓ $f" || echo "✗ MISSING: $f"
done
test -d .github/ISSUE_TEMPLATE && echo "✓ .github/ISSUE_TEMPLATE/" || echo "✗ MISSING"
```

Expected: 5 ✓ files + 1 ✓ directory.

### 2. README pre-publication disclaimer present

```bash
head -5 README.md | grep -q "Pre-publication notice" && echo "✓ disclaimer present" || echo "✗ disclaimer missing"
```

### 3. No hardcoded /home paths in tracked code

```bash
grep -rn "/home/" --include="*.py" --include="*.sh" --include="*.md" \
  --exclude-dir=.claude --exclude-dir=vendor \
  --exclude-dir=bacdive --exclude-dir=mediadive --exclude-dir=release \
  | grep -v "^data/release/" \
  | head
```

Expected: empty output (only `data/release/github_readiness_scan.md` documents historical findings; that path is excluded).

### 4. No personal email hardcoded

```bash
grep -rn "george.schaible@gmail" --include="*.py" --include="*.md" --exclude-dir=data | head
```

Expected: empty output.

### 5. No API credentials

```bash
grep -rn -i "api_key\|password\s*=\s*['\"]" --include="*.py" --exclude-dir=vendor | head
```

Expected: empty output (vendored GenomeSPOT model_training has BacDive auth scaffolding but reads creds from runtime file, not embedded).

### 6. No zero-byte stub files at root

```bash
find . -maxdepth 1 -type f -size 0 | head
```

Expected: empty output.

### 7. Smoke test passes

```bash
python3 cultureforge.py inspect --list 2>&1 | head -3
python3 cultureforge.py inspect 8 --section recipe 2>&1 | grep "PRIMARY"
python3 cultureforge.py inspect 32 --section recipe 2>&1 | grep "PRIMARY"
python3 cultureforge.py inspect 28 --section recipe 2>&1 | grep "PRIMARY"
```

Expected:
- list shows 26+ organisms
- gid=8: `methanogenic`
- gid=32: `aerobic_chemotrophic`
- gid=28: `anme_reverse_methanogenic (ANME-2d, nitrate-coupled)`

### 8. git status clean

```bash
git init  # if not yet initialized
git status --ignored 2>&1 | head -40
```

Expected: tracked files include source code + .md docs + LICENSE + CITATION.cff + CONTRIBUTING.md + .github/. Ignored should include __pycache__/, data/cultureforge.db, data/bacdive/strains/, data/gapseq/, data/genomes/, *.log, .claude/.

---

## Initial commit message

Use this template for the first public commit (HEREDOC keeps formatting clean):

```
git add LICENSE CITATION.cff .gitignore CONTRIBUTING.md README.md README_DEV.md \
        VALIDATION_REPORT.md USER_GUIDE_LIMITATIONS.md PHASE_3_CLOSEOUT.md \
        TESTER_QUICKSTART.md TESTER_FEEDBACK_TEMPLATE.md TESTER_GENOMES_OF_INTEREST.md \
        LIMITATIONS.md CLAUDE.md PROGRESS.md \
        RECIPE_EVALUATION.md RECIPE_VALIDATION_V11.md RECIPE_VALIDATION_V12.md \
        VALIDATION_TIMELINE.md PHASE_1_5_FIXES.md \
        BLIND_VALIDATION.md CAPABILITY_DETECTORS.md DENOVO_DESIGN.md REVIEW.md \
        VALIDATION_SUMMARY.md \
        .github/ISSUE_TEMPLATE/ \
        *.py *.sh \
        data/pathway_definitions.json \
        data/diagnostic_markers/ \
        data/sentinel/ \
        data/release/ \
        data/validation/ \
        data/build_phase2d_caches.py data/__init__.py \
        docs/ \
        vendor/

git commit -m "$(cat <<'EOF'
Initial public release of CultureForge (pre-publication)

CultureForge predicts cultivation media for novel and uncultured bacteria and
archaea from genome sequence. This is a pre-publication release for sharing
with collaborators and external validation.

Key components:
- 19 metabolic capability detectors with empirical validation
- Diagnostic marker BLAST framework with curated reference set (12+ markers
  across the major environmental microbiology metabolisms)
- Recipe composer with thermodynamic gating and acceptor-aware branching
- Published-media comparison metric against DSMZ / BacDive corpus (V12)
- Sentinel pattern for capability validation against named type strains
  (4 sentinels covering methanotrophy, DNRA, NOB Type B, ANME negative-control)

A peer-reviewed manuscript describing the methodology is in preparation.

See README.md for usage; LIMITATIONS.md and USER_GUIDE_LIMITATIONS.md for
documented limitations; VALIDATION_REPORT.md for empirical validation evidence;
PHASE_3_CLOSEOUT.md for the development retrospective.

Validation status: 19 supported metabolic capabilities, all empirically
validated against named-strain or test-set genomes. V12 published-media
comparison: 6/26 ≥70%, 7/26 50-69%, 12/26 <50%, 1/26 escalated.
EOF
)"
```

If the user prefers a more conservative initial commit (everything in one commit so the repo's first state is the polished one):

```
git add .
git commit -m "Initial public release of CultureForge (pre-publication)"
```

The verbose `git add` form above gives explicit visibility into what's being committed; the `git add .` form is shorter but relies entirely on .gitignore to exclude the right files.

---

## Post-push tasks (manual steps for the user)

After the first `git push`:

1. **GitHub repo settings:**
   - Add a one-line repository description: "Predict cultivation media for novel uncultured bacteria and archaea from genome sequence"
   - Add topics: `bioinformatics`, `microbiology`, `cultivation`, `genome-annotation`, `metabolic-prediction`, `microbial-ecology`
   - Optional: enable Discussions if expecting community Q&A

2. **Create initial Release (optional):**
   - Tag: `v0.1.0-pre-publication`
   - Title: "CultureForge v0.1.0 — Pre-publication release"
   - Description: copy from the commit message above
   - Optionally attach a database snapshot tarball as a release asset (separate from the git history due to size)

3. **Verify CITATION.cff renders:**
   - Visit the GitHub repo page; the "Cite this repository" button (right sidebar) should now appear
   - Confirm citation text matches what you intended

4. **README badge updates** (optional polish):
   - Add badges for license, citation, version (e.g., shields.io)
   - These are cosmetic; not required for first push

5. **External validation outreach:**
   - Distribute `TESTER_QUICKSTART.md` + `TESTER_FEEDBACK_TEMPLATE.md` + `TESTER_GENOMES_OF_INTEREST.md` to interested collaborators
   - Set up a feedback channel (GitHub Issues with the validation template, or a shared document)
   - Track received feedback against `data/sentinel/PHASE_3_7_VALIDATION_SUMMARY.md` for any issues that surface

---

## Things NOT to do at first push

- ❌ Do not push the SQLite database (`data/cultureforge.db`, 410 MB) — gitignored
- ❌ Do not push BacDive cached strain JSONs (304 MB) — gitignored
- ❌ Do not push gapseq output trees (341 MB) — gitignored
- ❌ Do not push downloaded genome FASTAs (92 MB) — gitignored
- ❌ Do not skip the `git status --ignored` check — confirm large files are NOT staged
- ❌ Do not force-push or rewrite history on a public branch
- ❌ Do not commit before filling in author placeholders in LICENSE / CITATION.cff / README

---

## Repository size estimate after first push

Tracked content (estimated):
- Python source: ~50 source files, ~1.5 MB total
- Markdown documentation: ~25 docs, ~500 KB total
- Diagnostic marker references (FASTA): ~2 MB total
- Pathway definitions JSON: ~100 KB
- Vendored GenomeSPOT (with .git/.egg-info ignored): ~50 MB
- Issue templates + LICENSE + CITATION + .gitignore: ~10 KB

**Total estimated repo size: 50-60 MB.** Under GitHub's 100 MB per-file and 1 GB per-repo soft limits.
