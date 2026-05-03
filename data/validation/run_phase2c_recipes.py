"""Phase 2c — generate recipes for all 26 organisms (18 dev + 8 blind).

Output: docs/recipe_examples/<organism>_recipe.txt (inspector format)
        docs/recipe_examples/<organism>_recipe.json (full JSON)
        + a summary table for docs/RECIPE_EVALUATION.md
"""

import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "docs" / "recipe_examples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (genome_id, label, organism set)
ORGANISMS = [
    # 18 dev set
    (7,  "Nitratidesulfovibrio_vulgaris", "dev"),
    (8,  "Methanococcus_jannaschii", "dev"),
    (9,  "Thermus_aquaticus", "dev"),
    (10, "Lactobacillus_plantarum", "dev"),
    (11, "Acidithiobacillus_ferrooxidans", "dev"),
    (12, "Clostridium_acetobutylicum", "dev"),
    (13, "Geobacter_sulfurreducens", "dev"),
    (14, "Sulfolobus_acidocaldarius", "dev"),
    (15, "Campylobacter_jejuni", "dev"),
    (16, "Magnetospirillum_magneticum", "dev"),
    (17, "Sulfurimonas_denitrificans", "dev"),
    (18, "Nitrosomonas_europaea", "dev"),
    (19, "Rhodopseudomonas_palustris", "dev"),
    (20, "Halobacterium_salinarum", "dev"),
    (21, "Syntrophomonas_wolfei", "dev"),
    (22, "Acetobacterium_woodii", "dev"),
    (31, "Allochromatium_vinosum", "dev"),
    (32, "Escherichia_coli", "dev"),
    # 8 blind set
    (23, "Nitrospira_moscoviensis", "blind"),
    (24, "Chloroflexus_aurantiacus", "blind"),
    (25, "Dehalococcoides_mccartyi", "blind"),
    (26, "Picrophilus_torridus", "blind"),
    (27, "Thermotoga_maritima", "blind"),
    (28, "Methanoperedens_nitroreducens", "blind"),
    (29, "Prometheoarchaeum_syntrophicum", "blind"),
    (30, "Scalindua_profunda", "blind"),
]


def main() -> None:
    conn = sqlite3.connect(str(ROOT / "data/cultureforge.db"))
    summary = []
    for gid, label, orgset in ORGANISMS:
        # Inspector text output
        txt_path = OUT_DIR / f"{label}_recipe.txt"
        cmd = [
            os.environ.get("CULTUREFORGE_PYTHON", sys.executable),
            str(ROOT / "cultureforge.py"), "inspect", str(gid),
            "--section", "recipe", "--output", str(txt_path),
        ]
        subprocess.run(cmd, check=False, capture_output=True)

        # JSON output via direct compose call (faster + structured)
        from compose_recipe import compose_recipe
        recipe = compose_recipe(gid, conn)
        d = asdict(recipe)
        for ing in d.get("ingredients", []):
            cat = ing.get("category")
            if hasattr(cat, "value"):
                ing["category"] = cat.value
        json_path = OUT_DIR / f"{label}_recipe.json"
        with json_path.open("w") as f:
            json.dump(d, f, indent=2, default=str)

        summary.append({
            "gid": gid, "label": label, "set": orgset,
            "species": recipe.species,
            "primary_mode": recipe.primary_cultivation_mode,
            "alt_modes": recipe.alternative_cultivation_modes,
            "n_ingredients": len(recipe.ingredients),
            "gas": (recipe.gas_phase.composition if recipe.gas_phase else None),
            "T_c": recipe.conditions.temperature_c if recipe.conditions else None,
            "ph": recipe.conditions.ph if recipe.conditions else None,
            "delta_g": (recipe.thermodynamic_checks[0].delta_g_kj_per_mol
                        if recipe.thermodynamic_checks else None),
            "feasibility": (recipe.thermodynamic_checks[0].feasibility_class
                            if recipe.thermodynamic_checks else None),
            "confidence": recipe.overall_confidence,
            "uncertainty_n": len(recipe.uncertainty_flags),
            "limitations": recipe.limitations_referenced,
            "escalated": recipe.escalated,
        })

    # Write a tab-delimited summary
    sum_path = OUT_DIR / "phase2c_summary.tsv"
    cols = ["gid","label","set","primary_mode","alt_modes","T_c","ph",
            "gas","delta_g","feasibility","confidence","limitations","escalated"]
    with sum_path.open("w") as f:
        f.write("\t".join(cols) + "\n")
        for s in summary:
            row = [
                str(s["gid"]), s["label"], s["set"], s["primary_mode"],
                ";".join(s["alt_modes"]),
                f"{s['T_c']:.1f}" if s["T_c"] else "",
                f"{s['ph']:.1f}" if s["ph"] else "",
                str(s["gas"]) if s["gas"] else "",
                f"{s['delta_g']:.1f}" if s["delta_g"] is not None else "",
                s["feasibility"] or "",
                f"{s['confidence']:.2f}",
                ";".join(s["limitations"]),
                "yes" if s["escalated"] else "no",
            ]
            f.write("\t".join(row) + "\n")
    print(f"Wrote {sum_path}")
    print(f"Wrote {len(ORGANISMS)} text + {len(ORGANISMS)} JSON files in {OUT_DIR}")


if __name__ == "__main__":
    main()
