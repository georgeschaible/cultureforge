# C2 Inspection — Extreme Archaea Cohort

**Date:** 2026-05-26 · **Repo HEAD:** `df8e8c6` on `main` · **Mode:** read-only (no code, marker DB, data/, or DB file modified) · **Status:** complete

## Plain-language summary (read this first)

The audit's *extreme_archaea* cohort is 8 genomes, current state **3 PASS / 1
PARTIAL / 4 FAIL** (38% PASS — the audit's third-worst category after
cable_bacteria and syntrophy). HEAD-state matches the audit; no audit-staleness.

The four failures and the partial all collapse to **one root cause already
documented as a scope gap**: archaeal sulfur-cycle enzymes and archaeal terminal
oxidases are recognized by gapseq pattern-matching at far lower sensitivity than
their bacterial counterparts, so their pathway-integrity scores never clear the
0.40 detection gate even when 3–4 strong diagnostic markers fire. `limitations.md`
L118-121 explicitly tags this as **"next-paper backlog, not in scope"**:

> **gapseq archaeal-enzyme recognition gaps — [SCOPE GAP].** Pathway recognition is weaker for archaeal enzyme variants, contributing to the low extreme_archaea cohort score. Mitigations (eggNOG-mapper, DRAM, AlphaFold annotation rescue) are next-paper backlog, not in scope.

**This is a STOP-and-report item.** The C2 framing — "lift extreme_archaea from
FAIL/PARTIAL to PASS where the underlying data supports it" — collides with a
scope decision already in the limitations doc. Three implementation paths exist:

1. **Honor the scope decision** and treat C2 as "audit refresh only" (0 lifts available — HEAD already matches the audit).
2. **Composition-layer workaround** (does NOT modify gapseq): add 1-2 marker-corroborated cultivation modes and relax 1 essential-marker gate. Lifts 3-4 of 5 non-PASS gids without violating the gapseq scope decision.
3. **Full archaeal-enzyme rescue** (modifies gapseq integration / adds eggNOG-mapper): explicit "next-paper" scope per the limitations doc.

I recommend a scoped version of path 2, but the decision is yours, and the
limitations-doc collision must be acknowledged in the manuscript regardless.

---

## 1. Pre-flight

- `pwd` = `/home/george/cultureforge` ✓
- `git status` clean (only `data/validation/sourmash_identity_verification/` untracked, expected)
- HEAD = `df8e8c6` on `main` (matches expected)
- DB present (1.5 GB, mtime 2026-05-21)
- /home disk: 894 GB free

## 2. Cohort roster — the canonical 8 (from audit §extreme_archaea)

| gid | Organism | Accession | Audit verdict |
|----:|----------|-----------|---------------|
| 9   | *Thermus aquaticus* YT-1                  | GCF_001280255.1 | **PASS** |
| 14  | *Sulfolobus acidocaldarius*               | NC_007181.1     | **PARTIAL** |
| 26  | *Picrophilus torridus* DSM 9790¹          | GCF_000008265.1 | **FAIL** |
| 27  | *Thermotoga maritima*                     | GCF_000008545.1 | **PASS** |
| 1012 | *Pyrococcus furiosus* DSM 3638           | GCF_000007305.1 | **PASS** ² |
| 1019 | *Thermococcus kodakarensis* KOD1         | GCF_000009965.1 | **FAIL** |
| 1047 | *Caldivirga maquilingensis* IC-167       | GCF_000018305.1 | **FAIL** |
| 1129 | *Stygiolobus azoricus* DSM 6296          | GCF_009729035.1 | **FAIL** |

¹ Loaded FASTA is actually *Picrophilus oshimae* DSM 9789 (sister species); audit-correction note in genomes.notes 2026-05-21, sourmash containment 0.74 to *P. oshimae* — both genus *Picrophilus*, biology identical for cultivation purposes.

² PASS is mechanism-dubious — see §3, gid 1012.

