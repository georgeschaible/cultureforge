# BacDive → CultureForge capability mapping

**Date:** 2026-04-28 (Phase 2d Task 3.2)
**Scope:** Minimum-viable mapping covering the BacDive phenotype fields that translate cleanly to CultureForge capability categories. Long-tail BacDive fields are documented as available but not used for similarity scoring (per Checkpoint A user direction).

## Capability vocabulary (target dimensions)

The CultureForge capability vector dimensions, in priority order for similarity scoring:

| Dim | Capability | CultureForge marker / pathway evidence |
|---|---|---|
| 1 | aerobic_chemotrophic | terminal oxidase + TCA pathway |
| 2 | fermentative | glycolysis + fermentation product pathways |
| 3 | methanogenic | mcrA + methanogenesis pathway |
| 4 | acetogenic | acsB_cdhC + cooS_cdhA + WL pathway (negative-gated by mcrA) |
| 5 | anaerobic_respiratory_sulfate | dsrAB + qmoA (forward SR discriminator) |
| 6 | anaerobic_respiratory_iron | mtrC_omcB + iron reduction pathway |
| 7 | anaerobic_respiratory_nitrate | nosZ + denitrification pathway |
| 8 | anaerobic_respiratory_organohalide | rdhA |
| 9 | anammox | hzsA + hdh |
| 10 | lithotrophic_aerobic_ammonia | amoA + hao |
| 11 | lithotrophic_aerobic_sulfur | soxB |
| 12 | lithotrophic_aerobic_iron | cyc2 (acidophilic Fe(II) ox) |
| 13 | nitrogen_fixation | nifH |
| 14 | anoxygenic_phototrophy_purple | pufLM |
| 15 | anoxygenic_phototrophy_green | pscA_fmoA |
| 16 | oxygenic_phototrophy | psaA_psbA |
| 17 | bacteriorhodopsin | rhodopsin marker |
| 18 | syntrophic | composite (no marker; β-ox + electron-bifurcating + no terminal acceptor) |
| 19 | halophily | derived from BacDive `halophily` + GenomeSPOT salinity |

## BacDive field → CultureForge mapping

BacDive stores phenotype data inside the `Physiology and metabolism` and
`Culture and growth conditions` top-level sections. Each subsection can be
absent, scalar, or a list of dicts. The mapping handles each case
defensively (absent → unknown, not absent → negative).

### `Physiology and metabolism / oxygen tolerance`

```json
{"oxygen tolerance": "obligate aerobe"}
{"oxygen tolerance": [{"oxygen tolerance": "facultative anaerobe"}, ...]}
```

| BacDive value | CultureForge mapping |
|---|---|
| `obligate aerobe`, `aerobe` | `aerobic_chemotrophic` ← 0.9; not anaerobic |
| `facultative anaerobe`, `facultative aerobe` | `aerobic_chemotrophic` ← 0.7; `fermentative` ← 0.5 |
| `microaerophile`, `microaerophilic` | `aerobic_chemotrophic` ← 0.5 (lower because microaerobic) |
| `obligate anaerobe`, `anaerobe`, `strict anaerobe` | (no aerobic credit; suppressed for similarity) |

The values inside BacDive are sometimes phrased differently across strain
records (`"facultative aerobe"` vs `"facultative anaerobe"` — both exist
with similar semantics). The mapping treats both as facultative.

### `Physiology and metabolism / metabolite utilization`

A list of dicts: `{"metabolite": "...", "utilization activity": "+|-|±"}`.
Hundreds of metabolites are reported across the corpus. Only a small subset
maps to specific CultureForge capabilities; the rest are informational.

| BacDive metabolite | CultureForge capability dim |
|---|---|
| `H2/CO2` (positive utilization) | `methanogenic` ← 0.7 (when archaeal) ; `acetogenic` ← 0.5 (when bacterial); `anoxygenic_phototrophy_purple` ← 0.3 (when "+ light") |
| `acetate` (positive) | informational only — too broad |
| `methanol` (positive) | `methanogenic` ← 0.5 (methylotrophic methanogens) |
| `formate` (positive) | `methanogenic` ← 0.4; `acetogenic` ← 0.3 |
| `nitrate` (positive utilization) | `anaerobic_respiratory_nitrate` ← 0.6 |
| `sulfate` (positive utilization) | `anaerobic_respiratory_sulfate` ← 0.6 |
| `iron(III)` (positive) | `anaerobic_respiratory_iron` ← 0.6 |
| `H2S`, `sulfide` | `lithotrophic_aerobic_sulfur` ← 0.5 (or `anoxygenic_phototrophy_*` if light) |
| `NH4+`, `ammonium` (oxidation) | `lithotrophic_aerobic_ammonia` ← 0.6 |
| `Fe(II)` (oxidation) | `lithotrophic_aerobic_iron` ← 0.6 |
| `glucose`, `lactate`, `succinate`, `etc.` (utilization) | informational only |

