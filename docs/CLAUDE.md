# CultureForge — Unified Architecture & Implementation Plan

## Project Vision
AI platform that predicts cultivation media for novel uncultured bacteria and archaea by integrating structured media databases, genome-scale metabolic modeling, protein structure-based function prediction, environmental context, and LLM reasoning into a single unified database and prediction engine.

---

## Core Data Sources (Unified Database)

All data feeds into a single SQLite/PostgreSQL database with cross-linked tables.

### Tier 1 — Media & Organism Data (Phase 1, building now)
| Source | URL / Access | What It Provides | License |
|--------|-------------|------------------|---------|
| **MediaDive** | https://mediadive.dsmz.de/rest | 3,200+ media recipes, molecular compositions, preparation instructions for 40,000+ strains | CC BY 4.0 |
| **BacDive** | https://api.bacdive.dsmz.de | 100,000+ strains: phenotypic traits, cultivation conditions, API test results, isolation sources | Free, no registration |
| **TEMPURA** | https://togodb.org/db/tempura | Min/optimum/max growth temperatures for 8,639 prokaryotic strains, linked to taxonomy & genomes | CC BY 4.0 |
| **ProTraits** | Literature-inferred | Carbon source utilization for 3,000+ organisms (48 carbon sources), phenotypic traits | Academic |
| **BRENDA** | https://www.brenda-enzymes.org/download.php | Enzyme cofactor requirements, metal ion dependencies, kinetic data for 77,000+ enzymes from 30,000+ organisms | CC BY 4.0 |

### Tier 2 — Genomic & Metabolic Data (Phase 2)
| Source | URL / Access | What It Provides |
|--------|-------------|------------------|
| **gapseq** | https://github.com/jotech/gapseq | Metabolic pathway prediction, auxotrophy detection, metabolic model reconstruction from genomes/MAGs |
| **GenomeSPOT** | https://github.com/cultivarium/GenomeSPOT | Predicts oxygen, temperature, salinity, pH preferences directly from genome sequences |
| **KEGG** | https://www.genome.jp/kegg/ | Metabolic pathway maps, reaction databases, compound information |
| **MetaCyc** | https://metacyc.org/ | Curated metabolic pathways and reactions |

### Tier 3 — Structure-Based Function Prediction (Phase 2-3)
| Source | URL / Access | What It Provides |
|--------|-------------|------------------|
| **AlphaFold DB** | https://alphafold.ebi.ac.uk/ | 200+ million predicted protein structures, searchable via API |
| **ESM Metagenomic Atlas** | https://esmatlas.com/ | 600+ million predicted structures from uncultured microbes |
| **Foldseek** | https://search.foldseek.com/ | Ultra-fast structural similarity search (4-5 orders of magnitude faster than Dali/TM-align) |
| **ESMFold** | pip install esm | Fast structure prediction from sequence (no MSA needed), suitable for genome-scale analysis |
| **PDB** | https://www.rcsb.org/ | Experimentally determined protein structures with functional annotations |

