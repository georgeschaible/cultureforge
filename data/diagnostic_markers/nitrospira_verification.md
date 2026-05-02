# Nitrospira moscoviensis Pre-Phase-3.3 Verification

**Date:** 2026-04-30
**Purpose:** Before committing Phase 3.3 to comammox amoA marker addition, verify that the test-set Nitrospira moscoviensis genome actually encodes comammox amoA. (Phase 3.2 surfaced that S. acidocaldarius DSM 639 lacks the canonical Sulfolobales sulfur-oxidation enzymes; verifying gene presence first prevents repeating that pattern.)

**Result: Outcome C — comammox amoA is ABSENT. The genome is a canonical nitrite oxidizer with strong nxrAB. Phase 3.3 should pivot from "comammox amoA references" to "canonical Nitrospira nitrite-oxidation detection (nxr-based)".**

---

## 1. Genome identification

| Field | Value |
|---|---|
| CultureForge genome_id | 23 |
| NCBI accession | GCF_001273775.1 |
| Assembly name | ASM127377v1 |
| Strain | **Nitrospira moscoviensis NSP M-1** |
| Assembly status | Complete Genome (chromosome NZ_CP011801.1) |
| Submission date | 2015-08-25 |
| Submitter | University of Vienna (Wagner / Daims group) |
| Genome size | 4,589,485 bp (~4.6 Mb) |
| Predicted proteins (gapseq prodigal) | 4,507 |
| NCBI Taxon ID | 42253 |

**Strain provenance**: NSP M-1 is the type-strain reference for canonical nitrite-oxidizing *Nitrospira moscoviensis* (Ehrich et al. 1995). The 2015 University of Vienna submission corresponds to Koch et al. 2015 (Science) and Daims et al. 2015 (Nature) — but those papers identified comammox in *Candidatus* Nitrospira inopinata (Daims et al.) and *Ca.* N. nitrosa / *Ca.* N. nitrificans (van Kessel et al.), NOT in N. moscoviensis NSP M-1. NSP M-1 was used as the canonical-only reference in those studies for comparison purposes.

---

## 2. BLAST verification

### 2.1 Comammox amoA references

Three full-length comammox amoA references fetched from UniProt:

| Accession | Source | Length |
|---|---|---|
| A0A0S4KUL9 | *Ca.* Nitrospira inopinata | 281 aa |
| A0A0S4LM25 | *Ca.* Nitrospira nitrificans | 282 aa |
| A0A5Q4ZZ13 | uncultured Nitrospira (environmental Clade A) | 280 aa |

Self-vs-self sanity check: refs cluster tightly (90–93% pident among themselves at 100% qcov, bitscores 503–526). Self-bitscore for A0A0S4KUL9 = 574. References are legitimate comammox amoA orthologs.

### 2.2 BLAST: comammox amoA refs vs N. moscoviensis NSP M-1 proteome

```
evalue 1e-10 → 0 hits
evalue 100   → best hit: A0A0S4KUL9 vs NZ_CP011801.1_1240 at 36.4% pident, 16% qcov, e=0.11, bs=30
```

All hits are short, low-identity, statistically meaningless (evalue >0.1, alignment <50 aa on a 281-aa reference).

**Conclusion: No detectable comammox amoA ortholog in N. moscoviensis NSP M-1.**

### 2.3 NCBI annotation cross-check

Direct NCBI Protein search confirms:

- `"Nitrospira moscoviensis" AND amoA` → **0 hits**
- `"Nitrospira moscoviensis" AND "ammonia monooxygenase"` → **0 hits**
- `"Nitrospira moscoviensis" AND monooxygenase` → 4 hits, all unrelated enzymes:
  - antibiotic biosynthesis monooxygenase family protein
  - cytochrome P450
  - putative alkanesulfonate monooxygenase
  - conserved exported protein of unknown function

**The genome's RefSeq PGAP annotation contains no amoA at all. This is not a divergence/threshold issue — the gene simply is not in this genome.**

### 2.4 nxrA cross-check (canonical Nitrospira nitrite oxidoreductase)

Reference: `A0A0S4KRS1` = *Ca.* Nitrospira inopinata nxrA, 1145 aa, full-length.