**Data-curation footnote.** Only four of the eight carry the literal
`[extreme_archaea]` notes tag in `genomes.notes`: 1012, 1019, 1047, 1129. The
remaining four (9, 14, 26, 27) are categorized into *extreme_archaea* in the
predictions audit by *physiology* (thermophile / hyperthermophile / thermoacidophile)
without that exact tag. The audit grouping is the canonical one for C2 scope.
Not a blocker; flagged for whoever maintains the genome-notes vocabulary.

## 3. HEAD-state inspect (single source of truth: predictions_audit.md §extreme_archaea + `cultureforge.py inspect <gid>` at HEAD `df8e8c6`)

| gid | T (°C) | pH  | O₂ | HEAD primary mode (conf) | Detected ≥0.50 | Strong positive markers | Audit | HEAD | Diverges? |
|----:|-------:|----:|----|--------------------------|----------------|-------------------------|-------|------|-----------|
|   9 | 67.7   | 7.6 | tol. | aerobic_chemotrophic 0.55 + fermentative 0.50 | Aerobic resp 0.55, Ferm 0.50 | autotrophy, terminal_oxidases | PASS | PASS | no |
|  14 | 74.9   | 4.0 | n.t. | aerobic_chemotrophic 0.50 | Aerobic resp 0.50 | autotrophy (75.5%), terminal_oxidases (82%) | PARTIAL | PARTIAL | no |
|  26 | 45.6   | 2.6 | n.t. | **(none — escalated)** | none | autotrophy, sor (61.7%), tetH (55.2%), tqoDoxD (68.5%); terminal_ox weak (35.6%) | FAIL | FAIL | no |
|  27 | (n/a)  | n/a | n/a | fermentative 0.78 | Ferm 0.78 | (none); hydrogenases [FeFe] A ×3 | PASS | PASS | no |
| 1012 | 90.8 | 7.0 | n.t. | anaerobic_respiratory 0.65 | Organohalide resp 0.65 ² | autotrophy, rdhA (34.7%, bs=99) ² | PASS | PASS | no |
| 1019 | 81.0 | 6.3 | n.t. | **(none — escalated)** | none | autotrophy | FAIL | FAIL | no |
| 1047 | 75.3 | 3.8 | n.t. | **(none — escalated)** | none (sulfate_red 0.40 capped; sulfur_ox 0.34 below gate) | aprAB (53.3%), dsrAB (37.3%), tetH (53.5%), autotrophy | FAIL | FAIL | no |
| 1129 | 80.6 | 4.0 | n.t. | **(none — escalated)** | none (sulfur_ox 0.457 just below 0.50) | autotrophy (77.9%), tetH (57.6%), tqoDoxA (81.1%), tqoDoxD (82.2%) | FAIL | FAIL | no |

² gid 1012 (Pyrococcus furiosus) PASSes only because rdhA fires at 34.7% identity / bs=99, triggering the organohalide-respiration `diagnostic_marker_override` (Phase 1.5n threshold raised to 34% to exclude Prometheoarchaeum). Pyrococcus does NOT perform organohalide respiration biologically — it is a hyperthermophilic peptide fermenter / S⁰ respirer. The mode (anaerobic_respiratory) happens to be the correct *coarse* mode for cultivation, so the audit accepted it. This is a known "right answer for wrong reason" — out of C2 scope to revisit.

**HEAD–audit divergence summary: zero.** The audit verdicts match HEAD-state for all 8 organisms. The "audit-stale" sub-category from task Step 1.5 yields zero lifts.

## 4. Failure-mode diagnosis (FAIL + PARTIAL)

### gid 14 — *Sulfolobus acidocaldarius* (PARTIAL)

