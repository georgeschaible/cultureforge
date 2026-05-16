# A4 Verification — Evidence-Based Anammox Composer Guard

Date: 2026-05-15 · CultureForge git HEAD 4be3d23 + A4 working changes
(uncommitted). DB backup: `data/cultureforge.db.pre_a4_20260515_2207`.

## Change verified

`compose_recipe.py` E.1 guard: replaced the unconditional species-name
predicate (`"scalindua" in context.species`) with an evidence-based predicate
— escalate only when the anammox capability/mode is asserted AND both `hzsA`
and `hdh` lack a `positive_call=1` row in `genome_diagnostic_markers`. `conn`
is threaded into `_apply_limitations_flags` (sole call site, line 222). Marker
presence uses the codebase `positive_call` convention, mirroring the existing
`_compose_anme_recipe` pattern (compose_recipe.py:471–482). No other flag rule
changed.

## Verification table

| gid | organism | expected | anammox conf | primary mode | recipe composes | escalation reason | verdict |
|----:|----------|----------|-------------:|--------------|:---------------:|-------------------|:-------:|
| 30 | *Ca.* Scalindua japonica husup-a2 | flip → compose | 0.95 | anammox | **YES** | none | **FLIP ✓** |
| 1105 | *Ca.* Scalindua brodae | flip → compose | 0.95 | anammox | **YES** | none | **FLIP ✓** |
| 1001 | *Ca.* Brocadia sinica JPN1 | hold PASS | 0.86 | anammox | YES | none | **HOLD ✓** |
| 1002 | *Ca.* Brocadia fulgida | hold PASS | 0.86 | anammox | YES | none | **HOLD ✓** |
| 1090 | *Ca.* Jettenia caeni | hold PASS | 0.86 | anammox | YES | none | **HOLD ✓** |
| 18 | *Nitrosomonas europaea* (AOB sentinel) | unchanged, no anammox | — (not detected) | lithotrophic_aerobic (ammonia oxidation) | YES | none | **HOLD ✓** |
| 8 | *Methanococcus jannaschii* (methanogen sentinel) | unchanged, no anammox | — (not detected) | methanogenic | YES | none | **HOLD ✓** |

Overall-confidence detail: gid 30 / 1105 → 0.85 (high); 1001 / 1002 / 1090 →
0.80 (high); gid 18 → 0.71; gid 8 → 0.73. Pre-A4 the inspection report
recorded gid 30 / 1105 as ESCALATED at overall conf 0.45 with the false
"Scalindua MAG lacks hzsA/hdh" reason — that reason no longer appears.

## Underlying marker evidence (positive_call = 1)

| gid | hzsA rows / max pident / max bits | hdh rows / max pident / max bits | anammox asserted | guard fires |
|----:|-----------------------------------|----------------------------------|:----------------:|:-----------:|
| 30 | 5 / 63.9% / 1074 | 16 / 77.2% / 967 | yes | no (markers present) |
| 1105 | 5 / 64.4% / 1068 | 16 / 78.8% / 987 | yes | no (markers present) |
| 1001 | 10 / 100% / 1660 | 20 / 88.3% / 1090 | yes | no (markers present) |
| 18 | 0 | 0 | **no** | no (gate false — not anammox) |
| 8 | 0 | 0 | **no** | no (gate false — not anammox) |

The two sentinels (18, 8) confirm the critical safety property: the predicate
is gated on the anammox capability/mode being asserted, so hzsA/hdh-negative
non-anammox organisms — which is *every* non-anammox organism — never reach
the escalation branch. `_apply_limitations_flags` runs for all genomes; the
`anammox_asserted` gate prevents a universal false-escalation.

## Safety net (preserved)

The defensive intent is preserved honestly: a genome where the anammox
capability/mode IS asserted but both `hzsA` and `hdh` have zero `positive_call`
rows (a genuinely incomplete anammox MAG — the original pre-2026-05-05 gid-30
state) still escalates, now with an honest reason ("Anammox capability
asserted but diagnostic markers (hzsA and hdh) absent or below threshold —
likely incomplete MAG"). This branch is verified by code logic and by the
gid-30/1105 vs gid-18/8 contrast above; a live synthetic hzsA/hdh-negative
"scalindua"-named genome was deliberately NOT fabricated because per A4
constraints no DB rows may be written.

## Fail-loud checklist

- gid 30 / 1105 still escalated? **NO** — both compose. ✓
- Any anammox-baseline organism (1001/1002/1090) lost recipe or dropped
  anammox confidence? **NO** — all hold at conf 0.86 / overall 0.80. ✓
- Any non-anammox sentinel (18, 8) gained anammox detection or changed
  behavior? **NO** — modes and recipes unchanged. ✓
- grep `scalindua` turned up logic-bearing code beyond the guard? **NO** —
  only the legitimate seawater-NaCl note in `_compose_anammox_recipe`
  (compose_recipe.py:712–716, out of scope per constraints) and a docstring
  mention (compose_recipe.py:1625). All other hits are documentation /
  organism names. ✓

No fail-loud condition triggered.
