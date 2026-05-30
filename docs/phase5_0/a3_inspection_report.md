# A3 Inspection Report — Microaerophile gas-phase modifier (audit P5)

**Date:** 2026-05-16 · **Repo HEAD:** 2b637ae · **Mode:** read-only (DB SELECT + `inspect` reads + code reads; no writes)
**Status:** COMPLETE — audit holds at HEAD, but **A3 is not a single coherent task** (STOP-and-report, §6).

## Plain-language summary (read this first)

These ~10 organisms are microaerophiles: they need *some* oxygen but die or are
strongly inhibited at normal air levels (21% O2). The system currently builds
recipes for them with **100% air and vigorous shaking** — a recipe that would
kill them. The audit ("P5") asked for a way to detect microaerophiles and lower
the oxygen.

Two findings change the shape of the work:

1. **Good news — the detection signal already exists.** The system already reads,
   per genome, whether the organism has a *high-affinity* oxygen enzyme (cbb3,
   the microaerophile hallmark) versus a *low-affinity* one (bo3, the
   normal-air hallmark). The microaerophile rule ("high-affinity present,
   low-affinity absent") is a few lines on top of data that is **already
   parsed** — no new gene-marker database is required. The plan's worry that the
   relevant markers were entirely absent was over-pessimistic.
2. **Caution — P5 is really two different problems bundled together.** Eight of
   the ten just need oxygen lowered. But two (Gallionella gid 1068, Mariprofundus
   gid 1072) are *also* misclassified at the energy-metabolism level — they are
   iron-eating autotrophs being given a sugar-eating recipe. Lowering O2 will
   not make their recipes correct. That second problem is out of A3's scope and
   needs its own decision.

## 1. Namespace + audit-vs-HEAD reconciliation

All 10 gids exist in the genome space and match the expected microaerophiles
(no namespace mismatch; the plan's correction holds). I verified the audit's
claims against HEAD with the actual tool on a representative sample (gid 15
full; gids 1068/1072/1083 recipe section), rather than trusting the audit text
(the A4-style discipline). **A1 and A4 did not touch oxygen handling, so nothing
flipped — every audit claim below is still true at HEAD.**

| gid | organism (genomes.notes) | HEAD primary mode | HEAD gas phase | audit verdict | matches HEAD? |
|----:|--------------------------|-------------------|----------------|---------------|:-------------:|
| 15 | Campylobacter jejuni | aerobic_chemotrophic (0.90) | **air 100%, 200 rpm** | PARTIAL, microaeroph flag missing | ✓ verified |
| 16 | Magnetospirillum/Paramagnetospirillum magneticum | aerobic_chemotrophic | air 100% (per audit L1330) | PARTIAL, flag missing | ✓ (audit) |
| 1014 | Aquifex aeolicus VF5 | lithotrophic_aerobic | air (per audit L1338) | PARTIAL, mode ✓ flag missing | ✓ (audit) |
| 1020 | Paramagnetospirillum magneticum AMB-1 | aerobic_chemotrophic | air 100% | PARTIAL (dup of 16) | ✓ (audit) |
| 1040 | Magnetococcus marinus MC-1 | lithotrophic_aerobic | air | PARTIAL, mode ok flag missing | ✓ (audit) |
| 1068 | Gallionella capsiferriformans ES-2 | **aerobic_chemotrophic** | **air 100%, 200 rpm** | PARTIAL — *wrong primary* (should be lithotrophic Fe-autotroph) **+** flag missing | ✓ verified — **dual issue** |
| 1072 | Mariprofundus ferrooxydans PV-1 | **aerobic_chemotrophic** (alt lithotrophic) | **air 100%; composes glucose-oxidation recipe** | PARTIAL — *wrong primary* (obligate Fe-lithoautotroph) **+** flag missing | ✓ verified — **dual issue** |
| 1083 | Beggiatoa alba B18LD | lithotrophic_aerobic (S oxidation) | **air 98% / CO2 2%, 150 rpm** | PARTIAL, mode ✓ flag missing | ✓ verified — pure O2 case |
| 1098 | Magnetospirillum gryphiswaldense MSR-1 | lithotrophic_aerobic | air | PARTIAL, label misleading + flag missing | ✓ (audit) |
| 1108 | Magnetospira sp. QH-2 | lithotrophic_aerobic | air | PARTIAL, should be aerobic_chemotrophic microaeroph | ✓ (audit) |

Audit P5 is at `docs/phase5_0/predictions_audit.md:1455`; the per-gid lines are
1329–1338 (section header "Microaerophile flag missing (recipe uses standard
aerobic 21% O2)" at L1327). Direct HEAD evidence captured for gid 15: the
capability section literally prints *"cbb3 oxidase complex complete
(high-affinity, microaerophilic)"* yet the recipe still emits "Atmospheric air
(21% O2 …). Standard aerobic culture" + 200 rpm — the signal is detected and
then ignored.

## 2. Gas-phase code path (where O2 is set)

Gas phase is **per-mode**, not one global default — each composer sets its own
`GasPhase(...)` (`compose_recipe.py` GasPhase calls at lines 384, 497, 520, 542,
562, 648, 760, 847, 883, 1124, 1183, 1237, 1340, …). The ones the P5 organisms
hit:

- **aerobic_chemotrophic** — `compose_recipe.py:847-849`:
  `GasPhase(composition={"air": 1.0}, pressure_atm=1.0, rationale="Atmospheric
  air (21% O2, 0.04% CO2). Standard aerobic culture.")`
- **lithotrophic_aerobic (non-autotroph)** — `:1124-1125`:
  `composition={"air": 1.0, "CO2": 0.0}`
- **lithotrophic_aerobic (autotroph, +CO2)** — `:1237-1238`:
  `composition={"air": 0.98, "CO2": 0.02}` (this is the gid 1083 Beggiatoa path)

There is **no per-organism O2 override and no microaerophile branch anywhere**:
`grep -ni "microaeroph|3%.*o2|5%.*o2|low.affinity|reduced.o2" compose_recipe.py`
→ empty. No clade-aware O2 tuning exists. Every aerobic composer hardcodes its
own atmosphere string.

## 3. Detection-layer status — better than the plan assumed

The plan said "no cydAB/ctaABCDE markers anywhere; no microaerophile pathway."
By those literal names that is true, **but the functional equivalents already
exist and are already parsed**:

- `data/diagnostic_markers/terminal_oxidases_refs.fasta` (+ `blastdb_terminal_
  oxidases.*`) — a terminal-oxidase BLAST reference set already in the repo.
- `capability_detectors.py:detect_aerobic_respiration` (L1062-1134) already
  reads `genome_reaction_markers` and computes booleans:
  - `bo3_cc` = bo3 oxidase complex complete — **low-affinity, normal-air**
    (`:1110`, evidence string `:1129` "low-affinity, aerobic")
  - `cbb3_cc` = cbb3 oxidase complex complete — **high-affinity, microaerophilic**
    (`:1111`, evidence string `:1131` "high-affinity, microaerophilic")
  - `bd_cc` = bd oxidase (ambiguous) (`:1112`)
  - plus a `terminal_oxidases` BLAST hit list (`:1118-1120`).
- These are combined only into a generic aerobic-respiration score
  (`oxidase_complete = bo3_cc or cbb3_cc`, `:1123`) — the high/low-affinity
  distinction is **computed and then discarded**.

So the microaerophile discriminator the audit wants — *"high-affinity oxidase
present AND low-affinity bo3/caa3 absent"* (≈ `cbb3_cc and not bo3_cc`) — is a
small derivation on data already in hand. **No marker-DB write is required**
(which keeps a future implementation within the "no marker DB modification"
constraint for the *detection* part). `data/pathway_definitions.json` has no
microaerophile entry (only an unrelated mention at L327 re: mtoA Fe-oxidation
gap, A.4 — relevant to gids 1068/1072, see §6).

## 4. Proposed architecture (for morning review)

**Recommendation: an O2-tolerance *modifier flag* on existing aerobic modes —
NOT a new top-level cultivation mode.** Reasoning:

- Microaerophily is an **O2-tolerance property orthogonal to energy
  metabolism**. The P5 set spans three primary modes: a heterotroph
  (Campylobacter, aerobic_chemotrophic), an S-lithoautotroph (Beggiatoa,
  lithotrophic_aerobic), an Fe-lithoautotroph (Gallionella). A single new
  `microaerophilic` mode cannot represent "still does X metabolism, just at low
  O2" for all three — it would have to duplicate every aerobic composer.
- The **anammox (A4) precedent does NOT transfer here.** Anammox is a distinct
  energy metabolism with its own substrates → it earned its own mode in
  `_MODE_COMPOSERS`/priority. Microaerophily changes only one recipe field
  (atmosphere), not the metabolism → it should be a post-composition modifier,
  the same shape as the existing E.1 limitations-flag pass, not a mode.

Minimal change set for the recommended approach:
1. **Detection (no DB/marker write):** in `capability_detectors.py` derive a
   `microaerophilic` boolean from the already-parsed oxidase booleans
   (`cbb3_cc and not bo3_cc`, with `bd_cc` as a supporting/ambiguous signal),
   and surface it on the capability profile.
2. **Thread to recipe context:** carry the flag into `RecipeContext` (same way
   other capability facts already reach the composer).
3. **Composer hook:** one modifier applied after the aerobic composers run
   (mirrors `_apply_limitations_flags`): if the flag is set and the chosen mode
   is an aerobic one, rewrite `recipe.gas_phase.composition` to a reduced-O2 mix
   and lower shaking, with an honest rationale string. Touch points:
   `compose_recipe.py:847-849`, `:1124-1125`, `:1237-1238` (or, better, one
   shared post-pass so the value lives in exactly one place).
4. **Files touched:** `capability_detectors.py`, `compose_recipe.py`, possibly
   the recipe-context dataclass. **No** marker DB, FASTA, BLAST, or
   `pathway_definitions.json` change needed for the core fix.

## 5. Effort estimate (split per sub-task)

| Sub-task | Effort | Notes |
|----------|--------|-------|
| Detection layer (microaerophile flag) | **Low (~½ day)** | Signal already parsed; just `cbb3_cc and not bo3_cc` + surface it. Smaller than the plan feared. |
| Composer hook (O2 modifier) | **Low–Med (~½–1 day)** | One post-composition pass; the recipe already has a `GasPhase` field the audit notes is "already supported". |
| Per-organism O2 curation | **Low as a blanket value; Med if tuned** | The audit itself proposes a uniform ~3–5% O2 modifier (L1457), not per-organism values. A single default (e.g. microaerobic 2–6% O2, reduced shaking) resolves 8/10. Per-species tuning (e.g. Campylobacter ~5% vs Mariprofundus gradient) is a **refinement, not a blocker** — much less of an unknown than the plan assumed. |
| Fixing gids 1068/1072 primary mode | **Out of A3 scope** | Separate problem — see §6. |

## 6. STOP-and-report — A3 is not a single coherent task (Rule 7)

P5 bundles **two separable problems**:

- **Group A — pure O2-modifier (8 gids): 15, 16, 1020, 1040, 1083, 1098, 1108,
  1014.** Primary mode is already acceptable; only the atmosphere (and shaking)
  is wrong. The §4 modifier fully addresses these.
- **Group B — O2-modifier + primary-mode misclassification (2 gids): 1068
  Gallionella, 1072 Mariprofundus.** Both are obligate microaerophilic
  **Fe(II)-oxidizing chemolithoautotrophs** currently classified
  `aerobic_chemotrophic`; gid 1072 is composing an *organic glucose-oxidation*
  recipe (verified at HEAD). Lowering O2 does **not** make these recipes
  biologically correct — they need the Fe(II)-oxidation / `lithotrophic_aerobic`
  classification fixed first. This corresponds to the separate audit gap
  "neutrophilic/microaerophilic iron oxidation (mtoA pathway) not covered (A.4)"
  noted in `pathway_definitions.json:327`. **Decision needed:** treat Group B's
  mode misclassification as its own item; A3 should explicitly scope to Group A
  (+ apply the O2 modifier to Group B once their mode is independently fixed).

This is documented here and rolled into the overnight summary's morning queue.
No fix improvised.

---

## 7. STOP block — 2026-05-29 A3 implementation attempt (reverted, no code shipped)

The §4 design above is preserved unchanged as the original
morning-review recommendation. This §7 appends what the
implementation attempt on 2026-05-29 found when the design was
verified against current HEAD (`eff4db5`) before any code change.
**No code changes were made. Working tree at end of attempt matches
`eff4db5` modulo the carried-over
`data/validation/sourmash_identity_verification/` untracked dir.**

### 7.1 Discriminator-vs-targets drift

The proposed discriminator `cbb3_cc AND NOT bo3_cc` (§4 step 1)
fires on **4 of 10** named §1 targets and misses **6 of 10** at HEAD:

- **Fires** (4): gids 15 *Campylobacter jejuni*, 16 *Magnetospirillum
  magneticum*, 1020 *Paramagnetospirillum magneticum* AMB-1, 1108
  *Magnetospira* sp. QH-2.
- **Misses — both bo3 and cbb3 complete** (the trigger excludes by
  construction): gids 1083 *Beggiatoa alba* B18LD, 1098
  *Magnetospirillum gryphiswaldense* MSR-1.
- **Misses — neither bo3 nor cbb3 complex complete** (organism's
  terminal oxidase is detected only via the `terminal_oxidases` BLAST
  hit list, not via the cbb3/bo3 complex-complete booleans): gids
  1014 *Aquifex aeolicus* VF5, 1040 *Magnetococcus marinus* MC-1.
- **Misses — bo3 complete, cbb3 absent** (Group B Fe-oxidizers; their
  microaerophily is encoded in a different oxidase profile entirely):
  gids 1068 *Gallionella capsiferriformans* ES-2, 1072 *Mariprofundus
  ferrooxydans* PV-1.

This is the same shape of drift that killed the C2 R₃ §5 design (a
discriminator that silently excludes its own intended targets). Even
if everything else were correct, the lift would not deliver the
eight Group A organisms the §5 effort estimate scoped.

### 7.2 Cohort-wide false-fire scan

`cbb3_cc AND NOT bo3_cc` fires on **42 of 164 genomes with reaction
markers (25.6 % of the dev cohort)**. The fire set includes 8
oxygenic cyanobacteria (*Nostoc*, *Synechocystis*, *Microcystis*,
*Prochlorococcus*, *Synechococcus*, *Crocosphaera*, *Trichormus*,
*Anabaena*), ~18 normal aerobic heterotrophs and lithotrophs
(*Bradyrhizobium*, *Pelagibacter*, *Rhodobacter*, *Nitrobacter*,
*Nitrosomonas*, *Pseudomonas putida*, *Halothiobacillus*, *Frankia*,
*Aurantimonas*, *Roseobacter*, *Bacillus* SG-1, *Cupriavidus*,
*Halomonas*, *Pseudorhizobium*, *Thiobacillus denitrificans*,
*Paracoccus*, *Leptothrix*, *Methylocaldum*), **one strict anaerobic
SRB** (*Desulfotignum phosphitoxidans* gid 1095 — assigning ~5 % O₂
to a strict anaerobe is biologically catastrophic), and 4
validation/sentinel/blind-test records (gids 17, 19, 20, 1000) that
should not be touched by a feature lift at all. A 25.6 % cohort-wide
touch rate makes the discriminator structurally unfit for purpose.

### 7.3 GenomeSPOT O₂ source — structurally non-load-bearing

Across all 165 genomes with growth predictions,
`genome_growth_predictions WHERE target='oxygen'` takes only two
values: `tolerant` and `not tolerant`. There is no `microaerophile`
value in the cohort. The path at `derive_recipe_context.py:132` that
reads `genomespot_oxygen == "microaerophile"` is **dead code** in
practice.

For the 10 named A3 targets, GenomeSPOT calls 9 / 10 "tolerant" —
including every Group A microaerophile (*Campylobacter*, both
*Magnetospirilla*, *Magnetococcus*, *Beggiatoa*, *Magnetospira*) and
both Group B microaerophilic Fe-oxidizers (*Gallionella*,
*Mariprofundus*). The one "not tolerant" call (*Aquifex aeolicus*
gid 1014) is also wrong — *Aquifex* is a hyperthermophilic
microaerophile, not a strict anaerobe. **GenomeSPOT's binary
O₂-tolerance signal cannot discriminate microaerophiles from full
aerobes in this cohort, in either direction.** This is the analogue
of R₃'s "GenomeSPOT O₂ unreliable for archaea" caveat — here the
unreliability shape is different (no microaerophile class exists at
all) but the upshot is the same: the O₂-source fallback path is not
load-bearing for A3.

### 7.4 Pre-existing detection — the real gap is wiring, not detection

The §3 paragraph "no microaerophile pathway exists" is half-true. By
the literal names `cydAB` / `ctaABCDE` it holds; by the functional
equivalent it does not. Substantial pre-existing detection lives in
the codebase at HEAD and the §4 recommendation did not surface it:

- `synthesize_denovo.py:1284-1407` — `determine_atmosphere()` already
  implements the cbb3/bo3 discriminator end-to-end. Comments at
  L1294-1296 read: *"aa3/bo3 complex_complete → aerobic /
  cbb3/bd complex_complete only → microaerophilic / no terminal
  oxidases → anaerobic / both high and low affinity → facultative."*
- `derive_recipe_context.py:109-113` — when both `lithotrophic_aerobic`
  and `anaerobic_respiratory` appear in the cultivation-modes set,
  `Atmosphere.MICROAEROBIC` is already chosen as primary, with
  `[AEROBIC, ANAEROBIC]` set as alternatives.
- `derive_recipe_context.py:131-137` — backup path: `genomespot_oxygen
  == "microaerophile"` (dead — see 7.3) OR `(primary == AEROBIC and
  cbb3 cap and not bo3 cap)` (this is the report's discriminator,
  already wired into RecipeContext-primary selection, with the same
  false-fire problem as 7.2).
- `derive_recipe_context.py:735-754` — when `is_microaerophile =
  ("lithotrophic_aerobic" in modes and "anaerobic_respiratory" in
  modes)`, a `SpecialRequirement("microaerophile", "Microaerophilic
  conditions recommended. Use reduced O2 (2-5%) with N2/CO2 balance,
  or CampyGen sachets…")` is already appended. This is why gids
  1098 and 1108 already print *SPECIAL REQUIREMENTS: microaerophile*
  in current `inspect` output.
- `media_format.py:122-127`, `capability_vector.py:126`,
  `recipe_comparison.py:387-390` — downstream consumers already
  branch on the microaerophile token.

**At HEAD, gids 1098 and 1108 already have `Atmosphere.MICROAEROBIC`
as their RecipeContext primary atmosphere and a `microaerophile`
special requirement.** What's missing is wiring at the gas-phase
composer: the three `GasPhase(...)` sites in `compose_recipe.py`
(L847-849, L1124-1125, L1237-1238) hardcode their composition string
and never consult `cond.microaerophile` or any equivalent. The
existing detection has no effect on the final Recipe §10 gas-phase
output.

### 7.5 The "wire the existing flag through" path is NOT safe by inspection alone

The co-occurrence trigger backing `derive_recipe_context.py:737`'s
`SpecialRequirement` was scanned cohort-wide (production code path:
`profile_capabilities(gid, conn)` → `_mode_names`, evaluating
`"lithotrophic_aerobic" in modes AND "anaerobic_respiratory" in modes`).
**It fires on 19 of 165 genomes.** Categorisation by biology
(full per-gid list in `docs/PHASE_6_BACKLOG.md`, entry "A3
microaerophile modifier — rethink before re-attempt", subsection
"Narrow lift candidate"):

- **2 genuine A3 named targets**: 1098 *Magnetospirillum
  gryphiswaldense* MSR-1 and 1108 *Magnetospira* sp. QH-2 (both
  obligately microaerophilic magnetotactic Alphaproteobacteria).
- **3 plausibly genuine** (microaerophilic Aquificales or
  Campylobacterota, not in A3 targets; one is an audit-correction
  record and should not be feature-touched regardless).
- **2 lethal false fires — strict anaerobic green-sulfur
  phototrophs**: 1010 *Chlorobaculum tepidum* TLS, 1117
  *Chlorobaculum limnaeum* DSM 1677. For obligate anaerobes a 5 % O₂
  recipe is **lethal** — Chlorobi do not survive air-level oxygen
  exposure beyond brief transients, and ~5 % O₂ is well above
  tolerance. This fails more actively than the existing air-100 %
  bug: it does not merely produce a no-growth recipe, it produces a
  kill-the-inoculum recipe.
- **10 clear false fires** — facultatives wrongly downgraded to
  microaerophilic (free-living rhizobia, purple non-sulfur
  phototrophs, textbook facultative denitrifiers).
- **2 validation/audit records** — should not be feature-touched by
  any lift regardless.

The current state of `cond.microaerophile` at HEAD is **safe but
cosmetic**: the flag currently affects only the
`RecipeContext.atmosphere.primary` label and the
`SpecialRequirement("microaerophile", …)` advisory note printed in
the inspect SPECIAL REQUIREMENTS section. It does NOT touch
`recipe.gas_phase.composition` — the gas phase is determined per-mode
by the composers at `compose_recipe.py:847-849, 1124-1125,
1237-1238`, which never read `cond.microaerophile`. So the 13 false
fires above currently surface only as a display/advisory mismatch,
not as a wrong recipe. The narrow-lift idea ("Path A") would wire
`cond.microaerophile` into the gas-phase composer; that wiring would
turn a harmless 13-organism mislabel into a 13-organism wrong recipe,
including the 2 lethal *Chlorobaculum* cases. It is therefore not
shippable as a standalone change. See the backlog entry referenced
above for the full per-gid list and the guard work required before
this wiring could be safe.

### 7.6 Root cause and decision

A3 as designed in §4 cannot be implemented this session because:

1. The proposed discriminator misses 60 % of its own named targets.
2. The proposed discriminator false-fires on 25.6 % of the dev
   cohort, including biologically incompatible categories (strict
   anaerobes, oxygenic phototrophs).
3. The GenomeSPOT O₂ fallback is structurally non-load-bearing in
   this cohort.
4. The "wire the existing flag through" alternative is not safe to
   enable without further gating — its underlying co-occurrence
   trigger also false-fires on 13/19 organisms including 2 strict
   anaerobic phototrophs where a microaerobic recipe would be
   actively lethal to the inoculum.
5. The actual gap at HEAD is the gas-phase composer ignoring already-
   computed microaerophile flags — but enabling that pipe without
   first redesigning the upstream discriminator turns a now-cosmetic
   mismatch into a wrong recipe.

**Action**: take A3 back to inspection. No code shipped. The §4
recommendation is preserved above as the original morning-review
proposal; this §7 is the implementation-attempt audit. Both stay in
the doc per the methodology-record discipline. Redesign and the
narrow-lift option are tracked together as a single A3-rethink
backlog item in `docs/PHASE_6_BACKLOG.md` (with the narrow lift as a
subordinate subsection marked not independently shippable).

**Cohort-scan numbers (this session)**:

- cbb3 ∧ ¬bo3 trigger: 42 / 164 genomes (25.6 %)
- co-occurrence trigger (`lithotrophic_aerobic` ∧ `anaerobic_respiratory`
  in primary modes): 19 / 165 genomes (11.5 %)
- 10 named §1 A3 targets, fires by each trigger: cbb3∧¬bo3 = {15, 16,
  1020, 1108}; co-occurrence = {1098, 1108}.

**Files touched this attempt**: none. Working tree matches HEAD
`eff4db5` modulo the carried-over untracked
`data/validation/sourmash_identity_verification/`.

**Surfaced**: 2026-05-29 A3 microaerophile-modifier implementation
attempt (no code shipped).
