# A1 Inspection Report — Archaeal AOA amoA Marker Extension

Date: 2026-05-15 · Read-only inspection · CultureForge git working tree

## Context

Phase 6 item A1 (audit recommendation P4 in `docs/phase5_0/predictions_audit.md`):
three ammonia-oxidizing archaea (AOA) FAIL the predictions audit because the
`ammonia_oxidation` capability never fires for them:

- gid 1049 *Nitrosopumilus maritimus* SCM1
- gid 1102 *Nitrososphaera viennensis* EN76
- gid 1106 *Candidatus* Nitrosocosmicus oleophilus MY3

This is a **read-only inspection** to ground the Step-2 architectural decision
(additive references vs. split `amoA_bacterial` / `amoA_archaeal` marker) in
verified evidence rather than "structurally analogous" reasoning. **No code,
marker DB, data/, or DB files were modified in producing this report.**

## Task 1 — Marker DB layout for ammonia monooxygenase

Marker reference files live in `data/diagnostic_markers/` as
`<marker>_refs.fasta` + a prebuilt BLAST DB `blastdb_<marker>.*`. 31 markers
total. CuMMO-superfamily / ammonia-oxidation-relevant markers present:
`amoA`, `pmoA`, `mmoX`, `hao`. No `bmoA`/`hmoA` (butane/other CuMMO) markers.

### `amoA_refs.fasta` — 4 references, ALL bacterial, ZERO archaeal

| Header accession | Organism | Lineage | Length (aa) | Origin |
|---|---|---|---|---|
| O85076 | *Nitrosospira multiformis* | β-proteobacteria (`_9PROT`) | 274 | Bacterial AOB |
| P95336 | *Nitrosospira briensis* | β-proteobacteria (`_9PROT`) | 274 | Bacterial AOB |
| A0A7D4WXT9 | *Candidatus* Nitrospira inopinata | Nitrospirota (`_9BACT`) | 138 (fragment) | Bacterial comammox |
| A0A8D4WF74 | uncultured *Nitrospira* sp. | Nitrospirota (`_9BACT`) | 79 (fragment) | Bacterial comammox |

**No Thaumarchaeota / AOA references exist.** Note *Nitrosomonas europaea*
itself is **not** in the set — bacterial AOB detection works via the
close relative *Nitrosospira*.

### `pmoA_refs.fasta` — 6 references (methanotroph pMMO β-subunit), all bacterial

Q607G3 (*Methylococcus capsulatus* Bath, 247), A4PDX7 (*Methylocaldum* sp., 247),
Q50541 (*Methylosinus trichosporium*, 252), O06122 (*Methylocystis* sp. M, 252),
I0JZS9 (*Methylacidiphilum fumariolicum* SolV, 245), A9QPD9 (*Methylacidiphilum
infernorum* V4, 249). Covers Type I/II/III methanotrophs.

### `mmoX_refs.fasta` — 4 references (soluble MMO α-chain)

P22869 (*M. capsulatus*, 527), P27353 (*M. trichosporium*, 526), Q3YA75
(*Methylomonas* sp., 526), Q3T939 (*Methylocella silvestris*, 526).

### `hao_refs.fasta` — 3 references (hydroxylamine oxidoreductase)

M5DCM0 (*Nitrosococcus*-class, 580), A0A1I0GQH4 (580→573), Q1PX48
(*Kuenenia stuttgartiensis* anammox, 536). **All bacterial; no archaeal hao.**

Other CuMMO-family markers (bmoA, hmoA): **none present.**

## Task 2 — Detector logic for `ammonia_oxidation`

`capability_detectors.py` does **not** hard-code amoA; capabilities are
data-driven from `data/pathway_definitions.json` consumed by
`detect_pathway_integrity()` (capability_detectors.py:243). Canonical
capability key: **`ammonia_oxidation`**; user-facing name
"Aerobic ammonia oxidation"; cultivation-mode group `lithotrophic_aerobic`
(capability_detectors.py:108-112).

### Pathway definition (`data/pathway_definitions.json` → `ammonia_oxidation`)

Steps and weights:
- "ammonia monooxygenase" — weight **2.5**, `diagnostic_marker: "amoA"`,
  patterns `ammonia monooxygenase|amoA|amoB|amoC`, EC 1.14.99.39
- "hydroxylamine oxidoreductase" — weight **2.0**, `diagnostic_marker: "hao"`,
  patterns `hydroxylamine oxidoreductase|haoA`, EC 1.7.2.6
- "cytochrome c554" — weight 0.8
- "cytochrome cM552" — weight 0.8

Total weight ≈ 6.1. Optional `ammonium transporter`; heme-biosynthesis
cofactor. Carries `"known_limitations": ["A.2"]` with summary:
*"Comammox amoA (Nitrospirota) too divergent from beta-proteobacterial
references; may be missed entirely (A.2)."*

