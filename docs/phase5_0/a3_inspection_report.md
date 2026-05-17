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
