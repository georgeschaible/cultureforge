# A1 Step 2 — Verification Report (archaeal AOA `amoA_archaeal` marker)

Date: 2026-05-15 · Phase 6 A1 implementation · targeted verification subset
(13 gids, not the full 168). DB backup: `data/cultureforge.db.pre_a1_20260515_1139`.

## What changed

- New marker `amoA_archaeal` (6 verified UniProt archaeal AmoA refs:
  D9J260, A0A060HNG6, A0A654M1Z2, D9J261, A0A5B8ZQK3, F4N9Y5) + BLAST DB
  `blastdb_amoA_archaeal` — **split** from bacterial `amoA`, not additive.
- `run_marker_blast.py`: `MARKER_THRESHOLDS["amoA_archaeal"] =
  {evalue 1e-20, pident 50, qcov 70}`; corrected the misleading amoA comment.
- `data/pathway_definitions.json` → `ammonia_oxidation`: added a single-marker
  `diagnostic_marker_override` (`marker: amoA_archaeal`, min_pident 50,
  min_qcov 70, min_evalue 1e-30, override_confidence 0.70) mirroring
  `aerobic_methanotrophy`'s `pmoA` block exactly; updated `limitation_summary`
  (A.2 retained, bacterial-side).
- `compose_recipe.py`: `amoA_archaeal` added to
  `_MODE_DIAGNOSTIC_MARKERS["lithotrophic_aerobic"]`.
- No changes to bacterial amoA refs/threshold, pathway-step weights, or
  `capability_detectors.py`.

## Control-flow basis (verified, not assumed)

`capability_detectors.py`: `detected = confidence>=0.50 AND pathway_score>=0.40`
is computed unconditionally at **L503**; the `diagnostic_marker_override`
block (**L519–550**) is entered only when **L523** `not detected`. Bacterial
AOB/comammox pass via pathway-step scoring (≥0.40 pathway_score) and **never
enter** the override branch — so the override's marker choice cannot affect
them. The override is strictly additive for AOA (pathway_score 0.00).

## Verification table

| gid | organism | expected | amoA hit | amoA_archaeal hit | amm_ox before | amm_ox after | Δ | methanotrophy before/after | mode assigned | recipe composes | verdict |
|----:|----------|----------|----------|-------------------|--------------:|-------------:|---:|----------------------------|---------------|:---:|---------|
| 1049 | *Nitrosopumilus maritimus* SCM1 | flip→PASS | none | 95.8% bs=410 qc=98 ✓ | 0.300 (rej) | **0.700 (det)** | +0.400 | 0.20 / 0.20 | lithotrophic_aerobic | yes (ammonia oxidation) | **PASS ✓** |
| 1102 | *Nitrososphaera viennensis* EN76 | flip→PASS | none | 100.0% bs=430 qc=99 ✓ | 0.300 (rej) | **0.700 (det)** | +0.400 | 0.20 / 0.20 | lithotrophic_aerobic | yes (ammonia oxidation) | **PASS ✓** |
| 1106 | *Ca.* Nitrosocosmicus oleophilus MY3 | flip→PASS | none | 100.0% bs=431 qc=99 ✓ | 0.300 (rej) | **0.700 (det)** | +0.400 | 0.20 / 0.20 | lithotrophic_aerobic | yes (ammonia oxidation) | **PASS ✓** |
| 18 | *Nitrosomonas europaea* | hold-PASS | 85.3% bs=491 ✓ | none | 0.916 (det) | 0.916 (det) | 0.000 | 0.35 / 0.35 | lithotrophic_aerobic | yes | **HELD ✓** |
| 1039 | *Nitrosomonas eutropha* C91 | hold-PASS | 84.9% bs=493 ✓ | none | 0.816 (det) | 0.816 (det) | 0.000 | 0.30 / 0.30 | lithotrophic_aerobic | yes | **HELD ✓** |
| 1114 | *Ca.* Nitrospira inopinata (comammox) | hold-PASS | 60.0% bs=355 ✓ | none | 0.916 (det) | 0.916 (det) | 0.000 | 0.25 / 0.25 | lithotrophic_aerobic (NOB) | yes | **HELD ✓** |
| 900 | *Methylococcus capsulatus* Bath (sentinel) | stay-rejected (amm_ox); methanotrophy held | 50.0% bs=267 | none | 0.326 (rej) | 0.326 (rej) | 0.000 | **0.803 / 0.803** | methanotrophic | yes | **CLEAN ✓** |
| 903 | *Methanosarcina acetivorans* C2A (methanogen sentinel) | stay-rejected | none | none | 0.000 | 0.000 | 0.000 | 0.20 / 0.20 | methanogenic | yes | **CLEAN ✓** |
| 1047 | *Caldivirga maquilingensis* (neg ctrl) | stay-rejected | none | none | 0.300 | 0.300 | 0.000 | 0.20 / 0.20 | (none) | escalates | **CLEAN ✓** |
| 1060 | *Halorubrum lacusprofundi* (neg ctrl) | stay-rejected | none | none | 0.300 | 0.300 | 0.000 | 0.20 / 0.20 | anaerobic_respiratory | yes | **CLEAN ✓** |
| 1026 | *Methanococcus maripaludis* S2 (neg ctrl) | stay-rejected | none | none | 0.300 | 0.300 | 0.000 | 0.20 / 0.20 | methanogenic | yes | **CLEAN ✓** |
| 1012 | *Pyrococcus furiosus* DSM 3638 (neg ctrl) | stay-rejected | none | none | 0.000 | 0.000 | 0.000 | 0.20 / 0.20 | anaerobic_respiratory | yes | **CLEAN ✓** |
| 1070 | *Ferroplasma acidarmanus* Fer1 (neg ctrl) | stay-rejected | none | none | 0.100 | 0.100 | 0.000 | 0.20 / 0.20 | (none) | escalates | **CLEAN ✓** |

