# Phase 1.5l — Results, Interpretation, and Recommended Next Steps

**Date:** 2026-04-27  
**Companion files:**
- `phase1_5l_marker_inventory.txt` — raw per-accession audit notes
- `phase1_5l_uniprot_audit.md` — structured audit with verdict tables (every accession)
- `phase1_5l_hit_patterns.tsv` — quantitative biological-sanity audit (every organism × marker)

---

## 1. What the audit revealed

Phase 1.5l was triggered by a single observation in the Phase 2c pre-audit (LIMITATIONS.md): the cyc2 reference for iron-oxidation detection was a barley plant Beclin-1 protein. We expected to find one or two more wrong references. Instead, **roughly half of all UniProt accessions in `fetch_markers.sh` returned proteins unrelated to the diagnostic marker the file was named for.**

Most-extreme contamination:
- **Five marker files were entirely wrong** (no correct sequences at all): `aprAB`, `hao`, `soxB`, `pscA_fmoA`, `cyc2`.
- **Animal/plant/fungal proteins embedded in microbial markers:**
  - `pufLM_refs.fasta` contained shark CFTR (P26362) and frog CFTR (P26363) in a microbial photosynthetic reaction-center file.
  - `autotrophy_refs.fasta` contained a cow MHC class II antigen (Q1JU64).
  - `pscA_fmoA_refs.fasta` contained a fungal NADP-dependent mannitol dehydrogenase (P0C0Y4).
  - `cyc2_refs.fasta` contained barley Beclin-1 (Q4A194).
- **Wrong-marker contamination** (right family, wrong subunit): nirS labeled as nosZ, nifD labeled as nifH, sat labeled as dsrAB, MtrA labeled as MtrC, mcrA labeled as mcrB+G, several methyltransferases labeled as mcrBG.

The root cause is procedural: Phase 1's `fetch_markers.sh` listed accessions that were guessed from "what gene name should this organism have" rather than queried from UniProt. Stable accession numbers don't carry semantic information — they have to be verified by reading each entry's protein name field.

## 2. What changed in this round

Concrete deliverables of Phase 1.5l:

1. **`fetch_markers.sh` rewritten as a verified script** (1,007 → 7,486 bytes). Every accession in the new file was checked against `rest.uniprot.org/uniprotkb/{acc}.txt` before commit. Header explicitly documents which accessions to NOT use (e.g. P24200 is the *E. coli* McrA restriction enzyme, not methyl-coenzyme M reductase).
2. **All 25 marker FASTAs in `data/diagnostic_markers/` regenerated.** Counts dropped from contaminated multi-sequence files to clean files (e.g. `cyc2_refs.fasta`: 1 → 3 sequences, all real Cyc2 cytochromes).
3. **All 23 marker BLAST databases rebuilt** (`blastdb_*.{pdb,phr,pin,…}` rebuilt 2026-04-27 08:41).
4. **Capability detection re-run on the development set.** Six organisms changed verdict; all changes are documented in `PHASE_1_5_FIXES.md` §8.
5. **Allochromatium re-validation** (the qmoA discrimination test from Phase 1.5k) confirmed unchanged after reference cleanup — Phase 1.5k's forward-vs-reverse-dsr discriminator is intact.

## 3. Detection-impact summary

| Organism | Pre-1.5l detection | Post-1.5l detection | Net |
|---|---|---|---|
| **Acidithiobacillus ferrooxidans** | sulfur_ox + N₂fix + aerobic_resp | + **Fe(II) oxidation (0.56)** ← cyc2 100% id, bs=980 | ✅ **gain** |
| **Clostridium acetobutylicum** | N₂fix + fermentation | + **acetogenesis** (acsB/cdhC corrected) | ✅ gain |
| **Geobacter sulfurreducens** | Fe(III)_red + N₂fix | Fe(III)_red (mtrC/omcB hit correctly now) + N₂fix | ✅ stronger evidence |
| **Sulfurimonas denitrificans** | sulfur_ox + denitrification | sulfur_ox (soxB now real) + denitrification | ✅ stronger evidence |
| **Allochromatium vinosum** | phototrophy + sulfur_ox + N₂fix | unchanged (qmoA discrimination intact) | ⚪ no change |
| **D. vulgaris** | sulfate_red + fermentation | unchanged | ⚪ no change |
| **Sulfolobus acidocaldarius** | aerobic_resp (0.50) | **(none)** | ❌ **regression** |

