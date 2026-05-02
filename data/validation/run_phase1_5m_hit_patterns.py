"""Phase 1.5m hit-pattern audit (Checkpoint 2 deliverable).

For each (organism in 26-organism dev+blind set, marker reference DB) pair,
run blastp against the post-1.5m marker BLAST databases. Emit a TSV that
mirrors phase1_5l_hit_patterns.tsv with one extra column comparing pre vs
post-1.5m positive-call decisions.

Output: data/validation/phase1_5m_hit_patterns.tsv
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER_DIR = ROOT / "data" / "diagnostic_markers"
OUT_TSV = ROOT / "data" / "validation" / "phase1_5m_hit_patterns.tsv"
PRE_TSV = ROOT / "data" / "validation" / "phase1_5l_hit_patterns.tsv"
BLASTP = os.environ.get("CULTUREFORGE_BLASTP") or shutil.which("blastp") or "blastp"

ORGANISMS: list[tuple[str, Path]] = [
    # 18 dev set
    ("Escherichia_coli_K12",          ROOT / "data/genomespot/ecoli/ecoli_proteins.faa"),
    ("Nitratidesulfovibrio_vulgaris", ROOT / "data/genomespot/dvulgaris/dvulgaris_proteins.faa"),
    ("Methanococcus_jannaschii",      ROOT / "data/genomespot/Methanococcus_jannaschii/Methanococcus_jannaschii_proteins.faa"),
    ("Thermus_aquaticus",             ROOT / "data/genomespot/Thermus_aquaticus/Thermus_aquaticus_proteins.faa"),
    ("Lactobacillus_plantarum",       ROOT / "data/genomespot/Lactobacillus_plantarum/Lactobacillus_plantarum_proteins.faa"),
    ("Acidithiobacillus_ferrooxidans",ROOT / "data/genomespot/Acidithiobacillus_ferrooxidans/Acidithiobacillus_ferrooxidans_proteins.faa"),
    ("Clostridium_acetobutylicum",    ROOT / "data/genomespot/Clostridium_acetobutylicum/Clostridium_acetobutylicum_proteins.faa"),
    ("Geobacter_sulfurreducens",      ROOT / "data/genomespot/Geobacter_sulfurreducens/Geobacter_sulfurreducens_proteins.faa"),
    ("Sulfolobus_acidocaldarius",     ROOT / "data/gapseq/Sulfolobus_acidocaldarius/Sulfolobus_acidocaldarius_proteins.faa"),
    ("Campylobacter_jejuni",          ROOT / "data/gapseq/Campylobacter_jejuni/Campylobacter_jejuni_proteins.faa"),
    ("Magnetospirillum_magneticum",   ROOT / "data/genomespot/Magnetospirillum_magneticum/Magnetospirillum_magneticum_proteins.faa"),
    ("Sulfurimonas_denitrificans",    ROOT / "data/genomespot/Sulfurimonas_denitrificans/Sulfurimonas_denitrificans_proteins.faa"),
    ("Nitrosomonas_europaea",         ROOT / "data/gapseq/Nitrosomonas_europaea/Nitrosomonas_europaea_proteins.faa"),
    ("Rhodopseudomonas_palustris",    ROOT / "data/gapseq/Rhodopseudomonas_palustris/Rhodopseudomonas_palustris_proteins.faa"),
    ("Halobacterium_salinarum",       ROOT / "data/gapseq/Halobacterium_salinarum/Halobacterium_salinarum_proteins.faa"),
    ("Syntrophomonas_wolfei",         ROOT / "data/gapseq/Syntrophomonas_wolfei/Syntrophomonas_wolfei_proteins.faa"),
    ("Acetobacterium_woodii",         ROOT / "data/gapseq/Acetobacterium_woodii/Acetobacterium_woodii_proteins.faa"),
    ("Allochromatium_vinosum",        ROOT / "data/gapseq/Allochromatium_vinosum/Allochromatium_vinosum.faa"),
    # 8 blind set
    ("Methanoperedens_nitroreducens", ROOT / "data/gapseq/Candidatus_Methanoperedens_nitroreducens/Candidatus_Methanoperedens_nitroreducens_proteins.faa"),
    ("Prometheoarchaeum_syntrophicum",ROOT / "data/gapseq/Candidatus_Prometheoarchaeum_syntrophicum/Candidatus_Prometheoarchaeum_syntrophicum_proteins.faa"),
    ("Scalindua_profunda",            ROOT / "data/gapseq/Candidatus_Scalindua_profunda/Candidatus_Scalindua_profunda_proteins.faa"),
    ("Chloroflexus_aurantiacus",      ROOT / "data/gapseq/Chloroflexus_aurantiacus/Chloroflexus_aurantiacus_proteins.faa"),
    ("Dehalococcoides_mccartyi",      ROOT / "data/gapseq/Dehalococcoides_mccartyi/Dehalococcoides_mccartyi_proteins.faa"),
    ("Nitrospira_moscoviensis",       ROOT / "data/gapseq/Nitrospira_moscoviensis/Nitrospira_moscoviensis_proteins.faa"),
    ("Picrophilus_torridus",          ROOT / "data/gapseq/Picrophilus_torridus/Picrophilus_torridus_proteins.faa"),
    ("Thermotoga_maritima",           ROOT / "data/gapseq/Thermotoga_maritima/Thermotoga_maritima_proteins.faa"),
]

MARKERS = [
    "mcrA", "mcrBG", "hzsA", "hdh",
    "dsrAB", "qmoA", "aprAB",
    "soxB", "cyc2",
    "amoA", "hao",
    "nifH", "nosZ",
    "acsB_cdhC", "cooS_cdhA",
    "mtrC_omcB",
    "pufLM", "psaA_psbA", "pscA_fmoA", "rhodopsin",
    "rdhA",
    "autotrophy",
    "terminal_oxidases",
]

DEFAULT_THRESH = {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0}
THRESH_OVERRIDES = {
    "amoA":  {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "pufLM": {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "mcrA":  {"evalue": 1e-30, "pident": 35.0, "qcov": 70.0},
    "hzsA":  {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
    "rdhA":  {"evalue": 1e-20, "pident": 30.0, "qcov": 60.0},
    "qmoA":  {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
}

# Curated biological expectations (extends Phase 1.5l). Values: POSITIVE / NEGATIVE / OPTIONAL.
# Phase 1.5l corrections incorporated (Rhodopseudomonas × soxB → OPTIONAL).
EXPECTATIONS: dict[str, dict[str, str]] = {
    # 18 dev set
    "Escherichia_coli_K12": {m: "NEGATIVE" for m in MARKERS} | {"terminal_oxidases": "POSITIVE"},
    "Nitratidesulfovibrio_vulgaris": {m: "NEGATIVE" for m in MARKERS} | {
        "dsrAB": "POSITIVE", "qmoA": "POSITIVE", "aprAB": "POSITIVE",
        "nifH": "OPTIONAL", "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",
        "terminal_oxidases": "OPTIONAL",
    },
    "Methanococcus_jannaschii": {m: "NEGATIVE" for m in MARKERS} | {
        "mcrA": "POSITIVE", "mcrBG": "POSITIVE",
        "nifH": "POSITIVE", "acsB_cdhC": "POSITIVE", "cooS_cdhA": "POSITIVE",
        "autotrophy": "OPTIONAL",
    },
    "Thermus_aquaticus": {m: "NEGATIVE" for m in MARKERS} | {"terminal_oxidases": "POSITIVE"},
    "Lactobacillus_plantarum": {m: "NEGATIVE" for m in MARKERS},
    "Acidithiobacillus_ferrooxidans": {m: "NEGATIVE" for m in MARKERS} | {
        "soxB": "OPTIONAL", "cyc2": "POSITIVE", "nifH": "POSITIVE",
        "autotrophy": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Clostridium_acetobutylicum": {m: "NEGATIVE" for m in MARKERS} | {
        "nifH": "POSITIVE", "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",
    },
    "Geobacter_sulfurreducens": {m: "NEGATIVE" for m in MARKERS} | {
        "nifH": "POSITIVE", "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",
        "mtrC_omcB": "POSITIVE",
    },
    "Sulfolobus_acidocaldarius": {m: "NEGATIVE" for m in MARKERS} | {
        "terminal_oxidases": "POSITIVE",
        "autotrophy": "POSITIVE",  # 3HP/4HB cycle (curation flip post-Checkpoint 2)
    },
    "Campylobacter_jejuni": {m: "NEGATIVE" for m in MARKERS} | {"terminal_oxidases": "POSITIVE"},
    "Magnetospirillum_magneticum": {m: "NEGATIVE" for m in MARKERS} | {
        "nifH": "POSITIVE", "nosZ": "OPTIONAL", "autotrophy": "OPTIONAL",
        "terminal_oxidases": "POSITIVE",
    },
    "Sulfurimonas_denitrificans": {m: "NEGATIVE" for m in MARKERS} | {
        "soxB": "POSITIVE", "nosZ": "POSITIVE",
        "autotrophy": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Nitrosomonas_europaea": {m: "NEGATIVE" for m in MARKERS} | {
        "amoA": "POSITIVE", "hao": "POSITIVE",
        "autotrophy": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Rhodopseudomonas_palustris": {m: "NEGATIVE" for m in MARKERS} | {
        "nifH": "POSITIVE", "nosZ": "OPTIONAL",
        "pufLM": "POSITIVE", "soxB": "OPTIONAL",
        "autotrophy": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Halobacterium_salinarum": {m: "NEGATIVE" for m in MARKERS} | {
        "rhodopsin": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Syntrophomonas_wolfei": {m: "NEGATIVE" for m in MARKERS} | {"nifH": "OPTIONAL"},
    "Acetobacterium_woodii": {m: "NEGATIVE" for m in MARKERS} | {
        "nifH": "OPTIONAL", "acsB_cdhC": "POSITIVE", "cooS_cdhA": "POSITIVE",
        "autotrophy": "OPTIONAL",
    },
    "Allochromatium_vinosum": {m: "NEGATIVE" for m in MARKERS} | {
        "dsrAB": "POSITIVE", "aprAB": "POSITIVE",
        "soxB": "POSITIVE", "nifH": "POSITIVE",
        "pufLM": "POSITIVE", "autotrophy": "POSITIVE",
        "terminal_oxidases": "OPTIONAL",
    },
    # 8 blind set
    "Methanoperedens_nitroreducens": {m: "NEGATIVE" for m in MARKERS} | {
        "mcrA": "POSITIVE",  # ANME runs methanogenesis in reverse; mcrA still present
        "mcrBG": "POSITIVE",
        "acsB_cdhC": "POSITIVE",  # Reverse Wood-Ljungdahl (curation flip post-Checkpoint 2)
        "cooS_cdhA": "POSITIVE",  # Reverse Wood-Ljungdahl (curation flip post-Checkpoint 2)
        "nifH": "POSITIVE",       # Some ANME encode nitrogenase (curation flip post-Checkpoint 2)
    },
    "Prometheoarchaeum_syntrophicum": {m: "NEGATIVE" for m in MARKERS},
    "Scalindua_profunda": {m: "NEGATIVE" for m in MARKERS} | {
        "hzsA": "POSITIVE", "hdh": "POSITIVE",
        "hao": "OPTIONAL", "autotrophy": "OPTIONAL",
    },
    "Chloroflexus_aurantiacus": {m: "NEGATIVE" for m in MARKERS} | {
        "pufLM": "POSITIVE",  # FAP-type reaction center, pufLM-like
        "autotrophy": "POSITIVE", "nifH": "OPTIONAL",
        "terminal_oxidases": "POSITIVE",
    },
    "Dehalococcoides_mccartyi": {m: "NEGATIVE" for m in MARKERS} | {
        "rdhA": "POSITIVE",
    },
    "Nitrospira_moscoviensis": {m: "NEGATIVE" for m in MARKERS} | {
        "amoA": "POSITIVE", "hao": "POSITIVE",  # comammox
        "autotrophy": "POSITIVE", "terminal_oxidases": "POSITIVE",
    },
    "Picrophilus_torridus": {m: "NEGATIVE" for m in MARKERS} | {
        "terminal_oxidases": "POSITIVE",
    },
    "Thermotoga_maritima": {m: "NEGATIVE" for m in MARKERS},
}


def run_blastp(proteome: Path, db_prefix: Path) -> list[dict]:
    if not proteome.exists():
        return [{"_missing": True}]
    cmd = [
        BLASTP, "-query", str(proteome), "-db", str(db_prefix),
        "-evalue", "1e-5",
        "-outfmt", "6 qseqid sseqid pident length mismatch gapopen "
                   "qstart qend sstart send evalue bitscore qcovs",
        "-max_target_seqs", "5", "-num_threads", "4",
    ]
    env = {**os.environ, "PATH": (os.environ.get("CULTUREFORGE_BLAST_BIN", "") + os.pathsep if os.environ.get("CULTUREFORGE_BLAST_BIN") else "") + os.environ.get("PATH", "")}
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
    if proc.returncode != 0:
        return []
    hits = []
    for line in proc.stdout.strip().splitlines():
        f = line.split("\t")
        if len(f) < 13:
            continue
        hits.append({"pident": float(f[2]), "evalue": float(f[10]),
                     "bitscore": float(f[11]), "qcov": float(f[12])})
    return hits


def verdict(positive: bool, exp: str) -> str:
    if exp == "POSITIVE": return "OK_TP" if positive else "MISS_FN"
    if exp == "NEGATIVE": return "OK_TN" if not positive else "FALSE_POS"
    if exp == "OPTIONAL": return "OK_OPT_HIT" if positive else "OK_OPT_NOHIT"
    return "UNKNOWN"


def load_pre_calls(path: Path) -> dict[tuple[str, str], str]:
    """Return {(organism, marker): positive_call} from Phase 1.5l TSV."""
    out: dict[tuple[str, str], str] = {}
    if not path.exists():
        return out
    with path.open() as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            out[(row["organism"], row["marker"])] = row.get("positive_call", "")
    return out


def main() -> int:
    pre = load_pre_calls(PRE_TSV)
    rows = []
    for i, (org, proteome) in enumerate(ORGANISMS, 1):
        for marker in MARKERS:
            db_prefix = MARKER_DIR / f"blastdb_{marker}"
            if not (Path(str(db_prefix) + ".pdb")).exists():
                rows.append({
                    "organism": org, "marker": marker,
                    "n_hits_total": "", "n_hits_positive": "",
                    "top_bitscore": "", "top_pident": "", "top_evalue": "",
                    "positive_call": "", "expectation": "",
                    "verdict": "DB_MISSING",
                    "pre_1_5m_call": pre.get((org, marker), ""),
                    "delta": "",
                })
                continue
            sys.stderr.write(f"[{i:02d}/{len(ORGANISMS)}] {org:35s} × {marker:20s} ... ")
            sys.stderr.flush()
            hits = run_blastp(proteome, db_prefix)
            if hits and hits[0].get("_missing"):
                sys.stderr.write("PROTEOME_MISSING\n")
                continue
            thr = THRESH_OVERRIDES.get(marker, DEFAULT_THRESH)
            positives = [h for h in hits
                         if h["evalue"] <= thr["evalue"]
                         and h["pident"] >= thr["pident"]
                         and h["qcov"]   >= thr["qcov"]]
            if hits:
                top = max(hits, key=lambda h: h["bitscore"])
                top_bs = round(top["bitscore"], 1); top_pid = round(top["pident"], 1)
                top_e = top["evalue"]
            else:
                top_bs = 0; top_pid = 0; top_e = ""
            positive = len(positives) >= 1
            exp = EXPECTATIONS.get(org, {}).get(marker, "UNKNOWN")
            v = verdict(positive, exp)
            new_call = "Y" if positive else "N"
            old_call = pre.get((org, marker), "")
            delta = "" if not old_call else ("same" if old_call == new_call else f"{old_call}→{new_call}")

            rows.append({
                "organism": org, "marker": marker,
                "n_hits_total": len(hits), "n_hits_positive": len(positives),
                "top_bitscore": top_bs, "top_pident": top_pid,
                "top_evalue": f"{top_e:.2e}" if isinstance(top_e, float) and top_e > 0 else "",
                "positive_call": new_call, "expectation": exp, "verdict": v,
                "pre_1_5m_call": old_call, "delta": delta,
            })
            sys.stderr.write(f"hits={len(hits):3d} pos={len(positives):3d} bs={top_bs:7.1f} pid={top_pid:5.1f} {v} [{delta}]\n")

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["organism", "marker", "n_hits_total", "n_hits_positive",
            "top_bitscore", "top_pident", "top_evalue",
            "positive_call", "expectation", "verdict",
            "pre_1_5m_call", "delta"]
    with OUT_TSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    counts: dict[str, int] = {}
    delta_counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        if r.get("delta"):
            delta_counts[r["delta"]] = delta_counts.get(r["delta"], 0) + 1
    sys.stderr.write("\n=== verdict tally ===\n")
    for k, v in sorted(counts.items()):
        sys.stderr.write(f"  {k:18s} {v}\n")
    sys.stderr.write("\n=== delta vs Phase 1.5l ===\n")
    for k, v in sorted(delta_counts.items(), key=lambda x: -x[1]):
        sys.stderr.write(f"  {k:18s} {v}\n")
    sys.stderr.write(f"\nWrote {OUT_TSV}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
