# A4 Inspection Report — Anammox Composer Guard for Scalindua

Date: 2026-05-15 · Read-only inspection · CultureForge git HEAD 4be3d23
(post-A1). **No code, marker DB, or DB rows were modified** in producing this
report. Phase 6 item "A4" maps to audit recommendation **P3** ("Add anammox
cultivation-mode mapping in the recipe composer", predictions_audit.md:1393).

## Headline

The audit's P3 framing is **stale and largely already resolved**. The anammox
cultivation mode, its composer, mode dispatch, priority entry, and
marker-corroboration **all already exist** (implemented in Phase 5.1) and work
correctly for Brocadia/Jettenia. The *only* remaining failure — the two
Scalindua MAGs (gid 30, gid 1105) — is caused by a **stale, unconditional
species-name escalation guard** in the composer, not by a missing mode or a
missing/divergent marker. The guard's own rationale text is empirically false.

---

## Task 1 — The two Scalindua targets

DB query (`notes LIKE '%Scalindua%'`):

| gid | accession | organism (from notes) |
|----:|-----------|-----------------------|
| 30 | GCF_002443295.1 | *Candidatus* Scalindua japonica husup-a2 MAG (AUDIT CORRECTION 2026-05-05: gid 30 previously held Salmonella data; re-downloaded + re-processed) |
| 1105 | GCF_000786775.1 | *Candidatus* Scalindua brodae (Phase 5.0 main) |

`inspect --section capabilities` / `--section recipe` results:

| gid | Anammox cap | primary mode (capability layer) | hzsA / hdh detected | recipe composes? | escalation reason (verbatim) |
|----:|---|---|---|---|---|
| 30 | **0.950 (detected, primary)** | anammox (conf 0.95) | hzsA 63.9% bs=1074 ✓; hdh 76.9% bs=967 ✓ | **NO — ESCALATED** | "Scalindua MAG lacks hzsA/hdh in predicted proteome. The composed recipe routes to the next-best detected mode but is not biologically correct. Manual annotation or improved MAG required." (overall conf 0.45) |
| 1105 | **0.950 (detected, primary)** | anammox (conf 0.95) | hzsA 64.4% bs=1068 ✓; hdh 78.1% bs=987 ✓ | **NO — ESCALATED** | identical reason text, overall conf 0.45 |

Both targets: Anammox capability fires at 0.95, the `anammox` mode is selected
as the **primary** cultivation mode, yet the recipe escalates. The escalation
reason claims the proteome "lacks hzsA/hdh" — directly contradicted by the
capability output, which is detecting Anammox *because* hzsA and hdh are both
present as strong positive marker hits.

---

## Task 2 — Anammox baseline (hold-PASS set)

DB query (`Brocadia|Kuenenia|Jettenia|Anammoxoglobus|anammox`, excluding the
two Scalindua targets) — no Kuenenia/Anammoxoglobus genomes are in the DB:

| gid | accession | organism | Anammox cap | primary mode | recipe | overall conf | status |
|----:|-----------|----------|---|---|---|---|---|
| 1001 | GCA_000949635.1 | *Ca.* Brocadia sinica JPN1 (smoke test) | 0.860 | **anammox** | **COMPOSES** (N2/CO2 90:10 anaerobic) | 0.80 (high) | **PASS** |
| 1002 | GCA_000987375.1 | *Ca.* Brocadia fulgida | 0.860 | **anammox** | **COMPOSES** (N2/CO2 90:10 anaerobic) | 0.80 (high) | **PASS** |
| 1090 | GCF_000296795.1 | *Ca.* Jettenia caeni | 0.860 | **anammox** | **COMPOSES** (N2/CO2 90:10 anaerobic) | 0.80 (high) | **PASS** |

All three currently **PASS** with the correct anaerobic anammox recipe — they
are **not** failing and **not** falling back to `lithotrophic_aerobic`. This is
the hold-PASS regression set for Step 2. (This directly contradicts the audit;
see Task 5.)

---

## Task 3 — Anammox detection-and-composition code path

### Pathway definition (`data/pathway_definitions.json` → key `anammox`)

- Step "nitrite reduction to nitric oxide" — weight 1.0 (nirS/nirK; no marker)
- Step "hydrazine synthesis from ammonium and nitric oxide" — weight **2.5**,
  `diagnostic_marker: "hzsA"` (EC 1.7.2.7)
- Step "hydrazine oxidation to dinitrogen" — weight **2.0**,
  `diagnostic_marker: "hdh"` (EC 1.7.2.8; patterns include `hzo`)
- Optional transporters: ammonium (`amt`), nitrite (`nirC`). Cofactor: heme c.
- `negative_markers: []`. **No `essential_marker`, no
  `diagnostic_marker_override`.**
- `known_limitations: ["E.1"]`,
  `limitation_summary: "Scalindua-type hzsA too divergent for BLAST or HMM
  detection. Deep-branching anammox lineages may be missed entirely (E.1)."`
  → **This summary is stale/false**: Scalindua hzsA is detected at ~64%
  identity, bitscore ~1070, well above the 30%/70% positive-call threshold.

### Detector logic (`capability_detectors.py`)

No anammox-specific code beyond the generic pathway scorer. The only anammox
references are the cultivation-mode-group map at **capability_detectors.py:112**
(`"anammox": ["Anaerobic ammonium oxidation"]`) and a generic comment at line
1074. Detection is purely the weighted pathway-step score + diagnostic-marker
boost (hzsA step 2.5 + hdh step 2.0, both boosted 1.5× when pident ≥ 40 and
bitscore ≥ 300 — satisfied for both Scalindua MAGs → Anammox 0.95).

### Composer (`compose_recipe.py`)

`_compose_anammox_recipe(context, conn=None)` at **compose_recipe.py:616** —
docstring explicitly notes "Marine Scalindua species require seawater
salinity"; the body even adds a Scalindua-specific NaCl note
(compose_recipe.py:712–728). It is fully wired:

- Mode → composer dispatch: `_MODE_COMPOSERS["anammox"] =
  _compose_anammox_recipe` (compose_recipe.py:1526)
- In `_SPECIFIC_MODES`/priority list (compose_recipe.py:1554)
- In `_MARKER_REQUIRED_MODES` (compose_recipe.py:1578)
- `_MODE_DIAGNOSTIC_MARKERS["anammox"] = ["hzsA", "hdh", "hao"]`
  (compose_recipe.py:1590) — Scalindua has positive hzsA + hdh, so the mode
  **is** marker-corroborated and not blocked by `_MARKER_REQUIRED_MODES`.
- A defensive-fallback comment at compose_recipe.py:1053 reads
  *"Phase 5.1 P3: superseded by top-level anammox mode"* — confirming the P3
  composer mapping was implemented in Phase 5.1.

### What "escalation" looks like here — the exact trigger

`compose_recipe()` (compose_recipe.py:175) runs the composer (anammox recipe is
fully built), then calls `_apply_limitations_flags(recipe, context)` at
**compose_recipe.py:222**. Inside that post-composition annotation pass,
**compose_recipe.py:2005–2020** ("E.1 — Scalindua MAG completeness"):

```python
if context.species and "scalindua" in context.species.lower():
    recipe.limitations_referenced.append("E.1")
    recipe.uncertainty_flags.append("Scalindua-clade detection failure is a MAG
        completeness limitation: predicted proteome lacks hzsA / hdh ...")
    recipe.escalated = True
    recipe.escalation_reason = ("Scalindua MAG lacks hzsA/hdh in predicted
        proteome. The composed recipe routes to the next-best detected mode
        but is not biologically correct. Manual annotation or improved MAG
        required.")
```

This fires **unconditionally on the species name** — it never inspects marker
hits or the Anammox capability score — and overwrites an already-correctly-
composed anammox recipe with `escalated = True`.

---

## Task 4 — Specific Scalindua failure mode

For both gid 30 and gid 1105 the divergence from the PASS baseline (1001/1002/
1090) is a **single post-composition guard**, not a detection or mapping gap:

1. **Anammox capability**: detected at **0.95** for both (vs 0.86 for the
   baseline) — *higher* than the passing baseline. hzsA + hdh both positive.
2. **Mode selection**: `anammox` is selected as the **primary** cultivation
   mode for both (capabilities output: "Mode: anammox conf 0.95").
3. **Composer entry**: yes — `_compose_anammox_recipe` is dispatched and builds
   the correct anaerobic recipe (same path as 1001/1002/1090).
4. **Escalation cause**: `_apply_limitations_flags` → the E.1 block
   (compose_recipe.py:2005–2020) sets `recipe.escalated = True` purely because
   `context.species` contains "scalindua".

Verbatim recipe-section output (both gids):

> RECIPE (Section 10)
> ESCALATED — no recipe composed
>   Reason: Scalindua MAG lacks hzsA/hdh in predicted proteome. The composed
>   recipe routes to the next-best detected mode but is not biologically
>   correct. Manual annotation or improved MAG required.
>   Overall confidence: 0.45

Verbatim capabilities output (gid 30; gid 1105 analogous):

> Mode: anammox                                  conf 0.95
>   ├─ Anammox                                            0.950
>   │   hydrazine synthesis from ammonium and nitric oxide: diagnostic marker hzsA detected (63.9% id, bs=1074)
>   │   hydrazine oxidation to dinitrogen: diagnostic marker hdh detected (76.9% id, bs=967)

One sentence: **Scalindua is detected as anammox at 0.95 and its correct
anaerobic recipe is composed, but a stale species-name guard then force-
escalates it with a rationale ("lacks hzsA/hdh") that the detection data
proves false.**

---

## Task 5 — Compare against the audit's "A4"/P3 framing

Audit, verbatim:

> **(predictions_audit.md:17)** "Anammox bacteria detect Anammox capability at
> 0.95 but the recipe composer has no `anammox` cultivation mode, so gids 30
> (Scalindua japonica) and 1105 (Scalindua brodae) escalate, while gids
> 1001/1002/1090 fall back to `lithotrophic_aerobic` with a misleadingly
> aerobic recipe. The capability layer works; the composer-side mapping is the
> gap."

> **(predictions_audit.md:1393–1395, P3)** "Add anammox cultivation-mode
> mapping in the recipe composer. **Impact:** 2 FAILs (gids 30, 1105 — both
> escalate) + 3 PARTIALs (1001, 1002, 1090 — mode falls back to
> `lithotrophic_aerobic` ...). ... the gap is at the composer end. ... Mapping
> is mechanical once the cultivation mode is registered."

**Consistency with Task 4: NOT consistent — the audit is stale on specifics**
(exactly the A1-style "audit can be wrong about specifics" situation):

- Audit: "composer has no `anammox` cultivation mode." **FALSE at HEAD.** The
  mode, composer, dispatch, priority, and marker-corroboration all exist
  (Phase 5.1; compose_recipe.py:616/1053/1526/1554/1578/1590).
- Audit: gids 1001/1002/1090 "fall back to `lithotrophic_aerobic` with a
  misleadingly aerobic recipe." **FALSE at HEAD.** All three compose as
  primary mode `anammox`, N2/CO2 90:10 anaerobic, overall confidence 0.80.
  They already PASS — they are the hold-PASS set, not PARTIALs to fix.
- Audit: gids 30/1105 escalate because of the missing composer mapping.
  **Mechanism is wrong.** They escalate because of the
  E.1 species-name guard (compose_recipe.py:2005–2020) added *after* the
  audit and *after* the P3 fix — the audit predates both.
- The guard's self-description ("routes to the next-best detected mode") is
  also inaccurate: anammox *is* the primary detected mode (0.95), so the
  recipe being discarded is the correct anammox recipe, not a fallback.

The audit was written before P3 was implemented (Phase 5.1) and before the
gid-30 MAG was audit-corrected (2026-05-05, Salmonella → Scalindua japonica
husup-a2). The guard was almost certainly correct *at the time it was written*
(the original gid-30 MAG likely lacked hzsA/hdh); it is now stale because the
re-processed MAGs do contain detectable hzsA/hdh.

---

## Task 6 — Marker DB check

Anammox-relevant marker references in `data/diagnostic_markers/`:

| marker | threshold (run_marker_blast.py) | refs | source organisms | Scalindua present? |
|---|---|---|---|---|
| hzsA | evalue 1e-30, **pident 30.0**, qcov 70.0 (L67) | 7 | Kuenenia stuttgartiensis, Brocadia anammoxidans/sinica JPN1/carolinensis, uncultured Brocadia, Jettenia asiatica/ecosi | **NO** |
| hdh | default (evalue 1e-30, pident 30.0, qcov 70.0) | 3 | Kuenenia stuttgartiensis (×3; one is the HAO_KUEST cross-entry) | **NO** |
| hao | default | 3 | Nitrosococcus oceani, Nitrosospira multiformis, Kuenenia stuttgartiensis | **NO** |

`grep -irl scalindua data/diagnostic_markers/*.fasta` → **no Scalindua in any
marker FASTA.** Despite this, Scalindua detection **succeeds cross-clade**:
gid 30/1105 hzsA hits the Brocadia/Kuenenia refs at ~62–64% identity
(bitscore ~1030–1074, positive_call=1), and hdh hits the Kuenenia refs at
~76–78% identity (bitscore ~950–987, positive_call=1). Both clear the 30%/70%
positive-call gate by a wide margin.

**Conclusion: the fix is NOT marker-side.** Scalindua is already detected
without a Scalindua reference. Adding Scalindua marker references would be a
robustness nice-to-have but is unnecessary for this fix and is out of scope
per the constraints. The stale claim in the pathway-def `limitation_summary`
("Scalindua-type hzsA too divergent for BLAST or HMM detection") is wrong.

---

## Architecture Recommendation for Step 2

### (a) Root cause (one paragraph)

The two Scalindua MAGs (gid 30 *Ca.* Scalindua japonica husup-a2, gid 1105
*Ca.* Scalindua brodae) are correctly detected as anammox (capability 0.95,
hzsA ~64% bs~1070 and hdh ~77% bs~970 both positive), the `anammox`
cultivation mode is selected as primary, and `_compose_anammox_recipe` builds
the biologically-correct anaerobic recipe — but a stale, unconditional
species-name guard at **compose_recipe.py:2005–2020** ("E.1 — Scalindua MAG
completeness"), run from `_apply_limitations_flags` (compose_recipe.py:222),
overwrites that recipe with `escalated = True` for *any* species containing
"scalindua", regardless of marker evidence. Its rationale ("predicted proteome
lacks hzsA / hdh") was true for the pre-correction gid-30 MAG but is now
factually false for both current MAGs. Audit P3 ("composer has no anammox
mode; mapping is mechanical once registered") is obsolete: the mapping was
implemented in Phase 5.1 and already works for Brocadia/Jettenia.

### (b) Fix locus

**Composer-side only.** Not marker-side (detection already works without
Scalindua refs), not pathway-def-side for behavior (the pathway def scores
correctly; only its stale `limitation_summary` text is cosmetically wrong),
and not detector-side (no anammox-specific detector logic exists or is
needed).

### (c) Minimal change set for Step 2

1. **`compose_recipe.py:2005–2020`** (the E.1 block) — the only behavioral
   change. Recommended: make the escalation **conditional on actual marker
   absence** rather than on the species name — e.g., only escalate when the
   Anammox capability is *not* detected / hzsA+hdh are *not* positive for this
   genome. This preserves the guard's original protective intent for a
   genuinely incomplete future Scalindua MAG while letting the two current,
   marker-positive MAGs compose. (A flat deletion also works but loses the
   safety net for low-quality MAGs.)
2. **`data/pathway_definitions.json`** → `anammox` `limitation_summary`
   (stale-text correction only; no behavioral effect): the "Scalindua-type
   hzsA too divergent for BLAST/HMM" claim is contradicted by detection at
   ~64% identity. Recommended for honesty, optional for function.
3. **`docs/phase5_0/predictions_audit.md`** → P3 errata note (A1-style):
   record that P3's composer mapping was already implemented in Phase 5.1,
   that 1001/1002/1090 already PASS (not PARTIAL), and that the residual
   gid 30/1105 failure is the stale E.1 species-name guard, not a missing
   mode. Documentation only.
4. Optionally also reconcile `docs/LIMITATIONS.md` E.1 wording (out of scope
   if it risks scope creep; flag for the human).

No marker DB changes, no DB row writes, no detector changes, no pathway-step
weight changes.

### (d) Verification matrix

**Targets that must flip (escalate → compose):**

| gid | organism | expected after fix |
|----:|----------|--------------------|
| 30 | *Ca.* Scalindua japonica husup-a2 | recipe composes, primary mode `anammox`, anaerobic N2/CO2 90:10, NaCl seawater-salinity note present, not escalated, overall conf ≈ 0.80 |
| 1105 | *Ca.* Scalindua brodae | same |

**Must hold (no regression, recipe still composes as anammox ≈ 0.80):**

| gid | organism |
|----:|----------|
| 1001 | *Ca.* Brocadia sinica JPN1 |
| 1002 | *Ca.* Brocadia fulgida |
| 1090 | *Ca.* Jettenia caeni |

**Cross-reactivity / no-false-escalation sentinels:**

- A non-anammox N-cycle organism with `hao` but no `hzsA`/`hdh` — e.g.
  **gid 18** *Nitrosomonas europaea* (AOB): must remain non-anammox and
  compose its normal recipe (confirms conditioning the guard on marker
  evidence does not leak anammox to hao-only organisms).
- The `"scalindua"` substring is genus-unique (no other DB organism name
  contains it), so removing/conditioning the guard cannot affect non-Scalindua
  organisms — but a sanity sweep that *no* previously-escalating non-anammox
  organism newly composes anammox is cheap insurance.
- If the conditional-escalation option is chosen, add a synthetic check that a
  hypothetical hzsA/hdh-negative "scalindua"-named genome still escalates
  (preserves the safety net).

### (e) Surprises / audit-specification corrections (A1-style)

1. **P3 is already done.** The audit's "composer has no anammox cultivation
   mode" is false at HEAD; the mode + composer + dispatch + priority +
   marker-corroboration were implemented in Phase 5.1
   (compose_recipe.py:616/1053/1526/1554/1578/1590).
2. **1001/1002/1090 already PASS**, not PARTIAL. They compose as primary mode
   `anammox`, anaerobic N2/CO2, overall conf 0.80 — not the
   "misleadingly aerobic `lithotrophic_aerobic` fallback" the audit describes.
   The audit's P3 impact line (2 FAIL + 3 PARTIAL) is now (2 FAIL + 0 PARTIAL).
3. **The real blocker is an undocumented stale guard**, not the audit's stated
   cause. The E.1 guard (compose_recipe.py:2005–2020) is unconditional on
   species name and post-dates the audit; its embedded rationale ("lacks
   hzsA/hdh") is empirically false for both current Scalindua MAGs (hzsA ~64%
   bs~1070, hdh ~77% bs~970, Anammox cap 0.95).
4. **The guard mis-describes its own behavior** ("routes to the next-best
   detected mode"): anammox *is* the primary detected mode, so the discarded
   recipe is the correct anammox recipe.
5. **Marker DB has zero Scalindua references** yet detection still works
   cross-clade — so this is decisively *not* a marker problem, and the
   pathway-def `limitation_summary` claiming Scalindua hzsA is "too divergent
   for BLAST or HMM detection" is stale and should be corrected.
6. **gid 30 provenance caveat**: gid 30 is an audit-corrected substitution
   (*Scalindua japonica* husup-a2 MAG replacing the unavailable original
   *Scalindua profunda*; pre-2026-05-05 it held Salmonella data). The guard
   was likely valid for the pre-correction MAG; it is the genome refresh, not
   a code regression, that made the guard stale. Step 2 should treat the guard
   as "fix the staleness," not "the guard was always wrong."
