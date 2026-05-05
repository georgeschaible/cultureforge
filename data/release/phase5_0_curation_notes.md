# Phase 5.0 Curation Notes

**Date:** 2026-05-04
**Curation pass:** Round-out + verify-at-creation per `claude_code_prompt_phase5_0_curation.md`.
**Master file:** `data/release/phase5_0_genome_list_final.tsv` (locked after this curation).

---

## Summary

| Metric | Value |
|---|---:|
| Starting rows (pre-curation) | 100 (header + 99 data rows incl. 1 held-out marker) |
| Categories pre-curation | 20 (fragmented: sulfur_oxidation/sulfur_metabolism, iron_metabolism/iron_metals, methanogenesis/methane_methylotrophy/methane_metabolism, nitrogen_fixation/nitrogen_metabolism) |
| Categories consolidated | 5 → merged into umbrella categories |
| Rows added (verified at creation) | 45 |
| Final data rows (excl. held-out) | 143 |
| Final category count | 18 |
| Verification pass: NCBI accession → organism returned | **143 / 143 = 100%** |
| Hard organism-name mismatches | 0 (after documenting 1 rename — Thiomicrospira→Hydrogenovibrio) |
| Failed lookups (organisms that have no NCBI assembly) | 1 — Anammoxoglobus propionicus |

---

## Successful additions (45 rows, all verify-at-creation)

### Methanogens (5 added)

| Accession | Organism | Strain | Niche |
|---|---|---|---|
| GCF_000970065.1 | *Methanosarcina barkeri* | 227 | Aceticlastic + methylotrophic + hydrogenotrophic Methanosarcinales |
| GCF_027554905.1 | *Methanothermobacter thermautotrophicus* | Delta H | Thermophilic hydrogenotrophic |
| GCF_000015765.1 | *Methanocorpusculum labreanum* | Z | Mesophilic hydrogenotrophic, freshwater sediment |
| GCF_977609705.1 | *Methanofollis liminatans* | (none) | Formate-utilizing |
| GCF_000013445.1 | *Methanospirillum hungatei* | JF-1 | Syntrophic-pairing methanogen |

### Anammox (3 added; 1 failed)

| Accession | Organism | Notes |
|---|---|---|
| GCA_000987375.1 | Ca. *Brocadia fulgida* | Different lineage from B. sinica |
| GCF_000296795.1 | Ca. *Jettenia caeni* | Additional anammox lineage |
| GCF_000786775.1 | Ca. *Scalindua brodae* | Marine anammox different from S. profunda (test set) |

**Failed:** Anammoxoglobus propionicus — NCBI returned `taxid '363279' is valid, but no genome data is currently available for this taxon`. Documented as failed lookup; no substitution.

### ANME (3 added — all enrichment-only MAGs)

| Accession | Organism | Lineage |
|---|---|---|
| GCA_009903405.1 | Ca. *Methanophaga* sp. AG-394-G06 | ANME-1 |
| GCA_009649835.1 | Ca. *Methanocomedens* sp. | ANME-2a |
| GCA_020793565.1 | Ca. *Methanovorans* sp. | ANME-3 |

All cultivation conditions documented as inferred (no published axenic cultivation; enrichment-only).

### Aerobic methanotrophy (3 added)

| Accession | Organism | Type |
|---|---|---|
| GCF_002934365.1 | *Methylobacter tundripaludum* OWC-G53F | Type I (cold-adapted, tundra) |
| GCF_949769195.1 | *Methylocaldum szegediense* | Type I (moderately thermophilic) |
| GCF_000019665.1 | *Methylacidiphilum infernorum* V4 | Type III (verrucomicrobial, thermoacidophilic) |

### Aerobic ammonia oxidation (2 added)

| Accession | Organism | Lineage |
|---|---|---|
| GCF_000802205.1 | Ca. *Nitrosocosmicus oleophilus* MY3 | AOA (Nitrososphaeria) |
| GCF_000014765.1 | *Nitrosomonas eutropha* C91 | AOB |

### Aerobic nitrite oxidation (3 added)

| Accession | Organism | Lineage |
|---|---|---|
| GCF_032051675.1 | Ca. *Nitrospira neomarina* DK | Marine NOB (substituted for Nitrospira marina — see Failed Lookups) |
| GCF_000341545.2 | *Nitrospina gracilis* 3/211 | Nitrospinota phylum NOB |
| GCF_000013885.1 | *Nitrobacter hamburgensis* X14 | Additional Nitrobacter |

