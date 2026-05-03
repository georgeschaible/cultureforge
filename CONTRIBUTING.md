# Contributing to CultureForge

CultureForge is a research tool in active development. Contributions are welcome.

## Pre-publication context

Until the CultureForge methodology manuscript is published, please coordinate substantive contributions (new capability detectors, methodology changes, framework extensions) with the project maintainer (george.schaible@gmail.com) so attribution and authorship questions are handled appropriately. Bug reports, documentation fixes, and validation feedback do not require prior coordination.

## What to contribute

- **Bug reports** — issues with installation, output errors, unexpected behavior. Open a GitHub issue with the `bug` label using the bug-report template.
- **Feature requests** — proposed new capability detectors, marker additions, recipe composer improvements. Open an issue with the `enhancement` label.
- **Capability additions** — proposing new metabolism coverage. Please review `data/diagnostic_markers/REFERENCE_CURATION.md` for the curation standard before submitting.
- **Validation feedback** — testers can submit feedback using `docs/tester/TESTER_FEEDBACK_TEMPLATE.md`. Open an issue with the `validation` label.
- **Documentation fixes** — typos, broken links, unclear language. Pull requests welcome without prior coordination.

## Standards for new capability additions

If proposing a new capability:

1. **Verification-before-curation:** verify each suggested marker reference at UniProt before adding (the project has caught wrong-protein traps where prompted accessions did not match the claimed function — see `data/diagnostic_markers/REFERENCE_CURATION.md` for examples).
2. **Empirical cross-reactivity assessment:** run a BLAST scan of the new marker references against the 26-organism test set + sentinels. Document the false-positive ceiling and true-positive floor.
3. **Threshold derivation from empirical separation gap:** thresholds (`min_pident`, `min_qcov`) should sit in the empirical gap, not be picked as round numbers. Document the gap data in `REFERENCE_CURATION.md`.
4. **Test-set exclusion:** marker references must not include the test-set genomes themselves (avoid trivial self-matches).
5. **Sentinel validation:** if no test-set genome covers the new capability, add a sentinel organism (gid=900+ pattern, see `data/sentinel/`).
6. **Recipe composer extension:** new capabilities need a corresponding recipe-composer branch. See existing patterns in `compose_recipe.py` and the per-sub-phase review documents in `data/diagnostic_markers/<topic>_review.md`.
7. **Documentation:** add a `data/diagnostic_markers/<topic>_review.md` literature review covering the threshold rationale, cross-reactivity scan, and sentinel validation. Update `docs/LIMITATIONS.md`, `data/diagnostic_markers/REFERENCE_CURATION.md`, `docs/PROGRESS.md`.

## Code standards

- **Python 3.10+** compatible
- **Existing code style** — no specific linter enforced; match surrounding code
- **Docstrings** — document new functions/classes explaining biological rationale, not just code behavior. The project values "why" comments more than "what" comments
- **Tests** — for new functionality where reasonable. The project does not currently have a comprehensive test suite; smoke tests via `cultureforge.py inspect` on representative genomes are the de facto regression check
- **Validation pipeline:** run `python3 cultureforge.py inspect <gid>` on at least 3 representative test-set organisms before committing, and verify V12 scores are byte-identical for all 26 test organisms (sentinels excluded)

## Reporting validation results

External validation submissions follow `docs/tester/TESTER_FEEDBACK_TEMPLATE.md`. Submit via GitHub issue (use the validation template) or directly to the project maintainer.

## Pull-request process

1. Open an issue describing the change before submitting a large PR
2. Branch off `main` and use a descriptive branch name (e.g., `feature/comammox-amoA-detection`, `fix/methanogenesis-mcrA-threshold-clarification`)
3. Keep PRs focused — one logical change per PR
4. Include validation evidence: V12 sweep before/after, sentinel-result diff, smoke-test output
5. Update relevant documentation (`docs/LIMITATIONS.md`, `data/diagnostic_markers/REFERENCE_CURATION.md`, `docs/PROGRESS.md`) as part of the PR

## Code of conduct

This project follows the principles of respectful, professional academic collaboration:

- Be kind. Disagreements about design or methodology are normal; personal attacks are not.
- Be specific. "This doesn't work" is less useful than "On Methanocaldococcus (gid=8) the recipe outputs 30°C instead of the expected 85°C TEMPURA optimum."
- Give credit. When discussing prior work — methods, datasets, references — cite the source.
- Ask questions. Open-source academic projects benefit from explicit explanations; "why was this threshold chosen?" is always a fair question.

## Questions

Open a GitHub issue with the `question` label, or contact the project maintainer at george.schaible@gmail.com.
