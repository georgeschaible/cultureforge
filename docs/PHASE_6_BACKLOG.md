# Phase 6+ Backlog

Items deferred from Phase 5.0 — not to be added until after Phase 5.0 evaluation
is complete and the manuscript is in submission.

## Tool integrations to consider

### High priority

- **eggNOG-mapper integration**: Fills gaps where gapseq's pathway approach is incomplete.
  Particularly relevant for rare metabolisms (anammox, cable bacteria, ANME, syntrophy).
  Adds COG/KOG categories + KEGG KO annotations for orthologous group context.
  Conda env present on Pod (`/home/gschaible/.conda/envs/`-style structure) but never wired in.

- **dbCAN / CAZy integration**: Activates `evidence_type='cazyme'` placeholder already in schema.
  Adds carbon substrate class specificity (cellulose vs hemicellulose vs chitin vs xylan vs etc.)
  beyond gapseq's general carbon source detection. dbCAN server was down during earlier
  exploration; needs to be revisited.

### Medium priority

- **Interpretability layer**: Borrowed principle from Máša et al. 2025. Surface the reasoning
  behind each recipe decision (capability detections → biomass template → substrate choices →
  confidence indicators). Probably a Phase 5.1 enhancement (1-2 days work), not Phase 6.
  Doesn't require new tools, just better output formatting.

### Lower priority

- **DRAM** (Distilled and Refined Annotation of Metabolism): Cleaner "ecological role"
  summaries than gapseq. Overlaps significantly with gapseq, so integration cost may
  not justify benefit. Worth knowing about, not necessarily integrating.

- **AlphaFold-based annotation rescue**: For specific capabilities where sequence-based
  detection fails. Only worth exploring if specific gaps surface during Phase 5.0 evaluation
  that can't be fixed by eggNOG/dbCAN.

- **Pyrodigal in gapseq pipeline**: Currently using prodigal subprocess + .faa input.
  Pyrodigal would be faster and let gapseq do auto-translation. Not blocking.

## Methodological additions to consider

- **HMM-based marker scans for hard-to-detect proteins**: Some autotrophy markers
  (rTCA aclA/aclB, CBB rbcL/cbbL) are not in current marker BLAST set. Hmmer profiles
  might catch them where sequence similarity fails. Phase 6 if Wave 1/2 evaluations
  reveal systematic gaps.

- **Active learning / Bayesian optimization for recipe refinement**: For Phase 7+
  when experimental cultivation validation data exists. Frame as: BacterAI-style loop
  applied to CultureForge predictions.

## inspect display-layer rendering of genomes.notes

The cultureforge.py inspect tool's display layer strips underscores
from genomes.notes when rendering (e.g., 'g__Picrophilus' renders
as 'g  Picrophilus'; file paths with underscores like
'.pre_audit_correction_20260504' become '.pre audit correction
20260504'; new bracket markers added by the 2026-05-21 curation
pass display with the same mangling).

The underlying DB content is correct (verified via direct SQL
read-back during the curation pass — see commit d610eaa).
This is a display-only rendering issue.

**Action**: audit whether any downstream consumer parses the
rendered output rather than reading the DB directly. If yes,
fix the display layer to preserve underscores. If no (all
consumers read the DB), document the rendering quirk and move on.

**Priority**: low — display issue, not data integrity.
**Surfaced**: 2026-05-21 curation pass (Phase 6.5 follow-up).

## R₃ thermoacidophilic-aerobic-heterotroph mode — rethink before re-attempt

The §5 R₃ design in `docs/phase6/c2_extreme_archaea_inspection.md`
attempted to lift gid 26 *Picrophilus* (FAIL → PASS) via a composition-
layer mode keyed on archaeal sulfur-oxidation markers (tetH /
tqoDoxA / tqoDoxD) plus an `autotrophy`-marker override gated by
Domain=Archaea + predicted pH < 4.5.

Implementation attempt 2026-05-28: pathway entry inserted into
`data/pathway_definitions.json` and reverted (no commit) after the
cohort scan revealed:

