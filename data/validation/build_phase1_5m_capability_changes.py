"""Build the V8 vs post-1.5m capability comparison TSV.

Reads phase1_5m_capability/*.json (post-1.5m calls) and compares against the
V8 baseline (extracted from phase1_5_capability_profiles.txt + Allochromatium
from PHASE_1_5_FIXES.md §7).

Output: data/validation/phase1_5m_capability_changes.tsv
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_DIR = ROOT / "data/validation/phase1_5m_capability"
OUT_TSV = ROOT / "data/validation/phase1_5m_capability_changes.tsv"

# V8 baseline = post-Phase-1.5k = the snapshot before Phase 1.5l/1.5m reference rebuild.
# 17 organisms from data/validation/phase1_5_capability_profiles.txt + Allochromatium added in 1.5k.
V8_BASELINE: dict[str, list[str]] = {
    "Escherichia_coli": [
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Nitratidesulfovibrio_vulgaris": [
        "Dissimilatory sulfate reduction",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Methanococcus_jannaschii": [
        "Methanogenesis (hydrogenotrophic, aceticlastic, or methylotrophic)",
    ],
    "Thermus_aquaticus": [
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Lactobacillus_plantarum": [
        "Substrate-level phosphorylation fermentation (mixed products)",
    ],
    "Acidithiobacillus_ferrooxidans": [
        "Sulfur/sulfide/thiosulfate oxidation",
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Clostridium_acetobutylicum": [
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
    ],
    "Geobacter_sulfurreducens": [
        "Dissimilatory sulfate reduction",
        "Dissimilatory Fe(III) reduction via extracellular electron transfer",
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Sulfolobus_acidocaldarius": [
        "Aerobic respiration",
    ],
    "Campylobacter_jejuni": [
        "Aerobic respiration via electron transport chain",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Magnetospirillum_magneticum": [
        "Dissimilatory sulfate reduction",
        "Denitrification (NO3- to N2)",
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Sulfurimonas_denitrificans": [
        "Sulfur/sulfide/thiosulfate oxidation",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Nitrosomonas_europaea": [
        "Aerobic ammonia oxidation (nitrification step 1)",
        "Sulfur/sulfide/thiosulfate oxidation",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Rhodopseudomonas_palustris": [
        "Anoxygenic phototrophy (purple bacteria, Type II reaction center)",
        "Sulfur/sulfide/thiosulfate oxidation",
        "Denitrification (NO3- to N2)",
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Halobacterium_salinarum": [
        "Bacteriorhodopsin/proteorhodopsin light-driven proton pump",
        "Substrate-level phosphorylation fermentation (mixed products)",
        "Aerobic respiration",
    ],
    "Syntrophomonas_wolfei": [
        "Substrate-level phosphorylation fermentation (mixed products)",
    ],
    "Acetobacterium_woodii": [
        "Acetogenesis via Wood-Ljungdahl pathway. Negative markers: mcrA (methanogen), dsrAB/aprAB (SRB using WL for autotrophic CO2 fixation), mtrC_omcB (iron reducer using WL for autotrophy)",
        "Biological nitrogen fixation (N2 to NH3)",
        "Substrate-level phosphorylation fermentation (mixed products)",
    ],
    # Allochromatium baseline from PHASE_1_5_FIXES.md §7 (post-1.5k validation):
    # Anoxygenic phototrophy 0.768, Sulfur oxidation 0.838, Nitrogen fixation 0.614, Sulfate reduction NOT detected (0.40)
    "Allochromatium_vinosum": [
        "Anoxygenic phototrophy (purple bacteria, Type II reaction center)",
        "Sulfur/sulfide/thiosulfate oxidation",
        "Biological nitrogen fixation (N2 to NH3)",
    ],
}


def short(name: str) -> str:
    """Compact display label for a capability name."""
    NAME_MAP = {
        "Substrate-level phosphorylation fermentation (mixed products)": "fermentation",
        "Aerobic respiration": "aerobic_resp",
        "Aerobic respiration via electron transport chain": "aerobic_etc",
        "Dissimilatory sulfate reduction": "sulfate_red",
        "Dissimilatory Fe(III) reduction via extracellular electron transfer": "Fe_red",
        "Biological nitrogen fixation (N2 to NH3)": "N2_fix",
        "Methanogenesis (hydrogenotrophic, aceticlastic, or methylotrophic)": "methanogenesis",
        "Sulfur/sulfide/thiosulfate oxidation": "sulfur_ox",
        "Aerobic ammonia oxidation (nitrification step 1)": "ammonia_ox",
        "Denitrification (NO3- to N2)": "denitrification",
        "Anoxygenic phototrophy (purple bacteria, Type II reaction center)": "phototrophy_purple",
        "Bacteriorhodopsin/proteorhodopsin light-driven proton pump": "rhodopsin",
    }
    if name in NAME_MAP:
        return NAME_MAP[name]
    if "Acetogenesis via Wood-Ljungdahl" in name:
        return "acetogenesis_WL"
    if "Acidophilic Fe(II)" in name or "iron oxidation" in name.lower():
        return "Fe_ox_acidophilic"
    return name[:30]


def main():
    rows = []
    rows.append("organism\tn_v8\tn_post1_5m\tv8_set\tpost_1_5m_set\tgained\tlost")

    for org, v8_caps in V8_BASELINE.items():
        json_path = JSON_DIR / f"{org}.json"
        if not json_path.exists():
            rows.append(f"{org}\t{len(v8_caps)}\t-\t{','.join(short(c) for c in v8_caps)}\tMISSING\t\t")
            continue
        with json_path.open() as f:
            d = json.load(f)
        post = d.get("primary_metabolisms", [])
        v8_set = {short(c) for c in v8_caps}
        post_set = {short(c) for c in post}
        gained = sorted(post_set - v8_set)
        lost = sorted(v8_set - post_set)
        rows.append(
            f"{org}\t{len(v8_caps)}\t{len(post)}\t"
            f"{','.join(sorted(v8_set))}\t"
            f"{','.join(sorted(post_set))}\t"
            f"{','.join(gained)}\t"
            f"{','.join(lost)}"
        )

    OUT_TSV.write_text("\n".join(rows) + "\n")
    print(f"Wrote {OUT_TSV}")
    print()
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
