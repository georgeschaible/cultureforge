"""Phase 1.5l hit-pattern audit.

For each (development-set organism, marker reference DB) pair, run blastp
against the post-correction marker BLAST databases and emit a TSV summarizing
hit counts, top scores, the positive-call decision, and a biological-sanity
verdict against curated expectations.

Output: data/validation/phase1_5l_hit_patterns.tsv
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
OUT_TSV = ROOT / "data" / "validation" / "phase1_5l_hit_patterns.tsv"
BLASTP = os.environ.get("CULTUREFORGE_BLASTP") or shutil.which("blastp") or "blastp"

# (organism display name, proteome path)
ORGANISMS: list[tuple[str, Path]] = [
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
]

# Markers (file basename → human label). Order by phenotype family.
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

# Per-marker BLAST thresholds — mirror run_marker_blast.py defaults.
DEFAULT_THRESH = {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0}
THRESH_OVERRIDES = {
    "amoA":  {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "pufLM": {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "mcrA":  {"evalue": 1e-30, "pident": 35.0, "qcov": 70.0},
    "hzsA":  {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
    "rdhA":  {"evalue": 1e-20, "pident": 30.0, "qcov": 60.0},
    "qmoA":  {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
}

# Curated biological expectations: organism → marker → expectation
# Values: "POSITIVE" (must hit), "NEGATIVE" (must not hit), "OPTIONAL" (may hit)
EXPECTATIONS: dict[str, dict[str, str]] = {
    "Escherichia_coli_K12": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "POSITIVE",
    },
    "Nitratidesulfovibrio_vulgaris": {
        "dsrAB": "POSITIVE", "qmoA": "POSITIVE", "aprAB": "POSITIVE",
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "OPTIONAL", "nosZ": "NEGATIVE",
        "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "OPTIONAL",
    },
    "Methanococcus_jannaschii": {
        "mcrA": "POSITIVE", "mcrBG": "POSITIVE",
        "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "POSITIVE", "cooS_cdhA": "POSITIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "OPTIONAL",
        "terminal_oxidases": "NEGATIVE",
    },
    "Thermus_aquaticus": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "POSITIVE",  # ba3/caa3-type, may hit weakly
    },
    "Lactobacillus_plantarum": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "NEGATIVE",  # aerotolerant fermenter, lacks ETC
    },
    "Acidithiobacillus_ferrooxidans": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "OPTIONAL", "cyc2": "POSITIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "POSITIVE",  # CBB cycle for CO2 fixation
        "terminal_oxidases": "POSITIVE",
    },
    "Clostridium_acetobutylicum": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",  # WL pathway components
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "NEGATIVE",  # strict anaerobe
    },
    "Geobacter_sulfurreducens": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "OPTIONAL", "cooS_cdhA": "OPTIONAL",
        "mtrC_omcB": "POSITIVE",  # iron reducer
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "NEGATIVE",  # anaerobe, but has many cytochromes
    },
    "Sulfolobus_acidocaldarius": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "POSITIVE",  # archaeal SoxM — known regression
    },
    "Campylobacter_jejuni": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "POSITIVE",  # microaerophile cb-type oxidase
    },
    "Magnetospirillum_magneticum": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "OPTIONAL",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "OPTIONAL",
        "terminal_oxidases": "POSITIVE",
    },
    "Sulfurimonas_denitrificans": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "POSITIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "POSITIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "POSITIVE",  # rTCA
        "terminal_oxidases": "POSITIVE",
    },
    "Nitrosomonas_europaea": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "POSITIVE", "hao": "POSITIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "POSITIVE",
        "terminal_oxidases": "POSITIVE",
    },
    "Rhodopseudomonas_palustris": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "OPTIONAL",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "POSITIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "POSITIVE",  # CBB cycle
        "terminal_oxidases": "POSITIVE",  # facultative aerobe
    },
    "Halobacterium_salinarum": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "NEGATIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "POSITIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "POSITIVE",  # archaeal terminal oxidase
    },
    "Syntrophomonas_wolfei": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "OPTIONAL", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "NEGATIVE",
        "terminal_oxidases": "NEGATIVE",  # obligate syntroph, anaerobe
    },
    "Acetobacterium_woodii": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "NEGATIVE", "qmoA": "NEGATIVE", "aprAB": "NEGATIVE",
        "soxB": "NEGATIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "OPTIONAL", "nosZ": "NEGATIVE",
        "acsB_cdhC": "POSITIVE", "cooS_cdhA": "POSITIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "NEGATIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "OPTIONAL",  # WL pathway, but no rbcL
        "terminal_oxidases": "NEGATIVE",
    },
    "Allochromatium_vinosum": {
        "mcrA": "NEGATIVE", "mcrBG": "NEGATIVE", "hzsA": "NEGATIVE", "hdh": "NEGATIVE",
        "dsrAB": "POSITIVE", "qmoA": "NEGATIVE", "aprAB": "POSITIVE",  # reverse dsr
        "soxB": "POSITIVE", "cyc2": "NEGATIVE",
        "amoA": "NEGATIVE", "hao": "NEGATIVE",
        "nifH": "POSITIVE", "nosZ": "NEGATIVE",
        "acsB_cdhC": "NEGATIVE", "cooS_cdhA": "NEGATIVE",
        "mtrC_omcB": "NEGATIVE",
        "pufLM": "POSITIVE", "psaA_psbA": "NEGATIVE", "pscA_fmoA": "NEGATIVE", "rhodopsin": "NEGATIVE",
        "rdhA": "NEGATIVE",
        "autotrophy": "POSITIVE",  # CBB
        "terminal_oxidases": "OPTIONAL",
    },
}


def run_blastp(proteome: Path, db_prefix: Path) -> list[dict]:
    """Run blastp and return parsed hit dicts (already filtered by per-marker thresholds)."""
    if not proteome.exists():
        return [{"_missing": True}]
    cmd = [
        BLASTP,
        "-query", str(proteome),
        "-db", str(db_prefix),
        "-evalue", "1e-5",
        "-outfmt", "6 qseqid sseqid pident length mismatch gapopen "
                   "qstart qend sstart send evalue bitscore qcovs",
        "-max_target_seqs", "5",
        "-num_threads", "4",
    ]
    env = {**os.environ, "PATH": (os.environ.get("CULTUREFORGE_BLAST_BIN", "") + os.pathsep if os.environ.get("CULTUREFORGE_BLAST_BIN") else "") + os.environ.get("PATH", "")}
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
    if proc.returncode != 0:
        sys.stderr.write(f"  blastp error db={db_prefix.name}: {proc.stderr[:200]}\n")
        return []
    hits = []
    for line in proc.stdout.strip().splitlines():
        f = line.split("\t")
        if len(f) < 13:
            continue
        hits.append({
            "qseq": f[0], "sseq": f[1],
            "pident": float(f[2]),
            "evalue": float(f[10]),
            "bitscore": float(f[11]),
            "qcov": float(f[12]),
        })
    return hits


def verdict(positive_call: bool, expectation: str) -> str:
    """Compare a positive-call to a curated expectation and return a one-word verdict."""
    if expectation == "POSITIVE":
        return "OK_TP" if positive_call else "MISS_FN"
    if expectation == "NEGATIVE":
        return "OK_TN" if not positive_call else "FALSE_POS"
    if expectation == "OPTIONAL":
        return "OK_OPT_HIT" if positive_call else "OK_OPT_NOHIT"
    return "UNKNOWN"


def main() -> int:
    rows = []
    for org_idx, (org, proteome) in enumerate(ORGANISMS, 1):
        for marker in MARKERS:
            db_prefix = MARKER_DIR / f"blastdb_{marker}"
            if not Path(str(db_prefix) + ".pdb").exists():
                rows.append({
                    "organism": org, "marker": marker,
                    "n_hits_total": "", "n_hits_positive": "",
                    "top_bitscore": "", "top_pident": "", "top_evalue": "",
                    "positive_call": "", "expectation": "", "verdict": "DB_MISSING",
                })
                continue

            sys.stderr.write(f"[{org_idx:02d}/{len(ORGANISMS)}] {org:35s} × {marker:20s} ... ")
            sys.stderr.flush()
            hits = run_blastp(proteome, db_prefix)

            if hits and hits[0].get("_missing"):
                rows.append({
                    "organism": org, "marker": marker,
                    "n_hits_total": "", "n_hits_positive": "",
                    "top_bitscore": "", "top_pident": "", "top_evalue": "",
                    "positive_call": "", "expectation": "", "verdict": "PROTEOME_MISSING",
                })
                sys.stderr.write("PROTEOME_MISSING\n")
                continue

            thr = THRESH_OVERRIDES.get(marker, DEFAULT_THRESH)
            positives = [
                h for h in hits
                if (h["evalue"] <= thr["evalue"]
                    and h["pident"] >= thr["pident"]
                    and h["qcov"]   >= thr["qcov"])
            ]
            if hits:
                top = max(hits, key=lambda h: h["bitscore"])
                top_bs = round(top["bitscore"], 1)
                top_pid = round(top["pident"], 1)
                top_e = top["evalue"]
            else:
                top_bs = 0
                top_pid = 0
                top_e = ""

            positive_call = len(positives) >= 1
            exp = EXPECTATIONS.get(org, {}).get(marker, "UNKNOWN")
            v = verdict(positive_call, exp)

            rows.append({
                "organism": org,
                "marker": marker,
                "n_hits_total": len(hits),
                "n_hits_positive": len(positives),
                "top_bitscore": top_bs,
                "top_pident": top_pid,
                "top_evalue": f"{top_e:.2e}" if isinstance(top_e, float) and top_e > 0 else "",
                "positive_call": "Y" if positive_call else "N",
                "expectation": exp,
                "verdict": v,
            })
            sys.stderr.write(f"hits={len(hits):3d} pos={len(positives):3d} top_bs={top_bs:7.1f} top_pid={top_pid:5.1f} {v}\n")

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["organism", "marker", "n_hits_total", "n_hits_positive",
            "top_bitscore", "top_pident", "top_evalue",
            "positive_call", "expectation", "verdict"]
    with OUT_TSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    n_total = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    sys.stderr.write("\n=== verdict tally ===\n")
    for k, v in sorted(counts.items()):
        sys.stderr.write(f"  {k:18s} {v}\n")
    sys.stderr.write(f"  total            {n_total}\n")
    sys.stderr.write(f"\nWrote {OUT_TSV}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
