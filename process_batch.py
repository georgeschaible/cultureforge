"""Batch processing for CultureForge (Phase 5.0).

Reads a TSV list of genomes, runs `process_genome` on each one not already
registered, and tracks progress to `data/release/phase5_0_batch_progress.tsv`
so interrupted runs resume cleanly.

Input TSV format (tab-separated, header optional):
    accession      file_path                            notes
    GCF_000146045.2  data/genomes/saccharomyces.fna     Validation: model eukaryote
    ...

Progress TSV columns:
    accession  status  gid   file_path  started_utc  finished_utc  error  notes

Status values:
    pending    — not yet attempted
    running    — currently in progress (set when batch starts a genome)
    success    — pipeline completed and inspect verifies the genome
    failed     — pipeline raised; partial state was rolled back
    skipped    — accession was already registered before this batch run

Resume semantics:
    The progress file is the source of truth. On batch start, every accession
    in the input TSV is matched against the progress file:
    - missing → pending
    - status=success or skipped → leave alone
    - status=failed → re-attempted (the gid was rolled back; clean slate)
    - status=running → re-attempted (a previous batch was killed mid-stage;
      clean slate via deregister of any orphan partial gid). The fact that
      the row is "running" without a corresponding genomes-table entry is
      the recovery signal.

Default execution: sequential. The --parallel flag opts into N concurrent
pipelines (caller's responsibility to confirm system has the capacity).
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from process_genome import process_genome
from register_genome import deregister_genome, USER_GID_MIN

_ROOT = Path(__file__).resolve().parent
_DEFAULT_DB = str(_ROOT / "data" / "cultureforge.db")
_DEFAULT_PROGRESS = str(_ROOT / "data" / "release" / "phase5_0_batch_progress.tsv")

PROGRESS_COLUMNS = (
    "accession", "status", "gid", "file_path",
    "started_utc", "finished_utc", "error", "notes",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_input_tsv(path: str) -> List[dict]:
    """Parse the user's genome list. Header row optional; columns auto-detected.

    Returns list of dicts with keys: accession, file_path, notes (notes optional).
    """
    rows: List[dict] = []
    with open(path) as f:
        # Sniff for a header
        first_line = f.readline().rstrip("\n")
        f.seek(0)
        has_header = "accession" in first_line.lower() and "\t" in first_line

        reader = csv.reader(f, delimiter="\t")
        if has_header:
            header = [h.strip().lower() for h in next(reader)]
        else:
            header = ["accession", "file_path", "notes"]

        for line_no, row in enumerate(reader, start=2 if has_header else 1):
            if not row or all(not cell.strip() for cell in row):
                continue
            if row[0].startswith("#"):
                continue
            entry = {
                "accession": "",
                "file_path": "",
                "notes": "",
            }
            for i, cell in enumerate(row):
                if i < len(header):
                    entry[header[i]] = cell.strip()
            if not entry.get("accession") or not entry.get("file_path"):
                print(f"WARNING: line {line_no} missing accession or file_path; skipped")
                continue
            rows.append(entry)
    return rows


def _read_progress(path: str) -> dict:
    """Return dict mapping accession -> progress row dict. Empty if file missing."""
    p = Path(path)
    if not p.exists():
        return {}
    out: dict = {}
    with p.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            acc = row.get("accession", "").strip()
            if acc:
                out[acc] = row
    return out


def _write_progress(path: str, rows_by_acc: dict) -> None:
    """Write the progress dict back to disk (atomic-ish via tmp + rename)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROGRESS_COLUMNS, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        for acc, row in rows_by_acc.items():
            full = {col: row.get(col, "") for col in PROGRESS_COLUMNS}
            writer.writerow(full)
    tmp.replace(p)


