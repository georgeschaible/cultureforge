# Overnight Inspection Summary

*Run date: 2026-05-16 · Repo HEAD: 2b637ae · Mode: read-only (items 1-3) + one doc write (item 4) · No DB writes, no git ops.*

## Top line

Four items + this summary. **All four COMPLETE** as inspections — but two
contain **STOP-and-report** decisions and one is largely **ALREADY-DONE**:

| Item | Status | One-line outcome |
|------|--------|------------------|
| C1 — media linkage refresh | COMPLETE · 2/4 ALREADY-DONE · 1 STOP-AND-REPORT | Not "4 stale linkages"; really 2 done, 1 quick win, 1 blocked. |
| A3 — microaerophile O2 | COMPLETE · STOP-AND-REPORT | One coherent fix for 8 gids; 2 gids (1068/1072) are a different bug. |
| B1 — heliobacterial pshA | COMPLETE · ready for implementation | Clean scope gap; verified real `pshA` references; A1-shape fix. |
| D1 — limitations.md | COMPLETE | ~2,200-word manuscript-reviewer doc written. |

No item ran over its 90-minute box; none halted the session.

## Per-item summaries

**C1 — `c1_inspection_report.md`.** The premise ("refresh four stale media
linkages to lift V12") does not survive the database. gid 9 (*Thermus
aquaticus*) and gid 17 (*Sulfurimonas denitrificans*) **already have correct
BacDive-direct linkages** via the exact IDs the task said to add (16714 / 6113,
both verified to the right species) — their low V12 is a recipe-content issue,
not a linkage one, and is out of C1's scope. gid 26 (*Picrophilus torridus*) is
a genuine ~15-min win, but the task's "DSMZ 1146" medium is wrong (that ID is a
*Venenivibrio* medium); the correct Picrophilus media (JCM J233 / J1267) are
already in the catalog. gid 30 (*Scalindua*) is **blocked**: uncultured, no
BacDive strain, needs a literature-curated medium plus a schema-convention
decision. The handoff's schema hint was also wrong (real table:
`organism_to_published_media`).

**A3 — `a3_inspection_report.md`.** All 10 audit-P5 microaerophiles verified at
HEAD (audit not stale here; spot-checked gids 15/1068/1072/1083 directly). Good
news: the detection signal already exists — `detect_aerobic_respiration` already
parses high-affinity `cbb3` vs low-affinity `bo3` oxidase booleans
(`capability_detectors.py:1110-1131`) and then discards the distinction; no new
marker DB is needed for detection. Recommended architecture is an **O2-modifier
flag on existing aerobic modes**, *not* a new mode (anammox/A4 precedent does
not transfer — microaerophily is orthogonal to energy metabolism). STOP-and-
report: P5 bundles two problems — 8 gids need only the O2 modifier; gids 1068
(*Gallionella*) and 1072 (*Mariprofundus*) are *also* misclassified Fe(II)-
oxidizing autotrophs (gid 1072 gets a glucose recipe) and need a separate fix.

**B1 — `b1_inspection_report.md`.** gid 1051 (*Heliomicrobium modesticaldum*)
confirmed misclassified `anaerobic_respiratory` at HEAD (phototrophy scores
0.00). Cause confirmed genuine: heliobacterial homodimeric Type I RC (BChl *g*,
`pshA`) is absent from all three reference sets — already self-documented in the
codebase as limitation **B.5** (= audit S2 = task B1). Verified, against live
UniProt with A1-style skepticism, that real correctly-annotated `pshA`
sequences exist (B0TBM3 = target's own genome → circularity risk; non-circular
outgroups Q1MX23/Q48238/Q9ZGF3/A0A5Q2N361 available). Recommendation mirrors A1:
split `pshA` marker + `diagnostic_marker_override` + `phototrophic_heliobacterial`
composer mode; cyanobacterial sentinels gids 1017/1018/1025/1028/1092.
Implementation = a separate marker-writing task (out of read-only scope).

**D1 — `limitations.md`.** Manuscript-reviewer limitations doc synthesized from
the audit, V12, A1/A4 errata, this run's findings, backlog and related-work.
Seven sections; every limitation tagged [REAL BUG] / [SCOPE GAP] / [DATA-INFRA];
includes an audit-vs-HEAD reconciliation table written to current HEAD state.

