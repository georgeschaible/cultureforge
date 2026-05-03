# De Novo Media Synthesizer — Design Document

**Status:** Design review (not yet implemented)  
**Replaces:** Template-based synthesize_media.py (kept as fallback comparison)  
**Core principle:** Build recipes from genomic evidence, not by copying relatives' media

---

## Architecture Overview

```
                    GENOME FASTA
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          gapseq    GenomeSPOT   MeBiPred
          (pathways,  (T,pH,     (metal
          transport)  O2,salt)   profile)
              │          │          │
              ▼          ▼          ▼
    ┌─────────────────────────────────────┐
    │     DE NOVO RECIPE ASSEMBLER        │
    │                                     │
    │  1. Energy metabolism determination │
    │  2. Carbon source selection         │
    │  3. Nitrogen source selection       │
    │  4. Sulfur source selection         │
    │  5. Phosphate/buffer               │
    │  6. Vitamins/cofactors             │
    │  7. Trace metals                    │
    │  8. Base salts/osmolarity          │
    │  9. pH buffer                       │
    │  10. Atmosphere/gas phase          │
    │                                     │
    │     ↓ Concentration Calibration ↓   │
    │  (query MediaDive for metabolism-   │
    │   specific median concentrations)   │
    │                                     │
    │     ↓ Compatibility Check ↓         │
    │  (precipitation rules + remediation)│
    │                                     │
    │     ↓ Format Prediction ↓           │
    │  (solid/liquid/gradient/Hungate)    │
    └─────────────────────────────────────┘
              │                    │
              ▼                    ▼
    DE NOVO RECIPE          TEMPLATE COMPARISON
    (primary output)       (from phylo_match,
                            shown side-by-side)
```

---

## Module: `synthesize_denovo.py`

New file. Does NOT import from `synthesize_media.py` (which becomes the "legacy template" path). Both share `confidence.py`, `compatibility.py`, `media_format.py`, `carbon_and_gas.py`, and `thermodynamics.py`.

### Function Architecture

```python
def synthesize_denovo(conn, genome_id, user_overrides=None):
    """Top-level entry point. Returns a DeNovoRecipe object."""
    
    # Phase 1: Gather all genomic evidence
    evidence = gather_evidence(conn, genome_id)
    
    # Phase 2: Determine each recipe dimension
    energy   = determine_energy_metabolism(conn, evidence)
    carbon   = determine_carbon_source(conn, evidence, energy)
    nitrogen = determine_nitrogen_source(conn, evidence)
    sulfur   = determine_sulfur_source(conn, evidence)
    phosphate = determine_phosphate(conn, evidence)
    vitamins = determine_vitamin_supplements(conn, evidence)
    metals   = determine_trace_metals(conn, evidence)
    salts    = determine_base_salts(conn, evidence)
    buffer   = determine_buffer(conn, evidence)
    atmosphere = determine_atmosphere(conn, evidence, energy)
    
    # Phase 3: Calibrate concentrations from database
    recipe = calibrate_concentrations(conn, 
        [energy, carbon, nitrogen, sulfur, phosphate, 
         vitamins, metals, salts, buffer, atmosphere],
        evidence)
    
    # Phase 4: Apply user overrides
    if user_overrides:
        recipe = apply_overrides(recipe, user_overrides)
    
    # Phase 5: Checks
    recipe.compatibility = check_compatibility(...)
    recipe.format = predict_format(...)
    recipe.thermodynamics = check_viability(...)
    
    # Phase 6: Confidence composition
    recipe.overall_confidence = compose_confidence(recipe)
    
    return recipe
```

---

## Detailed Design Per Dimension

### 1. Energy Metabolism Determination

**Input:** `genome_pathways`, `genome_hydrogenases`, `genome_carbon_sources`