**`ammonia_oxidation` has NO `diagnostic_marker_override` and NO
`essential_marker`.** Contrast: `aerobic_methanotrophy` HAS a
`diagnostic_marker_override` (pmoA, min_pident 60, min_qcov 80,
override_confidence 0.7); `lithotrophic_aerobic_nitrite` HAS
`essential_marker: nxrA` + override. Ammonia oxidation has neither —
its confidence is purely the weighted step score.

### BLAST thresholds (`run_marker_blast.py:43-84`)

Default `HIT_THRESHOLDS = {evalue 1e-30, pident 30.0, qcov 70.0}`.
Per-marker override:

```python
MARKER_THRESHOLDS = {
    "amoA":  {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    ...
    "pmoA":  {"evalue": 1e-30, "pident": 60.0, "qcov": 80.0},
    "mmoX":  {"evalue": 1e-30, "pident": 50.0, "qcov": 70.0},
}
```

Comment at run_marker_blast.py:51-54 explicitly claims amoA "spans AOB
(beta-proteobacteria), comammox (Nitrospirota), **AOA (Thaumarchaeota)**" —
**this is contradicted by the reference data (Task 1): no AOA refs exist.**
Documented intent/implementation mismatch.

In `detect_pathway_integrity` a marker hit only counts (sets step found,
1.5× boost) if `pident >= 40 AND bitscore >= 300` (capability_detectors.py:295)
— stricter than the BLAST positive-call gate. amoA / hao share the generic
pathway-step path; **bacterial-vs-archaeal origin is NOT tracked downstream.**
amoA and pmoA are separate markers/steps in separate pathway defs; no shared
code path beyond the generic scorer.

## Task 3 — Composer behavior for ammonia oxidizers

`ammonia_oxidation` → cultivation-mode group **`lithotrophic_aerobic`**
(capability_detectors.py:108). In `compose_recipe.py`,
`_compose_lithotrophic_aerobic_recipe` (compose_recipe.py:~1106) is the
dedicated chemolithoautotroph composer: aerobic gas phase, NH4+/inorganic
electron donor, CO2/bicarbonate carbon source, mineral salts. There is a
dedicated chemolithoautotrophic-ammonia-oxidizer route — **but AOA never
reach it**: `ammonia_oxidation` confidence stays at 0.30 (rejected), so
the genome enters no mode and the recipe **ESCALATES** (no recipe composed).
`lithotrophic_aerobic` is in `_MARKER_REQUIRED_MODES` with
`_MODE_DIAGNOSTIC_MARKERS["lithotrophic_aerobic"]` including `amoA` — so
even pathway-only signal cannot rescue the mode without an amoA marker hit.

## Task 4 — Positive controls & FAIL targets (`inspect --section capabilities`)

| gid | Organism | Type | amoA hit | `ammonia_oxidation` | Verdict |
|---|---|---|---|---|---|
| 18 | *Nitrosomonas europaea* | Bacterial AOB | 85.3% id, bs=491 | **0.916 detected** | PASS ✓ |
| 1039 | *Nitrosomonas eutropha* C91 | Bacterial AOB | 84.9% id, bs=493 | **0.816 detected** | PASS ✓ |
| 1114 | *Ca.* Nitrospira inopinata | Comammox | 60.0% id, bs=355 | **0.916 detected** | PASS ✓ (see note) |
| 1049 | *Nitrosopumilus maritimus* | **AOA** | none | 0.300 (pathway 0.00) | **FAIL ✗** |
| 1102 | *Nitrososphaera viennensis* | **AOA** | none | 0.300 (pathway 0.00) | **FAIL ✗** |
| 1106 | *Ca.* Nitrosocosmicus oleophilus | **AOA** | none | 0.300 (pathway 0.00) | **FAIL ✗** |

Bacterial AOB/comammox PASS; all three AOA FAIL — confirmed. The AOA
pathway score is **0.00**, not merely "amoA marker missing": gapseq
pattern search ALSO fails to recognise archaeal amoA/amoB/amoC, AND the
bacterial-type `hao` step (weight 2.0) is genuinely absent (AOA lack
canonical HAO; they use a divergent, still-debated hydroxylamine/NO route).

> **Note (1114 comammox):** passes only because its *own* amoA fragment
> (A0A7D4WXT9) is literally one of the 4 references — circular/overfit.
> The reference set is sparse; robustness, not just clade coverage, matters.

## Task 5 — Cross-reactivity baseline

Task instruction said "inspect 21 (Methylococcus capsulatus)". **gid 21 is
*Syntrophomonas wolfei*, not Methylococcus.** Methylococcus capsulatus Bath
is **gid 900** (SENTINEL). Both inspected:

- **gid 900** *Methylococcus capsulatus* Bath: `methanotrophic` mode conf
  **0.80**, pmoA 100.0% id bs=501, mmoX present. `ammonia_oxidation` =
  **0.326 (rejected, below threshold)** → pmoA does **not** currently
  cross-react into ammonia oxidation. Clean sentinel baseline.
- **gid 21** *Syntrophomonas wolfei*: `syntrophic` 0.70; no methanotrophy
  (0.250 rej), no ammonia oxidation. (Identity discrepancy noted.)

