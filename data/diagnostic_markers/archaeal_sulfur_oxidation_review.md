# Archaeal Sulfur Oxidation Markers — Phase 3.2 Literature Review

**Purpose:** Confirm enzyme set and candidate UniProt references for adding archaeal sulfur oxidation diagnostic markers to CultureForge. The current `lithotrophic_aerobic_sulfur` capability uses bacterial soxB only and misclassifies Sulfolobus acidocaldarius (and would mishandle Acidianus, Metallosphaera, Sulfurisphaera, etc.) because Sulfolobales archaea use a different enzymatic toolkit.

**Phase 3.2 scope:** Add markers for archaeal sulfur oxidation, extend the existing `sulfur_oxidation` pathway with new diagnostic-marker-bearing steps. Do NOT modify the capability framework.

**Date:** 2026-04-30

---

## 1. Biology background

Sulfolobales archaea (Acidianus, Metallosphaera, Saccharolobus, Sulfodiicoccus, Sulfolobus, Sulfuracidifex, Sulfurisphaera) are thermoacidophilic chemolithotrophs that oxidize reduced sulfur compounds (S⁰, S²⁻, S₂O₃²⁻, S₄O₆²⁻) for energy and fix CO₂ via the 3-hydroxypropionate / 4-hydroxybutyrate (3HP/4HB) cycle for autotrophic growth.

Unlike bacterial sulfur oxidizers (Paracoccus, Thiobacillus, Allochromatium, Sulfurimonas, etc.) which use the periplasmic SoxABXYZ multienzyme complex, **Sulfolobales archaea do not encode soxB at all**. The bacterial SOX system is absent from the order. Phase 1.5m's bacterial soxB references (`P72177`, `A0A5C4S040`, `A0A3D8P969` from Paracoccus / Chlorobaculum) therefore do not detect any archaeal sulfur oxidizer.

Archaeal sulfur oxidation uses a different family of enzymes:

| Enzyme | Substrate → Product | Cellular location | Conservation in Sulfolobales |
|---|---|---|---|
| **Sulfur oxygenase reductase (SOR)** | S⁰ + O₂ + H₂O → SO₃²⁻ + S₂O₃²⁻ + H₂S | Cytoplasmic (soluble) | Lineage-restricted: Acidianus, Metallosphaera, Sulfuracidifex, Sulfurisphaera tokodaii. ABSENT from Sulfolobus acidocaldarius and Saccharolobus solfataricus. |
| **Thiosulfate:quinone oxidoreductase (TQO; DoxD + DoxA)** | 2 S₂O₃²⁻ + 2 quinone → S₄O₆²⁻ + 2 quinol | Membrane | Broadly conserved across Sulfolobales sulfur oxidizers — the strongest single archaeal sulfur-oxidation marker. Present in Acidianus, Metallosphaera, Saccharolobus, Sulfodiicoccus, Sulfolobus, Sulfuracidifex, Sulfurisphaera (per Counts et al. 2021, Willard et al. 2024). |
| **Tetrathionate hydrolase (TetH; tth1)** | S₄O₆²⁻ + H₂O → S₂O₃²⁻ + SO₄²⁻ + S⁰ | Extracellular (acidophilic) | Present in many Sulfolobales sulfur oxidizers. Verified biochemically in Acidianus ambivalens (Protze et al. 2011). |
| **Heterodisulfide reductase-like complex (Hdr-like)** | proposed: cytoplasmic sulfur oxidation | Cytoplasmic (membrane-associated) | Function less settled — proposed role in S⁰ oxidation distinct from canonical methanogen Hdr. Found across Sulfolobales but verification standards from Phase 1.5m are not yet met. |
| **Sulfite:acceptor oxidoreductase (SAOR)** | SO₃²⁻ + H₂O + acceptor → SO₄²⁻ + acceptor·H₂ | Cytoplasmic, Mo-dependent | Polyphyletic — sulfite oxidation is performed by both bacterial and archaeal Mo-cofactor enzymes; not Sulfolobales-specific. Phase 3.2 defers SAOR. |

