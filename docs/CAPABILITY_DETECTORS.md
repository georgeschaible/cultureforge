# CultureForge Capability Detectors — Design & Usage

## Design Philosophy

Three biological principles drive the detector architecture:

### 1. Metabolisms are pathways, not enzymes

A methanogen has the complete methanogenesis pipeline: substrate input, methyl carrier transfers, methyl-CoM reduction by mcrA, and energy conservation. A genome with mcrA alone but no F420 biosynthesis or CoM biosynthesis is anomalous, not methanogenic. Each detector evaluates the full pathway from substrate to product.

### 2. Transport closes the loop, with annotation caveats

Transporter annotation is unreliable: MFS members get generic annotations from weak sequence signatures, and ABC transporter substrate-binding proteins diverge rapidly. Transporter evidence is therefore **asymmetric**: present transporters boost confidence, absent transporters do NOT lower it. This matches bench reasoning: "I see a matching permease, that reinforces the call" vs "I don't see one, but the substrate might diffuse."

### 3. Evidence is weighted, not gated

Each detector produces a continuous confidence score from multiple evidence types. No single input hard-gates the decision (except negative markers, which multiplicatively zero confidence). A high-confidence mcrA BLAST hit dominates over weak pathway signals; a complete pathway without marker confirmation still reaches detection threshold.

## Architecture

### Data flow

```
genome.fasta → gapseq pathways + transporters
             → prodigal → proteome.faa → diagnostic marker BLAST
             → reaction marker scan (terminal oxidases, catalase, hao)
             → CheckM quality assessment
                                    ↓
              capability_detectors.profile_capabilities()
                                    ↓
              CapabilityProfile (all detectors evaluated in parallel)
```

### Adding a new metabolism

Edit `data/pathway_definitions.json`. No code changes required.

Each pathway entry contains:
- `steps`: list of pathway steps with `gapseq_patterns` (regex matched against gapseq pathway names), `ec_numbers`, `weight`, and optional `diagnostic_marker` reference
- `required_transporters`: substrate transporters (positive-only bonus)
- `product_transporters`: product efflux transporters (positive-only bonus)
- `cofactor_biosyntheses`: required cofactor pathways
- `negative_markers`: diagnostic markers whose presence NEGATES this metabolism (e.g., mcrA negates acetogenesis)

**Important**: `gapseq_patterns` must match gapseq's actual pathway naming conventions, not enzyme names. gapseq uses high-level names like "methanogenesis from H2 and CO2" or "reductive acetyl coenzyme A pathway I (homoacetogenic bacteria)". Check the `genome_pathways` table for examples.

### Scoring formula

```
pathway_score    = sum(weight × found × dm_boost) / sum(all weights)
cofactor_score   = fraction of cofactor biosyntheses present
transporter_bonus = min(0.15, +0.10 per substrate + 0.05 per product)
negative_penalty  = 0.0 if any negative marker present with bs >= 300
                    1.0 otherwise

confidence = (0.70 × pathway_score + 0.20 × cofactor_score
              + 0.05 × diagnostic_boost + transporter_bonus)
             × negative_penalty

detected = confidence >= 0.50 AND pathway_score >= 0.40
```

### Diagnostic marker BLAST thresholds

Two tiers:
- **Full credit** (1.5× weight boost): identity >= 40%, bitscore >= 300
- **Moderate credit** (1.2× weight boost): identity >= 30%, bitscore >= 150
- Below these: not counted

These thresholds balance detection of divergent orthologs in novel lineages against false positives from paralogs.

### Composite detectors

Two metabolisms use composite signatures rather than defined pathways:

**Syntrophy**: beta-oxidation + electron-bifurcating hydrogenase + NO terminal electron acceptor. Confidence capped at 0.70.

**Salt-in halophily**: absent compatible solutes + elevated K+ transporters + acidic proteome (D+E fraction). Confidence capped at 0.75. The acidic proteome is the strongest single signal.

## Current Detection Results (Phase 1 smoke test)

| Organism | Top-1 Detection | Conf | Correct? |
|---|---|---|---|
| E. coli | Aerobic respiration | 0.80 | Yes |
| Methanococcus | Methanogenesis | 0.69 | Yes |
| Nitrosomonas | Ammonia oxidation | 0.92 | Yes |
| Rhodopseudomonas | Purple phototrophy | 0.77 | Yes |
| Halobacterium | Bacteriorhodopsin | 0.66 | Yes |
| Syntrophomonas | Syntrophy | 0.70 | Yes |
| Acetobacterium | Acetogenesis (WL) | 0.75 | Yes |
| D. vulgaris | Sulfate reduction | 0.73 | Yes (top-2; top-1 is acetogenesis FP) |

### Known false positives (to be tuned in Phase 2)

- **Acetogenesis FP in D. vulgaris and Geobacter**: WL pathway enzymes (CODH/ACS) are used by these organisms for CO2 fixation, not acetogenesis. Need additional negative markers (dsrAB for SRBs, mtrC/omcB for iron reducers).
- **Syntrophy FP in Clostridium**: [FeFe] hydrogenases + beta-oxidation + no aerobic respiration → false syntrophy call. Fermenters need a separate detector.
- **hao FP at low identity (30-40%)**: multiheme cytochromes match hydroxylamine oxidoreductase. Raised to 40%/300 threshold; some residual FPs remain.

## Transcriptomics Readiness

`PathwayStepEvidence` includes placeholder fields for future RNA-seq integration:

```python
expression_tpm: Optional[float] = None
expressed_above_threshold: Optional[bool] = None
```

No implementation in Phase 1. When RNA-seq integration lands (Phase 4+), expression data will provide an independent evidence layer confirming which predicted pathways are actually transcribed.

## Acidic Residue Distribution

Computed for all 17 validation organisms. Halobacterium salinarum (0.1574) is the clear outlier. The proposed threshold of 0.19 is too high — revised recommendation: 0.15 (separates Halobacterium from non-halophiles, with margin).

## Files

| File | Role |
|---|---|
| `capability_detectors.py` | Core module: detectors, composite detectors, orchestrator |
| `data/pathway_definitions.json` | Declarative pathway definitions for all metabolisms |
| `run_marker_blast.py` | BLAST proteome against diagnostic marker databases |
| `build_marker_blast_db.py` | Build BLAST databases from reference FASTAs |
| `fetch_markers.sh` | Download diagnostic marker sequences from UniProt |
| `data/diagnostic_markers/` | Reference FASTAs and BLAST databases |
| `qc_gate.py` | Genome quality gate (CheckM integration) |
| `run_checkm.py` | CheckM wrapper |
| `load_checkm.py` | genome_quality table loader |