The Step-3 risk to watch: adding divergent archaeal amoA refs at a permissive
threshold could let pmoA-bearing methanotrophs cross-hit, eroding the
empirically tuned pmoA 60%/amoA 50% Phase-3.5 separation. gid 900 is the
sentinel that must stay methanotrophic-only after any change.

## Task 6 — Candidate archaeal amoA references (verification only)

**The two accessions named in the audit are BOTH WRONG (hallucinated):**

| Audit-claimed | Reality (verified via UniProt) |
|---|---|
| Q5JIJ3 = "Nitrosopumilus AmoA-1" | **WRONG** — uncharacterized protein TK1987, *Thermococcus kodakarensis* (hyperthermophile, not an AOA), 128 aa |
| Q57F89 = "Nitrososphaera AmoA" | **WRONG** — endo-α-1,4-polygalactosaminidase, *Brucella abortus*, 129 aa |

**Real archaeal amoA accessions (verified, UniProtKB):**

- *Nitrosopumilus maritimus* (target gid 1049): **D9J260** (214 aa),
  D9J261 (214), D9J262 (208), D9J263 (208), A0A0U3R9G0 (193). All
  "Ammonia monooxygenase subunit A", gene amoA, TrEMBL.
- *Nitrososphaera viennensis* EN76 (target gid 1102): **A0A060HNG6**
  (216 aa, ORF NVIE_027270 — matches strain EN76), F4N9Y5 (216 aa).
- *Ca.* Nitrosocosmicus oleophilus (target gid 1106): **A0A654M1Z2**
  (216 aa, "Archaeal ammonia monooxygenase subunit A (AmoA)") — exact
  species match. (Genus fallbacks: *N. arcticus* A0A5B8ZQK3 196 aa,
  *N. franklandianus* A0A140CT22 197 aa.)

Sequences NOT downloaded (deferred to Step 3 per instructions).

---

## Architecture Recommendation for Step 2: SPLIT, not additive — and a marker fix alone is insufficient

### Recommendation

1. **Split the marker**: create `amoA_archaeal` as a *separate* marker with
   its own reference set (D9J260 Nitrosopumilus, A0A060HNG6 Nitrososphaera
   EN76, A0A654M1Z2 Nitrosocosmicus oleophilus, plus 1–2 genus outgroups)
   and its own clade-appropriate threshold. Keep `amoA` (bacterial/comammox)
   unchanged so the Phase-3.5 pmoA×amoA cross-reactivity calibration and the
   passing bacterial controls (gids 18, 1039, 1114) are not disturbed.
   This mirrors the codebase's **proven** dual-clade pattern for `nxrA`
   (Type A/B, <25% inter-clade identity, separate handling) and `pmoA`
   (Type I/II/III) — the literal same problem, already solved twice here,
   not analogy.
2. **Pathway-definition change is mandatory in the same step**: a split
   marker alone will NOT clear the `detected` gate
   (`confidence ≥ 0.50 AND pathway_score ≥ 0.40`). AOA pathway score is
   **0.00** today. Adding archaeal amoA recovers only the amoA step
   (2.5/6.1 ≈ 0.41 weighted) — and the bacterial-type `hao` step
   (2.0/6.1 ≈ 0.33) plus the two bacterial cytochrome steps (0.8 each)
   stay unmet because AOA genuinely lack them. Step 2 must also add a
   `diagnostic_marker_override` to the `ammonia_oxidation` pathway def
   (keyed on amoA-bacterial OR amoA-archaeal, with a confidence floor,
   exactly as `aerobic_methanotrophy` already does for pmoA) and make the
   bacterial `hao`/cytochrome steps optional or down-weighted when the
   archaeal amoA marker is the hit.
3. **Guard with the cross-reactivity sentinel**: gid 900 (*Methylococcus
   capsulatus*) must remain methanotrophic-only and `ammonia_oxidation`
   must stay rejected after the change; bacterial controls 18/1039/1114
   must remain PASS at ≥0.80.

### Critical files (Step 2, not this step)

- `data/diagnostic_markers/amoA_archaeal_refs.fasta` (new) + rebuilt BLAST DB
- `run_marker_blast.py` `MARKER_THRESHOLDS` (add `amoA_archaeal` entry)
- `data/pathway_definitions.json` → `ammonia_oxidation`
  (add `diagnostic_marker_override`; restructure hao/cytochrome step weights)
- `compose_recipe.py` `_MODE_DIAGNOSTIC_MARKERS["lithotrophic_aerobic"]`
  (add `amoA_archaeal`)
- No change needed to `capability_detectors.py` (data-driven).

### Verification (Step 2, end-to-end)

- `python3 cultureforge.py inspect <1049|1102|1106> --section capabilities`
  → `ammonia_oxidation` detected ≥ 0.50, mode `lithotrophic_aerobic`, recipe
  composes (no escalation).
- Regression: gids 18, 1039, 1114 still detected ≥ 0.80;
  gid 900 methanotrophic-only, `ammonia_oxidation` still rejected.
