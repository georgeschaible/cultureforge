"""Fetch 16S sequences for TEMPURA accessions not already in our reference FASTA.

Reads:  data/tempura/new_16s_accessions.json   — {accession: organism_id}
Appends to: data/16s_reference.fasta
"""

import json
import os
import sqlite3
import os
import time
from pathlib import Path

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
SLEEP = 0.4
FASTA_OUT = str(_ROOT / "data" / "16s_reference.fasta")
ACC_INPUT = str(_ROOT / "data" / "tempura" / "new_16s_accessions.json")
DB = str(_ROOT / "data" / "cultureforge.db")


def main():
    with open(ACC_INPUT) as f:
        acc_to_orgid = json.load(f)

    # Skip already-downloaded
    existing = set()
    if os.path.exists(FASTA_OUT):
        with open(FASTA_OUT) as f:
            for line in f:
                if line.startswith(">"):
                    acc = line.split("|")[0].lstrip(">").strip()
                    existing.add(acc)
                    # Also strip versions (KJ123.1 -> KJ123)
                    existing.add(acc.split(".")[0])

    remaining = [acc for acc in acc_to_orgid if acc not in existing
                 and acc.split(".")[0] not in existing]
    print(f"  {len(acc_to_orgid)} total TEMPURA accessions, "
          f"{len(remaining)} not yet downloaded")

    if not remaining:
        print("Nothing to fetch.")
        return

    conn = sqlite3.connect(DB)
    species_map = {r[0]: (r[1] or "unknown") for r in
                   conn.execute("SELECT id, species FROM organisms")}
    conn.close()

    fasta_handle = open(FASTA_OUT, "a")
    n_fetched = n_failed = 0

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        try:
            handle = Entrez.efetch(db="nucleotide", id=",".join(batch),
                                    rettype="fasta", retmode="text")
            text = handle.read()
            handle.close()

            for record in SeqIO.parse(StringIO(text), "fasta"):
                acc_id = record.id
                acc_base = acc_id.split(".")[0]
                # Find original accession (with or without version)
                orig_acc = None
                for acc in batch:
                    if acc == acc_id or acc == acc_base or acc.split(".")[0] == acc_base:
                        orig_acc = acc
                        break
                if orig_acc is None:
                    orig_acc = acc_id

                org_id = acc_to_orgid.get(orig_acc, 0)
                species = species_map.get(org_id, "unknown")
                safe_species = species.replace(" ", "_").replace("|", "_")

                fasta_handle.write(f">{orig_acc}|{org_id}|{safe_species}\n")
                fasta_handle.write(str(record.seq) + "\n")
                n_fetched += 1
        except Exception as e:
            print(f"  Batch {i//BATCH_SIZE + 1}: FAILED ({e})")
            n_failed += len(batch)

        if (i // BATCH_SIZE + 1) % 5 == 0 or i + BATCH_SIZE >= len(remaining):
            print(f"  Batch {i//BATCH_SIZE + 1}/"
                  f"{(len(remaining) + BATCH_SIZE - 1)//BATCH_SIZE}: "
                  f"{n_fetched} fetched, {n_failed} failed")
            fasta_handle.flush()

        time.sleep(SLEEP)

    fasta_handle.close()
    print(f"\nDone. {n_fetched} new sequences appended -> {FASTA_OUT}")


if __name__ == "__main__":
    main()
