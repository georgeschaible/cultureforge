"""Recipe composer (Phase 2c).

Reads a RecipeContext (Phase 2b) and produces a Recipe with full evidence trail.

Design principles (from prompt):
- Dominant-mode recipe: ONE recipe per genome based on its highest-confidence
  cultivation mode. Other modes are flagged.
- Thermodynamic feasibility as a coarse filter, not fine-tuning.
- Evidence-trail outputs: every ingredient carries rationale + confidence +
  derived_from.
- Honest uncertainty flags traced to docs/LIMITATIONS.md categories.

Workflow:
    1. Derive RecipeContext from CapabilityProfile.
    2. Choose primary cultivation mode (highest-confidence among feasible).
    3. Route to mode-specific composition function.
    4. Add common basal components (trace metals, vitamins, buffer, salts).
    5. Apply mode-specific adjustments.
    6. Apply thermodynamic gating.
    7. Apply uncertainty flags from docs/LIMITATIONS.md.
    8. Compute overall recipe confidence.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from recipe import (
    GasPhase, IncubationConditions, Ingredient, IngredientCategory,
    Recipe, ThermodynamicCheck,
)
from recipe_context import (
    Atmosphere, ElectronAcceptor, ElectronDonor, RecipeContext,
)
from derive_recipe_context import derive_recipe_context


# ---------------------------------------------------------------------------
# Constants — well-established media baselines
# ---------------------------------------------------------------------------

# SL-10 trace metal solution (Tschech & Pfennig 1984), per liter of stock.
# Recipe adds 1 mL of stock per 1 L medium.
SL10_TRACE_METALS_STOCK = {
    "FeCl2·4H2O":   {"g_per_L_stock": 1.5, "formula": "FeCl2·4H2O", "element": "Fe"},
    "ZnCl2":        {"g_per_L_stock": 0.07, "formula": "ZnCl2",     "element": "Zn"},
    "MnCl2·4H2O":   {"g_per_L_stock": 0.1, "formula": "MnCl2·4H2O", "element": "Mn"},
    "H3BO3":        {"g_per_L_stock": 0.006, "formula": "H3BO3",    "element": "B"},
    "CoCl2·6H2O":   {"g_per_L_stock": 0.19, "formula": "CoCl2·6H2O", "element": "Co"},
    "CuCl2·2H2O":   {"g_per_L_stock": 0.002, "formula": "CuCl2·2H2O", "element": "Cu"},
    "NiCl2·6H2O":   {"g_per_L_stock": 0.024, "formula": "NiCl2·6H2O", "element": "Ni"},
    "Na2MoO4·2H2O": {"g_per_L_stock": 0.036, "formula": "Na2MoO4·2H2O", "element": "Mo"},
}

# Wolin's vitamin solution (Wolin et al. 1963), per liter of stock.
# Recipe adds 1 mL of stock per 1 L medium.
WOLIN_VITAMINS_STOCK = {
    "Biotin":           {"mg_per_L_stock": 2.0, "rationale": "B-vitamin, common cofactor"},
    "Folic acid":       {"mg_per_L_stock": 2.0, "rationale": "C1 metabolism cofactor"},
    "Pyridoxine HCl":   {"mg_per_L_stock": 10.0, "rationale": "B6, transamination"},
    "Thiamine HCl":     {"mg_per_L_stock": 5.0, "rationale": "B1, decarboxylations"},
    "Riboflavin":       {"mg_per_L_stock": 5.0, "rationale": "B2, FAD/FMN"},
    "Nicotinic acid":   {"mg_per_L_stock": 5.0, "rationale": "B3, NAD/NADP"},
    "Ca-pantothenate":  {"mg_per_L_stock": 5.0, "rationale": "B5, CoA"},
    "Cyanocobalamin":   {"mg_per_L_stock": 0.1, "rationale": "B12, methyl transfer"},
    "p-Aminobenzoic acid": {"mg_per_L_stock": 5.0, "rationale": "Folate precursor"},
    "Lipoic acid":      {"mg_per_L_stock": 5.0, "rationale": "Lipoamide cofactor"},
}


# Default substrate activities for thermodynamic gating (25°C, pH 7).
# Coarse "standard physiological conditions" for the dominant reaction check.
DEFAULT_ACTIVITIES = {
    "H2_aq": 1e-6, "CO2_aq": 1e-3, "CH4_aq": 1e-6, "O2_aq": 2.5e-4,
    "NH4+": 1e-3, "NO3-": 1e-3, "NO2-": 1e-5, "N2_aq": 6e-4,
    "SO4-2": 1e-3, "HS-": 1e-5, "S0": 1.0, "Fe2+": 1e-6, "Fe3+_solid": 1.0,
    "acetate": 1e-3, "lactate": 1e-3, "succinate": 1e-4, "ethanol": 1e-4,
    "H+": 1e-7, "HCO3-": 1e-3, "H2O": 1.0, "Mn4+_solid": 1.0,
}


# Reaction templates — dominant energy-conserving reaction per cultivation mode.
# delta_g_standard values from Thauer/Amend & Shock thermodynamic tables;
# values at 25°C, pH 7, default activities (used as the no-environment-input default).
REACTION_TEMPLATES = {
    "methanogenic": {
        "reaction": "4 H2 + CO2 → CH4 + 2 H2O",
        "delta_g_standard": -135.6,   # kJ/mol (hydrogenotrophic methanogenesis)
    },
    "aerobic_chemotrophic": {
        "reaction": "Organic + O2 → CO2 + H2O (representative: glucose oxidation)",
        "delta_g_standard": -2880.0,  # glucose; large negative
    },
    "anaerobic_respiratory_sulfate": {
        "reaction": "lactate + SO4-2 → acetate + HCO3- + HS-",
        "delta_g_standard": -160.1,
    },
    "anaerobic_respiratory_iron": {
        "reaction": "acetate + 8 Fe(III) → 2 HCO3- + 8 Fe(II) + 9 H+",
        "delta_g_standard": -210.0,
    },
    "anaerobic_respiratory_nitrate": {
        "reaction": "5 organic + 4 NO3- → 5 CO2 + 2 N2 + 7 H2O (denitrification)",
        "delta_g_standard": -2700.0,  # large negative for full denitrification
    },
    "anaerobic_respiratory_dnra": {
        "reaction": "4 HCOO- + NO3- + 7 H+ → 4 CO2 + NH4+ + 3 H2O (DNRA via NrfA)",
        "delta_g_standard": -598.0,   # comparable to denitrification per electron, end product NH4+
    },
    "anaerobic_respiratory_organohalide": {
        "reaction": "H2 + R-Cl → R-H + HCl (reductive dehalogenation)",
        "delta_g_standard": -130.0,   # representative for PCE → TCE
    },
    "phototrophic": {
        "reaction": "Light + CO2 + e-donor → CH2O (photosynthesis, donor-dependent)",
        "delta_g_standard": -300.0,   # representative ΔG with light input
    },
    "fermentative": {
        "reaction": "glucose → 2 lactate (or other fermentation products)",
        "delta_g_standard": -196.0,   # homolactic fermentation
    },
    "lithotrophic_aerobic_ammonia": {
        "reaction": "NH4+ + 1.5 O2 → NO2- + H2O + 2 H+",
        "delta_g_standard": -274.7,   # nitritation
    },
    "lithotrophic_aerobic_sulfur": {
        "reaction": "HS- + 2 O2 → SO4-2 + H+",
        "delta_g_standard": -787.3,   # sulfide oxidation to sulfate
    },
    "lithotrophic_aerobic_iron": {
        "reaction": "4 Fe(II) + O2 + 4 H+ → 4 Fe(III) + 2 H2O",
        "delta_g_standard": -32.0,    # acidophilic Fe(II) oxidation; modest
    },
    "methanotrophic": {
        "reaction": "CH4 + 2 O2 → CO2 + 2 H2O (aerobic methane oxidation)",
        "delta_g_standard": -820.0,   # highly exergonic
    },
    "anme_reverse_methanogenic_nitrate": {
        "reaction": "CH4 + 4 NO3- + H+ → CO2 + 4 NO2- + 3 H2O (ANME-2d, nitrate-coupled)",
        "delta_g_standard": -517.0,   # energy-conserving; ANME-2d has highest yield among ANME
    },
    "anme_reverse_methanogenic_sulfate": {
        "reaction": "CH4 + SO4^2- → HCO3- + HS- + H2O (ANME-1/2/3, sulfate-coupled)",
        "delta_g_standard": -16.6,    # marginal but feasible — supports notoriously slow ANME growth
    },
    "anme_reverse_methanogenic": {
        # Default fallback when sub-mode unknown; uses sulfate coupled value as conservative baseline.
        "reaction": "CH4 + alternative acceptor → CO2 + reduced products (anaerobic methane oxidation)",
        "delta_g_standard": -16.6,
    },
    "lithotrophic_aerobic_nitrite": {
        "reaction": "NO2- + 0.5 O2 → NO3- (canonical NOB)",
        "delta_g_standard": -74.0,    # canonical nitrite oxidation; modest energy yield
    },
    "acetogenic": {
        "reaction": "4 H2 + 2 CO2 → acetate + 2 H2O + H+ (Wood-Ljungdahl)",
        "delta_g_standard": -94.9,
    },
    "syntrophic": {
        "reaction": "butyrate + 2 H2O → 2 acetate + 2 H2 + H+ (requires H2-consuming partner)",
        "delta_g_standard": +48.3,    # ENDERGONIC alone — viable only with low [H2] from partner
    },
    "halophilic_with_rhodopsin": {
        "reaction": "Light + H+ → H+ pumped (rhodopsin proton pumping; supplementary energy)",
        "delta_g_standard": -10.0,    # supplementary; main energy from heterotrophy
    },
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compose_recipe(genome_id: int, conn: sqlite3.Connection,
                   overrides: Optional[dict] = None) -> Recipe:
    """Top-level recipe composition.

    Args:
        genome_id: numeric genome ID.
        conn: open SQLite connection.
        overrides: optional dict with keys 'temperature' (°C), 'ph', 'salinity'
            (g/L NaCl). Each key, when present and not None, overrides the
            corresponding cultivation condition (Phase 3.1 manual overrides).

    Returns a Recipe object with full evidence trail. If detection failed
    catastrophically (no primary cultivation mode could be determined), the
    Recipe is marked `escalated=True` with an `escalation_reason`.
    """
    context = derive_recipe_context(genome_id, conn, overrides=overrides)

    if not context.primary_cultivation_modes:
        return _escalated_recipe(
            context,
            "No primary cultivation mode detected. Detection layer escalated to "
            "structural analysis (Tier 2). No recipe composed.",
        )

    # Fix #1: prefer specific modes over generic for recipe routing
    # F.3 mitigation: only promote marker-required modes that have diagnostic-marker corroboration
    primary_mode = _pick_primary_mode_for_recipe(context, conn=conn)
    alternative_modes = [m for m in context.primary_cultivation_modes if m != primary_mode]

    # Route to mode-specific composer; pass conn for sub-mode classifier (Fix #2)
    composer = _MODE_COMPOSERS.get(primary_mode, _compose_default_recipe)
    if primary_mode in ("anaerobic_respiratory", "anme_reverse_methanogenic"):
        recipe = composer(context, conn=conn)
    else:
        recipe = composer(context)
    recipe.alternative_cultivation_modes = alternative_modes

    # Common basal additions (some are skipped/modified inside composers)
    _add_common_basal_components(recipe, context)

    # Mode-specific adjustments based on conditions / context
    _apply_mode_adjustments(recipe, context)

    # Thermodynamic gating
    _apply_thermodynamic_check(recipe, context, primary_mode, conn=conn)

    # Limitations flags
    _apply_limitations_flags(recipe, context)

    # Final confidence
    recipe.overall_confidence = _compute_recipe_confidence(recipe, context)

    return recipe


# ---------------------------------------------------------------------------
# Helper: common basal components
# ---------------------------------------------------------------------------

def _add_common_basal_components(recipe: Recipe, context: RecipeContext) -> None:
    """Add baseline components common to most cultivation media.

    Phosphate buffer, NaCl baseline, MgSO4·7H2O, CaCl2·2H2O, SL-10 trace
    metals (1 mL/L), Wolin's vitamins (1 mL/L). Some categories may have
    been added by mode-specific composer first; this function only adds
    what's missing.
    """
    have_categories = {ing.category for ing in recipe.ingredients}

    # Buffer — phosphate by default; mode adjustments may swap to HEPES/PIPES later
    if IngredientCategory.BUFFER not in have_categories:
        ph = (recipe.conditions.ph if recipe.conditions and recipe.conditions.ph
              else 7.0)
        recipe.ingredients.append(Ingredient(
            name="Phosphate buffer (KH2PO4 + K2HPO4)",
            chemical_formula="KH2PO4 / K2HPO4",
            concentration=30.0, concentration_unit="mM",
            category=IngredientCategory.BUFFER,
            rationale=f"30 mM phosphate buffer adjusted to pH {ph:.1f}",
            confidence=0.85,
            derived_from=["pH from RecipeContext.conditions"],
        ))

    if IngredientCategory.SALT not in have_categories:
        # Baseline salts; halophile composer overrides NaCl. Phase 3.1: a user
        # --salinity override replaces the default 5 g/L baseline.
        salinity_override = (context.conditions.salinity_g_per_l
                              if context.conditions else None)
        if salinity_override is not None:
            nacl_conc = float(salinity_override)
            nacl_rationale = f"NaCl {nacl_conc:g} g/L (user-supplied salinity override)"
            nacl_derived = ["user_override"]
            nacl_confidence = 0.95
        else:
            nacl_conc = 5.0
            nacl_rationale = "Standard salinity baseline (5 g/L) for non-halophile"
            nacl_derived = ["RecipeContext.conditions.salinity_category"]
            nacl_confidence = 0.85
        recipe.ingredients.append(Ingredient(
            name="NaCl", chemical_formula="NaCl",
            concentration=nacl_conc, concentration_unit="g/L",
            category=IngredientCategory.SALT,
            rationale=nacl_rationale,
            confidence=nacl_confidence,
            derived_from=nacl_derived,
        ))
        recipe.ingredients.append(Ingredient(
            name="MgSO4·7H2O", chemical_formula="MgSO4·7H2O",
            concentration=0.2, concentration_unit="g/L",
            category=IngredientCategory.SALT,
            rationale="Magnesium and sulfur source",
            confidence=0.90,
            derived_from=["common basal"],
        ))
        recipe.ingredients.append(Ingredient(
            name="CaCl2·2H2O", chemical_formula="CaCl2·2H2O",
            concentration=0.04, concentration_unit="g/L",
            category=IngredientCategory.SALT,
            rationale="Calcium baseline",
            confidence=0.90,
            derived_from=["common basal"],
        ))

    # Always add trace metals + vitamins as composite ingredients (1 mL/L of stock)
    if IngredientCategory.TRACE_METAL not in have_categories:
        recipe.ingredients.append(Ingredient(
            name="SL-10 trace metal solution",
            chemical_formula="(see SL-10 reference)",
            concentration=1.0, concentration_unit="mL/L",
            category=IngredientCategory.TRACE_METAL,
            rationale=("SL-10 (Tschech & Pfennig 1984): Fe, Zn, Mn, B, Co, Cu, "
                       "Ni, Mo at standard concentrations. 1 mL/L final."),
            confidence=0.85,
            derived_from=["common basal", "MeBiPred metal predictions"],
        ))

    if IngredientCategory.VITAMIN not in have_categories:
        recipe.ingredients.append(Ingredient(
            name="Wolin's vitamin solution",
            chemical_formula="(see Wolin 1963 reference)",
            concentration=1.0, concentration_unit="mL/L",
            category=IngredientCategory.VITAMIN,
            rationale=("Wolin's vitamins (Wolin et al. 1963): biotin, folic "
                       "acid, pyridoxine, thiamine, riboflavin, nicotinic "
                       "acid, pantothenate, B12, p-aminobenzoic acid, lipoic "
                       "acid. 1 mL/L final."),
            confidence=0.85,
            derived_from=["common basal", "RecipeContext.cofactors"],
        ))


# ---------------------------------------------------------------------------
# Mode-specific composer functions
# ---------------------------------------------------------------------------

def _new_recipe_skeleton(context: RecipeContext, primary_mode: str) -> Recipe:
    """Build the empty Recipe with conditions + species already populated."""
    cond = _conditions_from_context(context)
    return Recipe(
        genome_id=context.genome_id,
        species=context.species,
        primary_cultivation_mode=primary_mode,
        conditions=cond,
    )


def _conditions_from_context(context: RecipeContext) -> IncubationConditions:
    """Pull T/pH from RecipeContext; supply biology-aware defaults if missing."""
    c = context.conditions
    t = (c.temperature_optimum_c if c and c.temperature_optimum_c is not None
         else 30.0)
    ph = c.ph_optimum if c and c.ph_optimum is not None else 7.0
    light_required = any(
        sr.requirement == "light" for sr in context.special_requirements
    )
    rationale = []
    if c and c.source != "unknown":
        # c.source is per-field: "temp:tempura, ph:genomespot, salinity:not_set"
        parts = [p.strip() for p in c.source.split(",")]
        temp_src = next((p.split(":", 1)[1] for p in parts if p.startswith("temp:")), "")
        ph_src = next((p.split(":", 1)[1] for p in parts if p.startswith("ph:")), "")
        rationale.append(f"Temperature {t}°C ({temp_src}), pH {ph} ({ph_src})")
    else:
        rationale.append(f"Temperature {t}°C, pH {ph} (default — no GenomeSPOT/TEMPURA data)")
    return IncubationConditions(
        temperature_c=t, ph=ph,
        light_required=light_required,
        light_intensity_umol_per_m2_per_s=(50.0 if light_required else None),
        shaking_rpm=None,  # default static; aerobic mode flips this
        rationale="; ".join(rationale),
    )


def _compose_methanogenic_recipe(context: RecipeContext) -> Recipe:
    """Methanogenic recipe.

    Atmosphere: H2/CO2 (80/20) at 2 atm.
    Carbon: CO2 (autotrophic for hydrogenotrophic methanogens).
    Reducing agent: Na2S (anaerobic establishment).
    Trace metals: Ni elevated (mcrA cofactor F430).
    """
    recipe = _new_recipe_skeleton(context, "methanogenic")
    recipe.composition_rationale.append(
        "Hydrogenotrophic methanogenesis: H2 oxidation coupled to CO2 reduction "
        "via mcrA (methyl-coenzyme M reductase). Atmosphere is the dominant "
        "energy source; medium provides reducing conditions and cofactors."
    )

    # Gas phase
    recipe.gas_phase = GasPhase(
        composition={"H2": 0.80, "CO2": 0.20},
        pressure_atm=2.0,
        rationale=("H2/CO2 80:20 at 2 atm overpressure — H2 is the electron "
                   "donor; CO2 is both terminal electron acceptor and carbon "
                   "source. Pressurized headspace increases dissolved H2."),
    )

    # Reducing agent
    recipe.ingredients.append(Ingredient(
        name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
        concentration=0.5, concentration_unit="mM",
        category=IngredientCategory.REDUCING_AGENT,
        rationale=("Removes residual O2 and establishes strict anaerobiosis "
                   "(methanogens are obligate anaerobes; mcrA is O2-sensitive)."),
        confidence=0.95,
        derived_from=["primary_atmosphere=anaerobic", "methanogenic mode"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Resazurin", chemical_formula="C12H6NNaO4",
        concentration=1.0, concentration_unit="mg/L",
        category=IngredientCategory.SUPPLEMENT,
        rationale="Oxygen indicator — pink in oxidized state, colorless when reduced.",
        confidence=0.95,
        derived_from=["anaerobic culture"],
    ))

    # Bicarbonate buffer (preferred for methanogens)
    recipe.ingredients.append(Ingredient(
        name="NaHCO3", chemical_formula="NaHCO3",
        concentration=2.5, concentration_unit="g/L",
        category=IngredientCategory.BUFFER,
        rationale=("Bicarbonate buffer in equilibrium with CO2 headspace — "
                   "couples buffering capacity to the carbon source."),
        confidence=0.85,
        derived_from=["methanogenic mode + CO2 headspace"],
    ))

    # Carbon source = CO2 (already in gas phase) — note explicitly
    recipe.ingredients.append(Ingredient(
        name="CO2 (from headspace + bicarbonate)", chemical_formula="CO2",
        concentration=20.0, concentration_unit="% v/v",
        category=IngredientCategory.CARBON_SOURCE,
        rationale="Autotrophic C source; supplied via H2/CO2 headspace + dissolved bicarbonate.",
        confidence=0.90,
        derived_from=["RecipeContext.carbon_sources", "methanogenic mode"],
    ))

    return recipe


def _compose_anme_recipe(context: RecipeContext,
                          conn: Optional["sqlite3.Connection"] = None) -> Recipe:
    """Recipe for ANME archaea — anaerobic methane oxidation (Methanoperedens-class).

    Atmosphere: anaerobic CH4 + N2 (or CH4 + CO2 for marine ANME). Distinct from
    methanotroph air+CH4 (Phase 3.5) and methanogen H2+CO2 (forward direction).
    Methane is substrate (electron donor + carbon source — oxidized to CO2).

    Acceptor selection branched by which essential_marker_OR signal fired:
      - dissimilatory nitrate-reduction pathway @ 100% (gapseq) → NaNO3 (ANME-2d)
      - dsrAB marker hit                                        → Na2SO4 (ANME-1/2/3 sulfate-coupled)
      - mtrC_omcB marker hit                                    → Fe(III) citrate (rare iron-coupled)

    Recipe also notes ANME cultivation is notoriously slow (weeks to months
    doubling time); enrichment culture conditions or syntrophic partners may be
    needed for ANME-1/2/3 (only ANME-2d Methanoperedens has been brought to
    pure culture readily).
    """
    recipe = _new_recipe_skeleton(context, "anme_reverse_methanogenic")
    recipe.composition_rationale.append(
        "Anaerobic methane oxidation by ANME archaea: methane is OXIDIZED "
        "(not produced) — methanogenesis pathway operates in REVERSE, with "
        "electrons flowing from CH4 to an alternative terminal electron "
        "acceptor (NO3- for ANME-2d / Methanoperedens, SO4²⁻ for ANME-1/2/3, "
        "rare Fe(III) for iron-coupled lineages). Distinguishing forward "
        "methanogenesis from reverse: same mcrA enzyme, but reverse-direction "
        "operation is indicated by co-occurrence with acceptor-partner enzymes "
        "(Phase 3.6 essential_marker_OR discriminator)."
    )

    # Determine which acceptor signal fired by inspecting the capability profile.
    has_dsrAB = False
    has_mtrC_omcB = False
    has_nitrate_pathway = False
    if conn is not None:
        try:
            row = conn.execute(
                "SELECT 1 FROM genome_diagnostic_markers "
                "WHERE genome_id = ? AND marker_name = 'dsrAB' AND positive_call = 1 LIMIT 1",
                (context.genome_id,)
            ).fetchone()
            has_dsrAB = bool(row)
            row = conn.execute(
                "SELECT 1 FROM genome_diagnostic_markers "
                "WHERE genome_id = ? AND marker_name = 'mtrC_omcB' AND positive_call = 1 LIMIT 1",
                (context.genome_id,)
            ).fetchone()
            has_mtrC_omcB = bool(row)
            row = conn.execute(
                "SELECT 1 FROM genome_pathways "
                "WHERE genome_id = ? "
                "  AND lower(pathway_name) LIKE '%nitrate reduction%dissimilatory%' "
                "  AND completeness >= 100 AND predicted = 1 LIMIT 1",
                (context.genome_id,)
            ).fetchone()
            has_nitrate_pathway = bool(row)
        except Exception:
            pass

    # Acceptor branching (priority: nitrate > sulfate > iron — most common to rarest)
    if has_nitrate_pathway:
        recipe.primary_cultivation_mode = "anme_reverse_methanogenic (ANME-2d, nitrate-coupled)"
        recipe.gas_phase = GasPhase(
            composition={"CH4": 0.20, "N2": 0.80},
            pressure_atm=1.0,
            rationale=("CH4/N2 80:20 anaerobic atmosphere. Methane is the "
                       "substrate (oxidized to CO2). N2 fills headspace without "
                       "supplying O2. CO2 may be substituted for N2 as buffer-"
                       "compatible balance gas."),
        )
        recipe.ingredients.append(Ingredient(
            name="NaNO3", chemical_formula="NaNO3",
            concentration=10.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale=("Sodium nitrate (~10 mM) as terminal electron acceptor. "
                       "ANME-2d (Methanoperedens) reduces NO3- via divergent "
                       "napAB-like nitrate reductase, with downstream conversion "
                       "of NO2- to N2 by partner enzymes or to NH4+ via nrfA "
                       "if present."),
            confidence=0.85,
            derived_from=["anme_reverse_methanogenesis (nitrate-coupled)",
                          "gapseq nitrate-reduction pathway @ 100%"],
        ))
    elif has_dsrAB:
        recipe.primary_cultivation_mode = "anme_reverse_methanogenic (ANME-1/2/3, sulfate-coupled)"
        recipe.gas_phase = GasPhase(
            composition={"CH4": 0.20, "N2": 0.80},
            pressure_atm=1.0,
            rationale=("CH4/N2 80:20 anaerobic atmosphere. Methane oxidation "
                       "coupled to sulfate reduction. Many ANME-1/2/3 grow only "
                       "in syntrophic consortia with sulfate-reducing bacterial "
                       "partners — pure-culture ANME-1/2/3 cultivation is rare."),
        )
        recipe.ingredients.append(Ingredient(
            name="Na2SO4", chemical_formula="Na2SO4",
            concentration=15.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale=("Sodium sulfate (~15 mM) as terminal electron acceptor. "
                       "Reduced to sulfide via dsrAB (canonical or non-canonical). "
                       "Energy yield is marginal (ΔG ≈ -16 kJ/mol) — accounts for "
                       "the notoriously slow growth of sulfate-coupled ANME."),
            confidence=0.80,
            derived_from=["anme_reverse_methanogenesis (sulfate-coupled)",
                          "dsrAB marker hit"],
        ))
    elif has_mtrC_omcB:
        recipe.primary_cultivation_mode = "anme_reverse_methanogenic (iron-coupled, rare)"
        recipe.gas_phase = GasPhase(
            composition={"CH4": 0.20, "N2": 0.80},
            pressure_atm=1.0,
            rationale="CH4/N2 80:20 anaerobic atmosphere; rare iron-coupled ANME variant.",
        )
        recipe.ingredients.append(Ingredient(
            name="Fe(III) citrate", chemical_formula="Fe(C6H5O7)",
            concentration=20.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale=("Soluble Fe(III) citrate as terminal electron acceptor. "
                       "Iron-coupled ANME is rare and primarily described from "
                       "environmental enrichments — pure-culture cultivation "
                       "may not be tractable."),
            confidence=0.65,
            derived_from=["anme_reverse_methanogenesis (iron-coupled)",
                          "mtrC_omcB marker hit"],
        ))
    else:
        # Fallback: shouldn't happen since essential_marker_OR requires at least one
        recipe.primary_cultivation_mode = "anme_reverse_methanogenic (acceptor unknown)"
        recipe.gas_phase = GasPhase(
            composition={"CH4": 0.20, "N2": 0.80}, pressure_atm=1.0,
            rationale="Anaerobic CH4/N2 atmosphere; specific acceptor not identified.",
        )

    # Reducing agent (anaerobic establishment)
    recipe.ingredients.append(Ingredient(
        name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
        concentration=0.3, concentration_unit="g/L",
        category=IngredientCategory.REDUCING_AGENT,
        rationale=("Sulfide reducing agent to establish strict anaerobic "
                   "conditions. Cysteine HCl (0.5 g/L) is an alternative. "
                   "ANME mcrA is O2-sensitive."),
        confidence=0.90,
        derived_from=["anaerobic cultivation requirement"],
    ))

    # Bicarbonate buffer
    recipe.ingredients.append(Ingredient(
        name="NaHCO3", chemical_formula="NaHCO3",
        concentration=2.5, concentration_unit="g/L",
        category=IngredientCategory.BUFFER,
        rationale="Bicarbonate buffer compatible with anaerobic methane atmosphere.",
        confidence=0.85,
        derived_from=["ANME cultivation conditions"],
    ))

    # Resazurin redox indicator
    recipe.ingredients.append(Ingredient(
        name="Resazurin", chemical_formula="C12H6NNaO4",
        concentration=1.0, concentration_unit="mg/L",
        category=IngredientCategory.SUPPLEMENT,
        rationale="Oxygen redox indicator — pink in oxidized state, colorless when reduced.",
        confidence=0.90, derived_from=["anaerobic culture"],
    ))

    # Cultivation difficulty notice
    recipe.composition_rationale.append(
        "ANME cultivation note: ANME archaea are notoriously slow-growing. "
        "Doubling times range from days (ANME-2d / Methanoperedens on nitrate) "
        "to weeks-months (ANME-1/2/3 on sulfate). Long incubation periods, high "
        "inoculum density, or syntrophic co-cultivation with sulfate-reducing "
        "bacterial partners may be required. Pure-culture ANME cultivation has "
        "been achieved primarily for ANME-2d (Methanoperedens nitroreducens)."
    )

    # Static incubation (no shaking; mass transfer driven by diffusion)
    if recipe.conditions:
        recipe.conditions.shaking_rpm = None
        recipe.conditions.rationale += "; static anaerobic incubation"

    return recipe


def _compose_anammox_recipe(context: RecipeContext,
                             conn: Optional["sqlite3.Connection"] = None) -> Recipe:
    """Recipe for anammox bacteria — anaerobic ammonium oxidation.

    Atmosphere: anaerobic N2 + CO2 (autotrophic via Wood-Ljungdahl-like CO2
    fixation). Distinct from aerobic AOB (Phase 3.5) which uses air + CO2.
    Donor: NH4+ at low concentration (substrate-inhibited above ~100 mM).
    Acceptor: NO2- at low concentration (substrate-inhibited above ~100 mM).
    Carbon: bicarbonate (autotrophic).

    Anammox cultivation is slow (doubling time 10-14 days for enrichment,
    longer for pure culture). Most pure-culture studies use enrichment from
    wastewater anammox reactors; only a few species (Brocadia, Kuenenia)
    have been brought to laboratory cultivation. Marine Scalindua species
    require seawater salinity.

    Signature markers: hzsA (hydrazine synthase α-subunit, unique to anammox)
    and hdh (hydrazine dehydrogenase) — these are diagnostic and have no
    eukaryotic or non-anammox bacterial homologs above ~30% identity.
    """
    recipe = _new_recipe_skeleton(context, "anammox")
    recipe.composition_rationale.append(
        "Anaerobic ammonium oxidation (anammox): NH4+ is oxidized to N2 via "
        "the hydrazine (N2H4) intermediate, with NO2- as the terminal electron "
        "acceptor. The hydrazine synthase (hzsA) catalyzes the unique N-N bond "
        "formation; hydrazine dehydrogenase (hdh) then oxidizes hydrazine "
        "to N2. Anammox is strict anaerobe (mcrA-like O2 sensitivity in "
        "hydrazine machinery) and autotrophic (CO2 fixation via Wood-Ljungdahl- "
        "like path coupled to inverse electron transport)."
    )

    # Atmosphere — N2/CO2 anaerobic
    recipe.gas_phase = GasPhase(
        composition={"N2": 0.90, "CO2": 0.10},
        pressure_atm=1.0,
        rationale=("N2/CO2 90:10 anaerobic atmosphere. CO2 is the carbon "
                   "source via autotrophic Wood-Ljungdahl-like fixation. N2 "
                   "fills headspace without supplying O2 — anammox is strictly "
                   "anaerobic. Trace O2 above ~2 µM inhibits hydrazine "
                   "synthase activity."),
    )

    # Electron donor — NH4+ at low concentration
    recipe.ingredients.append(Ingredient(
        name="NH4Cl", chemical_formula="NH4Cl",
        concentration=50.0, concentration_unit="mg/L",
        category=IngredientCategory.ELECTRON_DONOR,
        rationale=("Ammonium chloride (~1 mM, 50 mg/L) as electron donor. "
                   "Concentrations above ~100 mM inhibit hzsA. For enrichment "
                   "or continuous cultivation, increase to 5 mM (270 mg/L) but "
                   "stay below 200 mg/L to avoid substrate inhibition."),
        confidence=0.85,
        derived_from=["anammox electron donor", "hzsA marker detected"],
    ))

    # Electron acceptor — NO2- at matched low concentration
    recipe.ingredients.append(Ingredient(
        name="NaNO2", chemical_formula="NaNO2",
        concentration=70.0, concentration_unit="mg/L",
        category=IngredientCategory.ELECTRON_ACCEPTOR,
        rationale=("Sodium nitrite (~1 mM, 70 mg/L) as terminal electron "
                   "acceptor. Stoichiometry: 1 NH4+ + 1.32 NO2- → 1.02 N2 "
                   "+ 0.26 NO3- + 2 H2O. Replenish nitrite as it is consumed. "
                   "Concentrations above ~150 mg/L inhibit hdh."),
        confidence=0.85,
        derived_from=["anammox electron acceptor", "stoichiometry from Strous 1998"],
    ))

    # Carbon source — bicarbonate (autotrophic)
    recipe.ingredients.append(Ingredient(
        name="NaHCO3", chemical_formula="NaHCO3",
        concentration=2.0, concentration_unit="g/L",
        category=IngredientCategory.CARBON_SOURCE,
        rationale=("Sodium bicarbonate (~24 mM) as sole carbon source. "
                   "Anammox bacteria fix CO2 via a Wood-Ljungdahl-like pathway "
                   "(acetyl-CoA synthase with anammox-specific variants). "
                   "NaHCO3 also buffers media to pH 7.5-8.0."),
        confidence=0.85,
        derived_from=["anammox autotrophy", "Wood-Ljungdahl-like CO2 fixation"],
    ))

    # No reducing agent — anammox doesn't tolerate sulfide
    # (deliberately omitted; resazurin indicator is OK)
    recipe.ingredients.append(Ingredient(
        name="Resazurin", chemical_formula="C12H6NNaO4",
        concentration=0.5, concentration_unit="mg/L",
        category=IngredientCategory.SUPPLEMENT,
        rationale=("Oxygen indicator. Note: do NOT add sulfide reducing agents "
                   "(Na2S, cysteine) — sulfide inhibits anammox even at low "
                   "concentrations. Anammox itself maintains anaerobic conditions."),
        confidence=0.90,
        derived_from=["anammox sulfide sensitivity"],
    ))

    # Marine vs freshwater note. RecipeContext has no cultivation_context
    # attribute; context.species carries the organism string (genome notes),
    # which contains "Scalindua" for the marine lineage.
    notes = []
    if context.species and ("scalindua" in context.species.lower()
                            or "marine" in context.species.lower()):
        notes.append("Marine Scalindua species: add NaCl at 25-35 g/L (seawater salinity). "
                      "Freshwater Brocadia/Kuenenia: NaCl baseline 1-5 g/L is sufficient.")
    if notes:
        recipe.composition_rationale.extend(notes)

    # Growth-rate warning
    recipe.composition_rationale.append(
        "Anammox doubling time is exceptionally slow: 10-14 days under optimal "
        "enrichment, 20+ days in pure culture. Use enrichment reactors with "
        "biomass retention (sequencing-batch reactor, granular sludge, or "
        "membrane bioreactor) for routine cultivation. Pure-culture cultivation "
        "of Brocadia, Kuenenia, and Scalindua species is described in van der "
        "Star 2007 (Brocadia) and Awata 2013 (Scalindua)."
    )

    return recipe


def _compose_methanotrophy_recipe(context: RecipeContext) -> Recipe:
    """Aerobic methanotrophy recipe (Methylococcus / Methylosinus / Methylocystis class).

    Atmosphere: air + methane (80:20). Methane is both the carbon source AND
    the electron donor; O2 from air is the terminal electron acceptor.
    Cultivation requires sealed gas-tight vessel with periodic gas-phase
    replenishment as methane is consumed.

    Carbon: CH4 via gas phase (no organic carbon in liquid).
    Buffer: phosphate buffer near pH 6.8-7.2 (DSMZ Medium 921 / NMS pattern).
    Nitrogen: NH4Cl as standard inorganic nitrogen source.
    Trace metals: SL-10 — copper especially important for pMMO biosynthesis.
    Vitamins: standard Wolin's.
    Reducing agent: NOT needed (aerobic culture).
    """
    recipe = _new_recipe_skeleton(context, "methanotrophic")
    recipe.composition_rationale.append(
        "Aerobic methanotrophy: CH4 oxidation via methane monooxygenase "
        "(particulate pMMO, encoded by pmoCAB; or soluble sMMO, encoded by "
        "mmoXYBZDC). The methane is supplied via the headspace gas phase — "
        "no organic carbon is added to the liquid medium. Air provides O2 "
        "as terminal electron acceptor."
    )

    # Gas phase — methane + air. This is the first cultivation mode in
    # CultureForge requiring methane in the headspace.
    recipe.gas_phase = GasPhase(
        composition={"air": 0.80, "CH4": 0.20},
        pressure_atm=1.0,
        rationale=("Air (80%) + methane (20%) headspace. Air supplies O2 for "
                   "methane oxidation; methane is the carbon and energy "
                   "source. Cultivation requires gas-tight vessel; replenish "
                   "headspace periodically as methane is consumed. Some "
                   "media use 50:50 air:methane for higher methane uptake."),
    )

    # Buffer: phosphate near pH 7
    recipe.ingredients.append(Ingredient(
        name="K2HPO4", chemical_formula="K2HPO4",
        concentration=1.4, concentration_unit="g/L",
        category=IngredientCategory.BUFFER,
        rationale=("Potassium phosphate (dibasic) — buffer pair component for "
                   "near-neutral pH cultivation. DSMZ Medium 921 / NMS pattern."),
        confidence=0.90,
        derived_from=["aerobic_methanotrophy", "DSMZ Medium 921 (NMS)"],
    ))
    recipe.ingredients.append(Ingredient(
        name="KH2PO4", chemical_formula="KH2PO4",
        concentration=0.7, concentration_unit="g/L",
        category=IngredientCategory.BUFFER,
        rationale="Potassium phosphate (monobasic) — buffer pair component.",
        confidence=0.90,
        derived_from=["aerobic_methanotrophy", "DSMZ Medium 921 (NMS)"],
    ))

    # Nitrogen source: ammonium
    recipe.ingredients.append(Ingredient(
        name="NH4Cl", chemical_formula="NH4Cl",
        concentration=0.5, concentration_unit="g/L",
        category=IngredientCategory.NITROGEN_SOURCE,
        rationale=("Ammonium as N source. Some methanotrophs (Type II "
                   "Methylocystis) can fix N2; some (Methylocapsa, Crenothrix) "
                   "can also oxidize NH4+ at low rates via the related amoA-like "
                   "activity of pmoA. Ammonium is the standard inorganic N "
                   "source for canonical cultivation."),
        confidence=0.85,
        derived_from=["aerobic_methanotrophy", "DSMZ Medium 921 (NMS)"],
    ))

    # Carbon source: CH4 via gas phase (record explicitly)
    recipe.ingredients.append(Ingredient(
        name="CH4 (from headspace)", chemical_formula="CH4",
        concentration=20.0, concentration_unit="% v/v",
        category=IngredientCategory.CARBON_SOURCE,
        rationale=("Methane is both carbon source and electron donor — "
                   "supplied via gas phase, NOT in liquid medium."),
        confidence=0.95,
        derived_from=["aerobic_methanotrophy", "gas-phase carbon"],
    ))

    # Note on copper supplementation (in trace metal solution)
    recipe.composition_rationale.append(
        "Copper supplementation (in SL-10 trace metal solution) is critical "
        "for particulate methane monooxygenase (pMMO) biosynthesis. Type II "
        "methanotrophs may switch to soluble methane monooxygenase (sMMO) "
        "expression under copper limitation. Some cultivation protocols add "
        "additional CuSO4 to drive pMMO expression preferentially."
    )

    # Conditions: vigorous shaking for gas exchange
    if recipe.conditions:
        recipe.conditions.shaking_rpm = 200
        recipe.conditions.rationale += (
            "; vigorous shaking (200 rpm) for gas exchange in sealed vessel"
        )

    return recipe


def _compose_aerobic_chemotrophic_recipe(context: RecipeContext) -> Recipe:
    """Aerobic chemotrophic recipe (heterotrophs respiring O2).

    Atmosphere: air (21% O2).
    Carbon: organic (from RecipeContext, defaulting to a generic complex source).
    """
    recipe = _new_recipe_skeleton(context, "aerobic_chemotrophic")
    recipe.composition_rationale.append(
        "Aerobic chemotrophy: organic carbon oxidation coupled to O2 reduction "
        "via terminal oxidases (Cox/Qox/cbb3). Recipe provides organic carbon "
        "and atmospheric O2."
    )

    # Atmosphere: air
    recipe.gas_phase = GasPhase(
        composition={"air": 1.0}, pressure_atm=1.0,
        rationale="Atmospheric air (21% O2, 0.04% CO2). Standard aerobic culture.",
    )

    # Shaking on for aerobic
    if recipe.conditions:
        recipe.conditions.shaking_rpm = 200
        recipe.conditions.rationale += "; shaking 200 rpm for O2 transfer"

    # Carbon source from context, or generic peptone/yeast extract
    _add_carbon_sources(recipe, context, default_complex=True)

    return recipe


def _compose_anaerobic_respiratory_recipe(context: RecipeContext,
                                            conn: Optional["sqlite3.Connection"] = None) -> Recipe:
    """Anaerobic respiratory recipe — branches by detected acceptor.

    Sub-modes:
      - sulfate reduction (Desulfovibrio-type)
      - iron reduction (Geobacter-type)
      - denitrification
      - organohalide respiration (Dehalococcoides-type)
    """
    recipe = _new_recipe_skeleton(context, "anaerobic_respiratory")
    recipe.composition_rationale.append(
        "Anaerobic respiration: organic donor + non-O2 terminal acceptor."
    )

    # Determine the dominant acceptor
    dominant_acceptor = _pick_dominant_acceptor(context)
    sub_mode = _classify_anaerobic_subtype(context, conn=conn)

    # Atmosphere
    recipe.gas_phase = GasPhase(
        composition={"N2": 0.80, "CO2": 0.20}, pressure_atm=1.0,
        rationale="N2/CO2 80:20 anaerobic headspace; CO2 buffers via bicarbonate.",
    )

    # Reducing agent + indicator
    recipe.ingredients.append(Ingredient(
        name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
        concentration=0.5, concentration_unit="mM",
        category=IngredientCategory.REDUCING_AGENT,
        rationale="Establishes strict anaerobiosis.",
        confidence=0.95,
        derived_from=["anaerobic mode"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Resazurin", chemical_formula="C12H6NNaO4",
        concentration=1.0, concentration_unit="mg/L",
        category=IngredientCategory.SUPPLEMENT,
        rationale="Oxygen indicator.",
        confidence=0.95, derived_from=["anaerobic culture"],
    ))

    # Sub-mode specifics
    if sub_mode == "sulfate":
        recipe.primary_cultivation_mode = "anaerobic_respiratory (sulfate reduction)"
        recipe.ingredients.append(Ingredient(
            name="Na2SO4", chemical_formula="Na2SO4",
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale="Sulfate as terminal electron acceptor (~14 mM).",
            confidence=0.90,
            derived_from=["RecipeContext.electron_acceptors=SO4-2", "dsrAB+qmoA detected"],
        ))
        recipe.ingredients.append(Ingredient(
            name="Sodium DL-lactate", chemical_formula="C3H5NaO3",
            concentration=3.5, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="Standard SRB electron donor (~30 mM).",
            confidence=0.85,
            derived_from=["sulfate reduction; Desulfovibrio-type donor"],
        ))
    elif sub_mode == "iron":
        recipe.primary_cultivation_mode = "anaerobic_respiratory (iron reduction)"
        recipe.ingredients.append(Ingredient(
            name="Ferric citrate", chemical_formula="C6H5FeO7",
            concentration=13.7, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale="Soluble Fe(III) electron acceptor (~50 mM).",
            confidence=0.90,
            derived_from=["RecipeContext.electron_acceptors=Fe(III)", "mtrC/omcB detected"],
        ))
        recipe.ingredients.append(Ingredient(
            name="Sodium acetate", chemical_formula="CH3COONa",
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="Acetate is the canonical Geobacter electron donor (~25 mM).",
            confidence=0.85,
            derived_from=["iron reduction; Geobacter-type donor"],
        ))
    elif sub_mode == "nitrate":
        recipe.primary_cultivation_mode = "anaerobic_respiratory (denitrification)"
        recipe.ingredients.append(Ingredient(
            name="KNO3", chemical_formula="KNO3",
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale="Nitrate as terminal electron acceptor (~20 mM).",
            confidence=0.90,
            derived_from=["RecipeContext.electron_acceptors=NO3-", "nosZ detected"],
        ))
        _add_carbon_sources(recipe, context, default_complex=True)
    elif sub_mode == "dnra":
        # Phase 3.4: Dissimilatory nitrate reduction to ammonium (Wolinella-class)
        recipe.primary_cultivation_mode = "anaerobic_respiratory (DNRA via NrfA)"
        recipe.ingredients.append(Ingredient(
            name="KNO3", chemical_formula="KNO3",
            concentration=15.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale=("Potassium nitrate as terminal electron acceptor "
                       "(~15 mM). Reduced to ammonium via NrfA-catalyzed "
                       "pentaheme cytochrome c nitrite reductase (NO3- → "
                       "NO2- via NarG/NapA, then NO2- + 6 H+ + 6 e- → "
                       "NH4+ + 2 H2O via NrfA)."),
            confidence=0.90,
            derived_from=["RecipeContext.electron_acceptors=NO3-",
                          "nrfA detected (DNRA)"],
        ))
        # Formate as electron donor (canonical Wolinella substrate)
        recipe.ingredients.append(Ingredient(
            name="Sodium formate", chemical_formula="HCOONa",
            concentration=20.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale=("Formate as electron donor. Wolinella succinogenes and "
                       "similar canonical DNRA model organisms grow on formate. "
                       "Lactate or acetate are alternatives — substitute based "
                       "on the specific organism."),
            confidence=0.80,
            derived_from=["DNRA cultivation literature (DSMZ Medium 720 family)"],
        ))
    elif sub_mode == "organohalide":
        recipe.primary_cultivation_mode = "anaerobic_respiratory (organohalide respiration)"
        recipe.ingredients.append(Ingredient(
            name="PCE (tetrachloroethene)", chemical_formula="C2Cl4",
            concentration=100.0, concentration_unit="μM",
            category=IngredientCategory.ELECTRON_ACCEPTOR,
            rationale=("PCE as electron acceptor — ASSUMED substrate. "
                       "Specific organohalide cannot be determined from genome "
                       "alone (docs/LIMITATIONS.md A.1/D.1). User should select "
                       "based on isolation source chemistry."),
            confidence=0.50,
            derived_from=["rdhA detected", "LIMITATIONS A.1/D.1"],
        ))
        # Add hydrogen as donor (H2 atmosphere)
        recipe.gas_phase.composition = {"H2": 0.20, "N2": 0.60, "CO2": 0.20}
        recipe.gas_phase.rationale = ("H2/N2/CO2 20:60:20 — H2 is the electron "
                                      "donor for reductive dehalogenation.")
        recipe.ingredients.append(Ingredient(
            name="H2 (from headspace)", chemical_formula="H2",
            concentration=20.0, concentration_unit="% v/v",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="H2 electron donor (typical for organohalide respirers).",
            confidence=0.85, derived_from=["organohalide respiration"],
        ))
        # B12 critical
        recipe.ingredients.append(Ingredient(
            name="Cyanocobalamin (B12) supplement",
            chemical_formula="C63H88CoN14O14P",
            concentration=50.0, concentration_unit="μg/L",
            category=IngredientCategory.VITAMIN,
            rationale=("B12 supplementation critical for rdhA — corrinoid "
                       "biosynthesis often incomplete in obligate organohalide "
                       "respirers."),
            confidence=0.90, derived_from=["organohalide respiration"],
        ))

    # If neither donor nor acceptor was added by sub-mode, fallback
    if not any(i.category == IngredientCategory.ELECTRON_DONOR for i in recipe.ingredients):
        _add_carbon_sources(recipe, context, default_complex=True)

    return recipe


def _classify_anaerobic_subtype(context: RecipeContext,
                                 conn: Optional["sqlite3.Connection"] = None) -> str:
    """Pick anaerobic respiration subtype from detected acceptors / capabilities.

    Fix #2: when conn is available, query the CapabilityProfile directly to see
    capability-level names like 'Reductive dehalogenation of organohalide
    compounds...'. RecipeContext fields (cultivation_mode_notes,
    primary_cultivation_modes, electron_acceptors) only carry mode-level labels,
    so without the capability profile we miss the organohalide signal.

    Phase 3.4: when multiple anaerobic-respiratory capabilities co-detect
    (e.g., D. vulgaris fires both sulfate_reduction AND DNRA), prefer the
    highest-confidence one. The previous text-match priority would route
    D. vulgaris to DNRA spuriously because text matching is order-dependent.
    Confidence-aware selection respects the gapseq + marker scoring.
    """
    # Phase 3.4: capability-confidence-aware selection when conn available
    if conn is not None:
        try:
            from capability_detectors import profile_capabilities
            profile = profile_capabilities(context.genome_id, conn)
            # Map capability name → sub-mode key
            sub_mode_map = [
                ("Reductive dehalogenation", "organohalide"),
                ("Fe(III) reduction", "iron"),
                ("nitrate reduction to ammonium", "dnra"),
                ("DNRA", "dnra"),
                ("Denitrification", "nitrate"),
                ("Dissimilatory sulfate reduction", "sulfate"),
                ("Anaerobic ammonium oxidation", "anammox"),  # Phase 5.1 P3: superseded by top-level anammox mode; kept for defensive fallback only
            ]
            best_conf = 0.0
            best_sub = None
            for cap in profile.capabilities:
                if not cap.detected or cap.confidence < 0.50:
                    continue
                for pattern, sub in sub_mode_map:
                    if pattern.lower() in cap.name.lower():
                        if cap.confidence > best_conf:
                            best_conf = cap.confidence
                            best_sub = sub
                        break
            if best_sub:
                return best_sub
        except Exception:
            pass

    # Fallback: text-match priority when no capability profile available
    acceptor_names = " ".join(a.name.lower() for a in context.electron_acceptors)
    notes = " ".join(context.cultivation_mode_notes).lower()
    cap_names = " ".join(context.primary_cultivation_modes).lower()
    haystack = acceptor_names + " " + notes + " " + cap_names

    if ("organohalide" in haystack
            or "dehalogen" in haystack
            or "reductive dehalogenation" in haystack):
        return "organohalide"
    if "fe(iii)" in haystack or "iron reduction" in haystack or "fe(iii) reduction" in haystack:
        return "iron"
    if ("dnra" in haystack
            or "nitrate reduction to ammonium" in haystack
            or "nrfa" in haystack):
        return "dnra"
    if ("denitri" in haystack or "nitrate" in haystack or "no3" in haystack):
        return "nitrate"
    if "sulfate" in haystack or "so4" in haystack:
        return "sulfate"
    return "sulfate"  # default


def _pick_dominant_acceptor(context: RecipeContext) -> Optional[ElectronAcceptor]:
    """Return the highest-confidence acceptor; None if none detected."""
    if not context.electron_acceptors:
        return None
    return max(context.electron_acceptors, key=lambda a: a.confidence)


def _compose_phototrophic_recipe(context: RecipeContext) -> Recipe:
    """Phototrophic recipe.

    Branches by phototrophy type detected. Defaults to anoxygenic purple bacteria.
    """
    recipe = _new_recipe_skeleton(context, "phototrophic")
    recipe.composition_rationale.append(
        "Phototrophy: light-driven energy conservation. Recipe provides light, "
        "appropriate atmosphere, and electron donor (organic for heterotrophic "
        "phototrophs, sulfide / H2 for autotrophic phototrophs)."
    )
    recipe.conditions.light_required = True
    recipe.conditions.light_intensity_umol_per_m2_per_s = 50.0

    # Determine sub-mode from cultivation modes / capabilities
    cap_names = " ".join(context.primary_cultivation_modes).lower()
    notes = " ".join(context.cultivation_mode_notes).lower()
    has_oxygenic = "oxygenic" in cap_names + notes and "anoxygenic" not in cap_names + notes
    has_purple = "purple" in cap_names + notes
    has_green = "green sulfur" in cap_names + notes

    if has_oxygenic:
        recipe.primary_cultivation_mode = "phototrophic (oxygenic)"
        recipe.gas_phase = GasPhase(
            composition={"air": 1.0, "CO2": 0.0}, pressure_atm=1.0,
            rationale="Aerobic atmosphere — oxygenic photosynthesis evolves O2.",
        )
    else:
        # Anoxygenic — anaerobic atmosphere
        recipe.primary_cultivation_mode = (
            "phototrophic (anoxygenic, " +
            ("green sulfur" if has_green else "purple Type-II / FAP") + ")"
        )
        recipe.gas_phase = GasPhase(
            composition={"N2": 0.95, "CO2": 0.05}, pressure_atm=1.0,
            rationale="Anaerobic atmosphere required — anoxygenic photosynthesis.",
        )
        # Reducing agent
        recipe.ingredients.append(Ingredient(
            name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
            concentration=0.5, concentration_unit="mM",
            category=IngredientCategory.REDUCING_AGENT,
            rationale=("Establishes anaerobiosis. Sulfide also serves as "
                       "electron donor for purple sulfur and green sulfur "
                       "bacteria."),
            confidence=0.90, derived_from=["anoxygenic phototrophy"],
        ))

    # Electron donor — organic for purple non-sulfur (Rhodopseudomonas), sulfide for purple sulfur (Allochromatium)
    if any(d.name in ("HS-", "H2S", "sulfide", "S2-") for d in context.electron_donors):
        recipe.ingredients.append(Ingredient(
            name="Na2S·9H2O (electron donor)", chemical_formula="Na2S·9H2O",
            concentration=2.0, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="Sulfide as electron donor for anoxygenic photosynthesis.",
            confidence=0.85, derived_from=["RecipeContext.electron_donors=HS-"],
        ))

    _add_carbon_sources(recipe, context, default_complex=False)
    # Default carbon for phototrophs: malate
    if not any(i.category == IngredientCategory.CARBON_SOURCE for i in recipe.ingredients):
        recipe.ingredients.append(Ingredient(
            name="Sodium DL-malate", chemical_formula="C4H4Na2O5",
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.CARBON_SOURCE,
            rationale=("Malate is the canonical carbon source for purple "
                       "non-sulfur photoheterotrophs."),
            confidence=0.75,
            derived_from=["phototrophic mode default"],
        ))

    return recipe


def _compose_fermentative_recipe(context: RecipeContext) -> Recipe:
    """Fermentative recipe — anaerobic, organic carbon, no respiratory acceptor."""
    recipe = _new_recipe_skeleton(context, "fermentative")
    recipe.composition_rationale.append(
        "Fermentation: substrate-level phosphorylation. Recipe provides "
        "fermentable carbon source under anaerobic conditions; no terminal "
        "electron acceptor needed."
    )
    recipe.gas_phase = GasPhase(
        composition={"N2": 1.0}, pressure_atm=1.0,
        rationale="N2 anaerobic headspace; no CO2 needed.",
    )

    # Reducing agent
    recipe.ingredients.append(Ingredient(
        name="L-Cysteine·HCl", chemical_formula="C3H8ClNO2S",
        concentration=0.5, concentration_unit="g/L",
        category=IngredientCategory.REDUCING_AGENT,
        rationale=("Cysteine as reducing agent (gentler than Na2S for "
                   "fermenters; supplies sulfur amino acid)."),
        confidence=0.85, derived_from=["anaerobic + fermentative"],
    ))

    # Carbon source — typically glucose
    _add_carbon_sources(recipe, context, default_complex=False)
    if not any(i.category == IngredientCategory.CARBON_SOURCE for i in recipe.ingredients):
        recipe.ingredients.append(Ingredient(
            name="Glucose", chemical_formula="C6H12O6",
            concentration=10.0, concentration_unit="g/L",
            category=IngredientCategory.CARBON_SOURCE,
            rationale="Glucose as fermentable substrate (~55 mM).",
            confidence=0.80, derived_from=["fermentative mode default"],
        ))

    # Yeast extract baseline for fermenters that need vitamins/amino acids
    recipe.ingredients.append(Ingredient(
        name="Yeast extract", chemical_formula=None,
        concentration=2.0, concentration_unit="g/L",
        category=IngredientCategory.NITROGEN_SOURCE,
        rationale=("Yeast extract supplies amino acids, B-vitamins, and growth "
                   "factors that fermenters typically can't biosynthesize."),
        confidence=0.85, derived_from=["fermentative mode"],
    ))

    return recipe


def _compose_lithotrophic_aerobic_recipe(context: RecipeContext) -> Recipe:
    """Lithotrophic aerobic recipe — branches by donor type."""
    recipe = _new_recipe_skeleton(context, "lithotrophic_aerobic")
    recipe.composition_rationale.append(
        "Lithotrophic aerobic: inorganic electron donor + O2 acceptor. "
        "Autotrophic CO2 fixation supplies carbon."
    )

    cap_names = " ".join(context.primary_cultivation_modes).lower()
    notes = " ".join(context.cultivation_mode_notes).lower() + " " + " ".join(
        c.name for c in context.electron_donors
    ).lower() + " " + " ".join(c.name for c in context.electron_acceptors).lower()
    text = cap_names + " " + notes

    # Atmosphere — air with CO2 supplementation for autotrophy
    recipe.gas_phase = GasPhase(
        composition={"air": 0.98, "CO2": 0.02}, pressure_atm=1.0,
        rationale="Aerobic atmosphere with elevated CO2 for autotrophic carbon fixation.",
    )
    if recipe.conditions:
        recipe.conditions.shaking_rpm = 150
        recipe.conditions.rationale += "; shaking 150 rpm for O2 + CO2 transfer"

    # Carbon source = CO2 (autotrophic)
    recipe.ingredients.append(Ingredient(
        name="CO2 / NaHCO3 (autotrophic carbon)",
        chemical_formula="CO2 / NaHCO3",
        concentration=2.0, concentration_unit="g/L NaHCO3",
        category=IngredientCategory.CARBON_SOURCE,
        rationale=("CO2 from headspace + bicarbonate buffer. Autotrophic "
                   "lithotrophs fix CO2 via CBB cycle (rbcL detected) or rTCA."),
        confidence=0.85, derived_from=["RecipeContext.carbon_sources=CO2", "rbcL/aclA detected"],
    ))

    # Branch by donor
    if "fe(ii)" in text or "iron" in cap_names or "ferro" in text:
        # Acidophilic Fe(II) oxidation (Acidithiobacillus)
        recipe.primary_cultivation_mode = "lithotrophic_aerobic (Fe(II) oxidation, acidophilic)"
        recipe.ingredients.append(Ingredient(
            name="FeSO4·7H2O", chemical_formula="FeSO4·7H2O",
            concentration=20.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale=("Ferrous iron as electron donor (~70 mM). Acidic pH "
                       "(~2) keeps Fe(II) soluble."),
            confidence=0.90,
            derived_from=["RecipeContext.electron_donors=Fe(II)", "cyc2 detected"],
        ))
        # Override pH to acidic
        if recipe.conditions:
            recipe.conditions.ph = 2.0
            recipe.conditions.rationale += " — pH 2.0 (acidophilic; Fe(II) soluble)"
    elif any(t in text for t in ("no2-", "nitrite oxidation", "nxra")):
        # Phase 3.3: canonical NOB (Nitrospira / Nitrobacter / Nitrotoga / Nitrolancea)
        recipe.primary_cultivation_mode = "lithotrophic_aerobic (nitrite oxidation, canonical NOB)"
        recipe.ingredients.append(Ingredient(
            name="NaNO2", chemical_formula="NaNO2",
            concentration=0.5, concentration_unit="mM",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale=("Sodium nitrite as electron donor at LOW concentration "
                       "(0.5 mM). Nitrite is toxic to NOB above ~5 mM — replenish "
                       "during cultivation as it is consumed (NO2- → NO3-)."),
            confidence=0.90,
            derived_from=["RecipeContext.electron_donors=NO2-", "nxrA detected"],
        ))
        # NOB media run at slightly alkaline pH (DSMZ Medium 2399 ~ pH 7.5-8.0)
        if recipe.conditions and recipe.conditions.ph and recipe.conditions.ph < 7.4:
            recipe.conditions.ph = 7.5
            recipe.conditions.rationale += " — pH adjusted to 7.5 (canonical NOB optimum)"
        # Replace generic CO2/NaHCO3 with the explicit NaHCO3 form used in DSMZ NOB media
        for ing in recipe.ingredients:
            if ing.category == IngredientCategory.CARBON_SOURCE and "CO2" in ing.name:
                ing.name = "NaHCO3"
                ing.chemical_formula = "NaHCO3"
                ing.concentration = 2.5
                ing.concentration_unit = "g/L"
                ing.rationale = (
                    "Bicarbonate as carbon source for autotrophic CO2 fixation. "
                    "Nitrospira lineages use rTCA cycle (aclAB); Nitrobacter / "
                    "Nitrolancea / Nitrotoga use Calvin-Benson-Bassham (RuBisCO)."
                )
                ing.derived_from = ["lithotrophic_aerobic_nitrite capability"]
                break
        # Adjust shaking — NOB media benefit from gentle aeration to avoid
        # nitrite stripping; reduce default 150 → 120 rpm
        if recipe.conditions:
            recipe.conditions.shaking_rpm = 120
    elif any(t in text for t in ("nh4", "ammonia", "amoa")):
        recipe.primary_cultivation_mode = "lithotrophic_aerobic (ammonia oxidation)"
        recipe.ingredients.append(Ingredient(
            name="(NH4)2SO4", chemical_formula="(NH4)2SO4",
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="Ammonium as electron donor (~15 mM).",
            confidence=0.90,
            derived_from=["RecipeContext.electron_donors=NH4+", "amoA+hao detected"],
        ))
    elif any(t in text for t in ("hs-", "sulfide", "thiosulfate", "soxb", "sulfur")):
        recipe.primary_cultivation_mode = "lithotrophic_aerobic (sulfur oxidation)"
        recipe.ingredients.append(Ingredient(
            name="Na2S2O3·5H2O (thiosulfate)", chemical_formula="Na2S2O3·5H2O",
            concentration=5.0, concentration_unit="g/L",
            category=IngredientCategory.ELECTRON_DONOR,
            rationale="Thiosulfate as electron donor (~20 mM); SOX-pathway substrate.",
            confidence=0.85,
            derived_from=["RecipeContext.electron_donors=thiosulfate", "soxB detected"],
        ))

    return recipe


def _compose_acetogenic_recipe(context: RecipeContext) -> Recipe:
    """Acetogenic recipe — Wood-Ljungdahl pathway."""
    recipe = _new_recipe_skeleton(context, "acetogenic")
    recipe.composition_rationale.append(
        "Acetogenesis via Wood-Ljungdahl: CO2 + H2 → acetate. Strict anaerobic "
        "culture; B12 essential cofactor."
    )

    recipe.gas_phase = GasPhase(
        composition={"H2": 0.80, "CO2": 0.20}, pressure_atm=1.5,
        rationale="H2/CO2 80:20 — H2 electron donor, CO2 carbon source + electron acceptor.",
    )

    recipe.ingredients.append(Ingredient(
        name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
        concentration=0.5, concentration_unit="mM",
        category=IngredientCategory.REDUCING_AGENT,
        rationale="Establishes anaerobiosis.",
        confidence=0.95, derived_from=["acetogenic mode (anaerobic)"],
    ))
    recipe.ingredients.append(Ingredient(
        name="NaHCO3", chemical_formula="NaHCO3",
        concentration=2.5, concentration_unit="g/L",
        category=IngredientCategory.BUFFER,
        rationale="Bicarbonate buffer in equilibrium with CO2 headspace.",
        confidence=0.85, derived_from=["acetogenic mode"],
    ))
    # B12 essential
    recipe.ingredients.append(Ingredient(
        name="Cyanocobalamin (B12)",
        chemical_formula="C63H88CoN14O14P",
        concentration=50.0, concentration_unit="μg/L",
        category=IngredientCategory.VITAMIN,
        rationale=("B12 elevated for acsB/cooS — corrinoid is the methyl carrier "
                   "in WL pathway."),
        confidence=0.95, derived_from=["acetogenic mode (acsB+cooS)"],
    ))
    recipe.ingredients.append(Ingredient(
        name="CO2 (autotrophic carbon)", chemical_formula="CO2",
        concentration=20.0, concentration_unit="% v/v",
        category=IngredientCategory.CARBON_SOURCE,
        rationale="CO2 reduced to acetate via WL pathway; autotrophic.",
        confidence=0.90, derived_from=["acetogenic + RecipeContext.carbon_sources=CO2"],
    ))

    # Some acetogens (Acetobacterium woodii) also grow on fructose
    _add_carbon_sources(recipe, context, default_complex=False)

    return recipe


def _compose_syntrophic_recipe(context: RecipeContext) -> Recipe:
    """Syntrophic recipe — fatty acid donor with H2-consuming partner required."""
    recipe = _new_recipe_skeleton(context, "syntrophic")
    recipe.composition_rationale.append(
        "Syntrophy: organic donor oxidation is endergonic alone; only viable "
        "with a H2- or formate-consuming partner that keeps interspecies-H2 "
        "low. Recipe must include the partner (typically a hydrogenotrophic "
        "methanogen) — IT IS NOT POSSIBLE TO GROW PURE SYNTROPHS WITHOUT THEM."
    )

    recipe.gas_phase = GasPhase(
        composition={"N2": 0.80, "CO2": 0.20}, pressure_atm=1.0,
        rationale="N2/CO2 anaerobic headspace; partner methanogen produces CH4.",
    )
    recipe.ingredients.append(Ingredient(
        name="Sodium butyrate", chemical_formula="C4H7NaO2",
        concentration=2.2, concentration_unit="g/L",
        category=IngredientCategory.ELECTRON_DONOR,
        rationale="Butyrate (~20 mM) as syntroph donor; oxidized via β-oxidation.",
        confidence=0.85, derived_from=["syntrophic mode (Syntrophomonas-type)"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Na2S·9H2O", chemical_formula="Na2S·9H2O",
        concentration=0.5, concentration_unit="mM",
        category=IngredientCategory.REDUCING_AGENT,
        rationale="Establishes anaerobiosis.",
        confidence=0.95, derived_from=["anaerobic"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Yeast extract", chemical_formula=None,
        concentration=1.0, concentration_unit="g/L",
        category=IngredientCategory.NITROGEN_SOURCE,
        rationale="Yeast extract supplies vitamins / growth factors.",
        confidence=0.80, derived_from=["syntrophic mode"],
    ))
    # Partner organism note
    recipe.ingredients.append(Ingredient(
        name="REQUIRED CO-CULTURE: hydrogenotrophic methanogen partner",
        chemical_formula=None,
        concentration=0.0, concentration_unit="(co-inoculate)",
        category=IngredientCategory.SUPPLEMENT,
        rationale=("Pure-culture growth is thermodynamically impossible. "
                   "Co-inoculate with Methanospirillum hungatei, "
                   "Methanobacterium formicicum, or similar. The partner "
                   "consumes H2 produced by syntroph fatty-acid oxidation, "
                   "making the reaction exergonic."),
        confidence=0.95, derived_from=["syntrophic mode (fundamental requirement)"],
    ))
    recipe.uncertainty_flags.append(
        "Partner organism MUST be added — pure-culture growth is endergonic"
    )
    return recipe


def _compose_halophilic_recipe(context: RecipeContext) -> Recipe:
    """Halophilic-with-rhodopsin recipe (Halobacterium-type)."""
    recipe = _new_recipe_skeleton(context, "halophilic_with_rhodopsin")
    recipe.composition_rationale.append(
        "Extreme halophile with bacteriorhodopsin. Aerobic heterotroph using "
        "amino acids; rhodopsin provides supplementary light-driven energy. "
        "High NaCl (~25%) is essential."
    )

    recipe.gas_phase = GasPhase(
        composition={"air": 1.0}, pressure_atm=1.0,
        rationale="Aerobic; halobacteria are obligate aerobes despite having rhodopsin.",
    )
    if recipe.conditions:
        recipe.conditions.shaking_rpm = 150
        recipe.conditions.light_required = True  # supplementary
        recipe.conditions.light_intensity_umol_per_m2_per_s = 50.0
        recipe.conditions.rationale += "; shaking 150 rpm; ambient light for rhodopsin"

    # High NaCl. Phase 3.1: a user --salinity override replaces the 250 g/L default.
    sal_override = (context.conditions.salinity_g_per_l
                    if context.conditions else None)
    if sal_override is not None:
        nacl_conc = float(sal_override)
        nacl_rationale = (f"NaCl {nacl_conc:g} g/L (user-supplied salinity "
                          f"override; haloarchaeal default would be 250 g/L)")
        nacl_derived = ["user_override"]
    else:
        nacl_conc = 250.0
        nacl_rationale = ("25% NaCl (~4.3 M) — extreme halophile; cytoplasmic K+ "
                          "concentration matched to external Na+.")
        nacl_derived = ["RecipeContext.conditions.salinity_category=extreme_halophile"]
    recipe.ingredients.append(Ingredient(
        name="NaCl", chemical_formula="NaCl",
        concentration=nacl_conc, concentration_unit="g/L",
        category=IngredientCategory.SALT,
        rationale=nacl_rationale,
        confidence=0.95, derived_from=nacl_derived,
    ))
    recipe.ingredients.append(Ingredient(
        name="MgSO4·7H2O", chemical_formula="MgSO4·7H2O",
        concentration=20.0, concentration_unit="g/L",
        category=IngredientCategory.SALT,
        rationale="Elevated MgSO4 (~80 mM) typical of haloarchaeal media.",
        confidence=0.90, derived_from=["halophile mode"],
    ))
    recipe.ingredients.append(Ingredient(
        name="KCl", chemical_formula="KCl",
        concentration=2.0, concentration_unit="g/L",
        category=IngredientCategory.SALT,
        rationale="Potassium baseline (~25 mM) for halophile osmotic balance.",
        confidence=0.85, derived_from=["halophile mode"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Peptone", chemical_formula=None,
        concentration=10.0, concentration_unit="g/L",
        category=IngredientCategory.CARBON_SOURCE,
        rationale="Amino-acid carbon source for halobacterial growth.",
        confidence=0.85, derived_from=["heterotrophic halophile"],
    ))
    recipe.ingredients.append(Ingredient(
        name="Yeast extract", chemical_formula=None,
        concentration=5.0, concentration_unit="g/L",
        category=IngredientCategory.NITROGEN_SOURCE,
        rationale="Vitamins + amino acids.",
        confidence=0.85, derived_from=["heterotrophic halophile"],
    ))
    return recipe


def _compose_default_recipe(context: RecipeContext) -> Recipe:
    """Fallback when primary mode is unrecognized — basal heterotrophic recipe."""
    recipe = _new_recipe_skeleton(context, context.primary_cultivation_modes[0])
    recipe.composition_rationale.append(
        f"Primary mode '{context.primary_cultivation_modes[0]}' did not match a "
        "specific composer — falling back to basal heterotrophic medium."
    )
    recipe.gas_phase = GasPhase(
        composition={"air": 1.0}, pressure_atm=1.0,
        rationale="Default aerobic atmosphere (composer fallback).",
    )
    _add_carbon_sources(recipe, context, default_complex=True)
    return recipe


_MODE_COMPOSERS = {
    "methanogenic": _compose_methanogenic_recipe,
    "methanotrophic": _compose_methanotrophy_recipe,
    "anme_reverse_methanogenic": _compose_anme_recipe,
    "anammox": _compose_anammox_recipe,
    "aerobic_chemotrophic": _compose_aerobic_chemotrophic_recipe,
    "anaerobic_respiratory": _compose_anaerobic_respiratory_recipe,
    "phototrophic": _compose_phototrophic_recipe,
    "fermentative": _compose_fermentative_recipe,
    "lithotrophic_aerobic": _compose_lithotrophic_aerobic_recipe,
    "acetogenic": _compose_acetogenic_recipe,
    "syntrophic": _compose_syntrophic_recipe,
    "halophilic_with_rhodopsin": _compose_halophilic_recipe,
}


# ---------------------------------------------------------------------------
# Fix #1: Specificity-aware mode picker
# ---------------------------------------------------------------------------
# When the capability detector ranks a generic mode above a specific one (e.g.,
# Acidithiobacillus aerobic_resp 0.85 > Fe(II) ox 0.65), the recipe should
# still route to the more specific composer because it carries more biological
# information for cultivation. The specific modes below are listed in priority
# order — earlier entries win ties.
_SPECIFIC_MODES_PRIORITY = [
    # Phase 3.6: anme_reverse_methanogenic listed BEFORE methanogenic so the
    # priority loop encounters ANME first when both are detected. The mode
    # picker prefers ANME when its signature fires (mcrA + acceptor partner
    # via essential_marker_OR), preserving the empirical mcrA detection in
    # the capability profile while routing the recipe to anaerobic methane
    # oxidation cultivation. F.2 mitigation.
    "anme_reverse_methanogenic",
    "anammox",
    "methanogenic",
    "methanotrophic",
    "acetogenic",
    "syntrophic",
    "halophilic_with_rhodopsin",
    "phototrophic",
    "lithotrophic_aerobic",
]
# Generic modes are routes of last resort.
_GENERIC_MODES = {"aerobic_chemotrophic", "anaerobic_respiratory", "fermentative"}


# Modes that REQUIRE a diagnostic-marker hit to win the priority race.
# This mitigates docs/LIMITATIONS.md F.3 (spurious gapseq pathway calls): the recipe
# composer should weight diagnostic-marker-corroborated calls higher than
# gapseq-pathway-only calls (per the Phase 1.5n closeout guidance). Without
# this rule, Chloroflexus and Nitrospira route to the acetogenic composer
# because gapseq cross-annotates Wood-Ljungdahl-overlapping enzymes; with
# this rule, they fall through to the next priority that IS corroborated.
# Syntrophic is exempt because it's a composite-signature detector with no
# single diagnostic marker.
_MARKER_REQUIRED_MODES = {
    "methanogenic", "methanotrophic", "anme_reverse_methanogenic",
    "anammox",
    "acetogenic", "lithotrophic_aerobic",
    "phototrophic", "halophilic_with_rhodopsin",
}

# Cultivation-mode group names → required diagnostic markers (any one of).
# When the capability has at least one of these in `diagnostic_markers_hit`,
# the mode is "corroborated" and eligible for priority selection.
_MODE_DIAGNOSTIC_MARKERS = {
    "methanogenic":              ["mcrA", "mcrBG"],
    "methanotrophic":            ["pmoA", "mmoX"],
    "anme_reverse_methanogenic": ["mcrA"],  # mcrA + acceptor signature is the discriminator
    "anammox":                   ["hzsA", "hdh", "hao"],
    "acetogenic":                ["acsB_cdhC", "cooS_cdhA"],
    "lithotrophic_aerobic":      ["amoA", "amoA_archaeal", "hao", "soxB",
                                  "cyc2", "nxrA",
                                  "tqoDoxD", "tqoDoxA", "tetH", "sor"],
    "phototrophic":              ["pufLM", "pscA_fmoA", "psaA_psbA", "rhodopsin"],
    "halophilic_with_rhodopsin": ["rhodopsin"],
    # Phase 3.4: anaerobic_respiratory marker corroboration. Existing markers
    # (dsrAB, qmoA, mtrC_omcB, rdhA, hzsA, hdh, nosZ) carry sulfate reduction,
    # iron reduction, organohalide, anammox, and denitrification. Phase 3.4
    # adds nrfA for canonical NrfA-based DNRA (Wolinella-class obligates +
    # E. coli/D. vulgaris flagged as alternative).
    "anaerobic_respiratory":     ["dsrAB", "qmoA", "mtrC_omcB", "rdhA",
                                  "hzsA", "hdh", "nosZ", "nrfA"],
}


def _pick_primary_mode_for_recipe(context: RecipeContext,
                                    conn: Optional["sqlite3.Connection"] = None) -> str:
    """Choose the primary mode for recipe routing.

    Selection rule:
      1. If a specific mode is detected AND corroborated by a diagnostic
         marker hit on its underlying capability, prefer it (highest priority
         in `_SPECIFIC_MODES_PRIORITY` wins).
      2. Marker-exempt specific modes (currently `syntrophic`) are eligible
         based on detection alone.
      3. **Facultative anaerobe rule (Phase 2c E. coli fix):** if BOTH
         `aerobic_chemotrophic` AND `fermentative` are detected, AND no
         obligate-anaerobe mode (methanogenic / anaerobic_respiratory /
         syntrophic / acetogenic) is detected, AND aerobic_chemotrophic
         confidence ≥ 0.60, prefer aerobic primary. This matches lab
         convention (E. coli grown aerobically on LB / M9, not as anaerobic
         mixed-acid fermenter). The 0.60 threshold protects organisms with
         only weak aerobic respiration (Lactobacillus has no aerobic call;
         Scalindua's 0.55 falls below threshold).
      4. If no specific mode is corroborated, fall back to the highest-
         confidence detected mode (typically a generic respiratory or
         fermentative).

    The corroboration check requires the CapabilityProfile (queried from
    `conn`) — without it, the rule degrades to the simple priority list,
    which is fine for the dev set but risks F.3 spurious calls on the
    blind set.
    """
    detected = list(context.primary_cultivation_modes)
    detected_set = set(detected)

    # Build the corroborated set from the capability profile if conn given,
    # and also capture per-mode max-confidence for the facultative rule below
    corroborated = set()
    mode_confidence: dict = {}
    if conn is not None:
        try:
            from capability_detectors import (
                profile_capabilities, CULTIVATION_MODE_GROUPS,
            )
            profile = profile_capabilities(context.genome_id, conn)
            mode_confidence = {m["mode"]: m["max_confidence"]
                                for m in profile.cultivation_modes}
            # Map cap.name → diagnostic_markers_hit for each detected capability
            for cap in profile.capabilities:
                if not cap.detected or cap.confidence < 0.50:
                    continue
                for mode_name, patterns in CULTIVATION_MODE_GROUPS.items():
                    if any(p.lower() in cap.name.lower() for p in patterns):
                        required = _MODE_DIAGNOSTIC_MARKERS.get(mode_name, [])
                        if not required:
                            corroborated.add(mode_name)
                        elif any(m in cap.diagnostic_markers_hit for m in required):
                            corroborated.add(mode_name)
        except Exception:
            pass

    # Priority-ordered specific-mode selection (rules 1-2)
    for specific in _SPECIFIC_MODES_PRIORITY:
        if specific not in detected_set:
            continue
        if specific not in _MARKER_REQUIRED_MODES:
            return specific
        if conn is None or specific in corroborated:
            return specific
        # Otherwise demote — try the next specific mode

    # Rule 3: Facultative anaerobe handling
    # When both aerobic_chemotrophic and fermentative are detected and no
    # obligate-anaerobe mode is present, prefer aerobic — matches lab
    # convention for facultative organisms like E. coli.
    #
    # Phase 3.4 extension: anaerobic_respiratory should NOT count as obligate
    # when the only capability driving it is DNRA (NrfA-based nitrate-to-
    # ammonium). DNRA is facultative for most organisms (E. coli, Salmonella,
    # Mannheimia, etc.) — these grow aerobically by default and switch to DNRA
    # only under low-O2 high-NO3 conditions. For these organisms,
    # aerobic_chemotrophic is the appropriate primary mode and DNRA is flagged
    # as an alternative cultivation. Only treat anaerobic_respiratory as
    # obligate when a non-DNRA anaerobic respiration capability fires
    # (sulfate reduction, iron reduction, organohalide, anammox, denitrification).
    if ("aerobic_chemotrophic" in detected_set
            and "fermentative" in detected_set):
        obligate_anaerobe_modes = {
            "methanogenic", "anaerobic_respiratory",
            "syntrophic", "acetogenic",
        }
        has_obligate_anaerobe_mode = bool(detected_set & obligate_anaerobe_modes)
        # Phase 3.4: DNRA-only exception — if the anaerobic_respiratory signal
        # is solely from DNRA, this is a facultative organism, not obligate.
        if has_obligate_anaerobe_mode and "anaerobic_respiratory" in detected_set and conn is not None:
            try:
                from capability_detectors import (
                    profile_capabilities, CULTIVATION_MODE_GROUPS,
                )
                profile = profile_capabilities(context.genome_id, conn)
                anaer_patterns = CULTIVATION_MODE_GROUPS.get("anaerobic_respiratory", [])
                non_dnra_anaerobic = [
                    c for c in profile.capabilities
                    if c.detected and c.confidence >= 0.50
                    and any(p.lower() in c.name.lower() for p in anaer_patterns)
                    and "nitrate reduction to ammonium" not in c.name.lower()
                ]
                # If ONLY DNRA fires under anaerobic_respiratory, and no other
                # obligate-anaerobe mode is detected, demote anaerobic_respiratory
                # so the facultative-aerobic rule can fire.
                other_obligates = detected_set & {"methanogenic", "syntrophic", "acetogenic"}
                if not non_dnra_anaerobic and not other_obligates:
                    has_obligate_anaerobe_mode = False
            except Exception:
                pass
        # GenomeSPOT strict-anaerobe override
        is_strict_anaerobe_genomespot = False
        if conn is not None:
            try:
                row = conn.execute(
                    "SELECT value FROM genome_growth_predictions "
                    "WHERE genome_id = ? AND target = 'oxygen'",
                    (context.genome_id,)
                ).fetchone()
                if row and row[0] in ("not_tolerant", "anaerobe", "strict_anaerobe"):
                    is_strict_anaerobe_genomespot = True
            except Exception:
                pass

        aerobic_conf = mode_confidence.get("aerobic_chemotrophic", 0.0)
        if (not has_obligate_anaerobe_mode
                and not is_strict_anaerobe_genomespot
                and aerobic_conf >= 0.60):
            return "aerobic_chemotrophic"

    # Rule 4: Fall back to highest-confidence detected mode
    return detected[0]


# ---------------------------------------------------------------------------
# Fix #3: Carbon source filter for autotrophic modes
# ---------------------------------------------------------------------------

# Modes where the organism is biologically autotrophic — the recipe should
# list inorganic carbon (CO2) and only accept organic carbon when the
# RecipeContext evidence is overwhelming. Acidithiobacillus (lithotrophic Fe(II))
# and methanogens / acetogens fall into this category.
_AUTOTROPHIC_MODES = {
    "methanogenic", "acetogenic", "lithotrophic_aerobic",
}


def _filter_carbon_sources_for_mode(carbon_sources: list, primary_mode: str) -> list:
    """Suppress spurious organic carbon for obligate autotrophs.

    For autotrophic modes:
      - Always keep CO2 / methane / inorganic-class sources
      - Keep organic sources only with very high confidence (>=0.85) AND
        an explicit derived_from_capability link
      - If all carbon sources are organic and below 0.85 confidence,
        return an empty list (the composer will then fall back to CO2 + NaHCO3
        from the mode-specific composer).
    """
    if not carbon_sources:
        return []
    if primary_mode not in _AUTOTROPHIC_MODES:
        return carbon_sources
    # Autotrophic — filter organics
    inorganic_types = {"CO2", "methane", "inorganic"}
    kept = []
    for cs in carbon_sources:
        if cs.type in inorganic_types:
            kept.append(cs)
        elif cs.confidence >= 0.85 and cs.derived_from_capability:
            kept.append(cs)
        # else: drop (likely cross-reactive gapseq sugar pathway annotation)
    return kept


# ---------------------------------------------------------------------------
# Carbon source helper
# ---------------------------------------------------------------------------

def _add_carbon_sources(recipe: Recipe, context: RecipeContext,
                        default_complex: bool = True) -> None:
    """Add carbon sources from RecipeContext, or fallback to peptone+yeast extract.

    Fix #3: filter spurious organic carbon for autotrophic / lithotrophic modes.
    Acidithiobacillus (lithotrophic) and methanogens / acetogens shouldn't get
    glucose listed even if gapseq sugar-utilization annotations cross-react —
    these organisms are obligate autotrophs and the recipe should reflect that.
    """
    sources = _filter_carbon_sources_for_mode(
        context.carbon_sources, recipe.primary_cultivation_mode
    )
    if sources:
        for cs in sources[:2]:
            recipe.ingredients.append(Ingredient(
                name=cs.name.capitalize(),
                chemical_formula=None,
                concentration=2.0, concentration_unit="g/L",
                category=IngredientCategory.CARBON_SOURCE,
                rationale=("Carbon source from RecipeContext: " +
                           "; ".join(cs.evidence[:2]) if cs.evidence else
                           "Carbon source from RecipeContext"),
                confidence=cs.confidence,
                derived_from=([cs.derived_from_capability] if cs.derived_from_capability
                              else ["RecipeContext.carbon_sources"]),
            ))
        return
    # Fallback
    if default_complex:
        recipe.ingredients.append(Ingredient(
            name="Peptone", chemical_formula=None,
            concentration=5.0, concentration_unit="g/L",
            category=IngredientCategory.CARBON_SOURCE,
            rationale="Complex carbon/nitrogen source (default — no specific carbon detected).",
            confidence=0.65, derived_from=["composer default"],
        ))
        recipe.ingredients.append(Ingredient(
            name="Yeast extract", chemical_formula=None,
            concentration=2.0, concentration_unit="g/L",
            category=IngredientCategory.NITROGEN_SOURCE,
            rationale="Vitamins + amino acids supplement (default).",
            confidence=0.75, derived_from=["composer default"],
        ))


# ---------------------------------------------------------------------------
# Mode-specific adjustments after common-basal step
# ---------------------------------------------------------------------------

def _apply_mode_adjustments(recipe: Recipe, context: RecipeContext) -> None:
    """Apply mode-specific or condition-specific tweaks after common-basal."""
    cond = recipe.conditions
    if cond is None:
        return

    # Hyperthermophiles: switch buffer to HEPES/PIPES (phosphate precipitates at high T)
    if cond.temperature_c >= 65:
        for ing in recipe.ingredients:
            if ing.category == IngredientCategory.BUFFER and "phosphate" in ing.name.lower():
                ing.name = "PIPES buffer"
                ing.chemical_formula = "C8H18N2O6S2"
                ing.concentration = 25.0
                ing.concentration_unit = "mM"
                ing.rationale = (
                    f"PIPES buffer (25 mM) at pH {cond.ph:.1f} — replaces "
                    "phosphate; phosphate precipitates with Ca2+/Mg2+ at high T."
                )

    # Acidophiles: skip phosphate buffer entirely (pH < 4)
    if cond.ph < 4.0:
        recipe.ingredients = [
            i for i in recipe.ingredients
            if not (i.category == IngredientCategory.BUFFER and "phosphate" in i.name.lower())
        ]
        recipe.ingredients.append(Ingredient(
            name="H2SO4 (pH adjustment)", chemical_formula="H2SO4",
            concentration=0.0, concentration_unit="(adjust to pH "
                                                   f"{cond.ph:.1f})",
            category=IngredientCategory.BUFFER,
            rationale=f"Adjust pH to {cond.ph:.1f} with H2SO4 — acidophile.",
            confidence=0.90, derived_from=["acidophile pH"],
        ))

    # Halophilic - already handled in halophilic composer; skip here.

    # Methanogen: elevate Ni in trace metals (note as supplement, not modify SL-10)
    if "methanogenic" in recipe.primary_cultivation_mode:
        recipe.ingredients.append(Ingredient(
            name="NiCl2·6H2O (Ni supplement, elevated)", chemical_formula="NiCl2·6H2O",
            concentration=10.0, concentration_unit="μM",
            category=IngredientCategory.SUPPLEMENT,
            rationale=("Elevated Ni (~10 μM total) for F430 cofactor in mcrA. "
                       "Standard SL-10 includes lower Ni; this top-up matters."),
            confidence=0.90, derived_from=["methanogenic mode"],
        ))


# ---------------------------------------------------------------------------
# Thermodynamic gating (Phase 2c Task 3 — implemented in this scaffold)
# ---------------------------------------------------------------------------

def _apply_thermodynamic_check(recipe: Recipe, context: RecipeContext,
                                primary_mode: str,
                                conn: Optional["sqlite3.Connection"] = None) -> None:
    """Compute ΔG for the dominant reaction and attach a ThermodynamicCheck."""
    # Identify reaction template — disambiguate anaerobic_respiratory by sub-mode
    template_key = primary_mode
    if primary_mode == "anaerobic_respiratory":
        sub_mode = _classify_anaerobic_subtype(context, conn=conn)
        template_key = f"anaerobic_respiratory_{sub_mode}"
    elif primary_mode == "lithotrophic_aerobic":
        cap_text = " ".join(context.primary_cultivation_modes).lower() + " " + " ".join(
            d.name for d in context.electron_donors
        ).lower()
        if "fe(ii)" in cap_text or "iron" in cap_text or "ferro" in cap_text:
            template_key = "lithotrophic_aerobic_iron"
        elif "no2-" in cap_text or "nitrite oxidation" in cap_text or "nxra" in cap_text:
            template_key = "lithotrophic_aerobic_nitrite"
        elif "nh4" in cap_text or "ammonia" in cap_text:
            template_key = "lithotrophic_aerobic_ammonia"
        else:
            template_key = "lithotrophic_aerobic_sulfur"

    tmpl = REACTION_TEMPLATES.get(template_key) or REACTION_TEMPLATES.get(primary_mode)
    if tmpl is None:
        recipe.thermodynamic_checks.append(ThermodynamicCheck(
            capability_name=primary_mode,
            primary_reaction="(no template defined for this mode)",
            delta_g_kj_per_mol=0.0,
            feasible=True, feasibility_class="unknown",
            notes="Skipped thermodynamic check — no reaction template defined.",
        ))
        return

    dg = tmpl["delta_g_standard"]
    feasible = dg < -10.0
    if dg > 0:
        feasibility_class = "infeasible"
    elif dg <= -10.0:
        feasibility_class = "feasible"
    else:
        feasibility_class = "marginal"
    notes = ""
    if primary_mode == "syntrophic":
        notes = ("Reaction is endergonic alone (ΔG > 0). Becomes feasible only "
                 "when [H2] is kept low by a syntrophic partner — recipe "
                 "explicitly requires partner co-inoculation.")
        feasibility_class = "marginal"
        feasible = True   # context-conditional feasibility

    recipe.thermodynamic_checks.append(ThermodynamicCheck(
        capability_name=primary_mode,
        primary_reaction=tmpl["reaction"],
        delta_g_kj_per_mol=dg,
        feasible=feasible,
        feasibility_class=feasibility_class,
        notes=notes,
    ))

    if feasibility_class == "infeasible" and primary_mode != "syntrophic":
        recipe.escalated = True
        recipe.escalation_reason = (
            f"Thermodynamic gate failed: dominant reaction for {primary_mode} "
            f"has ΔG = {dg:.1f} kJ/mol > 0 under standard conditions. "
            "Escalating to ESCALATE_STRUCTURAL."
        )


# ---------------------------------------------------------------------------
# Limitations catalog flags
# ---------------------------------------------------------------------------

def _apply_limitations_flags(recipe: Recipe, context: RecipeContext) -> None:
    """Map detected capabilities + recipe state to docs/LIMITATIONS.md categories."""
    primary = recipe.primary_cultivation_mode.lower()
    cap_text = " ".join(context.primary_cultivation_modes).lower()
    notes = " ".join(context.cultivation_mode_notes).lower()

    # A.1 / D.1 — organohalide substrate ambiguity
    if "organohalide" in primary or "rdhA" in cap_text or "dehalogen" in notes:
        recipe.limitations_referenced.append("A.1")
        recipe.limitations_referenced.append("D.1")
        recipe.uncertainty_flags.append(
            "Specific halogenated substrate cannot be determined from genome alone "
            "(rdhA detects the family but not substrate specificity). User must "
            "select the actual halogenated electron acceptor based on isolation "
            "source chemistry."
        )
    # A.2 — comammox amoA divergence
    if "comammox" in notes or ("amoa" in cap_text and "nitrospira" in (
            context.species or "").lower()):
        recipe.limitations_referenced.append("A.2")

    # C.1 — ANME directional ambiguity
    if "methanogenic" in primary:
        species_lower = (context.species or "").lower()
        # Two triggers: (a) species in known ANME clades, (b) co-detected alt-acceptor metabolism
        anme_species = any(
            tag in species_lower
            for tag in ("methanoperedens", "anme", "methanosarcina")
        )
        has_alt_acceptor = any(
            "iron" in m.lower() or "sulfate" in m.lower() or "nitrate" in m.lower()
            for m in context.primary_cultivation_modes
        )
        if anme_species or has_alt_acceptor:
            recipe.limitations_referenced.append("C.1")
            recipe.uncertainty_flags.append(
                "ANME directional ambiguity: genome has methanogenesis enzymes "
                "(mcrA + WL pathway) but the metabolism may run in reverse "
                "(anaerobic methane oxidation). If suspected ANME, replace "
                "H2/CO2 with CH4 + electron acceptor (NO3-, SO4-2, or Fe(III)) "
                "and verify direction experimentally."
            )

    # C.2 — reverse-dsr (mostly resolved by qmoA AND-rule)
    if "sulfate reduction" in primary:
        recipe.limitations_referenced.append("C.2")

    # E.1 — Scalindua MAG completeness — escalate, recipe is wrong
    if context.species and "scalindua" in context.species.lower():
        recipe.limitations_referenced.append("E.1")
        recipe.uncertainty_flags.append(
            "Scalindua-clade detection failure is a MAG completeness limitation: "
            "predicted proteome lacks hzsA / hdh, so anammox could not be "
            "detected. The composed recipe is for the highest-confidence "
            "DETECTED mode but does NOT reflect the organism's true biology. "
            "Treat as ESCALATE_STRUCTURAL."
        )
        recipe.escalated = True
        recipe.escalation_reason = (
            "Scalindua MAG lacks hzsA/hdh in predicted proteome. The composed "
            "recipe routes to the next-best detected mode but is not biologically "
            "correct. Manual annotation or improved MAG required."
        )

    # F.1 — capability detected via override
    # (Detected by checking if any capability has the override flag)
    # This requires re-reading the capability profile which is in context only
    # indirectly via cultivation_mode_notes — we leave a generic flag.
    if any("override" in n.lower() for n in context.cultivation_mode_notes):
        recipe.limitations_referenced.append("F.1")


# ---------------------------------------------------------------------------
# Confidence computation
# ---------------------------------------------------------------------------

def _compute_recipe_confidence(recipe: Recipe, context: RecipeContext) -> float:
    """Coarse-bucket recipe confidence."""
    # Base from RecipeContext
    base = context.overall_confidence

    # Penalize uncertainty flags
    flag_penalty = min(0.20, 0.05 * len(recipe.uncertainty_flags))

    # Penalize default fallback ingredients (low-confidence carbon sources)
    fallback_count = sum(1 for i in recipe.ingredients
                          if "default" in i.rationale.lower() and i.confidence < 0.70)
    fallback_penalty = min(0.15, 0.04 * fallback_count)

    # Thermodynamic gate
    therm_penalty = 0.0
    for tc in recipe.thermodynamic_checks:
        if tc.feasibility_class == "infeasible":
            therm_penalty = 0.30
        elif tc.feasibility_class == "marginal" and recipe.primary_cultivation_mode != "syntrophic":
            therm_penalty = max(therm_penalty, 0.10)

    # Escalation overrides
    if recipe.escalated:
        return round(max(0.10, base - 0.40), 2)

    final = base - flag_penalty - fallback_penalty - therm_penalty
    final = max(0.20, min(0.95, final))

    parts = [f"base from RecipeContext = {base:.2f}"]
    if flag_penalty > 0: parts.append(f"-{flag_penalty:.2f} from uncertainty flags")
    if fallback_penalty > 0: parts.append(f"-{fallback_penalty:.2f} from fallback ingredients")
    if therm_penalty > 0: parts.append(f"-{therm_penalty:.2f} from thermodynamic gate")
    recipe.confidence_rationale = "; ".join(parts) + f" → final {final:.2f}"
    return round(final, 2)


# ---------------------------------------------------------------------------
# Escalation helper
# ---------------------------------------------------------------------------

def _escalated_recipe(context: RecipeContext, reason: str) -> Recipe:
    """Build an escalated (no-recipe-composed) Recipe."""
    return Recipe(
        genome_id=context.genome_id,
        species=context.species,
        primary_cultivation_mode="ESCALATE_STRUCTURAL",
        escalated=True,
        escalation_reason=reason,
        overall_confidence=0.10,
        confidence_rationale="No recipe composed; detection layer failed to produce a primary cultivation mode.",
        uncertainty_flags=["No primary cultivation mode detected — Tier 2 structural analysis recommended"],
    )