### Supporting Resources
| Source | What It Provides |
|--------|------------------|
| **SILVA** | 16S/18S rRNA reference database for phylogenetic placement |
| **GTDB** | Genome Taxonomy Database with habitat metadata |
| **LPSN** | Prokaryotic nomenclature (API: https://lpsn.dsmz.de/text/lpsn-api) |
| **KG-Microbe** | Knowledge graph linking traits, environments, media, genomic data |
| **NCBI Taxonomy** | Taxonomic classification and phylogenetic context |

---

## Unified Database Schema

All data converges into one database with these core table groups:

### Media tables
- `media` — each medium recipe (id, name, source, pH, temperature, atmosphere)
- `compounds` — chemical components (name, CAS, ChEBI ID, formula, molecular weight, role)
- `media_compounds` — which compounds in which media at what concentration
- `media_solutions` — stock solutions and preparation steps

### Organism tables
- `organisms` — strain-level data (taxonomy, NCBI taxid, domain, phylum through species)
- `organism_media` — which organisms grow on which media (including negative results!)
- `organism_traits` — phenotypic data from BacDive, TEMPURA, ProTraits
- `organism_environments` — isolation source, habitat metadata, geochemistry

### Genomic tables
- `genomes` — genome/MAG metadata (accession, completeness, contamination, source)
- `genome_pathways` — gapseq pathway predictions (pathway ID, completeness, confidence)
- `genome_auxotrophies` — predicted nutritional requirements from missing pathways
- `genome_transporters` — predicted transport capabilities
- `genome_growth_predictions` — GenomeSPOT output (predicted temp, pH, salinity, O2)

### Protein structure tables
- `proteins` — predicted proteins from genomes (id, genome_id, sequence, annotation)
- `protein_structures` — ESMFold/AlphaFold structure predictions (pLDDT scores)
- `structure_hits` — Foldseek search results (target, TM-score, probability, function transfer)
- `cofactor_requirements` — BRENDA-derived cofactor/metal requirements for annotated enzymes

### Prediction & results tables
- `predictions` — CultureForge predictions (input organism, predicted recipe, confidence)
- `experiments` — user-reported results (grew/didn't grow/weak, modifications, conditions)
- `prediction_feedback` — links predictions to experimental outcomes for learning

---

## Three-Tiered Analysis Architecture

### Tier 1 — Sequence-Based Analysis (fast mode, ~5-15 minutes per genome with pre-computed reference data; 2-3 hr if running gapseq fresh)
**Input:** 16S rRNA sequence OR genome/MAG FASTA + environmental parameters
**Pipeline:**
1. **Phylogenetic placement** — BLAST/MMseqs2 against reference 16S database → find closest cultivated relatives → retrieve their known media
2. **gapseq pathway prediction** — if genome provided, predict metabolic pathways, carbon source utilization, fermentation products
3. **Auxotrophy prediction** — identify missing biosynthetic pathways for amino acids, vitamins, cofactors → predict required supplements
4. **GenomeSPOT** — predict optimal temperature, pH, salinity, O2 requirement from genome
5. **Environmental matching** — compare user-provided environment data against known cultivation conditions in database
6. **ProTraits cross-reference** — check carbon source utilization predictions against ProTraits data for phylogenetic neighbors
7. **BRENDA lookup** — for annotated enzymes, identify required cofactors and metal ions

**Output:** Primary media recipe + confidence scores + rationale for each component

### Tier 2 — Structure-Based Function Recovery (standard mode, ~1-3 hours per genome)
**Triggers:** User-selected via `--tier standard`. Operates on all proteins annotated as "hypothetical" by Tier 1 — or on a user-specified protein subset via `--proteins`. See Addendum 2 ("Tiered Compute System") for the CLI contract.
**Pipeline:**
1. **ESMFold** — predict 3D structure for each hypothetical protein (fast, seconds per protein)
2. **Foldseek search** — search predicted structures against AlphaFold DB + PDB + ESM Metagenomic Atlas
3. **Function transfer** — for high-confidence structural matches (probability >0.7, TM-score >0.5):
   - Transfer functional annotation from matched protein
   - Specifically flag: transporters, enzyme activities, cofactor-binding domains, electron transfer proteins
4. **Impact assessment** — determine if newly annotated functions change the media prediction:
   - New transporter identified → organism can import compound X → may not need to be synthesized
   - New enzyme activity → organism has metabolic capability missed by sequence
   - Cofactor-binding domain → specific metal ion requirement for medium

**Output:** Revised media recipe with structure-informed modifications flagged separately

### Tier 3 — Deep Structural Analysis (deep mode, ~4-12 hours per genome; typically user-initiated on specific proteins of interest via `--proteins`)
**Triggers:** User selects specific proteins of interest for deeper analysis
**Pipeline:**
1. **HHPred-style profile-profile search** — more sensitive than Foldseek for very remote homologs
2. **AlphaFold2/ColabFold** — higher-accuracy structure prediction with MSA (slower but better for unusual folds)
3. **Active site analysis** — for enzyme-like structures, predict substrate specificity
4. **Protein-ligand docking** — if relevant, predict which small molecules bind

**Output:** Detailed structural report for selected proteins with functional hypotheses

---

## Media Composition Synthesizer (Core Innovation)

Not just recommending existing media — composing novel recipes through constraint satisfaction:

### Input Assembly
1. **Template medium** — closest phylogenetic relative's known medium
2. **Auxotrophy supplements** — compounds for missing biosynthetic pathways
3. **Environmental constraints** — pH, temperature, salinity, atmosphere from source habitat
4. **Cofactor requirements** — metal ions and cofactors from BRENDA enzyme annotations
5. **Structure-informed modifications** — revised predictions from Tier 2 analysis
6. **Electron donor/acceptor support** — user-specified energy metabolism components

### Electron Donor/Acceptor Reference Table
For environments with specific energy metabolisms, auto-suggest required media components:

| Energy Metabolism | Electron Donor | Electron Acceptor | Media Components Needed |
|-------------------|---------------|-------------------|------------------------|
| Iron reduction | Organic acids, H2 | Fe(III) | Ferric citrate, ferrihydrite, poorly crystalline iron oxide |
| Sulfate reduction | Organic acids, H2, lactate | SO4²⁻ | Na2SO4, MgSO4 |
| Sulfur oxidation | H2S, S⁰, thiosulfate | O2, NO3⁻ | Na2S, elemental sulfur, Na2S2O3 |
| Methanogenesis | H2/CO2, acetate, methanol | CO2 | NaHCO3 + H2/CO2 gas phase |
| Iron oxidation | Fe(II) | O2, NO3⁻ | FeSO4, FeCl2 (anaerobic prep) |
| Ammonia oxidation | NH4⁺ | O2, NO2⁻ | NH4Cl |
| Denitrification | Various organic | NO3⁻ | KNO3, NaNO3 |
| Anammox | NH4⁺ | NO2⁻ | NH4Cl, NaNO2 |
| Hydrogen oxidation | H2 | O2, SO4²⁻, CO2, Fe(III) | H2/CO2 gas phase |
| Phototrophic | Light + H2S or organic | CO2 | Specific light conditions, NaHCO3 |

### Output
- Complete recipe with compound names, concentrations (g/L), and roles
- Confidence scores at component, recipe, and strategy levels
- Preparation instructions (order of addition, sterilization, anaerobic handling)
- Experimental variation matrix (what to test if primary recipe fails)
- Co-culture suggestions if syntrophic dependencies detected
- Literature references supporting each decision

---

## User Workflow

### Step 1: Input
User provides:
- 16S rRNA sequence OR genome/MAG FASTA file
- Source environment description:
  - Temperature, pH, salinity (**recommended**, not strictly required — if omitted, GenomeSPOT predicts these from the genome and they combine with TEMPURA/BacDive data via the multi-source agreement rules in Addendum 2; any user-supplied value overrides predictions with 0.95 confidence)
  - Light conditions (if relevant)
  - Redox potential / oxygen status
  - Dominant electron donors/acceptors (Fe species, S species, etc.)
  - Any other geochemistry (metals, nutrients, organic carbon)
- Optional: any prior cultivation observations
- Optional: target application (pure culture, enrichment, defined community)

### Step 2: Automated Analysis (Tier 1 + Tier 2)
- Phylogenetic placement → nearest cultivated relatives
- Metabolic model reconstruction (if genome provided)
- Auxotrophy prediction
- Growth condition prediction (GenomeSPOT)
- Structure-based function recovery for hypothetical proteins
- Environmental analog matching
- All results stream to user as they complete

### Step 3: Recipe Generation
- Primary medium recipe with full rationale
- 2-3 alternative formulations testing different metabolic hypotheses
- Experimental variation matrix for systematic testing
- Equipment and atmosphere requirements

### Step 4: Experimental Design
- Plate layout for combinatorial testing
- Downloadable protocol (PDF, ELN-compatible)
- QR code for mobile lab reference
- Incubation timeline suggestions

### Step 5: Results & Learning
- User logs growth/no-growth/weak growth
- Modification tracking
- Negative results explicitly captured
- System suggests next experiments based on results
- Active learning identifies most informative experiments to run

---

## Implementation Roadmap

### Phase 1 — Data Foundation (Weeks 1-6) ← CURRENTLY HERE
- [x] Download MediaDive media recipes via REST API
- [x] Download BacDive strain data via API
- [ ] Build unified SQLite database
- [ ] Download TEMPURA growth temperature data
- [ ] Download BRENDA enzyme cofactor data (JSON download, CC BY 4.0)
- [ ] Build 16S reference BLAST database
- [ ] Implement phylogenetic matching (16S → closest relatives → media)
- [ ] Validate: test with known organisms, check if correct media are predicted

### Phase 2 — Metabolic & Structural Intelligence (Weeks 7-14)
- [ ] Install gapseq, run on test genomes
- [ ] Build auxotrophy prediction pipeline
- [ ] Integrate GenomeSPOT for growth condition prediction
- [ ] Install ESMFold for fast structure prediction
- [ ] Implement Foldseek search pipeline (API or local)
- [ ] Build Tier 2 structure-based function recovery pipeline
- [ ] Build Media Composition Synthesizer
- [ ] Build electron donor/acceptor reference system
- [ ] Validate: compare predicted vs known media for well-studied organisms

### Phase 3 — Reasoning & Interface (Weeks 15-22)
- [ ] Build FastAPI backend connecting all modules
- [ ] Implement LLM reasoning layer (RAG over literature + recipe database)
- [ ] Build web interface (React) — or use Claude Code to generate it
- [ ] Add Tier 3 deep structural analysis (HHPred integration)
- [ ] Build feedback/results logging system
- [ ] Build experimental design generator

### Phase 4 — Learning & Community (Weeks 23+)
- [ ] Implement active learning for experiment prioritization
- [ ] Build community features (shared results, recipe sharing)
- [ ] Train graph neural network on accumulated data
- [ ] API for external tool integration (ELN, LIMS)
- [ ] Publication and release

---

## Technical Stack

### Data Layer
- SQLite for proof of concept → PostgreSQL for production
- All tables cross-linked via NCBI taxonomy IDs and compound identifiers (ChEBI)
- Vector database (later) for literature embeddings

### Compute Layer
- gapseq (conda) — metabolic model reconstruction
- GenomeSPOT (pip) — growth condition prediction from genome
- ESMFold (pip) — fast protein structure prediction
- Foldseek (conda or web API) — structural similarity search
- BLAST/MMseqs2 — sequence similarity search
- COBRApy — flux balance analysis on metabolic models

### AI/ML Layer
- RAG pipeline over literature + recipe database
- LLM reasoning for natural language recipe explanation
- Active learning module for experiment suggestion

### Interface Layer
- FastAPI backend
- React web frontend (Phase 3)
- Mobile-friendly recipe display
- Export: PDF protocols, CSV recipes, SBML models

---

## Key Papers
1. Oberhardt et al. (2015) Nature Comms — KOMODO/GROWREC, collaborative filtering for media prediction (83% accuracy)
2. Koblitz et al. (2023) NAR — MediaDive, expert-curated media database
3. Zimmermann et al. (2021) Genome Biology — gapseq, metabolic pathway prediction (80% accuracy)
4. Joachimiak et al. (2025) bioRxiv — KG-Microbe knowledge graph
5. Nichols et al. (2010) AEM — iChip in situ cultivation
6. Sato et al. (2020) — TEMPURA growth temperature database
7. Barnum et al. (2024) bioRxiv — GenomeSPOT, growth condition prediction from genomes
8. van Kempen et al. (2023) Nature Biotech — Foldseek, fast structural search
9. Lin et al. (2023) Science — ESMFold, language model protein structure prediction
10. Máša et al. (2025) ScienceDirect — Explainable rule-based media prediction with KG-Microbe
# CultureForge CLAUDE.md Addendum — Thermodynamic Energetics & Metal-Binding Prediction

---

## Reaction Energetics Engine (Amend & Shock 2001 Integration)

### Purpose
Before suggesting a media recipe, verify that the organism's proposed energy metabolism is thermodynamically viable at the user's specific temperature, pressure, and chemical composition. This prevents CultureForge from designing media for metabolisms that are energetically impossible under the given conditions.

### Data Source
Amend & Shock (2001) "Energetics of overall metabolic reactions of thermophilic and hyperthermophilic Archaea and Bacteria" — FEMS Microbiology Reviews 25: 175-243.

This paper provides:
- Standard molal Gibbs free energies (ΔG°r) as a function of temperature (2-200°C) for **370 metabolic reactions**
- Apparent standard molal Gibbs free energies of formation (ΔG°) for **307 compounds** (solids, liquids, gases, aqueous solutes)
- Temperature-dependent data at 12 reference points: 2, 18, 25, 37, 45, 55, 70, 85, 100, 115, 150, 200°C
- Framework for calculating overall Gibbs free energy (ΔGr) at specific environmental compositions

### What Gets Digitized Into the Database

#### Table: `thermodynamic_compounds` (307 entries)
Columns: compound_name, phase (solid/liquid/gas/aqueous), ΔG° at each temperature point, chemical_system (H-O, H-O-N, H-O-S, etc.)

Data from paper Tables:
- Table 4.1: H-O system compounds (O2, H2O, H2, etc.)
- Table 5.1: H-O-N system (NO3-, NO2-, NH4+, N2, etc.)
- Table 6.1: H-O-S system (SO4²-, H2S, S, thiosulfate, polysulfides, etc.)
- Table 7.1: H-O-C_inorganic system (CO2, CH4, CO, COS, HCN, etc.)
- Table 8.1: Organic compounds (carboxylic acids, alcohols, alkanes, amino acids)
- Table 9.1: Metal-containing compounds and minerals (Fe, Mn, Cu, Zn, As, Se, U, etc.)
- Table 9.8: H-O-P system (phosphate, pyrophosphate, phosphite, hypophosphite)

#### Table: `metabolic_reactions` (370+ entries)
Columns: reaction_id, reaction_equation, chemical_system, ΔG°r at each temperature point, reaction_type (redox/disproportionation/hydrolysis), organisms_known (from Tables 4.4, 5.4, 6.4, 6.7, 7.4, 8.4, 8.7, 8.10, 8.13, 9.4, 9.7)

Reaction groups from the paper:
- Table 4.2: H-O reactions (knallgas, peroxide reduction) — 2 reactions
- Table 5.2: Nitrogen reactions (denitrification, nitrate/nitrite reduction, N fixation, anammox) — 11 reactions
- Table 6.2: Sulfur reactions (sulfate reduction, sulfur oxidation, thiosulfate disproportionation) — 22 reactions
- Table 6.5: Mixed S-N reactions — 5 reactions
- Table 7.2: Inorganic carbon reactions (methanogenesis, CO oxidation, methanotrophy) — 9 reactions
- Table 8.2: Organic C reactions (acetogenesis, fermentation, aerobic oxidation) — 12 reactions
- Table 8.5: Organic C + N reactions — 14 reactions
- Table 8.8: Organic C + S reactions (heterotrophic sulfate reduction) — 96 reactions
- Table 8.11: Amino acid reactions — 10 reactions
- Table 9.2: Metal/mineral reactions (pyrite oxidation, iron reduction, uraninite) — 13 reactions
- Table 9.5: Organic C + metal reactions — 15 reactions
- Appendix tables: Gas solubility, dissociation, auxiliary redox, Cl-redox, mineral reactions — 150+ additional

### How It Integrates Into the Prediction Pipeline

#### Step 1: Identify proposed energy metabolism
From genome annotation (gapseq) and user input, determine the most likely metabolic strategy:
- What electron donors are available? (H2, organic acids, H2S, Fe²⁺, etc.)
- What electron acceptors are available? (O2, NO3⁻, SO4²⁻, Fe³⁺, S⁰, CO2, etc.)

#### Step 2: Look up ΔG°r at the organism's growth temperature
Interpolate between the 12 temperature reference points in the database.
Key insight from the paper: "values of ΔG°r for many microbially mediated reactions are highly temperature dependent, and adopting values determined at 25°C for systems at elevated temperatures introduces significant and unnecessary errors."

#### Step 3: Calculate actual ΔGr using environmental composition
Using the equation: ΔGr = ΔG°r + RT ln(Qr)
where Qr is the activity product calculated from the user's environmental chemistry data.

This is crucial — ΔG°r alone does NOT determine reaction direction. The paper demonstrates this with anaerobic acetic acid oxidation: ΔG° is positive (+35.9 kJ/mol at 100°C), but the actual ΔG at real environmental conditions is -70.2 kJ/mol (strongly exergonic).

#### Step 4: Apply to media design
- If ΔGr is strongly negative (< -20 kJ/mol): proposed metabolism is viable, design media to support it
- If ΔGr is marginally negative (-20 to 0 kJ/mol): metabolism is borderline, suggest increasing electron donor concentration or adjusting conditions
- If ΔGr is positive: metabolism is NOT viable under these conditions, suggest alternative metabolisms or different media composition
- Flag reactions where temperature changes significantly affect ΔGr (guide incubation temperature selection)

#### Step 5: Optimize media composition for maximum energy yield
Use the Amend & Shock contour plots as a model: for a given reaction, calculate ΔGr across a range of reactant/product concentrations to find the media composition that maximizes available energy. This is novel — no existing tool does this.

### Important Thermodynamic Considerations (from the paper)

1. **pH and neutrality shift with temperature**: Neutral pH drops from ~7.4 at 0°C to ~5.6 at 200°C. pH 7 has no special significance at non-standard temperatures. Media pH must be set considering this.

2. **Speciation changes with temperature**: At neutral pH and 80°C, dissolved CO2 replaces HCO3⁻ as the dominant carbonate species. H2S increasingly dominates over HS⁻ with increasing temperature. These affect which chemical forms to use in media recipes.

3. **Gas solubility is temperature-dependent**: H2 is >2x more soluble at 200°C than at 50°C (unusual). CO2 solubility drops ~8x from 0°C to 200°C. This affects headspace gas composition design.

4. **Pressure effects are secondary to temperature**: For most biological conditions, temperature effects on ΔG° dominate over pressure effects. But for deep-sea organisms, pressure corrections may matter.

---

## Metal-Binding Prediction (MeBiPred Integration)

### Purpose
Predict which metal ions an organism's proteins require, directly from protein sequences. This determines which trace metals and their concentrations should be included in the cultivation medium.

### Data Sources

**Primary: MeBiPred**
- Web server: https://services.bromberglab.org/mebipred/home
- Standalone package: `pip install mymetal`
- Predicts binding for **10 metal ions**: Ca, Co, Cu, Fe, K, Mg, Mn, Na, Ni, Zn. Note: the trained model does NOT cover Mo, W, V, or Se — requirements for those metals are populated via BRENDA / AlphaFill cross-reference (see "Metals populated via supplementary sources" below).
- ~90% accurate in recognizing metal-binding proteins
- Reference-free (no alignments needed) — fast enough for genome-scale analysis
- Can work on short sequences (translated reads from metagenomes)
- Published: Aptekmann et al. (2022) Bioinformatics 38(14):3532

**Supplementary: AlphaFill**
- Enriches AlphaFold models with ligands and cofactors from experimental data
- Provides metal ion placements in predicted structures
- URL: https://alphafill.eu

**Supplementary: BRENDA**
- Experimentally validated cofactor and metal requirements for classified enzymes
- Cross-reference with MeBiPred predictions for annotated proteins

### How It Integrates Into the Prediction Pipeline

#### Tier 1 Analysis (fast, all proteins)
1. Run MeBiPred on all predicted proteins from the genome/MAG
2. Generate a **metal requirement profile**: count of proteins predicted to bind each metal ion
3. Cross-reference annotated enzymes against BRENDA for experimentally validated cofactor requirements
4. Output: ranked list of required metal ions with confidence scores

#### Tier 2 Analysis (hypothetical proteins only)
1. For proteins with no functional annotation, MeBiPred predictions are especially valuable
2. A hypothetical protein predicted to bind iron tells us something about the organism's iron dependency even when we don't know what the protein does
3. Combine with Foldseek structural hits: if a hypothetical protein structurally resembles a known metalloenzyme AND MeBiPred predicts the same metal binding, confidence is high

#### Translation to Media Components

**Metals predicted directly by MeBiPred (10):**

| Predicted Metal | Media Component(s) | Typical Concentration |
|----------------|--------------------|-----------------------|
| Fe (iron) | FeSO4·7H2O or FeCl2·4H2O (anaerobic), FeCl3·6H2O (aerobic) | 0.001-0.01 g/L |
| Zn (zinc) | ZnSO4·7H2O | 0.0001-0.001 g/L |
| Mn (manganese) | MnCl2·4H2O or MnSO4·H2O | 0.0001-0.001 g/L |
| Cu (copper) | CuSO4·5H2O or CuCl2·2H2O | 0.00001-0.0001 g/L |
| Co (cobalt) | CoCl2·6H2O | 0.00001-0.0001 g/L |
| Ni (nickel) | NiCl2·6H2O | 0.00001-0.0001 g/L |
| Mg (magnesium) | MgSO4·7H2O or MgCl2·6H2O | 0.1-1.0 g/L |
| Ca (calcium) | CaCl2·2H2O | 0.01-0.1 g/L |
| K (potassium) | KCl or K2HPO4 | 0.1-1.0 g/L (often via buffer) |
| Na (sodium) | NaCl | 0.1-5 g/L (organism-dependent) |

**Metals populated via supplementary sources — NOT in the MeBiPred model:**

| Metal | Media Component(s) | Typical Concentration | Evidence Source |
|-------|--------------------|-----------------------|-----------------|
| Mo (molybdenum) | Na2MoO4·2H2O | 0.00001-0.0001 g/L | BRENDA (molybdopterin enzymes: nitrate reductase, XDH, etc.) |
| W (tungsten) | Na2WO4·2H2O | 0.00001-0.0001 g/L | BRENDA (tungsten-containing AOR / FOR in hyperthermophiles) |
| Se (selenium) | Na2SeO3 | 0.000001-0.00001 g/L | BRENDA (selenocysteine/selenoprotein residue patterns) |
| V (vanadium) | Na3VO4 | 0.00001-0.0001 g/L | BRENDA (vanadium nitrogenase, V-haloperoxidases) |

BRENDA integration is pending; until it lands, requirements for these four metals must be inferred manually from the organism's lineage and known physiology.

#### Novel Feature: Metal Requirement Anomaly Detection

For the 10 metals MeBiPred covers, flag an organism when its predicted binding fraction exceeds a typical-proteome ceiling for that metal (implemented as `_check_anomaly` in `load_mebipred.py`). Current rules:
- Fraction of proteome binding the metal > typical ceiling → flag (e.g. Ni >10%, Cu >10%)
- `max_p > 0.95` on a rare-metal classifier (Cu, Co, Ni) → flag — verify against BRENDA

For the four rarer metals NOT in the MeBiPred model — **Mo, W, V, Se** — anomaly detection requires BRENDA cross-reference against known metalloenzyme families. The canonical example is tungsten: many hyperthermophilic methanogens require tungsten (for the tungsten-containing formaldehyde ferredoxin oxidoreductase / aldehyde oxidoreductase family), which is absent from most standard trace-element solutions. Detecting this requires scanning the predicted proteome against BRENDA's W-containing enzyme entries — MeBiPred alone cannot. Until BRENDA integration lands, these organisms need manual annotation.

### Database Tables

#### Table: `protein_metal_binding` (from MeBiPred)
Columns: protein_id, genome_id, metal_ion, binding_probability, binding_residues

#### Table: `genome_metal_profile` (aggregated)
Columns: genome_id, metal_ion, num_binding_proteins, fraction_of_proteome, confidence, media_implication

---

## Updated Implementation Roadmap Additions

### Phase 1 additions:
- [ ] Digitize Amend & Shock Table 4.1 through Table 9.8 (ΔG° values for 307 compounds)
- [ ] Digitize reaction tables (ΔG°r values for 370 reactions)
- [ ] Digitize organism-reaction tables (which organisms do which reactions)
- [ ] Build interpolation function for ΔG° at arbitrary temperatures
- [ ] Build ΔGr calculator: ΔG°r + RT ln(Qr)

### Phase 2 additions:
- [ ] Install MeBiPred: `pip install mymetal`
- [ ] Build pipeline: genome → predicted proteins → MeBiPred → metal profile → trace element recipe
- [ ] Integrate with BRENDA cofactor data for validation
- [ ] Build Reaction Energetics Engine: user environment + proposed metabolism → ΔGr → viability assessment
- [ ] Add thermodynamic viability check to Media Composition Synthesizer

### Phase 3 additions:
- [ ] Visualize energy landscapes: interactive ΔGr contour plots for proposed metabolisms
- [ ] Compare trace element requirements across related organisms
- [ ] Auto-generate non-standard trace element solutions for organisms with unusual metal profiles

---

## Key Papers to Add

11. Amend & Shock (2001) FEMS Microbiol Rev — Thermodynamic data for 370 metabolic reactions at temperatures to 200°C
12. Aptekmann et al. (2022) Bioinformatics — MeBiPred, metal-binding prediction from protein sequence (~90% accuracy)
13. Thauer et al. (1977) Bacteriol Rev — Classic reference for energy conservation in chemotrophic anaerobes (25°C baseline that Amend & Shock extend)
# CultureForge CLAUDE.md Addendum — Confidence Framework & Tiered Compute System

---

## Design Philosophy

CultureForge must be **transparent**, not a black box. Every prediction it makes must be traceable back to its source, and every recipe component must carry a confidence score. Users — experimental microbiologists — need to know which parts of a recipe to trust and which parts to vary experimentally. A 70% confidence score tells the user "try this but also test alternatives"; a 95% confidence score tells the user "this is well-supported by multiple lines of evidence."

---

## Confidence Scoring Framework

### Core Principle
Every piece of data and every prediction in CultureForge carries a confidence score between 0.0 and 1.0. These scores propagate through the pipeline and combine into final recipe confidence. This must be implemented as a shared module that ALL prediction components use.

### Module: `confidence.py`
Build this as a central Python module that all other components import. Every component that generates predictions must call into this module rather than inventing its own scoring.

**API:**
```python
from confidence import score, combine, explain

# Score a single prediction
conf = score(
    source="gapseq",              # which data source / tool
    metric_type="pathway_completeness",
    raw_value=0.87,               # the raw metric from the tool
    context={                      # any relevant context
        "organism_distance": 0.92,
        "validation_organism": "E. coli",
        "n_reactions": 15
    }
)
# Returns: ConfidenceScore(value=0.83, source="gapseq", rationale="...")

# Combine multiple confidences (for composite predictions)
combined = combine(
    method="min",      # "min", "mean", "weighted_mean", or "independent"
    scores=[conf1, conf2, conf3],
    weights=[0.5, 0.3, 0.2]  # optional, required for weighted_mean
)

# Generate human-readable explanation
text = explain(conf)
# Returns: "83% - gapseq pathway completeness (87%), validated against E. coli"
```

### Source-Level Baseline Confidence

Each data source has an intrinsic reliability that modulates all predictions derived from it:

| Source | Baseline | Rationale |
|--------|----------|-----------|
| MediaDive media recipes | 0.95 | Expert-curated from published protocols |
| BacDive phenotypic (experimental) | 0.90 | Direct experimental observations |
| BacDive phenotypic (inferred) | 0.70 | Predicted from related strains |
| TEMPURA growth temps (experimental) | 0.85 | Literature-sourced |
| TEMPURA growth temps (predicted) | 0.65 | Model-inferred |
| gapseq pathway predictions | 0.50-0.95 | Scales with completeness % and bitscore |
| GenomeSPOT predictions | 0.50-0.95 | Uses reported probability |
| MeBiPred predictions | 0.50-0.90 | Uses reported probability (~90% accuracy baseline) |
| BRENDA enzyme data | 0.90 | Experimentally characterized enzymes |
| ESMFold structures | 0.30-0.95 | Uses pLDDT score (confidence threshold 0.7) |
| Foldseek hits | 0.40-0.95 | Uses probability + TM-score |
| AlphaFold DB structures | 0.50-0.95 | Uses pLDDT score |
| HHPred matches | 0.40-0.95 | Uses probability score |
| Amend & Shock thermodynamic data | 0.90 | Peer-reviewed thermodynamic measurements |
| User-supplied environmental data | 0.95 | Trust the experimentalist |

Store these in a `source_confidence` reference table in the database so they're adjustable without code changes.

### Prediction-Level Confidence Rules

**Phylogenetic matching confidence** depends on 16S identity percentage:
- ≥97% identity → 0.90-0.95 (species-level, reliable)
- 90-97% identity → 0.70-0.90 (genus-level)
- 85-90% identity → 0.50-0.70 (family-level)
- <85% identity → 0.30-0.50 (phylum-level, low confidence)

Already partially implemented as LOW/GOOD flags — upgrade to continuous scoring.

**Metabolic prediction confidence** uses gapseq's reported metrics:
- Pathway completeness ≥90% AND predicted=TRUE → 0.90-0.95
- Pathway completeness 75-90% OR predicted=TRUE → 0.70-0.90
- Pathway completeness 50-75% → 0.40-0.70
- Pathway completeness <50% → 0.20-0.40

Modulate by organism phylogenetic distance from well-characterized organisms.

**Environmental condition confidence** from multiple sources combines:
- GenomeSPOT and TEMPURA and BacDive all agree → 0.95
- Two of three agree → 0.85
- Only one source available → 0.70
- Sources disagree → 0.50 (flag for user review)
- User-supplied override → 0.95 (override applies)

**Metal requirement confidence** uses MeBiPred probability directly, with boost when multiple proteins bind same metal:
- Single protein predicted with >0.8 probability → baseline MeBiPred score
- Multiple proteins binding same metal → +0.05 to +0.10 boost (cap at 0.95)
- BRENDA cross-reference confirms → +0.05 boost

**Structural analysis confidence (Tier 2/3)** combines:
- ESMFold pLDDT ≥0.7 → acceptable prediction quality
- Foldseek probability ≥0.7 AND TM-score ≥0.5 → strong structural homology
- Multiple independent hits to same fold → boost confidence
- Sequence homology ALSO detected → highest confidence (both methods agree)

### Recipe-Level Composite Confidence

Each recipe component carries its own confidence tag. The overall recipe confidence is computed as:

```
overall = min(critical_component_confidences) + agreement_bonus
```

Where:
- **Critical components** are: base salts, carbon source, electron donor/acceptor, required auxotrophy supplements, essential cofactors
- **Non-critical components** (e.g., pH buffer choice, specific trace element concentration within reasonable range) don't drag down overall confidence
- **Agreement bonus** (+0.05 to +0.10): when multiple independent methods predict the same requirement, confidence exceeds the minimum

### Required User-Facing Output

Every recipe recommendation MUST display:
1. Overall confidence score and category (LOW <0.60, MEDIUM 0.60-0.80, HIGH 0.80-0.95, VERY HIGH ≥0.95)
2. Per-component confidence with source rationale
3. Explicit uncertainty flags for any component with confidence <0.75
4. Recommended experimental variations for uncertain components
5. Complete provenance: which tools/databases contributed which predictions

Example output format:
```
================================================================================
RECOMMENDED MEDIUM: Modified Thermus 162 Medium
Overall Confidence: HIGH (0.85)
================================================================================

COMPONENTS:
  Base salts (Thermus 162 formulation)     [0.95] 
    → Direct phylogenetic match, 96.1% 16S identity to T. parvatiensis
  Trace metals SL-10                       [0.90] 
    → Standard for Thermus lineage + MeBiPred confirms Zn, Fe, Mn binding
  Tungsten supplement (Na2WO4, 10 μM)      [0.75] ⚠
    → MeBiPred predicts 3 W-binding proteins (unusual for lineage)
  Cysteine supplement (0.5 mM)             [0.80] ⚠
    → gapseq predicts partial cys biosynthesis gap (78% complete)
  pH 7.0 ± 0.3                             [0.90]
    → GenomeSPOT (0.92) + TEMPURA (pH 7.2) agree
  Temperature 70°C                         [0.95]
    → User-supplied, confirmed by TEMPURA range 60-80°C
  Anaerobic atmosphere                     [0.85]
    → Genome lacks terminal oxidases (gapseq)

⚠ UNCERTAINTY FLAGS:
  • Tungsten requirement is unusual for this lineage
    → RECOMMENDATION: Test variants with and without Na2WO4
  • Cysteine biosynthesis gap is partial (may be functional)
    → RECOMMENDATION: Test variants with 0, 0.25, 0.5 mM cysteine

PROVENANCE:
  Phylogenetic match: MediaDive + BacDive (16S BLAST)
  Metabolic analysis: gapseq v1.2 (pathway completeness + transporters)
  Environmental: GenomeSPOT + TEMPURA + user override
  Metal requirements: MeBiPred v2.0 + BRENDA cross-reference
  Thermodynamic check: Amend & Shock 2001 data, ΔG at 70°C = -45 kJ/mol ✓
================================================================================
```

### Database Schema Additions

Add these tables to support confidence tracking:

**Table: `source_confidence`** (reference table, pre-populated)
Columns: source_name, subtype, baseline_confidence, rationale, last_updated

**Table: `prediction_confidences`** (per-prediction tracking)
Columns: id, prediction_type, source, raw_value, context_json, computed_confidence, explanation, created_at

**Table: `recipe_components`** (new — per-component breakdown of each recipe)
Columns: id, prediction_id (FK → predictions), component_name, compound_name, concentration, concentration_units, role (base_salt / carbon_source / nitrogen_source / trace_metal / auxotrophy_supplement / electron_donor / electron_acceptor / buffer / other), component_confidence, confidence_source, uncertainty_flag, uncertainty_note

The main doc's `predictions` table stores one row per prediction with a reference to the full recipe; `recipe_components` decomposes that recipe so each individual compound carries its own confidence and provenance. Every entry in `recipe_components` should correspond to exactly one row added to `prediction_confidences`.

---

## Tiered Compute System

### User-Facing Tiers

Users select their compute tier when submitting a genome, trading wall-clock time for prediction rigor:

### Tier 1: Fast Mode (DEFAULT) — ~5-15 minutes per genome
**Use case:** Rapid screening, single-genome analysis by individual researchers, most users most of the time
**Components:**
- 16S phylogenetic matching
- gapseq metabolic analysis (pathway + transporter + auxotrophy prediction)
- GenomeSPOT growth condition prediction
- MeBiPred metal-binding prediction
- TEMPURA/BacDive trait lookup
- Environmental matching
- BRENDA cofactor cross-reference
- Thermodynamic viability check (Amend & Shock lookup)
- Media Composition Synthesis with confidence scoring

**Compute note:** gapseq currently takes ~2-3 hours but this can be parallelized. For Tier 1 to truly be "fast," we need either pre-computed gapseq results for common reference genomes OR accepting that Tier 1 is "same-day results" rather than "coffee-break results." Document this tradeoff clearly in the user interface.

### Tier 2: Standard Mode — ~1-3 hours per genome
**Use case:** Novel organisms where sequence-based annotation misses significant function, publication-quality predictions
**Everything in Tier 1, PLUS:**
- ESMFold structure prediction on all proteins annotated as "hypothetical" by Tier 1
- Foldseek search against AlphaFold DB + PDB + ESM Metagenomic Atlas
- Structure-based function transfer for high-confidence hits (probability ≥0.7, TM-score ≥0.5)
- Re-analysis of metabolic predictions incorporating newly-annotated proteins
- Upgraded confidence scores where structural evidence confirms sequence predictions

**Triggering specific Tier 2 actions:** Users can click/flag specific "hypothetical protein" entries from Tier 1 output to promote them to Tier 2 analysis individually, rather than running full Tier 2 on the whole genome.

### Tier 3: Deep Mode — ~4-12 hours per genome
**Use case:** Critical predictions needing maximum rigor, research publications, proteins of special interest
**Everything in Tier 2, PLUS:**
- HHPred profile-profile search for remaining unannotated proteins (more sensitive than Foldseek for distant homologs)
- AlphaFold2/ColabFold structure prediction for specific proteins of interest (higher accuracy than ESMFold)
- Active site analysis for putative enzymes
- Protein-ligand docking for key predicted binding sites
- Substrate specificity prediction

**Typical usage pattern:** User runs Tier 1 or 2 first, reviews the output, identifies 1-5 proteins of particular interest, then triggers Tier 3 analysis on just those specific proteins rather than the whole genome.

### Implementation: Command-Line Interface

```bash
# Default Tier 1
python predict_media.py <genome.fasta>

# Explicit tier
python predict_media.py <genome.fasta> --tier fast
python predict_media.py <genome.fasta> --tier standard
python predict_media.py <genome.fasta> --tier deep

# Tier 2 on specific proteins only (after Tier 1 has run)
python predict_media.py <genome.fasta> --tier standard --proteins protein_ids.txt

# Tier 3 on specific proteins
python predict_media.py <genome.fasta> --tier deep --proteins protein_ids.txt

# Environmental overrides
python predict_media.py <genome.fasta> --temperature 70 --pH 6.5 --salinity 0.5
```

### Implementation: Database Tracking

Track what's been computed for each genome so repeated runs don't redo work:

**Table: `genome_analyses`**
Columns: genome_id, tier_completed (1/2/3), tier1_timestamp, tier2_timestamp, tier3_timestamp, proteins_tier2 (JSON list), proteins_tier3 (JSON list), total_compute_seconds

When a user re-requests a prediction, the system checks this table and either:
- Returns cached results if the requested tier is already complete
- Runs only the additional components needed to reach the requested tier
- Respects protein-specific promotions (user selected specific proteins for deeper analysis)

### Server-Side Considerations (for eventual web deployment)

Single-user local installation (current state): no queueing needed, user waits synchronously.

Multi-user web deployment (future): must implement a job queue. Tier 1 jobs can run with ~10 concurrent workers on modest hardware. Tier 2 jobs need GPU access for ESMFold and should be queued with priority. Tier 3 jobs should require explicit user confirmation and perhaps a daily quota to prevent abuse.

Cache aggressively: pre-compute Tier 1 results for all reference genomes in the database. Pre-compute ESMFold structures for all proteins in the database. Re-use whenever possible.

---

## Integration with Existing Components

### Updates to `phylo_match.py`
Replace the existing LOW/GOOD flag system with calls to the confidence module. Every hit now carries a `ConfidenceScore` object rather than a flag string.

### Updates to Media Composition Synthesizer (when built)
Every component added to a recipe must carry its confidence. The synthesizer tracks provenance automatically and computes overall recipe confidence using the `combine()` API.

### Updates to Database Loaders
All data ingestion scripts must populate the `prediction_confidences` table as they load data. Current loader set:

- `build_database.py` — MediaDive media recipes + BacDive strain records (from `data/bacdive/strains/` + `data/mediadive/medium_strains/`) into `media`, `compounds`, `media_compounds`, `organisms`, `organism_media`
- `integrate_tempura.py` — TEMPURA growth-temperature data merged into `organisms` (fills T_opt gaps + adds min/max)
- `load_gapseq.py` — gapseq pathway/transporter output into `genome_pathways`, `genome_transporters`
- `load_genomespot.py` — GenomeSPOT predictions into `genome_growth_predictions`
- `load_mebipred.py` — MeBiPred per-protein predictions into `protein_metal_binding` + `genome_metal_profile`

Future loaders (when their data sources integrate): `load_brenda.py`, `load_protraits.py`, `load_silva.py`, and the Amend & Shock thermodynamics digitizer. Each should follow the same pattern: compute a `ConfidenceScore` for every row via `confidence.score()` and record it via `confidence.record()` with `related_table` + `related_id` set.

---

## Implementation Order

When building this out, follow this sequence:

1. **First:** Build `confidence.py` module with the core API (`score`, `combine`, `explain`). Pre-populate the source_confidence reference table. Write tests.

2. **Second:** Retrofit existing components (phylo_match.py, gapseq integration) to use the confidence module. Verify existing predictions still work and now carry proper confidence scores.

3. **Third:** Add each new component (GenomeSPOT, MeBiPred, thermodynamic engine) through the confidence framework from day one.

4. **Fourth:** Build the Media Composition Synthesizer that uses confidence-aware combination to produce final recipes.

5. **Fifth:** Implement the tier system as a wrapper around the existing pipeline. Tier 1 is the current default; Tier 2 adds ESMFold+Foldseek; Tier 3 adds HHPred+AlphaFold2.

Do NOT try to build the tier system before the confidence framework is in place — the tiers only make sense when users can see confidence scores improving as they move to higher tiers.

---

## Validation Criteria

The confidence system is working correctly when:

- A prototroph like E. coli on rich medium scores HIGH confidence (≥0.85)
- An organism with 95%+ 16S identity to well-characterized relatives scores HIGH
- An organism with 80-85% 16S identity scores MEDIUM (0.60-0.75) with appropriate uncertainty flags
- A novel organism with <80% identity to anything scores LOW (<0.60) and the system explicitly recommends Tier 2/3 analysis
- When user-supplied environmental data contradicts predictions, confidence drops appropriately and the system flags the disagreement
- Promoting to Tier 2/3 demonstrably improves confidence scores when structural evidence confirms sequence predictions
# CultureForge CLAUDE.md Addendum — Selective Suppression & Contaminant Inhibition

---

## Design Philosophy

Environmental microbiology frequently involves enrichment cultures where the target organism grows alongside persistent contaminants. A sulfide oxidizer may co-enrich with a nuisance sulfate reducer; a target methanogen may be outcompeted by acetogens; a target heterotroph may be overgrown by fast-growing environmental generalists.

The traditional solution relies on scattered domain expertise: "add molybdate to suppress sulfate reducers," "use 2-bromoethanesulfonate for methanogens," "lower the pH to select against this contaminant." This knowledge lives in experienced microbiologists' heads and scattered methods papers — nobody has systematized it.

CultureForge's selective suppression feature aims to fill this gap. Users submit both a target organism AND one or more contaminants; the system predicts media components that support the target while differentially inhibiting the contaminants. This is genuinely novel — no existing cultivation prediction tool attempts this.

---

## Feature Scope

**Tier placement:** Suppression runs as an **extension of Tier 1 (Fast Mode) output** — it is not a separate tier. The `--suppress` flag adds a *Selective Suppression Analysis* section to the standard recipe report. Suppression can also be requested while running Tier 2 or Tier 3 (it reuses whichever metabolic/structural predictions are available from the invoked tier) but does not by itself trigger extra compute beyond the selected tier.

### User Interface

```bash
# Single contaminant by genome
python predict_media.py target_genome.fasta --suppress contaminant_genome.fasta

# Multiple contaminants
python predict_media.py target.fasta \
  --suppress contam1.fasta \
  --suppress contam2.fasta

# Contaminant by taxonomy (when no genome available)
python predict_media.py target.fasta \
  --suppress-taxon "Desulfovibrio"

# Contaminant by 16S sequence
python predict_media.py target.fasta \
  --suppress-16s contaminant_16s.fasta
```

### Output Extension

When suppression is requested, the standard recipe output is extended with a new section:

```
================================================================================
SELECTIVE SUPPRESSION ANALYSIS
Target:      Thiobacillus denitrificans (sulfur oxidizer)
Contaminant: Desulfovibrio vulgaris (sulfate reducer)
================================================================================

RECOMMENDED SELECTIVE AGENTS:

  Sodium molybdate (Na2MoO4)                    [0.92] 
    Concentration: 20 mM
    Target effect:     No effect on sulfide oxidation pathway
    Contaminant block: Competitive inhibitor of ATP sulfurylase 
                       (blocks sulfate activation)
    Evidence: BRENDA EC 2.7.7.4 inhibitor data; classic method 
              (Oremland & Capone 1988)
    
  pH 6.5-7.0 (vs. typical 7.5-8.0)              [0.75]
    Target effect:     Within Thiobacillus tolerance range
    Contaminant block: Suboptimal for Desulfovibrio (prefers 7.0-7.8)
    Evidence: GenomeSPOT pH_min target=5.3, contaminant=6.2

⚠ SUPPRESSION UNCERTAINTY FLAGS:
  • Molybdate concentration may need adjustment for specific strains
    → RECOMMENDATION: Test 10, 20, 30 mM variants
  • pH-based selection is partial — combine with molybdate for stronger effect

POTENTIAL FALSE POSITIVES:
  Neither selective agent is predicted to affect the target organism's 
  core metabolism, but always verify growth rate on enriched medium 
  before committing to large-scale culture.
```

---

## Technical Architecture

### Data Sources Required

**1. BRENDA inhibitor data (primary source)**
BRENDA's existing database (already planned for cofactor integration) contains extensive inhibitor annotations: which compounds inhibit which enzymes at what concentrations, Ki values, and competitive vs. non-competitive mechanisms. Extract inhibitor-enzyme relationships into a dedicated table.

**2. Curated selective inhibitors table (CultureForge-specific)**
Build a curated reference table of classic selective agents used in microbial cultivation. This resource does not exist as a unified database anywhere — CultureForge will create it. Initial population should include:

- Molybdate (sulfate reducers, via ATP sulfurylase)
- 2-Bromoethanesulfonate / BES (methanogens, via methyl-CoM reductase)
- Chloramphenicol, streptomycin, kanamycin (bacteria vs. archaea at selective doses)
- Cycloheximide (eukaryotes vs. prokaryotes)
- Penicillin, ampicillin, vancomycin (Gram-positive vs. Gram-negative patterns)
- Sodium azide (selective at low concentrations against cytochrome oxidase)
- Tungstate (selective against molybdenum-dependent organisms)
- Chlorate (selective against nitrate reducers)
- Sodium selenite (selective against some enteric bacteria)
- Nystatin, amphotericin B (fungal suppression)
- pH-based selection (acidophile vs. neutrophile, alkaliphile selection)
- Temperature-based selection (thermophile enrichment, psychrophile protection)
- Specific carbon source exclusion (starving out metabolic groups)

Each entry should specify: target enzyme/process, target organism groups, typical working concentration, effective range, confounding factors, literature references.

**3. Environmental / physical selection factors**
Beyond chemical inhibitors, physical/environmental parameters can provide selection: temperature shifts, pH shifts, oxygen exclusion, specific light conditions, pressure, osmotic conditions. These are already partly modeled in CultureForge; the suppression module should leverage them.

### Database Schema Additions

**Table: `selective_inhibitors`** (curated reference)
Columns: id, compound_name, chemical_formula, cas_number, target_enzymes (JSON), target_organism_groups (JSON), typical_concentration_mM, concentration_range_min, concentration_range_max, mechanism, selectivity_notes, confounding_factors, references (JSON), confidence_baseline

**Table: `inhibitor_evidence`** (links inhibitors to specific organisms)
Columns: id, inhibitor_id, organism_id, evidence_type (BRENDA_direct/genomic_inferred/literature), strength, source, confidence, notes

**Table: `suppression_predictions`** (per-query cached results)
Columns: id, target_genome_id, contaminant_genome_id, recommended_inhibitors (JSON), confidence_overall, rationale, generated_at

### Core Algorithm

**Step 1: Differential metabolic analysis**
Run Tier 1 analysis (or retrieve cached results) for both target and contaminant. Extract:
- Predicted enzyme complement for each
- Predicted transporter complement for each
- Predicted growth conditions for each
- Predicted auxotrophies for each

**Step 2: Identify differential vulnerabilities**
For each enzyme in the contaminant's predicted metabolism, check:
- Is this enzyme ALSO in the target's metabolism? 
  - If yes: inhibitor would hit both → skip
  - If no or weak homology: inhibitor is potentially selective

For each metabolic pathway the contaminant uses:
- Does the target use the same pathway?
  - If different pathways achieve the same function: selective inhibition is possible
  - If same pathway: selective inhibition requires finding residue-level differences

**Step 3: Match vulnerabilities to known inhibitors**
Query BRENDA for inhibitors of the differentially-present enzymes.
Query the curated selective_inhibitors table for matches to the contaminant's organism group.
Cross-reference: are there known inhibitors that hit what the contaminant has but the target lacks?

**Step 4: Consider environmental selection**
Compare GenomeSPOT predictions for both organisms:
- Do temperature preferences differ? (select at edge of contaminant's range)
- Do pH preferences differ? (shift pH to disadvantage contaminant)
- Do salinity preferences differ? (add/remove salt)
- Do oxygen preferences differ? (modify atmosphere)

**Step 5: Verify against target organism**
For each candidate selective agent, verify that it does NOT affect the target:
- Check if target has the inhibited enzyme
- Check if target's homolog has the inhibitor-binding residues
- Check target's known inhibitor sensitivity from BRENDA if available

**Step 6: Compose suppression strategy with confidence**
Rank selective agents by:
- Strength of evidence that it blocks the contaminant
- Strength of evidence that it spares the target
- Multiple mechanisms > single mechanism
- Known use in published cultivation protocols > theoretical prediction

Combine multiple selective pressures (chemical + environmental) when complementary.

### Concentration Prediction

Getting the concentration right is critical. The system should provide:
- Typical literature concentration (from curated table)
- Suggested concentration range to test (usually 0.5×, 1×, 2× literature value)
- Upper limit where target might also be affected
- Lower limit below which contaminant suppression becomes unreliable

Example for molybdate against sulfate reducers:
- Typical: 20 mM Na2MoO4
- Range to test: 10, 20, 30 mM
- Upper limit concern: >50 mM may affect Mo-dependent enzymes in target
- Lower limit concern: <5 mM is often insufficient to fully suppress SRBs

### Integration with Confidence Framework

Every suppression prediction carries confidence scores:

**Differential vulnerability confidence:**
- Contaminant genome CONFIRMS has the target enzyme + target genome CONFIRMS lacks it → 0.90+
- Contaminant predicted via gapseq + target predicted via gapseq → 0.70-0.85
- Only homology-based inference → 0.50-0.70

**Inhibitor effectiveness confidence:**
- BRENDA direct evidence on this specific organism → 0.95
- BRENDA evidence on the enzyme family → 0.85
- Literature reports in cultivation methods → 0.90
- Theoretical prediction only → 0.60

**Overall suppression strategy confidence:**
- Multiple independent selective pressures agreeing → boost
- Single selective pressure with strong evidence → moderate confidence
- Multiple weak pressures → flag as experimental, recommend testing variants

---

## Implementation Priority

**Build LAST.** This feature is explicitly the final major capability to add. It depends on:
- ✓ Confidence framework (built)
- ✓ gapseq metabolic analysis (built)
- ✓ GenomeSPOT environmental prediction (built)
- ✗ BRENDA integration (not yet built — required)
- ✗ Media Composition Synthesizer (not yet built — required)
- ✗ Thermodynamic engine (not required but helpful for temperature-dependent inhibitor effectiveness)

The selective suppression feature slots in cleanly AFTER all core components are mature. Attempting to build it earlier would require retrofitting when those components land.

However, the architectural design above should be preserved in CLAUDE.md from now on so that intermediate components (especially BRENDA integration) are designed with suppression use cases in mind. Specifically:
- BRENDA integration should extract inhibitor data alongside cofactor data from day one
- Media Composition Synthesizer output format should accommodate a "selective agents" section
- Confidence framework should anticipate suppression-specific score types

---

## Scientific Context & Publication Value

This feature alone, if well-executed and experimentally validated, is publishable as a separate paper. The curated selective_inhibitors database would be a lasting community resource. The "predict inhibitors for enrichment cultures" concept is something microbiologists have asked about informally for decades but nobody has built.

Suggested validation approach when ready:
1. Compile 10-20 classical enrichment protocols from the literature that use selective inhibitors
2. Run CultureForge's suppression predictor on the same target/contaminant pairs
3. Compare system predictions to what experienced microbiologists actually used
4. Agreement validates the approach; disagreements may reveal either system bugs OR novel selective strategies worth testing

Target journals: *Applied and Environmental Microbiology*, *Applied Microbiology and Biotechnology*, or as a features paper in *mSystems*.

---

## Validation Criteria

The suppression feature is working correctly when:

- Target: sulfur oxidizer (Thiobacillus); Contaminant: sulfate reducer (Desulfovibrio) → recommends molybdate with HIGH confidence
- Target: hydrogenotrophic methanogen; Contaminant: acetogen → recommends BES with HIGH confidence  
- Target: archaeon; Contaminant: bacterium → recommends appropriate antibiotics with HIGH confidence
- Target: acidophile; Contaminant: neutrophile → recommends pH shift with HIGH confidence
- Target and contaminant are too metabolically similar → reports "no strong selective strategy identified" with LOW confidence rather than hallucinating inhibitors

False positive prevention is critical. The system must NEVER recommend an inhibitor that would also affect the target organism. When in doubt, the system should say "no reliable suppression strategy found" rather than guess.
# CultureForge CLAUDE.md Addendum — Carbon Utilization & Hydrogenase Databases

---

## Additional Tier 1 Data Sources

### CAZy / dbCAN — Carbohydrate-Active Enzymes

| Item | Detail |
|------|--------|
| **Source** | CAZy: https://www.cazy.org/ |
| **Annotation tool** | dbCAN3: https://bcb.unl.edu/dbCAN2/ (also available as `pip install dbcan` or `conda install -c bioconda dbcan`) |
| **What it provides** | Classification of all carbohydrate-active enzymes in a genome: glycoside hydrolases (GH), glycosyltransferases (GT), polysaccharide lyases (PL), carbohydrate esterases (CE), auxiliary activities (AA), carbohydrate-binding modules (CBM) |
| **License** | Free for academic use |
| **Runtime** | Minutes per genome (Tier 1 compatible) |

**Why it matters for media design:**

CAZy/dbCAN annotation directly determines which carbon sources the organism can utilize:

- Extensive GH families (cellulases, amylases, xylanases) → organism can grow on complex polysaccharides (cellulose, starch, xylan) → cheaper, more ecologically relevant carbon sources in medium
- No complex polysaccharide-degrading enzymes → organism needs simple sugars (glucose, fructose, etc.) or other defined carbon sources
- Specific GH families indicate specific substrates: GH13 (starch), GH5/GH9/GH48 (cellulose), GH10/GH11 (xylan), GH1/GH3 (various beta-glucosides), GH23/GH73 (peptidoglycan — may indicate predatory or scavenging lifestyle)
- CE families indicate ability to deacetylate various substrates
- PL families indicate ability to degrade pectin and other polyuronides

**Integration with existing components:**

- Complements gapseq pathway predictions: gapseq tells you which metabolic pathways exist, CAZy tells you which substrates can enter those pathways
- Complements transporter predictions: a transporter for cellobiose is only useful if the organism also has the CAZymes to produce cellobiose from cellulose
- Feeds into Media Composition Synthesizer: carbon source selection should consider both metabolic capability (gapseq) and substrate access (CAZy)
- Confidence scoring: dbCAN provides E-values and coverage metrics that map naturally into the confidence framework

**Database schema:**

**Table: `genome_cazymes`**
Columns: id, genome_id, cazyme_family (e.g., GH5), cazyme_subfamily, gene_id, dbcan_tool (HMMER/DIAMOND/eCAMI), evalue, coverage, substrate_class

**Table: `genome_carbon_sources`** (derived/aggregated)
Columns: id, genome_id, carbon_source, evidence_type (cazyme/transporter/pathway), n_supporting_genes, confidence

### Hydrogenase Database

| Item | Detail |
|------|--------|
| **Source** | https://www.archaea.bio/resources/bioinformatics/hydrogenase-database |
| **What it provides** | Classification of hydrogenases by type: [NiFe] (Group 1-4), [FeFe] (Groups A-F), [Fe]-only. Includes catalytic subunit sequences, phylogenetic classification, and functional annotations |
| **Scope** | Focused on archaeal hydrogenases but applicable to bacteria |

**Why it matters for media design:**

Hydrogenases are the gateway enzymes for H₂-based energy metabolism. Their presence and type directly determines cultivation conditions:

- **[NiFe] Group 1 (uptake hydrogenases)** → organism oxidizes H₂ as electron donor → ADD H₂ to headspace gas mix (typically 80:20 H₂:CO₂)
- **[NiFe] Group 2 (sensory/regulatory)** → organism senses H₂, may not use it as primary energy source
- **[NiFe] Group 3 (bidirectional/cofactor-coupled)** → organism can couple H₂ to NADP⁺/F420 reduction → relevant for methanogens and acetogens
- **[NiFe] Group 4 (energy-converting, membrane-bound)** → organism can generate or consume H₂ coupled to ion translocation → critical for energy conservation in many anaerobes
- **[FeFe] Group A (prototypical)** → organism produces H₂ fermentatively → may need H₂ removal (continuous flow or large headspace) to keep fermentation thermodynamically favorable
- **[FeFe] Group B/C (sensory)** → regulatory role
- **[Fe]-only (Hmd)** → specific to some methanogens, functions in methanogenesis

**Integration with existing components:**

- Directly informs electron donor/acceptor reference table in CLAUDE.md: presence of uptake [NiFe] hydrogenase → add H₂ to the headspace gas composition
- Feeds into thermodynamic engine: H₂-dependent reactions from Amend & Shock tables require knowing whether the organism actually has the enzymatic machinery to use H₂
- Connects to MeBiPred: hydrogenases require specific metals ([NiFe] needs Ni and Fe; [FeFe] needs Fe; [Fe]-only needs Fe) — cross-validates MeBiPred Ni predictions
- Informs Media Composition Synthesizer: gas phase composition (H₂:CO₂ ratio, N₂:CO₂ ratio, aerobic/anaerobic) is a critical recipe component

**Implementation approach:**

Two options for hydrogenase detection:
1. **HMM-based search** — build or obtain profile HMMs for each hydrogenase group's catalytic subunit, search against predicted proteins with hmmsearch. This is the most sensitive approach.
2. **BLAST against reference sequences** — download reference catalytic subunit sequences from the Hydrogenase Database, build a BLAST database, search predicted proteins. Simpler to implement.

Option 2 is sufficient for Tier 1; option 1 for Tier 2/3 if finer classification is needed.

**Database schema:**

**Table: `genome_hydrogenases`**
Columns: id, genome_id, gene_id, hydrogenase_type ([NiFe]/[FeFe]/[Fe]-only), group (1/2/3/4 for [NiFe]; A-F for [FeFe]), subunit (large/small/maturation), evidence_method (BLAST/HMM), evalue, pident, confidence

**Derived impact on recipe:**

| Hydrogenase type | Gas phase recommendation |
|-----------------|------------------------|
| [NiFe] Group 1 uptake | H₂:CO₂ 80:20 (or 4:1) at 1-2 bar overpressure |
| [NiFe] Group 3 F420-reducing | H₂:CO₂ 80:20 (methanogen standard) |
| [NiFe] Group 4 energy-converting | H₂:CO₂ or N₂:CO₂ depending on other metabolic predictions |
| [FeFe] Group A fermentative | N₂:CO₂ headspace (remove H₂ to favor fermentation thermodynamics) |
| [Fe]-only Hmd | H₂:CO₂ (methanogen conditions) |
| No hydrogenases detected | Headspace determined by other metabolic predictions |

---

## Implementation Priority

Both CAZy/dbCAN and the Hydrogenase Database are **Tier 1 additions** that should be integrated AFTER the Media Composition Synthesizer is working. They enhance recipe quality but are not blockers for the synthesizer's initial implementation.

Suggested order:
1. Media Composition Synthesizer (current priority)
2. Thermodynamic engine (Amend & Shock)
3. CAZy/dbCAN integration (carbon source selection)
4. Hydrogenase Database integration (gas phase selection)
5. BRENDA inhibitor data (for selective suppression)
6. Tier 2 structural analysis (ESMFold + Foldseek)
7. Selective suppression feature
8. SILVA database integration

Both CAZy/dbCAN and hydrogenase detection are estimated at one focused evening each — pip install, run on E. coli, load into database, connect to synthesizer carbon source / gas phase selection logic.
# CultureForge CLAUDE.md Addendum — Physical Media Format Prediction

---

## Physical Media Format Prediction

### Purpose
Not all organisms grow well in the same physical format. CultureForge should recommend whether to use solid agar plates, liquid broth, semi-solid gradient media, or specialized formats (roll tubes, Hungate tubes, gradient tubes, etc.) based on genomic and ecological evidence.

### Format Categories

| Format | Agar % | Typical Use | Key Organisms |
|--------|--------|-------------|---------------|
| Liquid broth | 0% | General cultivation, anaerobes in sealed vessels, planktonic organisms | Most organisms, especially strict anaerobes in Hungate/Balch tubes |
| Semi-solid | 0.15-0.4% | Microaerophiles, motile chemotactic organisms, gradient-dependent organisms | Campylobacter, Magnetospirillum, Aquaspirillum, many sulfide oxidizers |
| Soft agar overlay | 0.5-0.7% | Phage assays, some fastidious organisms, motility assessment | Used as overlay on base agar |
| Solid agar | 1.2-2.0% | Colony isolation, most aerobic heterotrophs, streak plates | Most culturable aerobes and facultative anaerobes |
| Roll tubes | 1.5-2.0% | Strict anaerobes requiring solid surface + anoxic conditions | Methanogens, Clostridia, many SRBs |
| Shake tubes | 0.5-1.0% | Microaerophiles needing spatial O₂ gradient in solid matrix | Microaerophilic iron oxidizers (Gallionella, Mariprofundus) |
| Gradient tubes | 0.15-0.5% | Organisms at redox interfaces (opposing e⁻ donor/acceptor gradients) | Sulfide-oxidizing bacteria at O₂/H₂S interface, iron oxidizers at Fe²⁺/O₂ interface |
| Gellan gum plates | 0.5-1.0% | Thermophiles and acidophiles (agar degrades at high T or low pH) | Thermus, Sulfolobus, most hyperthermophiles |
| Filter cultivation | N/A | Ultra-oligotrophs, slow growers, in situ-like conditions | Novel environmental isolates, SAR11-type organisms |

### Prediction Logic

**Decision tree based on genome + environmental data:**

```
1. Is the organism a strict anaerobe? (GenomeSPOT oxygen = "anaerobe")
   YES → Liquid in sealed tubes (Hungate/Balch) as default
         If colony isolation needed → Roll tubes or anaerobic chamber + plates
   
2. Is the organism a microaerophile? (GenomeSPOT oxygen = "microaerophile" 
   OR genome has high-affinity terminal oxidase cydAB but lacks low-affinity 
   cytochrome c oxidase)
   YES → Semi-solid gradient media (0.2-0.3% agar)
         Organism will form a band at preferred O₂ tension

3. Does the organism oxidize a reduced compound with O₂ or another 
   oxidant? (e.g., sulfide + O₂, Fe²⁺ + O₂, NH₄⁺ + O₂)
   YES → Gradient tubes: reduced compound in bottom agar, 
         oxidant diffusing from top
         Semi-solid (0.15-0.3% agar) for motile gradient organisms

4. Is the growth temperature > 65°C or pH < 3?
   YES → Gellan gum (Gelrite/Phytagel) instead of agar
         Agar hydrolyzes at high temperature and low pH
         Typical: 0.8-1.0% gellan gum + 1-3 mM MgCl₂ or CaCl₂ 
         (divalent cations required for gellan gum solidification)

5. Does the genome encode flagellar biosynthesis AND chemotaxis genes?
   (fliC, flgE, motA, motB + cheA, cheB, cheY, mcp genes)
   YES → Consider semi-solid media (0.2-0.4% agar) for initial 
         enrichment — motile organisms spread through semi-solid 
         and can be tracked/isolated from spreading zones

6. Is the organism predicted to be an oligotroph? (very few carbon 
   utilization pathways, limited CAZyme repertoire, slow predicted 
   growth rate)
   YES → Consider dilute media, filter cultivation, or extinction 
         dilution in liquid rather than rich agar plates

7. Default: Solid agar (1.5%) for aerobes/facultative anaerobes,
   liquid broth for anaerobes
```

### Genomic Markers for Format Prediction

**Detected by gapseq / prodigal annotation:**

| Marker Genes | Prediction | Confidence |
|-------------|------------|------------|
| fliC, flgE, flgK, motAB (flagellar biosynthesis + motor) | Motile → semi-solid may help | 0.75 |
| cheA, cheB, cheR, cheY, mcp (chemotaxis) | Chemotactic → semi-solid recommended | 0.80 |
| cydAB (cytochrome bd oxidase, high O₂ affinity) WITHOUT ctaABCDE (cytochrome c oxidase, low affinity) | Microaerophile → semi-solid/gradient | 0.80 |
| cydAB + ctaABCDE (both present) | Facultative → flexible format | 0.70 |
| No terminal oxidases detected | Strict anaerobe → liquid in sealed vessels | 0.85 |
| pilA, pilB, pilC (type IV pili) + biofilm genes | Surface-attacher → solid media or biocarriers | 0.70 |

### Integration with Existing Components

This feature extends the Media Composition Synthesizer output. After the recipe (compounds, concentrations, pH, temperature, atmosphere), add a section:

```
PHYSICAL FORMAT:
  Recommended: Semi-solid gradient tube (0.2% agar)         [0.85]
    → Genome encodes sulfide:quinone oxidoreductase (sqr) 
      + high-affinity terminal oxidase (cydAB)
    → Predicted microaerophilic sulfide oxidizer
    → Gradient: Na₂S (1 mM) in bottom agar, air headspace
    
  Alternative: Liquid culture in sealed serum bottle         [0.75]
    → If gradient cultivation is impractical
    → Provide O₂ at reduced partial pressure (2-5% O₂ in N₂)
    
  ⚠ Do NOT use standard aerobic agar plates
    → Predicted microaerophile will not grow at atmospheric O₂

  SOLIDIFYING AGENT:
    Agar (standard)                                          [0.90]
    → Growth temperature 45°C is within agar stability range
    → If agar inhibition suspected, try gellan gum (0.8% Gelrite 
      + 3 mM MgCl₂)
```

### Solidifying Agent Selection

| Condition | Recommended Agent | Concentration | Notes |
|-----------|------------------|---------------|-------|
| T < 65°C, pH 5-9 | Agar (Bacto, Noble, or Difco) | 1.2-2.0% | Standard, works for most organisms |
| T > 65°C | Gellan gum (Gelrite/Phytagel) | 0.5-1.0% | Requires 1-3 mM divalent cation (Mg²⁺ or Ca²⁺) for solidification |
| pH < 4 | Gellan gum | 0.5-0.8% | Agar hydrolyzes at low pH during autoclaving |
| Agar-sensitive organisms | Gellan gum or agarose (low-melt) | Variable | Some organisms are inhibited by agar impurities |
| Anaerobic + solid needed | Agar in roll tubes or Gelrite in anaerobic chamber | 1.5-2.0% | Maintain anoxic atmosphere throughout |

### Implementation Priority

This is a lightweight addition to the synthesizer — no new databases or tools required. The genomic markers can be detected from existing gapseq/prodigal annotations with simple gene name searches. Estimated effort: part of one evening, integrated directly into synthesize_media.py.

Build alongside or shortly after the CAZy/hydrogenase integration, since all three enhance the synthesizer's output quality without requiring major new infrastructure.

### Database Schema

**Table: `genome_motility_features`**
Columns: id, genome_id, has_flagella (bool), has_chemotaxis (bool), has_type4_pili (bool), terminal_oxidase_type (high_affinity/low_affinity/both/none), n_mcp_genes, confidence

No new reference table needed — the decision tree logic lives in the synthesizer code, referencing existing genome_pathways and genome annotation data.
# CultureForge CLAUDE.md Addendum — Media Compatibility & Precipitation Check

---

## Media Compatibility Engine (PHREEQC Integration)

### The Problem
Cultivation media often fail not because the wrong compounds are chosen, but because compounds react with each other and precipitate out of solution. Iron precipitates with phosphate (FePO₄, Fe₃(PO₄)₂). Calcium precipitates with carbonate (CaCO₃). Heavy metals crash out with sulfide (FeS, CuS, ZnS). Magnesium precipitates with phosphate at high pH (struvite, MgNH₄PO₄). These reactions remove essential nutrients from solution, starving organisms despite nominally adequate concentrations in the recipe.

Every experienced media chemist knows these incompatibilities and designs around them — separate sterilization of metal and phosphate solutions, chelator addition, pH adjustment timing. But no cultivation prediction tool incorporates this knowledge. CultureForge's Media Compatibility Engine fills this gap.

### Data Source & Tool

**PHREEQC** (US Geological Survey)
- URL: https://www.usgs.gov/software/phreeqc-version-3
- Python interface: `phreeqpython` (pip install phreeqpython) — object-oriented wrapper
- Alternative: `phreeqpy` (pip install phreeqpy) — lower-level IPhreeqc access
- Thermodynamic databases included: wateq4f.dat, llnl.dat, phreeqc.dat (cover all relevant mineral phases)
- License: Public domain (USGS)
- Capabilities: Aqueous speciation, saturation index calculation, mineral equilibrium, temperature-dependent solubility

PHREEQC calculates the saturation index (SI) for every mineral phase in its database given a solution composition, temperature, and pH. SI > 0 means the mineral is supersaturated (will precipitate). SI < 0 means undersaturated (will stay dissolved). SI ≈ 0 means at equilibrium.

### Two-Tiered Implementation

**Tier A: Fast rule-based check (milliseconds, always runs)**

A curated lookup table of known media incompatibilities. Catches the most common problems without requiring PHREEQC.

| Component A | Component B | Condition | Precipitate | Severity |
|------------|------------|-----------|-------------|----------|
| Fe²⁺/Fe³⁺ | PO₄³⁻/HPO₄²⁻ | pH > 5.5 | FePO₄, Fe₃(PO₄)₂ (vivianite) | HIGH |
| Fe²⁺/Fe³⁺ | S²⁻/HS⁻ | Any pH | FeS, FeS₂ | HIGH |
| Ca²⁺ | CO₃²⁻/HCO₃⁻ | pH > 7.5 | CaCO₃ (calcite) | MEDIUM |
| Ca²⁺ | PO₄³⁻ | pH > 6.5 | Ca₃(PO₄)₂ (apatite) | MEDIUM |
| Ca²⁺ | SO₄²⁻ | High conc. | CaSO₄ (gypsum) | LOW |
| Mg²⁺ | PO₄³⁻ + NH₄⁺ | pH > 8.0 | MgNH₄PO₄ (struvite) | MEDIUM |
| Mn²⁺ | CO₃²⁻ | pH > 7.5 | MnCO₃ (rhodochrosite) | MEDIUM |
| Cu²⁺ | S²⁻ | Any pH | CuS (covellite) | HIGH |
| Zn²⁺ | S²⁻ | Any pH | ZnS (sphalerite) | HIGH |
| Pb²⁺ | S²⁻ | Any pH | PbS (galena) | HIGH |
| Ni²⁺ | S²⁻ | Neutral-alkaline | NiS | HIGH |
| Co²⁺ | S²⁻ | Neutral-alkaline | CoS | HIGH |
| Al³⁺ | OH⁻ | pH > 5, pH < 3 | Al(OH)₃ | MEDIUM |
| Fe³⁺ | OH⁻ | pH > 3 | Fe(OH)₃ (ferrihydrite) | HIGH |

When the synthesizer produces a recipe, scan all compound pairs against this table. If a match is found, flag it with severity and suggest remediation.

**Tier B: Full PHREEQC speciation (seconds, runs on flagged recipes or user request)**

For recipes that trigger Tier A warnings, or for unusual compositions, run a full PHREEQC speciation calculation:

```python
from phreeqpython import PhreeqPython
pp = PhreeqPython()

# Define the complete medium as a PHREEQC solution
solution = pp.add_solution({
    'temp': 70,           # predicted growth temperature
    'pH': 7.0,            # predicted pH
    'FeCl2': 0.001,       # iron from recipe (g/L → mmol/kgw)
    'Na2HPO4': 0.5,       # phosphate from recipe
    'NaCl': 5.0,          # base salt
    'MgSO4': 0.2,         # magnesium/sulfate
    'CaCl2': 0.01,        # calcium
    'Na2S': 0.001,        # sulfide (if anaerobic/sulfidogenic)
})

# Check all mineral saturation indices
for phase in solution.phases:
    si = solution.si(phase)
    if si > 0:
        print(f"⚠ {phase}: SI = {si:.2f} — WILL PRECIPITATE")
```

### Remediation Suggestions

When precipitation is predicted, CultureForge should suggest specific fixes based on the type of incompatibility:

**Iron-phosphate precipitation:**
- Add chelator: EDTA (0.5-5 mg/L), NTA (nitrilotriacetic acid, 0.1-1 mg/L), or citrate (1-10 mM)
- Prepare iron solution and phosphate solution separately; autoclave separately; combine after cooling
- Use ferric citrate instead of FeCl₃ (pre-chelated iron)
- Reduce iron concentration if possible (check if MeBiPred iron requirement is truly high)

**Metal-sulfide precipitation (critical for anaerobic/sulfidogenic media):**
- Prepare sulfide solution (Na₂S) separately and add post-autoclaving under anaerobic conditions
- Use iron delivered as ferrous ammonium sulfate at reduced concentration
- Consider using titanium(III) citrate as reductant instead of Na₂S where possible
- If sulfide is the energy substrate (sulfide oxidizers), minimize free metal concentrations

**Calcium-carbonate precipitation:**
- Autoclave CaCl₂ and NaHCO₃ solutions separately
- Use CO₂ sparging to maintain dissolved CO₂ rather than adding bicarbonate salts
- Adjust pH downward before autoclaving (will rise during cooling)

**General strategies:**
- Order of addition matters: add chelators BEFORE metals
- Autoclaving pH shift: many media become more alkaline during autoclaving — account for this
- Temperature-dependent solubility: some precipitates dissolve at growth temperature but form at room temperature (or vice versa) — check at both temperatures

### Preparation Instructions Generator

Beyond just flagging incompatibilities, the system should generate preparation instructions:

```
PREPARATION NOTES:
  ⚠ Iron-phosphate incompatibility detected at pH 7.0

  SOLUTION A (autoclave separately):
    - Na₂HPO₄·12H₂O    1.5 g
    - KH₂PO₄            0.3 g
    - NH₄Cl              0.3 g
    → Dissolve in 500 mL H₂O, autoclave 121°C 15 min

  SOLUTION B (autoclave separately):
    - FeSO₄·7H₂O        0.001 g
    - Trace element solution SL-10    1 mL
    - Na-EDTA            0.005 g (chelator)
    → Dissolve in 10 mL H₂O, autoclave 121°C 15 min

  SOLUTION C (filter sterilize):
    - Vitamin solution    1 mL
    → Filter sterilize (0.2 µm), add post-autoclaving

  COMBINE: Cool Solutions A and B to ~50°C, 
           combine under sterile conditions,
           add Solution C, adjust pH to 7.0 with sterile NaOH/HCl
```

### Database Schema

**Table: `precipitation_rules`** (curated reference, Tier A)
Columns: id, component_a, component_b, condition_ph_min, condition_ph_max, condition_temp_min, condition_temp_max, precipitate_formula, precipitate_name, severity (HIGH/MEDIUM/LOW), remediation_strategy, references

**Table: `recipe_compatibility_checks`** (per-recipe results)
Columns: id, prediction_id, check_tier (A/B), n_warnings, warnings_json, remediation_json, phreeqc_output_json (null for Tier A), checked_at

### Confidence Integration

Compatibility check results affect recipe confidence:
- No precipitation warnings → no change to confidence
- MEDIUM severity warning with remediation available → confidence -0.05, add uncertainty flag
- HIGH severity warning → confidence -0.10, add uncertainty flag with explicit preparation instructions
- Multiple HIGH severity warnings → confidence -0.15, prominently flag "CAUTION: complex preparation required"

### Implementation Priority

Build AFTER the Media Composition Synthesizer is validated but BEFORE the selective suppression feature. The compatibility check directly improves the quality and usability of synthesized recipes.

Suggested position in build order:
1. ✓ Media Composition Synthesizer
2. Thermodynamic engine (Amend & Shock) — current priority
3. CAZy/dbCAN integration
4. Hydrogenase Database integration
5. **Media Compatibility Engine (this feature)**
6. BRENDA integration
7. SILVA integration
8. Selective suppression feature
9. Tier 2 structural analysis

Estimated effort: 1-2 focused evenings. Tier A (rule-based) is a few hours of work. Tier B (PHREEQC) requires installing phreeqpython and writing the interface, maybe another evening.