- *Picrophilus* (gid 26) carries individual markers but does not
  complete the gapseq R₃ pathway — its pathway-integrity score is
  sub-threshold, and it reaches PASS only via the `autotrophy`
  override at 33.0% pident (the weakest in the R₂+R₃ family).
- Genuine archaeal sulfur-oxidizing chemolithoautotrophs complete
  the pathway directly. *Metallosphaera sedula* (gid 1111) scores
  R₃ at conf 0.872 via pathway integrity alone and bypasses the
  override path entirely.
- The proposed override-level condition gate (Domain + pH) does not
  protect *Metallosphaera*-class organisms (the gate only filters
  override-dependent detections); it does block four cohort bacteria
  with tetH POSITIVE at low pH (*Acidithiobacillus ferrooxidans*
  gids 11 + 1055, *A. thiooxidans* gid 1128, *Leptospirillum
  ferrooxidans* gid 1089).
- The Picrophilus-tuned composer (pH 0.7, glucose, yeast extract)
  is biologically wrong for the Sulfolobales chemolithoautotrophs
  that R₃ would also catch.
- No marker-level discriminator cleanly separates *Picrophilus* from
  *Metallosphaera*-class organisms.
- Tightening via `autotrophy`-strength threshold would overfit and
  undermine the blind-test goal.

**Action**: redesign R₃ at the inspection level before any
implementation attempt. Possible directions: (a) make R₃ a shared
mode with `lithotrophic_aerobic` that forks on carbon-source markers;
(b) accept *Picrophilus* as a single-organism documented gap. The
blind-test cohort design should inform the choice.

**Priority**: medium — gid 26 remains FAIL; affects manuscript headline
for the extreme_archaea cohort.
**Surfaced**: 2026-05-28 C2 R₃ implementation attempt (reverted, no
commit).
**Reference**: `docs/phase6/c2_extreme_archaea_inspection.md` §5 R₃
(including the 2026-05-28 STOP block appended in the same pass).

## R₂ erratum candidate — gid 1111 Metallosphaera misclassified as anaerobic

The `anaerobic_archaeal_sulfur_respiration` mode (R₂, commit `4c0743d`)
classifies gid 1111 *Metallosphaera sedula* ARS120-2 at primary
confidence 0.80 and assigns the thermoacidophilic-anaerobic recipe:
H₂/CO₂ 80:20 atmosphere, elemental sulfur 5 g/L as terminal electron
acceptor, static anaerobic incubation, pH 3.0-4.0 with H₂SO₄.

This is biologically wrong. *Metallosphaera sedula* is an obligate
aerobic chemolithoautotroph (S/Fe oxidizer) of the Sulfolobales. Its
literature medium (DSMZ Medium 88 family, e.g. J267) is aerobic with
reduced sulfur as electron *donor*, not acceptor.

**Root cause**: R₂'s `essential_marker_OR` (tetH / tqoDoxA / tqoDoxD /
"sulfur reduction III" pathway) catches *Metallosphaera* via its very
strong tetH (61.0% / bs 606) + tqoDoxA (100% / bs 338) + tqoDoxD (100%
/ bs 365) hits. R₂'s `negative_markers` include `sor` (specifically to
exclude *Picrophilus* / *Ferroplasma* / *Sulfolobus*-aerobic) and
`qmoA`, but *Metallosphaera* has no `sor` hit and its `qmoA` hit
(bs 120) is below the hardcoded 300 threshold (per
`compose_recipe.py:1908` note). No veto fires.

**Action**: re-examine R₂'s aerobic-vs-anaerobic discriminator and add
an aerobic-archaeal-S-cycler veto. Possible approaches:
- Strong `terminal_oxidases` hit as an R₂ negative_marker
  (*Metallosphaera* has terminal_oxidases 63.6% / bs 612 — strong)
- Pathway-level "aerobic respiration" or "sulfur disproportionation II
  (aerobic)" pathway-completion veto (*Metallosphaera* has
  sulfur disproportionation II at 100% predicted; so does *Ferroplasma*
  but *Ferroplasma* is correctly out via no tetH/tqoDoxA/tqoDoxD)
