#!/usr/bin/env python3
"""
Verify the identity of the 168 dev-cohort genome FASTAs against GTDB RS226.

Sketches each genome with k=31, scaled=1000, runs `sourmash search
--containment` against the GTDB RS226 representatives sketch, and records the
top hits with their full GTDB lineage for downstream classification in Task 5.

sourmash is invoked via `conda run -n sourmash sourmash ...` so the script
runs from any active env, supporting manuscript reproducibility.

Usage:
    python3 data/validation/run_sourmash_identity_check.py
        [--manifest /tmp/genome_fasta_manifest.tsv]
        [--gtdb-db data/sourmash/gtdb-reps-rs226-k31.dna.zip]
        [--lineages data/sourmash/gtdb-rs226.lineages.csv]
        [--out-dir data/validation/sourmash_identity_verification]
        [--smoke-test 9,17,26,30,1012]
        [--top-n 3]
        [--workdir /tmp/sourmash_run]

The output TSV is written to
    <out-dir>/results_<UTC-timestamp>.tsv
with columns:
    gid, accession_in_db, claimed_organism, top_match_rank,
    top_match_gtdb_accession, top_match_lineage, top_match_genus,
    top_match_species, containment, query_name_from_fasta, notes
"""

import argparse
import csv
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


SOURMASH = ["conda", "run", "-n", "sourmash", "sourmash"]


def run(cmd, **kw):
    """Run a subprocess; raise on non-zero exit."""
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def sketch_one(fasta_path, out_sig, k=31, scaled=1000):
    """Sketch one FASTA into a .sig.zip with name-from-first."""
    cmd = SOURMASH + [
        "sketch", "dna",
        "-p", f"k={k},scaled={scaled}",
        "--name-from-first",
        "-o", str(out_sig),
        str(fasta_path),
    ]
    run(cmd)


def search_one(query_sig, db_path, out_csv, containment=True, top_n=3):
    """Run sourmash search; return top hits as list of dicts (parsed from CSV)."""
    cmd = SOURMASH + [
        "search",
        "-n", str(top_n),
        "-o", str(out_csv),
        str(query_sig),
        str(db_path),
    ]
    if containment:
        cmd.insert(cmd.index("search") + 1, "--containment")
    try:
        run(cmd)
    except subprocess.CalledProcessError as e:
        # Sourmash returns nonzero when nothing matched; treat as empty result
        if "no matches" in (e.stderr or "").lower() or "no matches" in (e.stdout or "").lower():
            return []
        raise

    if not os.path.exists(out_csv):
        return []
    with open(out_csv) as f:
        return list(csv.DictReader(f))


def load_lineages(path):
    """Map accession (ident) -> dict of lineage fields."""
    idx = {}
    with open(path) as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            idx[row["ident"]] = row
    return idx


def parse_accession(name_field):
    """Extract the leading accession from a sourmash result 'name' field.

    GTDB sketches use names like 'GCF_001541925.1 Nitrosopumilus sp. Nsub'.
    """
    m = re.match(r"^(GC[AF]_\d+\.\d+)", name_field or "")
    return m.group(1) if m else ""


def lookup_lineage(acc, lineages_idx):
    """Return (full_lineage, genus, species) or ('','','') if not found."""
    if acc not in lineages_idx:
        return "", "", ""
    row = lineages_idx[acc]
    parts = [row.get(k, "") for k in
             ("superkingdom", "phylum", "class", "order", "family", "genus", "species")]
    full = ";".join(p for p in parts if p)
    return full, row.get("genus", ""), row.get("species", "")