## Cross-cutting findings

- **Audit-staleness is now a confirmed class problem (third occurrence).** P3
  (→A4) and P4 (→A1) were stale; this run's *task framing itself* was stale —
  the referenced Tier-A/B/C/D handoff does not exist (canonical doc uses
  P1–P5/S1–S12), the asserted media schema was wrong, and the gid numbering
  silently collides with a legacy `organisms` table. The plan's pre-emptive
  corrections all held. Recommend commissioning the queued **Phase 6.5
  audit-refresh**.
- **The two-id-space hazard is real and recurring.** `genomes.id` (genome
  space, used by `compose_recipe`/V12) vs. legacy `organisms.id` produce
  *different organisms for the same number*. Every item had to defend against
  it. Worth a one-time codebase note / guard.
- **Reference-set circularity recurs.** A1 (amoA) and now B1 (pshA) both have
  the target's own genome as a candidate reference. Any marker-addition task
  must standardize "non-circular outgroup + sentinel" reference design.
- **"Already done / mis-scoped" pattern.** Like A4's P3, C1 (2/4 done) and A3
  (mis-scoped as one task) show the audit's recommendation list is partly
  obsolete or imprecise — reinforcing the audit-refresh need.
- **An architectural distinction emerged:** new-mode (anammox/A4, heliobacterial/
  B1 — distinct energy metabolism) vs. modifier-flag (microaerophile/A3 —
  property orthogonal to metabolism). Future "add a capability" work should
  first classify which shape applies.

## Morning decision queue

1. **C1 gid 30 (Scalindua):** approve curating a literature anammox medium (van
   der Star 2007 / Awata 2013) into a new `media` row, and decide the
   convention for paper-derived media (`source`/`source_id` values) and the
   `relationship` value for an uncultured organism with no BacDive strain.
2. **C1 gid 26 (Picrophilus):** approve the quick win — BacDive lookup + 3
   INSERTs against existing catalog media J233/J1267 (not "DSMZ 1146").
3. **C1 gids 9/17:** accept that low V12 here is a recipe-quality issue, not
   linkage — route to a separate recipe investigation, not C1.
4. **A3 scope:** confirm A3 = the 8-gid O2-modifier fix only; spin gids
   1068/1072 Fe(II)-oxidizer misclassification into its own item.
5. **A3 architecture:** approve "modifier flag on aerobic modes" (not a new
   mode) and a blanket reduced-O2 default (~3-5%) before per-organism tuning.
6. **B1:** approve a marker-writing task to add the split `pshA` marker +
   `phototrophic_heliobacterial` mode, using the non-circular reference design
   and the named cyanobacterial sentinels.
7. **Audit-refresh (Phase 6.5):** approve commissioning it — third staleness
   occurrence makes this a recurring cost, not a one-off.
8. **Proxy-pattern review:** decide whether the remaining benign species-name
   heuristic at `compose_recipe.py:712-716` should also be retired.

## Surprises and corrections (further errata uncovered)

- **C1's premise was ~50% obsolete:** 2 of 4 target linkages already exist and
  are correct. New erratum: the audit's "DSMZ 1146 Picrophilus medium" is a
  wrong reference (DSMZ 1146 = *Venenivibrio stagnispumantis* medium).
- **A3 detection is further along than assumed:** the cbb3/bo3 high/low-affinity
  signal is already computed (and discarded), and a `terminal_oxidases` marker
  set already exists — lowering the A3 effort estimate.
- **A3 mis-scoping erratum:** audit P5's 10-gid list silently mixes pure
  microaerophiles with two Fe(II)-oxidizer misclassifications (gids 1068/1072).
- **B1 confirmed, not stale:** the gap is already self-documented in code as
  B.5; audit S2 named no accessions (correctly — so no hallucination there,
  unlike P4), and the candidate accessions verified clean.
- **Namespace trap:** legacy `organisms.id` 9/17/26/30 = Acetobacter/
  Acidiphilium — a different organism set than the genome-space targets; a
  naive query would have produced entirely wrong conclusions.

*End of overnight run. No commits. No pushes. No DB writes. Reports:
`c1_inspection_report.md`, `a3_inspection_report.md`, `b1_inspection_report.md`,
`limitations.md`, and this summary — all under `docs/phase5_0/`.*