**Key distinguishing fact about Sulfolobus acidocaldarius DSM 639 (the test-set target):** Originally I expected TQO/DoxDA to fire on S. acidocaldarius. Empirical BLAST against the Phase 1.5m-style reference set rules this out — S. acidocaldarius DSM 639 lacks detectable orthologs to all four archaeal sulfur-oxidation markers (best DoxD hit: 30.3% pident over 36% qcov, e=8e-5, far below standard thresholds). UniProt has zero doxD/doxA/tetH/sor entries for this species under any synonym. This is consistent with Counts et al. 2021 / Willard et al. 2024 classifying S. acidocaldarius as a **limited** sulfur biooxidizer compared to Acidianus, Metallosphaera, and Sulfurisphaera. The DSM 639 reference genome simply does not encode the canonical Sulfolobales sulfur-oxidation gene complement.

**Implication for Phase 3.2:** The new markers will NOT detect S. acidocaldarius DSM 639. This is biologically correct, not a tool failure. The 18% V12 agreement score for Sulfolobus reflects a recipe that pairs sulfur as electron donor (DSMZ Medium 88) with limited gene-content evidence — and the gene-content evidence really is limited. The markers ARE valid for the broader Sulfolobales lineage and will catch Acidianus, Metallosphaera, Saccharolobus, Sulfurisphaera tokodaii, and Sulfuracidifex if any appear in future test sets. Phase 3.2 therefore delivers correct biology for the lineage but does not move the headline V12 score for the existing test-set target.

References:
- Counts JA, Willard DJ, Kelly RM. 2021. Life in hot acid: a genome-based reassessment of the archaeal order Sulfolobales. *Environ Microbiol* 23:3568–3584.
- Willard DJ, Aulitto M, Hahn C, Kelly RM. 2024. Phenotype-driven assessment of the ancestral trajectory of sulfur biooxidation in the thermoacidophilic archaea Sulfolobaceae. *mSystems*.
- Wang R, Lin JQ, Liu XM et al. 2021. Sulfur oxidation in the acidophilic autotrophic Acidithiobacillus. *Front Microbiol* 12:756048. (bacterial; useful as comparison)
- Protze J, Müller F-H, Lauber K et al. 2011. An extracellular tetrathionate hydrolase from the thermoacidophilic archaeon Acidianus ambivalens with an activity optimum at pH 1. *Front Microbiol* 2:68.
- Kletzin A. 1989, 1992. Cloning, sequence analysis, and biochemical characterization of sulfur oxygenase reductase from Acidianus ambivalens (then Desulfurolobus ambivalens). *J Bacteriol*.
- Müller F-H, Bandeiras TM, Urich T et al. 2004. Coupling of the pathway of sulphur oxidation to dioxygen reduction: characterization of a novel membrane-bound thiosulphate:quinone oxidoreductase. *Mol Microbiol* 53:1147-1160.

---

## 2. Proposed marker set

Four markers, in priority order:

| # | Marker key | Coverage | Why this priority |
|---|---|---|---|
| 1 | **tqoDoxD** | Highest — broadly conserved across Sulfolobales sulfur oxidizers | Catches S. acidocaldarius (the headline test-set target). Single best discriminator. |
| 2 | **tqoDoxA** | Same as DoxD (paired enzyme) | DoxD + DoxA hits together raise confidence; either alone is suggestive. |
| 3 | **tetH** | Broad among acidophilic sulfur oxidizers; verified biochemically | Distinct enzymology, complementary signal to TQO. |
| 4 | **sor** | Lineage-restricted (Acidianus, Metallosphaera, Sulfuracidifex, Sulfurisphaera tokodaii) | Won't hit S. acidocaldarius (correctly), but provides coverage for other Sulfolobales encountered in future test sets. |

**Hdr-like (deferred):** Function in archaeal sulfur oxidation is proposed but not biochemically settled to the standard required by Phase 1.5m (clear protein-name match + verified phenotype linkage). Adding Hdr-like would risk false-positive sulfur oxidation calls on methanogen genomes (which encode canonical methanogen Hdr) without clear discriminating sequence features. Deferred until a later sub-phase if needed.

**SAOR (deferred):** Sulfite oxidation is polyphyletic and not Sulfolobales-specific; would not improve archaeal sulfur-oxidation detection meaningfully and could cross-react with bacterial sulfite oxidoreductases. Deferred.

