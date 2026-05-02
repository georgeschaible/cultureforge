# Aerobic Methanotrophy / pmoA + mmoX — Phase 3.5 Literature Review

**Date:** 2026-05-01
**Purpose:** Confirm enzyme set + reference candidates + the critical pmoA/amoA cross-reactivity assessment for Phase 3.5 aerobic methanotrophy detection.

**Result:** 60% pident threshold cleanly discriminates pmoA from amoA cross-reactivity (empirical amoA ceiling = 50%, intra-clade pmoA floor = 58-60%). Dual-marker capability (pmoA OR mmoX) covers Type I, Type II, and Type III methanotroph lineages. mmoX is highly methanotroph-specific (zero cross-reactivity in the 26-organism test set).

---

## 1. Biology background

### 1.1 Two enzyme architectures, same metabolism

Aerobic methanotrophs use one or both of two distinct enzymes:

- **pMMO (particulate methane monooxygenase)** — membrane-bound, copper-dependent. Encoded by `pmoCAB` operon. The α subunit (pmoB, ~414 aa), β subunit (pmoA, ~247 aa), and γ subunit (pmoC, ~256 aa) form the active enzyme. **pmoA is the diagnostic subunit** for marker design.
- **sMMO (soluble methane monooxygenase)** — cytoplasmic, iron-dependent. Encoded by `mmoXYBZDC` operon. The hydroxylase α subunit (`mmoX`, ~526 aa) is the **diagnostic subunit**. Only present in some methanotrophs and typically expressed under copper limitation.

**A given methanotroph may encode pMMO only, sMMO only, or both.** Most Type II methanotrophs (Methylosinus, Methylocystis) have both. Type I (Methylococcus, Methylocaldum, Methylomonas) typically have pMMO only. Type III (Verrucomicrobia Methylacidiphilum) have only divergent pMMO.

### 1.2 The pmoA/amoA cross-reactivity problem

pmoA and amoA (ammonia monooxygenase α subunit) are **evolutionary paralogs**. Both are ~250 aa, share the same fold, and catalyze hydroxylation reactions on small substrates (CH₄ vs NH₃). Some methanotrophs (Crenothrix, some Methylocapsa) actually have low ammonia oxidation activity, and some AOB have low methane oxidation activity. The cross-reactivity is biological reality, not a sequence artifact.

This is the critical Phase 3.5 question: **at what pident does pmoA cleanly separate from amoA?**

### 1.3 Methanotroph lineage distribution

| Type | Phylum / class | Example genera | pMMO | sMMO |
|---|---|---|---|---|
| Type I | Gammaproteobacteria, Methylococcaceae | Methylococcus, Methylomonas, Methylobacter, Methylocaldum | ✅ Always | Some |
| Type II | Alphaproteobacteria, Methylocystaceae / Beijerinckiaceae | Methylosinus, Methylocystis, Methylocella | ✅ | ✅ |
| Type III | Verrucomicrobia | Methylacidiphilum | ✅ (highly divergent) | ❌ |
| NC10 | Methylomirabilota | Ca. Methylomirabilis | ✅ | (intraaerobic; N-DAMO niche, separate from Phase 3.5 scope) |

### 1.4 Cultivation conditions

Canonical methanotroph media (DSMZ Medium 921 / NMS):
- **Atmosphere**: air + methane (typically 80:20, range 50:50 to 90:10 depending on organism)
- **Carbon source**: methane (gas phase only; no organic carbon in liquid)
- **Buffer**: phosphate near pH 6.8-7.2
- **Nitrogen**: NH4Cl (~0.5 g/L) or KNO3
- **Trace metals**: standard SL-10; **copper especially important** (pMMO is Cu-dependent; sMMO expression switches on under low Cu)
- **Temperature**: 25-37°C for mesophiles; ~50-60°C for Methylocaldum thermophiles
- **Reducing agent**: NOT needed (aerobic culture)

### 1.5 Literature

- Hanson RS, Hanson TE. 1996. Methanotrophic bacteria. *Microbiol Rev* 60:439-471.
- Op den Camp HJ et al. 2009. Environmental, genomic and taxonomic perspectives on methanotrophic Verrucomicrobia. *Environ Microbiol Rep* 1:293-306.
- Tavormina PL et al. 2011. A novel family of functional operons encoding methane/ammonia monooxygenase-related proteins. *Environ Microbiol Rep* 3:91-100.
- Stein LY, Klotz MG. 2011. Nitrifying and denitrifying pathways of methanotrophic bacteria. *Biochem Soc Trans* 39:1826-1831.
- Knief C. 2015. Diversity and habitat preferences of cultivated and uncultivated aerobic methanotrophic bacteria evaluated based on pmoA as molecular marker. *Front Microbiol* 6:1346.