- **Biology:** thermoacidophilic chemolithoautotroph on S⁰ and Fe²⁺ (also heterotrophic on yeast extract). DSMZ 639.
- **HEAD detects:** aerobic_chemotrophic 0.50 only — based on a clean Sulfolobus-family terminal oxidase hit (Q97VG9_SACS2 at 82% id, bs=805).
- **Audit expectation:** primary should be `lithotrophic_aerobic` (chemolithoautotrophy on S⁰/Fe²⁺), with aerobic_chemotrophic as secondary.
- **Why it doesn't fire:** sulfur_oxidation pathway score = 0.00. Despite biology, **no archaeal S-oxidation markers hit** for gid 14 (sor/tetH/tqoDoxA/tqoDoxD all negative for *S. acidocaldarius*, surprisingly). Compare gid 1129 *Stygiolobus* and gid 26 *Picrophilus* which both hit 3-4 of those markers cleanly. The *S. acidocaldarius* genome submitted (NC_007181.1) may genuinely lack canonical SOR / TQO subunits at the loaded BLAST identity thresholds; cyc2 also negative.
- **Diagnosis:** **insufficient marker signal in the loaded genome** to corroborate `lithotrophic_aerobic`. PARTIAL appears correct at HEAD.
- **Per-organism quirk** — not a class problem (1129 shows that the markers DO fire for related Sulfolobales).
- **Path to PASS within scope:** marginal — would require dropping marker thresholds or adding archaeal-specific SOR HMM (scope-gap territory).

### gid 26 — *Picrophilus torridus* DSM 9790 (FAIL)

- **Biology:** aerobic thermoacidophilic heterotroph, optimum pH 0–3.5, T 60°C. Uses sulfur compounds for energy (sor, tetH, TQO) but is primarily organotrophic on yeast extract / glucose. DSMZ 9790.
- **HEAD detects:** nothing above 0.50. Best caps rejected: sulfur_oxidation 0.456 (pathway 0.29), fermentation 0.408 (pathway 0.30), aerobic_resp 0.206 (pathway 0.29).
- **Markers firing strongly:** 4-of-4 archaeal sulfur-oxidation markers (autotrophy 33% MCR_METS5, sor 61.7%, tetH 55.2%, tqoDoxD 68.5%) plus a weak terminal_oxidase (35.6% id — divergent archaeal cytochrome that the bacterial reference set classifies as "weak").
- **Why it doesn't fire:** the pathway scoring gives 0.29 for sulfur_oxidation despite 4 markers because the bacterial `dsrAB / soxB / aprAB` weighted steps remain unmet. The archaeal-marker boost was added Phase 3.2 as a *capability* booster (per `pathway_definitions.json:233`) but does not promote the call past the 0.40 pathway_score gate.
- **Diagnosis:** archaeal aerobic heterotroph with sulfur side-metabolism. The composer has NO mode for this niche. Sulfolobus (14) escapes FAIL only because its terminal oxidase happens to BLAST cleanly at 82% id; Picrophilus' divergent oxidase hits at 35.6% and is classed "weak", so aerobic_chemotrophic doesn't fire.
- **Path to PASS within scope:** composition-layer rule — accept `aerobic_chemotrophic` when (autotrophy POSITIVE) + (any archaeal-S marker POSITIVE) + (predicted pH < 4.5) + (T > 50°C) + (terminal_oxidase hit ≥ "weak"). This bypasses the gapseq archaeal-recognition gap without touching gapseq. Add a `thermoacidophilic_aerobic_heterotroph` composer variant for the recipe (yeast extract / glucose, pH 2 buffer, complete aerobic salts).

### gid 1019 — *Thermococcus kodakarensis* KOD1 (FAIL)

