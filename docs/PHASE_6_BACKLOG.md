# Phase 6+ Backlog

Items deferred from Phase 5.0 — not to be added until after Phase 5.0 evaluation
is complete and the manuscript is in submission.

## Tool integrations to consider

### High priority

- **eggNOG-mapper integration**: Fills gaps where gapseq's pathway approach is incomplete.
  Particularly relevant for rare metabolisms (anammox, cable bacteria, ANME, syntrophy).
  Adds COG/KOG categories + KEGG KO annotations for orthologous group context.
  Conda env present on Pod (`/home/gschaible/.conda/envs/`-style structure) but never wired in.

- **dbCAN / CAZy integration**: Activates `evidence_type='cazyme'` placeholder already in schema.
  Adds carbon substrate class specificity (cellulose vs hemicellulose vs chitin vs xylan vs etc.)
  beyond gapseq's general carbon source detection. dbCAN server was down during earlier
  exploration; needs to be revisited.

### Medium priority

- **Interpretability layer**: Borrowed principle from Máša et al. 2025. Surface the reasoning
  behind each recipe decision (capability detections → biomass template → substrate choices →
  confidence indicators). Probably a Phase 5.1 enhancement (1-2 days work), not Phase 6.
  Doesn't require new tools, just better output formatting.

### Lower priority

- **DRAM** (Distilled and Refined Annotation of Metabolism): Cleaner "ecological role"
  summaries than gapseq. Overlaps significantly with gapseq, so integration cost may
  not justify benefit. Worth knowing about, not necessarily integrating.

- **AlphaFold-based annotation rescue**: For specific capabilities where sequence-based
  detection fails. Only worth exploring if specific gaps surface during Phase 5.0 evaluation
  that can't be fixed by eggNOG/dbCAN.

- **Pyrodigal in gapseq pipeline**: Currently using prodigal subprocess + .faa input.
  Pyrodigal would be faster and let gapseq do auto-translation. Not blocking.

## Methodological additions to consider

- **HMM-based marker scans for hard-to-detect proteins**: Some autotrophy markers
  (rTCA aclA/aclB, CBB rbcL/cbbL) are not in current marker BLAST set. Hmmer profiles
  might catch them where sequence similarity fails. Phase 6 if Wave 1/2 evaluations
  reveal systematic gaps.

- **Active learning / Bayesian optimization for recipe refinement**: For Phase 7+
  when experimental cultivation validation data exists. Frame as: BacterAI-style loop
  applied to CultureForge predictions.

