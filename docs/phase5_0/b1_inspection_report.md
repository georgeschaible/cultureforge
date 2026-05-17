# B1 Inspection Report — Heliobacterial photosynthesis marker (pshA), gid 1051

**Date:** 2026-05-16 · **Repo HEAD:** 2b637ae · **Mode:** read-only (DB SELECT + `inspect` reads + code reads + live UniProt verification only; no writes)
**Status:** COMPLETE — real, well-founded gap (not stale); A1-shape recommendation below.

## Plain-language summary (read this first)

Heliobacteria (here: *Heliomicrobium modesticaldum*, gid 1051) are photosynthetic
bacteria, but they use a **unique kind of photosynthetic machinery** (a
homodimeric "Type I" reaction center built on bacteriochlorophyll *g*, encoded by
the gene *pshA*). The system's three photosynthesis detectors all look for
*other* kinds of reaction center (purple-bacterial, green-sulfur, cyanobacterial)
and none of them recognize the heliobacterial one. So gid 1051 — a textbook
phototroph — is currently misread as an "organohalide-respiring" anaerobe, which
is biologically wrong.

This is **not** a stale-audit artifact: I confirmed at HEAD that all
photosynthesis scores for gid 1051 are 0.00, and the gap is **already documented
in the codebase itself** as limitation "B.5". The fix is the same shape as the
A1 fix (archaeal amoA): add a new dedicated marker with carefully chosen
reference sequences and a small detector hook. I verified — against live UniProt,
with the same skepticism A1 used after it caught hallucinated accessions — that
real, correctly-annotated *pshA* sequences exist to build that marker.

## 1. Item mapping (three names, one gap)

- Task calls it **B1**.
- `docs/phase5_0/predictions_audit.md:1463` calls it **S2**: *"Heliobacterial
  photosynthesis marker — 1 FAIL (gid 1051 …). Add a `pshA` marker
  (heliobacterial reaction center) and a `phototrophic_heliobacterial` mode
  mapping."*
- The codebase already calls it **B.5**: `data/pathway_definitions.json`
  `anoxygenic_phototrophy_purple.known_limitations = ["B.5"]`,
  `limitation_summary = "Heliobacterial and Acidobacteria phototrophs use
  divergent reaction centers not covered by pufLM/pscA references (B.5)."`

So this is a **known, pre-documented framework scope gap**, not a discovery and
not stale. (Audit S2 is also flagged at L1493 as a candidate for the HMM-marker
backlog approach.)

## 2. gid 1051 current state at HEAD (verified, not from audit text)

- Namespace confirmed: `genomes.id=1051` = `GCF_000019165.1`, notes
  *"Heliomicrobium modesticaldum Ice1 [phototrophy]"*. (Correct genome space.)
- `cultureforge.py inspect 1051`:
  - **Primary mode: `anaerobic_respiratory (organohalide respiration)`**, conf
    0.65; alt `fermentative` 0.60.
  - Phototrophy explicitly **rejected**: *Green sulfur phototrophy 0.200
    (pathway 0.00)*, *Oxygenic phototrophy 0.200 (pathway 0.00)*. Anoxygenic
    purple does not even reach the rejected list (no pufLM signal at all).
- Audit `:634` / `:1342` / `:1512`: predicted `anaerobic_respiratory`, expected
  `phototrophic` → **FAIL**. A1/A4 changed nothing in phototrophy, so the audit
  claim is **still true at HEAD** (verified directly above — not trusted blindly).

The misclassification mechanism: with no reaction-center signal, the scorer
latches onto incidental reductive-dehalogenase / anaerobe hits and produces a
spurious organohalide-respiration call. Fixing detection removes the false call.

## 3. Existing phototrophy detection inventory

`data/pathway_definitions.json` has exactly three phototrophy pathways:

| pathway key | marker | reference set | covers |
|-------------|--------|---------------|--------|
| `anoxygenic_phototrophy_purple` | `pufLM` (override: pident≥35, qcov≥60, e≤1e-20 → conf 0.65) | `data/diagnostic_markers/pufLM_refs.fasta` (+blastdb) | purple bacteria, **Type II** RC |
| `anoxygenic_phototrophy_green_sulfur` | `pscA_fmoA` | `pscA_fmoA_refs.fasta` (+blastdb) | green sulfur bacteria, Type I RC + FMO |
| `oxygenic_phototrophy` | `psaA_psbA` | `psaA_psbA_refs.fasta` (+blastdb) | cyanobacteria, PSI+PSII |

- `pufLM_refs.fasta` references are purple bacteria only (Cereibacter,
  Rhodobacter, Blastochloris, Rhodospirillum) — **no heliobacteria**.
- `pscA_fmoA_refs.fasta` is green-sulfur (Chlorobaculum) — **no heliobacteria**.
- **No `pshA` marker, no `blastdb_pshA.*`, no heliobacterial sequence in any
  reference set** anywhere in `data/diagnostic_markers/`.
- The `anoxygenic_phototrophy_purple` entry itself documents this exclusion
  (B.5, §1).

## 4. Biology confirmation

Heliobacteria use a **homodimeric Type I reaction center with
bacteriochlorophyll *g*** (PshA core), phylogenetically and structurally
distinct from:
- purple-bacterial **Type II** RC (pufL/pufM) — different photosystem class
  entirely; pshA is **not** a pufLM homolog, so it cannot be detected by, and
  must **not** be added into, the pufLM reference set (doing so would corrupt
  the purple marker);
- green-sulfur **pscA** (also Type I, but a distinct family) and cyanobacterial
  **psaA** (Type I PSI) — homologous *class* but divergent enough that the
  existing pscA/psaA references do not recognize pshA (confirmed: gid 1051
  scores 0.00 on both).

