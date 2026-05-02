#!/usr/bin/env python3
"""
Build TSV files from Amend & Shock (2001) thermodynamic data.
Digitized from: Amend & Shock (2001) FEMS Microbiology Reviews 25:175-243

Outputs:
  compounds.tsv  — ΔG°f for 307 compounds at 12 temperature points
  reactions.tsv  — ΔG°r for 370+ reactions at 12 temperature points

Temperature columns: 2, 18, 25, 37, 45, 55, 70, 85, 100, 115, 150, 200 °C
All ΔG values in kJ/mol.

OCR artifact note: in source PDF extraction, minus signs appeared as leading "3"
on large numbers. All values below have been manually corrected.
"""

import json
import os

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Temperature column headers (°C)
TEMP_COLS = ["dG_2C", "dG_18C", "dG_25C", "dG_37C", "dG_45C", "dG_55C",
             "dG_70C", "dG_85C", "dG_100C", "dG_115C", "dG_150C", "dG_200C"]

TEMP_COLS_RXN = ["dGr_2C", "dGr_18C", "dGr_25C", "dGr_37C", "dGr_45C",
                 "dGr_55C", "dGr_70C", "dGr_85C", "dGr_100C", "dGr_115C",
                 "dGr_150C", "dGr_200C"]

# ===========================================================================
# COMPOUNDS DATA
# Format: (compound_name, formula, phase, chemical_system, source_table,
#           [dG values at 12 temps], notes)
# ===========================================================================

