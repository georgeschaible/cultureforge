# ANME / F.2 Reverse Methanogenesis — Phase 3.6 Literature Review

**Date:** 2026-05-01
**Purpose:** Discriminator design for distinguishing forward methanogenesis from reverse methanogenesis (anaerobic methane oxidation, ANME). The same enzyme (McrA) catalyzes both directions — direction is determined by physiological context (electron acceptor partner enzymes), not by mcrA sequence.

**Result:** Empirical co-occurrence discriminator works **without any new marker curation**. mcrA hit (existing, ≥35% pident threshold) AND any acceptor-partner signal (gapseq nitrate-reduction pathway ≥100% completeness for ANME-2d, or existing dsrAB/mtrC_omcB markers for sulfate/iron-coupled ANME). The signature fires only on Methanoperedens in the 26-organism test set; Methanocaldococcus correctly stays methanogenic.

---

## 1. Biology background

### 1.1 ANME archaea — three lineages, three signature acceptors

ANME (anaerobic methanotrophic) archaea oxidize methane in the absence of O₂, coupling the energy yield to reduction of an alternative electron acceptor. They run the methanogenesis pathway **in reverse**: methane → methyl-CoM → methylene-H₄MPT → methenyl-H₄MPT → ... → CO₂. The same enzymes operate; only the metabolic flux direction is opposite.

Three major lineages, distinguished by acceptor partner:

| Lineage | Acceptor | Partner enzyme(s) | Cultivation status |
|---|---|---|---|
| **ANME-1** | SO₄²⁻ | dsrAB (in syntrophic SRB consortium typically) | Mostly uncultured; freshwater + marine sediments |
| **ANME-2 (a/b/c)** | SO₄²⁻ | dsrAB | Mostly uncultured; marine sediments |
| **ANME-2d** (Methanoperedens) | NO₃⁻ | narG-related nitrate reductase, divergent from canonical bacterial narG | **Pure-culture cultivation achieved** (Haroon et al. 2013) |
| **ANME-3** | SO₄²⁻ | dsrAB | Mostly uncultured; marine sediments |
| Iron-coupled ANME (rare) | Fe(III) | mtrC/omcB-like | Environmental enrichments only |

### 1.2 Why mcrA cannot distinguish forward from reverse

McrA is the methyl-coenzyme M reductase α-subunit. The enzyme is bidirectional in vitro — same fold, same active site, same EC 2.8.4.1. Forward methanogens use it to reduce methyl-CoM to methane (with H₂ as electron donor). ANME archaea use the same protein in the reverse direction (CH₄ → methyl-CoM with electrons flowing toward an alternative acceptor downstream).

Some early work suggested that ANME mcrA proteins could be phylogenetically distinguished from forward methanogen mcrA via sequence trees. However, this is a noisy signal (lineage-dependent, with significant overlap), not a single-residue discriminator. **The reliable discriminator is co-occurrence with an acceptor-partner enzyme** — forward methanogens lack nitrate, sulfate, or iron reduction machinery beyond their canonical CO₂-reducing electron transport.

### 1.3 Cultivation conditions for ANME

Anaerobic methane oxidation cultivation is notoriously slow (doubling times of weeks to months) due to:
- Low energy yield from methane oxidation coupled to alternative acceptors (especially sulfate at ΔG ≈ -16 kJ/mol)
- Many ANME live in syntrophic consortia with sulfate-reducing bacterial partners (single-organism cultivation often fails)
- Strict anaerobic requirements

Only Methanoperedens nitroreducens (ANME-2d, nitrate-coupled) has been brought to pure culture readily — its higher energy yield from CH₄ + NO₃⁻ (ΔG ≈ -517 kJ/mol) supports growth without sulfate-reducer partners.

Canonical media:
- **Anaerobic atmosphere** (N₂/CO₂ or CH₄/CO₂)
- **Methane in headspace** (substrate, ~20% CH₄, balance N₂)
- **Dissolved electron acceptor**: NaNO₃ (10-15 mM) for ANME-2d; Na₂SO₄ (10-20 mM) for ANME-1/2/3
- **Bicarbonate buffer** (~2.5 g/L NaHCO₃)
- **Reducing agent** (Na₂S or cysteine)
- **Mesophilic** for ANME-2d (~30°C); cold (4-15°C) for marine ANME
- **Slow growth** — long incubation times required

### 1.4 Literature

