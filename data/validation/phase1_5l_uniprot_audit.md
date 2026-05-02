# Phase 1.5l — UniProt Reference Verification Audit

**Date:** 2026-04-27  
**Auditor:** CultureForge automated audit + manual verification against UniProt records  
**Scope:** Every UniProt accession in the Phase 1 / Phase 1.5 / Phase 1.5j / Phase 1.5k versions of `fetch_markers.sh`, plus the `fetch_autotrophy_markers.sh` companion script.  
**Trigger:** Phase 2c pre-audit (LIMITATIONS.md) discovered that the cyc2 reference was a barley plant Beclin-1 protein, motivating a systematic check of every other marker reference.

---

## 1. Executive Summary

| Outcome | Count | Notes |
|---|---|---|
| Total accessions audited | ~95 | Across 23 marker FASTAs |
| **VERIFIED** (correct protein) | ~30 | ~32% — most of these came from the manually curated qmoA, rhodopsin, and dsrAB sets |
| **WRONG-PROTEIN** (entirely unrelated) | ~45 | ~47% — sometimes egregious (animal/plant/fungal proteins in microbial markers) |
| **WRONG-MARKER** (related but wrong gene) | ~5 | E.g., nirS labeled as nosZ; nifD labeled as nifH; sat labeled as dsrAB |
| **DUPLICATE** | ~1 | rdhA had Q8L172 listed twice |
| Marker files entirely wrong | 5 | aprAB, hao, soxB, pscA_fmoA, cyc2 |
| Marker files mostly wrong | 7 | mcrA, mcrBG, pufLM, autotrophy, cooS_cdhA, mtrC_omcB, nosZ |
| Marker files clean | 4 | qmoA, rhodopsin, dsrAB (after cleanup), rdhA (after dedupe) |

**Headline:** ~50% of UniProt accessions in `fetch_markers.sh` returned proteins that have nothing to do with the diagnostic marker the file is named for. Detection has been working better than the contamination rate would suggest because the few correct reference sequences carry most of the BLAST signal — but sensitivity is silently reduced for every marker that operates with 1–2 correct references rather than the intended 3–5.

**Root cause:** Accessions in the Phase 1 marker fetch script were generated from organism + gene-name knowledge rather than from a UniProt query. UniProt accession numbers are stable, but they don't always correspond to the protein one expects from a given gene name in a given genome — particularly for accessions in the `Q*` and `A0A*` ranges, where the same accession block in one organism can land on completely unrelated proteins in another.

---

## 2. Per-Marker Verdict Tables

Each table below lists every accession that was in the *original* (pre-1.5l) reference FASTA. Lines with **WRONG** verdicts were removed during Phase 1.5l. Lines with **VERIFIED** verdicts were retained. New replacement accessions added during Phase 1.5l are listed in §3.

### 2.1 Methanogenesis: `mcrA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P11558 | VERIFIED | Methyl-coenzyme M reductase α (*Methanothermobacter marburgensis*) | KEPT |
| Q8TIY1 | WRONG-PROTEIN | Fun34 related protein (*Methanosarcina acetivorans*) | REMOVED |
| Q6LYP5 | WRONG-PROTEIN | FAD synthase (*Methanococcus maripaludis*) | REMOVED |
| A5UL61 | WRONG-PROTEIN | Cytidylate kinase (*Methanobrevibacter smithii*) | REMOVED |
| Q58256 | VERIFIED | Methyl-coenzyme M reductase α (*M. jannaschii*) | KEPT |

**Verdict:** 2/5 correct.

### 2.2 Methanogenesis: `mcrBG_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P11559 | VERIFIED but MISFILED | Methyl-coenzyme M reductase α (*M. voltae*) — this is mcrA, file expects mcrB+mcrG | KEPT (relabeled) |
| Q8TIY0 | WRONG-PROTEIN | Methyltransferase FkbM domain (*M. acetivorans*) | REMOVED |
| Q58257 | WRONG-MARKER | Methyltransferase mtrE (*M. jannaschii*) — related family but not mcrBG | REMOVED |
| Q58258 | WRONG-MARKER | Methyltransferase mtrD (*M. jannaschii*) — related family but not mcrBG | REMOVED |