**Logic:**
```python
def determine_energy_metabolism(conn, evidence):
    """Infer the organism's primary energy metabolism from genomic evidence.
    
    Decision tree:
    1. Has methanogenesis pathways OR [NiFe] G3 hydrogenase → METHANOGEN
       - e-donor: H2(aq), e-acceptor: CO2(aq), autotrophic
    2. Has dissimilatory sulfate reduction pathway → SULFATE REDUCER
       - e-donor: organic acids or H2, e-acceptor: SO4²⁻
    3. Has iron reduction pathway (e.g., outer-membrane cytochromes) → IRON REDUCER
       - e-donor: acetate/organic, e-acceptor: Fe(III)
    4. Has sulfur oxidation pathways (sox, dsr reverse) → SULFUR OXIDIZER
       - e-donor: S⁰/thiosulfate/H₂S, e-acceptor: O2/NO3⁻
    5. Has nitrification (amoABC) → AMMONIA OXIDIZER
    6. Has denitrification (narGHI, nirS/K, norBC, nosZ) → DENITRIFIER
    7. Has aerobic respiration (cytochrome c oxidase) + organic carbon → AEROBIC HETEROTROPH
    8. Has fermentation pathways but no respiration → FERMENTER
    
    Returns: EnergyMetabolism object with:
      - type: str (methanogen/sulfate_reducer/iron_reducer/etc.)
      - electron_donor: str
      - electron_acceptor: str
      - is_autotrophic: bool
      - genomic_evidence: list of pathway names/completeness
      - confidence: ConfidenceScore
    """
```

**Existing code that feeds this:**
- `carbon_and_gas.get_gas_phase_recommendation()` already does parts of this (H₂ pathway detection, methanogen detection, SRB detection)
- `carbon_and_gas.get_carbon_profile()` identifies usable carbon substrates
- `genome_hydrogenases` table has BLAST-confirmed [NiFe]/[FeFe] types

**New implementation needed:**
- Pathway-to-metabolism classification logic (the decision tree above)
- Outer-membrane cytochrome detection for Geobacter-type iron reducers
- Autotrophy detection from CO₂ fixation pathway presence

**Key gapseq pathway patterns for autotrophy:**
```python
AUTOTROPHY_PATTERNS = [
    (r"Calvin-Benson-Bassham", "Calvin cycle"),
    (r"reductive acetyl coenzyme A pathway", "Wood-Ljungdahl"),
    (r"reductive citric acid cycle|reductive TCA", "rTCA cycle"),
    (r"3-hydroxypropionate", "3-HP bicycle"),
    (r"dicarboxylate/4-hydroxybutyrate", "DC/4-HB cycle"),
]
```

### 2. Carbon Source Selection

**Input:** Energy metabolism determination, `genome_carbon_sources`, `genome_pathways`

**Logic:**
```python
def determine_carbon_source(conn, evidence, energy):
    """Select the primary carbon source based on metabolic type.
    
    If autotrophic:
      - Carbon source = CO2 (provided as NaHCO3 or CO2 gas phase)
      - No organic carbon in medium
      - Confidence HIGH if CO2 fixation pathway is >80% complete
    
    If heterotrophic:
      - Query genome_carbon_sources for the organism
      - Rank by: (a) pathway completeness, (b) prevalence in related 
        organisms' media, (c) simplicity (simple sugars > complex polymers)
      - For SRBs: prefer lactate/pyruvate/acetate (classic SRB substrates)
      - For fermenters: prefer glucose/sugars
      - For aerobes: prefer glucose (universal)
    
    Returns: CarbonSource object with compound, concentration, role, 
             genomic_evidence, confidence
    """
```

**Existing code:** `carbon_and_gas.get_carbon_profile()` already extracts 40+ carbon substrates from gapseq pathways.

**New implementation needed:**
- Ranking logic (prefer simple substrates, match to metabolism type)
- Autotroph override (if autotroph → CO₂ only, remove organic carbon)

### 3. Nitrogen Source

**Input:** `genome_pathways`, `genome_transporters`

**Logic:**
```python
def determine_nitrogen_source(conn, evidence):
    """Select nitrogen source from genomic evidence.
    
    Decision tree:
    1. nifHDK (nitrogen fixation) present AND predicted=true 
       → organism can fix N2, but NH4Cl is easier/cheaper for cultivation
       → use NH4Cl (standard), note N2 fixation capability
    2. Assimilatory nitrate reductase (nasA/narB) present
       → can use NO3⁻ as N source
       → use NH4Cl (simpler) unless user specifies otherwise
    3. Ammonium transporter (amtB) present
       → can import NH4⁺
       → use NH4Cl (preferred)
    4. Amino acid auxotrophies detected
       → needs organic nitrogen (yeast extract / peptone)
       → add complex nitrogen source
    
    Default: NH4Cl 0.5-1.0 g/L (universal for most prokaryotes)
    
    Returns: NitrogenSource object
    """
```

