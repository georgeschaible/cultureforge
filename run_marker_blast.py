"""BLAST a genome's predicted proteome against diagnostic marker databases.

Searches for high-weight diagnostic markers (mcrA, acsB, haoA, pufLM, etc.)
and stores hits in the genome_diagnostic_markers table.

Usage:
    python run_marker_blast.py <proteome.faa> --genome-id <id>
    # or programmatically:
    from run_marker_blast import blast_all_markers, SCHEMA_SQL
"""

import argparse
import os
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

from build_marker_blast_db import get_marker_databases

_ROOT = Path(__file__).parent

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS genome_diagnostic_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    marker_name TEXT NOT NULL,
    hit_gene TEXT,
    hit_accession TEXT,
    bitscore REAL,
    pident REAL,
    qcov REAL,
    evalue REAL,
    positive_call INTEGER DEFAULT 0,
    ingest_date TEXT,
    FOREIGN KEY (genome_id) REFERENCES genomes(id)
);
CREATE INDEX IF NOT EXISTS idx_gdm_genome ON genome_diagnostic_markers(genome_id);
CREATE INDEX IF NOT EXISTS idx_gdm_marker ON genome_diagnostic_markers(marker_name);
"""

# Default thresholds for positive call
HIT_THRESHOLDS = {
    "evalue": 1e-30,
    "pident": 30.0,
    "qcov": 70.0,
}

# Per-marker threshold overrides (Phase 1.5c).
# amoA/pufLM: broader thresholds for phylogenetically diverse markers.
#   amoA spans AOB (beta-proteobacteria), comammox (Nitrospirota), AOA (Thaumarchaeota).
#   pufLM spans purple bacteria and FAP-type reaction centers (Chloroflexi).
#   Both are integral membrane proteins with conserved structure but variable loops.
# mcrA: tighter threshold — highly conserved across all methanogens/ANME.
MARKER_THRESHOLDS = {
    "amoA":    {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "pufLM":   {"evalue": 1e-20, "pident": 25.0, "qcov": 60.0},
    "mcrA":    {"evalue": 1e-30, "pident": 35.0, "qcov": 70.0},
    "hzsA":    {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
    "rdhA":    {"evalue": 1e-20, "pident": 30.0, "qcov": 60.0},
    "qmoA":    {"evalue": 1e-30, "pident": 30.0, "qcov": 70.0},
    # Phase 3.3: nxrA tight threshold to discriminate canonical NOB from narG-family
    # cross-reactivity. Empirical narG ceiling = 48% pident; intra-clade NOB floor =
    # 87% pident. Threshold 75% sits in the gap. See nitrite_oxidation_review.md.
    "nxrA":    {"evalue": 1e-30, "pident": 75.0, "qcov": 80.0},
    # Phase 3.4: nrfA conservative threshold for canonical DNRA. NrfA family is
    # more sequence-divergent than NxrA — cross-class identity drops to ~32%.
    # Heme-motif analysis (CXXCK active site) classified borderline 30-34% hits as
    # 2 real divergent NrfA (Syntrophomonas, Geobacter) + 1 non-NrfA cytochrome
    # (Campylobacter, no CXXCK). 65% threshold cleanly catches canonical NrfA
    # (E. coli 90%, D. vulgaris 68.8%, Wolinella-class) while excluding the
    # Otr-family Campylobacter case. Divergent-NrfA gap documented in LIMITATIONS.
    "nrfA":    {"evalue": 1e-30, "pident": 65.0, "qcov": 80.0},
    # Phase 3.5: pmoA threshold sits in the 8-10 point gap between empirical
    # amoA cross-reactivity ceiling (50% pident, Nitrosomonas) and pmoA
    # cross-Type-I-II floor (58-60%). Dual-clade reference architecture (Type I,
    # II, III all represented) catches all major methanotroph lineages via
    # within-clade hits. mmoX threshold is generous because the family is
    # highly conserved (82-99% intra-family) with zero test-set cross-reactivity.
    # See methanotrophy_review.md.
    "pmoA":    {"evalue": 1e-30, "pident": 60.0, "qcov": 80.0},
    "mmoX":    {"evalue": 1e-30, "pident": 50.0, "qcov": 70.0},
}


def blast_all_markers(proteome_path: str,
                      genome_id: int,
                      conn: sqlite3.Connection) -> dict:
    """BLAST proteome against all marker databases and store results.

    Returns dict of marker_name -> list of positive hits.
    """
    conn.executescript(SCHEMA_SQL)

    # Clear previous results for this genome
    conn.execute("DELETE FROM genome_diagnostic_markers WHERE genome_id = ?",
                 (genome_id,))

    databases = get_marker_databases()
    if not databases:
        print("WARNING: No marker BLAST databases found. "
              "Run build_marker_blast_db.py first.", file=sys.stderr)
        return {}

    # Optional: prepend a conda env's bin/ to PATH so blastp resolves there.
    # Set CULTUREFORGE_BLAST_BIN to the directory containing blastp/makeblastdb;
    # otherwise rely on the ambient PATH (where BLAST+ is normally installed).
    blast_env = dict(os.environ)
    extra_bin = os.environ.get("CULTUREFORGE_BLAST_BIN")
    if extra_bin and os.path.isdir(extra_bin):
        blast_env["PATH"] = extra_bin + os.pathsep + blast_env.get("PATH", "")

    results = {}
    today = str(date.today())

    for marker_name, db_path in sorted(databases.items()):
        # Get per-marker thresholds (Phase 1.5c)
        thresholds = MARKER_THRESHOLDS.get(marker_name, HIT_THRESHOLDS)

        # Run BLASTP
        cmd = [
            "blastp",
            "-query", proteome_path,
            "-db", db_path,
            "-evalue", str(thresholds.get("evalue", HIT_THRESHOLDS["evalue"])),
            "-outfmt", "6 qseqid sseqid pident length mismatch gapopen "
                       "qstart qend sstart send evalue bitscore qcovs",
            "-max_target_seqs", "5",
            "-num_threads", "4",
        ]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                env=blast_env,
            )
        except Exception as e:
            print(f"  BLAST failed for {marker_name}: {e}", file=sys.stderr)
            results[marker_name] = []
            continue

        hits = []
        for line in proc.stdout.strip().split("\n"):
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 13:
                continue

            gene_id = fields[0]
            hit_acc = fields[1]
            pident = float(fields[2])
            evalue = float(fields[10])
            bitscore = float(fields[11])
            qcov = float(fields[12])

            positive = (
                evalue <= thresholds.get("evalue", HIT_THRESHOLDS["evalue"])
                and pident >= thresholds.get("pident", HIT_THRESHOLDS["pident"])
                and qcov >= thresholds.get("qcov", HIT_THRESHOLDS["qcov"])
            )

            conn.execute("""
                INSERT INTO genome_diagnostic_markers
                    (genome_id, marker_name, hit_gene, hit_accession,
                     bitscore, pident, qcov, evalue, positive_call, ingest_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (genome_id, marker_name, gene_id, hit_acc,
                  bitscore, pident, qcov, evalue, 1 if positive else 0, today))

            if positive:
                hits.append({
                    "gene": gene_id,
                    "accession": hit_acc,
                    "bitscore": bitscore,
                    "pident": pident,
                    "qcov": qcov,
                    "evalue": evalue,
                })

        results[marker_name] = hits

    conn.commit()
    return results