**Verdict:** 1/4 correct, and even that one is filed under the wrong subunit name.

### 2.3 Anammox: `hzsA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q1Q5W1 | WRONG-PROTEIN | Cobalt/zinc/cadmium efflux RND transporter (*Kuenenia*) | REMOVED |
| A0A2Z6A915 | VERIFIED-TrEMBL | Hydrazine synthase fragment (uncultured *Ca.* Brocadia) | KEPT |
| G9ITI6 | VERIFIED-TrEMBL | Hydrazine synthase α fragment (*Ca.* Brocadia anammoxidans) | KEPT |
| G9ITI8 | VERIFIED-TrEMBL | Hydrazine synthase α (*Ca.* Jettenia asiatica) | KEPT |

**Verdict:** 3/4 correct. Note: all three correct entries are TrEMBL fragments (~30–50% length); short reference sequences make qcov-gated detection harder.

### 2.4 Anammox: `hdh_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q1PW30 | VERIFIED | Hydrazine dehydrogenase (*Kuenenia stuttgartiensis*) | KEPT |
| Q1PX48 | VERIFIED | Hydroxylamine oxidoreductase (*Kuenenia*) — related but not hdh | KEPT (cross-reactive with hao) |
| A0A0M2UZ26 | WRONG-MARKER | Hydrazine **synthase** subunit C (*Ca.* Brocadia fulgida) — wrong subunit, belongs in hzsA | REMOVED |
| A0ABQ0JTR7 | WRONG-MARKER | Hydrazine **synthase** β (*Ca.* Brocadia sinica) — wrong subunit | REMOVED |

**Verdict:** 2/4 correct (one of which is hao, retained because hdh and hao are paralogs).

### 2.5 Sulfate reduction: `dsrAB_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P45574 | VERIFIED | Dissimilatory sulfite reductase α (*D. vulgaris*) | KEPT |
| P45575 | VERIFIED | Dissimilatory sulfite reductase β (*D. vulgaris*) | KEPT |
| O28606 | WRONG-MARKER | Sulfate adenylyltransferase **sat** (*A. fulgidus*) — different enzyme | REMOVED |
| O28607 | WRONG-PROTEIN | Diphthamide synthase domain protein (*A. fulgidus*) | REMOVED |

**Verdict:** 2/4 correct. Phase 1.5k discrimination (forward vs reverse dsr) relies on companion qmoA marker.

### 2.6 Sulfate reduction: `qmoA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q7X167 | VERIFIED-TrEMBL | QmoA (*Desulfovibrio desulfuricans*) | KEPT |
| A0A8G2C1P1 | VERIFIED-TrEMBL | QmoA (*Desulfomicrobium norvegicum*) | KEPT |
| A0A0U9HMV6 | VERIFIED-TrEMBL | QmoA (*Thermodesulfovibrio aggregans*) | KEPT |
| S5VWR0 | VERIFIED-TrEMBL | QmoA (*Megalodesulfovibrio gigas*) | KEPT |
| Q3IBM0 | VERIFIED-TrEMBL | QmoA (uncultured SRB) | KEPT |
| A0A212JYQ4 | VERIFIED-TrEMBL | QmoA (uncultured *Desulfovibrio* sp.) | KEPT |

**Verdict:** 6/6 correct. This is the only set that was already clean — manually curated during Phase 1.5k.

### 2.7 Sulfate reduction: `aprAB_refs.fasta` — ENTIRELY WRONG (PRE-1.5l)

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q725B6 | WRONG-PROTEIN | AgrB-like accessory gene regulator (*Listeria monocytogenes*) | REMOVED |
| Q72AU3 | WRONG-PROTEIN | Glycine-tRNA ligase β subunit (*D. vulgaris*) | REMOVED |

**Verdict:** 0/2 correct. The file produced no real aprAB hits in any genome before 1.5l.

### 2.8 Sulfur oxidation: `soxB_refs.fasta` — ENTIRELY WRONG (PRE-1.5l)

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q93UV4 | WRONG-PROTEIN | Fluoren-9-ol dehydrogenase (*Terrabacter* sp.) | REMOVED |
| Q3SLP0 | WRONG-PROTEIN | Ribosomal protein uS17 (*Thiobacillus denitrificans*) | REMOVED |
| O66037 | WRONG-PROTEIN | 3-phytase (*Bacillus* sp.) | REMOVED |

