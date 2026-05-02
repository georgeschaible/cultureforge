"""Capability vector module (Phase 2d Task 3).

Encodes a CultureForge CapabilityProfile or a BacDive strain as a dict
{capability_dim: confidence_0_to_1}. Provides cosine similarity for
functional neighbor matching.

See data/bacdive_capability_mapping.md for the BacDive → capability mapping.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional


# 19 capability dimensions (see bacdive_capability_mapping.md)
CAPABILITY_DIMS = [
    "aerobic_chemotrophic", "fermentative", "methanogenic", "acetogenic",
    "anaerobic_respiratory_sulfate", "anaerobic_respiratory_iron",
    "anaerobic_respiratory_nitrate", "anaerobic_respiratory_organohalide",
    "anammox",
    "lithotrophic_aerobic_ammonia", "lithotrophic_aerobic_sulfur",
    "lithotrophic_aerobic_iron",
    "nitrogen_fixation",
    "anoxygenic_phototrophy_purple", "anoxygenic_phototrophy_green",
    "oxygenic_phototrophy", "bacteriorhodopsin",
    "syntrophic", "halophily",
]


# Maps from CultureForge capability names (capability_detectors output) to
# capability_vector dimensions. Many CapabilityProfile names route to a
# specific dim; some need disambiguation (e.g., anaerobic_respiratory →
# sulfate vs iron vs nitrate vs organohalide).
_CAPABILITY_NAME_TO_DIM = {
    "Aerobic respiration": "aerobic_chemotrophic",
    "Aerobic respiration via electron transport chain": "aerobic_chemotrophic",
    "Substrate-level phosphorylation fermentation (mixed products)": "fermentative",
    "Methanogenesis (hydrogenotrophic, aceticlastic, or methylotrophic)": "methanogenic",
    "Acetogenesis via Wood-Ljungdahl": "acetogenic",
    "Dissimilatory sulfate reduction": "anaerobic_respiratory_sulfate",
    "Dissimilatory Fe(III) reduction via extracellular electron transfer":
        "anaerobic_respiratory_iron",
    "Denitrification (NO3- to N2)": "anaerobic_respiratory_nitrate",
    "Reductive dehalogenation of organohalide compounds as terminal electron acceptors":
        "anaerobic_respiratory_organohalide",
    "Anaerobic ammonium oxidation (anammox), ammonium + nitrite to dinitrogen via hydrazine":
        "anammox",
    "Aerobic ammonia oxidation (nitrification step 1)": "lithotrophic_aerobic_ammonia",
    "Sulfur/sulfide/thiosulfate oxidation": "lithotrophic_aerobic_sulfur",
    "Acidophilic Fe(II) oxidation": "lithotrophic_aerobic_iron",
    "Biological nitrogen fixation (N2 to NH3)": "nitrogen_fixation",
    "Anoxygenic phototrophy (purple bacteria, Type II reaction center)":
        "anoxygenic_phototrophy_purple",
    "Anoxygenic phototrophy (green sulfur bacteria, Type I reaction center)":
        "anoxygenic_phototrophy_green",
    "Oxygenic phototrophy (cyanobacteria, algae, plants)": "oxygenic_phototrophy",
    "Bacteriorhodopsin/proteorhodopsin light-driven proton pump": "bacteriorhodopsin",
    "Syntrophy (composite signature)": "syntrophic",
}


def cultureforge_to_vector(profile, conn: Optional[sqlite3.Connection] = None,
                             genome_id: Optional[int] = None) -> Dict[str, float]:
    """Convert a CultureForge CapabilityProfile to a capability vector.

    Includes a halophily dimension derived from GenomeSPOT salinity prediction
    (when available via conn + genome_id).
    """
    v: Dict[str, float] = {}
    for cap in profile.capabilities:
        if not cap.detected or cap.confidence < 0.50:
            continue
        # Find matching dimension
        for full_name, dim in _CAPABILITY_NAME_TO_DIM.items():
            if full_name.lower() in cap.name.lower() or cap.name.lower() in full_name.lower():
                v[dim] = max(v.get(dim, 0.0), cap.confidence)
                break

    # Halophily from GenomeSPOT
    if conn is not None and genome_id is not None:
        row = conn.execute(
            "SELECT numeric_value FROM genome_growth_predictions "
            "WHERE genome_id = ? AND target = 'salinity'",
            (genome_id,)
        ).fetchone()
        if row and row[0] is not None:
            sal = float(row[0])
            if sal >= 15:
                v["halophily"] = 0.9
            elif sal >= 5:
                v["halophily"] = 0.5
    return v


def bacdive_to_vector(strain: dict) -> Dict[str, float]:
    """Convert a BacDive strain document to a capability vector.

    See data/bacdive_capability_mapping.md for the field-by-field mapping.
    """
    v: Dict[str, float] = {}
    phys = strain.get("Physiology and metabolism", {}) or {}
    nt = strain.get("Name and taxonomic classification", {}) or {}
    domain = (nt.get("domain") or "").lower()

    # --- Oxygen tolerance ---
    ox = phys.get("oxygen tolerance")
    ox_values: List[str] = []
    if isinstance(ox, str):
        ox_values = [ox]
    elif isinstance(ox, list):
        for entry in ox:
            if isinstance(entry, dict):
                ox_values.append(entry.get("oxygen tolerance", ""))
            elif isinstance(entry, str):
                ox_values.append(entry)
    elif isinstance(ox, dict):
        ox_values = [ox.get("oxygen tolerance", "")]
    ox_text = " ".join(ox_values).lower()
    if any(k in ox_text for k in ("obligate aerobe", "aerobe")) and "anaerobe" not in ox_text:
        v["aerobic_chemotrophic"] = max(v.get("aerobic_chemotrophic", 0), 0.9)
    if "facultative" in ox_text:
        v["aerobic_chemotrophic"] = max(v.get("aerobic_chemotrophic", 0), 0.7)
        v["fermentative"] = max(v.get("fermentative", 0), 0.5)
    if "microaerophil" in ox_text:
        v["aerobic_chemotrophic"] = max(v.get("aerobic_chemotrophic", 0), 0.5)

    # --- Metabolite utilization (substrates the organism uses) ---
    mu = phys.get("metabolite utilization") or []
    if isinstance(mu, dict):
        mu = [mu]
    for m in mu if isinstance(mu, list) else []:
        if not isinstance(m, dict):
            continue
        met = (m.get("metabolite") or "").lower()
        act = (m.get("utilization activity") or m.get("activity") or "")
        positive = isinstance(act, str) and ("+" in act or act.lower() == "yes")
        if not positive:
            continue
        if "h2/co2" in met or ("h2" in met and "co2" in met):
            if domain == "archaea":
                v["methanogenic"] = max(v.get("methanogenic", 0), 0.7)
            else:
                v["acetogenic"] = max(v.get("acetogenic", 0), 0.5)
        if "methanol" in met and domain == "archaea":
            v["methanogenic"] = max(v.get("methanogenic", 0), 0.5)
        if "formate" in met:
            if domain == "archaea":
                v["methanogenic"] = max(v.get("methanogenic", 0), 0.4)
            else:
                v["acetogenic"] = max(v.get("acetogenic", 0), 0.3)
        if "nitrate" in met:
            v["anaerobic_respiratory_nitrate"] = max(v.get("anaerobic_respiratory_nitrate", 0), 0.6)
        if "sulfate" in met:
            v["anaerobic_respiratory_sulfate"] = max(v.get("anaerobic_respiratory_sulfate", 0), 0.6)
        if "iron(iii)" in met or "fe(iii)" in met:
            v["anaerobic_respiratory_iron"] = max(v.get("anaerobic_respiratory_iron", 0), 0.6)
        if "h2s" in met or "sulfide" in met or "thiosulfate" in met:
            v["lithotrophic_aerobic_sulfur"] = max(v.get("lithotrophic_aerobic_sulfur", 0), 0.5)
        if "ammonium" in met or "nh4" in met:
            v["lithotrophic_aerobic_ammonia"] = max(v.get("lithotrophic_aerobic_ammonia", 0), 0.6)
        if "fe(ii)" in met or "iron(ii)" in met:
            v["lithotrophic_aerobic_iron"] = max(v.get("lithotrophic_aerobic_iron", 0), 0.6)

    # --- Metabolite production ---
    mp = phys.get("metabolite production") or []
    if isinstance(mp, dict):
        mp = [mp]
    for m in mp if isinstance(mp, list) else []:
        if not isinstance(m, dict):
            continue
        met = (m.get("metabolite") or "").lower()
        prod = (m.get("production") or "")
        positive = isinstance(prod, str) and prod.lower() == "yes"
        if not positive:
            continue
        if "methane" in met:
            v["methanogenic"] = max(v.get("methanogenic", 0), 0.9)
        if met == "acetate":
            v["acetogenic"] = max(v.get("acetogenic", 0), 0.5)
            v["fermentative"] = max(v.get("fermentative", 0), 0.3)
        if "lactate" in met or "ethanol" in met or "butyrate" in met:
            v["fermentative"] = max(v.get("fermentative", 0), 0.5)
        if met in ("h2", "hydrogen"):
            v["fermentative"] = max(v.get("fermentative", 0), 0.4)
        if met == "n2" or "dinitrogen" in met:
            v["anaerobic_respiratory_nitrate"] = max(v.get("anaerobic_respiratory_nitrate", 0), 0.6)

    # --- Enzymes ---
    enzymes = phys.get("enzymes") or []
    if isinstance(enzymes, dict):
        enzymes = [enzymes]
    for e in enzymes if isinstance(enzymes, list) else []:
        if not isinstance(e, dict):
            continue
        name = (e.get("value") or e.get("enzyme") or "").lower()
        act = (e.get("activity") or "")
        positive = isinstance(act, str) and "+" in act
        if not positive:
            continue
        if "catalase" in name:
            v["aerobic_chemotrophic"] = max(v.get("aerobic_chemotrophic", 0), 0.4)
        if "oxidase" in name and "amine" not in name:
            v["aerobic_chemotrophic"] = max(v.get("aerobic_chemotrophic", 0), 0.6)
        if "nitrogenase" in name:
            v["nitrogen_fixation"] = max(v.get("nitrogen_fixation", 0), 0.9)

    # --- Halophily ---
    halophily_text = ""
    halo = phys.get("halophily")
    if isinstance(halo, str):
        halophily_text = halo
    elif isinstance(halo, list):
        halophily_text = " ".join(
            (e.get("halophily level") or e.get("halophily") or "") if isinstance(e, dict) else str(e)
            for e in halo
        )
    halophily_text = halophily_text.lower()
    cgc = strain.get("Culture and growth conditions", {}) or {}
    salt_text = ""
    salt = cgc.get("culture salt") or cgc.get("salt")
    if isinstance(salt, list):
        for s in salt:
            if isinstance(s, dict):
                salt_text += " " + str(s.get("salt", ""))
    elif isinstance(salt, str):
        salt_text = salt
    salt_text = salt_text.lower()
    if ("extreme halophil" in halophily_text or "halophil" in halophily_text and "non" not in halophily_text):
        v["halophily"] = 0.9
        if domain == "archaea":
            v["bacteriorhodopsin"] = max(v.get("bacteriorhodopsin", 0), 0.7)
    elif "moderate" in halophily_text or "halotolerant" in halophily_text:
        v["halophily"] = 0.5
    elif "non-halophil" in halophily_text:
        v["halophily"] = 0.0

    return v


def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity over capability vectors. 0.0 when both empty."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def find_functional_neighbors(target_genome_id: int, conn: sqlite3.Connection,
                                top_n: int = 5,
                                min_similarity: float = 0.40) -> List[tuple]:
    """Find functionally-similar CultureForge organisms (within the 26-organism
    dev+blind set) that DO have published media linked via direct BacDive match.

    The BacDive `Physiology and metabolism` section is too sparse (in practice
    most strains carry only `oxygen tolerance`) to support reliable BacDive-to-
    BacDive vector matching. Instead, we leverage the rich CultureForge
    capability profiles we already have for all 26 organisms: compute a vector
    for each, find the closest match among the subset that has direct media
    linkage, and reuse THEIR media as the reference.

    Returns: list of (neighbor_genome_id, neighbor_species, similarity,
                      [medium_ids that cultivate the neighbor]).
    """
    from capability_detectors import profile_capabilities

    target_profile = profile_capabilities(target_genome_id, conn)
    target_vec = cultureforge_to_vector(target_profile, conn=conn,
                                          genome_id=target_genome_id)
    if not target_vec:
        return []

    # Candidate genomes: any CF genome that has at least one direct media link
    # (i.e., a BacDive match that pointed to a MediaDive medium).
    candidates = conn.execute("""
        SELECT DISTINCT g.id, COALESCE(o.species, g.notes, g.accession)
        FROM genomes g
        LEFT JOIN organisms o ON o.id = g.organism_id
        JOIN organism_to_published_media op ON op.cultureforge_genome_id = g.id
        WHERE op.relationship = 'direct' AND g.id != ?
    """, (target_genome_id,)).fetchall()

    scored: List[tuple] = []
    for cgid, raw_sp in candidates:
        try:
            cprof = profile_capabilities(cgid, conn)
        except Exception:
            continue
        cvec = cultureforge_to_vector(cprof, conn=conn, genome_id=cgid)
        if not cvec:
            continue
        sim = cosine_similarity(target_vec, cvec)
        if sim >= min_similarity:
            sp_clean = (raw_sp or "?").replace("Validation organism: ", "") \
                                       .replace("Blind validation: ", "") \
                                       .replace("Blind v2: ", "") \
                                       .replace("_", " ")
            scored.append((cgid, sp_clean, sim))
    scored.sort(key=lambda x: x[2], reverse=True)

    out: List[tuple] = []
    for cgid, sp, sim in scored[:top_n]:
        media_ids = [r[0] for r in conn.execute(
            "SELECT DISTINCT medium_id FROM organism_to_published_media "
            "WHERE cultureforge_genome_id = ? AND relationship = 'direct'",
            (cgid,)
        ).fetchall()]
        if not media_ids:
            continue
        out.append((cgid, sp, round(sim, 3), media_ids))
    return out
