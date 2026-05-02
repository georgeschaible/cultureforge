"""Load gapseq/GenomeSPOT/MeBiPred results for all 10 validation organisms,
register each in the database, and run the synthesizer to produce recipes.

Each organism gets:
  1. A genome row in the genomes table
  2. gapseq pathways/transporters loaded
  3. GenomeSPOT predictions loaded
  4. MeBiPred metal profile loaded
  5. Hydrogenase BLAST results loaded
  6. Carbon source profile computed
  7. Full synthesizer run with appropriate --energy-metabolism and --temperature
  8. Output saved to data/validation/<name>_validation.txt

Usage:
    python run_validation_synthesize.py [organism_name]

If organism_name is given, process only that one. Otherwise process all.
"""

import csv
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Ensure we can import project modules
sys.path.insert(0, str(Path(__file__).parent))

import confidence
import carbon_and_gas
from load_gapseq import (
    load_pathways, load_transporters, load_reaction_markers,
    populate_essential_compounds,
    get_gapseq_version_from_file, SCHEMA_SQL as GAPSEQ_SCHEMA,
)
from load_genomespot import load as load_genomespot_data, SCHEMA_SQL as GS_SCHEMA
from load_mebipred import load as load_mebipred_data, SCHEMA_SQL as MB_SCHEMA

_ROOT = Path(__file__).parent
DB = str(_ROOT / "data" / "cultureforge.db")


# Organism definitions: name, accession, temperature, energy_metabolism,
# organism_id (from BacDive/MediaDive if exists, None if not)
ORGANISMS = [
    {
        "name": "Thermus_aquaticus",
        "accession": "NC_006461.1",
        "temperature": 70,
        "energy_metabolism": None,
        "domain": "Bacteria",
        "biomass": "Gram_neg",
    },
    {
        "name": "Methanococcus_jannaschii",
        "accession": "NC_000909.1",
        "temperature": 85,
        "energy_metabolism": "methanogenesis",
        "domain": "Archaea",
        "biomass": "Archaea",
    },
    {
        "name": "Lactobacillus_plantarum",
        "accession": "NC_004567.2",
        "temperature": 37,
        "energy_metabolism": None,
        "domain": "Bacteria",
        "biomass": "Gram_pos",
    },
    {
        "name": "Acidithiobacillus_ferrooxidans",
        "accession": "NC_011761.1",
        "temperature": 30,
        "energy_metabolism": "sulfur-oxidation",
        "domain": "Bacteria",
        "biomass": "Gram_neg",
        "ph": 2.0,
    },
    {
        "name": "Clostridium_acetobutylicum",
        "accession": "NC_003030.1",
        "temperature": 37,
        "energy_metabolism": None,
        "domain": "Bacteria",
        "biomass": "Gram_pos",
    },
    {
        "name": "Geobacter_sulfurreducens",
        "accession": "NC_002939.5",
        "temperature": 30,
        "energy_metabolism": "iron-reduction",
        "domain": "Bacteria",
        "biomass": "Gram_neg",
    },
    {
        "name": "Sulfolobus_acidocaldarius",
        "accession": "NC_007181.1",
        "temperature": 75,
        "energy_metabolism": "sulfur-oxidation",
        "domain": "Archaea",
        "biomass": "Archaea",
        "ph": 2.5,
    },
    {
        "name": "Campylobacter_jejuni",
        "accession": "NC_002163.1",
        "temperature": 42,
        "energy_metabolism": None,
        "domain": "Bacteria",
        "biomass": "Gram_neg",
    },
    {
        "name": "Magnetospirillum_magneticum",
        "accession": "NC_007626.1",
        "temperature": 30,
        "energy_metabolism": None,
        "domain": "Bacteria",
        "biomass": "Gram_neg",
    },
    {
        "name": "Sulfurimonas_denitrificans",
        "accession": "NC_009663.1",
        "temperature": 25,
        "energy_metabolism": "sulfur-oxidation",
        "domain": "Bacteria",
        "biomass": "Gram_neg",
    },
]


def find_organism_id(conn, name):
    """Try to find a matching organism_id in our database."""
    species = name.replace("_", " ")
    row = conn.execute(
        "SELECT id FROM organisms WHERE species LIKE ? LIMIT 1",
        (f"%{species}%",)
    ).fetchone()
    return row[0] if row else None