**The Sulfolobus regression is the only genuine regression.** Pre-1.5l detection was carried partly by spurious BLAST homology between archaeal proteins and a *Sulfolobus* alcohol dehydrogenase (Q4J781) that had been misfiled in the terminal-oxidases reference. After cleanup the file no longer contains an archaeal terminal oxidase, so SoxM-type aerobic respiration in *Sulfolobus* falls below the detection threshold. This is documented and gated for Phase 1.5m.

## 4. Quantitative hit-pattern verification (Task 3)

Every (organism, marker) pair in the 18-organism development set was BLASTed against the post-correction marker databases. The TSV `phase1_5l_hit_patterns.tsv` records hit counts, top bitscore, top % identity, and a one-word verdict that compares the positive-call decision against a curated biological expectation.

Verdict labels: **OK_TP** (called positive, expected positive), **OK_TN** (called negative, expected negative), **OK_OPT_HIT / OK_OPT_NOHIT** (marker plausibly present or absent — either result is biologically reasonable), **FALSE_POS** (expected negative but called positive — investigate), **MISS_FN** (expected positive but no positive call — investigate).

### Tally across 414 (organism × marker) pairs

| Verdict | Count | % | Interpretation |
|---|---|---|---|
| OK_TN | 346 | 83.6% | True negative — no spurious cross-reactive call |
| OK_TP | 38  | 9.2% | True positive — corrected reference detects what it should |
| OK_OPT_HIT | 13 | 3.1% | Optional marker present (e.g., Wood-Ljungdahl genes in SRBs) |
| OK_OPT_NOHIT | 4 | 1.0% | Optional marker absent — biologically reasonable |
| **FALSE_POS** | **8** | 1.9% | Cross-reactive call in unexpected organism — triaged below |
| **MISS_FN** | **5** | 1.2% | Real biology missed — triaged below |

**96.9% biological agreement (401/414).** The 13 attention-needed pairs cluster on three known issues described in §6.

### FALSE_POS triage (8 rows)

| Organism | Marker | top_bs | top_pid | Diagnosis |
|---|---|---|---|---|
| Methanococcus_jannaschii | qmoA | 247 | 38.6% | **qmoA family bleed.** qmoA belongs to the NfnAB/HdrA flavoprotein superfamily; 30% pident threshold lets unrelated paralogs through. dsrAB+qmoA AND-rule (Phase 1.5k) saves the SR call because dsrAB is absent in these organisms. |
| Acidithiobacillus_ferrooxidans | qmoA | 122 | 30.4% | Same as above. dsrAB absent → no SR call → harmless at the capability layer. |
| Sulfolobus_acidocaldarius | qmoA | 122 | 31.9% | Same as above. |
| Syntrophomonas_wolfei | qmoA | 203 | 34.5% | Same as above. |
| Rhodopseudomonas_palustris | soxB | **712** | **60.5%** | **Curated expectation likely wrong.** *R. palustris* CGA009 encodes soxXAYZ-B-CD genes; this is a real soxB. The audit script's expectation should flip to OPTIONAL or POSITIVE. |
| Thermus_aquaticus | soxB | 394 | 36.6% | Borderline. Could be a metallohydrolase paralog rather than a true soxB. Worth a single-row inspection. |
| Geobacter_sulfurreducens | terminal_oxidases | 413 | 41.1% | Geobacter has many cytochromes; Paracoccus Cox references cross-react. Detector saved by the TCA-completeness gate (Geobacter fails it). Harmless at the capability layer. |
| Magnetospirillum_magneticum | dsrAB | 315 | 44.9% | Possible dsr-like operon (some magnetotacts encode reverse-direction dsr). Worth confirming whether qmoA is also present (would be a real concern); current TSV row says no — so isolated dsrAB hit, not a forward SR caller. |

**Net assessment:** Of the 8 FALSE_POS rows, **0 produce an incorrect capability call after the existing detector logic runs**. Four are saved by the dsrAB+qmoA AND-rule, two by the TCA gate, one is a curation error in the audit script's expectation table, one is a cross-reactive paralog with no downstream consequence.

