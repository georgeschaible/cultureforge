"""A1 verification probe — read-only capability + recipe snapshot per gid.

Usage: python3 data/validation/a1_verify_probe.py <stage>
  stage = "before" or "after". Prints one JSON line per gid.
"""
import json
import sqlite3
import sys

sys.path.insert(0, ".")
from capability_detectors import profile_capabilities  # noqa: E402
from compose_recipe import compose_recipe  # noqa: E402

GIDS = [1049, 1102, 1106, 18, 1039, 1114, 900, 903,
        1047, 1060, 1026, 1012, 1070]

CAPS = ("ammonia_oxidation", "methane_oxidation",
        "aerobic_methanotrophy")


def best_marker(conn, gid, marker):
    row = conn.execute(
        """SELECT pident, bitscore, qcov, positive_call
             FROM genome_diagnostic_markers
            WHERE genome_id=? AND marker_name=?
            ORDER BY bitscore DESC LIMIT 1""",
        (gid, marker)).fetchone()
    if not row:
        return None
    return {"pident": row[0], "bitscore": row[1],
            "qcov": row[2], "positive_call": row[3]}


def cap_by_name(profile, *names):
    for c in profile.capabilities:
        # match canonical key OR description substring
        if c.name in names:
            return c
    # fall back: description contains a friendly token
    for c in profile.capabilities:
        d = c.name.lower()
        if "ammonia oxidation" in d and "ammonia_oxidation" in names:
            return c
        if ("methanotrophy" in d or "methane" in d) and (
                "methane_oxidation" in names
                or "aerobic_methanotrophy" in names):
            return c
    return None


def main():
    stage = sys.argv[1]
    conn = sqlite3.connect("data/cultureforge.db")
    for gid in GIDS:
        prof = profile_capabilities(gid, conn)
        amm = cap_by_name(prof, "ammonia_oxidation")
        met = cap_by_name(prof, "aerobic_methanotrophy", "methane_oxidation")
        modes = [(m["mode"], round(m["max_confidence"], 3))
                 for m in prof.cultivation_modes]
        rec = compose_recipe(gid, conn)
        out = {
            "gid": gid,
            "stage": stage,
            "ammonia_oxidation": {
                "conf": round(amm.confidence, 3) if amm else None,
                "detected": amm.detected if amm else None,
                "name": amm.name if amm else None,
            },
            "methanotrophy": {
                "conf": round(met.confidence, 3) if met else None,
                "detected": met.detected if met else None,
                "name": met.name if met else None,
            },
            "amoA": best_marker(conn, gid, "amoA"),
            "amoA_archaeal": best_marker(conn, gid, "amoA_archaeal"),
            "modes": modes,
            "recipe_escalated": rec.escalated,
            "recipe_primary_mode": getattr(
                rec, "primary_cultivation_mode", None),
            "recipe_overall_conf": round(rec.overall_confidence, 3),
            "recipe_escalation_reason": (
                rec.escalation_reason if rec.escalated else None),
        }
        print(json.dumps(out))
    conn.close()


if __name__ == "__main__":
    main()