**Existing code:** `genome_pathways` has nitrogen fixation pathways; `genome_transporters` has ammonium transporter annotations.

**New query needed:**
```sql
-- Check for nitrogen fixation
SELECT pathway_name, completeness FROM genome_pathways
WHERE genome_id = ? AND lower(pathway_name) LIKE '%nitrogen fixation%'
  AND (predicted = 1 OR completeness >= 75)

-- Check for ammonium transporter
SELECT substrate, COUNT(*) FROM genome_transporters
WHERE genome_id = ? AND lower(substrate) LIKE '%ammoni%'
GROUP BY substrate
```

### 4. Sulfur Source

**Input:** `genome_pathways`, energy metabolism determination

**Logic:**
```python
def determine_sulfur_source(conn, evidence, energy):
    """Select sulfur source.
    
    1. If energy metabolism uses sulfate (SRB, sulfur oxidizer)
       → sulfate is both electron acceptor AND sulfur source
       → already provided via Na2SO4 from energy determination
    2. Sulfate assimilation pathway present (cysNDC, sat, aprAB)
       → can assimilate SO4²⁻ for biosynthesis
       → MgSO4 provides both Mg²⁺ and SO4²⁻ (standard)
    3. Cysteine biosynthesis incomplete (auxotrophy for cysteine)
       → needs organic sulfur (cysteine supplement)
    
    Default: MgSO4 0.2-1.0 g/L (provides Mg + S)
    
    Returns: SulfurSource object
    """
```

**Existing code:** Cysteine auxotrophy is already detected by `genome_auxotrophies` view.

### 5. Phosphate/Buffer

**Input:** `genome_transporters`, `genome_growth_predictions` (pH)

**Logic:**
```python
def determine_phosphate(conn, evidence):
    """Select phosphate source and concentration.
    
    Phosphate transporters indicate phosphate acquisition strategy:
    - High-affinity pst system → organism lives in P-limited environment
      → use lower phosphate (0.1-0.3 g/L)
    - Low-affinity pit system → normal P availability
      → standard phosphate (0.3-0.5 g/L)
    
    Buffer selection based on predicted pH:
    - pH 5.5-7.5 → KH2PO4/K2HPO4 (phosphate buffer, pKa 7.2)
    - pH 7.5-9.0 → NaHCO3/Na2CO3 (carbonate buffer, pKa 10.3)
    - pH <5.5 → MES (pKa 6.1) or citrate buffer
    - pH >9.0 → CAPS (pKa 10.4) or carbonate
    
    Returns: PhosphateBuffer object
    """
```

**New query needed:**
```sql
-- Check for phosphate transporters
SELECT substrate, COUNT(*) FROM genome_transporters
WHERE genome_id = ? AND lower(substrate) LIKE '%phosphat%'
GROUP BY substrate
```

### 6-7. Vitamins/Cofactors and Trace Metals

**Already fully implemented:**
- Vitamins: `genome_auxotrophies` view → `add_auxotrophy_supplements()` → `COFACTOR_CONCENTRATION_OVERRIDES`
- Metals: `genome_metal_profile` → `add_metal_supplements()` → `METAL_SUPPLEMENT` table

**Changes needed:** Extract these functions from `synthesize_media.py` into standalone callables that don't require a template.

### 8. Base Salts / Osmolarity

**Input:** `genome_growth_predictions` (salinity), `genome_pathways`

**Logic:**
```python
def determine_base_salts(conn, evidence):
    """Determine NaCl and base salt mixture from genomic evidence.
    
    1. GenomeSPOT salinity prediction → target NaCl concentration
    2. Compatible solute genes:
       - ectABC (ectoine biosynthesis) → moderate halophile (3-10% NaCl)
       - betAB (betaine biosynthesis) → moderate halophile
       - No compatible solute genes → freshwater or mild salt (<2% NaCl)
    3. Marine origin (phylogenetic context) → sea salts base (~3.5% NaCl)
    
    Standard base salts (beyond NaCl):
    - MgSO4·7H2O: 0.2-1.0 g/L (Mg + sulfate)
    - CaCl2·2H2O: 0.05-0.1 g/L (calcium)
    - KCl: 0.3-0.5 g/L (potassium, if not via K2HPO4 buffer)
    
    Concentration calibration: query MediaDive for median NaCl in media
    used by organisms at similar salinity.
    
    Returns: BaseSalts object with compounds + concentrations
    """
```

