# C1 Inspection Report — Refresh published-media linkages for gids 9, 17, 26, 30

**Date:** 2026-05-16 · **Repo HEAD:** 2b637ae · **Mode:** read-only (SELECT-only DB access, no writes)
**Status:** COMPLETE — but the task's framing is substantially stale (details below).

## Plain-language summary (read this first)

The task asked me to plan adding "published media" links for four organisms so a
quality score (called V12) goes up. When I looked at the actual database, the
picture is very different from what the task description assumed:

- **Two of the four (gid 9 Thermus aquaticus, gid 17 Sulfurimonas denitrificans)
  ALREADY HAVE these links.** They were added at some earlier point, using the
  exact BacDive reference IDs the task told me to "add" (16714 and 6113). I
  verified both IDs point to the correct species. So for these two, **there is
  nothing to add** — their low V12 scores are caused by something else
  (a recipe-versus-media comparison issue), which is outside what C1 can fix.
- **One (gid 26 Picrophilus torridus) genuinely has no links** and is a
  straightforward fix — but the specific medium the task named ("DSMZ 1146") is
  the **wrong medium**; the correct Picrophilus media are already sitting in the
  database under different IDs.
- **One (gid 30 Scalindua japonica) genuinely has no links** and is **blocked**:
  the medium it needs comes from scientific papers, not a media catalog, and the
  organism has never been grown in pure culture, so the normal linking mechanism
  does not apply. This is a STOP-and-report item needing a human decision.

So C1 is not "refresh four linkages." It is really: 2 already done, 1 quick win
(with a corrected medium), 1 blocked pending a decision.

---

## 1. Schema verification

The handoff's schema hint ("table is `media` with columns source_id, name,
source; `published_media` does not exist") is **partly wrong and misleading**:

- `published_media` — confirmed **does not exist**. (This part of the hint was right.)
- The actual organism→media link table is **`organism_to_published_media`**, not
  `media`. Schema:
  ```
  organism_to_published_media(
    cultureforge_genome_id INTEGER,
    medium_id              TEXT,     -- joins to media.source_id, NOT media.id
    relationship           TEXT,     -- 'direct' (same species) | 'functional_neighbor'
    similarity_score       REAL,
    bacdive_id             INTEGER)  -- the BacDive strain that supplied the link
    PRIMARY KEY (cultureforge_genome_id, medium_id, relationship)
  ```
- `media` is the **media catalog**: `id` (int PK), `source_id` (TEXT, UNIQUE —
  e.g. `'878'`, `'J276'`), `name`, `source` (DSMZ/JCM/…), plus pH/description.
  **Critical join detail:** `organism_to_published_media.medium_id` is TEXT and
  matches `media.source_id` — *not* `media.id`. (E.g. link `medium_id='878'`
  resolves to `media.id=2359`, "THERMUS 162 MEDIUM".)
- Upstream of direct links: **`organism_to_bacdive`**
  `(cultureforge_genome_id, bacdive_id, match_method, match_confidence)`. A
  "direct" published-media link is only created when a genome has a BacDive
  match here. **No `organism_to_bacdive` row ⇒ no direct media link.**
- `bacdive_cache(bacdive_id, species_name, strain_designation, domain,
  dsm_number, ncbi_taxid)` — used here to verify the BacDive IDs.
- Legacy `organism_media(organism_id, media_id, growth)` is a *different,
  older* table keyed on the legacy `organisms` namespace; **not** used by V12.

## 2. gid namespace — confirmed (the plan's correction holds)

`genomes` has 168 rows (ids 7–1137). For gids 9/17/26/30, `genomes.organism_id`
is NULL (these are re-downloaded genomes, not linked to the legacy `organisms`
table). Identity is established by `genomes.accession` + `genomes.notes`, which
explicitly record the 2026-05-05 audit correction:

| gid | accession | genomes.notes (abridged) | True species |
|----:|-----------|--------------------------|--------------|
| 9 | GCF_001280255.1 | "was T. thermophilus HB8 from start … re-downloaded" | **Thermus aquaticus** |
| 17 | GCF_000012965.1 | "was Sulfurovum NBC37-1 from start … re-downloaded" | **Sulfurimonas denitrificans** |
| 26 | GCF_000008265.1 | "was Brevibacillus brevis NBRC 100599 … " biomass=Archaea | **Picrophilus torridus** |
| 30 | GCF_002443295.1 | "S. profunda unavailable; substituting **Scalindua japonica husup-a2** MAG; originally Salmonella" | **Ca. Scalindua japonica** |

(The legacy `organisms` table ids 9/17/26/30 are Acetobacter/Acidiphilium — a
different namespace, irrelevant to V12. The plan's namespace correction is
confirmed correct.)

## 3. Per-gid current state

