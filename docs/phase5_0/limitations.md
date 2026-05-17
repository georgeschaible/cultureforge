# CultureForge — Known Limitations

*Prepared for manuscript reviewers. Repo state: HEAD 2b637ae, 2026-05-16.*

Every limitation below is tagged with one of three classes, because the
appropriate response differs:

- **[REAL BUG]** — a defect in code logic; fixable within the framework.
- **[SCOPE GAP]** — the framework is working as designed but the design does
  not cover this biology; documented and deferred, not "broken".
- **[DATA-INFRA]** — a data-curation / linkage / reference-set issue; resolved
  by curation, not by code.

Limitations are stated specifically (organism gid, file, line) wherever
possible. We prefer a short list of well-characterized limitations over an
exhaustive vague one.

---

## 1. Scope — what CultureForge does and does not claim

CultureForge predicts cultivation media and conditions for uncultured
prokaryotes from genome/MAG sequence plus environmental context. It **does
not** claim to: (a) infer metabolisms that are invisible at the single-genome
level (obligate syntrophy, partner-dependent electron transfer); (b) predict
context-dependent expression (a capability present in the genome but only
realized under specific substrate availability); or (c) substitute for
empirical optimization. Validation is by an internal predictions audit (168
organisms: **63% PASS, 82% directional-or-better**) and a secondary
recipe-quality metric (V12). The audit is the headline metric; §6 explains why.

## 2. Organism classes with systematic limitations

- **Cable bacteria — [SCOPE GAP].** 0% PASS in the audit cohort. Long-range
  electron transport along filaments is not inferable from a single genome and
  has no diagnostic-marker proxy in the current framework.
- **ANME archaea (ANME-1 / -2a / -3) — [SCOPE GAP].** 3 FAILs (gids 1005, 1006,
  1007). ANME run methanogenesis in reverse coupled to a *partner's* sulfate/
  nitrate reduction. The genome encodes `mcrA` like a methanogen; the reverse
  direction and the syntrophic acceptor are not single-genome observable.
  Deferred as audit P2; explicitly a fundamental, not incidental, limit.
- **Heliobacterial phototrophs — [SCOPE GAP → actionable].** 1 FAIL (gid 1051
  *Heliomicrobium modesticaldum*); currently misclassified
  `anaerobic_respiratory (organohalide respiration)` (verified at HEAD).
  Heliobacteria use a homodimeric Type I reaction center (BChl *g*, *pshA*) not
  covered by the purple (`pufLM`) / green-sulfur (`pscA`) / oxygenic (`psaA`)
  reference sets. Already self-documented in
  `data/pathway_definitions.json` as limitation **B.5**. Inspection (B1 report)
  confirms it is a clean reference-coverage gap with verified candidate `pshA`
  references; resolvable by an A1-shape marker addition (a future curation+code
  task).
- **Neutrophilic microaerophilic Fe(II) oxidizers — [REAL BUG].** gids 1068
  (*Gallionella*), 1072 (*Mariprofundus*) are obligate Fe(II)-oxidizing
  chemolithoautotrophs classified `aerobic_chemotrophic`; gid 1072 is composed
  an *organic glucose-oxidation* recipe (verified at HEAD). The `mtoA`
  neutrophilic-Fe-oxidation pathway is uncovered
  (`data/pathway_definitions.json:327`, limitation A.4). This is distinct from,
  and not fixed by, the microaerophile O2 issue (§4).
- **Comammox / archaeal ammonia oxidizers — [DATA-INFRA, resolved].** Previously
  FAILed (gids 1049/1102/1106). Fixed in A1 via a split `amoA_archaeal` marker;
  now detected. Carries a residual reference-circularity caveat (§3).

## 3. Detection-layer limitations

- **Reference-set circularity — [DATA-INFRA].** A1 added each target's own
  UniProt AmoA to the `amoA_archaeal` reference set, so gids 1102/1106 hit at
  ~100% and gid 1114 at high identity partly because their own sequence is the
  reference. Mitigated by including genus-outgroup references at lower identity
  thresholds, but **apparent performance on self-referenced organisms
  overstates generalization**. The same risk recurs for any future `pshA`
  marker (B1: target gid 1051's own genome is accession B0TBM3 — must rely on
  non-circular Heliobacteriaceae outgroups). Reviewers should read
  self-referenced hits as upper bounds.