def short_notes(notes, n=80):
    return (notes or "")[:n].replace("\t", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default="/tmp/genome_fasta_manifest.tsv")
    ap.add_argument("--gtdb-db", default="data/sourmash/gtdb-reps-rs226-k31.dna.zip")
    ap.add_argument("--lineages", default="data/sourmash/gtdb-rs226.lineages.csv")
    ap.add_argument("--out-dir", default="data/validation/sourmash_identity_verification")
    ap.add_argument("--top-n", type=int, default=3, help="top N hits per query")
    ap.add_argument("--smoke-test", default="",
                    help="comma-separated gids; if set, only these are processed")
    ap.add_argument("--workdir", default="",
                    help="working dir for per-query sketches; defaults to mkdtemp")
    ap.add_argument("--no-containment", action="store_true",
                    help="use Jaccard similarity instead of containment")
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel worker threads (each spawns sourmash subprocesses)")
    args = ap.parse_args()

    # Setup
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    suffix = "_smoke" if args.smoke_test else ""
    out_tsv = out_dir / f"results_{ts}{suffix}.tsv"

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="sourmash_run_"))
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"[setup] workdir = {workdir}", file=sys.stderr)
    print(f"[setup] output  = {out_tsv}", file=sys.stderr)

    # Smoke-test gid filter
    smoke = set(args.smoke_test.split(",")) if args.smoke_test else set()

    # Load manifest
    queries = []
    with open(args.manifest) as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for row in rdr:
            if row["fasta_exists"] != "Y":
                continue
            if smoke and row["gid"] not in smoke:
                continue
            queries.append(row)
    print(f"[setup] {len(queries)} queries to process"
          + (f" (smoke test: {sorted(smoke)})" if smoke else ""), file=sys.stderr)

    # Load lineages
    print(f"[setup] loading lineages from {args.lineages} ...", file=sys.stderr)
    lineages_idx = load_lineages(args.lineages)
    print(f"[setup] {len(lineages_idx)} lineage records loaded", file=sys.stderr)

    # Sanity-check the DB exists
    for p in (args.gtdb_db, args.lineages):
        if not os.path.exists(p):
            print(f"[fatal] missing path: {p}", file=sys.stderr)
            sys.exit(2)

    # Write output header
    out_cols = ["gid", "accession_in_db", "claimed_organism", "top_match_rank",
                "top_match_gtdb_accession", "top_match_lineage",
                "top_match_genus", "top_match_species", "containment_or_similarity",
                "query_name_from_fasta", "notes"]
    metric = "similarity" if args.no_containment else "containment"
    containment = not args.no_containment

    def process_one(idx, q):
        """Sketch one genome and search; return (idx, q, hits_or_None, error_str)."""
        gid = q["gid"]
        fasta_path = q["fasta_path"]
        sig_path = workdir / f"gid_{gid}.sig.zip"
        search_csv = workdir / f"gid_{gid}.search.csv"
        try:
            if not sig_path.exists():
                sketch_one(fasta_path, sig_path)
            hits = search_one(sig_path, args.gtdb_db, search_csv,
                              containment=containment, top_n=args.top_n)
            return idx, q, hits, None
        except subprocess.CalledProcessError as e:
            err = (e.stderr or "")[-400:]
            return idx, q, None, err

    write_lock = threading.Lock()
    completed = [0]
    total = len(queries)
    start_t = time.time()

    def write_row(outw, idx, q, hits, error):
        gid = q["gid"]
        acc = q["accession"]
        notes = q["notes"]
        with write_lock:
            completed[0] += 1
            done = completed[0]
            elapsed = time.time() - start_t
            eta_s = (elapsed / done) * (total - done) if done else 0
            if error is not None:
                print(f"[{done}/{total}] gid={gid} ERROR: {error[:200]}", file=sys.stderr)
                outw.writerow([gid, acc, notes, "1", "", "", "", "", "",
                              "", f"sourmash_error: {error}"])
                return
            query_name = hits[0].get("query_name", "") if hits else ""
            if not hits:
                outw.writerow([gid, acc, notes, "1", "", "", "", "", "",
                              query_name, "no_matches"])
                print(f"[{done}/{total}] gid={gid} no_matches "
                      f"(elapsed {elapsed:.0f}s, ETA {eta_s:.0f}s)", file=sys.stderr)
                return
            for rank, h in enumerate(hits, 1):
                match_acc = parse_accession(h.get("name", ""))
                lineage, genus, species = lookup_lineage(match_acc, lineages_idx)
                val = h.get(metric, h.get("similarity", "") or "")
                if rank == 1:
                    print(f"[{done}/{total}] gid={gid} -> "
                          f"{h.get('name','')[:60]} {metric}={val} "
                          f"(elapsed {elapsed:.0f}s, ETA {eta_s:.0f}s)",
                          file=sys.stderr)
                outw.writerow([gid, acc, notes if rank == 1 else "", str(rank),
                              match_acc, lineage, genus, species, val,
                              query_name if rank == 1 else "", ""])

    with open(out_tsv, "w", newline="") as outf:
        w = csv.writer(outf, delimiter="\t")
        w.writerow(out_cols)

        if args.workers <= 1:
            for i, q in enumerate(queries, 1):
                _, _, hits, err = process_one(i, q)
                write_row(w, i, q, hits, err)
        else:
            print(f"[setup] running {args.workers} workers in parallel", file=sys.stderr)
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = [ex.submit(process_one, i, q) for i, q in enumerate(queries, 1)]
                for fut in as_completed(futs):
                    idx, q, hits, err = fut.result()
                    write_row(w, idx, q, hits, err)

    print(f"\n[done] wrote {out_tsv}", file=sys.stderr)
    print(str(out_tsv))  # print final path to stdout for capture


if __name__ == "__main__":
    main()