- Combination of the above

> **CAUTION — regression-check any aerobic discriminator against
> R₂'s actual targets before shipping.** Sulfolobales lineage members
> carry terminal-oxidase and aerobic-respiration genes even when their
> *operational* niche is anaerobic-S-respiration (e.g., facultative
> behavior or unused but encoded aerobic machinery). The same
> non-specificity that sank R₃ (markers present in both target and
> non-target lineages) can sink a R₂ aerobic-veto: a `terminal_oxidases`
> negative_marker could veto a real R₂ win on gids 1129 *Stygiolobus
> azoricus*, 1047 *Caldivirga maquilingensis*, 1019 *Thermococcus
> kodakarensis*, or 1012 *Pyrococcus furiosus*. Required pre-ship
> regression: re-inspect all four R₂ targets with the proposed veto
> active and confirm each still routes to R₂ at PASS confidence. If
> any drops, the veto is too broad and needs scoping (pathway-level
> + marker combination, not single marker).

**Out of scope for this session.** Pre-existing since commit `4c0743d`
(2026-05-26 R₂ landing); not introduced by anything in 2026-05-28's
work. Tracked here so it can be addressed in a dedicated R₂ touch-up
session.

**Priority**: medium — produces a recipe that would not grow
*Metallosphaera*; affects blind-test interpretation if any blind-test
organism shares the marker profile.
**Surfaced**: 2026-05-28 C2 R₃ implementation attempt (during cohort
scan for R₃ regression candidates).
**Reference**: `data/pathway_definitions.json` R₂ entry (line 237 area);
`compose_recipe.py:1945` (R₂ diagnostic marker list);
`compose_recipe.py:1908` (qmoA threshold note).


## A3 microaerophile modifier — rethink before re-attempt

The §4 design in `docs/phase5_0/a3_inspection_report.md` attempted to
lift ~5–6 microaerophile gids (P5: gids 15, 16, 1014, 1020, 1040,
1083, 1098, 1108 — Group A; 1068, 1072 — Group B; see report §1)
from FAIL/PARTIAL → PASS via a post-composition gas-phase modifier
triggered by `cbb3_cc AND NOT bo3_cc`.

Implementation attempt 2026-05-29: no code shipped; verification
against HEAD `eff4db5` revealed (full root cause in
`docs/phase5_0/a3_inspection_report.md` §7 STOP block):

- The discriminator `cbb3_cc AND NOT bo3_cc` fires on **4 of 10**
  named targets and **misses 6 of 10** (1014, 1040, 1068, 1072,
  1083, 1098). Causes: 1083 and 1098 have BOTH bo3 and cbb3
  complete; 1014 and 1040 have NEITHER complex complete (terminal
  oxidase detected only via the `terminal_oxidases` BLAST hit
  list); 1068 and 1072 have bo3 but no cbb3.
- The same discriminator **false-fires on 42 of 164 dev-cohort
  genomes (25.6 %)**, including 8 oxygenic cyanobacteria, 1 strict
  anaerobic SRB (*Desulfotignum phosphitoxidans* gid 1095), ~18
  textbook aerobic heterotrophs/lithotrophs, and 4 validation/
  sentinel/blind-test records.
- GenomeSPOT's `oxygen` field is binary `{tolerant, not_tolerant}`
  in this cohort — never `microaerophile`. The fallback path at
  `derive_recipe_context.py:132` that reads
  `genomespot_oxygen == "microaerophile"` is dead in practice. 9 of
  10 A3 targets are called "tolerant"; *Aquifex* (1014) is wrongly
  called "not tolerant". GenomeSPOT cannot discriminate
  microaerophiles in this cohort in either direction.