def register_genome(conn, org):
    """Insert or update a genome row for this organism."""
    name = org["name"]
    acc = org["accession"]
    genome_fasta = str(_ROOT / "data" / "genomes" / f"{name}.fasta")

    existing = conn.execute("SELECT id FROM genomes WHERE accession=?", (acc,)).fetchone()
    if existing:
        return existing[0]

    org_id = find_organism_id(conn, name)

    # Get genome length
    bp = 0
    with open(genome_fasta) as f:
        for line in f:
            if not line.startswith(">"):
                bp += len(line.strip())

    # Get gapseq version if available
    gapseq_dir = _ROOT / "data" / "gapseq" / name
    pwy_file = list(gapseq_dir.glob("*-all-Pathways.tbl"))
    gv = None
    n_genes = None
    if pwy_file:
        gv = None
        with open(pwy_file[0]) as f:
            for line in f:
                if line.startswith("# gapseq version:"):
                    gv = line.split(":", 1)[1].strip()
                    break
        draft_xml = list(gapseq_dir.glob("*-draft.xml"))
        if draft_xml:
            with open(draft_xml[0]) as f:
                n_genes = f.read().count("<fbc:geneProduct ")

    conn.execute("""
        INSERT INTO genomes
          (organism_id, accession, source, file_path, length_bp,
           biomass_template, n_unique_genes, gapseq_version, notes)
        VALUES (?, ?, 'NCBI RefSeq', ?, ?, ?, ?, ?, ?)
    """, (org_id, acc, genome_fasta, bp, org.get("biomass"),
          n_genes, gv, f"Validation organism: {name}"))
    conn.commit()
    return conn.execute("SELECT id FROM genomes WHERE accession=?", (acc,)).fetchone()[0]


def load_all_data(conn, org, genome_id):
    """Load gapseq + GenomeSPOT + MeBiPred + hydrogenases for this organism."""
    name = org["name"]
    gapseq_dir = _ROOT / "data" / "gapseq" / name
    gs_dir = _ROOT / "data" / "genomespot" / name
    mb_dir = _ROOT / "data" / "mebipred" / name
    h_dir = _ROOT / "data" / "hydrogenase"

    loaded = []

    # gapseq
    pwy_files = list(gapseq_dir.glob("*-all-Pathways.tbl"))
    trn_files = list(gapseq_dir.glob("*-Transporter.tbl"))
    if pwy_files:
        conn.executescript(GAPSEQ_SCHEMA)
        confidence.populate_source_table(conn)
        populate_essential_compounds(conn)
        n_pwy, n_pred, n_conf = load_pathways(conn, genome_id, str(pwy_files[0]))
        loaded.append(f"gapseq pathways: {n_pwy} ({n_pred} predicted)")
    if trn_files:
        n_trn, n_tconf = load_transporters(conn, genome_id, str(trn_files[0]))
        loaded.append(f"transporters: {n_trn}")

    # Reaction markers (terminal oxidases, catalase, hao, amo)
    rxn_files = list(gapseq_dir.glob("*-all-Reactions.tbl"))
    if rxn_files:
        n_markers = load_reaction_markers(conn, genome_id, str(rxn_files[0]))
        loaded.append(f"reaction markers: {n_markers}")

    # GenomeSPOT
    gs_tsv = gs_dir / f"{name}.predictions.tsv"
    if gs_tsv.exists():
        conn.executescript(GS_SCHEMA)
        n = load_genomespot_data(conn, genome_id, str(gs_tsv))
        loaded.append(f"GenomeSPOT: {n} predictions")

    # MeBiPred
    mb_tsv = mb_dir / f"{name}_predictions.tsv"
    if mb_tsv.exists():
        conn.executescript(MB_SCHEMA)
        n_prot, n_bind, n_profile = load_mebipred_data(conn, genome_id, str(mb_tsv))
        loaded.append(f"MeBiPred: {n_prot} proteins, {n_profile} metal profile")

    # Hydrogenases
    h_tsv = h_dir / f"{name}_hits.tsv"
    if h_tsv.exists():
        carbon_and_gas.init_schema(conn)
        conn.execute("DELETE FROM genome_hydrogenases WHERE genome_id=?", (genome_id,))
        with open(h_tsv) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 6:
                    continue
                gene_id, ref_full = parts[0], parts[1]
                pident, evalue, bitscore = float(parts[2]), float(parts[4]), float(parts[5])
                ref_parts = ref_full.split("|")
                h_type = ref_parts[1] if len(ref_parts) > 1 else "?"
                group_str = ref_parts[2].replace("Group", "") if len(ref_parts) > 2 else "?"
                ref_acc = ref_parts[3] if len(ref_parts) > 3 else ""
                conf_val = min(0.95, max(0.50, 0.50 + (bitscore - 100) / 2000))
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO genome_hydrogenases
                          (genome_id, gene_id, hydrogenase_type, group_id,
                           reference_id, reference_acc, pident, evalue, bitscore, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (genome_id, gene_id, h_type, group_str, ref_parts[0], ref_acc,
                          pident, evalue, bitscore, conf_val))
                except Exception:
                    pass
        n_h = conn.execute("SELECT COUNT(*) FROM genome_hydrogenases WHERE genome_id=?",
                           (genome_id,)).fetchone()[0]
        loaded.append(f"hydrogenases: {n_h} hits")

    # Carbon sources
    carbon_and_gas.init_schema(conn)
    profile = carbon_and_gas.get_carbon_profile(conn, genome_id)
    conn.execute("DELETE FROM genome_carbon_sources WHERE genome_id=?", (genome_id,))
    for c_name, info in profile.items():
        conn.execute("""
            INSERT OR IGNORE INTO genome_carbon_sources
              (genome_id, carbon_source, evidence_type, evidence_pathway,
               max_completeness, confidence)
            VALUES (?, ?, 'gapseq_pathway', ?, ?, ?)
        """, (genome_id, c_name, info["pathways"][0], info["max_completeness"],
              info["confidence"].value))
    loaded.append(f"carbon sources: {len(profile)}")
    conn.commit()

    return loaded