### gid 9 — Thermus aquaticus — **ALREADY DONE**
- `organism_to_bacdive`: bacdive **16714**, `species_name_exact`, confidence 0.95.
- `organism_to_published_media`: **3 direct links**, all similarity 1.0, all via
  bacdive 16714:
  | medium_id | resolves to (media.name / source) |
  |-----------|-----------------------------------|
  | `86` | CASTENHOLZ MEDIUM (DSMZ) |
  | `878` | THERMUS 162 MEDIUM (DSMZ) |
  | `J276` | CASTENHOLZ MEDIUM (JCM) |
- **BacDive 16714 verified = `Thermus aquaticus` strain YT-1, DSM 625** (domain
  Bacteria). This directly answers the task's verification ask: it is **T.
  aquaticus, NOT T. thermophilus**. Concern resolved.
- Castenholz and Thermus 162 are the canonical Thermus media — the linkage is
  correct and complete. The reported low V12 (~33%) is therefore **not** a
  missing-linkage problem; it is a downstream recipe-vs-media comparison issue,
  outside C1's scope (flagged for the morning queue / a separate item).

### gid 17 — Sulfurimonas denitrificans — **ALREADY DONE**
- `organism_to_bacdive`: bacdive **6113**, `species_name_exact`, 0.95.
- `organism_to_published_media`: **1 direct link**, similarity 1.0:
  `medium_id='113'` → "THIOBACILLUS DENITRIFICANS MEDIUM" (DSMZ).
- **BacDive 6113 verified = `Sulfurimonas denitrificans`, DSM 1251.** This is
  exactly the BacDive ID the task said to "link via" — already present.
- Caveat to note (not a C1 action): the single linked medium is the *Thiobacillus
  denitrificans* medium. DSMZ commonly shares one medium across chemolithotrophic
  denitrifiers, so this is plausibly the BacDive-recommended medium for S.
  denitrificans DSM 1251 — but only one medium is linked, which partly explains
  the low V12 (~10%). Adding more is not a linkage *refresh* (the BacDive link is
  correct); it would be a curation expansion, a separate decision.

### gid 26 — Picrophilus torridus — **GENUINE GAP, quick win, task medium is wrong**
- `organism_to_bacdive`: **no row.** `organism_to_published_media`: **no row.**
  This is why V12 is 0% (no direct media, falls to functional-neighbor branch).
- The task says to add "DSMZ 1146 Picrophilus medium + MR-A medium." **DSMZ 1146
  is NOT a Picrophilus medium** — `media.source_id='1146'` is "VENENIVIBRIO
  STAGNISPUMANTIS MEDIUM" (DSMZ). No medium named "MR-A" exists in the catalog.
  This part of the handoff is stale/incorrect.
- The correct, usable Picrophilus media **already exist in the catalog** (JCM,
  not DSMZ):
  | media.id | source_id | name |
  |---------:|-----------|------|
  | 1986 | `J233` | PICROPHILUS MEDIUM (JCM) |
  | 3248 | `J1267` | MODIFIED PICROPHILUS MEDIUM (JCM) |
- So no new media row is needed — only (a) a BacDive match for Picrophilus
  torridus and (b) direct links to `J233` / `J1267`.