The "informational only" rows ARE displayed in the inspector when present,
but they're not used in similarity scoring (too broad — every chemoorganotroph
uses many of these).

### `Physiology and metabolism / metabolite production`

A list of dicts: `{"metabolite": "...", "production": "yes|no"}`.

| BacDive metabolite | CultureForge mapping |
|---|---|
| `methane` (yes) | `methanogenic` ← 0.9 (very strong) |
| `acetate` (yes, anaerobic) | `acetogenic` ← 0.5; `fermentative` ← 0.3 |
| `H2` (yes, anaerobic) | `fermentative` ← 0.4 (mixed-acid fermenters); `syntrophic` ← 0.3 |
| `lactate`, `ethanol`, `butyrate` (yes) | `fermentative` ← 0.5 |
| `N2` (yes) | `anaerobic_respiratory_nitrate` ← 0.6 (denitrifier producing N₂) |

### `Physiology and metabolism / enzymes`

| BacDive enzyme (positive activity) | CultureForge mapping |
|---|---|
| `catalase` | `aerobic_chemotrophic` ← 0.4 (catalase is a strong aerobic indicator) |
| `cytochrome c oxidase`, `oxidase` | `aerobic_chemotrophic` ← 0.6 |
| `nitrogenase` | `nitrogen_fixation` ← 0.9 |

The corpus contains ~50 enzyme tests; most are not metabolism-defining and
are informational only.

### `Physiology and metabolism / halophily / Culture and growth conditions / salt`

| BacDive salinity | CultureForge mapping |
|---|---|
| > 15% NaCl tolerance, or `halophilic`, `extreme halophile` | `halophily` ← 0.9 |
| 5-15% NaCl tolerance, `moderate halophile` | `halophily` ← 0.5 |
| < 5%, `non-halophile`, `halotolerant` | `halophily` ← 0.0 |

For haloarchaea specifically (`Halobacterium`, `Haloarcula`, `Haloferax`,
`Halococcus`, …) the `bacteriorhodopsin` capability is also added at 0.7
when domain == `Archaea` AND halophily ≥ 0.5. This follows the convention
that bacteriorhodopsin is restricted to extreme-halophile archaea even
though the marker check would catch proteorhodopsin in marine bacteria.

## Long-tail BacDive fields — present but not used

These fields are loaded into `bacdive_cache.response_json` but not
projected into the capability vector:

- `Morphology` (cell shape, gram stain, motility, spore-forming) — useful for
  cultivation flagging but doesn't map to capability categories.
- `metabolite utilization` for the ~200 minor substrates (sugars, amino
  acids, carboxylic acids) — too broad to discriminate cultivation modes.
- `enzyme activity` for the ~40 minor enzymes (e.g., specific peptidases) —
  not metabolism-defining.
- `compound production` (secondary metabolites, antibiotics) — outside
  cultivation-mode scope.
- `Culture and growth conditions / culture media` — already linked via
  the MediaDive `medium-strains` reverse index.
- `Genome-based predictions` — overlaps with our pipeline; not used to
  avoid double-counting.

If similarity scoring later proves too coarse for some organism class,
any of these fields can be promoted to the capability vector with an
explicit weight.

## Implementation notes (for Task 3.1)

The capability vector is a `dict[str, float]` with the 19 dimensions above
as keys and confidence values in [0.0, 1.0]. Cosine similarity is computed
over the union of nonzero dimensions of both vectors:

```python
def cosine(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    if not keys: return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    norm_a = sum(v*v for v in a.values()) ** 0.5
    norm_b = sum(v*v for v in b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0: return 0.0
    return dot / (norm_a * norm_b)
```

When BacDive data is partial (many fields absent — typical for older or
Candidatus records), the vector simply has fewer nonzero dimensions. This
biases similarity toward whatever capabilities ARE annotated, which is
acceptable for our use case (functional neighbor matching is a fallback
for organisms without direct media links; partial BacDive data is better
than none).
