"""Pathway-integrity detectors for CultureForge metabolic capability profiling.

Replaces the sequential decision tree in synthesize_denovo.py with parallel
pathway-integrity detectors that evaluate whether an organism has a complete
functional pipeline for each metabolism.  Detection is based on:
  - Pathway step coverage (weighted, from gapseq pathway data)
  - Diagnostic marker BLAST hits (high-weight evidence)
  - Cofactor biosynthesis capability
  - Transporter presence (positive-only bonus, asymmetric)
  - Negative markers (multiplicative penalty)

New metabolisms are added by editing data/pathway_definitions.json — no code
changes required.

Phase 1: builds alongside existing determine_energy_metabolism().
Phase 2 (next session): wires into recipe synthesis.

See CAPABILITY_DETECTORS.md for design philosophy and usage.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from qc_gate import QualityVerdict, evaluate_genome_quality
from run_marker_blast import get_marker_hits

_ROOT = Path(__file__).parent
PATHWAY_DEFS_PATH = _ROOT / "data" / "pathway_definitions.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PathwayStepEvidence:
    """Evidence for a single pathway step."""
    step_name: str
    weight: float
    found: bool
    best_completeness: float
    diagnostic_marker_hit: Optional[dict] = None
    # Future: populated when RNA-seq data is loaded
    expression_tpm: Optional[float] = None
    expressed_above_threshold: Optional[bool] = None


@dataclass
class TransporterEvidence:
    """Evidence for a transporter associated with a pathway."""
    transporter_name: str
    found: bool
    count: int
    optional: bool


@dataclass
class Capability:
    """Result of pathway-integrity detection for one metabolism."""
    name: str
    detected: bool
    confidence: float                           # 0.0 to 1.0
    pathway_completeness: float                 # weighted fraction of steps found
    step_evidence: List[PathwayStepEvidence]     = field(default_factory=list)
    transporter_evidence: List[TransporterEvidence] = field(default_factory=list)
    cofactor_coverage: float                    = 0.0
    negative_markers_present: List[str]         = field(default_factory=list)
    diagnostic_markers_hit: List[str]           = field(default_factory=list)
    evidence_summary: List[str]                 = field(default_factory=list)
    uncertainty_flags: List[str]                = field(default_factory=list)


@dataclass
class CapabilityProfile:
    """Complete metabolic capability profile for a genome."""
    genome_id: int
    quality_verdict: QualityVerdict
    capabilities: List[Capability]              # ALL detectors, including negatives
    primary_metabolisms: List[str]              # subset with confidence >= 0.50
    cultivation_modes: List[Dict] = field(default_factory=list)  # Phase 1.5f
    recommended_action: str = "flag_uncertain"
    escalation_rationale: Optional[str] = None


# Cultivation mode groupings (Phase 1.5f)
CULTIVATION_MODE_GROUPS = {
    "phototrophic": ["Anoxygenic phototrophy (purple",
                     "Anoxygenic phototrophy (green",
                     "Oxygenic phototrophy"],
    "aerobic_chemotrophic": ["Aerobic respiration"],
    "anaerobic_respiratory": ["Dissimilatory sulfate reduction",
                               "Denitrification",
                               "Dissimilatory Fe(III) reduction",
                               "Anaerobic ammonium oxidation",
                               "Reductive dehalogenation",
                               "Dissimilatory nitrate reduction to ammonium"],
    "methanogenic": ["Methanogenesis"],
    "methanotrophic": ["Aerobic methanotrophy"],
    "anme_reverse_methanogenic": ["Anaerobic methane oxidation"],
    "fermentative": ["Substrate-level phosphorylation fermentation"],
    "syntrophic": ["Syntrophy"],
    "lithotrophic_aerobic": ["Aerobic ammonia oxidation",
                              "Sulfur/sulfide/thiosulfate oxidation",
                              "Acidophilic Fe(II) oxidation",
                              "Aerobic nitrite oxidation"],
    "acetogenic": ["Acetogenesis"],
    "halophilic_with_rhodopsin": ["Bacteriorhodopsin"],
}


def determine_cultivation_modes(capabilities: List[Capability],
                                 threshold: float = 0.50) -> List[Dict]:
    """Group detected capabilities into cultivation modes.

    A cultivation mode is active if any capability within its group is
    detected with confidence >= threshold.  When multiple modes are active,
    they are co-primary and the recipe synthesizer should generate
    alternative recipes for each.
    """
    active_modes = []

    for mode_name, mode_patterns in CULTIVATION_MODE_GROUPS.items():
        active_caps = []
        for cap in capabilities:
            if not cap.detected or cap.confidence < threshold:
                continue
            if any(pat.lower() in cap.name.lower() for pat in mode_patterns):
                active_caps.append((cap.name, cap.confidence))
        if active_caps:
            active_modes.append({
                "mode": mode_name,
                "capabilities": active_caps,
                "max_confidence": max(c[1] for c in active_caps),
            })

    active_modes.sort(key=lambda m: m["max_confidence"], reverse=True)
    return active_modes


# ---------------------------------------------------------------------------
# Pathway definition loader
# ---------------------------------------------------------------------------

def _load_pathway_definitions() -> dict:
    """Load pathway definitions from JSON."""
    with open(PATHWAY_DEFS_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Evidence gathering helpers
# ---------------------------------------------------------------------------

def _get_pathways(conn: sqlite3.Connection, genome_id: int) -> List[dict]:
    """Fetch all gapseq pathway predictions for a genome."""
    rows = conn.execute("""
        SELECT pathway_name, completeness, predicted
          FROM genome_pathways
         WHERE genome_id = ?
    """, (genome_id,)).fetchall()
    return [{"name": r[0], "completeness": r[1], "predicted": bool(r[2])}
            for r in rows]


def _get_transporters(conn: sqlite3.Connection, genome_id: int) -> List[Tuple[str, int]]:
    """Fetch transporter substrate counts for a genome."""
    rows = conn.execute("""
        SELECT substrate, COUNT(*) as n
          FROM genome_transporters
         WHERE genome_id = ?
         GROUP BY substrate
    """, (genome_id,)).fetchall()
    return [(r[0], r[1]) for r in rows]


def _step_found_in_pathways(pathways: List[dict], step: dict) -> Tuple[bool, float]:
    """Check if a pathway step is represented in gapseq pathway data.

    Searches by gapseq_patterns (regex against pathway names) and by
    EC numbers.  Returns (found, best_completeness).
    """
    best_comp = 0.0
    found = False

    # Search by gapseq pathway name patterns
    for pattern in step.get("gapseq_patterns", []):
        rx = re.compile(pattern, re.IGNORECASE)
        for p in pathways:
            if rx.search(p["name"]):
                comp = p["completeness"]
                if comp > best_comp:
                    best_comp = comp
                if p["predicted"] or comp >= 50:
                    found = True

    # Search by EC numbers in pathway names (some gapseq entries include EC)
    for ec in step.get("ec_numbers", []):
        for p in pathways:
            if ec in p["name"]:
                if p["completeness"] > best_comp:
                    best_comp = p["completeness"]
                if p["predicted"] or p["completeness"] >= 50:
                    found = True

    return found, best_comp


def _transporter_found(transporters: List[Tuple[str, int]],
                       patterns: List[str]) -> Tuple[bool, int]:
    """Check if any transporter matches the given patterns."""
    total = 0
    for sub, count in transporters:
        if sub is None:
            continue
        for pat in patterns:
            if re.search(pat, sub, re.IGNORECASE):
                total += count
                break
    return total > 0, total


def _cofactor_found(pathways: List[dict], patterns: List[str]) -> bool:
    """Check if cofactor biosynthesis pathway is present."""
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for p in pathways:
            if rx.search(p["name"]) and (p["predicted"] or p["completeness"] >= 50):
                return True
    return False


# ---------------------------------------------------------------------------
# Generic pathway-integrity detector
# ---------------------------------------------------------------------------

def detect_pathway_integrity(genome_id: int,
                              pathway_def: dict,
                              conn: sqlite3.Connection,
                              marker_hits: dict = None,
                              ) -> Capability:
    """Evaluate pathway integrity for one metabolism.

    Scoring (asymmetric for transporters):
      pathway_score   = sum(weight * found) / sum(all weights)
                        Diagnostic markers boost weight 1.5x when present.
      cofactor_score  = fraction of cofactor biosyntheses present
      transporter_bonus = +0.10 if substrate transporter, +0.05 if product
                          NO penalty for absent transporters
      negative_penalty  = 0.0 if any required-absent marker IS present
                          1.0 if all required-absent markers are absent

    Final confidence =
        (0.70 * pathway_score + 0.20 * cofactor_score
         + 0.05 * diagnostic_marker_boost + transporter_bonus)
      * negative_penalty

    detected = confidence >= 0.50 AND pathway_score >= 0.40
    """
    if marker_hits is None:
        marker_hits = get_marker_hits(genome_id, conn)

    pathways = _get_pathways(conn, genome_id)
    transporters = _get_transporters(conn, genome_id)

    name = pathway_def.get("description", "unknown")
    evidence_summary = []
    uncertainty_flags = []

    # --- Pathway step evaluation ---
    step_evidence = []
    total_weight = 0.0
    found_weight = 0.0

    for step in pathway_def.get("steps", []):
        w = step["weight"]
        found, comp = _step_found_in_pathways(pathways, step)

        # Check diagnostic marker BLAST hit for this step.
        # Only count high-confidence BLAST hits: >=50% identity AND
        # bitscore >= 300 for full weight.  Weak hits (30-50% id) are
        # noted but don't override the pathway search — they may be
        # paralogs or distant homologs that don't carry the same function.
        dm_name = step.get("diagnostic_marker")
        dm_hit = None
        dm_boost = 1.0
        if dm_name and dm_name in marker_hits and marker_hits[dm_name]:
            best_hit = max(marker_hits[dm_name], key=lambda h: h["bitscore"])
            if best_hit["pident"] >= 40 and best_hit["bitscore"] >= 300:
                # High-confidence marker hit
                dm_hit = best_hit
                found = True
                dm_boost = 1.5
                evidence_summary.append(
                    f"{step['name']}: diagnostic marker {dm_name} detected "
                    f"({best_hit['pident']:.1f}% id, bs={best_hit['bitscore']:.0f})")
            elif best_hit["pident"] >= 30 and best_hit["bitscore"] >= 150:
                # Moderate-confidence: note but don't override pathway search
                dm_hit = best_hit
                dm_boost = 1.2
                evidence_summary.append(
                    f"{step['name']}: weak {dm_name} hit "
                    f"({best_hit['pident']:.1f}% id, bs={best_hit['bitscore']:.0f}) — "
                    f"may be paralog")

        effective_weight = w * dm_boost
        total_weight += effective_weight
        if found:
            found_weight += effective_weight

        step_evidence.append(PathwayStepEvidence(
            step_name=step["name"],
            weight=effective_weight,
            found=found,
            best_completeness=comp,
            diagnostic_marker_hit=dm_hit,
        ))

    pathway_score = found_weight / total_weight if total_weight > 0 else 0.0

    # --- Cofactor biosynthesis ---
    cofactor_defs = pathway_def.get("cofactor_biosyntheses", [])
    cofactors_found = 0
    for cof in cofactor_defs:
        if _cofactor_found(pathways, cof["patterns"]):
            cofactors_found += 1
        else:
            uncertainty_flags.append(
                f"cofactor {cof['name']}{'' if 'biosynthesis' in cof['name'].lower() else ' biosynthesis'} not detected — "
                f"may need supplementation or uses alternative pathway")
    cofactor_score = (cofactors_found / len(cofactor_defs)
                      if cofactor_defs else 1.0)

    # --- Transporter evidence (asymmetric: bonus only, no penalty) ---
    transporter_bonus = 0.0
    transport_ev = []

    for tdef in pathway_def.get("required_transporters", []):
        found, count = _transporter_found(transporters, tdef["patterns"])
        transport_ev.append(TransporterEvidence(
            transporter_name=tdef["name"], found=found,
            count=count, optional=tdef.get("optional", False),
        ))
        if found:
            transporter_bonus += 0.10
            evidence_summary.append(
                f"{tdef['name']}: detected ({count} hits) — "
                f"supporting evidence (transporter annotations may be unreliable)")

    for tdef in pathway_def.get("product_transporters", []):
        found, count = _transporter_found(transporters, tdef["patterns"])
        transport_ev.append(TransporterEvidence(
            transporter_name=tdef["name"], found=found,
            count=count, optional=tdef.get("optional", False),
        ))
        if found:
            transporter_bonus += 0.05

    transporter_bonus = min(transporter_bonus, 0.15)

    # --- Negative markers ---
    negative_penalty = 1.0
    neg_present = []
    for neg_marker in pathway_def.get("negative_markers", []):
        if neg_marker in marker_hits and marker_hits[neg_marker]:
            best = max(marker_hits[neg_marker], key=lambda h: h["bitscore"])
            # Only count as truly present if bitscore is substantial.
            # Threshold 300 excludes weak cross-hits (E. coli has mcrA
            # at bs=214 from a distant homolog, not true mcrA).
            if best["bitscore"] >= 300:
                negative_penalty = 0.0
                neg_present.append(neg_marker)
                evidence_summary.append(
                    f"NEGATIVE: {neg_marker} detected (bs={best['bitscore']:.0f}) — "
                    f"this metabolism should NOT have this marker")

    # --- Diagnostic marker boost ---
    dm_names_hit = []
    for step in pathway_def.get("steps", []):
        dm = step.get("diagnostic_marker")
        if dm and dm in marker_hits and marker_hits[dm]:
            if dm not in dm_names_hit:
                dm_names_hit.append(dm)
    diagnostic_boost = min(0.05, 0.025 * len(dm_names_hit))

    # --- Final confidence ---
    raw_confidence = (
        0.70 * pathway_score
        + 0.20 * cofactor_score
        + diagnostic_boost
        + transporter_bonus
    )
    confidence = raw_confidence * negative_penalty
    confidence = max(0.0, min(1.0, confidence))

    # --- Phase 1.5j/1.5k/3.6: Essential marker cap ---
    # When a pathway definition specifies essential_marker (single) or
    # essential_marker_AND (list), the organism must have the marker(s) as
    # positive BLAST hits.  Without them, confidence is capped at 0.40.
    #
    # essential_marker: "X"           → require X
    # essential_marker_AND: ["X","Y"] → require ALL of X and Y
    # essential_marker_OR (Phase 3.6): heterogeneous OR-group with marker names
    #     and/or pathway-pattern dicts. At least ONE of the entries must signal
    #     positive. Used for ANME detection where the discriminator is mcrA AND
    #     ANY of (dsrAB, mtrC_omcB, dissimilatory-nitrate-reduction-pathway).
    #     Pathway-pattern entries are appropriate when curated marker BLAST
    #     can't reach divergent paralogs (e.g., Methanoperedens narG at 24%
    #     pident to canonical refs); gapseq's UniRef-based pathway annotation
    #     succeeds where direct BLAST fails. Use this fallback when biology-
    #     grounded marker curation is genuinely infeasible — not as convenience
    #     replacement for curatable markers.
    essential_missing = False
    essential_single = pathway_def.get("essential_marker")
    essential_and = pathway_def.get("essential_marker_AND")
    essential_or = pathway_def.get("essential_marker_OR")

    if essential_and:
        # Phase 1.5k: multi-marker AND requirement
        missing = []
        present = []
        for marker_name in essential_and:
            hits = marker_hits.get(marker_name, [])
            has_it = any(
                h["bitscore"] >= 200 and h["pident"] >= 30
                for h in hits
            )
            if has_it:
                present.append(marker_name)
            else:
                missing.append(marker_name)
        if missing:
            confidence = min(confidence, 0.40)
            essential_missing = True
            rationale = pathway_def.get("essential_marker_rationale", "")
            evidence_summary.append(
                f"Essential marker(s) missing: {', '.join(missing)} — "
                f"confidence capped at 0.40 ({rationale})")
    elif essential_single:
        # Phase 1.5j: single essential marker (backward compat)
        essential_hits = marker_hits.get(essential_single, [])
        has_essential = any(
            h["bitscore"] >= 200 and h["pident"] >= 30
            for h in essential_hits
        )
        if not has_essential:
            confidence = min(confidence, 0.40)
            essential_missing = True
            evidence_summary.append(
                f"Essential marker {essential_single} absent or below threshold — "
                f"confidence capped at 0.40 ({pathway_def.get('essential_marker_rationale', '')})")

    # Phase 3.6: essential_marker_OR — heterogeneous OR-group. ALL of essential_marker_AND
    # already required above; OR-group adds requirement that AT LEAST ONE alternative
    # signal must fire. Entries may be marker names (string) or pathway-pattern dicts.
    if essential_or and not essential_missing:
        import re as _re
        any_or_present = False
        or_signals_found = []
        or_signals_checked = []
        for entry in essential_or:
            if isinstance(entry, str):
                # Marker-name entry: positive_call equivalent
                or_signals_checked.append(entry)
                hits = marker_hits.get(entry, [])
                if any(h["bitscore"] >= 200 and h["pident"] >= 30 for h in hits):
                    any_or_present = True
                    or_signals_found.append(entry)
            elif isinstance(entry, dict) and entry.get("type") == "pathway_pattern":
                # Pathway-pattern entry: gapseq pathway match at min completeness
                pattern = entry.get("pattern", "")
                min_completeness = entry.get("min_completeness", 100)
                require_predicted = entry.get("require_predicted", True)
                label = entry.get("label", f"pathway:{pattern}")
                or_signals_checked.append(label)
                pat_re = _re.compile(pattern, _re.IGNORECASE)
                for pwy in pathways:
                    if (pat_re.search(pwy["name"])
                            and pwy["completeness"] >= min_completeness
                            and (not require_predicted or pwy["predicted"])):
                        any_or_present = True
                        or_signals_found.append(
                            f"{label} (pwy='{pwy['name']}', "
                            f"completeness={pwy['completeness']:.0f}%)")
                        break
        if not any_or_present:
            confidence = min(confidence, 0.40)
            essential_missing = True
            evidence_summary.append(
                f"essential_marker_OR group requires ANY of "
                f"{or_signals_checked} — none present; confidence capped at 0.40 "
                f"({pathway_def.get('essential_marker_rationale', '')})")
        else:
            evidence_summary.append(
                f"essential_marker_OR satisfied by: {', '.join(or_signals_found)}")

    detected = confidence >= 0.50 and pathway_score >= 0.40

    # --- Phase 1.5n: Diagnostic marker override ---
    # For metabolisms where a single marker is uniquely diagnostic (e.g.,
    # rdhA for organohalide respiration, pufLM for Type-II anoxygenic
    # phototrophy, rhodopsin for light-driven proton pumping), allow the
    # marker BLAST hit alone to drive detection when pathway-based scoring
    # rejects the call.  The override:
    #   - fires ONLY if pathway-based detection failed (`not detected`)
    #   - is suppressed by the negative-marker rule (no override if neg fires)
    #   - applies as a floor: confidence = max(confidence, override_confidence)
    #   - thresholds defined per metabolism in `diagnostic_marker_override`
    #   - queries the DB directly because get_marker_hits() filters by
    #     positive_call=1, but override thresholds may be more liberal
    #     on qcov than the positive-call threshold (e.g., rdhA override
    #     accepts qcov>=50 while positive_call requires qcov>=60).
    override_cfg = pathway_def.get("diagnostic_marker_override")
    override_hit = None
    if (override_cfg
            and override_cfg.get("enabled")
            and not detected
            and negative_penalty > 0
            and not essential_missing):
        marker_name = override_cfg["marker"]
        rows = conn.execute("""
            SELECT bitscore, pident, qcov, evalue
              FROM genome_diagnostic_markers
             WHERE genome_id = ? AND marker_name = ?
               AND pident >= ? AND qcov >= ? AND evalue <= ?
             ORDER BY bitscore DESC
             LIMIT 1
        """, (genome_id, marker_name,
              override_cfg["min_pident"],
              override_cfg["min_qcov"],
              override_cfg["min_evalue"])).fetchone()
        if rows is not None:
            override_hit = {"bitscore": rows[0], "pident": rows[1],
                            "qcov": rows[2], "evalue": rows[3]}
            override_conf = override_cfg["override_confidence"]
            confidence = max(confidence, override_conf)
            detected = True
            uncertainty_flags.append("detected_via_marker_override")
            evidence_summary.append(
                f"Diagnostic marker override applied: {marker_name} hit at "
                f"{override_hit['pident']:.1f}% identity, qcov={override_hit['qcov']:.0f}%, "
                f"bitscore {override_hit['bitscore']:.0f} — pathway integrity scoring "
                f"would reject this call but the marker is uniquely diagnostic. "
                f"Rationale: {override_cfg['rationale']}")

    # Build summary
    found_steps = sum(1 for s in step_evidence if s.found)
    total_steps = len(step_evidence)
    evidence_summary.insert(0,
        f"Pathway: {found_steps}/{total_steps} steps detected "
        f"(weighted score {pathway_score:.2f})")
    if cofactor_defs:
        evidence_summary.append(
            f"Cofactors: {cofactors_found}/{len(cofactor_defs)} biosyntheses detected")

    return Capability(
        name=name,
        detected=detected,
        confidence=round(confidence, 3),
        pathway_completeness=round(pathway_score, 3),
        step_evidence=step_evidence,
        transporter_evidence=transport_ev,
        cofactor_coverage=round(cofactor_score, 3),
        negative_markers_present=neg_present,
        diagnostic_markers_hit=dm_names_hit,
        evidence_summary=evidence_summary,
        uncertainty_flags=uncertainty_flags,
    )


# ---------------------------------------------------------------------------
# Composite detectors
# ---------------------------------------------------------------------------

def detect_syntrophy(genome_id: int,
                     conn: sqlite3.Connection,
                     other_capabilities: List[Capability]) -> Capability:
    """Composite syntrophy detector.

    Signature: beta-oxidation + electron-bifurcating hydrogenase +
    NO terminal electron acceptor capabilities.
    Confidence cap: 0.70.
    """
    pathways = _get_pathways(conn, genome_id)
    transporters = _get_transporters(conn, genome_id)
    evidence = []
    score = 0.0

    # Beta-oxidation pathway
    beta_ox = any(
        re.search(r"fatty acid.*beta.*oxidation|beta.*oxidation.*fatty", p["name"], re.I)
        and (p["predicted"] or p["completeness"] >= 50)
        for p in pathways
    )
    if beta_ox:
        score += 0.25
        evidence.append("beta-oxidation pathway detected")
    else:
        evidence.append("beta-oxidation pathway NOT detected")

    # Electron-bifurcating hydrogenase
    try:
        h_rows = conn.execute("""
            SELECT hydrogenase_type, group_id, bitscore
              FROM genome_hydrogenases
             WHERE genome_id = ? AND bitscore >= 100
        """, (genome_id,)).fetchall()
        has_bifurcating = any(
            (t == "[FeFe]" and g.strip() in ("A", "A1", "A2", "A3"))
            or (t == "[NiFe]" and g.strip() == "3")
            for t, g, _ in h_rows
        )
    except Exception:
        has_bifurcating = False
        h_rows = []

    if has_bifurcating:
        score += 0.25
        evidence.append("electron-bifurcating hydrogenase detected")
    else:
        evidence.append("no electron-bifurcating hydrogenase detected")

    # Fatty acid transporter
    fa_found, fa_count = _transporter_found(
        transporters, ["fatty acid", "fadL", "long.chain.*fatty"])
    if fa_found:
        score += 0.05
        evidence.append(f"fatty acid transporter detected ({fa_count} hits)")

    # Check for fermentation — fermenters use substrate-level phosphorylation,
    # not syntrophy.  Clostridium has beta-oxidation + [FeFe] hydrogenase but
    # is a fermenter, not a syntroph.  Classical fermentation pathways (lactate
    # DH, ethanol DH, mixed acid) are NOT present in obligate syntrophs because
    # they lack substrate-level fermentation of sugars.
    # NOTE: Obligate syntrophs also "ferment" in the thermodynamic sense
    # (syntrophic beta-oxidation is fermentation coupled to partner H2
    # consumption). But gapseq will not report classical fermentation pathways
    # for them. The check therefore correctly excludes Clostridium/Lactobacillus
    # while allowing Syntrophomonas.
    # Check for STRONG fermentation signal — organisms with high-confidence
    # fermentation (>= 0.80, i.e. multiple fermentation products + glycolysis)
    # are classical fermenters, not syntrophs.  Lower fermentation scores
    # are allowed because syntrophs can have some fermentation genes that
    # they use in the syntrophic context (beta-oxidation producing acetate
    # is technically "fermentation to acetate" by gapseq's naming).
    ferm_cap = next((c for c in other_capabilities
                     if "fermentation" in c.name.lower()), None)
    if ferm_cap and ferm_cap.detected and ferm_cap.confidence >= 0.80:
        evidence.append(f"strong fermentation detected (conf={ferm_cap.confidence:.2f}) — "
                        "organism is a classical fermenter, not an obligate syntroph")
        return Capability(
            name="Syntrophy (composite signature)",
            detected=False,
            confidence=0.0,
            pathway_completeness=0.0,
            evidence_summary=evidence,
            uncertainty_flags=["excluded by strong fermentation (>= 0.80)"],
        )

    # ABSENCE of terminal acceptors — the diagnostic signature
    terminal_names = [
        "Aerobic respiration",
        "Dissimilatory sulfate reduction",
        "Denitrification",
        "Dissimilatory Fe(III) reduction",
    ]
    has_terminal = False
    for cap in other_capabilities:
        if cap.detected and any(tn.lower() in cap.name.lower() for tn in terminal_names):
            has_terminal = True
            break

    if not has_terminal:
        score += 0.20
        evidence.append("NO terminal electron acceptor metabolism detected — "
                        "consistent with obligate syntrophy")
    else:
        evidence.append("terminal electron acceptor metabolism IS present — "
                        "not obligately syntrophic")
        score -= 0.15

    confidence = min(0.70, max(0.0, score))
    detected = confidence >= 0.40 and beta_ox and has_bifurcating and not has_terminal

    return Capability(
        name="Syntrophy (composite signature)",
        detected=detected,
        confidence=round(confidence, 3),
        pathway_completeness=round(score, 3),
        evidence_summary=evidence,
        uncertainty_flags=["confidence capped at 0.70 — syntrophy is inferential"],
    )


def compute_acidic_residue_fraction(proteome_path: str) -> float:
    """Compute fraction of D+E residues across all predicted proteins."""
    total_residues = 0
    de_residues = 0
    in_seq = False

    with open(proteome_path) as f:
        for line in f:
            if line.startswith(">"):
                in_seq = True
                continue
            if in_seq:
                seq = line.strip().upper()
                total_residues += len(seq)
                de_residues += seq.count("D") + seq.count("E")

    return de_residues / total_residues if total_residues > 0 else 0.0


def detect_salt_in_halophily(genome_id: int,
                              conn: sqlite3.Connection,
                              proteome_path: str = None) -> Capability:
    """Composite salt-in halophile detector.

    Signature: no compatible solutes + elevated K+ transporters + acidic proteome.
    Confidence cap: 0.75.
    """
    pathways = _get_pathways(conn, genome_id)
    transporters = _get_transporters(conn, genome_id)
    evidence = []
    score = 0.0

    # Compatible solute biosynthesis INCOMPLETE
    compat_solute_patterns = [
        r"ectoine.*biosynthesis|ectABC",
        r"glycine betaine.*biosynthesis|betABI",
    ]
    has_compat_solutes = False
    for pat in compat_solute_patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for p in pathways:
            if rx.search(p["name"]) and p["predicted"] and p["completeness"] >= 80:
                has_compat_solutes = True
                break

    if not has_compat_solutes:
        score += 0.15
        evidence.append("compatible solute biosynthesis incomplete/absent — "
                        "consistent with salt-in strategy")
    else:
        evidence.append("compatible solute biosynthesis PRESENT — "
                        "suggests salt-out strategy, not salt-in")
        score -= 0.10

    # K+ transporter count
    k_patterns = [r"trkA", r"trkH", r"ktrA", r"ktrB", r"kdpA", r"kdpB", r"kdpC",
                  r"ktrC", r"ktrD", r"potassium"]
    k_found, k_count = _transporter_found(transporters, k_patterns)
    # Count distinct K+ transporter systems
    k_systems = 0
    for sub, count in transporters:
        if sub and re.search(r"potassium|trk|ktr|kdp", sub, re.I):
            k_systems += 1

    if k_systems >= 3:
        score += 0.20
        evidence.append(f"{k_systems} K+ transporter systems detected (>=3 required)")
    elif k_systems >= 1:
        score += 0.05
        evidence.append(f"{k_systems} K+ transporter system(s) detected (<3)")
    else:
        evidence.append("no K+ transporter systems detected")

    # Acidic proteome (strongest single signal)
    acidic_frac = None
    # Check if cached in genome_quality
    try:
        row = conn.execute(
            "SELECT acidic_residue_fraction FROM genome_quality WHERE genome_id = ?",
            (genome_id,)
        ).fetchone()
        if row and row[0] is not None:
            acidic_frac = row[0]
    except Exception:
        pass

    # Compute if not cached and proteome available
    if acidic_frac is None and proteome_path and os.path.exists(proteome_path):
        acidic_frac = compute_acidic_residue_fraction(proteome_path)
        # Cache it
        try:
            from load_checkm import update_acidic_fraction
            update_acidic_fraction(conn, genome_id, acidic_frac)
        except Exception:
            pass

    if acidic_frac is not None:
        if acidic_frac >= 0.19:
            score += 0.35
            evidence.append(f"acidic proteome: D+E fraction = {acidic_frac:.3f} "
                            f"(>=0.19 threshold) — STRONG salt-in signal")
        elif acidic_frac >= 0.16:
            score += 0.10
            evidence.append(f"acidic proteome: D+E fraction = {acidic_frac:.3f} "
                            f"(borderline, 0.16-0.19)")
        else:
            evidence.append(f"acidic proteome: D+E fraction = {acidic_frac:.3f} "
                            f"(below threshold) — not salt-in")
    else:
        uncertainty_flags = ["acidic residue fraction not computed — no proteome"]
        evidence.append("acidic residue fraction unavailable")

    confidence = min(0.75, max(0.0, score))
    detected = confidence >= 0.40 and not has_compat_solutes

    return Capability(
        name="Extreme salt-in halophily (composite signature)",
        detected=detected,
        confidence=round(confidence, 3),
        pathway_completeness=round(score, 3),
        evidence_summary=evidence,
        uncertainty_flags=["confidence capped at 0.75 — salt-in is a composite signature"],
    )


# ---------------------------------------------------------------------------
# Cross-detector context helpers (Phase 1.5b)
# ---------------------------------------------------------------------------

def _check_autotrophy(genome_id: int,
                      conn: sqlite3.Connection,
                      marker_hits: dict = None) -> Tuple[bool, List[str]]:
    """Check for autotrophic CO2 fixation pathways.

    Returns (autotrophy_detected, evidence_strings).
    Checks gapseq pathway completeness AND diagnostic marker BLAST hits.
    Pathways: CBB, rTCA, 3HP bicycle, 3HP/4HB cycle, DC/4HB cycle.
    Markers: rbcL (CBB), aclA (rTCA), mcr (3HP), 4hbd (3HP/4HB + DC/4HB).
    """
    pathways = _get_pathways(conn, genome_id)
    evidence = []

    # CBB cycle requires HIGHER threshold (>= 90% AND predicted=true) because
    # CBB genes at 70-85% are pentose phosphate pathway overlap, not real
    # autotrophy. Other autotrophic pathways use standard 70% threshold.
    auto_patterns = [
        (r"Calvin-Benson-Bassham|reductive pentose phosphate|CBB", "CBB cycle", 90, True),
        (r"3-hydroxypropionate", "3-hydroxypropionate bicycle/cycle", 70, False),
        (r"reductive TCA|reverse TCA|rTCA|reductive citric acid", "reductive TCA cycle", 80, False),
        (r"3-hydroxypropionate.*4-hydroxybutyrate", "3HP/4HB cycle", 70, False),
        (r"dicarboxylate.*4-hydroxybutyrate", "DC/4HB cycle", 70, False),
    ]

    pathway_detected = False
    for pattern, name, min_comp, require_predicted in auto_patterns:
        rx = re.compile(pattern, re.IGNORECASE)
        for p in pathways:
            if not rx.search(p["name"]):
                continue
            if require_predicted:
                if p["predicted"] and p["completeness"] >= min_comp:
                    evidence.append(f"{name}: {p['name']} ({p['completeness']:.0f}%, predicted)")
                    pathway_detected = True
                    break
            else:
                if p["predicted"] or p["completeness"] >= min_comp:
                    evidence.append(f"{name}: {p['name']} ({p['completeness']:.0f}%)")
                    pathway_detected = True
                    break

    # Check autotrophy diagnostic marker BLAST hits
    if marker_hits is None:
        marker_hits = get_marker_hits(genome_id, conn)
    auto_hits = marker_hits.get("autotrophy", [])
    if auto_hits:
        best = max(auto_hits, key=lambda h: h["bitscore"])
        if best["bitscore"] >= 400:
            evidence.append(f"autotrophy marker BLAST: {best['accession']} "
                            f"({best['pident']:.0f}% id, bs={best['bitscore']:.0f})")
            pathway_detected = True

    return pathway_detected, evidence


def _apply_fermentation_disqualifiers(
        base_cap: Capability,
        genome_id: int,
        conn: sqlite3.Connection,
        other_capabilities: List[Capability] = None,
        marker_hits: dict = None,
) -> Capability:
    """Apply autotrophy and acceptor-metabolism disqualifiers to fermentation.

    Phase 1.5b: two context filters that prevent fermentation from over-firing.

    1. Autotrophy disqualifier: if strong CO2 fixation detected, cap fermentation
       at 0.40 (below detection threshold). The organism uses glycolytic enzymes
       anabolically, not catabolically.

    2. Acceptor-metabolism disqualifier: if a terminal-acceptor metabolism
       (>= 0.55) is also detected, cap fermentation BELOW the strongest acceptor's
       confidence (so it ranks as secondary, not primary). Reflects facultative
       anaerobe biology where respiration is preferred over fermentation when
       an acceptor is available.
    """
    # Autotrophy check
    auto_detected, auto_evidence = _check_autotrophy(genome_id, conn, marker_hits)
    if auto_detected:
        capped = min(base_cap.confidence, 0.40)
        return Capability(
            name=base_cap.name,
            detected=False,
            confidence=round(capped, 3),
            pathway_completeness=base_cap.pathway_completeness,
            step_evidence=base_cap.step_evidence,
            transporter_evidence=base_cap.transporter_evidence,
            cofactor_coverage=base_cap.cofactor_coverage,
            negative_markers_present=base_cap.negative_markers_present,
            diagnostic_markers_hit=base_cap.diagnostic_markers_hit,
            evidence_summary=base_cap.evidence_summary + [
                f"Autotrophic CO2 fixation detected: {'; '.join(auto_evidence)}",
                "Fermentation suppressed: glycolytic enzymes used anabolically, not catabolically"
            ],
            uncertainty_flags=base_cap.uncertainty_flags + ["autotrophy_disqualifier_applied"],
        )

    # Iron reduction cross-suppression (Phase 1.5i).
    # Geobacter and other dissimilatory iron reducers oxidize acetate coupled
    # to Fe(III) reduction. The acetate oxidation pathway shares enzymes with
    # fermentation product formation. When iron reduction is detected with
    # mtrC/omcB markers, the evidence driving fermentation is actually
    # anaerobic respiration.
    if other_capabilities:
        iron_red_cap = next(
            (c for c in other_capabilities
             if "fe(iii) reduction" in c.name.lower() and c.detected and c.confidence >= 0.50),
            None)
        if iron_red_cap:
            capped = min(base_cap.confidence, 0.40)
            return Capability(
                name=base_cap.name,
                detected=False,
                confidence=round(capped, 3),
                pathway_completeness=base_cap.pathway_completeness,
                step_evidence=base_cap.step_evidence,
                transporter_evidence=base_cap.transporter_evidence,
                cofactor_coverage=base_cap.cofactor_coverage,
                negative_markers_present=base_cap.negative_markers_present,
                diagnostic_markers_hit=base_cap.diagnostic_markers_hit,
                evidence_summary=base_cap.evidence_summary + [
                    f"Iron reduction detected ({iron_red_cap.confidence:.2f}) — "
                    f"acetate oxidation evidence attributed to anaerobic respiration "
                    f"with Fe(III) as terminal acceptor, not fermentation"
                ],
                uncertainty_flags=base_cap.uncertainty_flags + ["iron_reduction_disqualifier_applied"],
            )

    # Syntrophy disqualifier (Phase 1.5f): symmetric cross-suppression.
    # When syntrophy is detected, the beta-oxidation evidence is attributed
    # to syntrophic fatty acid oxidation, not free-living fermentation.
    if other_capabilities:
        syntrophy_cap = next(
            (c for c in other_capabilities
             if "syntrophy" in c.name.lower() and c.detected and c.confidence >= 0.60),
            None)
        if syntrophy_cap:
            capped = min(base_cap.confidence, 0.40)
            return Capability(
                name=base_cap.name,
                detected=False,
                confidence=round(capped, 3),
                pathway_completeness=base_cap.pathway_completeness,
                step_evidence=base_cap.step_evidence,
                transporter_evidence=base_cap.transporter_evidence,
                cofactor_coverage=base_cap.cofactor_coverage,
                negative_markers_present=base_cap.negative_markers_present,
                diagnostic_markers_hit=base_cap.diagnostic_markers_hit,
                evidence_summary=base_cap.evidence_summary + [
                    f"Syntrophy detected ({syntrophy_cap.confidence:.2f}) — "
                    f"beta-oxidation evidence attributed to syntrophic metabolism, "
                    f"not free-living fermentation"
                ],
                uncertainty_flags=base_cap.uncertainty_flags + ["syntrophy_disqualifier_applied"],
            )

    # Acceptor-metabolism disqualifier
    if other_capabilities and base_cap.detected:
        acceptor_names = [
            "Aerobic respiration",
            "Dissimilatory sulfate reduction",
            "Denitrification",
            "Dissimilatory Fe(III) reduction",
            "Methanogenesis",
            "Anaerobic ammonium oxidation",
            "Reductive dehalogenation",
        ]
        strong_acceptors = []
        for cap in other_capabilities:
            if cap.confidence >= 0.55 and any(
                    an.lower() in cap.name.lower() for an in acceptor_names):
                strong_acceptors.append((cap.name, cap.confidence))

        if strong_acceptors:
            # Cap fermentation BELOW the strongest acceptor's confidence so it ranks
            # as secondary, not primary. The previous fixed cap at 0.65 didn't push
            # fermentation below acceptors in the 0.55-0.65 range.
            max_acceptor_conf = max(c for _, c in strong_acceptors)
            capped = min(base_cap.confidence, max_acceptor_conf - 0.05, 0.65)
            return Capability(
                name=base_cap.name,
                detected=True,
                confidence=round(capped, 3),
                pathway_completeness=base_cap.pathway_completeness,
                step_evidence=base_cap.step_evidence,
                transporter_evidence=base_cap.transporter_evidence,
                cofactor_coverage=base_cap.cofactor_coverage,
                negative_markers_present=base_cap.negative_markers_present,
                diagnostic_markers_hit=base_cap.diagnostic_markers_hit,
                evidence_summary=base_cap.evidence_summary + [
                    f"Strong acceptor metabolism present: "
                    f"{', '.join(f'{n}({c:.2f})' for n, c in strong_acceptors)}",
                    "Fermentation kept as secondary capability (facultative pattern)"
                ],
                uncertainty_flags=base_cap.uncertainty_flags + ["acceptor_disqualifier_applied"],
            )

    return base_cap


def _get_genomespot_oxygen(conn: sqlite3.Connection, genome_id: int) -> Optional[str]:
    """Get GenomeSPOT oxygen tolerance prediction.

    Returns 'tolerant', 'not_tolerant', or None if not available.

    Phase 1.5i: For archaeal genomes, returns None (do not use GenomeSPOT
    oxygen prediction as a disqualifier). GenomeSPOT was trained on bacterial
    data and misclassifies archaeal aerobes (Sulfolobus scored 0.94 confidence
    "not tolerant" despite being an obligate aerobe). For archaea, only the
    obligate-anaerobe-metabolism disqualifier is used.
    """
    try:
        row = conn.execute("""
            SELECT ggp.value, g.biomass_template
            FROM genome_growth_predictions ggp
            JOIN genomes g ON g.id = ggp.genome_id
            WHERE ggp.genome_id = ? AND lower(ggp.target) LIKE '%oxygen%'
        """, (genome_id,)).fetchone()
        if row and row[0]:
            value, biomass = row
            if biomass == "Archaea":
                return None  # Don't trust GenomeSPOT on archaea
            return value.lower().replace(" ", "_")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Aerobic respiration detector
# ---------------------------------------------------------------------------

def detect_aerobic_respiration(genome_id: int,
                               conn: sqlite3.Connection,
                               marker_hits: dict = None,
                               other_capabilities: List[Capability] = None,
                               ) -> Capability:
    """Detect aerobic respiration from multiple evidence sources.

    Phase 1.5 rewrite: weighted combination of evidence, not single-complex
    gating.  Recognizes bo3, cbb3, bd (ambiguous), caa3, qoxABCD, soxM
    (archaeal), and generic cytochrome c oxidase.

    Phase 1.5b: anaerobe disqualifier. When a strong obligate-anaerobe
    metabolism (methanogenesis, sulfate reduction, anammox, organohalide
    respiration) is detected at >= 0.70, cytochrome c hits are likely from
    non-respiratory functions. Cap score at 0.30.

    Scoring:
      oxidase_complete (any type)           +0.50
      oxidase partial / BLAST-only hits     +0.20
      cytc >= 6 AND TCA >= 80               +0.25
      cytc >= 6 alone                       +0.15
      TCA >= 80                             +0.10
      catalase present                      +0.05
      bd only (no other oxidase)            +0.10

    Cap at 0.40 when TCA < 50 and no complete oxidase (prevents anaerobe FPs).
    """
    if marker_hits is None:
        marker_hits = get_marker_hits(genome_id, conn)

    evidence = []
    score = 0.0

    # --- Reaction markers (from gapseq reaction table scan) ---
    try:
        rxn_markers = {}
        for row in conn.execute("""
            SELECT marker, n_good_blast, best_bitscore, complex_complete
              FROM genome_reaction_markers
             WHERE genome_id = ?
        """, (genome_id,)).fetchall():
            rxn_markers[row[0]] = {
                "n_good_blast": row[1], "best_bitscore": row[2],
                "complex_complete": bool(row[3]),
            }
    except Exception:
        rxn_markers = {}

    bo3_cc = rxn_markers.get("bo3_oxidase", {}).get("complex_complete", False)
    cbb3_cc = rxn_markers.get("cbb3_oxidase", {}).get("complex_complete", False)
    bd_cc = rxn_markers.get("bd_oxidase", {}).get("complex_complete", False)
    cytc_hits = rxn_markers.get("cytc_oxidase", {}).get("n_good_blast", 0)
    catalase_cc = rxn_markers.get("catalase", {}).get("complex_complete", False)
    catalase_hits = rxn_markers.get("catalase", {}).get("n_good_blast", 0)

    # --- Terminal oxidase BLAST hits (expanded marker database) ---
    ox_blast = marker_hits.get("terminal_oxidases", [])
    has_ox_blast = bool(ox_blast)
    best_ox_blast = max((h["bitscore"] for h in ox_blast), default=0)

    # --- Score: any complete oxidase complex ---
    oxidase_complete = bo3_cc or cbb3_cc
    oxidase_blast_strong = has_ox_blast and best_ox_blast >= 400

    if oxidase_complete:
        score += 0.50
        if bo3_cc:
            evidence.append("bo3 oxidase complex complete (low-affinity, aerobic)")
        if cbb3_cc:
            evidence.append("cbb3 oxidase complex complete (high-affinity, microaerophilic)")
    elif oxidase_blast_strong:
        # Strong terminal oxidase BLAST hit (caa3, qox, soxM, etc.)
        best_hit = max(ox_blast, key=lambda h: h["bitscore"])
        score += 0.50
        evidence.append(f"terminal oxidase BLAST hit ({best_hit['accession']}, "
                        f"{best_hit['pident']:.0f}% id, bs={best_hit['bitscore']:.0f})")
    elif has_ox_blast:
        # Partial/weaker terminal oxidase hits
        best_hit = max(ox_blast, key=lambda h: h["bitscore"])
        score += 0.20
        evidence.append(f"terminal oxidase partial BLAST ({best_hit['accession']}, "
                        f"{best_hit['pident']:.0f}% id, bs={best_hit['bitscore']:.0f})")

    # --- Partial oxidase evidence (many subunit hits but no complex_complete) ---
    # Catches organisms like Thermus with caa3/ba3 oxidase subunits that
    # gapseq detects but doesn't assemble into a complete complex.
    oxidase_partial = (not oxidase_complete and not oxidase_blast_strong
                       and cytc_hits >= 10)
    if oxidase_partial:
        score += 0.20
        evidence.append(f"oxidase partial: {cytc_hits} cytochrome c oxidase hits "
                        f"(subunits detected, no complete complex)")

    # --- bd oxidase (ambiguous but supporting) ---
    if bd_cc and not oxidase_complete and not oxidase_blast_strong:
        score += 0.10
        evidence.append("bd oxidase complex (ambiguous: respiratory or protective)")

    # --- TCA cycle ---
    pathways = _get_pathways(conn, genome_id)
    tca_best = 0.0
    for p in pathways:
        if re.search(r"TCA cycle", p["name"], re.I) and p["predicted"]:
            if p["completeness"] > tca_best:
                tca_best = p["completeness"]

    # --- cytc + TCA combined signal ---
    if cytc_hits >= 6 and tca_best >= 80:
        score += 0.25
        evidence.append(f"cytochrome c oxidase: {cytc_hits} hits + TCA {tca_best:.0f}% "
                        f"(strong combined aerobic signal)")
    elif cytc_hits >= 6:
        score += 0.15
        evidence.append(f"cytochrome c oxidase: {cytc_hits} hits (moderate)")
    if tca_best >= 80:
        score += 0.10
        evidence.append(f"TCA cycle {tca_best:.0f}% complete")

    # --- Catalase (supports aerobic lifestyle) ---
    if catalase_cc or catalase_hits >= 5:
        score += 0.05
        evidence.append(f"catalase detected ({catalase_hits} hits)")

    # --- Cap for organisms without oxidase + incomplete TCA ---
    if tca_best < 50 and not oxidase_complete and not oxidase_blast_strong:
        score = min(score, 0.40)
        evidence.append(f"TCA incomplete ({tca_best:.0f}%) + no oxidase → capped at 0.40")

    # --- Phase 1.5b+f: Anaerobe disqualifier ---
    # Multiple lines of evidence for anaerobic lifestyle:
    # 1. GenomeSPOT oxygen prediction (strongest external signal)
    # 2. Obligate-anaerobe metabolisms detected at >= 0.50
    # When either fires, cytochrome c hits are attributed to anaerobic
    # electron transport rather than aerobic respiration.
    genomespot_oxygen = _get_genomespot_oxygen(conn, genome_id)
    anaerobe_evidence = []

    # GenomeSPOT "not_tolerant" is strong evidence of anaerobic lifestyle
    if genomespot_oxygen == "not_tolerant":
        anaerobe_evidence.append(f"GenomeSPOT predicts oxygen not tolerant")

    # Check for obligate-anaerobe metabolisms (threshold 0.50, expanded list)
    if other_capabilities:
        obligate_anaerobe_names = [
            "Methanogenesis",
            "Dissimilatory sulfate reduction",
            "Dissimilatory Fe(III) reduction",
            "Anaerobic ammonium oxidation",
            "Reductive dehalogenation",
        ]
        for c in other_capabilities:
            if c.confidence >= 0.50 and any(
                    an.lower() in c.name.lower() for an in obligate_anaerobe_names):
                anaerobe_evidence.append(f"{c.name} ({c.confidence:.2f})")

    if anaerobe_evidence:
        score = min(score, 0.30)
        evidence.append(
            f"Anaerobe signals: {'; '.join(anaerobe_evidence)}; "
            f"cytochrome c hits attributed to anaerobic electron transport → capped at 0.30")

    confidence = min(1.0, max(0.0, score))
    detected = confidence >= 0.50

    return Capability(
        name="Aerobic respiration",
        detected=detected,
        confidence=round(confidence, 3),
        pathway_completeness=round(score, 3),
        evidence_summary=evidence,
    )


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def _find_proteome(genome_id: int, conn: sqlite3.Connection) -> Optional[str]:
    """Try to find a proteome .faa file for a genome."""
    row = conn.execute("SELECT accession, file_path FROM genomes WHERE id = ?",
                       (genome_id,)).fetchone()
    if not row:
        return None
    acc, fpath = row

    # Map accession to gapseq directory name
    gapseq_root = _ROOT / "data" / "gapseq"
    if gapseq_root.exists():
        for d in gapseq_root.iterdir():
            if d.is_dir():
                faas = list(d.glob("*_proteins.faa")) + list(d.glob("*.faa"))
                if faas:
                    # Check if this directory has pathways matching our genome
                    pwys = list(d.glob("*Pathways.tbl"))
                    if pwys:
                        return str(faas[0])
    return None


def profile_capabilities(genome_id: int,
                          conn: sqlite3.Connection,
                          proteome_path: str = None,
                          ) -> CapabilityProfile:
    """Full metabolic capability profiling for a genome.

    Phase 1.5b orchestration: TWO-PASS detection.

    Pass 1 (primary): Detectors that don't depend on other capabilities.
      All pathway-integrity detectors from JSON, EXCEPT fermentation (which
      needs context from Pass 1 results).

    Pass 2 (context-dependent): Detectors that need Pass 1 results.
      - Aerobic respiration (needs primary caps for anaerobe disqualifier)
      - Fermentation (needs primary caps for acceptor disqualifier + autotrophy check)
      - Syntrophy (needs primary + context caps for fermentation/acceptor checks)
      - Salt-in halophily (independent but runs in Pass 2 for ordering)
    """
    # 1. QC gate
    qc = evaluate_genome_quality(genome_id, conn)
    if qc.verdict == "REJECT":
        return CapabilityProfile(
            genome_id=genome_id,
            quality_verdict=qc,
            capabilities=[],
            primary_metabolisms=[],
            recommended_action="reject",
            escalation_rationale=qc.rationale,
        )

    # 2. Diagnostic marker hits (use cached)
    marker_hits = get_marker_hits(genome_id, conn)

    # 3. Find proteome if not provided
    if proteome_path is None:
        proteome_path = _find_proteome(genome_id, conn)

    # 4. Load pathway definitions
    pathway_defs = _load_pathway_definitions()

    # ---- PASS 1: Primary detectors (no cross-detector dependencies) ----
    primary_caps: List[Capability] = []
    fermentation_base = None

    for pathway_key, pathway_def in pathway_defs.items():
        cap = detect_pathway_integrity(genome_id, pathway_def, conn, marker_hits)
        if "fermentation" in pathway_key.lower():
            # Save fermentation for Pass 2 (needs context)
            fermentation_base = cap
        else:
            primary_caps.append(cap)

    # ---- PASS 2: Context-dependent detectors ----
    # Order matters: syntrophy before fermentation for symmetric cross-suppression
    context_caps: List[Capability] = []

    # Aerobic respiration (needs primary caps for anaerobe disqualifier)
    aero_cap = detect_aerobic_respiration(
        genome_id, conn, marker_hits, other_capabilities=primary_caps)
    context_caps.append(aero_cap)

    # Syntrophy (needs primary + aero + raw fermentation for checks)
    # Pass the raw fermentation_base as a "virtual" capability so the
    # fermentation >= 0.80 check in detect_syntrophy can see it.
    all_for_syntrophy = primary_caps + context_caps
    if fermentation_base is not None:
        all_for_syntrophy = all_for_syntrophy + [fermentation_base]
    syntrophy_cap = detect_syntrophy(genome_id, conn, all_for_syntrophy)
    context_caps.append(syntrophy_cap)

    # Fermentation (needs primary + aero + syntrophy for all disqualifiers)
    if fermentation_base is not None:
        all_so_far = primary_caps + context_caps
        ferm_cap = _apply_fermentation_disqualifiers(
            fermentation_base, genome_id, conn, all_so_far, marker_hits)
        context_caps.append(ferm_cap)

    # Salt-in halophily
    halophily_cap = detect_salt_in_halophily(
        genome_id, conn, proteome_path)
    context_caps.append(halophily_cap)

    capabilities = primary_caps + context_caps

    # Identify primary metabolisms and cultivation modes (Phase 1.5f)
    primary = [cap.name for cap in capabilities
               if cap.detected and cap.confidence >= 0.50]
    cultivation_modes = determine_cultivation_modes(capabilities)

    # 8. Assess escalation
    if qc.verdict in ("PROCEED", "PROCEED_WITH_FLAG") and not primary:
        action = "escalate_tier2"
        escalation = ("No metabolic capability detected with confidence >= 0.50. "
                      "This may indicate a novel lineage with divergent enzymes. "
                      "Recommend Tier 2 structural analysis (ESMFold + Foldseek).")
    elif qc.verdict == "NO_QC":
        action = "flag_uncertain"
        escalation = None
    else:
        action = "synthesize"
        escalation = None

    return CapabilityProfile(
        genome_id=genome_id,
        quality_verdict=qc,
        capabilities=capabilities,
        primary_metabolisms=primary,
        cultivation_modes=cultivation_modes,
        recommended_action=action,
        escalation_rationale=escalation,
    )


# ---------------------------------------------------------------------------
# CLI / reporting
# ---------------------------------------------------------------------------

def format_profile(profile: CapabilityProfile) -> str:
    """Format a CapabilityProfile as human-readable text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"  CAPABILITY PROFILE — genome_id={profile.genome_id}")
    lines.append("=" * 80)
    lines.append("")

    qc = profile.quality_verdict
    lines.append(f"  Quality: {qc.verdict} — {qc.rationale}")
    if qc.genome_size:
        lines.append(f"  Genome: {qc.genome_size:,} bp, GC={qc.gc_content:.1%}, "
                     f"N50={qc.n50:,}")
    lines.append(f"  Action: {profile.recommended_action}")
    if profile.escalation_rationale:
        lines.append(f"  Escalation: {profile.escalation_rationale}")
    lines.append("")

    if profile.primary_metabolisms:
        lines.append(f"  PRIMARY METABOLISMS ({len(profile.primary_metabolisms)}):")
        for m in profile.primary_metabolisms:
            lines.append(f"    + {m}")
        lines.append("")

    lines.append(f"  ALL DETECTORS ({len(profile.capabilities)}):")
    for cap in sorted(profile.capabilities,
                      key=lambda c: c.confidence, reverse=True):
        flag = "+" if cap.detected else "-"
        lines.append(f"    [{flag}] {cap.name}")
        lines.append(f"        confidence={cap.confidence:.3f}  "
                     f"pathway={cap.pathway_completeness:.3f}  "
                     f"cofactors={cap.cofactor_coverage:.3f}")
        if cap.diagnostic_markers_hit:
            lines.append(f"        markers: {', '.join(cap.diagnostic_markers_hit)}")
        if cap.negative_markers_present:
            lines.append(f"        NEGATIVE markers present: "
                         f"{', '.join(cap.negative_markers_present)}")
        for ev in cap.evidence_summary[:5]:
            lines.append(f"        - {ev}")
        for uf in cap.uncertainty_flags[:3]:
            lines.append(f"        ! {uf}")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python capability_detectors.py <genome_id> [--db <path>]")
        sys.exit(1)

    genome_id = int(sys.argv[1])
    db_path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--db" else \
              str(_ROOT / "data" / "cultureforge.db")

    conn = sqlite3.connect(db_path)
    profile = profile_capabilities(genome_id, conn)
    print(format_profile(profile))
    conn.close()