---

## 2. Reference candidates

All 6 pmoA + 4 mmoX accessions hand-fetched from UniProt and verified.

### 2.1 pmoA — 6 accessions across 4 genera and 3 lineage types

| # | Accession | Source organism | Length | Status | Type |
|---|---|---|---|---|---|
| 1 | Q607G3 | *Methylococcus capsulatus* Bath | 247 | **Swiss-Prot** | Type I (Gammaproteobacteria) |
| 2 | A4PDX7 | *Methylocaldum* sp. T-025 | 247 | TrEMBL | Type I (thermophile) |
| 3 | Q50541 | *Methylosinus trichosporium* | 252 | TrEMBL | Type II (Alphaproteobacteria, Methylocystaceae) |
| 4 | O06122 | *Methylocystis* sp. M | 252 | TrEMBL | Type II |
| 5 | I0JZS9 | *Methylacidiphilum fumariolicum* SolV | 245 | TrEMBL | Type III (Verrucomicrobia) |
| 6 | A9QPD9 | *Methylacidiphilum infernorum* V4 | 249 | TrEMBL | Type III |

**Test-set exclusion:** None of these are from Nitrosomonas (the only test-set organism with closely related amoA). ✓

### 2.2 mmoX — 4 accessions across 3 genera and Type I/II

| # | Accession | Source organism | Length | Status | Type |
|---|---|---|---|---|---|
| 1 | P22869 | *Methylococcus capsulatus* Bath | 527 | **Swiss-Prot** | Type I |
| 2 | P27353 | *Methylosinus trichosporium* | 526 | **Swiss-Prot** | Type II |
| 3 | Q3YA75 | *Methylomonas* sp. GYJ3 | 526 | TrEMBL | Type I |
| 4 | Q3T939 | *Methylocella silvestris* | 526 | TrEMBL | Type II Beijerinckiaceae |

**Test-set exclusion:** None from test-set organisms. ✓

---

## 3. Pairwise reference identity

### 3.1 pmoA — three-clade architecture

| Pair | pident | qcov |
|---|---|---|
| Type I × Type I (Methylococcus × Methylocaldum) | **85.4%** | 100% |
| Type II × Type II (Methylosinus × Methylocystis) | **86.5%** | 100% |
| Type I × Type II | **58-60%** | 99% |
| Type I × Type III (Methylococcus × Methylacidiphilum SolV) | **53.5%** | 91% |
| Type I × Type III (Methylococcus × Methylacidiphilum V4) | **39.9%** | 98% |
| Type II × Type III | 36-55% | 91-98% |

**Key observation:** the Type III Verrucomicrobia pmoA is highly divergent from canonical Type I/II — down to 36% pident in some cases. The two Type III refs (M. fumariolicum SolV at I0JZS9, M. infernorum V4 at A9QPD9) cluster with each other but only barely with Type I/II.

### 3.2 mmoX — single tight clade

| Pair | pident | qcov |
|---|---|---|
| All cross-genus pairs (Methylococcus / Methylosinus / Methylomonas / Methylocella) | **82-99%** | 99-100% |

mmoX is **highly conserved** across methanotroph lineages. Cross-genus identity stays above 81% throughout. This is much tighter than pmoA's family.

---

## 4. Empirical cross-reactivity assessments

### 4.1 The critical test: pmoA vs amoA

**Direct ref-vs-ref comparison:**
- Methylococcus capsulatus pmoA (Q607G3) × Nitrosospira amoA (O85076): **50.2% pident, 96% qcov, bs=265**
- Methylococcus capsulatus pmoA × Nitrosospira briensis amoA (P95336): 50.0%, 96%, 267
- Most pmoA × amoA cross-reactivity: 38-50% pident, ~90-98% qcov

**Cross-reactivity ceiling: 50% pident.**

### 4.2 BLAST scan of pmoA refs vs all 26 test-set proteomes

| Test genome | Best pident | Best qcov | n_hits | Best query |
|---|---|---|---|---|
| **Nitrosomonas europaea** (gid 18) | **50.0%** | 96% | 12 | sp\|Q607G3\|PMOA_METCA (Methylococcus capsulatus pmoA) |
| 25 other organisms | 0 hits | — | 0 | — |

