# Manuscript methods notes (running)

> **STATUS: Running notes, not authoritative.** This file is a
> catch-basin for items that need to land in the eventual
> manuscript's methods / limitations section. It is NOT a draft
> of the methods section itself and MUST NOT be cited as one.
> Entries are reminders of decisions, caveats, and
> reference-circularity issues that arose during the codebase
> work and would otherwise be lost between the per-file design /
> verification documents and the eventual D2 manuscript-outline
> work (see `docs/phase6/blind_test_cohort_design.md` §2).
>
> When the manuscript methods section is drafted, each entry
> here should be either incorporated or explicitly closed.
> Until then: **append, do not overwrite.**

---

## Entries

### 1. Domain of applicability (Bacteria + Archaea; eukaryotes excluded)

The CultureForge platform's domain of applicability is prokaryotes
— Bacteria and Archaea only. Eukaryotic organisms (fungi,
protists, microalgae, eukaryotic phototrophs, metazoan MAGs of
any kind) are out of scope for both the platform predictions and
the blind-test cohort.

**Where this is already written:**

- `docs/CLAUDE.md` (Project Vision, opening sentence): *"AI
  platform that predicts cultivation media for novel uncultured
  bacteria and archaea …"*
- `docs/phase6/blind_test_cohort_design.md` §15: locked
  discovery-methodology clause pinning the Option 1 broad query
  to NCBI taxids Bacteria (`2`) and Archaea (`2157`); eukaryotic
  MAGs explicitly named as out of scope.
- `docs/phase6/blind_test_cohort_design.md` §13.2: the
  environmental-scope reasoning cites the CLAUDE.md vision
  sentence as one of four supporting signals for the
  environmental-scope decision.
- `docs/phase6/blind_test_cohort_design.md` §7: category list
  (methanogenesis, anammox, ANME, comammox, cable bacteria,
  syntrophy, sulfate reduction, hyperthermophile, …) is entirely
  prokaryotic by construction.

**Manuscript action.** The methods section should state the
domain-of-applicability claim directly (Bacteria + Archaea,
eukaryotes out) alongside the discovery- and scope-filter
operationalization. The 2026-05-31 batch-1 funnel is a useful
empirical anchor: 150,024 raw hits = 141,783 Bacteria + 8,241
Archaea + 0 eukaryotes, by construction.

### 2. amoA_archaeal reference-circularity on AOA validation (gids 1102, 1106, 1114)

The A1 ammonia-oxidation work added an `amoA_archaeal` diagnostic
marker and verified AOA detection across the dev cohort. Three
positive hits in that verification are NOT independent — they are
self-references against the marker training set:

- **gid 1102** hits at 100% identity because its own UniProt AmoA
  (`A0A060HNG6`) is in
  `data/diagnostic_markers/amoA_archaeal_refs.fasta`.
- **gid 1106** hits at 100% identity because its own UniProt AmoA
  (`A0A654M1Z2`) is in the same reference set.
- **gid 1114** (comammox) carries the same reference-circularity
  issue with `A0A7D4WXT9`.

By contrast, gid 1049 hits at 95.8% (its UniProt ref `D9J260` is
a fragment), and a genuinely novel AOA would rely on the
genus-outgroup references (`D9J261`, `A0A5B8ZQK3`, `F4N9Y5`) at
the 50/70 threshold — which is where the marker's actual
generalization claim lives.

The caveat is recorded inline at
`docs/phase5_0/a1_verification.md:70-76`.

**Manuscript action.** The A1 writeup in the methods section
should disclose the reference-circularity for gids 1102, 1106,
1114 as a limitation of the AOA validation. The marker's
generalization claim rests on the genus-outgroup refs and the
50/70 threshold, not on the 100% self-hits, and the manuscript
should frame the validation accordingly.

---

## How to add to this file

Append entries at the end under a new `### N. …` header. Each
entry should:

- State the item in 1–3 sentences.
- Cite the authoritative source(s) by repo path (and line range
  where useful).
- End with a **Manuscript action:** line stating what needs to
  happen in the eventual write-up.

Do not edit prior entries after they land; if an entry needs
correction or update, append a follow-up entry that references
the earlier one by number.