**Verdict:** 0/3 correct. The marker existed in name only — every BLAST against soxB pre-1.5l was matching dehydrogenases, ribosomal proteins, or phytases.

### 2.9 Iron oxidation: `cyc2_refs.fasta` — ENTIRELY WRONG (PRE-1.5l)

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q4A194 | WRONG-PROTEIN | **Beclin 1 protein** (*Hordeum vulgare* / **barley**) | REMOVED |

**Verdict:** 0/1 correct. The single reference was a plant autophagy protein. **This was the canary that triggered the entire Phase 1.5l audit.** Every Acidithiobacillus iron-oxidation prediction made before Phase 1.5l was based on weak homology between bacterial cytochromes and a barley autophagy protein.

### 2.10 Ammonia oxidation: `amoA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q04507 | VERIFIED | Ammonia monooxygenase α (*Nitrosomonas europaea*) | KEPT |
| A0A7D4WXT9 | VERIFIED-TrEMBL | AmoA fragment (*Ca.* Nitrospira inopinata) — only 79 aa | KEPT (but short) |
| A0A8D4WF74 | VERIFIED-TrEMBL | Ammonia monooxygenase fragment (uncultured *Nitrospira*) — 138 aa | KEPT (but short) |

**Verdict:** 3/3 correct. One full-length and two fragments. Short fragments contribute weak BLAST signal but expand phylogenetic coverage.

### 2.11 Ammonia oxidation: `hao_refs.fasta` — ENTIRELY WRONG (PRE-1.5l)

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P24022 | WRONG-PROTEIN | **Bacteriocin lactacin-F** (*Lactobacillus johnsonii*) | REMOVED |
| Q82SR3 | WRONG-PROTEIN | ATPase ABC transport (*N. europaea*) | REMOVED |

**Verdict:** 0/2 correct. The hao marker was matching bacteriocins and ABC transporters, not hydroxylamine oxidoreductase.

### 2.12 N fixation: `nifH_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P00459 | VERIFIED | Nitrogenase iron protein 1 (*Azotobacter vinelandii*) | KEPT |
| P07328 | WRONG-MARKER | Nitrogenase MoFe protein α **nifD** (*Azotobacter*) — different subunit | REMOVED |
| P00458 | VERIFIED | Nitrogenase iron protein (*Klebsiella pneumoniae*) | KEPT |

**Verdict:** 2/3 correct. The nifD contamination is the cleaner kind — it's a real nitrogenase, just the wrong subunit, so it produced cross-reactive (but biologically related) signal.

### 2.13 Denitrification: `nosZ_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P19573 | VERIFIED | Nitrous-oxide reductase (*Stutzerimonas stutzeri*) | KEPT |
| P24474 | WRONG-MARKER | Nitrite reductase **nirS** (*P. aeruginosa*) — different denitrification step | REMOVED |
| Q53198 | WRONG-PROTEIN | Putative transposase (*Sinorhizobium fredii*) | REMOVED |

**Verdict:** 1/3 correct. Phase 1.5j uses nosZ as an essential gating marker — fortunately P19573 alone is full-length and well-conserved enough to detect canonical denitrifiers.

### 2.14 Acetogenesis: `acsB_cdhC_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P27988 | VERIFIED | CO dehydrogenase / acetyl-CoA synthase α (*Moorella thermoacetica*) | KEPT |
| Q8TMC6 | WRONG-PROTEIN | Transposase (*M. acetivorans*) | REMOVED |
| Q3AEH4 | WRONG-PROTEIN | Cytochrome c NapC/NirT family (*Carboxydothermus*) | REMOVED |
| P31896 | VERIFIED but MISFILED | CO dehydrogenase **cooS** (*Rhodospirillum rubrum*) — belongs in cooS_cdhA | KEPT (cross-reactive) |

**Verdict:** 2/4 correct, one of which is filed in the wrong marker.

