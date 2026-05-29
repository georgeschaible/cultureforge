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

