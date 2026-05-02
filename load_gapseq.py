"""Load gapseq output into the CultureForge database.

Adds tables:
  - genomes               : per-genome metadata
  - genome_pathways       : pathway predictions from `gapseq find -p all`
  - genome_transporters   : transporter predictions from `gapseq find-transport`
  - essential_compounds   : reference list of biomass-essential compounds and the
                            biosynthesis-pathway name patterns that produce them

Adds view:
  - genome_auxotrophies   : derived view — for each genome × essential compound
                            with NO complete biosynthesis pathway, emit a row.
                            "Empty result for a genome" == "true prototroph".

Then loads the E. coli K-12 MG1655 gapseq run, linking it to organism id=4414
(DSM 498 = E. coli K-12 W3110, sister K-12 strain).

Usage:
    python load_gapseq.py
"""

import csv
import os
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

import confidence

_ROOT = Path(__file__).parent

DB = str(_ROOT / "data" / "cultureforge.db")
GAPSEQ_DIR = str(_ROOT / "data" / "gapseq" / "ecoli")
GENOME_FASTA = str(_ROOT / "data" / "genomes" / "ecoli_k12_mg1655.fasta")
ORGANISM_ID = 4414  # E. coli DSM 498 (K-12 W3110, closest BacDive entry to MG1655)


# ---------------------------------------------------------------- schema setup

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS genomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organism_id INTEGER,                    -- nullable: MAGs may not have one
    accession TEXT NOT NULL,                -- NCBI accession or MAG id
    source TEXT,                            -- NCBI / IMG / MAG / etc.
    file_path TEXT,
    length_bp INTEGER,
    biomass_template TEXT,                  -- gapseq: Gram_pos / Gram_neg / Archaea
    n_unique_genes INTEGER,
    completeness_pct REAL,                  -- CheckM, optional
    contamination_pct REAL,                 -- CheckM, optional
    gapseq_version TEXT,
    gapseq_run_date TEXT,
    notes TEXT,
    FOREIGN KEY (organism_id) REFERENCES organisms(id),
    UNIQUE (accession)
);

CREATE TABLE IF NOT EXISTS genome_pathways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    pathway_id TEXT NOT NULL,
    pathway_name TEXT,
    predicted INTEGER NOT NULL,             -- 0 / 1
    completeness REAL,                      -- 0-100
    n_key_reactions INTEGER,
    n_key_reactions_found INTEGER,
    n_reactions_found INTEGER,
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, pathway_id)
);

CREATE TABLE IF NOT EXISTS genome_transporters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    tc_id TEXT,                             -- TC classification, e.g. 1.A.1.13.1
    substrate TEXT NOT NULL,                -- e.g. "potassium"
    exchange_id TEXT,                       -- e.g. "EX_cpd00205_e0"
    reaction_ids TEXT,                      -- comma-list (gapseq emits multi)
    query_seqid TEXT,
    pident REAL,
    evalue REAL,
    bitscore REAL,
    FOREIGN KEY (genome_id) REFERENCES genomes(id)
);

CREATE TABLE IF NOT EXISTS essential_compounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- e.g. "L-arginine"
    compound_class TEXT NOT NULL,           -- amino_acid / vitamin / cofactor / nucleotide
    pathway_name_pattern TEXT NOT NULL,     -- LIKE pattern matching pathway_name
    notes TEXT
);

CREATE TABLE IF NOT EXISTS genome_reaction_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL,
    marker TEXT NOT NULL,          -- e.g. bd_oxidase, bo3_oxidase, catalase, hao
    n_good_blast INTEGER DEFAULT 0,
    best_bitscore REAL DEFAULT 0,
    complex_complete INTEGER DEFAULT 0,  -- 1 if complex.status == '1'
    FOREIGN KEY (genome_id) REFERENCES genomes(id),
    UNIQUE (genome_id, marker)
);

CREATE INDEX IF NOT EXISTS idx_gp_genome   ON genome_pathways(genome_id);
CREATE INDEX IF NOT EXISTS idx_gp_predicted ON genome_pathways(predicted);
CREATE INDEX IF NOT EXISTS idx_gp_name     ON genome_pathways(pathway_name);
CREATE INDEX IF NOT EXISTS idx_gt_genome   ON genome_transporters(genome_id);
CREATE INDEX IF NOT EXISTS idx_gt_substrate ON genome_transporters(substrate);
CREATE INDEX IF NOT EXISTS idx_grm_genome  ON genome_reaction_markers(genome_id);