- Substantial pre-existing microaerophile detection already exists
  at HEAD in `synthesize_denovo.py:1284-1407` (cbb3/bo3
  discriminator) and `derive_recipe_context.py:109-137,735-754`
  (co-occurrence trigger sets `Atmosphere.MICROAEROBIC` primary and
  `SpecialRequirement("microaerophile")`). The §4 recommendation
  did not surface this. **At HEAD, gids 1098 and 1108 already have
  microaerophile flags set in RecipeContext.** The actual gap is at
  the gas-phase composer: the three `GasPhase(...)` sites in
  `compose_recipe.py` (L847-849, L1124-1125, L1237-1238) hardcode
  the composition string and never read `cond.microaerophile`.
  Existing detection therefore has no effect on the final
  Recipe §10 gas-phase output.

**Action**: redesign A3 at the inspection level before any
implementation attempt. A real microaerophile discriminator needs
(at minimum) an oxidase combination (cbb3 OR a strong-affinity
`terminal_oxidases` hit pattern WITHOUT a complete bo3/aa3) **plus**
a co-signal (lithotrophy/autotrophy pattern, or a denitrification-
style anaerobic-respiratory secondary capacity that genuinely
co-occurs with low-O₂ niches) **plus** a taxonomic guard that
explicitly excludes oxygenic phototrophs (cyanobacteria via
`psaA_psbA` markers) and strict anaerobic phototrophs (Chlorobi via
`pscA_fmoA`), with a way to distinguish biologically-genuine
microaerophiles from textbook facultative denitrifiers. The Group B
case (Fe-oxidizing microaerophiles 1068, 1072) is a separate
discriminator entirely — their microaerophily lives in the
neutrophilic Fe-oxidation pathway (`pathway_definitions.json:361`
already flags this as documented gap A.4: "Neutrophilic/
microaerophilic iron oxidation (mtoA pathway) not covered"); A3
redesign should align with whatever lands for A.4 rather than
overlap it.

The blind-test cohort composition should inform the redesign: if
the blind set is dominated by Aquificales / Campylobacterota
microaerophiles, the discriminator priorities differ from a blind
set dominated by magnetotactic Alphaproteobacteria or Sulfolobales.

### Narrow lift candidate — NOT independently shippable

A scoped alternative considered during the 2026-05-29 attempt:
wire the existing `cond.microaerophile` flag (from
`derive_recipe_context.py:737`, triggered when
`"lithotrophic_aerobic" in modes AND "anaerobic_respiratory" in
modes`) through to the gas-phase composer in `compose_recipe.py`
(touch points: L847-849, L1124-1125, L1237-1238). Detection layer
untouched — uses what's already in place.

**Intended lift**: 2 organisms — gid 1098 *Magnetospirillum
gryphiswaldense* MSR-1 and gid 1108 *Magnetospira* sp. QH-2. Both
are obligately microaerophilic magnetotactic Alphaproteobacteria;
both already get `Atmosphere.MICROAEROBIC` primary and a
`microaerophile` SpecialRequirement at HEAD, so the lift would
deliver the already-detected reality for these two organisms.

**Blocker — co-occurrence-trigger cohort scan (2026-05-29)**: the
underlying trigger fires on **19 of 165 dev-cohort genomes**, not
just the 2 intended. Full list with biology:

- **Genuine microaerophiles** (5 of 19, of which 2 are A3 targets):
  17 *Sulfurovum* NBC37-1 (audit-correction record), 1022
  *Hydrogenobacter thermophilus* TK-6, 1058 *Persephonella marina*
  EX-H1, **1098 *Magnetospirillum gryphiswaldense* MSR-1**, **1108
  *Magnetospira* sp. QH-2**.
- **Lethal false fires — strict anaerobic green-sulfur
  phototrophs** (2): 1010 *Chlorobaculum tepidum* TLS, 1117
  *Chlorobaculum limnaeum* DSM 1677. For obligate anaerobes a 5 %
  O₂ recipe is lethal — Chlorobi do not survive air-level oxygen
  exposure beyond brief transients, and ~5 % O₂ is well above
  tolerance. This fails more actively than the existing air-100 %
  bug: it does not produce a no-growth recipe, it produces a
  kill-the-inoculum recipe.
- **Clear false fires — facultatives wrongly downgraded** (10):
  19 *Rhodopseudomonas palustris* (blind-validation record), 1023
  *Bradyrhizobium diazoefficiens*, 1033 *Anaeromyxobacter
  dehalogenans*, 1036 *Stutzerimonas stutzeri* A1501, 1059
  *Rhodobacter capsulatus* SB 1003, 1073 *Roseobacter litoralis*
  Och 149 (aerobic anoxygenic phototroph), 1077 *Rhodopseudomonas
  palustris* CGA009, 1078 *Cupriavidus metallidurans* CH34, 1093
  *Thioalkalivibrio nitratireducens*, 1096 *Thiobacillus
  thioparus*, 1115 *Thiobacillus denitrificans* RG, 1124
  *Paracoccus denitrificans*.
- **Validation/audit records** (2): 17, 19 (also counted above).

> **CAUTION — the existing co-occurrence flag is currently
> cosmetic; Path A would make it consequential.**
> `cond.microaerophile` and the `Atmosphere.MICROAEROBIC` primary
> it sets affect only the `RecipeContext.atmosphere.primary` label
> and the `SpecialRequirement("microaerophile", …)` advisory note
> printed in the inspect SPECIAL REQUIREMENTS section. They do NOT
> touch `recipe.gas_phase.composition` — the gas phase is
> determined per-mode by the composers in `compose_recipe.py`. So
> the 13 false fires above currently surface only as a display/
> advisory mismatch (harmless). The narrow lift would wire
> `cond.microaerophile` into the composer; that wiring would turn
> the 13-organism display mismatch into a 13-organism wrong
> recipe, including the 2 *Chlorobaculum* strains where the
> resulting 5 % O₂ atmosphere would be lethal to the obligate-
> anaerobic inoculum.

**What a viable narrow lift would require** (and why it is not
independently shippable):

1. A negative-marker guard: veto microaerophile-flag application
   when any of `pscA_fmoA` (green-sulfur photosynthesis) or
   `psaA_psbA` (oxygenic photosynthesis) is present at strong
   bitscore. Drops 1010 and 1117. Possibly also veto on `pufLM`
   (purple bacteria) to drop 19, 1059, 1073, 1077 — but this
   requires a separate decision because anoxygenic photoheterotrophs
   and microaerophiles are not strictly mutually exclusive in
   literature.
2. A second guard for textbook facultative denitrifiers: organisms
   with both strong aerobic respiration AND strong denitrification
   that are not biologically microaerophilic. The marker shape is
   harder to define and may require a per-organism allow-list —
   which the R₃ "no overfit discriminators" guardrail explicitly
   disallows.
3. After both guards are in place, re-run the cohort scan and
   confirm only true microaerophiles remain.

This guard-design work is the A3 redesign in the parent entry above
— there is no independent path. Tackle only after the A3 redesign
has produced a defensible discriminator, at which point the narrow
lift likely falls out of the broader redesign anyway.

### Audit-doc P5 recommendation reasoning also stale (surfaced 2026-05-29 during predictions-audit refresh)

`docs/phase5_0/predictions_audit.md` §5 P5 (L1525-1527) reads:
*"P5 — Add a microaerophile primary-mode label (or 1-3% O2 atmosphere
modifier) for organisms with cydAB without low-affinity ctaABCDE … **Biological
rationale**: All of these are well-characterized microaerophiles; recipe-as-
composed uses 21% O2 which is lethal or strongly inhibitory at standard partial
pressures. Detection is genomically tractable (high-affinity cytochrome bd
oxidase as sole terminal oxidase) and the recipe-output already supports a
`Pressure / Gas phase` field — only need a modifier that lowers O2 to ~3-5%
when the microaerophile flag is set."*