---

## 3. Reference availability — UniProt accession audit

For each marker, candidate accessions verified via direct UniProt lookup. All entries below have been individually fetched and inspected; protein names, organisms, and lengths confirmed.

### 3.1 tqoDoxD — Thiosulfate:quinone oxidoreductase, large subunit

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P97207 | Swiss-Prot | 184 aa | *Acidianus ambivalens* | Gene `doxD`. Canonical Müller et al. 2004 reference. **Primary reference.** |
| Q97XJ3 | TrEMBL | 183 aa | *Saccharolobus solfataricus* P2 (formerly Sulfolobus solfataricus P2) | Gene `doxD`, locus SSO-region. |
| (need 2-4 more for genus diversity) | | | Metallosphaera, Sulfurisphaera, Sulfuracidifex | Will search and add during Task 2 curation |

**Test-set check:** P97207 (A. ambivalens) and Q97XJ3 (S. solfataricus P2) — neither is in the 26-organism dev/blind set. ✓

### 3.2 tqoDoxA — Thiosulfate:quinone oxidoreductase, small subunit

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P97224 | Swiss-Prot | 168 aa | *Acidianus ambivalens* | Gene `doxA`. Paired with P97207 in the doxDA operon. **Primary reference.** |
| Q97XJ4 | TrEMBL | 171 aa | *Saccharolobus solfataricus* P2 | Gene `doxA`, locus SSO1741. Paired with Q97XJ3. |
| (need 2-4 more) | | | Same genera as DoxD | Will search during Task 2 |

**Test-set check:** Same as DoxD. ✓

### 3.3 tetH — Tetrathionate hydrolase

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| G8YXZ9 | Swiss-Prot (reviewed Apr 2018) | 535 aa | *Acidianus ambivalens* | Gene `tth1`. Protze et al. 2011 biochemical characterization. **Primary reference.** |
| F4B6C8 | TrEMBL | 516 aa | *Acidianus hospitalis* W1 | Locus Ahos_1670. |
| (need 2-3 more) | | | Metallosphaera sedula, Acidianus brierleyi | Will search during Task 2 |

**Test-set check:** Acidianus ambivalens, A. hospitalis — neither in test set. ✓

### 3.4 sor — Sulfur oxygenase reductase

| Accession | Status | Length | Source organism | Notes |
|---|---|---|---|---|
| P29082 | Swiss-Prot | 309 aa | *Acidianus ambivalens* | Gene `sor`. Kletzin 1989 / 1992 — founding reference. **Primary reference.** |
| Q977W3 | TrEMBL | 308 aa | *Acidianus tengchongensis* | |
| A4ZIS7 | TrEMBL | 316 aa | *Sulfuracidifex metallicus* (formerly Sulfolobus metallicus) | Lineage outside Acidianus, useful for genus diversity. |
| (need 1 more) | | | *Sulfurisphaera tokodaii* (formerly Sulfolobus tokodaii) | Will search during Task 2 |

**Test-set check:** Acidianus ambivalens, A. tengchongensis, Sulfuracidifex metallicus — none in test set. ✓

