"""Load CheckM quality metrics into the CultureForge database.

Adds table: genome_quality

Usage:
    from load_checkm import load, SCHEMA_SQL
    conn.executescript(SCHEMA_SQL)
    load(conn, genome_id, checkm_result_dict)
"""

import sqlite3
from datetime import date

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS genome_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id INTEGER NOT NULL UNIQUE,
    completeness REAL,
    contamination REAL,
    strain_heterogeneity REAL,
    genome_size INTEGER,
    gc_content REAL,
    n50 INTEGER,
    acidic_residue_fraction REAL,
    checkm_version TEXT,
    run_date TEXT,
    FOREIGN KEY (genome_id) REFERENCES genomes(id)
);
"""


def load(conn: sqlite3.Connection, genome_id: int, result: dict) -> None:
    """Upsert genome quality metrics for a genome."""
    conn.execute(SCHEMA_SQL.replace("CREATE TABLE IF NOT EXISTS",
                                     "CREATE TABLE IF NOT EXISTS"))
    existing = conn.execute(
        "SELECT id FROM genome_quality WHERE genome_id = ?", (genome_id,)
    ).fetchone()

    if existing:
        conn.execute("""
            UPDATE genome_quality SET
                completeness = ?,
                contamination = ?,
                strain_heterogeneity = ?,
                genome_size = ?,
                gc_content = ?,
                n50 = ?,
                checkm_version = ?,
                run_date = ?
            WHERE genome_id = ?
        """, (
            result.get("completeness"),
            result.get("contamination"),
            result.get("strain_heterogeneity"),
            result.get("genome_size"),
            result.get("gc_content"),
            result.get("n50"),
            result.get("checkm_version"),
            str(date.today()),
            genome_id,
        ))
    else:
        conn.execute("""
            INSERT INTO genome_quality
                (genome_id, completeness, contamination, strain_heterogeneity,
                 genome_size, gc_content, n50, checkm_version, run_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            genome_id,
            result.get("completeness"),
            result.get("contamination"),
            result.get("strain_heterogeneity"),
            result.get("genome_size"),
            result.get("gc_content"),
            result.get("n50"),
            result.get("checkm_version"),
            str(date.today()),
        ))
    conn.commit()


def update_acidic_fraction(conn: sqlite3.Connection, genome_id: int,
                           fraction: float) -> None:
    """Update the acidic residue fraction for a genome."""
    conn.execute("""
        UPDATE genome_quality SET acidic_residue_fraction = ?
        WHERE genome_id = ?
    """, (fraction, genome_id))
    conn.commit()