This session's A3 verification (commit `05255b6`) demonstrated that the
analogous `cbb3_cc AND NOT bo3_cc` discriminator misses 6 of 10 named
targets and false-fires on 25.6 % of the cohort (including 8 oxygenic
cyanobacteria and one strict anaerobic SRB). The `cydAB` framing in P5's
biological rationale is similarly non-specific and would have the same
shape of failure. P5's *verdicts* (PARTIAL for gids 15, 16, 1014, 1020,
1040, 1068, 1072, 1083, 1098, 1108) are still correct at HEAD — A3 did
not lift them — so this is reasoning-staleness only, not verdict-
staleness. **No edit applied to P5 in the 2026-05-29 audit-refresh
pass** (scope was the four documented errata, not the recommendation
reasoning sections).

**Action**: when the A3 redesign in the parent entry above lands, also
update P5's "Biological rationale" line in the predictions_audit doc to
reflect the redesigned discriminator (or to point to the redesign
inspection report if the lift is documented elsewhere).

**Priority**: low — reasoning-only; verdicts unchanged; will roll up
naturally with the A3 redesign.
**Surfaced**: 2026-05-29 (during predictions-audit refresh session).

**Priority**: medium — 8 to 10 PARTIAL/FAIL gids would lift if a
real discriminator is built; affects manuscript headline for the
microaerophile cohort. Narrow-lift subsection on its own: not
independently shippable.
**Surfaced**: 2026-05-29 A3 implementation attempt (reverted, no
code shipped).
**Reference**: `docs/phase5_0/a3_inspection_report.md` §7
(2026-05-29 STOP block appended in this pass);
`synthesize_denovo.py:1284-1407` (existing parallel cbb3/bo3
discriminator); `derive_recipe_context.py:109-113, 131-137,
735-754` (existing co-occurrence detection wiring);
`compose_recipe.py:847-849, 1124-1125, 1237-1238` (gas-phase
composer touch points where the wiring would land);
`pathway_definitions.json:361` (A.4 Fe-oxidation gap, related to
Group B).