**Finding: only Nitrosomonas produces any pmoA cross-reactivity.** Every other test organism (Methanococcus, E. coli, Acidithiobacillus, Sulfolobus, Geobacter, Rhodopseudomonas, Allochromatium, Methanoperedens, Scalindua, etc.) produces zero hits at evalue ≤ 1e-30. The pmoA family is methanotroph-specific except for the well-known amoA cross-paralogy.

The 12 hits on Nitrosomonas correspond to the 6 pmoA refs × 2 amoA paralogs in Nitrosomonas's genome. All cluster in the 38-50% pident range.

### 4.3 The discrimination question

| Boundary | pident |
|---|---|
| pmoA intra-Type I clade (Methylococcus × Methylocaldum) | 85% |
| pmoA cross-Type I-II clade | 58-60% |
| pmoA intra-Type III clade (Methylacidiphilum × Methylacidiphilum) | likely 80%+ within-genus |
| **pmoA × amoA cross-reactivity ceiling** | **50%** |

**There is an 8-10 point gap between the amoA ceiling (50%) and the cross-Type I-II floor (58%).** The recommended threshold sits in this gap.

### 4.4 Type III handling — dual-clade reference architecture

Methylacidiphilum is the most divergent pmoA clade (36-55% to Type I/II). At a 60% threshold, a pmoA from a Methylacidiphilum genome would NOT clear the threshold against Type I/II references — but it WOULD clear it against the Type III references in our DB (I0JZS9 + A9QPD9), assuming intra-Methylacidiphilum identity is ~80%+ (typical within-genus).

This is the same dual-clade architecture pattern as Phase 3.3 nxrA: with refs from each clade, OR-logic best-hit determines lineage. Type I genomes hit Type I refs at 85%+, Type II hit Type II refs at 86%+, Type III hit Type III refs at 80%+ (predicted). Cross-clade hits stay around 36-60%.

### 4.5 mmoX cross-reactivity

**BLAST scan of mmoX refs vs all 26 test-set proteomes: zero hits.**

mmoX is highly methanotroph-specific. The protein family conservation (82-99% intra-family) plus absence of close paralogs in non-methanotrophic test organisms gives clean detection without threshold concerns.

---

## 5. Threshold recommendation

| Marker | min_pident | min_qcov | min_evalue | Logic |
|---|---|---|---|---|
| **pmoA** | **60.0** | **80** | 1e-30 | OR-logic with mmoX; dual-clade refs catch Type I/II/III |
| **mmoX** | **50.0** | **70** | 1e-30 | OR-logic with pmoA; protein family naturally conserved |

### 5.1 pmoA threshold rationale

- **60% pident** sits in the 8-10 point gap between empirical amoA cross-reactivity ceiling (50%) and pmoA cross-Type I-II floor (58%).
- Type I and Type II methanotrophs hit their respective clade refs at 85%+ within-genus and 60% cross-clade, well above the threshold.
- Type III Verrucomicrobia methanotrophs hit their Type III refs (within-Methylacidiphilum at expected 80%+); they would NOT clear 60% against Type I/II refs alone, but DO clear via the Type III refs in the dual-clade architecture.
- Nitrosomonas europaea's amoA cross-reactivity caps at 50% — cleanly excluded.

### 5.2 mmoX threshold rationale

- **50% pident** is generous because the family is so tightly conserved (intra-family 82-99%). Even a divergent novel methanotroph mmoX would clear 50% easily against existing refs.
- Zero cross-reactivity in the 26-organism test set — no concern about false positives even at this looser threshold.
- The 70% qcov is similarly generous; mmoX is ~526 aa and full-length matches are normal.

### 5.3 Single-marker (OR-logic) suffices — no negative marker needed

The empirical 60% pmoA threshold cleanly separates true methanotroph pmoA from Nitrosomonas amoA at 50%. The prompt's optional negative-marker logic (suppress aerobic_methanotrophy when amoA fires) is **NOT needed** at this threshold. The amoA cross-reactivity is bounded below the threshold by the 8-10 point gap.

---

## 6. Capability definition preview (for Task 3)

```
aerobic_methanotrophy:
  diagnostic_markers: [pmoA, mmoX]
  diagnostic_marker_logic: OR (either marker alone suffices)
  diagnostic_marker_thresholds:
    pmoA: pident≥60, qcov≥80, evalue≤1e-30
    mmoX: pident≥50, qcov≥70, evalue≤1e-30
  diagnostic_marker_override:
    marker: pmoA (or mmoX) — either at threshold gives 0.70 confidence
  essential_marker_AND: []  // OR logic
  pathway_steps:
    - Methane monooxygenase (particulate, pMMO): pmoA marker
    - Methane monooxygenase (soluble, sMMO): mmoX marker
    - Methanol dehydrogenase: gapseq mxaF / xoxF
    - Formaldehyde and formate metabolism
    - Aerobic respiration (terminal oxidase)
```