DROP VIEW IF EXISTS genome_auxotrophies;
-- An organism is auxotrophic for a compound if NONE of the biosynthesis
-- pathways that produce it are functional. We accept a pathway as functional
-- if EITHER:
--   (a) gapseq's strict Prediction flag is true (key enzymes present), OR
--   (b) completeness >= 75%  -- catches pathways missing only a non-key step,
--       which is the threshold gapseq uses internally for "added because of
--       completeness threshold" decisions.
CREATE VIEW genome_auxotrophies AS
WITH compound_status AS (
    SELECT g.id            AS genome_id,
           ec.id           AS essential_compound_id,
           ec.name         AS compound_name,
           ec.compound_class,
           MAX(CASE WHEN gp.predicted = 1
                          OR gp.completeness >= 75
                    THEN 1 ELSE 0 END)              AS has_functional_pathway,
           MAX(COALESCE(gp.completeness, 0))         AS best_completeness,
           COUNT(gp.id)                              AS n_pathway_variants_found
      FROM genomes g
      CROSS JOIN essential_compounds ec
      LEFT JOIN genome_pathways gp
        ON gp.genome_id = g.id
       AND lower(gp.pathway_name) LIKE lower(ec.pathway_name_pattern)
       AND lower(gp.pathway_name) LIKE '%biosynthesis%'
     GROUP BY g.id, ec.id
)
SELECT genome_id,
       essential_compound_id,
       compound_name,
       compound_class,
       best_completeness,
       n_pathway_variants_found
  FROM compound_status
 WHERE has_functional_pathway = 0;