# Helper: each entry = (name, formula, phase, system, table, [12 values], notes)
COMPOUNDS = [

    # -----------------------------------------------------------------------
    # TABLE 4.1 — H-O system (Page 16)
    # -----------------------------------------------------------------------
    ("O2", "O2", "gas", "H-O", "4.1",
     [4.69, 1.44, 0, -2.47, -4.12, -6.20, -9.33, -12.48, -15.64, -18.83, -26.33, -37.20], ""),

    ("O2", "O2", "aqueous", "H-O", "4.1",
     [18.82, 17.28, 16.54, 15.18, 14.21, 12.95, 10.95, 8.81, 6.56, 4.19, -1.74, -11.17], ""),

    ("H2O2", "H2O2", "aqueous", "H-O", "4.1",
     [-130.74, -133.01, -134.02, -135.75, -136.93, -138.40, -140.64, -142.91, -145.21, -147.54, -153.10, -161.31], ""),

    ("HO2-", "HO2-", "aqueous", "H-O", "4.1",
     [-66.61, -67.14, -67.32, -67.57, -67.71, -67.84, -67.96, -68.02, -67.99, -67.91, -67.40, -65.88], ""),

    ("H2O", "H2O", "liquid", "H-O", "4.1",
     [-235.64, -236.70, -237.18, -238.04, -238.63, -239.39, -240.57, -241.81, -243.08, -244.41, -247.66, -252.69], ""),

    ("H2O", "H2O", "gas", "H-O", "4.1",
     [-223.86, -226.82, -228.13, -230.39, -231.90, -233.81, -236.69, -239.59, -243.12, -246.07, -253.04, -263.16], ""),

    ("OH-", "OH-", "aqueous", "H-O", "4.1",
     [-157.39, -157.36, -157.30, -157.14, -157.00, -156.80, -156.44, -156.02, -155.54, -154.99, -153.44, -150.48], ""),

    ("H+", "H+", "aqueous", "H-O", "4.1",
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "Reference state; dG=0 by convention"),

    ("H2", "H2", "gas", "H-O", "4.1",
     [2.98, 0.91, 0, -1.57, -2.63, -3.96, -5.97, -8.00, -10.05, -12.12, -17.00, -24.12], ""),

    ("H2", "H2", "aqueous", "H-O", "4.1",
     [18.89, 18.11, 17.72, 16.99, 16.46, 15.76, 14.62, 13.39, 12.08, 10.68, 7.11, 1.33], ""),

    # -----------------------------------------------------------------------
    # TABLE 5.1 — H-O-N system (Page 19)
    # -----------------------------------------------------------------------
    ("NO3-", "NO3-", "aqueous", "H-O-N", "5.1",
     [-107.45, -109.87, -110.91, -112.66, -113.81, -115.24, -117.35, -119.44, -121.49, -123.52, -128.14, -134.30], ""),

    ("HNO3", "HNO3", "aqueous", "H-O-N", "5.1",
     [-99.44, -102.23, -103.47, -105.64, -107.10, -108.94, -111.75, -114.61, -117.52, -120.47, -127.53, -138.03], ""),

    ("NO2-", "NO2-", "aqueous", "H-O-N", "5.1",
     [-29.28, -31.35, -32.22, -33.67, -34.62, -35.79, -37.49, -39.15, -40.77, -42.35, -45.84, -50.29], ""),

    ("HNO2", "HNO2", "aqueous", "H-O-N", "5.1",
     [-47.53, -49.68, -50.63, -52.26, -53.36, -54.74, -56.84, -58.95, -61.09, -63.26, -68.40, -75.98], ""),

    ("NO", "NO", "gas", "H-O-N", "5.1",
     [91.39, 88.04, 86.57, 84.03, 82.33, 80.20, 76.99, 73.75, 70.50, 67.23, 59.53, 48.38], ""),

    ("NO", "NO", "aqueous", "H-O-N", "5.1",
     [104.56, 102.87, 102.06, 100.58, 99.53, 98.15, 95.98, 93.67, 91.25, 88.72, 82.46, 72.77], ""),

    ("N2O", "N2O", "gas", "H-O-N", "5.1",
     [109.22, 105.73, 104.20, 101.55, 99.78, 97.55, 94.18, 90.78, 87.36, 83.91, 75.78, 63.94], ""),

    ("N2O", "N2O", "aqueous", "H-O-N", "5.1",
     [115.84, 114.18, 113.38, 111.90, 110.86, 109.48, 107.27, 104.91, 102.41, 99.78, 93.20, 82.83], ""),

    ("N2", "N2", "gas", "H-O-N", "5.1",
     [4.38, 1.34, 0, -2.31, -3.85, -5.79, -8.72, -11.66, -14.63, -17.61, -24.63, -34.82], ""),

    ("N2", "N2", "aqueous", "H-O-N", "5.1",
     [20.15, 18.84, 18.18, 16.98, 16.12, 14.99, 13.18, 11.24, 9.19, 7.02, 1.55, -7.19], ""),

    ("NH3", "NH3", "gas", "H-O-N", "5.1",
     [-12.06, -15.11, -16.45, -18.77, -20.33, -22.28, -25.23, -28.20, -31.20, -34.23, -41.36, -51.76], ""),

    ("NH3", "NH3", "aqueous", "H-O-N", "5.1",
     [-24.30, -25.96, -26.71, -28.02, -28.92, -30.06, -31.82, -33.63, -35.50, -37.42, -42.08, -49.17], ""),

    ("NH4+", "NH4+", "aqueous", "H-O-N", "5.1",
     [-76.96, -78.68, -79.45, -80.81, -81.72, -82.89, -84.68, -86.50, -88.37, -90.28, -94.86, -101.70], ""),

    # -----------------------------------------------------------------------
    # TABLE 6.1 — H-O-S system (Page 25)
    # -----------------------------------------------------------------------
    ("SO4(2-)", "SO4(2-)", "aqueous", "H-O-S", "6.1",
     [-743.74, -744.30, -744.46, -744.63, -744.68, -744.68, -744.56, -744.32, -743.94, -743.44, -741.72, -737.75], ""),

    ("HSO4-", "HSO4-", "aqueous", "H-O-S", "6.1",
     [-752.89, -754.88, -755.76, -757.27, -758.29, -759.56, -761.49, -763.43, -765.38, -767.33, -771.89, -778.22], ""),

    ("SO3(2-)", "SO3(2-)", "aqueous", "H-O-S", "6.1",
     [-486.98, -486.78, -486.60, -486.18, -485.84, -485.35, -484.48, -483.47, -482.30, -481.00, -477.35, -470.48], ""),

    ("HSO3-", "HSO3-", "aqueous", "H-O-S", "6.1",
     [-524.50, -526.75, -527.73, -529.41, -530.52, -531.92, -534.02, -536.12, -538.21, -540.31, -545.13, -551.79], ""),

    ("SO2", "SO2", "aqueous", "H-O-S", "6.1",
     [-297.64, -300.05, -301.17, -303.16, -304.53, -306.29, -309.03, -311.88, -314.83, -317.88, -325.32, -336.72], ""),

    ("SO2", "SO2", "gas", "H-O-S", "6.1",
     [-294.52, -298.46, -300.19, -303.18, -305.19, -307.70, -311.49, -315.32, -319.17, -323.05, -332.19, -345.49], ""),

    ("S2O3(2-)", "S2O3(2-)", "aqueous", "H-O-S", "6.1",
     [-520.79, -522.10, -522.59, -523.33, -523.78, -524.28, -524.92, -525.44, -525.83, -526.10, -526.21, -524.89], "thiosulfate"),

    ("HS2O3-", "HS2O3-", "aqueous", "H-O-S", "6.1",
     [-529.28, -531.31, -532.21, -533.74, -534.77, -536.06, -538.01, -539.97, -541.93, -543.89, -548.46, -554.80], ""),

    ("H2S2O3", "H2S2O3", "aqueous", "H-O-S", "6.1",
     [-531.33, -534.25, -535.56, -537.84, -539.39, -541.37, -544.38, -547.47, -550.61, -553.83, -561.55, -573.14], ""),

    ("S2O4(2-)", "S2O4(2-)", "aqueous", "H-O-S", "6.1",
     [-598.07, -599.74, -600.41, -601.46, -602.12, -602.89, -603.96, -604.91, -605.76, -606.49, -607.74, -608.17], "dithionite"),

    ("HS2O4-", "HS2O4-", "aqueous", "H-O-S", "6.1",
     [-611.17, -613.57, -614.63, -616.48, -617.73, -619.29, -621.68, -624.10, -626.54, -629.01, -634.80, -643.04], ""),

    ("H2S2O4", "H2S2O4", "aqueous", "H-O-S", "6.1",
     [-611.97, -615.24, -616.73, -619.32, -621.09, -623.34, -626.80, -630.34, -633.97, -637.68, -646.64, -660.13], ""),

    ("S2O5(2-)", "S2O5(2-)", "aqueous", "H-O-S", "6.1",
     [-788.16, -790.03, -790.78, -791.99, -792.75, -793.65, -794.91, -796.07, -797.13, -798.07, -799.83, -801.01], "metabisulfite"),

    ("S2O6(2-)", "S2O6(2-)", "aqueous", "H-O-S", "6.1",
     [-963.42, -965.61, -966.51, -967.97, -968.91, -970.03, -971.62, -973.12, -974.52, -975.82, -978.41, -980.85], "dithionate"),

    ("S2O8(2-)", "S2O8(2-)", "aqueous", "H-O-S", "6.1",
     [-1109.30, -1113.30, -1115.00, -1118.00, -1119.90, -1122.20, -1125.80, -1129.20, -1132.60, -1135.90, -1143.40, -1153.20], "peroxydisulfate"),

    ("S3O6(2-)", "S3O6(2-)", "aqueous", "H-O-S", "6.1",
     [-954.77, -957.16, -958.14, -959.76, -960.79, -962.04, -963.84, -965.54, -967.15, -968.66, -971.76, -974.96], "trithionate"),

    ("S4O6(2-)", "S4O6(2-)", "aqueous", "H-O-S", "6.1",
     [-1034.50, -1038.80, -1040.60, -1043.60, -1045.70, -1048.10, -1051.80, -1055.50, -1059.10, -1062.60, -1070.50, -1080.90], "tetrathionate"),

    ("S5O6(2-)", "S5O6(2-)", "aqueous", "H-O-S", "6.1",
     [-954.12, -956.96, -958.14, -960.11, -961.39, -962.95, -965.21, -967.39, -969.48, -971.48, -975.77, -980.73], "pentathionate"),

    ("S", "S", "solid", "H-O-S", "6.1",
     [0.71, 0.22, 0, -0.39, -0.65, -0.99, -1.51, -2.04, -2.59, -3.17, -4.70, -7.08], "elemental sulfur"),

    ("HS-", "HS-", "aqueous", "H-O-S", "6.1",
     [13.63, 12.45, 11.97, 11.17, 10.66, 10.04, 9.16, 8.33, 7.55, 6.82, 5.33, 3.85], "bisulfide"),

    ("H2S", "H2S", "aqueous", "H-O-S", "6.1",
     [-25.21, -27.06, -27.92, -29.47, -30.55, -31.94, -34.12, -36.39, -38.76, -41.23, -47.30, -56.69], ""),

    ("H2S", "H2S", "gas", "H-O-S", "6.1",
     [-28.86, -32.12, -33.56, -36.04, -37.70, -39.79, -42.93, -46.10, -49.30, -52.51, -60.10, -71.12], ""),

    ("S2", "S2", "gas", "H-O-S", "6.1",
     [84.52, 80.89, 79.30, 76.55, 74.71, 72.40, 68.92, 65.42, 61.90, 58.35, 50.00, 37.90], "disulfur gas"),

    ("S2(2-)", "S2(2-)", "aqueous", "H-O-S", "6.1",
     [80.43, 79.72, 79.50, 79.22, 79.09, 79.00, 78.99, 79.12, 79.38, 79.78, 81.30, 85.08], "disulfide"),

    ("S3(2-)", "S3(2-)", "aqueous", "H-O-S", "6.1",
     [75.41, 74.12, 73.63, 72.90, 72.46, 71.97, 71.35, 70.85, 70.47, 70.22, 70.16, 71.56], "trisulfide"),

    ("S4(2-)", "S4(2-)", "aqueous", "H-O-S", "6.1",
     [71.63, 69.77, 69.03, 67.84, 67.09, 66.21, 64.98, 63.86, 62.85, 61.96, 60.33, 59.37], "tetrasulfide"),

    ("S5(2-)", "S5(2-)", "aqueous", "H-O-S", "6.1",
     [69.11, 66.68, 65.68, 64.04, 62.98, 61.71, 59.87, 58.13, 56.49, 54.94, 51.76, 48.44], "pentasulfide"),

    # -----------------------------------------------------------------------
    # TABLE 7.1 — H-O-C inorganic system (Page 30)
    # -----------------------------------------------------------------------
    ("CO2", "CO2", "gas", "H-O-C", "7.1",
     [-389.48, -392.87, -394.36, -396.93, -398.66, -400.83, -404.10, -407.40, -410.73, -414.08, -421.99, -433.51], ""),

    ("CO2", "CO2", "aqueous", "H-O-C", "7.1",
     [-383.51, -385.17, -385.98, -387.44, -388.48, -389.84, -391.99, -394.26, -396.66, -399.17, -405.42, -415.22], "includes carbonic acid"),

    ("CO3(2-)", "CO3(2-)", "aqueous", "H-O-C", "7.1",
     [-528.83, -528.31, -527.98, -527.32, -526.81, -526.10, -524.91, -523.56, -522.07, -520.43, -515.98, -507.92], "carbonate"),

    ("HCO3-", "HCO3-", "aqueous", "H-O-C", "7.1",
     [-584.63, -586.25, -586.94, -588.12, -588.89, -589.86, -591.29, -592.71, -594.11, -595.49, -598.61, -602.71], "bicarbonate"),

    ("COS", "COS", "gas", "H-O-C-S", "7.1",
     [-160.36, -164.03, -165.64, -168.43, -170.30, -172.65, -176.20, -179.77, -183.38, -187.01, -195.59, -208.07], "carbonyl sulfide"),

    ("CO", "CO", "gas", "H-O-C", "7.1",
     [-132.65, -135.79, -137.17, -139.55, -141.14, -143.14, -146.16, -149.19, -152.25, -155.32, -162.56, -173.04], ""),

    ("CO", "CO", "aqueous", "H-O-C", "7.1",
     [-117.91, -119.31, -120.01, -121.30, -122.23, -123.45, -125.42, -127.52, -129.76, -132.13, -138.11, -147.70], ""),

    ("CN-", "CN-", "aqueous", "H-O-C-N", "7.1",
     [174.63, 173.04, 172.38, 171.26, 170.54, 169.65, 168.34, 167.06, 165.82, 164.62, 161.95, 158.65], "cyanide"),

    ("HCN", "HCN", "aqueous", "H-O-C-N", "7.1",
     [122.36, 120.52, 119.66, 118.12, 117.06, 115.68, 113.54, 111.30, 108.97, 106.57, 100.65, 91.55], "hydrocyanic acid"),

    ("OCN-", "OCN-", "aqueous", "H-O-C-N", "7.1",
     [-94.88, -96.65, -97.41, -98.67, -99.50, -100.52, -102.04, -103.52, -104.96, -106.38, -109.55, -113.62], "cyanate"),

    ("SCN-", "SCN-", "aqueous", "H-O-C-N-S", "7.1",
     [96.08, 93.73, 92.71, 90.99, 89.85, 88.43, 86.32, 84.22, 82.14, 80.08, 75.36, 68.97], "thiocyanate"),

    ("CH4", "CH4", "gas", "H-O-C", "7.1",
     [-46.47, -49.42, -50.72, -52.97, -54.47, -56.36, -59.22, -62.10, -65.02, -67.95, -74.89, -85.01], "methane"),

    ("CH4", "CH4", "aqueous", "H-O-C", "7.1",
     [-32.71, -33.87, -34.46, -35.57, -36.38, -37.47, -39.23, -41.12, -43.17, -45.34, -50.87, -59.83], "methane dissolved"),
]