**New pathway patterns needed:**
```python
HALOPHILE_MARKERS = [
    (r"ectoine biosynthesis", "moderate halophile"),
    (r"glycine betaine biosynthesis", "osmotic stress adaptation"),
]
```

### 9. pH Buffer — see §5 (combined with phosphate)

### 10. Atmosphere/Gas Phase — already implemented in `carbon_and_gas.get_gas_phase_recommendation()`

**Enhancement needed:** The current implementation now correctly handles methanogen detection ([NiFe] G3 alone triggers it). For the de novo synthesizer, the gas phase is a first-class output rather than a supplementary annotation.

---

## Concentration Calibration Engine

This is the key innovation that replaces template matching. Instead of copying concentrations from a specific medium, query MediaDive for **statistical concentration ranges** across all media used for organisms with similar metabolism.

### Database Queries

```python
def calibrate_concentration(conn, compound_name, metabolism_type=None, 
                            taxonomy_hint=None):
    """Query MediaDive for the median concentration of a compound
    across media used for organisms with similar characteristics.
    
    Strategy (try in order, fall back through):
    1. Exact organism species match → concentrations from its known media
    2. Same genus → median across genus media
    3. Same metabolism type → median across all media for that metabolism
       (e.g., "what concentration of Na2SO4 do sulfate reducers use?")
    4. Global median → across all media in the database
    
    Returns: (median_conc, p10, p90, n_data_points, source_level)
    """
```

**SQL for metabolism-specific calibration:**
```sql
-- Example: lactate concentration in media for sulfate reducers
SELECT mc.g_per_L 
FROM media_compounds mc
JOIN compounds c ON c.id = mc.compound_id
JOIN organism_media om ON om.media_id = mc.media_id
JOIN organisms o ON o.id = om.organism_id
WHERE lower(c.name) LIKE '%lactate%'
  AND mc.g_per_L > 0
  AND om.growth = 1
  AND lower(o.species) LIKE '%desulfo%'  -- metabolism proxy via taxonomy
ORDER BY mc.g_per_L
```

**Already validated:** The query above returns n=280 data points for lactate in Desulfovibrio media, with a median of 2.49 g/L — which matches the real Postgate Medium C value of 2.04 g/L. This proves the calibration approach works.

### Metabolism-to-taxonomy proxies

Since we can't directly query "organisms that do sulfate reduction" without running gapseq on every organism in the DB, we use taxonomy as a proxy:

```python
METABOLISM_TAXONOMY_PROXIES = {
    "sulfate_reducer": ["desulfo", "desulfur", "archaeoglobus"],
    "methanogen": ["methano", "methanococcus", "methanosarcina", "methanobacterium"],
    "iron_reducer": ["geobacter", "shewanella", "desulfuromonas"],
    "sulfur_oxidizer": ["thiobacillus", "acidithiobacillus", "sulfolobus", "sulfurimonas"],
    "fermenter": ["clostridium", "lactobacillus", "streptococcus"],
    "aerobic_heterotroph": None,  # too broad — use global median
}
```

---

## Existing Code Reuse Map

| Component | Current location | Reuse in de novo? | Changes needed |
|---|---|---|---|
| `get_carbon_profile()` | `carbon_and_gas.py` | ✓ direct reuse | None |
| `get_gas_phase_recommendation()` | `carbon_and_gas.py` | ✓ direct reuse | None |
| `get_auxotrophies()` | `predict_media.py` | ✓ extract to shared module | Minor refactor |
| `get_metal_profile()` | `predict_media.py` | ✓ extract to shared module | Minor refactor |
| `COFACTOR_CONCENTRATION_OVERRIDES` | `synthesize_media.py` | ✓ move to shared constants | Just move |
| `METAL_SUPPLEMENT` | `synthesize_media.py` | ✓ move to shared constants | Just move |
| `Component` class | `synthesize_media.py` | ✓ reuse as-is | None |
| `classify_role()` | `synthesize_media.py` | ✓ reuse for output formatting | None |
| `check_compatibility()` | `compatibility.py` | ✓ direct reuse | None |
| `predict_format()` | `media_format.py` | ✓ direct reuse | None |
| `check_thermodynamic_viability()` | `synthesize_media.py` | ✓ extract to `thermodynamics.py` | Move |
| `compose_overall_confidence()` | `synthesize_media.py` | ✓ reuse pattern | Adapt for de novo components |
| `build_variation_matrix()` | `synthesize_media.py` | ✓ reuse as-is | None |
| `generate_prep_instructions()` | `compatibility.py` | ✓ direct reuse | None |
| `rank_candidate_media()` | `phylo_match.py` | ✓ for template comparison side | None |