- Knittel K, Boetius A. 2009. Anaerobic oxidation of methane: progress with an unknown process. *Annu Rev Microbiol* 63:311-334.
- Haroon MF et al. 2013. Anaerobic oxidation of methane coupled to nitrate reduction in a novel archaeal lineage. *Nature* 500:567-570. (ANME-2d / Methanoperedens nitroreducens discovery)
- Timmers PHA et al. 2017. Reverse methanogenesis and respiration in methanotrophic archaea. *Archaea* 2017:1654237.
- McGlynn SE. 2017. Energy metabolism during anaerobic methane oxidation in ANME archaea. *Microbes Environ* 32:5-13.
- Welte CU et al. 2016. Nitrate- and nitrite-dependent anaerobic oxidation of methane. *Environ Microbiol Rep* 8:941-955.

---

## 2. Empirical Methanoperedens enzyme content verification

The Phase 3.6 discriminator must work on the test-set target. Empirical check via current `genome_diagnostic_markers` table + `genome_pathways` table:

### 2.1 Methanoperedens (gid=28) marker hits

| Marker | n positive_call | Max pident | Notes |
|---|---|---|---|
| **mcrA** | **5** | **70.1%** | ✅ Real methanogenesis-pathway machinery (operating in reverse) |
| mcrBG | 6 | 75.8% | mcr beta-gamma subunits, paired with mcrA |
| acsB_cdhC | 8 | 65.2% | Wood-Ljungdahl carbonyl branch — used in reverse for AcCoA → CH₄ pathway |
| cooS_cdhA | 16 | 45.9% | CO dehydrogenase, also WL-related |
| nifH | 10 | 67.2% | Methanoperedens fixes N₂ |
| **dsrAB** | **0** | — | ✅ Correctly absent (not sulfate-coupled) |
| **mtrC_omcB** | **0** | — | ✅ Correctly absent (not iron-coupled in this strain) |
| **nrfA** | **0** | — | ✅ Correctly absent (not DNRA — Methanoperedens uses NO₃⁻ but converts to N₂ downstream, not NH₄⁺) |
| **nxrA** | **0** (best 48% pident, sub-threshold) | 48.0% | The 48% hit IS the narG-related nitrate reductase cross-reactivity (Phase 3.3 documented this same signal) |

### 2.2 narG/napA presence in Methanoperedens — direct empirical check

Built temporary BLAST DB from 3 canonical narG references (B. subtilis P42175, Bradyrhizobium P85097, Stutzerimonas A4VHZ2; E. coli P09152 excluded as test-set organism). BLAST against Methanoperedens proteome:

| Threshold | Result |
|---|---|
| evalue ≤ 1e-30 | **0 hits** |
| evalue ≤ 100 (very loose) | Best hit 24.5% pident, 56% qcov, e=1.15e-36 (B. subtilis narG × FZMP01000203.1_78) |

**Methanoperedens nitroreducens encodes nitrate reductase but at very low BLAST identity (<25% pident) to canonical bacterial narG.** This is consistent with the literature — Methanoperedens uses a periplasmic napAB-like architecture distinct from canonical narGHIJ.

### 2.3 The reliable signal: gapseq pathway annotation

Where direct BLAST fails (low identity to canonical narG), gapseq's UniRef-based pathway annotation succeeds:

| Pathway | Completeness | Predicted |
|---|---|---|
| nitrite oxidation | 100% | ✓ |
| **nitrate reduction III (dissimilatory)** | **100%** | ✓ |
| **nitrate reduction VIIIb (dissimilatory)** | **100%** | ✓ |
| **nitrate reduction IX (dissimilatory)** | **100%** | ✓ |
| **nitrate reduction IV (dissimilatory)** | **100%** | ✓ |
| nitrate reduction (cytochrome c) — gapseq R247-RXN | UniRef50_A0A0P7ZF78 at **68.5% pident** (good_blast, full) | ✓ |

**4 dissimilatory nitrate-reduction pathways at 100% completeness in Methanoperedens — overwhelming evidence of nitrate-reduction capability.** gapseq's UniRef-based detection is the right tool for this divergent enzyme family (it uses much broader reference sets than CultureForge's curated marker BLAST).

### 2.4 Cross-organism control: Methanocaldococcus jannaschii (gid=8)