- **Single-genome framework scope — [SCOPE GAP].** Worst audit cohorts —
  cable_bacteria 0%, syntrophy 29%, iron_metals 33%, carbon_fixation 33%,
  extreme_archaea 38% — cluster on metabolisms that are syntrophic,
  context-dependent, or rely on enzyme families with poor BLAST-identity
  separation. This is the design boundary, not a tuning failure.
- **BLAST-identity thresholds vs. divergent homologs — [SCOPE GAP].** Marker
  detection is BLAST-identity-gated; deep-branching lineages can fall below
  threshold even when the function is present. (Conversely, anammox markers
  were shown to detect cross-clade down to ~60% identity — A4 — so the gap is
  family-specific, not uniform.) HMM-based marker scans are a deferred
  methodological improvement targeting exactly this (audit L1493).

## 4. Composition-layer limitations

- **Microaerophile O2 not modeled — [REAL BUG].** ~10 organisms (gids 15, 16,
  1014, 1020, 1040, 1068, 1072, 1083, 1098, 1108) are microaerophiles for which
  the composer emits 21% O2 (100% air) and vigorous shaking — inhibitory or
  lethal. The discriminating signal *already exists and is parsed* (high-affinity
  `cbb3` vs low-affinity `bo3` oxidase booleans in
  `capability_detectors.py:detect_aerobic_respiration`, ~L1110-1131) but is
  discarded; no O2-modifier exists anywhere in `compose_recipe.py`. Audit P5.
  Inspection (A3 report) recommends a modifier flag on existing aerobic modes
  (not a new mode); note P5 conflates this with the §2 Fe-oxidizer
  misclassification for gids 1068/1072.
- **Species-name proxy reasoning (retired, recorded) — [REAL BUG, fixed].** A4
  removed a guard that escalated *any* organism whose name contained
  "scalindua" with a hardcoded "lacks hzsA/hdh" rationale contradicted by the
  marker evidence. Replaced with an evidence-based predicate. **Recorded here
  because a second, benign instance remains by design**:
  `compose_recipe.py:712-716` keys a marine-NaCl recipe enhancement on the
  species name "scalindua". It is correctness-safe but is the same proxy
  pattern; flagged for principled review (not yet retired).
- **MAG-completeness assumptions — [SCOPE GAP].** The composer assumes detected
  capabilities reflect true biology. For genuinely incomplete MAGs this can be
  wrong; A4 preserved an honest incomplete-MAG escalation (anammox asserted but
  both `hzsA` and `hdh` absent) but this is a heuristic, not a completeness
  guarantee.

## 5. Upstream-tool limitations

- **GenomeSPOT temperature bias — [SCOPE GAP].** Predicted growth temperatures
  skew low versus true optima (e.g. gid 15 *Campylobacter jejuni* predicted
  24.5°C vs ~42°C avian-host optimum, verified at HEAD). Recipes inherit this
  bias unless a user override is supplied.
- **gapseq archaeal-enzyme recognition gaps — [SCOPE GAP].** Pathway
  recognition is weaker for archaeal enzyme variants, contributing to the low
  extreme_archaea cohort score. Mitigations (eggNOG-mapper, DRAM, AlphaFold
  annotation rescue) are next-paper backlog, not in scope.

## 6. Audit and validation methodology limitations

- **Audit-as-primary vs. V12-secondary — [DATA-INFRA].** V12 (recipe vs.
  curated BacDive/DSMZ media) is depressed by stale organism→media linkage
  infrastructure after the 2026-05-05 genome audit corrections, not by worse
  recipes. The C1 inspection confirms this concretely: for gids 9
  (*Thermus aquaticus*) and 17 (*Sulfurimonas denitrificans*) the BacDive-direct
  linkages **already exist and are correct** (BacDive 16714/6113 verified), yet
  V12 is ~33% / ~10% — i.e. the residual gap is recipe-content, not linkage; and
  for uncultured organisms (gid 30 *Scalindua*) the BacDive-direct mechanism
  **cannot apply at all** (no axenic strain, no DSM medium). The predictions
  audit is therefore the more faithful headline metric.