This confirms the audit's stated cause is the **actual** reason gid 1051 fails —
not a side issue. It is a genuine reference-coverage gap.

## 5. Candidate pshA references — verified live against UniProt (A1 skepticism applied)

Audit S2 names **no** accessions (verified — it just says "add a pshA marker").
A1 previously caught the audit hallucinating accessions (P4's Q5JIJ3/Q57F89), so
every accession below was fetched and confirmed from live UniProt REST with gene,
protein name, organism, and length:

| accession | organism | protein name | len | use |
|-----------|----------|--------------|----:|-----|
| **B0TBM3** | *Heliobacterium modesticaldum* str. ATCC 51547 / **Ice1** | Reaction center core polypeptide PshA (HM1_0690) | 608 | **target's own genome — circularity risk (see note)** |
| Q1MX24 | *Heliomicrobium modesticaldum* (generic) | p800 reaction center core protein | 608 | species-level ref |
| Q1MX23 | *Heliomicrobium gestii* | p800 reaction center core protein | 608 | **genus outgroup** |
| Q48238 / Q9ZGF3 | *Heliobacterium mobile* (*Heliobacillus mobilis*) | Reaction center core polypeptide PshA | 609 | **genus outgroup** |
| A0A5Q2N361 | *Heliorestis convoluta* | P800 reaction center core protein | — | **family outgroup (alkaliphile)** |
| A0A505… (truncated in TSV) | *Heliophilum fasciatum* | Photosynthetic reaction center core protein | — | family outgroup — **confirm full accession before use** |

All are real, all annotated as the heliobacterial RC core (pshA); all TrEMMBL
(unreviewed) — expected for this under-curated lineage. Skepticism satisfied:
unlike P4's audit accessions, these check out.

**Reference-circularity caveat (mirror A1's gids 1102/1106/1114 finding):**
**B0TBM3 is the gid-1051 target's own genome (strain Ice1).** Including it as a
reference guarantees a ~100% self-hit and inflates apparent performance. The
robust reference set must lean on the **non-circular outgroups** (Q1MX23 gestii,
Q48238/Q9ZGF3 mobile, A0A5Q2N361 Heliorestis, Heliophilum) at a lower identity
threshold — exactly the design A1 used for `amoA_archaeal`. The verification
plan for any future implementation must record the self-hit caveat for gid 1051.

## 6. Architecture recommendation (mirrors A1; anammox/A4 for the mode)

**Recommend a SPLIT new marker + override + new composer mode — the A1 shape —
NOT folding pshA into an existing marker, and NOT a pathway-step rebuild.**

1. **New marker `pshA`** with its own `pshA_refs.fasta` + `blastdb_pshA.*`
   (parallels A1's *split* `amoA_archaeal`, kept separate from `amoA`). Do **not**
   add pshA into `pufLM_refs` — different photosystem class; it would create
   purple-bacterial false positives.
2. **`diagnostic_marker_override` on a heliobacterial phototrophy pathway**
   (new `anoxygenic_phototrophy_heliobacterial`, or a heliobacterial override on
   the anoxygenic-phototrophy family) — same mechanism as the existing `pufLM`
   override and A1's `amoA_archaeal` override. Justified because the homodimeric
   PshA RC is **pathognomonic** for heliobacterial phototrophy (a single strong
   marker is decisive), so an override (marker → confidence floor) is more
   appropriate than diluting it across weighted pathway steps — identical
   reasoning to A1.
3. **`phototrophic_heliobacterial` composer mode** registered the way A4
   registered `anammox`: add to `_MODE_COMPOSERS`, `_SPECIFIC_MODES_PRIORITY`,
   `_MARKER_REQUIRED_MODES`, and `_MODE_DIAGNOSTIC_MARKERS` (`["pshA"]`) in
   `compose_recipe.py` (~1522–1604), with a composer producing an
   anaerobic/anoxic, light-driven, organic-carbon (heliobacteria are
   photoheterotrophs/diazotrophs, not autotrophs) recipe.
4. **Minimal file set:** new `data/diagnostic_markers/pshA_refs.fasta`
   (+ built blastdb), `data/pathway_definitions.json` (new pathway/override),
   `compose_recipe.py` (mode registration + `_compose_*` function). This is a
   marker-DB *creation*, so it is **out of scope for this read-only run** and is
   a future implementation step.

**Cross-reactivity sentinels (must be tested in any future implementation):**
Type I reaction centers are homologous across clades, so pshA references must be
shown **not** to cross-react with:
- Cyanobacteria (psaA, Type I PSI) — DB sentinels: **gids 1017 (Nostoc PCC 7120),
  1018 (Synechocystis PCC 6803), 1025 (Prochlorococcus MIT 9313), 1028
  (Synechococcus PCC 7942), 1092 (Anabaena sp. 90)** — none should gain a
  heliobacterial-phototrophy call.
- Green-sulfur bacteria (pscA, Type I) — the existing `pscA_fmoA` reference
  organisms (Chlorobaculum) must likewise not flip.
A future verification table should hold these as negative controls alongside
gid 1051 as the positive (with the B0TBM3 self-hit caveat noted).

## 7. STOP-and-report

None blocking. One scoping note for the morning queue: implementing B1 requires
**writing a new marker reference set + BLAST DB** (and code), which is
explicitly outside this read-only inspection's mandate and the "no marker DB
modification" constraint — so B1 is *inspection-complete and ready*, but its
implementation is a separate, approved, marker-writing task. The reference
design (non-circular outgroups + sentinels) is settled above.