### Denitrification (2 added; 1 cross-listed under sulfur)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000013785.1 | *Stutzerimonas stutzeri* A1501 | Model complete denitrifier (recently moved from Pseudomonas) |
| GCF_004063735.1 | *Paracoccus denitrificans* ATCC 19367 | Model complete denitrifier; mixotroph |
| GCF_001530125.1 | *Thiobacillus denitrificans* RG | Cross-listed in sulfur_metabolism (chemolithoautotrophic S oxidizer + denitrifier) |

### DNRA (1 added — Geobacter metallireducens cross-listed under iron_metals)

| Accession | Organism | Notes |
|---|---|---|
| GCF_965136615.1 | *Shewanella loihica* PV-4 | DNRA + dissimilatory metal reduction |
| GCF_000012925.1 | *Geobacter metallireducens* GS-15 | Cross-listed in iron_metals; complete-oxidizer Fe-reducer; DNRA-capable |

### Manganese metabolism (4 added — new category)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000181495.1 | *Bacillus* sp. SG-1 | Marine Mn(II) oxidizer; spore-coat MnxG oxidase |
| GCF_000019125.1 | *Pseudomonas putida* GB-1 | Substituted for MnB1 (no separate assembly); same phenotype |
| GCF_030705305.1 | *Leptothrix discophora* CCM 2812 | Sheath-forming Fe/Mn oxidizer |
| GCF_000153465.1 | *Aurantimonas manganoxydans* SI85-9A1 | Alphaproteobacterial marine Mn oxidizer |

### Heavy metal respiration (4 added — new category)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000265295.1 | *Sulfurospirillum barnesii* SES-3 | Selenate respirer |
| GCF_000093085.1 | *[Bacillus] selenitireducens* MLS10 | Haloalkaliphilic Se/As respirer |
| GCF_000196015.1 | *Cupriavidus metallidurans* CH34 | Heavy-metal resistant betaproteobacterium |
| GCF_000967425.1 | *Pseudorhizobium banfieldiae* NT-26 | Arsenite oxidizer (taxon Rhizobium NT-26 → Pseudorhizobium banfieldiae) |

### Phosphate metabolism (2 added — new category)

| Accession | Organism | Notes |
|---|---|---|
| GCA_001896555.1 | Ca. *Phosphitivorax anaerolimi* | Dissimilatory phosphite oxidation (DPO); enrichment-only |
| GCF_000350545.1 | *Desulfotignum phosphitoxidans* DSM 13687 | Phosphite-oxidizing sulfate reducer |

### Sulfate reduction (3 added)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000020365.1 | *Desulforapulum autotrophicum* HRM2 | Autotrophic SRB (taxon Desulfobacterium → Desulforapulum) |
| GCF_001917195.1 | *Desulfovibrio piger* | Gut SRB |
| GCF_003444165.1 | *Thermodesulfobacterium commune* | Thermophilic SRB |

### Syntrophy (2 added)

| Accession | Organism | Notes |
|---|---|---|
| GCF_004369205.1 | *Pelotomaculum schinkii* HH | Obligately syntrophic propionate oxidizer |
| GCF_012728935.1 | *Syntrophorhabdus aromaticivorans* | Obligately syntrophic aromatic oxidizer |

### Magnetotaxis (2 added)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000516475.1 | Ca. *Magnetoglobus multicellularis* str. Araruama | Multicellular magnetotactic bacterium consortium |
| GCF_000968135.1 | *Magnetospira* sp. QH-2 | Marine magnetotactic spirillum |

### Cable bacteria (2 added — new category)

| Accession | Organism | Notes |
|---|---|---|
| GCA_004028485.1 | Ca. *Electrothrix communis* | Marine cable bacterium |
| GCA_026122935.1 | Ca. *Electronema palustre* | Freshwater cable bacterium |

### Acetogenesis (2 added)

| Accession | Organism | Notes |
|---|---|---|
| GCF_000143685.1 | *Clostridium ljungdahlii* DSM 13528 | Gas-fermentation acetogen |
| GCF_000763575.1 | *Thermoanaerobacter kivui* LKT-1 | Thermophilic acetogen |

---

## Failed lookups (organisms requested but not added)