| Marker / Pathway | Methanocaldococcus | ANME signature would fire? |
|---|---|---|
| mcrA positive | 10 hits at 83.7% pident | ✅ mcrA criterion met |
| dsrAB positive | 0 | — |
| mtrC_omcB positive | 0 | — |
| Dissimilatory nitrate reduction at 100% | **0** | ❌ acceptor-partner criterion NOT met |
| Result | | **❌ correctly stays methanogenic** |

### 2.5 Cross-organism check across all 26 test genomes

Joining mcrA hits + nitrate-reduction pathway:

| gid | Organism | mcrA positive | Nitrate-red pwy @ 100% | ANME signature fires? |
|---|---|---|---|---|
| 8 | Methanocaldococcus jannaschii | 10 (83.7% pident) | 0 | ❌ NO (forward methanogen) |
| 15 | Campylobacter jejuni | 0 | 1 | ❌ NO (no mcrA — DNRA-capable, classified aerobic_chemotrophic) |
| **28** | **Methanoperedens nitroreducens** | **5 (70.1% pident)** | **4** | ✅ **YES (TARGET)** |
| 32 | E. coli | 0 | 4 | ❌ NO (no mcrA — DNRA/denitrifier, classified aerobic_chemotrophic) |
| 22 others | various | 0 | 0 | ❌ NO |

**Only Methanoperedens fires the ANME signature.** Clean discrimination achieved without any new marker curation.

---

## 3. Discriminator design recommendation

### 3.1 ANME signature logic

```
ANME signature = mcrA marker positive_call (existing threshold: pident≥35, qcov≥70, evalue≤1e-30)
                  AND ANY of:
                    A. Dissimilatory nitrate reduction pathway @ ≥100% completeness  → ANME-2d (nitrate-coupled)
                    B. dsrAB marker positive_call (existing)                          → ANME-1/2/3 (sulfate-coupled)
                    C. mtrC_omcB marker positive_call (existing)                      → Iron-coupled ANME (rare)
```

### 3.2 Capability framework extension

Per the Phase 3.6 prompt's Option B: add a new field `essential_marker_OR` alongside the existing `essential_marker_AND`. Capability detection logic:

```python
# All AND markers required:
if not all(marker_hit(m) for m in essential_marker_AND):
    return capped at 0.40 (essential_marker missing)

# At least ONE OR marker required (when list non-empty):
if essential_marker_OR and not any(or_signal_hit(m) for m in essential_marker_OR):
    return capped at 0.40 (no acceptor partner)
```

For ANME, the `essential_marker_OR` list contains a mix of marker names AND a special pathway-pattern entry. Need to extend the syntax to support both:

```json
"essential_marker_AND": ["mcrA"],
"essential_marker_OR": [
  "dsrAB",
  "mtrC_omcB",
  {"type": "pathway_pattern", "pattern": "nitrate reduction.*dissimilatory", "min_completeness": 100}
]
```

The pathway-pattern entry checks `genome_pathways` for any row matching the pattern at the given completeness threshold. This handles Methanoperedens's divergent narG (where direct BLAST fails but gapseq pathway annotation succeeds).

### 3.3 Forward methanogenesis suppression rule

Implementation in compose_recipe.py mode picker:

```python
# After the existing specific-mode priority loop, before facultative-anaerobe rule:
if "anme_reverse_methanogenesis" in detected_set and \
   mode_confidence.get("anme_reverse_methanogenesis", 0) >= 0.50:
    # ANME signature fired — Methanoperedens-class organism.
    # Suppress methanogenic mode at recipe-time even though mcrA detected forward
    # methanogenesis capability. The capability profile preserves mcrA detection
    # (it's genuinely there), but the cultivation mode is reverse, not forward.
    return "anme_reverse_methanogenesis"
```

### 3.4 New mode group

Add `anme_reverse_methanogenic` (or similar) to `CULTIVATION_MODE_GROUPS` in capability_detectors.py, mapping the new capability into its own mode group. The mode picker then naturally distinguishes it from `methanogenic` mode group.

Or, simpler: keep methanogenic capability mapped to methanogenic group, ANME capability mapped to its own group, and use the suppression rule above to break ties at recipe-time.

### 3.5 Recipe composer routing

New `_compose_anme_recipe()` function:
- Atmosphere: anaerobic CH₄ + N₂ (or CH₄ + CO₂ for marine ANME)
- Acceptor selection branched by which signature element fired:
  - Pathway pattern match → NaNO₃ ~10-15 mM (ANME-2d)
  - dsrAB marker hit → Na₂SO₄ ~10-20 mM (sulfate-coupled, slow)
  - mtrC_omcB marker hit → Fe(III) citrate (iron-coupled, rare)