def get_marker_hits(genome_id: int, conn: sqlite3.Connection) -> dict:
    """Retrieve cached marker hits for a genome. Returns marker_name -> list of hits."""
    results = {}
    rows = conn.execute("""
        SELECT marker_name, hit_gene, hit_accession, bitscore, pident, qcov, evalue
          FROM genome_diagnostic_markers
         WHERE genome_id = ? AND positive_call = 1
         ORDER BY marker_name, bitscore DESC
    """, (genome_id,)).fetchall()

    for marker, gene, acc, bs, pid, qc, ev in rows:
        if marker not in results:
            results[marker] = []
        results[marker].append({
            "gene": gene,
            "accession": acc,
            "bitscore": bs,
            "pident": pid,
            "qcov": qc,
            "evalue": ev,
        })
    return results


def main():
    parser = argparse.ArgumentParser(
        description="BLAST proteome against diagnostic marker databases")
    parser.add_argument("proteome", help="Path to predicted proteome (.faa)")
    parser.add_argument("--genome-id", type=int, required=True,
                        help="Genome ID in the database")
    parser.add_argument("--db", default=str(_ROOT / "data" / "cultureforge.db"),
                        help="Database path")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    results = blast_all_markers(args.proteome, args.genome_id, conn)

    total_positive = sum(len(v) for v in results.values())
    markers_with_hits = sum(1 for v in results.values() if v)
    print(f"\n{markers_with_hits}/{len(results)} markers detected "
          f"({total_positive} total positive hits)")

    for marker, hits in sorted(results.items()):
        if hits:
            best = max(hits, key=lambda h: h["bitscore"])
            print(f"  {marker}: {len(hits)} hits "
                  f"(best: {best['pident']:.1f}% id, bs={best['bitscore']:.0f})")

    conn.close()


if __name__ == "__main__":
    main()