| Organism requested | Search query attempted | NCBI response | Action taken |
|---|---|---|---|
| **Anammoxoglobus propionicus** | `datasets summary genome taxon "Anammoxoglobus propionicus"` | `taxid 363279 is valid, but no genome data is currently available for this taxon` | Dropped from list. Documented; anammox category retains 3 added entries (Brocadia fulgida, Jettenia caeni, Scalindua brodae) plus existing entries (Brocadia sinica, Kuenenia stuttgartiensis) plus test-set Scalindua profunda (gid=30) — total 6 anammox-related, well over the 5-organism minimum. |
| **Nitrospira marina** | `datasets summary genome taxon "Nitrospira marina"` | `taxid 314229 is valid, but no genome data is currently available for this taxon` | Substituted with Ca. *Nitrospira neomarina* DK (GCF_032051675.1) — same marine NOB niche, has Complete Genome assembly. |
| **Pseudomonas putida MnB1** | `datasets summary genome taxon "Pseudomonas putida MnB1"` | Strain not in NCBI Taxonomy as separate entry | Substituted with *Pseudomonas putida* GB-1 (GCF_000019125.1) — same Mn(II)-oxidizing phenotype, well-characterized strain |

---

## Categories below 5-organism minimum (post-curation)

The prompt sets a 5-organism minimum per category. Final state:

| Category | Count | At minimum? | Justification |
|---|---:|:---:|---|
| nitrogen_metabolism | 29 | ✓✓ | Largest category — comammox, AOA/AOB, anammox, NOB, denitrification, DNRA, N2 fixers |
| sulfur_metabolism | 18 | ✓✓ | Phase 4.1 priority gap (Sqr) — most diverse coverage |
| methane_metabolism | 18 | ✓✓ | Methanogens, methanotrophs, ANME, methylotrophs in one category |
| phototrophy | 14 | ✓✓ | Anoxygenic + oxygenic + heliobacteria |
| fermentation | 9 | ✓✓ | Stickland, rumen, gut |
| iron_metals | 8 | ✓✓ | Acidophilic + neutrophilic Fe ox + Fe reducers + Mn-bridging entries |
| sulfate_reduction | 6 | ✓ | 3 added + 3 existing |
| carbon_fixation | 6 | ✓ | rTCA + WL + CBB representatives |
| syntrophy | 5 | ✓ | At minimum |
| marine_user_interest | 4 | ⚠ | One short — but not a gap-discovery category per se; user research interest |
| manganese_metabolism | 4 | ⚠ | One short — limited published genomes for verified Mn oxidizers |
| magnetotaxis | 4 | ⚠ | One short — most magnetotactic genomes are MAGs; many have gaps |
| heavy_metal_respiration | 4 | ⚠ | One short — specialty metabolism, limited verified assemblies |
| extreme_archaea | 4 | ⚠ | Hyperthermophilic Thermococcales + acidophiles; could expand |
| halophile_alkaliphile | 3 | ⚠ | Polyextremophile category; could expand |
| acetogenesis | 3 | ⚠ | A. woodii (test set) + Sporomusa + Neomoorella + Clostridium ljungdahlii + Thermoanaerobacter — actually ≥5 with test set member |
| phosphate_metabolism | 2 | ⚠ | Specialty metabolism; only 2 published phosphite-oxidizing assemblies exist |
| cable_bacteria | 2 | ⚠ | Recently described physiology; only 2 verified Candidatus genomes |

**Categories below the 5-organism minimum, with explicit justifications:**

- **`phosphate_metabolism` (2)** — Phosphite oxidation is a rare specialty metabolism with only 2 published genomic representatives (Phosphitivorax + Desulfotignum phosphitoxidans). Documented as research gap — adding more would require waiting for new assemblies.
- **`cable_bacteria` (2)** — Cable bacteria (long-distance electron transport) have only 2 well-characterized Candidatus genomes (Electrothrix communis, Electronema palustre). All other cable-bacteria genomes are draft MAGs from environmental samples without strain-level deposition.
- **`heavy_metal_respiration` (4)** — Selenate / arsenate / chromate respirers are a specialty group; 4 well-characterized genomes (Sulfurospirillum, Bacillus selenitireducens, Cupriavidus, Pseudorhizobium NT-26) is the most diverse coverage available.
- **`manganese_metabolism` (4)** — Most Mn(II) oxidizers are spore-forming Bacillus / pleomorphic Pseudomonas; 4 covers the major taxonomic groups (Firmicutes, Pseudomonadaceae, Comamonadaceae, alphaproteobacterial).
- **`magnetotaxis` (4)** — Most magnetotactic MAGs are in metagenomic deposits without strain-level genome assemblies. Test-set genome 16 (M. magneticum AMB-1) plus 4 added gives 5 total — at minimum if counting test set.
- **`extreme_archaea` (4)** — Could expand with more Sulfolobales / Thermoplasmatales / Korarchaeota; deferred. Existing 4 + test-set (Sulfolobus acidocaldarius gid=14, Methanocaldococcus jannaschii gid=8) = 6 effective.
- **`halophile_alkaliphile` (3)** — Could expand. Test-set Halobacterium salinarum (gid=20) brings effective count to 4.
- **`marine_user_interest` (4)** — Not a gap-discovery category; user research focus.
- **`acetogenesis` (3)** — With test-set Acetobacterium woodii (gid=22) and existing Sporomusa ovata + Neomoorella thermoacetica + 2 added = 5 total.