def run_synthesizer(org, output_path):
    """Run synthesize_media.py and capture output."""
    name = org["name"]
    genome = str(_ROOT / "data" / "genomes" / f"{name}.fasta")
    acc = org["accession"]

    cmd = [
        sys.executable, str(_ROOT / "synthesize_media.py"),
        genome, "--accession", acc,
        "--temperature", str(org["temperature"]),
        "--top", "10", "--no-persist",
    ]
    if org.get("energy_metabolism"):
        cmd.extend(["--energy-metabolism", org["energy_metabolism"]])
    if org.get("ph"):
        cmd.extend(["--ph", str(org["ph"])])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr

    with open(output_path, "w") as f:
        f.write(f"{'='*80}\n")
        f.write(f"CULTUREFORGE VALIDATION: {name}\n")
        f.write(f"{'='*80}\n\n")
        f.write(output)

    return output


def main():
    target_name = sys.argv[1] if len(sys.argv) > 1 else None
    conn = sqlite3.connect(DB)

    try:
        for org in ORGANISMS:
            name = org["name"]
            if target_name and name != target_name:
                continue

            print(f"\n{'='*60}")
            print(f"  Processing: {name}")
            print(f"{'='*60}")

            # Check if gapseq data exists
            gapseq_dir = _ROOT / "data" / "gapseq" / name
            if not list(gapseq_dir.glob("*-all-Pathways.tbl")):
                print(f"  [SKIP] gapseq not complete yet for {name}")
                continue

            # Register genome
            genome_id = register_genome(conn, org)
            print(f"  genome_id = {genome_id}")

            # Load all data
            loaded = load_all_data(conn, org, genome_id)
            for l in loaded:
                print(f"  loaded: {l}")

            # Run synthesizer
            output_path = str(_ROOT / "data" / "validation" / f"{name}_validation.txt")
            print(f"  Running synthesizer...")
            output = run_synthesizer(org, output_path)

            # Extract key lines from output
            for line in output.split("\n"):
                if any(k in line for k in [
                    "Overall Confidence", "Headspace:", "Recommended:",
                    "VIABLE", "STRICT ANAER", "can utilize",
                    "Solidifying agent"
                ]):
                    print(f"    {line.strip()}")

            print(f"  Saved to: {output_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