## Display-only inconsistency — *Chlorobaculum* strains print microaerophile advisory despite anaerobic gas phase

At HEAD, gids 1010 *Chlorobaculum tepidum* TLS and 1117
*Chlorobaculum limnaeum* DSM 1677 (both strict anaerobic
green-sulfur phototrophs) print
`SPECIAL REQUIREMENTS: - microaerophile: Microaerophilic conditions
recommended. Use reduced O2 (2-5%) with N2/CO2 balance…` in the
`cultureforge.py inspect` output, while their actual GAS PHASE
section correctly reads `Anaerobic atmosphere required — anoxygenic
photosynthesis.` The recipe is correct; only the advisory tag is
wrong. Same root cause as the A3-rethink entry above: the
co-occurrence trigger at `derive_recipe_context.py:737` fires for
these gids without a phototrophy veto.

**Priority**: low — display-only; not a recipe bug. Will resolve as
a side-effect when the A3 redesign's phototroph guard lands. No
separate fix required.
**Surfaced**: 2026-05-29 (during A3 co-occurrence cohort scan).


## "DSMZ 1146" stale reference outside the audit doc (found-while-reconciling)

`docs/phase5_0/v12_revalidation.md:72` still carries an outdated
*"DSMZ 1146 Picrophilus medium"* line as a target instruction. The
C1 erratum at `docs/phase5_0/predictions_audit.md:1456-1478` (and
the 2026-05-29 cross-reference added to it) reconciles the medium
references for Picrophilus DSM 9789 / DSM 9790 to JCM J233 /
J1267 (catalog) and DSMZ Medium 88 strain-modified (literature) —
both valid; DSMZ 1146 is wrong (it is *Venenivibrio
stagnispumantis* medium).

**Action**: in a separate doc-sweep session, update `v12_revalidation.md:72`
to the corrected references (likely add `[AUDIT CORRECTION
YYYY-MM-DD: ...]` annotation preserving the original, mirroring the
audit-doc methodology-record discipline). Also worth sweeping
`docs/phase5_0/limitations.md` and
`docs/phase5_0/overnight_inspection_summary.md` for the same
residual "DSMZ 1146" references that the 2026-05-29 grep surfaced.

**Out of scope** for the 2026-05-29 predictions-audit refresh session
(that session was scoped to `docs/phase5_0/predictions_audit.md` only).
**Priority**: low — outdated reference, not a recipe bug; corrected
references are already documented in the audit-doc C1 erratum.
**Surfaced**: 2026-05-29 (DSMZ-1146 grep sweep during predictions-
audit refresh).