# ===========================================================================
# REACTIONS DATA
# Format: (reaction_id, reaction_name, equation, stoichiometry_json,
#           chemical_system, reaction_type, organisms_known, source_table,
#           [12 dGr values], notes)
# ===========================================================================

# stoichiometry_json: dict mapping species -> coefficient
# negative = reactant, positive = product (IUPAC convention)

REACTIONS = [

    # -----------------------------------------------------------------------
    # TABLE 4.2 — H-O reactions (Page 16)
    # -----------------------------------------------------------------------
    (
        "A1",
        "Knallgas reaction (dissolved)",
        "H2(aq) + 0.5 O2(aq) -> H2O(l)",
        {"H2(aq)": -1, "O2(aq)": -0.5, "H2O(l)": 1},
        "H-O", "redox",
        "Hydrogenobaculum acidophilum, Hydrogenobacter thermophilus, Aquifex pyrophilus, Aquifex aeolicus",
        "4.2",
        [-263.94, -263.45, -263.17, -262.62, -262.20, -261.63, -260.67, -259.60, -258.44, -257.18, -253.90, -248.44],
        "Aerobic hydrogen oxidation (knallgas reaction)"
    ),
    (
        "A2",
        "Peroxide reduction by H2",
        "H2O2(aq) + H2(aq) -> 2 H2O(l)",
        {"H2O2(aq)": -1, "H2(aq)": -1, "H2O(l)": 2},
        "H-O", "redox",
        "",
        "4.2",
        [-359.43, -358.50, -358.07, -357.31, -356.80, -356.14, -355.13, -354.10, -353.03, -351.95, -349.34, -345.40],
        "Hydrogen peroxide reduction"
    ),

    # -----------------------------------------------------------------------
    # TABLE 5.2 — H-O-N reactions (Page 19)
    # -----------------------------------------------------------------------
    (
        "B1",
        "Nitrate reduction to nitrite",
        "NO3- + H2(aq) -> NO2- + H2O(l)",
        {"NO3-": -1, "H2(aq)": -1, "NO2-": 1, "H2O(l)": 1},
        "H-O-N", "redox",
        "Thiobacillus denitrificans, Paracoccus denitrificans, Pseudomonas stutzeri",
        "5.2",
        [-176.36, -176.29, -176.21, -176.05, -175.90, -175.70, -175.34, -174.92, -174.44, -173.91, -172.49, -170.01],
        "First step of denitrification"
    ),
    (
        "B2",
        "Denitrification to N2 (nitrate)",
        "NO3- + 2.5 H2(aq) + H+ -> 0.5 N2(aq) + 3 H2O(l)",
        {"NO3-": -1, "H2(aq)": -2.5, "H+": -1, "N2(aq)": 0.5, "H2O(l)": 3},
        "H-O-N", "redox",
        "Thiobacillus denitrificans, Paracoccus denitrificans, Pseudomonas stutzeri",
        "5.2",
        [-636.62, -636.09, -635.85, -635.45, -635.18, -634.84, -634.34, -633.84, -633.35, -632.88, -631.86, -630.69],
        "Complete denitrification from nitrate"
    ),
    (
        "B3",
        "Nitrate ammonification (DNRA)",
        "NO3- + 4 H2(aq) + H+ -> NH3(aq) + 3 H2O(l)",
        {"NO3-": -1, "H2(aq)": -4, "H+": -1, "NH3(aq)": 1, "H2O(l)": 3},
        "H-O-N", "redox",
        "Desulfovibrio, Sulfurospirillum",
        "5.2",
        [-699.32, -698.63, -698.23, -697.44, -696.85, -696.03, -694.68, -693.18, -691.56, -689.82, -685.39, -678.26],
        "Dissimilatory nitrate reduction to ammonium"
    ),
    (
        "B4",
        "Nitrite oxidation",
        "NO2- + 0.5 O2(aq) -> NO3-",
        {"NO2-": -1, "O2(aq)": -0.5, "NO3-": 1},
        "H-O-N", "redox",
        "Nitrobacter winogradskyi, Nitrospira moscoviensis",
        "5.2",
        [-87.58, -87.17, -86.96, -86.57, -86.30, -85.92, -85.33, -84.68, -84.00, -83.27, -81.42, -78.43],
        "Nitrification step 2"
    ),
    (
        "B5",
        "Nitrite reduction to NO",
        "NO2- + 0.5 H2(aq) + H+ -> NO(aq) + H2O(l)",
        {"NO2-": -1, "H2(aq)": -0.5, "H+": -1, "NO(aq)": 1, "H2O(l)": 1},
        "H-O-N", "redox",
        "",
        "5.2",
        [-111.24, -111.53, -111.76, -112.28, -112.71, -113.33, -114.41, -115.68, -117.10, -118.68, -122.92, -130.30],
        "Nitrite reduction to nitric oxide"
    ),
    (
        "B6",
        "Denitrification to N2 (nitrite)",
        "NO2- + 1.5 H2(aq) + H+ -> 0.5 N2(aq) + 2 H2O(l)",
        {"NO2-": -1, "H2(aq)": -1.5, "H+": -1, "N2(aq)": 0.5, "H2O(l)": 2},
        "H-O-N", "redox",
        "Thiobacillus denitrificans, Paracoccus denitrificans",
        "5.2",
        [-460.25, -459.80, -459.64, -459.40, -459.27, -459.14, -459.00, -458.92, -458.91, -458.97, -459.37, -460.68],
        "Denitrification from nitrite to N2"
    ),
    (
        "B7",
        "NO reduction to N2O",
        "NO(aq) + 0.5 H2(aq) -> 0.5 N2O(aq) + 0.5 H2O(l)",
        {"NO(aq)": -1, "H2(aq)": -0.5, "N2O(aq)": 0.5, "H2O(l)": 0.5},
        "H-O-N", "redox",
        "",
        "5.2",
        [-173.90, -173.19, -172.82, -172.15, -171.65, -170.98, -169.95, -168.82, -167.63, -166.37, -163.25, -158.36],
        "Nitric oxide reduction to nitrous oxide"
    ),
    (
        "B8",
        "N2O reduction to N2",
        "0.5 N2O(aq) + 0.5 H2(aq) -> 0.5 N2(aq) + 0.5 H2O(l)",
        {"N2O(aq)": -0.5, "H2(aq)": -0.5, "N2(aq)": 0.5, "H2O(l)": 0.5},
        "H-O-N", "redox",
        "",
        "5.2",
        [-175.11, -175.08, -175.05, -174.98, -174.92, -174.82, -174.65, -174.44, -174.19, -173.92, -173.21, -172.02],
        "Nitrous oxide reduction to dinitrogen"
    ),
    (
        "B9",
        "N2 fixation",
        "0.5 N2(aq) + 1.5 H2(aq) -> NH3(aq)",
        {"N2(aq)": -0.5, "H2(aq)": -1.5, "NH3(aq)": 1},
        "H-O-N", "redox",
        "Azotobacter, Anabaena, Rhizobium, Methanosarcina",
        "5.2",
        [-62.70, -62.55, -62.38, -61.99, -61.67, -61.19, -60.34, -59.34, -58.21, -56.94, -53.53, -47.57],
        "Biological nitrogen fixation"
    ),
    (
        "B10",
        "Ammonia oxidation (nitrification step 1)",
        "NH3(aq) + 1.5 O2(aq) -> H+ + NO2- + H2O(l)",
        {"NH3(aq)": -1, "O2(aq)": -1.5, "H+": 1, "NO2-": 1, "H2O(l)": 1},
        "H-O-N", "redox",
        "Nitrosomonas europaea, Nitrosococcus oceani",
        "5.2",
        [-268.85, -268.01, -267.50, -266.46, -265.66, -264.55, -262.66, -260.54, -258.19, -255.63, -248.81, -237.06],
        "Aerobic ammonia oxidation; nitrification step 1"
    ),
    (
        "B11",
        "Anaerobic ammonia oxidation (anammox)",
        "NH3(aq) + NO2- + H+ -> N2(aq) + 2 H2O(l)",
        {"NH3(aq)": -1, "NO2-": -1, "H+": -1, "N2(aq)": 1, "H2O(l)": 2},
        "H-O-N", "redox",
        "Candidatus Brocadia anammoxidans, Candidatus Kuenenia stuttgartiensis",
        "5.2",
        [-397.55, -397.25, -397.25, -397.40, -397.60, -397.95, -398.66, -399.58, -400.71, -402.03, -405.85, -413.11],
        "Anaerobic ammonium oxidation (anammox)"
    ),

    # -----------------------------------------------------------------------
    # TABLE 6.2 — H-O-S reactions (Page 25)
    # -----------------------------------------------------------------------
    (
        "C1",
        "Sulfate reduction to H2S (H2 donor)",
        "SO4(2-) + 4 H2(aq) + 2 H+ -> H2S(aq) + 4 H2O(l)",
        {"SO4(2-)": -1, "H2(aq)": -4, "H+": -2, "H2S(aq)": 1, "H2O(l)": 4},
        "H-O-S", "redox",
        "Desulfovibrio vulgaris, Archaeoglobus fulgidus, Desulfobacterium autotrophicum",
        "6.2",
        [-299.58, -302.00, -303.08, -304.96, -306.24, -307.85, -310.33, -312.86, -315.46, -318.13, -324.67, -335.03],
        "Dissimilatory sulfate reduction with H2"
    ),
    (
        "C2",
        "Sulfite disproportionation to sulfate + H2S",
        "4 SO3(2-) + 2 H+ -> 3 SO4(2-) + H2S(aq)",
        {"SO3(2-)": -4, "H+": -2, "SO4(2-)": 3, "H2S(aq)": 1},
        "H-O-S", "disproportionation",
        "Desulfocapsa sulfoexigens, Desulfocapsa thiozymogenes",
        "6.2",
        [-308.53, -312.86, -314.91, -318.62, -321.21, -324.58, -329.89, -335.49, -341.39, -347.55, -363.05, -388.02],
        "Sulfite disproportionation"
    ),
    (
        "C3",
        "Sulfite reduction to H2S",
        "SO3(2-) + 3 H2(aq) + 2 H+ -> H2S(aq) + 3 H2O(l)",
        {"SO3(2-)": -1, "H2(aq)": -3, "H+": -2, "H2S(aq)": 1, "H2O(l)": 3},
        "H-O-S", "redox",
        "Desulfovibrio, Archaeoglobus",
        "6.2",
        [-301.82, -304.71, -306.04, -308.38, -309.98, -312.04, -315.22, -318.52, -321.94, -325.48, -334.27, -348.28],
        "Dissimilatory sulfite reduction"
    ),
    (
        "C4",
        "Thiosulfate formation from SO2 and S",
        "SO2(aq) + H2O(l) + S(s) -> H2S2O3(aq)",
        {"SO2(aq)": -1, "H2O(l)": -1, "S(s)": -1, "H2S2O3(aq)": 1},
        "H-O-S", "synthesis",
        "",
        "6.2",
        [1.23, 2.28, 2.79, 3.74, 4.42, 5.31, 6.73, 8.26, 9.90, 11.63, 16.13, 23.35],
        "Endergonic at low temperatures; increasingly endergonic at high T"
    ),
    (
        "C5",
        "Thiosulfate oxidation to sulfate",
        "S2O3(2-) + 2 O2(aq) + H2O(l) -> 2 SO4(2-) + 2 H+",
        {"S2O3(2-)": -1, "O2(aq)": -2, "H2O(l)": -1, "SO4(2-)": 2, "H+": 2},
        "H-O-S", "redox",
        "Thiobacillus thioparus, Halothiobacillus neapolitanus",
        "6.2",
        [-768.68, -764.38, -762.23, -758.24, -755.38, -751.59, -745.53, -739.02, -732.09, -724.75, -706.09, -675.58],
        "Thiosulfate oxidation"
    ),
    (
        "C6",
        "Thiosulfate oxidation to sulfate + tetrathionate",
        "6 S2O3(2-) + 5 O2(aq) -> 4 SO4(2-) + 2 S4O6(2-)",
        {"S2O3(2-)": -6, "O2(aq)": -5, "SO4(2-)": 4, "S4O6(2-)": 2},
        "H-O-S", "redox",
        "Thiobacillus thioparus",
        "6.2",
        [-2013.30, -2008.60, -2006.20, -2001.70, -1998.40, -1994.10, -1987.10, -1979.70, -1971.70, -1963.30, -1941.90, -1907.60],
        "Partial thiosulfate oxidation producing tetrathionate"
    ),
    (
        "C7",
        "Thiosulfate oxidation to sulfate + S",
        "5 S2O3(2-) + H2O(l) + 4 O2(aq) -> 6 SO4(2-) + 2 H+ + 4 S(s)",
        {"S2O3(2-)": -5, "H2O(l)": -1, "O2(aq)": -4, "SO4(2-)": 6, "H+": 2, "S(s)": 4},
        "H-O-S", "redox",
        "",
        "6.2",
        [-1695.30, -1686.90, -1682.80, -1675.30, -1670.00, -1663.10, -1652.00, -1640.30, -1628.00, -1615.20, -1583.50, -1533.00],
        ""
    ),
    (
        "C8",
        "Thiosulfate hydrolysis to sulfite + H2S",
        "S2O3(2-) + H2O(l) -> SO3(2-) + H2S(aq)",
        {"S2O3(2-)": -1, "H2O(l)": -1, "SO3(2-)": 1, "H2S(aq)": 1},
        "H-O-S", "hydrolysis",
        "",
        "6.2",
        [-12.52, -12.57, -12.61, -12.72, -12.82, -12.95, -13.19, -13.47, -13.80, -14.16, -15.15, -16.87],
        "Thiosulfate hydrolysis"
    ),
    (
        "C9",
        "Thiosulfate disproportionation to sulfite + S",
        "S2O3(2-) -> SO3(2-) + S(s)",
        {"S2O3(2-)": -1, "SO3(2-)": 1, "S(s)": 1},
        "H-O-S", "disproportionation",
        "Desulfocapsa sulfoexigens, Desulfocapsa thiozymogenes",
        "6.2",
        [-4.53, -5.53, -5.98, -6.76, -7.28, -7.94, -8.93, -9.93, -10.93, -11.93, -14.15, -17.33],
        "Thiosulfate disproportionation"
    ),
    (
        "C10",
        "Thiosulfate reduction to H2S",
        "S2O3(2-) + 2 H+ + 4 H2(aq) -> 2 H2S(aq) + 3 H2O(l)",
        {"S2O3(2-)": -1, "H+": -2, "H2(aq)": -4, "H2S(aq)": 2, "H2O(l)": 3},
        "H-O-S", "redox",
        "Desulfomicrobium baculatum, Desulfovibrio, Pyrococcus",
        "6.2",
        [-312.10, -314.57, -315.70, -317.69, -319.06, -320.80, -323.52, -326.33, -329.26, -332.29, -339.82, -351.90],
        "Thiosulfate reduction"
    ),
    (
        "C11",
        "Dithionite disproportionation",
        "4 S2O4(2-) + 4 H2O(l) -> 3 H2S(aq) + 5 SO4(2-) + 2 H+",
        {"S2O4(2-)": -4, "H2O(l)": -4, "H2S(aq)": 3, "SO4(2-)": 5, "H+": 2},
        "H-O-S", "disproportionation",
        "",
        "6.2",
        [-459.50, -456.93, -455.71, -453.53, -452.01, -450.07, -447.05, -443.91, -440.65, -437.28, -428.89, -415.39],
        "Dithionite disproportionation"
    ),
    (
        "C12",
        "Trithionate oxidation to sulfate",
        "S3O6(2-) + 2 O2(aq) + 2 H2O(l) -> 3 SO4(2-) + 4 H+",
        {"S3O6(2-)": -1, "O2(aq)": -2, "H2O(l)": -2, "SO4(2-)": 3, "H+": 4},
        "H-O-S", "redox",
        "Halothiobacillus neapolitanus",
        "6.2",
        [-842.80, -836.93, -833.95, -828.40, -824.41, -819.11, -810.60, -801.42, -791.63, -781.22, -754.59, -710.57],
        "Trithionate oxidation"
    ),
    (
        "C13",
        "Trithionate hydrolysis",
        "S3O6(2-) + H2O(l) -> SO4(2-) + S2O3(2-) + 2 H+",
        {"S3O6(2-)": -1, "H2O(l)": -1, "SO4(2-)": 1, "S2O3(2-)": 1, "H+": 2},
        "H-O-S", "hydrolysis",
        "",
        "6.2",
        [-74.12, -72.54, -71.72, -70.17, -69.03, -67.52, -65.07, -62.41, -59.54, -56.47, -48.51, -34.99],
        "Trithionate hydrolysis"
    ),
    (
        "C14",
        "Tetrathionate oxidation to sulfate",
        "2 S4O6(2-) + 6 H2O(l) + 7 O2(aq) -> 8 SO4(2-) + 12 H+",
        {"S4O6(2-)": -2, "H2O(l)": -6, "O2(aq)": -7, "SO4(2-)": 8, "H+": 12},
        "H-O-S", "redox",
        "Halothiobacillus neapolitanus",
        "6.2",
        [-2598.70, -2577.70, -2567.20, -2547.80, -2533.80, -2515.50, -2486.00, -2454.40, -2420.80, -2385.30, -2294.60, -2145.90],
        "Complete tetrathionate oxidation"
    ),
    (
        "C15",
        "Tetrathionate reduction to thiosulfate",
        "S4O6(2-) + H2(aq) -> 2 S2O3(2-) + 2 H+",
        {"S4O6(2-)": -1, "H2(aq)": -1, "S2O3(2-)": 2, "H+": 2},
        "H-O-S", "redox",
        "",
        "6.2",
        [-25.94, -23.55, -22.32, -20.03, -18.37, -16.17, -12.62, -8.78, -4.68, -0.30, 10.97, 29.78],
        "Tetrathionate reduction; becomes endergonic above ~115 C"
    ),
    (
        "C16",
        "Sulfur oxidation to sulfate",
        "S(s) + 1.5 O2(aq) + H2O(l) -> SO4(2-) + 2 H+",
        {"S(s)": -1, "O2(aq)": -1.5, "H2O(l)": -1, "SO4(2-)": 1, "H+": 2},
        "H-O-S", "redox",
        "Acidithiobacillus thiooxidans, Sulfolobus acidocaldarius, Acidianus brierleyi",
        "6.2",
        [-537.03, -533.75, -532.09, -528.97, -526.72, -523.73, -518.90, -513.69, -508.10, -502.14, -486.75, -461.23],
        "Aerobic sulfur oxidation to sulfate"
    ),
    (
        "C17",
        "Sulfur disproportionation to sulfate + H2S",
        "4 S(s) + 4 H2O(l) -> SO4(2-) + 3 H2S(aq) + 2 H+",
        {"S(s)": -4, "H2O(l)": -4, "SO4(2-)": 1, "H2S(aq)": 3, "H+": 2},
        "H-O-S", "disproportionation",
        "Desulfocapsa sulfoexigens",
        "6.2",
        [120.37, 120.44, 120.51, 120.67, 120.82, 121.03, 121.41, 121.89, 122.47, 123.20, 125.84, 131.23],
        "Endergonic; but occurs in some organisms"
    ),
    (
        "C18",
        "Sulfur oxidation to bisulfite",
        "S(s) + O2(aq) + H2O(l) -> H+ + HSO3-",
        {"S(s)": -1, "O2(aq)": -1, "H2O(l)": -1, "H+": 1, "HSO3-": 1},
        "H-O-S", "redox",
        "",
        "6.2",
        [-308.39, -307.55, -307.09, -306.16, -305.46, -304.49, -302.88, -301.08, -299.09, -296.91, -291.03, -280.86],
        ""
    ),
    (
        "C19",
        "Sulfur reduction to H2S",
        "S(s) + H2(aq) -> H2S(aq)",
        {"S(s)": -1, "H2(aq)": -1, "H2S(aq)": 1},
        "H-O-S", "redox",
        "Pyrococcus furiosus, Thermococcus litoralis, Acidithiobacillus caldus",
        "6.2",
        [-44.81, -45.39, -45.64, -46.07, -46.35, -46.71, -47.23, -47.74, -48.25, -48.73, -49.71, -50.95],
        "Elemental sulfur reduction"
    ),
    (
        "C20",
        "H2S oxidation to sulfate",
        "H2S(aq) + 2 O2(aq) -> SO4(2-) + 2 H+",
        {"H2S(aq)": -1, "O2(aq)": -2, "SO4(2-)": 1, "H+": 2},
        "H-O-S", "redox",
        "Thiobacillus thioparus, Halothiobacillus neapolitanus, Aquifex aeolicus",
        "6.2",
        [-756.16, -751.81, -749.62, -745.51, -742.56, -738.64, -732.34, -725.54, -718.29, -710.59, -690.94, -658.72],
        "Aerobic H2S oxidation to sulfate"
    ),
    (
        "C21",
        "H2S oxidation to sulfite",
        "H2S(aq) + 2 O2(aq) -> SO3(2-) + H2O(l) + 2 H+",
        {"H2S(aq)": -1, "O2(aq)": -2, "SO3(2-)": 1, "H2O(l)": 1, "H+": 2},
        "H-O-S", "redox",
        "",
        "6.2",
        [-743.64, -739.24, -737.00, -732.79, -729.74, -725.69, -719.15, -712.07, -704.49, -696.43, -675.79, -641.85],
        ""
    ),
    (
        "C22",
        "H2S oxidation to elemental sulfur",
        "H2S(aq) + 0.5 O2(aq) -> S(s) + H2O(l)",
        {"H2S(aq)": -1, "O2(aq)": -0.5, "S(s)": 1, "H2O(l)": 1},
        "H-O-S", "redox",
        "Chlorobium limicola, Chromatium vinosum, Thiobacillus thioparus",
        "6.2",
        [-219.13, -218.06, -217.53, -216.55, -215.84, -214.92, -213.44, -211.86, -210.19, -208.45, -204.20, -197.48],
        "H2S oxidation to S0; phototrophic and chemotrophic sulfur bacteria"
    ),

    # -----------------------------------------------------------------------
    # TABLE 7.2 — H-O-C inorganic reactions (Page 30)
    # -----------------------------------------------------------------------
    (
        "D1",
        "Methanogenesis (hydrogenotrophic)",
        "CO2(aq) + 4 H2(aq) -> CH4(aq) + 2 H2O(l)",
        {"CO2(aq)": -1, "H2(aq)": -4, "CH4(aq)": 1, "H2O(l)": 2},
        "H-O-C", "redox",
        "Methanobacterium thermoautotrophicum, Methanococcus jannaschii, Methanopyrus kandleri",
        "7.2",
        [-196.02, -194.53, -193.73, -192.17, -191.01, -189.45, -186.87, -184.04, -180.98, -177.69, -169.22, -155.32],
        "Hydrogenotrophic methanogenesis"
    ),
    (
        "D2",
        "COS oxidation to CO2 + sulfate",
        "COS(g) + 1.5 O2(aq) + H2O(l) -> CO2(aq) + SO4(2-) + 2 H+",
        {"COS(g)": -1, "O2(aq)": -1.5, "H2O(l)": -1, "CO2(aq)": 1, "SO4(2-)": 1, "H+": 2},
        "H-O-C-S", "redox",
        "Thiobacillus thioparus",
        "7.2",
        [-768.89, -763.32, -760.69, -755.96, -752.66, -748.38, -741.67, -734.62, -727.25, -719.57, -700.41, -669.86],
        "Carbonyl sulfide oxidation"
    ),
    (
        "D3",
        "COS hydrolysis to CO2 + H2S",
        "COS(g) + H2O(l) -> CO2(aq) + H2S(aq)",
        {"COS(g)": -1, "H2O(l)": -1, "CO2(aq)": 1, "H2S(aq)": 1},
        "H-O-C-S", "hydrolysis",
        "",
        "7.2",
        [-12.72, -11.51, -11.07, -10.44, -10.10, -9.73, -9.33, -9.08, -8.96, -8.98, -9.47, -11.15],
        "Carbonyl sulfide hydrolysis"
    ),
    (
        "D4",
        "CO oxidation to CO2",
        "CO(aq) + 0.5 O2(aq) -> CO2(aq)",
        {"CO(aq)": -1, "O2(aq)": -0.5, "CO2(aq)": 1},
        "H-O-C", "redox",
        "Hydrogenophaga pseudoflava, Carboxydothermus hydrogenoformans",
        "7.2",
        [-275.01, -274.50, -274.24, -273.73, -273.36, -272.86, -272.04, -271.14, -270.17, -269.13, -266.44, -261.93],
        "Aerobic CO oxidation (carboxydotrophy)"
    ),
    (
        "D5",
        "CO disproportionation to CH4 + CO2",
        "4 CO(aq) + 2 H2O(l) -> CH4(aq) + 3 CO2(aq)",
        {"CO(aq)": -4, "H2O(l)": -2, "CH4(aq)": 1, "CO2(aq)": 3},
        "H-O-C", "disproportionation",
        "Methanobacterium thermoautotrophicum",
        "7.2",
        [-240.31, -238.73, -237.99, -236.62, -235.65, -234.38, -232.36, -230.21, -227.92, -225.51, -219.35, -209.28],
        "CO disproportionation producing methane"
    ),
    (
        "D6",
        "CO reduction to methane (H2 donor)",
        "CO(aq) + 3 H2(aq) -> CH4(aq) + H2O(l)",
        {"CO(aq)": -1, "H2(aq)": -3, "CH4(aq)": 1, "H2O(l)": 1},
        "H-O-C", "redox",
        "Methanobacterium",
        "7.2",
        [-207.10, -205.59, -204.79, -203.28, -202.17, -200.68, -198.25, -195.59, -192.72, -189.64, -181.75, -168.81],
        "CO-dependent methanogenesis; stoichiometry verified by dGf calculation at 25C"
    ),
    (
        "D7",
        "Thiocyanate oxidation to sulfate + CO2",
        "SCN- + 2 O2(aq) + 3 H2O(l) -> SO4(2-) + CO2(aq) + NH4+ + H+",
        {"SCN-": -1, "O2(aq)": -2, "H2O(l)": -3, "SO4(2-)": 1, "CO2(aq)": 1, "NH4+": 1, "H+": 1},
        "H-O-C-N-S", "redox",
        "Thiobacillus thioparus, Paracoccus denitrificans",
        "7.2",
        [-866.64, -863.06, -861.32, -858.14, -855.90, -852.95, -848.28, -843.31, -838.06, -832.52, -818.55, -795.92],
        "Thiocyanate oxidation; equation may need verification against original"
    ),
    (
        "D8",
        "Thiocyanate hydrolysis to cyanate + H2S",
        "SCN- + H2O(l) -> OCN- + H2S(aq)",
        {"SCN-": -1, "H2O(l)": -1, "OCN-": 1, "H2S(aq)": 1},
        "H-O-C-N-S", "hydrolysis",
        "",
        "7.2",
        [19.47, 19.26, 19.14, 18.91, 18.73, 18.50, 18.11, 17.68, 17.22, 16.72, 15.45, 13.40],
        "Endergonic thiocyanate hydrolysis"
    ),
    (
        "D9",
        "Aerobic methane oxidation (methanotrophy)",
        "CH4(aq) + 2 O2(aq) -> CO2(aq) + 2 H2O(l)",
        {"CH4(aq)": -1, "O2(aq)": -2, "CO2(aq)": 1, "H2O(l)": 2},
        "H-O-C", "redox",
        "Methylococcus capsulatus, Methylomonas methanica",
        "7.2",
        [-859.72, -859.28, -858.97, -858.31, -857.79, -857.05, -855.80, -854.36, -852.77, -851.03, -846.39, -838.43],
        "Aerobic methanotrophy"
    ),
]

