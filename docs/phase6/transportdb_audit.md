# TransportDB2 integration audit

**Date:** 2026-05-21
**Scope:** Determine whether the Saier-lab TransportDB2 / TCDB
(https://www.membranetransport.org/) is integrated into CultureForge, and
how transporter evidence is currently represented and used.
**Method:** Read-only codebase grep + DB schema inspection. No edits.

---

## 1. Direct references to TransportDB / TCDB

**No direct CultureForge integration** with TransportDB2, the Saier lab's
membranetransport.org service, or any explicit TCDB download/parser.

Searched: `transportdb`, `membranetransport`, `saier`, `transporter
classification`, `TC.*number`, in `*.py / *.md / *.json / *.yml / *.yaml /
*.txt / *.tsv / *.csv` outside `__pycache__`, `.git`, and `data/`.

Result: zero meaningful matches in repo code or curator-authored docs.
Two false positives (an ATCC strain reference in
`VERIFICATION_DISCIPLINE.md:55`, and a pathway-step "classification"
reference in `docs/CAPABILITY_DETECTORS.md:39`).

The **one** code-level reference to TC families is the hardcoded
`NA_CYCLING_TC_FAMILIES` constant in `synthesize_denovo.py:85`, which
hardcodes three TC family prefixes used in marine-salinity detection
(see §3 below).

---

## 2. How transporters are currently represented

Transporters are an indirect derivative of **gapseq** output, not a
first-class CultureForge reference.

### Pipeline

1. `process_genome.py:205` invokes `gapseq find-transport -b 200
   <genome>` per accession.  This produces `<accession>-Transporter.tbl`
   in the gapseq output directory.
2. `register_genome.py` loads that TSV into the SQLite table
   `genome_transporters`.
3. Downstream code reads that table via
   `capability_detectors._get_transporters()` and
   `synthesize_denovo.get_transporter_summary()`.

### Schema (`genome_transporters`)

```sql
CREATE TABLE genome_transporters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    tc_id TEXT,                     -- e.g. "1.A.1.13.10"
    substrate TEXT NOT NULL,        -- e.g. "potassium"
    exchange_id TEXT,               -- e.g. "EX_cpd00205_e0"
    reaction_ids TEXT,              -- gapseq's reaction ID list
    query_seqid TEXT,               -- e.g. "gnl|TC-DB|Q58752"
    pident REAL,
    evalue REAL,
    bitscore REAL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id)
);
```

**TC IDs ARE stored** — this is the indirect TCDB linkage. They come
from gapseq, which BLASTs the genome's proteins against TCDB sequences
internally as part of `find-transport`. So CultureForge inherits TCDB
classification through gapseq, but does not query the membranetransport.org
service directly, store TCDB sequences locally, or curate any TC
references.

### Sample of stored evidence (genome_id 7, Desulfovibrio vulgaris)

```
tc_id=1.A.1.13.10  substrate=potassium  query_seqid=gnl|TC-DB|Q58752  pident=33.86
tc_id=1.A.1.13.2   substrate=potassium  query_seqid=gnl|TC-DB|O27564  pident=27.21
tc_id=1.A.1.13.7   substrate=potassium  query_seqid=gnl|TC-DB|P73132  pident=39.64
...
```

### Downstream use of transporter data

Three places in code consume `genome_transporters`:

| File | What it does | Uses TC ID? |
|---|---|---|
| `capability_detectors.py:172,215,344,356` | Matches transporters against pathway-specific name patterns (e.g. `"ammonium.*transport"`, `"amt"`, `"focA"`) for pathway scoring | **No** — uses substrate/name regex from `pathway_definitions.json` |
| `synthesize_denovo.py:211,343,777,918` | Heuristics: sugar transporter density (heterotrophy), amtB presence (ammonium), pst (high-affinity phosphate) | **No** — substrate name and counts |
| `synthesize_denovo.py:1149` | Marine salinity detection — counts hits within hardcoded Na+ cycling TC families (`2.A.36`, `2.A.63`, `3.D.5`) | **Yes** — single use of `tc_id LIKE 'prefix%'` |

### Pathway-definition transporter wiring

`data/pathway_definitions.json` declares per-pathway `required_transporters`
and `product_transporters` keyed on substrate/gene-name regex. Examples:

| Pathway | Required transporter | Patterns |
|---|---|---|
| acetate fermentation | formate transporter | `formate.*transport`, `focA` |
| nitrogen | ammonium transporter | `ammonium.*transport`, `amt`, `ammoni` |
| sulfate reduction | sulfate transporter | `sulfate.*transport`, `sulP`, `sbp`, `cysUWA`, `sulfate.*permease` |
| nitrate respiration | nitrate/nitrite transporter | `nitrate.*transport`, `nitrite.*transport`, `narK` |

Scoring uses these regex patterns against gapseq's substrate/name fields,
not against the `tc_id` column.

### Diagnostic markers (separate machinery)

`data/diagnostic_markers/` contains 301 files (FASTA refs + BLAST DBs)
for marker enzymes (amoA, aprAB, acsB_cdhC, etc.). None are explicitly
transporter-related — this directory targets enzyme catalysis evidence,
not membrane-transport classification.

---

## 3. Apparent integration gap

**TC IDs flow in but are essentially unused downstream.** Every stored
row in `genome_transporters` has a `tc_id`, but only `NA_CYCLING_TC_FAMILIES`
in `synthesize_denovo.py` actually queries that column. Every other
consumer falls back to substrate-name regex.

This is a usable axis of evidence that the framework is not currently
exploiting. Concretely:

- **No TC-family-keyed pathway definitions.** Pathways are matched via
  gene/substrate name fragments. This works but is brittle (gene name
  drift) and misses families that share function but don't share name
  patterns.
- **No use of TC hierarchy.** Stored TC IDs are e.g. `1.A.1.13.10`
  (channel/porin family). The framework never traverses from a leaf TC
  ID to its parent class for broader matching, except by manual
  prefix-match in the Na+ cycling code.
- **No external TCDB enrichment.** TC IDs are not enriched with TCDB
  metadata (transporter family name, substrate class, ion coupling) at
  load time. Such enrichment would let pathway definitions and recipe
  heuristics reference TC families directly.

---

## 4. Brief assessment

**Is this a meaningful gap, or is current handling sufficient?**

Current handling is **functional for the framework's published scope**.
Gapseq's substrate strings give pathway-level evidence (does the genome
have *some* sulfate transporter?), and pattern-matching covers the
common families that pathway curators have explicitly enumerated. The
single TC-family usage (Na+ cycling for marine detection) demonstrates
the pattern is technically extensible.