- **Biology:** hyperthermophilic peptide fermenter + S⁰ respirer (sulfhydrogenase). Same niche as *Pyrococcus furiosus* (gid 1012). JCM 12380.
- **HEAD detects:** nothing. Fermentation 0.339 (pathway 0.20). Sister gid 1012 (Pyrococcus) PASSes only via rdhA marker override that does NOT fire on Thermococcus.
- **Markers firing:** only autotrophy.
- **Why it doesn't fire:** Thermococcales sulfhydrogenase / S⁰ reductase is archaeal-specific and absent from `dsrAB` / `qmoA` markers; rdhA is biologically absent (correctly). gapseq does predict "sulfur reduction III" at 100% (visible in inspect §5) but that pathway is not wired to any capability (no entry in `pathway_definitions.json` for archaeal anaerobic sulfur reduction).
- **Diagnosis:** missing pathway-definition / capability — `anaerobic_archaeal_S0_respiration` or similar. Composer also missing a hyperthermophilic-peptide-fermenter recipe.
- **Path to PASS within scope:** add a capability `Anaerobic archaeal sulfur respiration` keyed on (gapseq "sulfur reduction III" or "sulfur reduction II") + (autotrophy POSITIVE) + (T_opt > 70°C), routing to a new `anaerobic_archaeal_sulfur_respiration` mode with a Pyrococcus/Thermococcus medium (peptone 5 g/L, yeast extract 1 g/L, NaCl 20 g/L, S⁰ 5 g/L, N₂/CO₂ headspace, near-neutral pH). Side effect: gid 1012 would route via this principled path instead of the questionable rdhA override.

### gid 1047 — *Caldivirga maquilingensis* IC-167 (FAIL)

- **Biology:** thermoacidophilic facultative anaerobic crenarchaeote, dissimilatory S⁰/thiosulfate reduction with peptides or H₂. DSMZ 13496.
- **HEAD detects:** nothing. sulfate_reduction 0.40 (capped because qmoA absent), sulfur_oxidation 0.336 (pathway 0.16).
- **Markers firing strongly:** aprAB (53.3% bs=658, *very* strong), dsrAB (37.3% bs=218, marginal but real), tetH (53.5% bs=405, strong), autotrophy (35.4%, bs=194).
- **Why it doesn't fire:** dsrAB+aprAB are present but qmoA is hard-required (`essential_marker` in `dissimilatory_sulfate_reduction` pathway def). Caldivirga uses the reverse-acting dsrAB for dissimilatory **S⁰ reduction** (not sulfate); qmoA isn't part of that variant. The essential-marker gate, designed to exclude assimilatory dsr-like hits, is over-strict for archaeal S⁰ reducers.
- **Diagnosis:** essential-marker gate (qmoA) over-strict for the archaeal anaerobic S-reducer biology.
- **Path to PASS within scope:** EITHER (a) relax the qmoA essential-marker gate when (dsrAB POSITIVE bs≥150) AND (aprAB POSITIVE bs≥300) AND (T_opt > 60°C) AND (predicted O₂ "not tolerant"), promoting the call to `anaerobic_respiratory` via dissimilatory sulfur reduction — OR (b) introduce the same new capability proposed for gid 1019 (anaerobic_archaeal_S0_respiration) and let Caldivirga route through it on aprAB+dsrAB+autotrophy+tetH. Option (b) is the more principled fix; (a) is a narrow gate-relaxation.

### gid 1129 — *Stygiolobus azoricus* DSM 6296 (FAIL)

- **Biology:** thermoacidophilic anaerobic S⁰ reducer with H₂ as electron donor (Sulfolobales). DSMZ 6296.
- **HEAD detects:** nothing. sulfur_oxidation 0.457 (closest to 0.50 of any FAIL; pathway 0.30). Fermentation rejected because autotrophy fires.
- **Markers firing strongly:** 4-of-4 archaeal markers — autotrophy 77.9% bs=583, tetH 57.6% bs=453, tqoDoxA 81.1% bs=285, tqoDoxD 82.2% bs=316. **Strongest marker pattern of any failing gid.**
- **Why it doesn't fire:** the markers route to `lithotrophic_aerobic` (sulfur oxidation, Sulfolobales-style), but the genome's biology is anaerobic S⁰ reduction (opposite direction), and the gapseq pathway score for `sulfur_oxidation` is only 0.30 because Stygiolobus doesn't oxidize sulfur — same enzyme machinery used in reverse. The capability is misnamed for this organism.
- **Diagnosis:** same as 1047 — needs an anaerobic_archaeal_S0_respiration mode that recognizes the markers + autotrophy + anaerobic context regardless of the oxidative-direction naming.
- **Path to PASS within scope:** same as 1047 option (b) — new capability + composer mode. Composer should use H₂/CO₂ headspace (gid 1129 H₂-utilizing), elemental S⁰ as e-acceptor, thermoacidophilic salts, pH 3-4, T 80°C.