"""


# --- The 20 standard amino acids + key vitamins/cofactors that, if absent,
#     mean the organism is auxotrophic and the medium must supply them.
# Patterns are matched against the ENTIRE pathway_name with LIKE.
# We anchor to "<compound> biosynthesis%" (no leading %) so that
# pathways merely *mentioning* the compound (e.g.
# "UDP-N-acetylmuramoyl-pentapeptide biosynthesis II (lysine-containing)"
# or "L-pyrrolysine biosynthesis" or "glycine betaine biosynthesis")
# are not falsely counted as biosynthesis routes for the target compound.
ESSENTIAL_COMPOUNDS = [
    # 20 amino acids — "<L-aa> biosynthesis..."
    ("L-alanine",       "amino_acid", "L-alanine biosynthesis%"),
    ("L-arginine",      "amino_acid", "L-arginine biosynthesis%"),
    ("L-asparagine",    "amino_acid", "L-asparagine biosynthesis%"),
    ("L-aspartate",     "amino_acid", "L-aspartate biosynthesis%"),
    ("L-cysteine",      "amino_acid", "L-cysteine biosynthesis%"),
    ("L-glutamate",     "amino_acid", "L-glutamate biosynthesis%"),
    ("L-glutamine",     "amino_acid", "L-glutamine biosynthesis%"),
    ("glycine",         "amino_acid", "glycine biosynthesis%"),
    ("L-histidine",     "amino_acid", "L-histidine biosynthesis%"),
    ("L-isoleucine",    "amino_acid", "L-isoleucine biosynthesis%"),
    ("L-leucine",       "amino_acid", "L-leucine biosynthesis%"),
    ("L-lysine",        "amino_acid", "L-lysine biosynthesis%"),
    ("L-methionine",    "amino_acid", "L-methionine biosynthesis%"),
    ("L-phenylalanine", "amino_acid", "L-phenylalanine biosynthesis%"),
    ("L-proline",       "amino_acid", "L-proline biosynthesis%"),
    ("L-serine",        "amino_acid", "L-serine biosynthesis%"),
    ("L-threonine",     "amino_acid", "L-threonine biosynthesis%"),
    ("L-tryptophan",    "amino_acid", "L-tryptophan biosynthesis%"),
    ("L-tyrosine",      "amino_acid", "L-tyrosine biosynthesis%"),
    ("L-valine",        "amino_acid", "L-valine biosynthesis%"),
    # Vitamins / cofactors — anchored to the cofactor name + biosynthesis
    ("biotin (B7)",       "vitamin",  "biotin biosynthesis%"),
    ("folate (B9)",       "vitamin",  "tetrahydrofolate biosynthesis%"),
    ("thiamin (B1)",      "vitamin",  "thiamin%biosynthesis%"),     # "thiamin diphosphate biosynthesis I" etc.
    # gapseq names "flavin biosynthesis I (bacteria and plants)" with no "ribo" prefix
    ("riboflavin (B2)",   "vitamin",  "flavin biosynthesis%"),
    # gapseq: "phosphopantothenate biosynthesis I" — phospho-form of B5; accept either name
    ("pantothenate (B5)", "vitamin",  "%pantothenate biosynthesis%"),
    ("pyridoxal-5P (B6)", "vitamin",  "pyridoxal 5'-phosphate biosynthesis%"),
    ("cobalamin (B12)",   "vitamin",  "%cobalamin biosynthesis%"),  # "adenosylcobalamin biosynthesis…"
    # Niacin (B3): non-auxotrophic if either de novo NAD biosynthesis
    # ("NAD de novo biosynthesis I", "NAD biosynthesis from nicotinamide") works
    ("niacin (B3)",       "vitamin",  "NAD%biosynthesis%"),
    # Cofactors — heme has prenylated/sirohaem variants; anchor where possible
    ("heme",              "cofactor", "heme%biosynthesis%"),
    ("siroheme",          "cofactor", "siroheme biosynthesis%"),
    ("molybdopterin",     "cofactor", "molybdopterin biosynthesis%"),
    # NAD listed under cofactor as well (different from niacin label, same pattern)
    ("NAD",               "cofactor", "NAD%biosynthesis%"),
]


# ---------------------------------------------------------------- file readers

def parse_tsv_with_comments(path):
    """Read a TSV that may have leading '#'-prefixed comment lines."""
    with open(path) as f:
        rows = []
        header = None
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if header is None:
                header = fields
                continue
            rows.append(dict(zip(header, fields)))
    return header, rows


def get_gapseq_version_from_file(path):
    """Pluck the version line from a gapseq TSV header."""
    with open(path) as f:
        for line in f:
            if line.startswith("# gapseq version:"):
                return line.split(":", 1)[1].strip()
            if not line.startswith("#"):
                break
    return None


def get_genome_length(fasta_path):
    n = 0
    with open(fasta_path) as f:
        for line in f:
            if line.startswith(">"):
                continue
            n += len(line.strip())
    return n


# ---------------------------------------------------------------- loaders

def insert_genome(conn, organism_id, accession, source, file_path, biomass,
                  n_genes, gapseq_version, notes=None):
    """Insert (or refresh) a genome row. To keep the load idempotent without
    orphaning pathways/transporters, we explicitly clean up any prior data
    for the same accession before inserting."""
    length_bp = get_genome_length(file_path) if os.path.exists(file_path) else None

    existing = conn.execute(
        "SELECT id FROM genomes WHERE accession=?", (accession,)
    ).fetchone()
    if existing:
        old_id = existing[0]
        conn.execute("DELETE FROM genome_pathways      WHERE genome_id=?", (old_id,))
        conn.execute("DELETE FROM genome_transporters  WHERE genome_id=?", (old_id,))
        # Also drop any prior confidence records pointing to this genome's
        # pathways/transporters so re-loading doesn't accumulate stale rows.
        conn.execute(
            "DELETE FROM prediction_confidences "
            "WHERE related_table='genome_pathways' AND related_id IN "
            "  (SELECT id FROM genome_pathways WHERE genome_id=?)",
            (old_id,))
        conn.execute(
            "DELETE FROM prediction_confidences "
            "WHERE related_table='genome_transporters' AND related_id IN "
            "  (SELECT id FROM genome_transporters WHERE genome_id=?)",
            (old_id,))
        conn.execute("DELETE FROM genomes              WHERE id=?",        (old_id,))

    conn.execute("""
        INSERT INTO genomes
            (organism_id, accession, source, file_path, length_bp,
             biomass_template, n_unique_genes,
             gapseq_version, gapseq_run_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (organism_id, accession, source, file_path, length_bp,
          biomass, n_genes, gapseq_version, str(date.today()), notes))
    return conn.execute(
        "SELECT id FROM genomes WHERE accession=?", (accession,)
    ).fetchone()[0]