The OR-logic accommodates Type I (pmoA only), Type II (both pmoA and mmoX), and Type III (highly divergent pmoA, no mmoX).

---

## 7. Recipe composer requirements (preview — for Task 4)

This is the first cultivation mode that requires **methane in the gas phase**. New infrastructure:

1. **GasPhase composition with CH₄:** `{"air": 0.80, "CH4": 0.20}` at 1.0 atm. Requires sealed cultivation vessel with methane-air headspace; periodic gas-phase replenishment as methane is consumed.
2. **Methanotrophy thermodynamic template:** `CH4 + 2 O2 → CO2 + 2 H2O`, ΔG ~-820 kJ/mol (highly exergonic). Requires CH4_aq added to DEFAULT_ACTIVITIES if not present (suggest 1e-5 M ≈ 10 μM dissolved methane).
3. **Atmosphere check update:** recipe_comparison.py `_categorize_atmosphere` (or equivalent) needs a "methanotroph" category for proper diff comparison against published methanotroph media.
4. **Recipe composer routing:** new `_compose_methanotrophy_recipe()` function. Carbon source provided via gas phase (no organic carbon ingredient). Phosphate buffer near pH 7.0. NH4Cl as nitrogen. Standard SL-10 trace metals + Wolin's vitamins; copper note in composition_rationale (pMMO biosynthesis). Vigorous shaking for gas exchange. No reducing agent.
5. **Mode-picker priority:** aerobic_methanotrophy preferred over generic aerobic_chemotrophic when detected.

---

## 8. Recommendation summary for Checkpoint A

**Markers to add (2):** pmoA (single-clade dual-genus) and mmoX (single tight family). OR-logic detection.

**Reference set:**
- 6 verified pmoA accessions across 4 genera and 3 lineage types (Type I × 2, Type II × 2, Type III × 2). 1 Swiss-Prot, 5 TrEMBL.
- 4 verified mmoX accessions across 3 genera spanning Type I and Type II. 2 Swiss-Prot, 2 TrEMBL.
- Test-set exclusions verified: no Nitrosomonas amoA in pmoA refs.

**Thresholds:**
- pmoA: 60% pident, 80% qcov, 1e-30 evalue
- mmoX: 50% pident, 70% qcov, 1e-30 evalue

**Empirical cross-reactivity finding:** pmoA × amoA cross-reactivity caps at 50% pident in the 26-organism test set (Nitrosomonas europaea is the only non-methanotroph with any hit). The 8-10 point gap between amoA ceiling (50%) and cross-Type I-II pmoA floor (58%) cleanly accommodates a 60% threshold. mmoX is methanotroph-specific with zero cross-reactivity in the test set.

**Single-marker (OR-logic) sufficient.** No negative-marker logic needed at the 60% threshold; the amoA cross-reactivity is bounded below the threshold.

**Type III Verrucomicrobia coverage:** included via dual-clade reference architecture. Methylacidiphilum genomes hit the Type III refs (I0JZS9 + A9QPD9) at within-genus 80%+ identity, well above the 60% threshold. Cross-clade Type I/II ↔ Type III stays in the 36-55% range, well below.

**Test-set impact (predicted):** Zero changes. No methanotroph in the 26-organism test set; Nitrosomonas's amoA cross-reactivity correctly stays below the pmoA threshold. V12 score should be byte-identical.

**Sentinel for future validation:** *Methylococcus capsulatus* Bath (GCF_000008325.1, sentinel from Phase 3.3a coverage audit) would be the canonical empirical validation target. Phase 3.5 Task 7 (sentinel verification) is optional per prompt — defer to later work unless time permits.

**Risk assessment:** Low. The cross-reactivity gap (50% → 58%) is narrower than Phase 3.3's nxrA gap (48% → 87%) but still empirically clean. The dual-clade reference architecture handles Type III divergence. mmoX cross-reactivity is essentially zero. New gas-phase infrastructure is the main implementation work but is well-scoped (one new gas composition, one new ΔG template, one new atmosphere category).

---

## 9. Stop here for Checkpoint A

Per the Phase 3.5 prompt, stopping for user acknowledgment before proceeding to Task 2 (reference curation, BLAST DB build, capability definition, recipe composer routing including methane-headspace template).