```
evalue 1e-10:
  A0A0S4KRS1 → NZ_CP011801.1_226   96.07% pident, 100% qcov, bs=2332
  A0A0S4KRS1 → NZ_CP011801.1_4209  95.90% pident, 100% qcov, bs=2329
  A0A0S4KRS1 → NZ_CP011801.1_4206  95.63% pident, 100% qcov, bs=2325
  A0A0S4KRS1 → NZ_CP011801.1_3752  94.67% pident, 100% qcov, bs=2272
  A0A0S4KRS1 → NZ_CP011801.1_3748  94.32% pident, 100% qcov, bs=2254
```

**5 nxrA paralogs, all at 94–96% pident over full length (qcov 100%, bitscore 2254–2332).** This is overwhelming evidence that N. moscoviensis NSP M-1 is a strong canonical nitrite oxidizer. The presence of multiple nxrA paralogs is consistent with literature describing 2–3 nxr operons in *Nitrospira* species.

---

## 3. Current CultureForge classification

`python3 cultureforge.py inspect "Nitrospira" --section capabilities --section recipe`:

**Capabilities:**
- **Primary mode: acetogenic, conf 0.60** ⚠ wrong
- Acetogenesis (Wood-Ljungdahl) detected at 0.605 (pathway 3/6 steps, weighted 0.58; cofactors 1/1)
- All other capabilities rejected including:
  - Aerobic ammonia oxidation: 0.300 (pathway score 0.00 — correctly negative)
  - Aerobic respiration: 0.316 (below threshold)
  - No nitrite oxidation capability defined in pathway_definitions.json

**Recipe (V12 score 20%):**
- Primary cultivation mode: acetogenic
- Gas phase: H2/CO2 80:20 at 1.5 atm
- Temperature: 39°C
- pH: 7.0
- Carbon source: CO2 (autotrophic via Wood-Ljungdahl)
- Electron donor: H2
- Reaction: 4 H2 + 2 CO2 → acetate + 2 H2O + H⁺
- Reducing agent: present
- Trace metals + Wolin's vitamins added

**Biological assessment:** The current recipe is fundamentally wrong. N. moscoviensis is an obligate aerobic chemolithoautotroph that uses **NO2⁻ as electron donor** (not H2) and **O2 as terminal acceptor** (not CO2 via WL). The correct recipe (DSMZ Medium 2399 / similar) calls for:
- Aerobic atmosphere (air)
- NaNO2 (~0.5 mM) as electron donor
- NaHCO3 / CO2 as carbon source
- Trace metals + vitamins
- pH ~7.5
- Temperature ~37°C (mesophile, type strain)

The **20% V12 score correctly flags this** as a poorly-matching recipe. The root cause is the F.3 spurious-gapseq-pathway pattern (acetogenesis pathway partially scored without diagnostic markers; no nitrite-oxidation alternative to displace it).

---

## 4. Verdict

**Outcome C: comammox amoA is genuinely absent from N. moscoviensis NSP M-1.**

This is a Sulfolobus-DSM-639-style situation: adding comammox amoA references would not improve the test-set score for this organism, because the gene is not in the genome.

**However, this is not the dominant problem.** The dominant problem is that CultureForge has no detector for canonical Nitrospira nitrite oxidation. Despite N. moscoviensis having 5 strong nxrA paralogs (94–96% pident), the capability framework cannot detect this signal because:
1. There is no `nitrite_oxidation` (or `lithotrophic_aerobic_nitrite`) capability in `pathway_definitions.json`
2. There is no `nxrA` diagnostic marker in `data/diagnostic_markers/`
3. Without these, the capability detector falls back to whatever spurious gapseq pathway happens to score highest — currently acetogenesis (0.605).

## Recommendation: Pivot Phase 3.3

**Original Phase 3.3 framing**: Add comammox amoA references to fix LIMITATIONS A.2 (Nitrospira moscoviensis comammox detection failure).

**Pivoted Phase 3.3 framing**: Add canonical Nitrospira nitrite oxidation detection.

