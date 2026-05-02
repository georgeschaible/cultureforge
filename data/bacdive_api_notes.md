# BacDive REST API — investigation notes

**Date:** 2026-04-28 (Phase 2d Task 1.2)
**Base URL:** `https://api.bacdive.dsmz.de`
**Authentication:** **None required** for the endpoints we need. The about/landing page mentions account registration for some legacy clients, but the modern REST endpoints work anonymously (verified live in this investigation).
**Rate limits:** Not published. The existing `download_bacdive.py` uses a small inter-request delay and successfully downloaded 30,538 strain records. No rate-limit errors observed.
**Documentation:** Landing page at `https://api.bacdive.dsmz.de/` lists endpoint examples but no formal OpenAPI / Swagger spec. We verified the working endpoints by direct probing.

## Endpoint catalog (verified working)

| Endpoint | HTTP | Returns |
|---|---|---|
| `GET /fetch/{bacdive_id}` | 200 | Full strain detail (10+ sections) |
| `GET /taxon/{taxon_name}` | 200 | List of BacDive IDs for organisms in that taxon |
| `GET /culturecollectionno/{ccno}` | 200 | List of BacDive IDs for a given strain number (e.g., DSM 2661) |
| `GET /` | 200 (HTML) | Landing page with endpoint examples |

`{taxon_name}` accepts genus-level names directly (e.g., `Methanocaldococcus`); species-level names need URL encoding for the space (`Methanocaldococcus%20jannaschii`). The taxon-by-species query may return zero results in some cases — coverage is incomplete; the more reliable path is the local `species → bacdive_id` map built from MediaDive's `medium-strains/*` data.

## Endpoints that DO NOT work as the prompt's pseudocode suggested

| Attempt | Result |
|---|---|
| `GET /search?species=...` | 404 |
| `GET /search?q=...` | 404 |
| `GET /search/species/...` | 404 |
| `GET /search/{name}` | 404 |
| `GET /fetch/6981,6984` (multi-ID) | 404 (only single-ID `/fetch/{id}` works) |
| `GET /fetch/{id}/` (trailing slash) | 404 |

There is **no formal `/search` endpoint** in BacDive's public API. Workarounds:
- For organism → BacDive ID: use `/taxon/{genus}` to enumerate IDs in a genus, OR `/culturecollectionno/{ccno}` if the strain number is known, OR map via MediaDive's `medium-strains/*` (which carries `bacdive_id` per species record).
- For multi-fetch: loop with `time.sleep(0.2)` between single fetches.

## fetch/{id} JSON schema

Response envelope:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": {
    "{bacdive_id}": { ... full strain document ... }
  }
}
```

Strain document top-level sections (from sample `bacdive_id=6981` Methanocaldococcus jannaschii):

| Section | Phase 2d relevance |
|---|---|
| `General` | BacDive-ID, DSM-number, NCBI tax id, keywords, description |
| `Name and taxonomic classification` | domain / phylum / class / order / family / genus / species / strain designation |
| `Morphology` | cell shape, spore-forming, gram stain |
| `Culture and growth conditions` | **culture media (links to MediaDive medium IDs)**, growth temperature, oxygen tolerance, salinity |
| `Physiology and metabolism` | **oxygen tolerance, metabolite utilization (substrate use), enzymes, halophily, etc.** ← primary source for capability mapping |
| `Isolation, sampling and environmental information` | habitat, sample source |
| `Sequence information` | 16S rRNA, genome assembly accessions |
| `Genome-based predictions` | precomputed phenotypic predictions (some overlap with our pipeline) |
| `External links` | NCBI, ATCC, UniProt links |
| `Reference` | citations |

The Phase 2d capability-mapping layer needs to read `Physiology and metabolism` (and `Culture and growth conditions` for atmosphere/temperature/pH) and translate the BacDive vocabulary into CultureForge capability categories.

## Local cache state

Already complete from Phase 1 (per `PROGRESS.md`):
- `data/bacdive/strains/{bacdive_id}.json` — 30,538 strains (~82% of medium-linked strains in MediaDive's strain table)
- The cache covers the BacDive entries that MediaDive links to known media — i.e., the union of strains for which we'd want a capability-vector mapping anyway.

**Phase 2d does not need to download additional BacDive data for the 26-organism dev+blind set.** Spot-check coverage:

| Organism | Local cache hit | BacDive ID |
|---|---|---|
| Methanocaldococcus jannaschii | ✅ | 6981 |
| Escherichia coli (DSM 1) | ✅ | (varies — ~50 E. coli strains in cache) |
| Halobacterium salinarum | ✅ | (in cache) |
| Acidithiobacillus ferrooxidans | ✅ | (in cache) |
| Methanoperedens nitroreducens | ❌ likely missing (uncultured-only) |
| Scalindua profunda | ❌ likely missing (uncultured-only) |

For the 6 blind-set Candidatus organisms, BacDive coverage is genuinely thin because they're uncultured / MAG-only. This is exactly the case where **functional neighbor matching** matters — find cultured organisms with similar capability profiles and use their published media as the reference.

## Capability-mapping fields (initial scope for Task 3.2)

Promising fields in `Physiology and metabolism`:

| BacDive field | Likely CultureForge capability mapping |
|---|---|
| `oxygen tolerance` | aerobic_chemotrophic / fermentative / anaerobic depending on category |
| `metabolite utilization` | substrate use → carbon source / electron donor categories |
| `metabolite production` | fermentation products → fermentation mode confirmation |
| `enzyme activity` (catalase, oxidase, etc.) | aerobic respiration confirmation |
| `halophily` | halophilic_with_rhodopsin (when archaeal + extreme) |
| `compound production` | secondary metabolites — informational only |

Different strains expose different subsets of these fields; the mapping needs to handle missing data gracefully (treat absent → unknown, not absent → negative).

## Recommendation: use local cache primarily

Both APIs are public, no-auth, and reasonably stable. **But for the 26-organism Phase 2d validation, no live API queries are needed at all.** The existing local cache is sufficient:

- 3,336 MediaDive media (full corpus)
- 2,705 MediaDive medium-strain mapping files
- 30,538 BacDive strain records (~82% of medium-linked strains)

The integration code (Task 2) should:
1. Read primarily from local JSON files (with optional fallback to live API for cache misses).
2. Build SQLite cache tables (`mediadive_cache`, `bacdive_cache`, `organism_to_bacdive`, `organism_to_published_media`) by scanning the local JSONs once, then querying tables for routine ops.
3. Provide thin `mediadive_client.py` / `bacdive_client.py` wrappers that hit the live API only when the cache doesn't have the requested ID.
4. Apply gentle rate limiting (`time.sleep(0.2)`) to live calls, matching the existing `download_*.py` patterns.

For the 26-organism set, the full Phase 2d pipeline can complete offline — which is faster, more reproducible, and avoids any API-instability surprises during validation.
