# Marker reference audit findings (Phase 5.0 Task 2.2)

**Date:** 2026-05-04
**Audited:** Sampling pass — 1 sample per marker file (every 10th UniProt accession header), 31 marker FASTAs total = 31 sampled accessions.
**Method:** Each sampled UniProt accession verified against UniProt REST API (`curl https://rest.uniprot.org/uniprotkb/<acc>.json`). Returned `organism.scientificName` and `proteinDescription` compared against the FASTA header's claimed organism + description.

## Audit results — Step 1: Are the accessions correct?

- Total accessions sampled: 31 (one per marker FASTA)
- Successful verifications (organism + protein description match): **31 / 31 = 100%**
- Failed lookups: 0
- Suspicious entries (UniProt returned different protein than header claims): 0

**Conclusion:** All 31 sampled marker reference accessions are real UniProt entries that return the expected protein from the expected organism. No fabricated or wrong-organism marker references found in this sampling pass.

Verification audit trail saved to `data/release/audits/marker_audit_results.tsv`.

Per the prompt's escalation policy:
- Failure rate < 5% → marker references treated as trustworthy; no further investigation needed.
- This audit's pass rate is 100%; sampling is sufficient evidence of trustworthiness.

## Audit results — Step 2: Test-set exclusion compliance

The marker reference accessions are correct. But **five marker FASTAs draw from sentinel organisms (gids 900-903)**, violating the test-set-exclusion rule documented in `VERIFICATION_DISCIPLINE.md` Rule 5 and `data/diagnostic_markers/REFERENCE_CURATION.md`.

| Marker | UniProt accession | Organism in reference | Sentinel gid | Validation impact |
|---|---|---|---:|---|
| mcrA | Q8THH1 (`MCRA_METAC`) | *Methanosarcina acetivorans* C2A | 903 | Phase 3.6 ANME-negative + Phase 3.8 methanogenesis-override positive validation reported "mcrA at 100% pident self-hit" — this is **literally** a self-hit (Methanosarcina protein in reference set + Methanosarcina proteome → 100% by construction). The sentinel didn't validate generalization; it confirmed self-recognition. |
| mmoX | P22869 (`MEMA_METCA`) | *Methylococcus capsulatus* Bath | 900 | Phase 3.5 sentinel validation reported "mmoX at 100% pident on Methylococcus capsulatus Bath" — same self-hit pattern. The mmoX sentinel was effectively validating that BLAST finds the reference protein in the proteome it was extracted from. |
| nrfA | Q9S1E5 (`NRFA_WOLSU`) | *Wolinella succinogenes* DSM 1740 | 901 | Phase 3.7 sentinel reported "nrfA at 100% pident on Wolinella" — same self-hit. The Phase 3.4 DNRA validation used Wolinella's own NrfA as the canonical reference, and then the Phase 3.7 sentinel "validated" detection on Wolinella itself. |
| nxrA | Q3SQW5 (`Q3SQW5_NITWN`) | *Nitrobacter winogradskyi* Nb-255 | 902 | Phase 3.7 NOB Type B clade sentinel reported "nxrA at 100% pident on Nitrobacter" — same self-hit. The "Type B clade arm validation" for nxrA was self-recognition, not generalization to other Type B NOBs. |
| pmoA | Q607G3 (`PMOA_METCA`) | *Methylococcus capsulatus* Bath | 900 | Same as mmoX — pmoA reference contains Methylococcus capsulatus' own protein; Phase 3.5 sentinel was self-hit. |

**No marker reference draws from a non-sentinel test-set organism (gids 7-32).** The violations are all confined to sentinels.

## Conclusion: marker accessions verify, but sentinel-marker decoupling failed

The marker references are **biologically correct** (the proteins are real, named correctly, from the named organisms) but **methodologically compromised** for the sentinel use cases. The Phase 3.5 / 3.7 / 3.8 sentinel results that reported "100% pident hit on the sentinel" were measuring self-recognition by construction, not validation that detection generalizes to the named-strain.

This re-frames the sentinel results:

| Phase | Original interpretation | Corrected interpretation |
|---|---|---|
| Phase 3.5 (Methylococcus / methanotrophy) | Sentinel validates pmoA + mmoX detection on a methanotroph | Sentinel confirms that BLAST finds the reference protein in the proteome it was extracted from. Validates the BLAST infrastructure, not generalization of detection logic. |
| Phase 3.7 (Wolinella / DNRA) | Sentinel validates nrfA detection on a DNRA organism | Same — confirms self-recognition |
| Phase 3.7 (Nitrobacter / NOB Type B) | Sentinel validates nxrA Type B detection | Same — confirms self-recognition |
| Phase 3.7 (Methanosarcina / ANME-negative) | Sentinel validates ANME-negative-control on a forward methanogen | Mixed — the mcrA self-hit is self-recognition, but the **negative result** (ANME OR-group correctly resolves to all-negative because dsrAB / mtrC_omcB / nitrate-pwy are absent) IS legitimate generalization. The Phase 3.6 false-positive prevention test holds. |
| Phase 3.8 (Methanosarcina methanogenesis-override) | Sentinel validates mcrA-only override path | Same self-hit issue — but the override-confidence threshold of 0.65 firing on 100% pident self-hit doesn't meaningfully test the override at lower-pident fringes. |

The Phase 3.6 ANME-negative-control validation result is the only one that escapes this issue completely (the negative-result aspect is genuine).

## Required actions

This finding affects future marker-reference curation discipline more than it affects existing CultureForge code:

1. **Update `data/diagnostic_markers/REFERENCE_CURATION.md`** — codify that future marker reference additions must check the test-set + sentinel exclusion list before adding a candidate accession. The current list is documented but was not enforced for the 5 violations above.

2. **Phase 3.5 / 3.7 / 3.8 sentinel "100% pident self-hit" results need re-interpretation in any future manuscript content.** The negative-control aspect of the Methanosarcina sentinel (ANME-negative) survives; the positive-recognition claims need different framing.

3. **Phase 5.0 main work consideration.** When new marker references are curated based on Phase 5.0 gap-discovery findings (Phase 5.1+), the sentinel-marker decoupling must be enforced from day one. Either:
   - Use a non-test-set organism's protein as the reference (always)
   - OR use a different organism for the sentinel than the one whose protein is in the reference set

4. **For now, no immediate code changes.** The marker references continue to work correctly for actual cultivation prediction on novel genomes (since novel genomes are not in any reference set). The integrity issue only surfaces in self-recognition sentinel tests.

## Comprehensive audit not needed

Per the escalation criterion in the Phase 5.0 prompt, sampling pass rate >5% failure rate triggers expanded sampling. With 0% accession-validity failures, the marker references are trustworthy and comprehensive sampling isn't required. The test-set-exclusion violation is a separate concern (about reference-set composition discipline, not accession correctness) and is documented above.