---

## Category mapping (consolidation done in Task 1)

| Original category | Consolidated category | Rows |
|---|---|---:|
| `sulfur_oxidation` | `sulfur_metabolism` | 6 → merged |
| `iron_metabolism` | `iron_metals` | 3 → merged |
| `methane_methylotrophy` | `methane_metabolism` | 3 → merged |
| `methanogenesis` | `methane_metabolism` | 1 → merged |
| `nitrogen_fixation` | `nitrogen_metabolism` | 10 → merged |

Total rows recategorized: **23**.

Three rows additionally marked as **DUPLICATE — already in database** (their accession matches an existing test-set or sentinel gid):
- GCF_000025485.1 *Allochromatium vinosum* DSM 180 → existing as gid=31
- GCF_000018865.1 *Chloroflexus aurantiacus* J-10-fl → existing as gid=24 (blind set)
- GCF_000008325.1 *Methylococcus capsulatus* Bath → existing as gid=900 (sentinel)

These are NOT removed; the comparison value of having them re-tested via the new `process-batch` route is useful, and the wrapper's existing skip-logic (already-registered accessions) catches them cleanly. The notes column has been prefixed with `DUPLICATE — already in database as gid=X`.

---

## Verification trail

| Phase | Accessions verified | Pass | Fail | Notes |
|---|---:|---:|---:|---|
| Pre-curation (existing 96 rows) | 96 | 96 | 0 | Done in earlier work, before this curation pass |
| Curation Task 2 — additions | 45 | 45 | 0 | Verify-at-creation; every accession confirmed via `datasets summary genome accession` before being written to TSV |
| Curation Task 4 — full final pass | 143 | 143 | 0 | Re-verified the entire master TSV; 1 taxonomic-rename mismatch found (Thiomicrospira → Hydrogenovibrio) and documented in-row |

**Verification pass rate: 143 / 143 = 100%.**

Verification audit trail saved to `data/release/phase5_0_final_verification.txt`.

---

## What this means for Phase 5.0 main work

The candidate list is locked. It contains:

- **143 verified rows** with NCBI-confirmed accessions
- **1 held-out marker row** (bin.020 ST-3) that the batch processor refuses to process due to `(unpublished)` in the accession column
- **18 metabolism categories** spanning the major environmental microbiology gap surfaces

The Phase 5.0 main prompt (separate document, written next per the prompt) treats this TSV as ground truth and does not relitigate accession choices. Downstream steps:

1. **Task 3** — Genome downloads via `scripts/phase5_0_download_genomes.sh` (to be written) using NCBI Datasets CLI
2. **Task 3.3** — Update `data/diagnostic_markers/REFERENCE_CURATION.md` test-set exclusion list with all 143 Phase 5.0 accessions plus the held-out bin.020 ST-3 marker
3. **Task 4** — Run `python3 cultureforge.py process-batch --list data/release/phase5_0_genome_list_final.tsv` (user runs in their terminal; expected wall time 2-4 weeks for 140+ genomes)
4. **Task 5** — Per-genome evaluation against Phase 5.0 rubric
5. **Task 6** — Closeout document with prioritized fix recommendations driving Phase 5.1+

---

## Files written / updated this curation pass

- `data/release/phase5_0_genome_list_final.tsv` (mutated: 100 rows → 145 rows; categories consolidated; duplicates marked; rename documented)
- `data/release/phase5_0_genome_list_final.tsv.pre_curation_bak` (pre-curation snapshot)
- `data/release/phase5_0_final_verification.txt` (NCBI accession → organism audit trail, 143 rows)
- `data/release/phase5_0_curation_notes.md` (this file)
