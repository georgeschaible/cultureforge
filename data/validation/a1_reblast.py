"""A1 targeted marker-BLAST re-run for the verification subset.

Uses cached proteome.faa where present; runs prodigal for genome-only gids.
Calls run_marker_blast.blast_all_markers (the same path process_genome Stage 4
uses), which DELETEs+re-inserts genome_diagnostic_markers for each gid.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")
from run_marker_blast import blast_all_markers, SCHEMA_SQL  # noqa: E402

# gid -> proteome path (None => derive via prodigal from genome_fasta)
PROTEOME = {
    1049: "data/user_genomes/GCF_000018465.1/proteome.faa",
    1102: "data/user_genomes/GCF_000698785.1/proteome.faa",
    1106: "data/user_genomes/GCF_000802205.1/proteome.faa",
    1039: "data/user_genomes/GCF_000014765.1/proteome.faa",
    1114: "data/user_genomes/GCF_001458695.1/proteome.faa",
    900:  "data/sentinel/Methylococcus_capsulatus_Bath/proteome.faa",
    903:  "data/sentinel/Methanosarcina_acetivorans_C2A/proteome.faa",
    1047: "data/user_genomes/GCF_000018305.1/proteome.faa",
    1060: "data/user_genomes/GCF_000022205.1/proteome.faa",
    1026: "data/user_genomes/GCF_000011585.1/proteome.faa",
    1012: "data/user_genomes/GCF_000007305.1/proteome.faa",
    1070: "data/user_genomes/GCF_000152265.2/proteome.faa",
}
GENOME_ONLY = {18: "data/genomes/Nitrosomonas_europaea.fasta"}


def prodigal(genome, outdir):
    faa = Path(outdir) / "proteome.faa"
    gff = Path(outdir) / "genes.gff"
    cmd = ["prodigal", "-i", genome, "-a", str(faa),
           "-o", str(gff), "-f", "gff", "-p", "single"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"prodigal failed: {r.stderr[:300]}")
    return str(faa)


def main():
    conn = sqlite3.connect("data/cultureforge.db")
    conn.executescript(SCHEMA_SQL)
    tmp = tempfile.mkdtemp(prefix="a1_reblast_")

    plan = []
    for gid, p in PROTEOME.items():
        plan.append((gid, p))
    for gid, gpath in GENOME_ONLY.items():
        print(f"  prodigal gid {gid} <- {gpath}", flush=True)
        plan.append((gid, prodigal(gpath, tmp)))

    for gid, faa in sorted(plan):
        if not Path(faa).exists():
            raise FileNotFoundError(f"gid {gid}: proteome missing {faa}")
        res = blast_all_markers(faa, gid, conn)
        conn.commit()
        n_pos = sum(1 for v in res.values() for h in v)
        arch = "amoA_archaeal" in res and len(res["amoA_archaeal"]) > 0
        amo = "amoA" in res and len(res["amoA"]) > 0
        print(f"  gid {gid}: {len(res)} markers fired, {n_pos} positive hits; "
              f"amoA={'Y' if amo else 'n'} amoA_archaeal={'Y' if arch else 'n'}",
              flush=True)
    conn.close()
    print("RE-BLAST COMPLETE")


if __name__ == "__main__":
    main()