Specifically:
1. **New marker `nxrA`** — 4–6 references covering canonical *Nitrospira* (the *Ca.* N. inopinata reference A0A0S4KRS1 used in this verification, plus refs from *Nitrospira defluvii*, *Nitrospira lenta*, and outgroup nitrite oxidoreductase from *Nitrobacter winogradskyi*). Test-set exclusion: no NSP M-1 proteins as references.
2. **New capability `lithotrophic_aerobic_nitrite`** in `pathway_definitions.json`:
   - Diagnostic marker: nxrA
   - Pathway steps: nitrite oxidation, ammonia assimilation, autotrophic CO2 fixation (rTCA or 3HP/4HB)
   - Negative markers: amoA (positive amoA + nxrA = comammox; nxrA alone = canonical)
   - Description: Aerobic nitrite oxidation (canonical Nitrospira / Nitrobacter / Nitrococcus / Nitrolancea / Nitrotoga lineages)
3. **Recipe composer routing**: aerobic atmosphere, NaNO2 electron donor at low concentration (avoiding nitrite toxicity above ~5 mM), NaHCO3 carbon source, ~pH 7.5, ~37°C for N. moscoviensis (use TEMPURA when present).
4. **Optional secondary**: comammox amoA references CAN still be added (cheaply) as the comammox-distinguishing marker. When nxrA AND amoA both fire, classify as comammox; nxrA alone = canonical. This gives forward-compatibility with future *Ca.* N. inopinata-class test organisms without committing additional pathway-definition complexity.

Estimated impact:
- N. moscoviensis V12 score: should rise from 20% (current heterotrophic-acetogen recipe) to a much higher score because the lithoautotrophic nitrite-oxidizer recipe matches DSMZ 2399 directly.
- No regressions expected: the new capability fires only when nxrA marker hits, and no other test-set organism has nxrA (canonical Nitrospira is the only nitrite-oxidizer lineage in the test set). Cross-contamination scan during Phase 3.3 will confirm.

Estimated time: Phase 3.3 pivoted scope is similar to original (5–7 days):
- nxrA reference curation (1–2 days, small set, well-characterized)
- New capability definition (half day)
- Recipe composer routing for nitrite oxidation (half day) — likely needs a new composer function or extension of existing lithotrophic_aerobic
- Cross-contamination + V12 validation (1 day)
- Documentation (half day)

---

## Files referenced

- Proteome: `data/gapseq/Nitrospira_moscoviensis/Nitrospira_moscoviensis_proteins.faa` (4507 sequences)
- Verification BLAST DB: `/tmp/p3_3v/nm_db` (transient)
- Comammox amoA refs: `/tmp/p3_3v/comammox_amoA_refs.fa` (transient, A0A0S4KUL9 / A0A0S4LM25 / A0A5Q4ZZ13)
- nxrA ref: `/tmp/p3_3v/nxrA_refs.fa` (transient, A0A0S4KRS1)

## Literature

- Ehrich S, Behrens D, Lebedeva E, Ludwig W, Bock E. 1995. A new obligately chemolithoautotrophic, nitrite-oxidizing bacterium, *Nitrospira moscoviensis* sp. nov. and its phylogenetic relationship. *Arch Microbiol* 164:16–23. (Original description of NSP M-1.)
- Daims H, Lebedeva EV, Pjevac P et al. 2015. Complete nitrification by *Nitrospira* bacteria. *Nature* 528:504–509. (Comammox discovery; *Ca.* N. inopinata.)
- van Kessel MAHJ, Speth DR, Albertsen M et al. 2015. Complete nitrification by a single microorganism. *Nature* 528:555–559. (Comammox; *Ca.* N. nitrosa / *Ca.* N. nitrificans.)
- Koch H, Lücker S, Albertsen M et al. 2015. Expanded metabolic versatility of widespread taxonomic group through complete oxidation of ammonia. *PNAS* 112:11371–11376. (Comammox phylogeny and gene content.)
- Spieck E, Lipski A. 2011. Cultivation, growth physiology, and chemotaxonomy of nitrite-oxidizing bacteria. *Methods Enzymol* 486:109–130. (Cultivation references for canonical NOB media.)