### 2.15 Acetogenesis: `cooS_cdhA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P31896 | VERIFIED | CO dehydrogenase (*R. rubrum*) | KEPT |
| Q2RJY1 | WRONG-PROTEIN | Ribosomal protein bL32 (*M. thermoacetica*) | REMOVED |
| P29342 | WRONG-PROTEIN | Ribosomal protein bL12 (*S. antibioticus*) | REMOVED |
| Q8TMC8 | WRONG-PROTEIN | Uncharacterized protein (*M. acetivorans*) | REMOVED |

**Verdict:** 1/4 correct.

### 2.16 Iron reduction: `mtrC_omcB_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q8EG35 | PARTIALLY CORRECT | MtrA decaheme cytochrome (*Shewanella*) — periplasmic, file expects outer-membrane MtrC | KEPT (cross-reactive) |
| Q74D43 | WRONG-PROTEIN | Sugar transporter SemiSWEET (*G. sulfurreducens*) | REMOVED |
| Q74AE7 | WRONG-PROTEIN | Peptidylprolyl isomerase PpiC-type (*G. sulfurreducens*) | REMOVED |

**Verdict:** 1/3 correct, and that one is the wrong subunit (MtrA, not MtrC).

### 2.17 Phototrophy: `pufLM_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q07006 | WRONG-PROTEIN | Glutamyl endopeptidase (*Streptomyces griseus*) | REMOVED |
| P02948 | VERIFIED but MISFILED | Light-harvesting B-870 α (*R. capsulatus*) — pufA, not pufL/M | KEPT (cross-reactive) |
| P06008 | VERIFIED but MISFILED | Reaction center H chain (*Blastochloris viridis*) — puhA, not pufL/M | KEPT (cross-reactive) |
| P06009 | VERIFIED | Reaction center L chain (*B. viridis*) — pufL ✓ | KEPT |
| P26362 | WRONG-PROTEIN | **CFTR** (*Squalus acanthias* / **shark**) | REMOVED |
| P26363 | WRONG-PROTEIN | **CFTR** (*Xenopus laevis* / **frog**) | REMOVED |
| A7NQ45 | WRONG-PROTEIN | Methyltransferase type 11 (*Roseiflexus*) | REMOVED |
| A7NQ46 | WRONG-PROTEIN | ABC transporter (*Roseiflexus*) | REMOVED |

**Verdict:** 1 fully correct + 2 cross-reactive paralogs / 8. **Two animal CFTR proteins** were embedded in a microbial photosynthetic reaction center marker.

### 2.18 Phototrophy: `psaA_psbA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P29254 | VERIFIED | Photosystem I P700 apoprotein A1 (*Synechocystis*) | KEPT |
| P16033 | VERIFIED | Photosystem II protein D1 (*Synechocystis*) | KEPT |
| P10898 | VERIFIED | Photosystem II CP43 (*Chlamydomonas reinhardtii*) | KEPT |
| Q8DHP3 | WRONG-PROTEIN | β-xylanase (*Thermosynechococcus*) | REMOVED |

**Verdict:** 3/4 correct. Note: P10898 is a eukaryotic alga; intentional or accidental is unclear.

### 2.19 Phototrophy: `pscA_fmoA_refs.fasta` — ENTIRELY WRONG (PRE-1.5l)

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q8KEI5 | WRONG-PROTEIN | Zinc protease (*Chlorobaculum tepidum*) | REMOVED |
| P0C0Y4 | WRONG-PROTEIN | **NADP-dependent mannitol dehydrogenase** (*Alternaria alternata* / **fungus**) | REMOVED |
| Q3AUE1 | WRONG-PROTEIN | DUF1997 domain protein (*Chlorobium chlorochromatii*) | REMOVED |

**Verdict:** 0/3 correct. A fungal mannitol dehydrogenase was acting as the green-sulfur-bacteria reaction-center reference.

### 2.20 Phototrophy: `rhodopsin_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P02945 | VERIFIED | Bacteriorhodopsin (*Halobacterium salinarum* NRC-1) | KEPT |
| Q9F7P4 | VERIFIED | Green-light proteorhodopsin (γ-proteobacterium EBAC31A08) | KEPT |

**Verdict:** 2/2 correct.