**New code needed:**

| Module | Purpose | Est. size |
|---|---|---|
| `synthesize_denovo.py` | Main de novo pipeline | ~500 lines |
| `determine_metabolism()` | Energy metabolism decision tree | ~150 lines |
| `calibrate_concentrations()` | Database-backed concentration lookup | ~100 lines |
| `determine_nitrogen/sulfur/phosphate()` | N/S/P source selection | ~100 lines each |
| `determine_base_salts()` | Osmolarity + salt composition | ~80 lines |
| Updates to `carbon_and_gas.py` | Autotrophy detection, enhanced carbon ranking | ~50 lines |

---

## Output Format

The de novo recipe replaces the current "COMPONENTS" section with a genomically-justified breakdown:

```
================================================================================
  DE NOVO RECIPE — composed from genomic evidence
  Query: NC_002937.3 (Desulfovibrio vulgaris Hildenborough)
  Overall Confidence: HIGH (0.82)
================================================================================

  ENERGY METABOLISM: Sulfate reduction (dissimilatory)
    Electron donor:    Na-DL-lactate         2.5 g/L       [0.90]
      → gapseq: lactate oxidation pathway 100% complete
      → calibrated: median for Desulfovibrio media = 2.49 g/L (n=280)
    Electron acceptor: Na2SO4                3.0 g/L       [0.90]
      → gapseq: dissimilatory sulfate reduction 80% complete
      → calibrated: median for sulfate reducer media = 2.97 g/L (n=414)
    Thermodynamics:    ΔGr = -141 kJ/mol at 37°C → ✓ VIABLE

  CARBON SOURCE: Lactate (heterotrophic)
      → same as electron donor (common for SRBs)
      → genome also encodes: pyruvate, ethanol, formate, malate utilization
      → NOT autotrophic (no Calvin/WL/rTCA pathways detected)

  NITROGEN SOURCE: NH4Cl                    1.0 g/L       [0.85]
      → ammonium transporter detected (amtB)
      → no nitrogen fixation genes (nifHDK absent)
      → calibrated: median in SRB media = 0.99 g/L (n=450)

  SULFUR SOURCE: MgSO4·7H2O                2.0 g/L       [0.90]
      → sulfate is both electron acceptor and sulfur source
      → also provides Mg²⁺

  PHOSPHATE / BUFFER: K2HPO4                0.5 g/L       [0.85]
      → phosphate transporter (pst) detected
      → pH 7.0 buffer (phosphate pKa 7.2, good match)

  VITAMINS / COFACTORS:
      Thiamin (B1)                          1.0 mg/L      [0.72] ⚠
      Riboflavin (B2)                       1.0 mg/L      [0.72] ⚠
      → 10 auxotrophies detected; 8 covered by yeast extract below
      → 2 cofactors (heme, molybdopterin) as explicit supplements

  TRACE METALS (SL-10 equivalent):
      FeSO4·7H2O                            5.0 mg/L      [0.95]
      NiCl2·6H2O                            50 µg/L       [0.95] ⚠ elevated Ni (15.7%)
      MnCl2·4H2O                            500 µg/L      [0.95]
      ZnSO4·7H2O                            500 µg/L      [0.95]
      CoCl2·6H2O                            50 µg/L       [0.95]
      CuSO4·5H2O                            50 µg/L       [0.95]
      → MeBiPred: elevated Fe (19.4%) + Ni (15.7%) — consistent with
        [NiFe]-hydrogenases and cytochrome c₃

  BASE SALTS / OSMOLARITY:
      NaCl                                  1.0 g/L       [0.85]
      CaCl2·2H2O                            0.1 g/L       [0.85]
      → GenomeSPOT salinity: 0.75% NaCl (freshwater strain)
      → no ectoine/betaine genes (not halophilic)

  REDUCING AGENT:
      Na2S·9H2O                             0.5 g/L       [0.90]
      → strict anaerobe (GenomeSPOT O2 p=0.98)
      Resazurin                             0.5 mg/L
      → redox indicator (standard for anaerobic media)

  ATMOSPHERE: N2:CO2 (80:20)
      → strict anaerobe + heterotrophic sulfate reducer
      → [NiFe] G1 uptake hydrogenase detected — H2:CO2 option for
        lithoautotrophic growth test

  PHYSICAL FORMAT: Liquid in sealed tubes (Hungate/Balch)    [0.90]
      → strict anaerobe
  SOLIDIFYING AGENT: Agar 1.5% (T=37°C, pH 7.0 — within agar range)

================================================================================
  TEMPLATE COMPARISON (for reference)
================================================================================
  Nearest template: DESULFOVIBRIO (POSTGATE) MEDIUM (#63)
  16S identity to best relative: 99.8%
  Template match score: 0.95

  Side-by-side:
  Component          De novo         Template        Match?
  Lactate            2.5 g/L         2.04 g/L        ~ (similar)
  Na2SO4             3.0 g/L         1.02 g/L        ~ (de novo higher)
  NH4Cl              1.0 g/L         1.02 g/L        ✓ match
  K2HPO4             0.5 g/L         0.51 g/L        ✓ match
  MgSO4              2.0 g/L         2.04 g/L        ✓ match
  Yeast extract      —               1.02 g/L        ✗ (de novo omits)
  FeSO4              5.0 mg/L        500 mg/L        ✗ (template has more)
  Trace metals       SL-10 equiv     none            + (de novo adds)
  
  Agreement: 4/7 within 50% → GOOD agreement
  De novo advantages: trace metals, Ni supplement, calibrated SO4
  Template advantages: yeast extract (covers vitamins), higher Fe
================================================================================
```

