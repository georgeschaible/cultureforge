"""Fetch 16S rRNA sequences from NCBI for accessions found in BacDive data.

Reads:  data/16s_accessions.json   — {bacdive_id: [(accession, length, desc), ...]}
Writes: data/16s_reference.fasta   — FASTA with headers >accession|bacdive_id|species
        data/16s_acc_to_bid.json   — {accession: bacdive_id} mapping

Uses NCBI Entrez efetch in batches of 200 (NCBI guideline for unauthenticated).
"""

import json
import os
import sqlite3
import time
from pathlib import Path

import os

from Bio import Entrez, SeqIO
from io import StringIO

Entrez.email = os.environ.get("ENTREZ_EMAIL", "your-email@example.com")
Entrez.tool = "CultureForge"
if Entrez.email == "your-email@example.com":
    print("WARNING: ENTREZ_EMAIL environment variable not set. NCBI Entrez requires "
          "a contact email per their access policy. Set ENTREZ_EMAIL=you@example.com "
          "before running this script.")

_ROOT = Path(__file__).parent

BATCH_SIZE = 200
SLEEP = 0.4  # NCBI asks for ≤3 requests/sec without API key
FASTA_OUT = str(_ROOT / "data" / "16s_reference.fasta")
MAP_OUT = str(_ROOT / "data" / "16s_acc_to_bid.json")
DB = str(_ROOT / "data" / "cultureforge.db")


def load_accessions():
    with open(_ROOT / "data" / "16s_accessions.json") as f:
        raw = json.load(f)
    # Build accession -> bacdive_id mapping (first occurrence wins)
    acc_to_bid = {}
    for bid, entries in raw.items():
        for acc, length, desc in entries:
            if acc not in acc_to_bid:
                acc_to_bid[acc] = int(bid)
    return acc_to_bid


def get_species_map():
    """Map bacdive_id -> species from the database."""
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, species FROM organisms").fetchall()
    conn.close()
    return {r[0]: r[1] or "unknown" for r in rows}


def fetch_batch(accessions):
    """Fetch a batch of sequences from NCBI nucleotide."""
    ids = ",".join(accessions)
    handle = Entrez.efetch(db="nucleotide", id=ids, rettype="fasta", retmode="text")
    text = handle.read()
    handle.close()
    return text


def main():
    acc_to_bid = load_accessions()
    species_map = get_species_map()
    accessions = list(acc_to_bid.keys())
    print(f"Fetching {len(accessions)} sequences from NCBI in batches of {BATCH_SIZE}...")

    # Check for existing partial download
    existing = set()
    if os.path.exists(FASTA_OUT):
        with open(FASTA_OUT) as f:
            for line in f:
                if line.startswith(">"):
                    acc = line.split("|")[0].lstrip(">").strip()
                    existing.add(acc)
        print(f"  Resuming: {len(existing)} sequences already downloaded")

    remaining = [a for a in accessions if a not in existing]
    print(f"  {len(remaining)} sequences to fetch")

    fasta_handle = open(FASTA_OUT, "a")
    n_fetched = 0
    n_failed = 0

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        try:
            text = fetch_batch(batch)
            # Parse and rewrite headers with our metadata
            for record in SeqIO.parse(StringIO(text), "fasta"):
                # NCBI returns IDs like "KJ812345.1"
                # Match to our accessions (might be versioned or not)
                acc_found = None
                for acc in batch:
                    if record.id.startswith(acc) or acc.startswith(record.id.split(".")[0]):
                        acc_found = acc
                        break
                if acc_found is None:
                    # Try matching on the full description
                    acc_found = record.id.split(".")[0]

                bid = acc_to_bid.get(acc_found, acc_to_bid.get(record.id.split(".")[0], 0))
                species = species_map.get(bid, "unknown")
                safe_species = species.replace(" ", "_")

                fasta_handle.write(f">{acc_found}|{bid}|{safe_species}\n")
                fasta_handle.write(str(record.seq) + "\n")
                n_fetched += 1

        except Exception as e:
            print(f"  Batch {i//BATCH_SIZE + 1}: FAILED ({e})")
            n_failed += len(batch)

        if (i // BATCH_SIZE + 1) % 10 == 0 or i + BATCH_SIZE >= len(remaining):
            print(f"  Batch {i//BATCH_SIZE + 1}/{(len(remaining) + BATCH_SIZE - 1)//BATCH_SIZE}: "
                  f"{n_fetched} fetched, {n_failed} failed")
            fasta_handle.flush()

        time.sleep(SLEEP)

    fasta_handle.close()

    # Save mapping
    with open(MAP_OUT, "w") as f:
        json.dump(acc_to_bid, f)

    print(f"\nDone. {n_fetched} sequences -> {FASTA_OUT}")
    print(f"Mapping: {MAP_OUT}")


if __name__ == "__main__":
    main()