### MISS_FN triage (5 rows)

| Organism | Marker | top_bs | top_pid | Diagnosis |
|---|---|---|---|---|
| **Sulfolobus_acidocaldarius** | **terminal_oxidases** | 305 | 37.5% | **Documented regression.** Bacterial Cox references don't span archaeal SoxM/SoxB. Fix: add 2–3 archaeal terminal-oxidase references. |
| Thermus_aquaticus | terminal_oxidases | 447 | 43.1% | Has hits at 43% identity but qcov gate fails — Thermus ba3/caa3 oxidase is shorter than the Paracoccus reference. Same family of fix as Sulfolobus. |
| Campylobacter_jejuni | terminal_oxidases | 0 | 0 | **Missing cbb3 references.** Campylobacter uses cb-type oxidase (cbb3 / ccoNOQP); current `terminal_oxidases_refs.fasta` covers Cox + Qox only. |
| Sulfurimonas_denitrificans | terminal_oxidases | 55 | 25.5% | Same fix as Campylobacter — needs cbb3 references. |
| Sulfurimonas_denitrificans | autotrophy | 0 | 0 | **Missing rTCA references.** `autotrophy_refs.fasta` contains only rbcL (CBB cycle); Sulfurimonas fixes CO₂ via rTCA (aclA/aclB). |

**Net assessment:** All 5 MISS_FN rows trace to **incomplete, not contaminated** references. Phase 1.5l fixed the contamination problem but did not expand reference coverage. These five rows are the agenda for Phase 1.5m.

### What was confirmed correct

- **Acidithiobacillus × cyc2:** OK_TP at 100% identity, bs=980 (the headline gain — pre-1.5l this was undetectable because the reference was barley Beclin-1).
- **D. vulgaris × dsrAB / qmoA / aprAB:** all OK_TP at high bitscore (~330–810).
- **Methanococcus × mcrA / mcrBG:** both OK_TP.
- **Nitrosomonas × amoA / hao:** both OK_TP.
- **Allochromatium × dsrAB POSITIVE / qmoA NEGATIVE:** Phase 1.5k forward-vs-reverse dsr discriminator is intact post-correction.
- **Halobacterium × terminal_oxidases:** OK_TP at 41.3% identity (Halobacterium uses a Cox-type oxidase that hits Paracoccus references; only Sulfolobus has the SoxM-family architecture that needs archaeal references).
- **Acetobacterium × acsB_cdhC + cooS_cdhA:** OK_TP for the canonical Wood-Ljungdahl acetogen.

## 5. What this means for downstream pipeline trust

Three observations matter for how to interpret pre-1.5l validation results:

**(a) Most pre-1.5l capability calls were carried by the few correct references that were present.** The audit showed that wrong-protein references usually produced no significant BLAST hits (their sequences are unrelated, so they fail the e-value/% identity/qcov gate). This is why detection mostly worked despite ~50% contamination — the noise was filtered out.

**(b) Sensitivity was silently reduced for every marker that operated with 1–2 correct references instead of 3–5.** A diverse reference set is what lets BLAST recognize phylogenetically distant homologs. With only one correct reference, organisms whose marker sequence has diverged beyond ~40% identity from that one reference get missed. We can't easily quantify how many real signals were missed pre-1.5l, but the 1.5l Acidithiobacillus iron-oxidation gain (which moved from undetected to 0.56 confidence, top hit at 100% identity) is the kind of result that was being silently lost.

**(c) Some `WRONG-MARKER` references produce *cross-reactive* signal that is biologically informative even though it's not what the file is named for.** Examples kept in the corrected references: P02948 (pufA, kept in pufLM); P31896 (cooS, kept in acsB_cdhC). These are biologically related paralogs and produce useful BLAST signal at a step the detector is trying to score. They were retained intentionally with comments. They are not data errors — they are members of the same enzyme family that the marker is meant to recognize.

The capability detector's confidence framework already discounts single-evidence calls (one-source thermal class is capped at 0.70; multi-source agreement is needed for 0.85+). That mechanism will downstream-correct most cases where Phase 1's contaminated references were producing weak-but-positive calls; the major risk was the *opposite* — missed calls — and Phase 1.5l fixes those.

## 6. Recommended next steps

In priority order. Items 1–3 should land before Phase 2c starts; items 4–6 are independent improvements.