- Bicarbonate buffer, Na₂S reducing agent, near-neutral pH, mesophilic temperature
- Cultivation difficulty note: long incubation times, may require enrichment culture / syntrophic partners
- Two new thermodynamic templates: anme_nitrate_coupled (ΔG ≈ -517 kJ/mol), anme_sulfate_coupled (ΔG ≈ -16 kJ/mol)

### 3.6 Atmosphere category

Update `_cf_atmosphere_category` in recipe_comparison.py: when CH₄ + (no O₂ / no air), category = "anme" (distinct from "methanotroph" which has O₂, "methanogen" which has H₂/CO₂, and "anaerobic" which has neither CH₄ nor H₂).

---

## 4. Recommendation summary for Checkpoint A

**Markers to add: NONE.** The discriminator uses existing markers (mcrA, dsrAB, mtrC_omcB) plus gapseq pathway annotation as the narG proxy. This avoids curating divergent narG references at sub-30% pident (which would risk widespread false positives).

**Framework extension:** new `essential_marker_OR` field in pathway_definitions.json schema; entries can be marker names OR pathway-pattern dicts. Implementation in capability_detectors.py.

**Discriminator logic:** mcrA AND (nitrate-reduction-pathway @ 100% complete OR dsrAB OR mtrC_omcB).

**Empirical validation against test set:**
- ✅ Methanoperedens (gid=28): mcrA at 70.1% + 4 nitrate-reduction pathways at 100% → ANME signature **fires** (TARGET)
- ✅ Methanocaldococcus (gid=8): mcrA at 83.7% but ZERO nitrate/sulfate/iron acceptor signals → ANME signature does **NOT fire** (forward methanogen, correct)
- ✅ E. coli, Campylobacter: nitrate-reduction pathways present but NO mcrA → ANME signature does **NOT fire** (DNRA/denitrifier, not ANME)
- ✅ 22 other test organisms: neither criterion met → no firing

**Forward methanogenesis suppression:** mode-picker rule routes ANME-detected organisms to anme_reverse_methanogenesis primary, preserving the mcrA detection in the capability profile but flipping recipe-time classification.

**Recipe routing:** new `_compose_anme_recipe()` with acceptor-aware branching (NaNO₃ for ANME-2d via pathway match, Na₂SO₄ for sulfate-coupled, Fe(III) for iron-coupled). Anaerobic CH₄+N₂ atmosphere. New "anme" atmosphere category. Two new thermodynamic templates.

**Test-set impact (predicted):**
- **Methanoperedens (gid=28)**: classification flips from methanogenic primary (currently wrong; recipe is H₂/CO₂ at 100°C-style methanogen recipe, biologically wrong for ANME-2d) to anme_reverse_methanogenesis primary with anaerobic CH₄+N₂ atmosphere + 10 mM NaNO₃ + bicarbonate buffer. V12 score should improve from current 28% to a higher band depending on how well the recipe matches BacDive Methanoperedens cultivation references.
- **Methanocaldococcus**: unchanged (still methanogenic primary, no acceptor partners).
- **All 24 other organisms**: unchanged.

**Risk assessment: LOW.** The empirical co-occurrence signature is unique to Methanoperedens in the 26-organism test set. The framework extension (essential_marker_OR with pathway-pattern support) is a clean addition that doesn't disrupt existing capabilities. No mcrA threshold changes needed.

---

## 5. Stop here for Checkpoint A

Per the Phase 3.6 prompt, stopping for user acknowledgment before proceeding to Tasks 2-7 (capability framework extension, recipe composer routing, atmosphere categorization, cross-organism verification, V12 validation, optional sentinel, documentation closeout).

**Key questions to confirm:**

1. **Discriminator design = mcrA + (nitrate pathway @ 100% OR dsrAB OR mtrC_omcB)** with NO new marker curation?
2. **essential_marker_OR field with pathway-pattern entry support** as the framework extension approach?
3. **Forward methanogenesis suppression at recipe-time mode picker** rather than capability-detector level (preserves the mcrA finding in capability profile but flips recipe routing)?
4. **Single ANME capability with acceptor-aware recipe routing**, rather than three separate capabilities (anme_nitrate, anme_sulfate, anme_iron)?