### 2.21 Reductive dehalogenation: `rdhA_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q3ZAB8 | VERIFIED | Trichloroethene reductive dehalogenase (*Dehalococcoides* 195) | KEPT |
| Q8L172 | VERIFIED | Tetrachloroethene reductive dehalogenase (*Desulfitobacterium* Y51) | KEPT |
| Q69GM4 | VERIFIED | Chloroethene reductive dehalogenase (*Dehalococcoides* VS) | KEPT |
| Q69GM3 | VERIFIED but PERIPHERAL | vcrB membrane anchor (*Dehalococcoides* VS) — anchor, not catalytic rdhA | REMOVED |
| A0A0A7NZR9 | VERIFIED-TrEMBL | RDH-like KB1rdhA26 (*Dehalococcoides*) | KEPT |
| Q8GJ27 | VERIFIED | Tetrachloroethene RDH (*Dehalobacter restrictus*) | KEPT |
| Q8GJ31 | VERIFIED | Tetrachloroethene RDH (*Desulfitobacterium*) | KEPT |
| Q8L172 | DUPLICATE | Same as above, listed twice | DEDUPED |
| Q848J2 | VERIFIED | Tetrachloroethene RDH (*Desulfitobacterium*) | KEPT |

**Verdict:** 7 unique correct + 1 anchor + 1 duplicate / 9. Cleaned to 6 catalytic rdhA references.

### 2.22 Autotrophy: `autotrophy_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| P54205 | VERIFIED | RuBisCO large chain (*Synechocystis*) | KEPT |
| Q3IXP8 | WRONG-MARKER | Hydroxypyruvate reductase / glycerate kinase (*Rhodobacter*) | REMOVED |
| Q1JU64 | WRONG-PROTEIN | **MHC class II antigen** (*Bos taurus* / **cow**) | REMOVED |
| Q8KFR1 | WRONG-PROTEIN | Ribosomal protein bS20 (*Chlorobaculum*) | REMOVED |
| Q9F721 | WRONG-PROTEIN | Cytochrome bc complex cytochrome b (*Chlorobaculum*) | REMOVED |
| A4YHK3 | WRONG-PROTEIN | DEAD/DEAH-box helicase (*Metallosphaera sedula*) | REMOVED |

**Verdict:** 1/6 correct. The autotrophy marker file contained a **cow MHC class II antigen** — there's no plausible explanation for how this ended up there other than accession-block confusion.

### 2.23 Aerobic respiration: `terminal_oxidases_refs.fasta`

| Accession | Verdict | What it actually is | Used? |
|---|---|---|---|
| Q56431 | WRONG-PROTEIN | Pyrroline-5-carboxylate reductase fragment (*Thermus*) | REMOVED |
| P82543 | VERIFIED | Cytochrome c oxidase subunit 2A (*T. thermophilus*) | KEPT |
| P34957 | VERIFIED | Quinol oxidase subunit 2 qoxA (*B. subtilis*) | KEPT |
| P34956 | VERIFIED | Quinol oxidase subunit 1 qoxB (*B. subtilis*) | KEPT |
| P39484 | WRONG-PROTEIN | Glucose 1-dehydrogenase (*Priestia megaterium*) | REMOVED |
| Q4J781 | WRONG-PROTEIN | NAD-dependent **alcohol dehydrogenase** (*S. acidocaldarius*) | REMOVED |
| P08305 | VERIFIED | Cytochrome c oxidase subunit 1-α (*P. denitrificans*) | KEPT |
| P08306 | VERIFIED | Cytochrome c oxidase subunit 2 (*P. denitrificans*) | KEPT |

**Verdict:** 5/8 correct. **The Sulfolobus alcohol dehydrogenase Q4J781 is the explanation for the Phase 1.5l Sulfolobus regression.** Phase 1 detection at 0.50 confidence was partly carried by spurious BLAST hits between archaeal proteins and this misfiled alcohol dehydrogenase, not by genuine SoxM/SoxB recognition. After cleanup the file no longer contains an archaeal terminal oxidase, so Sulfolobus aerobic respiration falls below detection threshold.

---

## 3. Replacement Accessions Added in Phase 1.5l

The following accessions were added during the Phase 1.5l correction round. Every one was verified against UniProt by reading the entry header before being committed to `fetch_markers.sh` v2.