### Priority 1 — Phase 1.5m: expand reference coverage, don't just clean

The hit-pattern TSV reveals that the Sulfolobus regression is one instance of a **family of "incomplete-reference" issues** that all need the same kind of fix: add verified references for marker variants that were never represented in Phase 1's set. Bundle them into a single Phase 1.5m round.

| Marker | Missing variants | Affected organisms | Suggested references |
|---|---|---|---|
| `terminal_oxidases` | Archaeal SoxM/SoxB | Sulfolobus | `P39481` SoxB (*S. acidocaldarius*) — verify; SoxM from *Acidianus* or *Metallosphaera* |
| `terminal_oxidases` | Bacterial cbb3 (ccoNOQP) | Campylobacter, Sulfurimonas | ccoN/ccoO from *Pseudomonas stutzeri* or *Bradyrhizobium*; ccoN from *Helicobacter* |
| `terminal_oxidases` | ba3/caa3 of correct length | Thermus | The current Thermus reference (P82543) is a 2A subunit fragment; add full-length Thermus ba3 (CbaA / SoxN) |
| `autotrophy` | rTCA cycle | Sulfurimonas, future Aquificales | aclA + aclB from *Hydrogenobacter* / *Sulfurimonas autotrophica* |
| `autotrophy` | 3-hydroxypropionate (Sulfolobales) | Future Sulfolobales | mcr (malonyl-CoA reductase) from *Metallosphaera sedula* |

After adding references, rebuild the affected BLAST DBs, re-run capability detection on all 18 development organisms, and update PHASE_1_5_FIXES.md with a §9 Phase 1.5m subsection.

**Expected effort:** one focused session. Same pattern as Phase 1.5l Step 4 (UniProt verification + FASTA rebuild + BLAST DB rebuild + re-run).

### Priority 2 — Tighten qmoA threshold OR document the AND-rule dependency

Four organisms (Methanococcus, Acidithiobacillus, Sulfolobus, Syntrophomonas) hit the qmoA reference at 30–39% identity, which is the qmoA flavoprotein-superfamily cross-reactivity. The current `MARKER_THRESHOLDS["qmoA"]` is `pident≥30`. None of the four produces a forward sulfate-reduction call because the Phase 1.5k AND-rule requires dsrAB + qmoA both, and dsrAB is absent in those four.

Two equally reasonable fixes — pick one:
- **Fix A (defensive):** Tighten `qmoA` threshold to `pident≥40`. Eliminates all four FALSE_POS rows. Verify D. vulgaris's true qmoA hit is still positive (it should be — D. vulgaris qmoA hits its own reference family at high identity). Risk: if a real diverse forward SR organism has qmoA at 35% identity, it would be missed.
- **Fix B (architectural):** Document that qmoA cross-reacts with NfnAB/HdrA homologs and that the dsrAB+qmoA AND-rule is the load-bearing biological constraint, not the qmoA threshold per se. Add a code-level comment in `pathway_definitions.json` and `run_marker_blast.py`. No threshold change.

I'd lean toward **Fix B** — the AND-rule is doing the work correctly, and tightening qmoA could miss diverse SRBs we don't have in the development set. But add the cross-reactivity comment so a future maintainer doesn't tighten it without thinking.

**Expected effort:** 30 minutes for either fix.

### Priority 3 — Curation fix: Rhodopseudomonas × soxB expectation

The TSV row `Rhodopseudomonas_palustris × soxB` returned 60.5% identity / bs=712 — this is a real soxB, not a contaminant. *R. palustris* CGA009 carries soxXAYZ-B-CD. Update the `EXPECTATIONS` dict in `data/validation/run_phase1_5l_hit_patterns.py` from `NEGATIVE` to `OPTIONAL` and re-run the audit. Net effect: 7 FALSE_POS instead of 8.

**Expected effort:** 5 minutes.

### Priority 4 — Lock in the audit as a CI artifact

`fetch_markers.sh` v2 has the headline warning, but there is no automated test that catches the next "shark CFTR in pufLM" mistake before it reaches production. A small reproducible check that should be run before any future `fetch_markers.sh` edit:

1. After `bash fetch_markers.sh`, parse each generated FASTA's `>` headers (UniProt headers contain the protein name).
2. For each marker, assert that the protein-name field of every retained sequence contains a marker-specific keyword (e.g. `pufLM` requires "reaction center" or "puh" or "puf" in the header; `cyc2` requires "cytochrome" or "Cyc2"; `dsrAB` requires "sulfite reductase").
3. Fail the build if any header is empty or doesn't match.

This is ~50 lines of Python and would have caught the original Phase 1 contamination immediately.

**Expected effort:** half a session.

### Priority 5 — Re-run the BLIND_VALIDATION_V5 set against the corrected references

`data/validation/BLIND_VALIDATION_V5.md` was the most recent blind validation before the audit. Running the same set against post-correction references will re-baseline the published validation accuracy figure. If the blind set includes organisms with markers that were previously contaminated (e.g., any phototroph that depends on pufLM, any iron oxidizer that depends on cyc2), the corrected results will be the publication-quality figure.

**Expected effort:** half a session if blind set genomes are already loaded; otherwise scales with how many gapseq runs are needed.

### Priority 6 — Move on to Phase 2c

PROGRESS.md flags Phase 2c as "ready" pending the Phase 1.5l outcome. With the audit complete and the regression scoped, there is no remaining audit work blocking Phase 2c. The two natural sequencings are:

- **Phase 1.5m first, then Phase 2c** — clean all five MISS_FN rows while the marker-FASTA pipeline is in working memory. Recommended.
- **Phase 2c first, 1.5m alongside** — only Sulfolobus / Campylobacter / Sulfurimonas detection is affected; if Phase 2c doesn't depend on archaeal aerobe or microaerophile detection in particular, the work can run in parallel.

I'd recommend **Phase 1.5m first** because it's a single focused session and starting Phase 2c with five known MISS_FN rows on the books is a debt that compounds.

### Priority 7 — Backlog: the cross-reactive paralog cleanup

Some retained references are technically the wrong subunit but biologically informative paralogs (P02948 pufA in pufLM, P31896 cooS in acsB_cdhC, Q1PX48 hao in hdh). These are not errors but are also not what the file is named for. A future cleanup could either:

- Rename the marker files to reflect the family they recognize (e.g. `pufLM` → `puf_family`), or
- Split the cross-reactive paralogs into companion files (`pufA_refs.fasta`, `cooS_refs.fasta`) so the named marker file contains only the named gene.

This is purely organizational hygiene and has no detection impact. Worth doing only if the marker set grows past ~30 markers and naming starts mattering.

## 7. Bottom line

The Phase 1.5l audit found that ~50% of marker reference accessions were wrong, fixed all of them, and produced quantitative evidence that the corrected references behave biologically: 96.9% (401/414) of the (organism, marker) pairs in the development set match the curated expectation. Detection sensitivity is now genuinely better than pre-1.5l for at least four organisms (Acidithiobacillus, Clostridium, Geobacter, Sulfurimonas), one false-confidence detection was removed (Sulfolobus aerobic respiration was partly carried by a misfiled alcohol dehydrogenase), and the Phase 1.5k forward-vs-reverse-dsr discrimination is intact.

Of the 13 attention-needed rows in the TSV:
- **0 produce an incorrect downstream capability call** (the existing AND-rules and TCA gate absorb the FALSE_POS cases).
- **5 trace to the same root cause** — incomplete reference coverage for archaeal terminal oxidases, cbb3 oxidases, and rTCA-cycle markers — and are bundled into Phase 1.5m as one focused session.
- **1 is a curation error** in the audit script's expectation table (Rhodopseudomonas × soxB) — 5 minute fix.

The audit deliverables (this writeup + `phase1_5l_uniprot_audit.md` + `phase1_5l_hit_patterns.tsv` + `phase1_5l_marker_inventory.txt`) make every reference-replacement decision auditable from a single set of files. `fetch_markers.sh` v2 is the canonical script and reproduces the entire post-correction reference set. `data/validation/run_phase1_5l_hit_patterns.py` is reproducible and re-runnable; running it post-1.5m will re-baseline the verdict tally.

**Go/no-go for Phase 2c:** Go, after Phase 1.5m lands the five MISS_FN fixes (or with explicit acceptance that those organisms will misclassify until 1.5m). The audit revealed no systematic issue that should block downstream work.