### gid 30 — Ca. Scalindua japonica — **GENUINE GAP, BLOCKED (STOP-and-report)**
- `organism_to_bacdive`: **no row.** `organism_to_published_media`: **no row.**
- No anammox/Scalindua medium exists in the catalog (`media` search for ANAMMOX/
  SCALINDUA/ANAEROBIC AMMONIUM → nothing relevant; `J451` "ANOXIC MEDIUM FOR
  STRAIN AcBE2-1" is unrelated). MediaDive cache likewise has none.
- Scalindua is **uncultured** (a MAG; no axenic strain ⇒ no BacDive strain ⇒ no
  DSM number). The normal direct-link mechanism (genome→BacDive→catalog medium)
  **cannot apply**. The recommended recipe (van der Star 2007 / Awata 2013) is a
  **paper-derived enrichment medium**, not a catalog entry.
- **STOP-and-report:** linking gid 30 requires a human decision — see §5.

## 4. Proposed linkage plan (dry — nothing executed)

| gid | action | needs new `media` row? | proposed write (for a future, approved step) |
|----:|--------|------------------------|----------------------------------------------|
| 9 | **none — already correct** | no | — (verify-only; concern resolved: BacDive 16714 = T. aquaticus) |
| 17 | **none — link correct**; optional curation expansion is a separate decision | no | — |
| 26 | add bacdive match + 2 direct links | **no** (J233/J1267 already in catalog) | 1× `organism_to_bacdive(26, <Picrophilus torridus bacdive_id>, 'manual'|'species_name_exact', ~0.95)`; then 2× `organism_to_published_media(26, 'J233', 'direct', 1.0, <bid>)` and `(26, 'J1267', 'direct', 1.0, <bid>)` |
| 30 | **blocked** — needs a curated custom medium + a linkage convention decision | **yes** (paper-derived, must be created first) | deferred — see §5 |

Notes for whoever executes the approved step later:
- `medium_id` in the INSERT is the **`media.source_id`** string (`'J233'`), not
  the integer `media.id`.
- For gid 26, the one open lookup is Picrophilus torridus' BacDive ID. The
  BacDive REST API (`https://api.bacdive.dsmz.de`) and local cache
  (`data/bacdive/strains/`) are available; `bacdive_client.py` has
  `search_strain_by_name` (cache) and `fetch_strains_by_taxon` (live). I did
  **not** perform this lookup — it is a write-adjacent curation step the task
  scoped to "verify the source exists," and cache-first lookup for the specific
  ID is best done in the approved execution step, not this read-only pass.

## 5. STOP-and-report — gid 30 (Scalindua) linkage

Per task Rule 7 (success criteria depend on info not in the codebase / needs an
architectural decision not pre-made). The morning decisions:

1. **Where does the medium come from?** It is not in any catalog. Someone must
   curate the van der Star 2007 / Awata 2013 anammox enrichment recipe into a
   new `media` row (and ideally `media_compounds`). That is external curation,
   beyond SELECT/REST verification.
2. **What `source` / `source_id` convention for a paper-derived medium?** The
   catalog assumes DSMZ/JCM/MediaDive IDs. A custom entry needs a chosen
   `source` value (e.g. `'LITERATURE'`) and a synthetic `source_id`
   (e.g. `'LIT_anammox_vanderStar2007'`) — a schema-convention decision.
3. **What `relationship`?** `organism_to_published_media` only allows `direct`
   (same-species, BacDive-backed) or `functional_neighbor`. Scalindua has no
   BacDive strain, so `direct` (which the schema comment ties to a BacDive
   match) is a semantic stretch. Either relax that convention or introduce a new
   relationship value — a decision, not an inspection finding.

Do **not** improvise this. It is recorded here and rolled into the overnight
summary's morning-decision queue.

## 6. V12 verification approach (how we'd confirm a future fix worked)

V12 runner: `data/validation/run_phase2d_validation.py`. It does **not** need to
be modified; reading it (not running it — it is slow and writes
`docs/recipe_examples/phase2d_validation_summary.tsv`) shows the mechanism:

- `ORGANISMS` list (lines ~26–53) maps gid 9→`Thermus_aquaticus`,
  17→`Sulfurimonas_denitrificans`, 26→`Picrophilus_torridus`,
  30→`Scalindua_profunda` (label still says profunda; actual genome is the
  japonica husup-a2 substitute — a cosmetic label-vs-genome mismatch worth a
  one-line fix someday, not C1).
- Per gid (lines ~56–124): builds the recipe via `compose_recipe(gid, conn)`,
  then queries `organism_to_published_media … relationship='direct'`. If direct
  media exist → `compare_recipes(..., relationship='direct')` and
  `agreement = report.overall_agreement`. If none → falls back to
  `find_functional_neighbors` and compares against neighbor media instead.
  `agreement_pct = int(agreement*100)`.
- **Implication per gid:**
  - gid 9, 17: already on the **direct** branch (links exist). Their low V12 is
    a `compare_recipes` agreement issue (recipe content vs. the correct media),
    **not** something adding/refreshing links will move. Verifying a *recipe*
    fix would mean re-running V12 and watching their `agreement_pct`.
  - gid 26: currently **functional_neighbor** branch (0% ⇒ likely no usable
    neighbors). After adding the J233/J1267 direct links it would switch to the
    **direct** branch; re-run V12 and confirm `agreement_pct` for gid 26 rises
    from 0 and `relationship` flips to `direct`.
  - gid 30: currently functional_neighbor (~42%). Only changes if a curated
    anammox medium is created and linked (blocked, §5).
- **Verification recipe (future, post-approval):** snapshot
  `phase2d_validation_summary.tsv`, apply the approved INSERTs, re-run the
  runner, diff the four rows' `relationship` + `agreement_pct`. Expected
  movement is **only for gid 26** under C1 alone; 9/17 need a separate
  recipe-quality investigation; 30 is blocked.

## 7. Implementation effort estimate (for the morning)

| gid | effort | nature |
|----:|--------|--------|
| 9 | **none** | already correct; verification concern (16714 = T. aquaticus) resolved here |
| 17 | **none** for the link itself | correct as-is; any media expansion = separate curation decision, not a refresh |
| 26 | **~15 min** | 1 BacDive lookup (cache-first) + 3 INSERTs; media already in catalog. Lowest-risk real win. |
| 30 | **blocked / hours** | needs literature media curation + 3 schema-convention decisions (§5) before any INSERT |

**Bottom line for C1:** the headline assumption ("four stale linkages to
refresh") does not survive contact with the database. The honest state is
**2 already-done, 1 quick win (with a corrected target medium), 1 blocked**. The
two low V12 scores the task most wanted lifted (Thermus 33%, Sulfurimonas 10%)
are **not** linkage problems and cannot be fixed by C1 — they need a separate
recipe-quality look. Only gid 26 yields a V12 improvement from C1 work alone.