---

## Implementation Order

1. **Extract shared code** from `synthesize_media.py` into importable functions (auxotrophies, metals, Component class, concentration overrides) — ~30 min
2. **Build `determine_energy_metabolism()`** decision tree — the core new logic — ~2 hr
3. **Build concentration calibration engine** — database queries with metabolism-proxy taxonomy — ~1 hr
4. **Build `determine_nitrogen/sulfur/phosphate/salts()`** — simpler decision trees — ~1 hr
5. **Build `synthesize_denovo.py` main pipeline** — wires everything together — ~2 hr
6. **Build template comparison** — call existing `rank_candidate_media()` + side-by-side diff — ~1 hr
7. **Test on all 12 validation organisms** — compare de novo vs template vs reality — ~2 hr
8. **Write up results** — update VALIDATION_SUMMARY.md with de novo accuracy — ~1 hr

**Estimated total: ~10-12 hours of implementation.**

---

## Key Design Decisions

### Why not just improve the template matching?

Template matching has a fundamental cold-start problem: for truly novel organisms with no close relative in the database, there's no template to match. The de novo approach works from first principles — if the genome encodes sulfate reduction, lactate oxidation, and requires iron, the recipe includes those things regardless of whether the organism has a cultivated relative.

### Why keep the template as a comparison?

The template comparison serves as a sanity check. When both approaches agree, confidence is high. When they disagree, the user can see exactly where and why — e.g., "the de novo recipe uses lactate at 2.5 g/L; the nearest template uses 2.0 g/L" — and make an informed choice.

### Why calibrate from the database instead of using fixed concentrations?

Fixed concentrations (e.g., "always use 2 g/L Na₂SO₄ for sulfate reducers") ignore the diversity of cultivation conditions. By querying the database, we get statistically grounded ranges: "sulfate reducer media use 0.15-4.25 g/L Na₂SO₄ (P10-P90), with a median of 2.97 g/L." This gives the user a well-informed starting point and a range for optimization.

### What happens for organisms with completely unknown metabolism?

If no energy metabolism can be determined (no respiratory or fermentation pathways detected — possible for very novel lineages):
1. Fall back to the template-based approach
2. Flag as LOW confidence
3. Recommend Tier 2 (structure-based) analysis to recover function from hypothetical proteins