## 5. Fix-category groupings

### Category R₀ — Audit refresh only (0 actions, 0 lifts)
HEAD matches audit; no audit-staleness lifts available. Confirms the predictions audit is reflecting current code.

### Category R₁ — Per-organism marker insufficiency, no scoped fix
- **gid 14** *S. acidocaldarius*: archaeal S-markers genuinely absent at current BLAST thresholds in the loaded genome. PARTIAL appears defensible. Lowering thresholds risks regression across other Sulfolobales / cross-reactivity with bacterial soxB.

### Category R₂ — Single shared root cause: archaeal anaerobic S-respiration not modeled
Affects: **gid 1019, gid 1047, gid 1129** (3 of 5 non-PASS). Possibly also gid 1012 (relieves the rdhA-override dependency).

Proposed fix shape (composition-layer, no gapseq change):
1. Add a new capability `anaerobic_archaeal_sulfur_respiration` in `pathway_definitions.json` with a marker-corroborated override (similar to ANME's `mcrA + acceptor_partner` pattern):
   - Required: `autotrophy` POSITIVE + (`tetH` OR `tqoDoxA` OR `tqoDoxD` OR (`dsrAB` bs≥150 AND `aprAB` bs≥300)) POSITIVE
   - Plus context: predicted T_opt ≥ 60°C AND predicted O₂ tolerance ≠ "tolerant"
   - Plus a gapseq-pathway hint: any of "sulfur reduction II", "sulfur reduction III", "thiosulfate reduction" predicted
2. New `CULTIVATION_MODE_GROUPS` entry `anaerobic_archaeal_sulfur_respiration` (or fold into `anaerobic_respiratory` with a context flag).
3. New composer `_compose_anaerobic_archaeal_sulfur_respiration_recipe` — base choice between hyperthermophilic-near-neutral (Thermococcales: peptone+YE+S⁰+NaCl, N₂/CO₂, pH 7) and thermoacidophilic (Sulfolobales / Caldivirga: mineral base + S⁰ + H₂/CO₂, pH 3-4) based on predicted pH and the markers present.

Estimated effort: 2-3 focused evenings. Lifts: 1019, 1047, 1129 (3 lifts).
Risk: low if marker thresholds are tight; principled regression check on gids 1012 (must continue to PASS — preferably via the new mode rather than rdhA) plus a handful of bacterial SRBs to ensure dsrAB+aprAB+autotrophy doesn't wrongly route Desulfovibrio-class organisms.

### Category R₃ — Thermoacidophilic aerobic archaeal heterotroph not modeled
Affects: **gid 26** (FAIL); related to **gid 14** (PARTIAL).

Proposed fix shape:
1. Composition-layer rule: when (autotrophy POSITIVE) + (any of sor/tetH/tqoDoxD POSITIVE) + (predicted pH < 4.5) + (T_opt > 50°C) + (Domain=Archaea) + (no archaeal-S-respiration markers from R₂), accept aerobic_chemotrophic at confidence 0.55 with a weak-terminal-oxidase relaxation (or 0.50 threshold lowering specifically when archaeal-S markers corroborate).
2. New composer variant `_compose_thermoacidophilic_aerobic_heterotroph_recipe` — yeast extract 2 g/L + glucose 2 g/L + DSMZ-1146-style mineral salts (or DSMZ J233 / J1267 Picrophilus media) + H₂SO₄ buffer to pH 1.5-2.5 + aerobic salts + S⁰ optional (1 g/L), aerobic atmosphere, T 55-65°C.

Estimated effort: 1-2 evenings. Lifts: 26 → PASS. May upgrade 14 PARTIAL→PASS if the mode wires through (depends on whether S. acidocaldarius corroborates a S-marker — currently it does not, so 14 may stay PARTIAL).
Risk: medium. The "Domain=Archaea + autotrophy + low pH" trigger could false-fire on a hypothetical heterotrophic archaeon. Regression check on Halobacterium / Thermoplasma / Sulfolobus-like organisms.

### Category R₄ — Pre-documented scope gap (defer per limitations.md)
The underlying gapseq archaeal-pathway recognition gap is explicitly out-of-scope per `limitations.md` L118-121. R₂ and R₃ are workarounds at the composition layer that do *not* attempt to fix gapseq itself. A full rescue would require eggNOG-mapper / DRAM / AlphaFold-based annotation integration and is "next-paper backlog."

## 6. Recommended ordering (smallest, highest-leverage first)

| Step | Fix | Effort | Lifts | Regression risk | Order rationale |
|------|-----|--------|------:|-----------------|-----------------|
| 0    | (audit refresh — confirmed null result) | 0 | 0   | none   | already done in this inspection |
| 1    | **R₂** anaerobic_archaeal_sulfur_respiration | 2-3 eve | **3** (1019, 1047, 1129) | low | single biggest leverage; principled; tightens the rdhA over-call for 1012 as side effect |
| 2    | **R₃** thermoacidophilic_aerobic_heterotroph | 1-2 eve | **1-2** (26 def; 14 maybe) | medium | smaller leverage, narrower trigger needed, more regression-prone |
| 3    | (R₁ for gid 14 — defer/document) | n/a | 0 | n/a | scope gap |

If R₁+R₂ both land cleanly: cohort goes from 3/8 → 6/8 PASS (75%), and the
known PARTIAL (14) stays PARTIAL pragmatically.

## 7. Expected pass-rate lift if all fixes land

| Cohort | Now | After R₁ | After R₁+R₂ | Manuscript headline |
|--------|----:|---------:|------------:|---------------------|
| extreme_archaea (n=8) | 3/8 (38%) | 6/8 (75%) | 6-7/8 (75-88%) | C2 fixes lift it from 3rd-worst to mid-pack |
| Overall (n=168) | 106 PASS (63%) | +3 → 109 (65%) | +4-5 → 110-111 (65-66%) | small total bump; cohort-specific signal much stronger |

## 8. STOP-and-report items requiring user decision

1. **The C2 task framing collides with `limitations.md:118-121`** — extreme_archaea low pass rate is already documented as a known SCOPE GAP, with mitigation explicitly tagged as "next-paper backlog, not in scope." R₂ and R₃ are composition-layer workarounds that **do not violate the scope decision** (they don't touch gapseq), but the manuscript should be updated either way: either limitations.md L118-121 needs softening to reflect the workaround, OR the scope decision stands and C2 should be re-framed as a smaller targeted fix (or deferred).

2. **gid 1012 *Pyrococcus furiosus* PASSes via biologically incorrect rdhA marker override.** Out of formal C2 scope (it's currently PASS), but R₂ landing would let us route 1012 through the principled new anaerobic_archaeal_sulfur_respiration mode rather than the rdhA quirk. Decision: include 1012 in the R₂ regression target list (preferred) or leave its current PASS path alone?

3. **gid 14 *S. acidocaldarius* PARTIAL — accept as scope-limited, or push?** The genome genuinely lacks archaeal-S-marker hits in our reference set. Lowering thresholds is regression-prone. Accepting PARTIAL is principled and aligns with limitations.md L118.

4. **The four "soft-tag" genomes (9, 14, 26, 27) lack the literal `[extreme_archaea]` notes tag** in `genomes.notes`. Data curation note — should the notes vocabulary be normalized? Not blocking, but worth a one-line `data/validation/` follow-up.

5. **No DB writes proposed in this inspection.** R₁ and R₂ implementations would be code-only edits to `capability_detectors.py`, `compose_recipe.py`, and `data/pathway_definitions.json` (with a marker DB rebuild for any added/modified marker references — but none currently required since the existing archaeal markers suffice).

---

End of C2 inspection. No code, marker DB, data/, or DB file modified. No commit.