But there is a real opportunity:

1. **For new pathways or unusual organisms**, name-pattern matching
   misses transporters whose gene names don't fit the curator's regex
   — exactly the case where TC-family matching would be more robust
   (e.g., specialized halophile/thermophile/methanogen transporters
   whose nomenclature differs from `narK`/`amtB`/`focA`).
2. **For QC and contamination detection** (relevant to the current
   sourmash identity-verification work), TC profile divergence could
   serve as a secondary signal alongside Mash/sourmash containment —
   e.g., an "archaeal" genome whose TC families are dominated by
   bacterial-typical patterns is suspicious.
3. **Cost is low.** TCDB's family/subfamily classification is a static
   reference (curated tree, ~10k families). Importing it as a small
   lookup table (`tc_id → family_name, transporter_class, common_substrate`)
   plus updating pathway_definitions.json to optionally accept TC
   prefixes would not require any external service.

**Not a blocker** for the current manuscript scope, but the gap is real
and the fix would be small and well-defined.

---

## Files referenced

- `process_genome.py` — gapseq find-transport invocation (line 205)
- `register_genome.py` — loads `genome_transporters` table (line 50)
- `capability_detectors.py` — pathway-scoring transporter matching
  (lines 172, 215, 250-365, 591)
- `synthesize_denovo.py` — heuristics and the only `tc_id` query
  (lines 82-89, 211, 342-357, 767, 916-921, 1149)
- `confidence.py` — transporter prediction confidence scoring
  (lines 183-200, 247, 371)
- `data/pathway_definitions.json` — `required_transporters`,
  `product_transporters` arrays per pathway
- `data/diagnostic_markers/` — 301 marker files, none transporter-related
- DB schema — `genome_transporters` table with `tc_id` column

## Files NOT found

- No file containing `TransportDB` or `membranetransport`
- No file containing `saier` (case-insensitive)
- No TCDB reference download script, no TCDB cache directory, no
  TC-family enrichment table