(rej = rejected/not detected; det = detected. "recipe composes" = `compose_recipe`
not escalated. amm_ox = `ammonia_oxidation` capability confidence.)

## Fail-loud conditions — ALL CLEAR

| Condition | Result |
|---|---|
| Any AOA target `ammonia_oxidation` < 0.50 after | NO — all three = 0.700 |
| Any existing PASS (18, 1039, 1114) drops below 0.80 | NO — 0.916 / 0.816 / 0.916 unchanged |
| gid 900 methanotrophy drops OR amm_ox rises above rejection | NO — methanotrophy 0.803 unchanged; amm_ox 0.326 (still rejected, no amoA_archaeal hit) |
| Methanosarcina 903 gains `ammonia_oxidation` > 0.30 | NO — 0.000 unchanged |
| Any negative-control Archaeon gains `ammonia_oxidation` > 0.30 | NO — max = 0.300 (1047/1060/1026), none exceed 0.30; none gained an amoA_archaeal hit |

## Notes / observations

- AOA detection mechanism: `pathway_score` stays **0.00** (gapseq still blind
  to archaeal amo; AOA genuinely lack bacterial hao/cytochromes — as expected).
  Detection is carried entirely by the `diagnostic_marker_override` firing on
  the `amoA_archaeal` hit, flooring confidence at 0.70 (= override_confidence).
  Recipe routes to `lithotrophic_aerobic (ammonia oxidation)` and composes.
- 1102 / 1106 hit `amoA_archaeal` at 100% identity because their own UniProt
  AmoA (A0A060HNG6 / A0A654M1Z2) is in the reference set — the same
  reference-circularity caveat that already applies to comammox gid 1114
  (A0A7D4WXT9). 1049 hits at 95.8% (its ref D9J260 is a fragment); a genuinely
  novel AOA would rely on the genus-outgroup refs (D9J261, A0A5B8ZQK3, F4N9Y5)
  and the 50/70 threshold — robustness, not just clade coverage, was the
  curation goal.
- Cross-reactivity guard intact: zero `amoA_archaeal` hits on the methanotroph
  sentinel (900), the methanogen sentinel (903), or any of the 5 negative
  controls. Bacterial `amoA` hits for 18/900/1039/1114 are byte-identical to
  the pre-change values — the bacterial marker, threshold, and pathway scoring
  were not perturbed.
- Bacterial controls (18, 1039, 1114) confirmed to detect via pathway scoring
  (modes still corroborated by `amoA`); they did not touch the new override,
  consistent with the L503/L523 control-flow guarantee.
