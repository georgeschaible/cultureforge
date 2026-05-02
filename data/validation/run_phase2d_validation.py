"""Phase 2d Task 6 — full validation pass on all 26 organisms.

For each (CF genome) → write the comparison report (text + JSON) and aggregate
into a single summary TSV.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from compose_recipe import compose_recipe
from recipe_comparison import compare_recipes
from capability_vector import find_functional_neighbors

OUT = ROOT / "docs" / "recipe_examples"
OUT.mkdir(parents=True, exist_ok=True)

ORGANISMS = [
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
    rows = []
    for gid, label, orgset in ORGANISMS:
        recipe = compose_recipe(gid, conn)

        # Direct match path
        direct_media = [r[0] for r in conn.execute(
            "SELECT DISTINCT medium_id FROM organism_to_published_media "
            "WHERE cultureforge_genome_id = ? AND relationship = 'direct'",
            (gid,)
        ).fetchall()]

        relationship = ""
        n_refs = 0
        n_neighbors = 0
        n_shared = 0
        n_critical = 0
        n_important = 0
        agreement = 0.0
        ref_ids: list = []

        if direct_media:
            relationship = "direct"
            n_refs = len(direct_media)
            ref_ids = direct_media
            report = compare_recipes(recipe, direct_media, conn,
                                       relationship="direct", genome_id=gid,
                                       species=label)
            n_shared = sum(1 for d in report.diffs if d.kind == "shared")
            # n_shared as the count of common ingredients = total diffs of kind shared
            # (we don't add shared to diffs anymore — count from the rationale text)
            shared_match = report.rationale.split(" shared")[0].split()[-1]
            try: n_shared = int(shared_match)
            except: pass
            n_critical = sum(1 for d in report.diffs if d.severity == "critical")
            n_important = sum(1 for d in report.diffs if d.severity == "important")
            agreement = report.overall_agreement
        else:
            relationship = "functional_neighbor"
            nbrs = find_functional_neighbors(gid, conn, top_n=5,
                                              min_similarity=0.30)
            n_neighbors = len(nbrs)
            neighbor_media: list = []
            for ngid, ns, sim, media in nbrs:
                neighbor_media.extend(media)
            seen: set = set()
            ref_ids = [m for m in neighbor_media if not (m in seen or seen.add(m))]
            n_refs = len(ref_ids)
            if ref_ids:
                report = compare_recipes(recipe, ref_ids, conn,
                                           relationship="functional_neighbor",
                                           genome_id=gid, species=label)
                shared_match = report.rationale.split(" shared")[0].split()[-1]
                try: n_shared = int(shared_match)
                except: pass
                n_critical = sum(1 for d in report.diffs if d.severity == "critical")
                n_important = sum(1 for d in report.diffs if d.severity == "important")
                agreement = report.overall_agreement

        rows.append({
            "gid": gid, "label": label, "set": orgset,
            "relationship": relationship,
            "n_neighbors": n_neighbors,
            "n_refs": n_refs,
            "n_shared": n_shared,
            "n_critical": n_critical,
            "n_important": n_important,
            "agreement_pct": int(agreement * 100),
            "ref_ids": ",".join(sorted(ref_ids)[:6]) + ("..." if len(ref_ids) > 6 else ""),
        })

    # Save TSV
    tsv = OUT / "phase2d_validation_summary.tsv"
    cols = ["gid","label","set","relationship","n_neighbors","n_refs",
            "n_shared","n_critical","n_important","agreement_pct","ref_ids"]
    with tsv.open("w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"Wrote {tsv}")

    # Print
    print()
    for r in rows:
        sett = r["set"][:5]
        rel = r["relationship"][:8]
        print(f"  [{sett}] gid={r['gid']:2d}  {r['label'][:32]:32s}  "
              f"{rel:9s}  refs={r['n_refs']:3d}  "
              f"shared={r['n_shared']:3d}  crit={r['n_critical']}  imp={r['n_important']}  "
              f"agreement={r['agreement_pct']}%")


if __name__ == "__main__":
    main()
