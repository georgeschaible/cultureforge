# Related Work for CultureForge Manuscript

Papers to cite, read in depth, and position CultureForge against when writing.

## Key framework paper (cite as motivation)

**Jiménez DJ et al. (2026).** Discovery and cultivation of prokaryotic taxa in the age
of metagenomics and artificial intelligence. *The ISME Journal* 20(1):wrag012.
DOI: 10.1093/ismejo/wrag012

Perspective paper proposing a 4-step framework for genome-driven cultivation:
(1) microbiome reshaping, (2) genome-resolved metagenomics, (3) AI/ML + GEMs,
(4) targeted culturomics. Explicitly names gapseq as a complementary tool.
Identifies AI-assisted media design from MAGs as an unmet need — exactly the
gap CultureForge fills. **Cite as the framework CultureForge implements.**

## Closest peer (cite as comparator)

**Máša P et al. (2025).** Explainable rule-based prediction of cultivation media
for microbes. *Computational and Structural Biotechnology Journal*.
DOI: 10.1016/j.csbj.2025.10.014

Rule-based classifier + LLM comparison for cultivation media prediction from
microbial traits using the KG-Microbe knowledge graph. **Differentiates from
CultureForge by**: requires curated trait labels (KG-Microbe entries),
does not work on novel MAGs without prior annotations.

## Complementary downstream tool (cite as context, not competitor)

**Dama AC et al. (2023).** BacterAI maps microbial metabolism without prior
knowledge. *Nature Microbiology* 8:1018-1025. DOI: 10.1038/s41564-023-01376-0

Robot-driven reinforcement learning for media optimization. Learned amino acid
requirements for *S. gordonii* and *S. sanguinis* using up to 39-ingredient media.
**Solves a different problem**: refining media for organisms already in culture,
not predicting media for organisms not yet in culture.

## Historical baseline (cite as precedent)

**Oberhardt MA et al. (2015).** Harnessing the landscape of microbial culture media
to predict new organism-media pairings. *Nature Communications* 6:8493.
DOI: 10.1038/ncomms9493

KOMODO database + phylogeny-based collaborative filtering for media prediction.
First systematic attempt at media prediction. Uses 16S rRNA + DSMZ media database.
**Limitation**: requires phylogenetic proximity to a cultivated reference;
fails for taxonomically novel MAGs.

## Positioning CultureForge

The above four papers collectively define the competitive landscape. CultureForge
is positioned at the intersection of these approaches but addresses cases none of
them handle: **genome-based media prediction for novel MAGs without prior cultivation
history or curated trait annotations**, validated against cultivated reference
organisms.

