"""Phase 1.5m conflict scanner.

For every accession listed in fetch_markers.sh, fetch the UniProt entry,
parse organism, and flag any reference that comes from a species in the
26-organism dev+blind exclusion list.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FETCH_SH = ROOT / "fetch_markers.sh"

# Lower-cased, with synonyms. Match is "any token of the canonical organism name
# substring-matches the UniProt OS line, considering only species-binomial first two words".
EXCLUDED_SPECIES = [
    # 18 dev set
    ("Escherichia", "coli"),
    ("Nitratidesulfovibrio", "vulgaris"),
    ("Desulfovibrio", "vulgaris"),  # synonym
    ("Methanocaldococcus", "jannaschii"),
    ("Methanococcus", "jannaschii"),  # synonym
    ("Thermus", "aquaticus"),
    ("Lactobacillus", "plantarum"),
    ("Acidithiobacillus", "ferrooxidans"),
    ("Clostridium", "acetobutylicum"),
    ("Geobacter", "sulfurreducens"),
    ("Sulfolobus", "acidocaldarius"),
    ("Campylobacter", "jejuni"),
    ("Magnetospirillum", "magneticum"),
    ("Sulfurimonas", "denitrificans"),
    ("Nitrosomonas", "europaea"),
    ("Rhodopseudomonas", "palustris"),
    ("Halobacterium", "salinarum"),
    ("Syntrophomonas", "wolfei"),
    ("Acetobacterium", "woodii"),
    ("Allochromatium", "vinosum"),
    ("Chromatium", "vinosum"),  # synonym
    # 8 blind set
    ("Methanoperedens", "nitroreducens"),
    ("Prometheoarchaeum", "syntrophicum"),
    ("Scalindua", "profunda"),
    ("Chloroflexus", "aurantiacus"),
    ("Dehalococcoides", "mccartyi"),
    ("Nitrospira", "moscoviensis"),
    ("Picrophilus", "torridus"),
    ("Thermotoga", "maritima"),
]


def parse_fetch_sh(text: str) -> list[tuple[str, list[str]]]:
    """Return list of (marker_name, [accessions]) tuples."""
    out = []
    cur_name = None
    cur_acc: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"build_ref\s+(\S+)\s*\\?", s)
        if m:
            if cur_name is not None:
                out.append((cur_name, cur_acc))
            cur_name = m.group(1)
            cur_acc = []
            # also accept inline accessions on same line
            tail = s[m.end():].strip()
            for tok in re.split(r"\s+", tail):
                tok = tok.rstrip("\\")
                if tok and re.match(r"^[A-Z][A-Z0-9]{5,9}$", tok):
                    cur_acc.append(tok)
            continue
        if cur_name is None:
            continue
        if s.startswith("#") or s == "":
            continue
        m_acc = re.match(r"^([A-Z][A-Z0-9]{5,9})\s*\\?\s*(?:#.*)?$", s)
        if m_acc:
            cur_acc.append(m_acc.group(1))
            continue
        # End of build_ref block? heuristic: blank or non-acc line after we have accs
        if cur_acc and not s.endswith("\\"):
            out.append((cur_name, cur_acc))
            cur_name = None
            cur_acc = []
    if cur_name is not None and cur_acc:
        out.append((cur_name, cur_acc))
    return out


def fetch_organism(acc: str) -> tuple[str, str, str]:
    """Return (status, organism, gene_name) for an accession."""
    try:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "20",
             f"https://rest.uniprot.org/uniprotkb/{acc}.txt"],
            capture_output=True, text=True, timeout=30
        )
    except Exception as e:
        return ("FETCH_FAIL", str(e), "")
    text = r.stdout
    if not text.strip():
        return ("EMPTY", "", "")
    status = "Reviewed" if " Reviewed;" in text else "Unreviewed"
    # OS line — first only
    m_os = re.search(r"^OS   (.+?)$", text, re.MULTILINE)
    organism = m_os.group(1).strip().rstrip(".").rstrip(" ") if m_os else "?"
    # remove parenthetical strain info
    organism = re.sub(r"\s*\(.*?\)\s*$", "", organism).strip()
    # GN
    m_gn = re.search(r"^GN   Name=([^;\s]+)", text, re.MULTILINE)
    gene = m_gn.group(1).rstrip(";") if m_gn else "?"
    # protein name
    m_de = re.search(r"^DE   RecName: Full=([^;{]+)", text, re.MULTILINE)
    if m_de is None:
        m_de = re.search(r"^DE   SubName: Full=([^;{]+)", text, re.MULTILINE)
    protein = m_de.group(1).strip() if m_de else "?"
    return (status, organism, f"{gene}|{protein}")


def is_excluded(organism: str) -> bool:
    org_low = organism.lower()
    for genus, species in EXCLUDED_SPECIES:
        if genus.lower() in org_low and species.lower() in org_low:
            return True
    return False


def main() -> int:
    text = FETCH_SH.read_text()
    blocks = parse_fetch_sh(text)
    total_accessions = sum(len(a) for _, a in blocks)
    print(f"Found {len(blocks)} markers, {total_accessions} total accessions.\n")

    flagged: dict[str, list[tuple[str, str]]] = {}
    for marker, accs in blocks:
        for acc in accs:
            status, organism, info = fetch_organism(acc)
            excluded = is_excluded(organism)
            tag = "❌ EXCLUDED" if excluded else " ok"
            print(f"  [{marker:18s}] {acc:12s} {status:11s} {tag}  | {organism} | {info}")
            if excluded:
                flagged.setdefault(marker, []).append((acc, organism))

    print()
    print("=" * 70)
    print("CONFLICT SUMMARY")
    print("=" * 70)
    if not flagged:
        print("No conflicts — all references are outside the dev+blind exclusion list.")
    else:
        for marker, conflicts in flagged.items():
            print(f"\n{marker}:")
            for acc, org in conflicts:
                print(f"  - {acc}  →  {org}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