def load_pathways(conn, genome_id, path):
    header, rows = parse_tsv_with_comments(path)
    n_inserted = 0
    n_predicted = 0
    n_conf = 0
    # Clear any prior load for this genome to keep the loader idempotent
    conn.execute("DELETE FROM genome_pathways WHERE genome_id=?", (genome_id,))
    for r in rows:
        pid = (r.get("ID") or "").strip("|")
        if not pid:
            continue
        predicted = 1 if r.get("Prediction", "").lower() == "true" else 0
        try:
            comp = float(r.get("Completeness") or 0)
        except ValueError:
            comp = 0.0
        try:
            n_key = int(r.get("KeyReactions") or 0)
        except ValueError:
            n_key = 0
        try:
            n_key_found = int(r.get("KeyReactionsFound") or 0)
        except ValueError:
            n_key_found = 0
        # ReactionsFound is a space-separated list of reaction IDs in the TSV
        rxns = (r.get("ReactionsFound") or "").split()
        conn.execute("""
            INSERT INTO genome_pathways
                (genome_id, pathway_id, pathway_name, predicted, completeness,
                 n_key_reactions, n_key_reactions_found, n_reactions_found)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (genome_id, pid, r.get("Name"), predicted, comp,
              n_key, n_key_found, len(rxns)))
        new_pwy_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        n_inserted += 1
        n_predicted += predicted

        # Record per-pathway confidence so it's queryable downstream.
        # We score every pathway (predicted and not) so the auxotrophy view
        # can later ask "how confident are we that this pathway is missing?"
        conf = confidence.score(
            "gapseq", "pathway_completeness", comp,
            context={
                "raw_value": comp,
                "predicted": bool(predicted),
                "pathway_id": pid,
                "n_key_reactions": n_key,
                "n_key_reactions_found": n_key_found,
                "n_reactions_found": len(rxns),
            },
        )
        confidence.record(conn, "pathway", conf,
                          related_table="genome_pathways",
                          related_id=new_pwy_id)
        n_conf += 1
    conn.commit()
    return n_inserted, n_predicted, n_conf


def load_transporters(conn, genome_id, path):
    header, rows = parse_tsv_with_comments(path)
    n_inserted = 0
    n_conf = 0
    conn.execute("DELETE FROM genome_transporters WHERE genome_id=?", (genome_id,))
    for r in rows:
        sub = (r.get("sub") or "").strip()
        if not sub:
            continue
        try:
            pident = float(r.get("pident") or 0) or None
        except ValueError:
            pident = None
        try:
            evalue = float(r.get("evalue") or 0) or None
        except ValueError:
            evalue = None
        try:
            bitscore = float(r.get("bitscore") or 0) or None
        except ValueError:
            bitscore = None
        conn.execute("""
            INSERT INTO genome_transporters
                (genome_id, tc_id, substrate, exchange_id, reaction_ids,
                 query_seqid, pident, evalue, bitscore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (genome_id, r.get("tc"), sub, r.get("exid"), r.get("rea"),
              r.get("qseqid"), pident, evalue, bitscore))
        new_trn_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        n_inserted += 1

        # Per-transporter confidence (BLAST-evidence based)
        conf = confidence.score(
            "gapseq", "transporter_bitscore",
            bitscore if bitscore is not None else 0,
            context={
                "raw_value": bitscore,
                "pident": pident,
                "evalue": evalue,
                "substrate": sub,
                "tc_id": r.get("tc"),
            },
        )
        confidence.record(conn, "transporter", conf,
                          related_table="genome_transporters",
                          related_id=new_trn_id)
        n_conf += 1
    conn.commit()
    return n_inserted, n_conf


# Reaction IDs and names that map to each marker
REACTION_MARKER_DEFS = {
    "bd_oxidase":   {"rxn": "RXN0-5266", "label": "cytochrome bd-I ubiquinol oxidase (high-affinity)"},
    "bo3_oxidase":  {"rxn": "RXN0-5268", "label": "cytochrome bo3 terminal oxidase (low-affinity)"},
    "cytc_oxidase": {"rxn": "CYTOCHROME-C-OXIDASE-RXN", "label": "cytochrome c oxidase"},
    "catalase":     {"rxn": "CATAL-RXN", "label": "catalase"},
    "hao":          {"rxn": "HAONITRO-RXN", "label": "hydroxylamine oxidoreductase"},
}


def load_reaction_markers(conn, genome_id, reactions_path):
    """Extract key reaction markers (terminal oxidases, catalase, hao) from
    the gapseq all-Reactions.tbl file and store them in genome_reaction_markers.

    This is a general-purpose function: it scans the reaction table for
    predefined reaction IDs and counts good_blast hits per marker.
    """
    header, rows = parse_tsv_with_comments(reactions_path)
    if not rows:
        return 0

    # Aggregate per marker: count good_blast, track best bitscore, complex_complete
    stats = {}
    for marker, spec in REACTION_MARKER_DEFS.items():
        stats[marker] = {"n_good": 0, "best_bs": 0.0, "complex_complete": False}

    for r in rows:
        rxn = r.get("rxn", "")
        status = r.get("status", "")
        for marker, spec in REACTION_MARKER_DEFS.items():
            if rxn != spec["rxn"]:
                continue
            if status == "good_blast":
                stats[marker]["n_good"] += 1
                try:
                    bs = float(r.get("bitscore") or 0)
                    if bs > stats[marker]["best_bs"]:
                        stats[marker]["best_bs"] = bs
                except (ValueError, TypeError):
                    pass
            cs = r.get("complex.status", "")
            if cs == "1":
                stats[marker]["complex_complete"] = True

    # Also detect cbb3 (high-affinity cytochrome c oxidase) as a sub-marker
    # by looking for "Cbb3" in the name field of CYTOCHROME-C-OXIDASE-RXN rows
    stats["cbb3_oxidase"] = {"n_good": 0, "best_bs": 0.0, "complex_complete": False}
    for r in rows:
        if r.get("rxn") != "CYTOCHROME-C-OXIDASE-RXN":
            continue
        name = r.get("name", "")
        if "Cbb3" not in name and "cbb3" not in name:
            continue
        if r.get("status") == "good_blast":
            stats["cbb3_oxidase"]["n_good"] += 1
            try:
                bs = float(r.get("bitscore") or 0)
                if bs > stats["cbb3_oxidase"]["best_bs"]:
                    stats["cbb3_oxidase"]["best_bs"] = bs
            except (ValueError, TypeError):
                pass
        if r.get("complex.status") == "1":
            stats["cbb3_oxidase"]["complex_complete"] = True

    # Also detect ammonia monooxygenase (amoABC) reactions
    stats["amo"] = {"n_good": 0, "best_bs": 0.0, "complex_complete": False}
    for r in rows:
        name = (r.get("name") or "").lower()
        if "ammonia monooxygenase" in name or "ammonia oxidation" in name:
            if r.get("status") == "good_blast":
                stats["amo"]["n_good"] += 1
                try:
                    bs = float(r.get("bitscore") or 0)
                    if bs > stats["amo"]["best_bs"]:
                        stats["amo"]["best_bs"] = bs
                except (ValueError, TypeError):
                    pass
            if r.get("complex.status") == "1":
                stats["amo"]["complex_complete"] = True

    # Also count TCA cycle best completeness from the pathways table
    # (already available via genome_pathways; this is just the reaction side)

    conn.execute("DELETE FROM genome_reaction_markers WHERE genome_id=?", (genome_id,))
    n = 0
    for marker, s in stats.items():
        conn.execute("""
            INSERT INTO genome_reaction_markers
              (genome_id, marker, n_good_blast, best_bitscore, complex_complete)
            VALUES (?, ?, ?, ?, ?)
        """, (genome_id, marker, s["n_good"], s["best_bs"],
              1 if s["complex_complete"] else 0))
        n += 1
    conn.commit()
    return n


def populate_essential_compounds(conn):
    """Refresh the essential_compounds reference table on every run so pattern
    edits take effect."""
    conn.execute("DELETE FROM essential_compounds")
    conn.executemany(
        "INSERT INTO essential_compounds (name, compound_class, pathway_name_pattern) "
        "VALUES (?, ?, ?)",
        ESSENTIAL_COMPOUNDS,
    )
    conn.commit()


# ---------------------------------------------------------------- test query

TEST_QUERY = """
SELECT o.species,
       o.ccno,
       g.accession           AS genome_accession,
       ga.compound_name      AS needs_compound,
       ga.compound_class,
       ga.best_completeness  AS best_pathway_completeness_pct,
       ga.n_pathway_variants_found
  FROM organisms o
  JOIN genomes   g  ON g.organism_id = o.id
  LEFT JOIN genome_auxotrophies ga ON ga.genome_id = g.id
 WHERE o.id = ?
 ORDER BY ga.compound_class, ga.compound_name;
"""


def main():
    if not os.path.exists(DB):
        sys.exit(f"Database {DB} not found.")
    if not os.path.isdir(GAPSEQ_DIR):
        sys.exit(f"Gapseq output dir {GAPSEQ_DIR} not found.")

    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA_SQL)
    # Ensure source_confidence + prediction_confidences tables exist before
    # we record any per-pathway / per-transporter scores.
    confidence.populate_source_table(conn)
    print("Schema ready (genomes, genome_pathways, genome_transporters, "
          "essential_compounds, view: genome_auxotrophies, "
          "source_confidence, prediction_confidences)")

    populate_essential_compounds(conn)
    n_essential = conn.execute("SELECT COUNT(*) FROM essential_compounds").fetchone()[0]
    print(f"  essential_compounds: {n_essential} entries")

    pathways_path     = os.path.join(GAPSEQ_DIR, "ecoli_k12_mg1655-all-Pathways.tbl")
    transporters_path = os.path.join(GAPSEQ_DIR, "ecoli_k12_mg1655-Transporter.tbl")
    gapseq_version    = get_gapseq_version_from_file(pathways_path)

    # Pull n_unique_genes out of the gapseq logs / draft for this genome.
    # Easier: re-derive from the rxnXgenes.RDS by counting via R, but we
    # captured "1464 unique genes" in the prior run; hard-code as a hint.
    # Better approach: parse the SBML draft for fbc:geneProduct count.
    n_genes = None
    draft_xml = os.path.join(GAPSEQ_DIR, "ecoli_k12_mg1655-draft.xml")
    if os.path.exists(draft_xml):
        with open(draft_xml) as f:
            xml = f.read()
        n_genes = xml.count("<fbc:geneProduct ")

    genome_id = insert_genome(
        conn,
        organism_id=ORGANISM_ID,
        accession="NC_000913.3",
        source="NCBI RefSeq",
        file_path=GENOME_FASTA,
        biomass="Gram_neg",
        n_genes=n_genes,
        gapseq_version=gapseq_version,
        notes=("Linked to BacDive DSM 498 (E. coli K-12 W3110) — sister K-12 "
               "strain to MG1655; both share >99.9% genome identity."),
    )
    print(f"  genome inserted: id={genome_id}, accession=NC_000913.3, "
          f"biomass=Gram_neg, gapseq={gapseq_version}, genes={n_genes}")

    n_pwy, n_pred, n_pwy_conf = load_pathways(conn, genome_id, pathways_path)
    print(f"  pathways loaded: {n_pwy} ({n_pred} predicted PRESENT, "
          f"{n_pwy_conf} confidence records)")

    n_trn, n_trn_conf = load_transporters(conn, genome_id, transporters_path)
    print(f"  transporters loaded: {n_trn} ({n_trn_conf} confidence records)")

    # Verbose test query (only when --verbose is passed)
    if "--verbose" in sys.argv:
        print()
        print("=" * 78)
        print("TEST QUERY: organisms -> genomes -> auxotrophies for organism_id=4414")
        print("=" * 78)
        rows = conn.execute(TEST_QUERY, (ORGANISM_ID,)).fetchall()
        needs = [r for r in rows if r[3] is not None]
        if not needs:
            print(f"\n  {rows[0][0]} ({rows[0][1]}, genome {rows[0][2]}):")
            print(f"    PROTOTROPH — synthesises every essential compound.")
        else:
            print(f"\n  {rows[0][0]} ({rows[0][1]}, genome {rows[0][2]}) needs:")
            for r in needs:
                print(f"    [{r[4]:11s}]  {r[3]:25s}  "
                      f"best={r[5] or 0:>5.1f}% ({r[6] or 0} variants)")
        summary = conn.execute("""
            SELECT compound_class, COUNT(*) AS n_missing
              FROM genome_auxotrophies WHERE genome_id = ?
            GROUP BY compound_class
        """, (genome_id,)).fetchall()
        if summary:
            for cls, n in summary:
                print(f"  {cls:12s}: {n} missing")
        else:
            print("  All compound classes covered — true prototroph.")

    conn.close()
    print(f"\nDone. Database: {DB}")


if __name__ == "__main__":
    main()