- **"Tuned on the test set we built the framework on" risk — [SCOPE GAP].**
  Markers, thresholds, and pathway definitions were developed against the same
  organism panel the audit scores. Combined with §3 circularity, audit numbers
  should be read as in-distribution performance; out-of-distribution
  generalization is unmeasured.
- **Audit-staleness as a class problem — [DATA-INFRA].** The predictions audit
  has now been shown stale **three independent times**: (1) P3 described an
  anammox composer gap already implemented in Phase 5.1 (corrected by A4);
  (2) P4 supplied hallucinated UniProt accessions (corrected by A1); (3) this
  inspection run's task framing referenced a "handoff document" with
  Tier-A/B/C/D codes that **does not exist** (the canonical doc uses P1–P5/
  S1–S12), asserted a `media` schema that is wrong (the real linkage table is
  `organism_to_published_media`), and used a gid namespace that silently
  collides with a legacy `organisms` table. Staleness is recurrent and
  structural; a dedicated audit-refresh reconciliation is queued (see §7).

## 7. Future work deferred from Phase 5/6

Stated as deferred, not promised. (Use "deferred", never "we will fix in vX".)

- **P1 — Wood-Ljungdahl primary-mode re-ranking.** Acetogenesis over-detected;
  rolled back (commit d4e9587), deferred to Phase 6.
- **P2 — ANME reverse-methanogenesis.** Deferred; fundamental syntrophy limit.
- **P5 / A3 — microaerophile O2 modifier.** Inspected (A3 report); recommended
  as a modifier-flag architecture; not yet implemented. Note it is two
  separable problems (O2 modifier vs. Fe-oxidizer misclassification).
- **S2 / B1 / B.5 — heliobacterial `pshA` marker.** Inspected (B1 report);
  reference design settled (non-circular Heliobacteriaceae outgroups +
  cyanobacterial sentinels gids 1017/1018/1025/1028/1092); implementation is a
  separate marker-writing task.
- **C1 — media-linkage refresh.** Inspected (C1 report): 2/4 already done, 1
  quick win (gid 26 *Picrophilus*, using catalog media J233/J1267 — the task's
  "DSMZ 1146" is wrong), 1 blocked (gid 30 *Scalindua*, needs a curated
  literature medium + a linkage-convention decision).
- **Phase 6.5 — audit-refresh.** Systematic reconciliation of
  `predictions_audit.md` against HEAD; rationale in §6.
- **Next-paper material (not Phase 6):** eggNOG-mapper, dbCAN/CAZy, DRAM,
  AlphaFold annotation rescue, interpretability layer, HMM-based marker scans.

### Documented limitations needing reconciliation (audit vs. HEAD)

Written to the **current HEAD state**, flagging where source docs disagree:

| Source doc claims | HEAD reality | Class |
|-------------------|--------------|-------|
| Audit P3: anammox composer missing | implemented Phase 5.1; A4 fixed the real (guard) blocker | stale audit |
| Audit P4: accessions Q5JIJ3/Q57F89 | hallucinated; A1 substituted verified accessions | stale audit |
| Task handoff: Tier A/B/C/D, `media` schema, gids = those organisms | no such handoff; linkage table is `organism_to_published_media`; gids are genome-space (legacy `organisms` collides) | stale framing |
| Audit C1: "DSMZ 1146 Picrophilus medium" | DSMZ 1146 = *Venenivibrio* medium; correct media are JCM J233/J1267 | stale data ref |
| Audit P5: one microaerophile task | two problems (O2 modifier + Fe-oxidizer misclassification, gids 1068/1072) | mis-scoped |

---

*Positioning note for reviewers:* relative to peers — Máša et al. 2025
(trait-based, needs curated labels), BacterAI (refines organisms already in
culture), KOMODO (16S-phylogeny-based) — CultureForge's differentiator is
genome-based prediction for organisms with no cultivation history. The
limitations above are concentrated where that differentiator is hardest
(syntrophy, context-dependent metabolism, divergent enzyme families), which is
the honest and expected failure surface for a genome-only approach.
