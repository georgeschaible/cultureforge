# MediaDive REST API — investigation notes

**Date:** 2026-04-28 (Phase 2d Task 1.1)
**Base URL:** `https://mediadive.dsmz.de/rest`
**Authentication:** None required.
**Rate limits:** No published rate limit; a polite delay (`time.sleep(0.2)` between requests) is what `download_medium_strains.py` already uses without issue. The full corpus (3,336 media + 2,705 medium-strain mapping files) was downloaded in Phase 1 with no API errors.
**Documentation page:** `https://mediadive.dsmz.de/doc/index.html` exists; we relied on the existing `download_mediadive.py` / `download_medium_strains.py` for endpoint patterns (verified live).

## Endpoint catalog

All endpoints return `{ status, count, data }` JSON envelopes.

| Endpoint | HTTP | Returns |
|---|---|---|
| `GET /medium` | 200 | List of all 3,336 media: `{ id, name, complex_medium, source, link, min_pH, max_pH, reference, description }` |
| `GET /medium/{id}` | 200 | Full medium recipe: `{ medium: {...}, solutions: [...] }` |
| `GET /medium-strains/{id}` | 200 | Strains cultivated on this medium: list of `{ id, species, ccno, growth, bacdive_id, domain }` |
| `GET /strains` | 400 ("WrongCall") | NOT supported |
| `GET /strain/{name}` | 400 ("WrongCall") | NOT supported |
| `GET /strain-media/{bacdive_id}` | 400 ("WrongCall") | NOT supported (reverse direction must be built locally) |
| `GET /search?q=...` | 400 ("WrongCall") | NOT supported |
| `GET /compounds` | 400 ("WrongCall") | NOT supported (compound info only via medium recipes) |

The supported endpoints are minimal: medium-by-id (forward) + medium-strain-list (forward). **There is no API path from `bacdive_id` → media list.** That reverse mapping must be built locally by scanning all `/medium-strains/*` responses — which is exactly what was done in Phase 1, and the resulting 2,705 mapping files are cached at `data/mediadive/medium_strains/`.

## Medium recipe JSON schema (e.g., medium 282 "METHANOCALDOCOCCUS MEDIUM")

```json
{
  "medium": {
    "id": 282,
    "name": "METHANOCALDOCOCCUS MEDIUM",
    "complex_medium": "no",
    "min_pH": 6,
    "max_pH": 6,
    "source": "DSMZ",
    "link": "https://www.dsmz.de/microorganisms/medium/pdf/DSMZ_Medium282.pdf"
  },
  "solutions": [
    {
      "id": 548,
      "name": "Main sol. 282",
      "volume": 1012,
      "recipe": [
        {"recipe_order": 1, "compound": "K2HPO4", "compound_id": 10,
         "amount": 0.14, "unit": "g", "g_l": 0.13834, "mmol_l": 0.794254, "optional": 0},
        {"recipe_order": 2, "compound": "CaCl2 x 2 H2O", "compound_id": 7,
         "amount": 0.14, "unit": "g", "g_l": 0.13834, "mmol_l": 0.940992, "optional": 0},
        ...
      ],
      "steps": [...],
      "equipment": {...}
    },
    ...
  ]
}
```

Concentrations are reported in three forms (g per 1L final medium, mM, and per-solution amount + unit). `g_l` is the per-1L-medium concentration after sub-solution combination — the field the recipe composer should use for comparison.

## medium-strains response schema (e.g., medium-strains/282)

```json
{
  "status": 200,
  "count": 13,
  "data": [
    {"id": 1909, "species": "Methanocaldococcus jannaschii",
     "ccno": "DSM 2661", "growth": 1, "bacdive_id": 6981, "domain": "A"},
    ...
  ]
}
```

`growth: 1` = strain grows on this medium; `growth: 0` = strain tested on this medium and did NOT grow (negative result, also useful).

## Local cache state

Already complete from Phase 1:
- `data/mediadive/all_media.json` — index of all 3,336 media
- `data/mediadive/index.json` — same index
- `data/mediadive/media/{id}.json` — 3,336 full medium recipes (one file per medium)
- `data/mediadive/medium_strains/{id}.json` — 2,705 medium-strain mapping files

**Phase 2d does not need to re-download MediaDive content.** All Phase 2d-relevant data is already on disk.

## Reverse index buildable from local cache

`download_medium_strains.py` only emits per-medium → strains; the reverse `bacdive_id → list[medium_id]` index can be built in <1 second from the cached files:

```python
import json, os
from collections import defaultdict
bd_to_media = defaultdict(list)
for fn in os.listdir("data/mediadive/medium_strains"):
    mid = fn.replace(".json", "")
    for s in json.load(open(f"data/mediadive/medium_strains/{fn}")):
        if s.get("bacdive_id") and s.get("growth") == 1:
            bd_to_media[s["bacdive_id"]].append(mid)
```

Validated on 26-organism dev+blind set: 21,244 species and 35,190 BacDive IDs are linked to at least one MediaDive medium in the local cache.

Spot-check results (dev set):

| Organism | Media linked |
|---|---|
| Methanocaldococcus jannaschii | 282, J232 |
| Escherichia coli | 1, 215, 220, 237, 238, 306, 339, 1270 |
| Halobacterium salinarum | 97, 372, J168, J169 |
| Acidithiobacillus ferrooxidans | 70, 71, 271, 670, 882, J92, J1321 |
| Geobacter sulfurreducens | (no direct match — not linked in MediaDive's strain table) |