**Excluded by name:** P29086 (309-region transporter ORF), P29087 (sor 5'-region ORF), P29088 (77 aa fragment) — flanking-region ORFs from the Kletzin sequencing project, not SOR proteins. Reject as wrong-protein.

---

## 4. Test-set exclusions enforced

The following test-set species are sulfur-oxidation-relevant and have proteins that MUST NOT be used as references:

- **Sulfolobus acidocaldarius** (target organism for Phase 3.2 fix) — no S. acidocaldarius protein may appear in any reference set.
- **Acidithiobacillus ferrooxidans** (bacterial sulfur oxidizer, dev set) — already excluded for soxB.
- **Allochromatium vinosum** (bacterial sulfur oxidizer with reverse-dsr, dev set) — already excluded for soxB.
- **Sulfurimonas denitrificans** (bacterial sulfur oxidizer, dev set) — already excluded for soxB.

For the proposed candidate accessions above, I have manually verified that none originate from any of the 26 test-set species.

---

## 5. Pathway integration plan (preview — for Task 3, after acknowledgment)

The current `sulfur_oxidation` capability has 5 pathway steps with one diagnostic marker (soxB on the thiosulfate-oxidation step). Phase 3.2 will add 3-4 new pathway steps, each with its own diagnostic marker, all under the same capability:

```json
"sulfur_oxidation": {
  "steps": [
    ... existing 5 steps unchanged ...
    {"name": "thiosulfate:quinone oxidoreductase (DoxD)",
     "gapseq_patterns": ["thiosulfate.*quinone", "doxD"],
     "weight": 1.5,
     "diagnostic_marker": "tqoDoxD"},
    {"name": "thiosulfate:quinone oxidoreductase (DoxA)",
     "gapseq_patterns": ["thiosulfate.*quinone", "doxA"],
     "weight": 1.0,
     "diagnostic_marker": "tqoDoxA"},
    {"name": "tetrathionate hydrolase (acidophilic)",
     "gapseq_patterns": ["tetrathionate.*hydrolase", "tetH"],
     "weight": 1.5,
     "diagnostic_marker": "tetH"},
    {"name": "sulfur oxygenase/reductase (cytoplasmic)",
     "gapseq_patterns": ["sulfur oxygenase", "sor"],
     "weight": 1.5,
     "diagnostic_marker": "sor"}
  ]
}
```

This satisfies the prompt's Option B (multi-marker OR logic) without changing the capability framework: the existing scoring logic already treats each step independently, and any single diagnostic marker hit boosts the pathway score for that step.

**Expected detection outcome for Sulfolobus acidocaldarius DSM 639 (REVISED after empirical check):**
- TQO/DoxD hit: NO (best 30.3% / 36% qcov, e=8e-5; below standard thresholds)
- TQO/DoxA hit: NO
- TetH hit: NO (best 30% pident over 14% qcov)
- SOR hit: NO
- Net: sulfur_oxidation capability stays at 0.20 (rejected). Sulfolobus continues to detect as aerobic_chemotrophic primary. Phase 3.2 does not move this organism's V12 score because the genome genuinely lacks the canonical sulfur-oxidation enzyme complement (consistent with Counts/Willard literature classifying it as "limited sulfur biooxidation"). This is biologically correct.

**Expected detection outcome for non-target organisms in test set:**
- Bacterial sulfur oxidizers (Acidithiobacillus, Allochromatium, Sulfurimonas) — already detected via soxB; new markers should NOT cross-react significantly because doxDA/sor/tetH have low sequence identity to bacterial sulfur-handling enzymes.
- Methanogens / anaerobes / heterotrophs — should NOT gain sulfur oxidation. The cross-contamination check in Task 2.4 will verify this empirically.

---

## 6. Recommendation summary for Checkpoint A

**Markers to add (4):** tqoDoxD, tqoDoxA, tetH, sor.

**Markers deferred:** Hdr-like (function not biochemically settled), SAOR (polyphyletic, not Sulfolobales-specific).

**Reference availability:** All 4 markers have at least one Swiss-Prot reviewed entry from a non-test-set organism (P97207 / P97224 / G8YXZ9 / P29082, all from Acidianus ambivalens). Additional TrEMBL refs available across genera for diversity. Target ~4-6 references per marker, covering 3+ genera each. Total 16-24 new accessions.

**Pathway integration:** Add 4 new steps to existing `sulfur_oxidation` capability, each carrying one diagnostic_marker. No capability framework changes needed.

**Test-set discipline:** All proposed primary references have been individually verified against the 26-organism exclusion list. No Sulfolobus acidocaldarius proteins.

**Risk assessment:** Low. Sulfolobales-specific enzymes have low sequence similarity to bacterial sulfur-handling proteins; cross-reactivity with the 8 non-Sulfolobales sulfur-handling test organisms (Acidithiobacillus, Allochromatium, Sulfurimonas, Nitratidesulfovibrio, Chloroflexus, Magnetospirillum, Sulfolobus acidocaldarius itself, Picrophilus) is unlikely but will be verified empirically in Task 2.4.

---

## 7. Stop here for Checkpoint A

Per the Phase 3.2 prompt, I am stopping at this point and waiting for user acknowledgment of the marker set before proceeding to Task 2 (reference curation, BLAST DB build, cross-contamination check) and beyond.