| Marker | New accession | Source organism | What it is |
|---|---|---|---|
| mcrA | P07962, Q8THH1, P07961 | *M. thermoautotrophicus*, *M. mazei*, *M. fervidus* | Verified mcrA |
| mcrBG | P11560, P07955, Q58252, P11562, P07964, Q58255 | mixed methanogens | Verified mcrB and mcrG (replaces the misfiled mcrA + methyltransferases) |
| aprAB | T2G6Z9, T2G899 | *M. gigas* | Verified aprA + aprB (replaces Listeria AgrB and glycine-tRNA ligase) |
| hao | Q50925, Q1PX48 | *N. europaea*, *Kuenenia* | Verified hydroxylamine oxidoreductase |
| soxB | P72177, A0A5C4S040, A0A3D8P969 | *Paracoccus*, *Chlorobaculum*, etc. | Verified soxB (replaces fluorenol DH, ribosomal protein, phytase) |
| pscA_fmoA | Q46393, Q46135, O07091, Q8KEP5 | Chlorobiaceae | Verified fmoA + pscC/pscD |
| cyc2 | B7JAQ7, O33823, A0A060UV08 | *Acidithiobacillus* and relatives | Verified cyc2 outer-membrane cytochrome (replaces barley Beclin-1) |
| pufLM | (replaced wholesale) | mixed purple bacteria + FAP types | 9 verified pufL+pufM (replaces shark/frog CFTR + others) |
| nosZ | (added 4 verified) | mixed denitrifiers | 5 total verified nosZ (replaces nirS + transposase) |
| mtrC_omcB | P0DSN4, Q749K5 | *Shewanella*, *Geobacter* | Verified mtrC + omcB (replaces sugar transporter + isomerase) |
| autotrophy | (added 2 verified) | mixed cyanobacteria | 3 total verified rbcL (replaces cow MHC, ribosomal proteins, helicase) |
| cooS_cdhA | (added 3 verified) | mixed | 4 total verified cooS/CODH (replaces ribosomal proteins) |
| terminal_oxidases | (kept 5 correct) | mixed | 5 total verified Cox/Qox (replaces Sulfolobus alcohol DH and others) |

`qmoA`, `rhodopsin`, `dsrAB` (post-cleanup), and `rdhA` (post-dedupe) needed no new accessions — only removals.

---

## 4. Methodology Notes

- Each accession was verified by direct lookup of the UniProtKB record on `rest.uniprot.org`. Verdicts use the `protein name` and `gene name` fields from the UniProt entry header.
- "VERIFIED-TrEMBL" indicates a `Q*`/`A0A*`-style automatic-annotation accession that visibly matches the expected gene name in its description; these are weaker references than Swiss-Prot but functionally correct.
- "PARTIALLY CORRECT" / "WRONG-MARKER" indicates the protein is in the right family but the wrong member (e.g., MtrA when the file expects MtrC; nirS when the file expects nosZ).
- "WRONG-PROTEIN" indicates the protein is biologically unrelated to the marker.

---

## 5. Limitations of This Audit

- **TrEMBL annotations are not human-curated.** Three of the six qmoA references are TrEMBL entries, so their "verified" status depends on automated UniProt annotation accuracy. They look correct but were not confirmed by reading primary literature.
- **No structural verification was performed.** Two proteins can carry the same gene name but differ enough in sequence that BLAST won't connect them. Phase 1.5l fixed annotation contamination but did not verify that the kept references span the actual phylogenetic diversity of the marker family.
- **Some markers retained cross-reactive paralogs intentionally.** Examples: P02948 (pufA, kept in pufLM), P06008 (puhA, kept in pufLM), P31896 (cooS, kept in acsB_cdhC). These are biologically related and contribute useful BLAST signal even though they are not strictly the named gene. Where this matters, the relevant detector logic still operates correctly because pathway-level scoring requires positive BLAST signal *somewhere* in the family rather than for a specific subunit.
- **Hit-pattern verification (Phase 1.5l Task 3)** is in the companion file `phase1_5l_hit_patterns.tsv` — quantitative confirmation that corrected references produce the expected hit/no-hit pattern across the 18-organism development set.
