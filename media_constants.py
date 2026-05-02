"""Shared constants and reference tables for media synthesis.

Used by both the legacy template-based synthesizer (synthesize_media.py)
and the de novo synthesizer (synthesize_denovo.py).
"""

# Trace metal supplement concentrations per CLAUDE.md addendum 1
METAL_SUPPLEMENT = {
    "Fe": ("FeSO4·7H2O", 0.005, "g/L"),
    "Zn": ("ZnSO4·7H2O", 0.0005, "g/L"),
    "Mn": ("MnCl2·4H2O", 0.0005, "g/L"),
    "Cu": ("CuSO4·5H2O", 0.00005, "g/L"),
    "Co": ("CoCl2·6H2O", 0.00005, "g/L"),
    "Ni": ("NiCl2·6H2O", 0.00005, "g/L"),
    "Mg": ("MgSO4·7H2O", 0.5, "g/L"),
    "Ca": ("CaCl2·2H2O", 0.05, "g/L"),
    "K":  ("K2HPO4", 0.5, "g/L"),
    "Na": ("NaCl", 1.0, "g/L"),
}

# Cofactor-specific concentration overrides
COFACTOR_CONCENTRATION = {
    "heme":             0.005,   # g/L = 5 mg/L
    "siroheme":         0.001,
    "molybdopterin":    0.001,
    "NAD":              0.005,
    "biotin (B7)":      0.00002,  # 20 µg/L
    "folate (B9)":      0.001,
    "cobalamin (B12)":  0.0001,   # 100 µg/L
    "thiamin (B1)":     0.001,
    "riboflavin (B2)":  0.001,
    "pantothenate (B5)": 0.001,
    "pyridoxal-5P (B6)": 0.001,
    "niacin (B3)":      0.001,
}

# Amino acid supplement default
AA_SUPPLEMENT_CONC = 0.050  # g/L = 50 mg/L

# Autotrophy pathway patterns (CO2 fixation)
AUTOTROPHY_PATTERNS = [
    (r"Calvin-Benson-Bassham", "Calvin cycle (CBB)"),
    (r"reductive acetyl coenzyme A pathway", "Wood-Ljungdahl pathway"),
    (r"reductive citric acid cycle|reductive TCA", "reductive TCA cycle"),
    (r"3-hydroxypropionate", "3-HP bicycle"),
    (r"dicarboxylate.*hydroxybutyrate", "DC/4-HB cycle"),
]

# Metabolism-to-taxonomy proxies for concentration calibration
# NOTE: This proxy approach should eventually be replaced by direct
# metabolism tagging from pre-computed gapseq results on reference genomes.
# For now, taxonomy-based queries are an acceptable approximation because
# metabolic type correlates strongly with phylogeny for most major groups.
METABOLISM_TAXONOMY_PROXIES = {
    "sulfate_reducer":     ["%desulfo%", "%desulfur%", "%archaeoglobus%"],
    "methanogen":          ["%methano%"],
    "iron_reducer":        ["%geobacter%", "%shewanella%", "%desulfuromonas%"],
    "sulfur_oxidizer":     ["%thiobacillus%", "%acidithiobacillus%", "%sulfolobus%",
                            "%sulfurimonas%", "%thiomargarita%"],
    "fermenter":           ["%clostridium%", "%lactobacillus%", "%streptococcus%",
                            "%leuconostoc%"],
    "nitrogen_fixer":      ["%azotobacter%", "%rhizobium%", "%bradyrhizobium%"],
    "ammonia_oxidizer":    ["%nitrosomonas%", "%nitrosospira%"],
    "denitrifier":         ["%pseudomonas%", "%paracoccus%"],
    "aerobic_heterotroph": None,  # too broad — use global median
}

# Reducing agent selection by metabolism type (approved addition #1)
REDUCING_AGENTS = {
    "sulfate_reducer":     ("Na2S·9H2O", 0.5, "g/L",
                            "Standard for SRB; sulfide is also a metabolic product"),
    "methanogen":          ("Na2S·9H2O", 0.5, "g/L",
                            "Standard for methanogens; DTT (0.5 mM) as alternative"),
    "iron_reducer":        ("Ti(III) citrate", 0.8, "mM",
                            "Avoids FeS precipitation that occurs with Na2S + Fe(III)"),
    "fermenter":           ("L-Cysteine-HCl", 0.5, "g/L",
                            "Standard for Clostridia and general anaerobes"),
    "default_anaerobe":    ("L-Cysteine-HCl", 0.5, "g/L",
                            "General-purpose reducing agent for anaerobic media"),
}

# Buffer selection by pH range
BUFFER_BY_PH = [
    # (ph_min, ph_max, compound, pKa, typical_conc_gL)
    (3.0, 5.5, "Citrate buffer (Na-citrate + citric acid)", 4.8, 2.0),
    (5.5, 6.5, "MES (2-(N-morpholino)ethanesulfonic acid)", 6.1, 1.95),
    (6.0, 7.5, "KH2PO4 / K2HPO4", 7.2, 0.5),
    (7.0, 8.5, "NaHCO3", 6.4, 2.5),  # CO2/HCO3 system
    (8.5, 10.0, "CAPS (N-cyclohexyl-3-aminopropanesulfonic acid)", 10.4, 2.2),
]

# Carbon source preferences by metabolism type
PREFERRED_CARBON_BY_METABOLISM = {
    "sulfate_reducer":     ["lactate", "pyruvate", "acetate", "ethanol", "formate"],
    "methanogen":          ["CO2"],  # autotrophic; acetate for aceticlastic
    "iron_reducer":        ["acetate", "lactate", "formate"],
    "fermenter":           ["glucose", "sucrose", "starch", "fructose", "maltose"],
    "aerobic_heterotroph": ["glucose", "succinate", "acetate"],
    "sulfur_oxidizer":     ["CO2"],  # mostly autotrophic
    "ammonia_oxidizer":    ["CO2"],  # obligate autotroph
}

# ---------------------------------------------------------------------------
# Genome QC thresholds (MIMAG standards for MAGs)
# ---------------------------------------------------------------------------

GENOME_QC_THRESHOLDS = {
    "high_quality":   {"completeness": 90.0, "contamination": 5.0},
    "medium_quality": {"completeness": 70.0, "contamination": 10.0},
    "low_quality":    {"completeness": 50.0, "contamination": 15.0},
}