def _accession_already_registered(db_path: str, accession: str) -> Optional[int]:
    """Return existing gid for the accession, or None if not present."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM genomes WHERE accession = ?", (accession,)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _process_one(
    entry: dict,
    db_path: str,
    biomass_template: str,
    skip_checkm2: bool,
    skip_mebipred: bool,
    verbose: bool,
    gapseq_output_dir_pattern: Optional[str] = None,
    skip_gapseq: bool = False,
) -> dict:
    """Run the pipeline for one entry. Returns the updated progress row dict."""
    acc = entry["accession"]
    fp = entry["file_path"]
    notes = entry.get("notes", "") or f"Phase 5.0 batch entry: {acc}"
    started = _utc_now()

    # Per-genome biomass override via the notes column (look for "biomass=Archaea")
    bt = biomass_template
    if "biomass=" in notes:
        try:
            bt = notes.split("biomass=", 1)[1].split()[0].rstrip(",")
        except (IndexError, AttributeError):
            pass

    # Phase 5.0: derive the cluster gapseq output dir for this accession
    gapseq_dir_for_this = None
    if skip_gapseq:
        if not gapseq_output_dir_pattern:
            raise ValueError(
                "skip_gapseq=True requires gapseq_output_dir_pattern (e.g. "
                "'data/cluster_gapseq_outputs/{accession}/')"
            )
        gapseq_dir_for_this = gapseq_output_dir_pattern.format(accession=acc)

    try:
        gid = process_genome(
            input_path=fp,
            accession=acc,
            notes=notes,
            biomass_template=bt,
            skip_checkm2=skip_checkm2,
            skip_mebipred=skip_mebipred,
            gapseq_output_dir=gapseq_dir_for_this,
            skip_gapseq=skip_gapseq,
            db_path=db_path,
            verbose=verbose,
        )
        return {
            "accession": acc,
            "status": "success",
            "gid": str(gid),
            "file_path": fp,
            "started_utc": started,
            "finished_utc": _utc_now(),
            "error": "",
            "notes": notes,
        }
    except Exception as exc:
        # process_genome already deregisters on failure, but in case it didn't
        # complete the cleanup (e.g. the cleanup itself failed), check for
        # any orphan gid >= USER_GID_MIN with this accession and try again.
        try:
            orphan = _accession_already_registered(db_path, acc)
            if orphan and orphan >= USER_GID_MIN:
                deregister_genome(db_path, orphan)
        except Exception:
            pass
        return {
            "accession": acc,
            "status": "failed",
            "gid": "",
            "file_path": fp,
            "started_utc": started,
            "finished_utc": _utc_now(),
            "error": str(exc).splitlines()[0][:300],
            "notes": notes,
        }


def process_batch(
    input_tsv: str,
    progress_tsv: str = _DEFAULT_PROGRESS,
    db_path: str = _DEFAULT_DB,
    biomass_template: str = "Gram_neg",
    skip_checkm2: bool = False,
    skip_mebipred: bool = False,
    verbose: bool = False,
    parallel: int = 1,
    gapseq_output_dir_pattern: Optional[str] = None,
    skip_gapseq: bool = False,
) -> dict:
    """Run the full pipeline on every entry in the input TSV.

    Skips entries whose accession is already registered. Tracks progress
    to the progress TSV so interrupted runs resume.

    Returns a summary dict with counts per status.
    """
    entries = _read_input_tsv(input_tsv)
    progress = _read_progress(progress_tsv)

    print(f"=== CultureForge process-batch ===", flush=True)
    print(f"  Input list:  {input_tsv}  ({len(entries)} entries)", flush=True)
    print(f"  Progress:    {progress_tsv}", flush=True)
    print(f"  Database:    {db_path}", flush=True)
    print(f"  Parallel:    {parallel}", flush=True)
    print(f"  Default biomass: {biomass_template}", flush=True)
    if skip_gapseq:
        print(f"  Skip-gapseq:     yes — using {gapseq_output_dir_pattern}", flush=True)
    print("", flush=True)

    todo: List[dict] = []
    skipped = succeeded_prior = 0
    for entry in entries:
        acc = entry["accession"]
        prior = progress.get(acc)

        # Already finished in a prior run
        if prior and prior["status"] in ("success", "skipped"):
            succeeded_prior += 1 if prior["status"] == "success" else 0
            skipped += 1 if prior["status"] == "skipped" else 0
            continue

        # Already registered in DB but not in our progress file → mark as skipped
        already = _accession_already_registered(db_path, acc)
        if already is not None:
            progress[acc] = {
                "accession": acc,
                "status": "skipped",
                "gid": str(already),
                "file_path": entry["file_path"],
                "started_utc": _utc_now(),
                "finished_utc": _utc_now(),
                "error": f"accession already registered as gid={already}",
                "notes": entry.get("notes", ""),
            }
            skipped += 1
            continue

        # Failed / running / pending — all get re-attempted
        todo.append(entry)

    _write_progress(progress_tsv, progress)
    print(f"Resuming: {len(todo)} pending, {skipped} skipped, {succeeded_prior} prior successes", flush=True)
    print("", flush=True)

    if not todo:
        print("Nothing to do.", flush=True)
        return {"pending": 0, "succeeded": succeeded_prior, "failed": 0, "skipped": skipped}

    succeeded = failed = 0
    n_total = len(todo)

    def _emit(idx: int, entry: dict, suffix: str = "") -> None:
        print(f"[{idx}/{n_total}] {entry['accession']} — {entry.get('notes', '(no notes)')[:60]}{suffix}",
              flush=True)

    if parallel <= 1:
        for i, entry in enumerate(todo, start=1):
            _emit(i, entry, " ...")
            # Mark running first so an interrupted batch can be detected later
            progress[entry["accession"]] = {
                "accession": entry["accession"],
                "status": "running",
                "gid": "",
                "file_path": entry["file_path"],
                "started_utc": _utc_now(),
                "finished_utc": "",
                "error": "",
                "notes": entry.get("notes", ""),
            }
            _write_progress(progress_tsv, progress)

            result = _process_one(
                entry, db_path, biomass_template,
                skip_checkm2, skip_mebipred, verbose,
                gapseq_output_dir_pattern=gapseq_output_dir_pattern,
                skip_gapseq=skip_gapseq,
            )
            progress[entry["accession"]] = result
            _write_progress(progress_tsv, progress)

            if result["status"] == "success":
                succeeded += 1
                print(f"      ✓ success — gid={result['gid']}", flush=True)
            else:
                failed += 1
                print(f"      ✗ failed — {result['error']}", flush=True)
            print("", flush=True)
    else:
        # Parallel mode — spawn N workers. Note: each gapseq run uses
        # substantial CPU/RAM, so the user is responsible for choosing a
        # reasonable N. SQLite writes are serialized via the GIL (we
        # serialize progress-file writes via a lock).
        from threading import Lock
        progress_lock = Lock()

        def _runner(idx_entry):
            i, entry = idx_entry
            _emit(i, entry, " ... (parallel)")
            with progress_lock:
                progress[entry["accession"]] = {
                    "accession": entry["accession"], "status": "running",
                    "gid": "", "file_path": entry["file_path"],
                    "started_utc": _utc_now(), "finished_utc": "",
                    "error": "", "notes": entry.get("notes", ""),
                }
                _write_progress(progress_tsv, progress)

            result = _process_one(
                entry, db_path, biomass_template,
                skip_checkm2, skip_mebipred, verbose,
                gapseq_output_dir_pattern=gapseq_output_dir_pattern,
                skip_gapseq=skip_gapseq,
            )
            with progress_lock:
                progress[entry["accession"]] = result
                _write_progress(progress_tsv, progress)
            return i, entry, result

        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = [pool.submit(_runner, ie) for ie in enumerate(todo, start=1)]
            for fut in as_completed(futures):
                i, entry, result = fut.result()
                if result["status"] == "success":
                    succeeded += 1
                    print(f"[{i}/{n_total}] {entry['accession']} ✓ gid={result['gid']}", flush=True)
                else:
                    failed += 1
                    print(f"[{i}/{n_total}] {entry['accession']} ✗ {result['error']}", flush=True)

    summary = {
        "pending": 0,
        "succeeded": succeeded + succeeded_prior,
        "failed": failed,
        "skipped": skipped,
    }
    print("", flush=True)
    print(f"=== Batch complete ===", flush=True)
    print(f"  Newly succeeded:  {succeeded}", flush=True)
    print(f"  Newly failed:     {failed}", flush=True)
    print(f"  Skipped (already in DB): {skipped}", flush=True)
    print(f"  Prior successes (resumed): {succeeded_prior}", flush=True)
    print(f"  Progress file: {progress_tsv}", flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch CultureForge processing for a TSV list of genomes",
    )
    parser.add_argument("--list", required=True, help="Input TSV (accession, file_path, notes)")
    parser.add_argument("--progress", default=_DEFAULT_PROGRESS,
                        help="Progress TSV path (default: data/release/phase5_0_batch_progress.tsv)")
    parser.add_argument("--db", default=_DEFAULT_DB)
    parser.add_argument("--biomass-template", default="Gram_neg",
                        choices=["Gram_neg", "Gram_pos", "Archaea"])
    parser.add_argument("--skip-checkm2", action="store_true")
    parser.add_argument("--skip-mebipred", action="store_true")
    parser.add_argument("--parallel", type=int, default=1,
                        help="Concurrent pipelines (default 1; gapseq is heavy, increase carefully)")
    parser.add_argument(
        "--gapseq-output-dir-pattern",
        help="Template path to pre-computed gapseq outputs, with {accession} "
             "placeholder (e.g. 'data/cluster_gapseq_outputs/{accession}/'). "
             "Used with --skip-gapseq for the cluster-then-load hybrid workflow.",
    )
    parser.add_argument(
        "--skip-gapseq", action="store_true",
        help="Skip the local gapseq run and load pre-computed cluster outputs. "
             "Requires --gapseq-output-dir-pattern.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    summary = process_batch(
        input_tsv=args.list,
        progress_tsv=args.progress,
        db_path=args.db,
        biomass_template=args.biomass_template,
        skip_checkm2=args.skip_checkm2,
        skip_mebipred=args.skip_mebipred,
        verbose=args.verbose,
        parallel=args.parallel,
        gapseq_output_dir_pattern=args.gapseq_output_dir_pattern,
        skip_gapseq=args.skip_gapseq,
    )
    sys.exit(0 if summary["failed"] == 0 else 1)