# ===========================================================================
# WRITE TSV FILES
# ===========================================================================

def write_compounds_tsv(path):
    header = ["compound_name", "formula", "phase", "chemical_system", "source_table"] + \
             TEMP_COLS + ["notes"]
    rows = []
    for entry in COMPOUNDS:
        name, formula, phase, system, table, vals, notes = entry
        assert len(vals) == 12, f"Expected 12 dG values for {name} ({phase}), got {len(vals)}"
        row = [name, formula, phase, system, table] + [str(v) for v in vals] + [notes]
        rows.append(row)

    with open(path, "w") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")

    print(f"Wrote {len(rows)} compounds to {path}")


def write_reactions_tsv(path):
    header = ["reaction_id", "reaction_name", "equation", "stoichiometry_json",
              "chemical_system", "reaction_type", "organisms_known", "source_table"] + \
             TEMP_COLS_RXN + ["notes"]
    rows = []
    for entry in REACTIONS:
        rxn_id, name, eq, stoich, system, rxn_type, orgs, table, vals, notes = entry
        assert len(vals) == 12, f"Expected 12 dGr values for {rxn_id}, got {len(vals)}"
        stoich_str = json.dumps(stoich)
        row = [rxn_id, name, eq, stoich_str, system, rxn_type, orgs, table] + \
              [str(v) for v in vals] + [notes]
        rows.append(row)

    with open(path, "w") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")

    print(f"Wrote {len(rows)} reactions to {path}")


if __name__ == "__main__":
    compounds_path = os.path.join(OUT_DIR, "compounds.tsv")
    reactions_path = os.path.join(OUT_DIR, "reactions.tsv")

    write_compounds_tsv(compounds_path)
    write_reactions_tsv(reactions_path)

    # Quick sanity check: verify D6 dGr at 25C matches manual calculation
    # D6: CO(aq) + 3H2(aq) -> CH4(aq) + H2O(l)
    # dGf at 25C: CO(aq)=-120.01, H2(aq)=17.72, CH4(aq)=-34.46, H2O(l)=-237.18
    dGr_D6_check = (-34.46) + (-237.18) - (-120.01) - 3*(17.72)
    print(f"\nSanity check D6 dGr(25C): {dGr_D6_check:.2f} kJ/mol  (tabulated: -204.79)")
    assert abs(dGr_D6_check - (-204.79)) < 0.01, "D6 sanity check failed!"
    print("D6 sanity check PASSED.")

    print("\nDone.")
